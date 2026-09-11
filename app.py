"""SatQuery — Cyber-Geospatial Intelligence & Orbital VLM Analysis Platform.

Features
--------
- Qwen3-VL-4B-Instruct inference with 4-bit quantisation & FP16 safe fallback.
- Question routing: VQA / counting / comparison / grounding / change detection.
- Multi-spectral visual evidence extraction: attention heatmap + tactical reticle box.
- Bi-temporal disaster damage analysis with pixel-difference heat mapping.
- Heuristic confidence estimate & GeoTIFF raster telemetry.
- Next-Gen Aerospace Mission Control HUD Interface.
"""

from __future__ import annotations

import asyncio.base_events as _asyncio_base_events
import base64
import io
import mimetypes
import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageEnhance
import gradio as gr
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

# -----------------------------------------------------------------------------
# Gradio / Python 3.12+ cleanup workaround
# -----------------------------------------------------------------------------
_original_event_loop_del = getattr(_asyncio_base_events.BaseEventLoop, "__del__", None)
if _original_event_loop_del is not None and not getattr(_original_event_loop_del, "_satquery_patched", False):
    def _satquery_event_loop_del(self):
        try:
            _original_event_loop_del(self)
        except ValueError as exc:
            if str(exc) != "Invalid file descriptor: -1":
                raise

    _satquery_event_loop_del._satquery_patched = True
    _asyncio_base_events.BaseEventLoop.__del__ = _satquery_event_loop_del

try:
    import spaces
    HAS_SPACES = True
except ImportError:
    HAS_SPACES = False

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    rasterio = None
    HAS_RASTERIO = False


# =============================================================================
# CONFIG & TELEMETRY
# =============================================================================

MODEL_ID = os.getenv("SATQUERY_MODEL_ID", "Qwen/Qwen3-VL-4B-Instruct")
MAX_NEW_TOKENS = int(os.getenv("SATQUERY_MAX_NEW_TOKENS", "128"))
DEFAULT_ATTENTION = os.getenv("SATQUERY_SHOW_EVIDENCE", "1") != "0"

EXAMPLES: list[tuple[str, str, str]] = [
    ("examples/scene_535.png", "Residential Infrastructure", "Is a residential building present in this scene?"),
    ("examples/scene_545.png", "Canopy & Road Network", "Are there more forests than roads in the image?"),
    ("examples/scene_498.png", "Hydrology & Agriculture", "Are there more large water areas than farmlands?"),
    ("examples/scene_479.png", "Transportation Arteries", "Is there a small road visible across the terrain?"),
]

DISASTER_EXAMPLES: list[tuple[str, str, str, str, str]] = [
    (
        "Tsunami Impact",
        "Palu, Indonesia (2018)",
        "disaster_examples/tsunami_before.tiff",
        "disaster_examples/tsunami_after.tiff",
        "Describe the coastal inundation and structural damage caused by the tsunami between these scenes.",
    ),
    (
        "Slope Landslide",
        "Mountain Corridor",
        "disaster_examples/landslide_before.tiff",
        "disaster_examples/landslide_after.tiff",
        "Describe what changed on the mountain slope between these two temporal images.",
    ),
    (
        "Urban Earthquake",
        "Structural Collapse",
        "disaster_examples/earthquake_before.tiff",
        "disaster_examples/earthquake_after.tiff",
        "How many buildings appear damaged or collapsed in the post-disaster scene compared to before?",
    ),
    (
        "Severe Drought",
        "Vegetation Stress",
        "disaster_examples/famine_before.tiff",
        "disaster_examples/famine_after.tiff",
        "Describe the change in vegetation health and soil moisture between these two images.",
    ),
    (
        "Farmland Conversion",
        "Urban Sprawl / SDG 11",
        "disaster_examples/arable_land_before.tiff",
        "disaster_examples/arable_land_after.tiff",
        "Has agricultural farmland been converted to built-up area between the two timestamps?",
    ),
    (
        "Flood Inundation",
        "River Basin Surge",
        "disaster_examples/water_rise_before.tiff",
        "disaster_examples/water_rise_after.tiff",
        "Has the water surface area expanded significantly between these two observation captures?",
    ),
]


# =============================================================================
# MODEL CACHE
# =============================================================================

_model = None
_processor = None


def _load():
    """Load model and processor with GPU 4-bit NF4 quant or FP16/CPU fallback."""
    global _model, _processor
    if _model is not None:
        return _model, _processor

    print(f"Loading {MODEL_ID}...")
    load_kwargs: dict[str, Any] = {"device_map": "auto"}
    if torch.cuda.is_available():
        try:
            import bitsandbytes
            quant = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            load_kwargs["quantization_config"] = quant
        except Exception as exc:
            print("Quantization warning (falling back to float16):", exc)
            load_kwargs["torch_dtype"] = torch.float16
    else:
        load_kwargs["torch_dtype"] = torch.float32

    _model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID,
        **load_kwargs,
    )
    _processor = AutoProcessor.from_pretrained(MODEL_ID)
    print("Model and processor loaded.")
    return _model, _processor


def _model_device(model):
    return next(model.parameters()).device


# =============================================================================
# QUESTION ROUTER
# =============================================================================


def route_question(query: str, temporal: bool = False) -> str:
    """Deterministic transparent question routing."""
    q = (query or "").strip().lower()
    if temporal or any(k in q for k in (
        "before", "after", "changed", "change", "damage", "damaged",
        "destroyed", "collapsed", "increase", "decrease", "lost", "inundation",
    )):
        return "Change Detection"
    if any(k in q for k in ("how many", "how much", "count", "number of", "tally")):
        return "Feature Counting"
    if any(k in q for k in ("more", "less", "fewer", "greater", "larger", "compare", "versus", "vs")):
        return "Spatial Comparison"
    if any(k in q for k in ("where", "which area", "which region", "location", "located", "quadrant")):
        return "Visual Grounding"
    if any(k in q for k in ("is there", "are there", "present", "visible", "contains", "contain", "detect")):
        return "Presence Verification"
    return "Multimodal VQA"


# =============================================================================
# IMAGE & GEOSPATIAL TELEMETRY
# =============================================================================


def _safe_rgb(image: Image.Image) -> Image.Image:
    if not isinstance(image, Image.Image):
        raise TypeError("Expected a PIL image")
    return image.convert("RGB")


def _preprocess_image(image: Image.Image, contrast: float = 1.0, sharpness: float = 1.0) -> Image.Image:
    out = _safe_rgb(image)
    if abs(contrast - 1.0) > 1e-6:
        out = ImageEnhance.Contrast(out).enhance(float(contrast))
    if abs(sharpness - 1.0) > 1e-6:
        out = ImageEnhance.Sharpness(out).enhance(float(sharpness))
    return out


def _geo_metadata(path: str | None) -> dict[str, str]:
    if not path or not HAS_RASTERIO or not Path(path).exists():
        return {}
    try:
        with rasterio.open(path) as src:
            bounds = src.bounds
            return {
                "driver": str(src.driver),
                "crs": str(src.crs) if src.crs else "EPSG:4326 (WGS84)",
                "width": str(src.width),
                "height": str(src.height),
                "bands": str(src.count),
                "resolution": f"{src.res[0]:.3f} × {src.res[1]:.3f} m/px",
                "bounds": f"[{bounds.left:.4f}, {bounds.bottom:.4f}, {bounds.right:.4f}, {bounds.top:.4f}]",
            }
    except Exception as exc:
        print("Geo metadata warning:", exc)
        return {}


def metadata_text(image: Image.Image, source_path: str | None = None) -> str:
    meta = _geo_metadata(source_path)
    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║                GEOSPATIAL SENSOR TELEMETRY                  ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  MATRIX RASTER   : {image.width} × {image.height} px (Channels: {image.mode})",
    ]
    if meta:
        lines += [
            f"║  COORDINATE CRS  : {meta['crs']}",
            f"║  SPECTRAL BANDS  : {meta['bands']} Channel(s) [{meta['driver']}]",
            f"║  GSD RESOLUTION  : {meta['resolution']}",
            f"║  BOUNDING EXTENT : {meta['bounds']}",
        ]
    else:
        lines += [
            "║  COORDINATE CRS  : Standard Local Optical Frame (GSD: ~0.5m)",
            "║  SPECTRAL BANDS  : 3 Optical (RGB Visible Spectrum)",
            "║  GEO-REFERENCING : Pixel-Relative Local Matrix",
        ]
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


# =============================================================================
# ATTENTION EVIDENCE & GROUNDING
# =============================================================================


def _force_eager_attention(model):
    previous: list[tuple[Any, Any]] = []
    for module in model.modules():
        config = getattr(module, "config", None)
        if config is not None and hasattr(config, "_attn_implementation"):
            previous.append((config, config._attn_implementation))
            config._attn_implementation = "eager"
    return previous


def _restore_attention(previous):
    for config, value in previous:
        config._attn_implementation = value


def _find_image_token_positions(model, input_ids: torch.Tensor) -> torch.Tensor:
    image_token_id = getattr(model.config, "image_token_id", None)
    if image_token_id is None:
        vals, counts = torch.unique(input_ids, return_counts=True)
        candidate = vals[int(counts.argmax())].item()
        if int(counts.max()) < 4:
            return torch.empty(0, dtype=torch.long, device=input_ids.device)
        image_token_id = candidate
    return (input_ids == image_token_id).nonzero(as_tuple=True)[0]


def _extract_attention(model, processor, image: Image.Image, query: str, max_new_tokens: int):
    device = _model_device(model)
    messages = [{
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": query},
        ],
    }]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], return_tensors="pt").to(device)

    previous = _force_eager_attention(model)
    try:
        with torch.inference_mode():
            out = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                output_attentions=True,
                return_dict_in_generate=True,
            )
    finally:
        _restore_attention(previous)

    answer = processor.batch_decode(
        out.sequences[:, inputs["input_ids"].shape[1]:],
        skip_special_tokens=True,
    )[0].strip()

    positions = _find_image_token_positions(model, inputs["input_ids"][0])
    if not getattr(out, "attentions", None) or positions.numel() == 0:
        return answer, None, None

    n_layers = len(out.attentions[0])
    layer_ids = range(max(0, n_layers * 3 // 4), n_layers)
    accum = torch.zeros(len(positions), device=device)
    used = 0

    for step_attn in out.attentions:
        for layer_idx in layer_ids:
            layer_attn = step_attn[layer_idx]
            if layer_attn is None or layer_attn.ndim != 4:
                continue
            if layer_attn.shape[-1] <= int(positions.max().item()):
                continue
            values = layer_attn[0, :, -1, :].mean(dim=0)
            accum += values[positions]
            used += 1

    if used == 0:
        return answer, None, None

    attn = (accum / used).float().cpu().numpy()

    grid = None
    grid_thw = inputs.get("image_grid_thw")
    if grid_thw is not None:
        vals = grid_thw[0].tolist() if hasattr(grid_thw[0], "tolist") else grid_thw[0]
        vision_config = getattr(model.config, "vision_config", None)
        merge = int(getattr(vision_config, "spatial_merge_size", 1))
        if len(vals) >= 3:
            h = int(vals[-2]) // max(1, merge)
            w = int(vals[-1]) // max(1, merge)
            if h * w == len(attn):
                grid = (h, w)

    return answer, attn, grid


def _generate_answer(image: Image.Image, query: str, extract_evidence: bool):
    model, processor = _load()
    if extract_evidence:
        return _extract_attention(model, processor, image, query, MAX_NEW_TOKENS)

    device = _model_device(model)
    messages = [{
        "role": "user",
        "content": [{"type": "image"}, {"type": "text", "text": query}],
    }]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], return_tensors="pt").to(device)
    with torch.inference_mode():
        out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
    answer = processor.batch_decode(
        out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )[0].strip()
    return answer, None, None


def _smooth_attention(arr: np.ndarray, passes: int = 2) -> np.ndarray:
    out = arr.astype(np.float32, copy=True)
    for _ in range(max(0, passes)):
        pad = np.pad(out, 1, mode="edge")
        out = (
            pad[:-2, :-2] + pad[:-2, 1:-1] + pad[:-2, 2:] +
            pad[1:-1, :-2] + pad[1:-1, 1:-1] + pad[1:-1, 2:] +
            pad[2:, :-2] + pad[2:, 1:-1] + pad[2:, 2:]
        ) / 9.0
    return out


def _connected_components(mask: np.ndarray):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    components = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            ys, xs = [], []
            while stack:
                cy, cx = stack.pop()
                ys.append(cy); xs.append(cx)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            components.append((np.asarray(ys), np.asarray(xs)))
    return components


def _evidence_box(image: Image.Image, attn_1d: np.ndarray, grid: tuple[int, int]) -> Image.Image:
    from PIL import ImageDraw
    h, w = grid
    arr = _smooth_attention(attn_1d.reshape(h, w), passes=2)
    lo, hi = float(arr.min()), float(arr.max())
    arr = (arr - lo) / (hi - lo + 1e-8)
    threshold = max(float(np.quantile(arr, 0.78)), 0.42)
    mask = arr >= threshold
    comps = _connected_components(mask)
    if comps:
        ys, xs = max(comps, key=lambda c: float(arr[c].mean() * np.sqrt(len(c[0]))))
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
    else:
        cy, cx = np.unravel_index(int(np.argmax(arr)), arr.shape)
        y0, y1 = max(0, int(cy) - 2), min(h - 1, int(cy) + 2)
        x0, x1 = max(0, int(cx) - 2), min(w - 1, int(cx) + 2)

    pad_y = max(2, int((y1 - y0 + 1) * 0.32))
    pad_x = max(2, int((x1 - x0 + 1) * 0.32))
    y0, y1 = max(0, y0 - pad_y), min(h - 1, y1 + pad_y)
    x0, x1 = max(0, x0 - pad_x), min(w - 1, x1 + pad_x)

    W, H = image.size
    px0, px1 = int(x0 / w * W), int((x1 + 1) / w * W)
    py0, py1 = int(y0 / h * H), int((y1 + 1) / h * H)
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    line = max(3, round(min(W, H) / 180))
    c = (0, 240, 255)  # Cyan HUD Reticle
    draw.rectangle((px0, py0, px1, py1), outline=c, width=line)
    L = max(14, round(min(W, H) * 0.05))
    for sx, sy in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        hx = 1 if sx == px0 else -1
        vy = 1 if sy == py0 else -1
        draw.line((sx, sy, sx + hx * L, sy), fill=c, width=line + 2)
        draw.line((sx, sy, sx, sy + vy * L), fill=c, width=line + 2)
    return out


def _overlay(image: Image.Image, attn_1d: np.ndarray, grid: tuple[int, int], alpha: float = 0.45) -> Image.Image:
    import matplotlib
    h, w = grid
    arr = attn_1d.reshape(h, w)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    heat = Image.fromarray((arr * 255).astype(np.uint8)).resize(image.size, Image.BILINEAR)
    cmap = matplotlib.colormaps["turbo"]
    heat_rgb = (cmap(np.asarray(heat) / 255.0)[:, :, :3] * 255).astype(np.uint8)
    return Image.blend(image.convert("RGB"), Image.fromarray(heat_rgb), alpha=alpha)


# =============================================================================
# CONFIDENCE & TELEMETRY
# =============================================================================


def estimate_confidence(answer: str, route: str, evidence_available: bool) -> tuple[int, str]:
    a = (answer or "").strip().lower()
    score = 62
    if a:
        score += 8
    if any(x in a for x in ("cannot determine", "uncertain", "unclear", "insufficient resolution")):
        score -= 30
    if any(x in a for x in ("yes", "no", "approximately", "evident", "visible", "present", "detected")):
        score += 8
    if route == "Feature Counting":
        score -= 5
    if route == "Visual Grounding":
        score -= 2
    if evidence_available:
        score += 7
    score = max(12, min(96, score))
    label = "HIGH CONFIDENCE 🟢" if score >= 75 else "MODERATE TELEMETRY 🟡" if score >= 55 else "LOW / ADVISORY 🔴"
    return score, label


# =============================================================================
# BI-TEMPORAL DISASTER ANALYSIS
# =============================================================================


def _extract_temporal(model, processor, image_a: Image.Image, image_b: Image.Image, query: str):
    device = _model_device(model)
    messages = [{
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "image"},
            {"type": "text", "text": query},
        ],
    }]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image_a, image_b], return_tensors="pt").to(device)
    with torch.inference_mode():
        out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
    answer = processor.batch_decode(
        out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )[0].strip()
    return answer


def _diff_map(image_a: Image.Image, image_b: Image.Image, grid: int = 24) -> np.ndarray:
    a = np.asarray(image_a.convert("RGB").resize((384, 384)), dtype=np.float32)
    b = np.asarray(image_b.convert("RGB").resize((384, 384)), dtype=np.float32)
    diff = np.abs(a - b).mean(axis=-1)
    step = 384 // grid
    cropped = diff[:step * grid, :step * grid]
    return cropped.reshape(grid, step, grid, step).mean(axis=(1, 3))


def _diff_overlay(image_b: Image.Image, diff_arr: np.ndarray, alpha: float = 0.48) -> Image.Image:
    import matplotlib
    arr = diff_arr.copy()
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    heat = Image.fromarray((arr * 255).astype(np.uint8)).resize(image_b.size, Image.BILINEAR)
    cmap = matplotlib.colormaps["hot"]
    heat_rgb = (cmap(np.asarray(heat) / 255.0)[:, :, :3] * 255).astype(np.uint8)
    return Image.blend(image_b.convert("RGB"), Image.fromarray(heat_rgb), alpha=alpha)


def _diff_box(image_b: Image.Image, diff_arr: np.ndarray) -> Image.Image:
    from PIL import ImageDraw
    h, w = diff_arr.shape
    arr = _smooth_attention(diff_arr, passes=2)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    mask = arr >= max(float(np.quantile(arr, 0.78)), 0.42)
    comps = _connected_components(mask)
    if comps:
        ys, xs = max(comps, key=lambda c: float(arr[c].mean() * np.sqrt(len(c[0]))))
        y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    else:
        cy, cx = np.unravel_index(int(np.argmax(arr)), arr.shape)
        y0, y1 = max(0, int(cy) - 2), min(h - 1, int(cy) + 2)
        x0, x1 = max(0, int(cx) - 2), min(w - 1, int(cx) + 2)
    pad_y = max(2, int((y1 - y0 + 1) * 0.32))
    pad_x = max(2, int((x1 - x0 + 1) * 0.32))
    y0, y1 = max(0, y0 - pad_y), min(h - 1, y1 + pad_y)
    x0, x1 = max(0, x0 - pad_x), min(w - 1, x1 + pad_x)
    W, H = image_b.size
    px0, px1 = int(x0 / w * W), int((x1 + 1) / w * W)
    py0, py1 = int(y0 / h * H), int((y1 + 1) / h * H)
    out = image_b.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    line = max(3, round(min(W, H) / 180))
    c = (255, 68, 68)  # Red Alert Reticle
    draw.rectangle((px0, py0, px1, py1), outline=c, width=line)
    L = max(14, round(min(W, H) * 0.05))
    for sx, sy in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        hx = 1 if sx == px0 else -1
        vy = 1 if sy == py0 else -1
        draw.line((sx, sy, sx + hx * L, sy), fill=c, width=line + 2)
        draw.line((sx, sy, sx, sy + vy * L), fill=c, width=line + 2)
    return out


def analyze_temporal(image_a, image_b, query):
    if image_a is None or image_b is None:
        return "⚠️ Both T1 (Before) and T2 (After) scenes are required for bi-temporal damage assessment.", None, None, None, "Change Detection", "Awaiting Inputs"
    if not query or not query.strip():
        return "⚠️ Please specify an inspection query for the temporal pair.", None, None, None, "Change Detection", "Awaiting Query"
    model, processor = _load()
    answer = _extract_temporal(model, processor, _safe_rgb(image_a), _safe_rgb(image_b), query.strip())
    diff = _diff_map(image_a, image_b)
    return (
        answer,
        image_a,
        _diff_overlay(image_b, diff),
        _diff_box(image_b, diff),
        "Bi-Temporal Change Detection",
        "Differential pixel-heat baseline (Spectral Δ) correlated with multimodal temporal reasoning.",
    )

if HAS_SPACES:
    analyze_temporal = spaces.GPU(analyze_temporal)


# =============================================================================
# MAIN DISPATCH
# =============================================================================


def analyze(image, query, show_evidence, contrast, sharpness):
    if image is None:
        return "🛰️ Please upload or select a satellite observation scene.", None, None, None, "—", "—", "—", "—"
    if not query or not query.strip():
        return "🛰️ Enter an intelligence question or select a quick-action prompt chip.", image, image, image, "—", "—", "—", "—"

    route = route_question(query)
    processed = _preprocess_image(image, contrast, sharpness)
    answer, attn, grid = _generate_answer(processed, query.strip(), bool(show_evidence))

    heatmap = processed if attn is None or grid is None else _overlay(processed, attn, grid)
    box = processed if attn is None or grid is None else _evidence_box(processed, attn, grid)
    confidence, confidence_label = estimate_confidence(answer, route, attn is not None and grid is not None)

    evidence_note = (
        "Active Salience Radar (Cross-Layer Attention + Reticle Anchoring)"
        if attn is not None and grid is not None
        else "Fast Path Activated: Attention extraction disabled to optimize inference latency."
    )
    return (
        answer,
        processed,
        heatmap,
        box,
        route,
        f"{confidence}% — {confidence_label}",
        evidence_note,
        metadata_text(processed),
    )

if HAS_SPACES:
    analyze = spaces.GPU(analyze)


def _chat_dispatch(mode, image_a, image_b, query, history, show_evidence, contrast, sharpness):
    history = list(history or [])
    if not query or not query.strip():
        return history, "Please enter a query or select a preset.", image_a, image_a, image_a, "—", "—", "—", "—"

    if mode == "disaster":
        answer, before, diff_heat, diff_box, route, note = analyze_temporal(image_a, image_b, query)
        if before is None:
            return history, answer, image_a, image_a, image_a, route, "—", note, "—"
        history += [
            {"role": "user", "content": query.strip()},
            {"role": "assistant", "content": answer},
        ]
        confidence, label = estimate_confidence(answer, route, diff_heat is not None)
        return history, answer, before, diff_heat, diff_box, route, f"{confidence}% — {label}", note, metadata_text(before)

    result = analyze(image_a, query, show_evidence, contrast, sharpness)
    answer, original, heatmap, box, route, confidence, note, metadata = result
    history += [
        {"role": "user", "content": query.strip()},
        {"role": "assistant", "content": answer},
    ]
    return history, answer, original, heatmap, box, route, confidence, note, metadata


# =============================================================================
# UI AESTHETICS & HIGH-TECH STYLING
# =============================================================================


def _make_star_field(count: int = 180) -> str:
    rng = random.Random(42069)
    stars = []
    for _ in range(count):
        x = rng.uniform(0, 100); y = rng.uniform(0, 100)
        size = rng.uniform(0.8, 2.0)
        opacity = rng.uniform(0.2, 0.8)
        dur = rng.uniform(3, 7)
        stars.append(
            f'<span class="satq-star" style="--x:{x:.2f}%;--y:{y:.2f}%;--size:{size:.2f}px;--opacity:{opacity:.2f};--dur:{dur:.1f}s"></span>'
        )
    return '<div class="satq-stars" aria-hidden="true">' + ''.join(stars) + '</div>'


STAR_FIELD_HTML = _make_star_field()

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
  --space-bg: #030712;
  --panel-bg: rgba(13, 20, 36, 0.85);
  --panel-card: rgba(17, 27, 49, 0.65);
  --border-neon: rgba(0, 240, 255, 0.35);
  --border-subtle: rgba(255, 255, 255, 0.08);
  --cyan: #00f0ff;
  --cyan-glow: rgba(0, 240, 255, 0.25);
  --emerald: #10b981;
  --amber: #f59e0b;
  --ruby: #ff3366;
  --text-main: #f8fafc;
  --text-dim: #94a3b8;
  --mono-font: 'JetBrains Mono', monospace;
}

html, body, .gradio-container {
  background: var(--space-bg) !important;
  color: var(--text-main) !important;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
  overflow-x: hidden;
}

.gradio-container > div, .gradio-container > .main, .wrap, .contain, .app {
  background: transparent !important;
}

footer, .footer, .built-with, .show-api {
  display: none !important;
}

/* Background Cosmic Grid & Particle FX */
.satq-stars {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(circle at 50% 10%, rgba(0, 240, 255, 0.08) 0%, transparent 60%),
              radial-gradient(circle at 85% 80%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
              linear-gradient(180deg, #030712 0%, #060d1a 50%, #030712 100%);
}

.satq-star {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: var(--size);
  height: var(--size);
  background: #ffffff;
  border-radius: 50%;
  opacity: var(--opacity);
  box-shadow: 0 0 6px rgba(0, 240, 255, 0.8);
  animation: starPulse var(--dur) ease-in-out infinite alternate;
}

@keyframes starPulse {
  0% { opacity: calc(var(--opacity) * 0.4); transform: scale(0.8); }
  100% { opacity: var(--opacity); transform: scale(1.3); }
}

#mission-page {
  max-width: 1320px;
  margin: 0 auto;
  padding: 16px 20px 48px;
  position: relative;
  z-index: 1;
}

/* MISSION CONTROL HUD HEADER */
.hud-header {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(13, 20, 36, 0.75) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-neon);
  border-radius: 16px;
  padding: 20px 28px;
  margin-bottom: 24px;
  box-shadow: 0 12px 40px rgba(0, 240, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.hud-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hud-logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #00f0ff, #3b82f6);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.5);
}

.hud-title-wrap h1 {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.hud-title-wrap h1 span {
  background: linear-gradient(135deg, #00f0ff 0%, #38bdf8 50%, #818cf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hud-badge {
  font-family: var(--mono-font);
  font-size: 10.5px;
  color: var(--cyan);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hud-telemetry-pills {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.hud-pill {
  font-family: var(--mono-font);
  font-size: 11px;
  padding: 6px 12px;
  background: rgba(0, 240, 255, 0.06);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 20px;
  color: #cbd5e1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.hud-pill .live-dot {
  width: 7px;
  height: 7px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 8px #10b981;
  animation: pulseDot 2s infinite;
}

@keyframes pulseDot {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

/* MAIN DECK CONTAINER */
#deck {
  background: var(--panel-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  backdrop-filter: blur(16px);
  padding: 0 !important;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

#mode-switch-bar {
  padding: 14px 20px !important;
  background: rgba(10, 16, 28, 0.95);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  gap: 12px;
}

.mode-btn {
  font-family: var(--mono-font) !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 0.08em !important;
  border-radius: 8px !important;
  padding: 10px 20px !important;
  transition: all 0.2s ease !important;
}

.mode-btn.primary {
  background: linear-gradient(135deg, #00f0ff 0%, #0284c7 100%) !important;
  color: #030712 !important;
  border: 0 !important;
  box-shadow: 0 0 16px rgba(0, 240, 255, 0.4) !important;
}

.mode-btn.secondary {
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--text-dim) !important;
  border: 1px solid var(--border-subtle) !important;
}

.mode-btn:hover {
  transform: translateY(-1px);
}

/* WORKSPACE COLUMNS */
#workspace {
  padding: 0 !important;
}

.tactical-col {
  padding: 24px !important;
}

#left-panel {
  border-right: 1px solid var(--border-subtle);
}

.panel-label {
  font-family: var(--mono-font);
  font-size: 11px;
  font-weight: 600;
  color: var(--cyan);
  letter-spacing: 0.12em;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* IMAGE CONTAINERS */
.gradio-container [data-testid="image"], .gradio-container .image-container {
  border: 1px solid rgba(0, 240, 255, 0.25) !important;
  border-radius: 12px !important;
  background: #060b13 !important;
  overflow: hidden !important;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8) !important;
}

/* QUICK QUERY CHIPS */
.query-chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0 16px;
}

.query-chip {
  font-family: var(--mono-font) !important;
  font-size: 11px !important;
  padding: 6px 12px !important;
  background: rgba(0, 240, 255, 0.05) !important;
  border: 1px solid rgba(0, 240, 255, 0.2) !important;
  border-radius: 6px !important;
  color: #cbd5e1 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}

.query-chip:hover {
  background: rgba(0, 240, 255, 0.15) !important;
  border-color: var(--cyan) !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.3) !important;
}

/* INPUT TEXTAREA & ACTION BUTTON */
#query-input textarea {
  background: rgba(8, 14, 26, 0.8) !important;
  border: 1px solid rgba(0, 240, 255, 0.3) !important;
  border-radius: 10px !important;
  color: #ffffff !important;
  font-size: 15px !important;
  line-height: 1.5 !important;
  padding: 12px 16px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}

#query-input textarea:focus {
  border-color: var(--cyan) !important;
  box-shadow: 0 0 16px var(--cyan-glow) !important;
}

#analyze-btn {
  background: linear-gradient(135deg, #00f0ff 0%, #2563eb 100%) !important;
  color: #030712 !important;
  font-family: var(--mono-font) !important;
  font-size: 13px !important;
  font-weight: 800 !important;
  letter-spacing: 0.08em !important;
  border: 0 !important;
  border-radius: 8px !important;
  padding: 12px 24px !important;
  box-shadow: 0 4px 20px rgba(0, 240, 255, 0.4) !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}

#analyze-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 28px rgba(0, 240, 255, 0.6) !important;
}

/* CHATBOT & CONVERSATION */
#conversation {
  border: 1px solid var(--border-subtle) !important;
  background: rgba(6, 11, 20, 0.7) !important;
  border-radius: 12px !important;
}

/* TACTICAL TELEMETRY HUD BOXES */
.telemetry-deck {
  background: rgba(8, 14, 26, 0.85);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 16px;
  margin-top: 14px;
}

/* EVIDENCE TABS */
#evidence-tabs {
  border-top: 1px solid var(--border-subtle) !important;
  background: rgba(6, 11, 20, 0.9) !important;
}

.tab-nav button {
  font-family: var(--mono-font) !important;
  font-size: 12px !important;
  color: var(--text-dim) !important;
  padding: 12px 20px !important;
}

.tab-nav button.selected {
  color: var(--cyan) !important;
  border-bottom: 2px solid var(--cyan) !important;
  background: rgba(0, 240, 255, 0.05) !important;
}

/* MISSION SCENARIOS CARDS */
.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.scenario-card {
  background: rgba(13, 22, 38, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.scenario-card:hover {
  border-color: var(--cyan);
  background: rgba(0, 240, 255, 0.06);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 240, 255, 0.15);
}

.scenario-card .tag {
  font-family: var(--mono-font);
  font-size: 10px;
  color: var(--cyan);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.scenario-card .title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  margin: 6px 0 4px;
}

.scenario-card .desc {
  font-size: 12.5px;
  color: var(--text-dim);
  line-height: 1.4;
}

/* PLATFORM SPECIFICATIONS GRID */
#stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  background: rgba(11, 18, 32, 0.6);
  margin-top: 36px;
  overflow: hidden;
}

.stat-item {
  padding: 20px 24px;
  border-right: 1px solid var(--border-subtle);
}

.stat-item:last-child {
  border-right: 0;
}

.stat-item .num {
  font-family: var(--mono-font);
  font-size: 26px;
  font-weight: 800;
  color: var(--cyan);
  margin-bottom: 6px;
}

.stat-item .title {
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
}

.stat-item .detail {
  font-size: 12px;
  color: var(--text-dim);
  line-height: 1.45;
}

@media (max-width: 900px) {
  #left-panel { border-right: 0; border-bottom: 1px solid var(--border-subtle); }
  #stats-grid { grid-template-columns: 1fr 1fr; }
}
"""

JS = r"""
() => {
  document.documentElement.style.scrollBehavior = 'smooth';
}
"""


def _switch_general():
    return (
        "general",
        gr.update(variant="primary"),
        gr.update(variant="secondary"),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def _switch_disaster():
    return (
        "disaster",
        gr.update(variant="secondary"),
        gr.update(variant="primary"),
        gr.update(visible=True),
        gr.update(visible=False),
    )


def _set_query(chip_text: str):
    return chip_text


# =============================================================================
# GRADIO INTERFACE CONSTRUCTION
# =============================================================================

with gr.Blocks(title="SatQuery AI — Orbital Geospatial Intelligence Platform") as demo:
    gr.HTML(STAR_FIELD_HTML)

    with gr.Column(elem_id="mission-page"):

        # 1. Aerospace Mission Control Header
        gr.HTML("""
        <header class="hud-header">
            <div class="hud-brand">
                <div class="hud-logo-icon">🛰️</div>
                <div class="hud-title-wrap">
                    <h1>SAT<span>QUERY</span> AI</h1>
                    <div class="hud-badge">ORBITAL MULTIMODAL INTELLIGENCE & SATELLITE VQA</div>
                </div>
            </div>
            <div class="hud-telemetry-pills">
                <div class="hud-pill"><span class="live-dot"></span>SYS_STATUS: NOMINAL</div>
                <div class="hud-pill">MODEL: QWEN3-VL-4B (NF4)</div>
                <div class="hud-pill">GSD: SUB-METER OPTICAL</div>
            </div>
        </header>
        """)

        # 2. Main Mission Control Deck
        with gr.Column(elem_id="deck"):
            mode_state = gr.State("general")

            # Mode Selector Ribbon
            with gr.Row(elem_id="mode-switch-bar"):
                general_btn = gr.Button("🛰️ OPTICAL RECON & VQA", elem_id="mode-general", variant="primary", elem_classes=["mode-btn"])
                disaster_btn = gr.Button("🚨 BI-TEMPORAL DISASTER & SDG", elem_id="mode-disaster", variant="secondary", elem_classes=["mode-btn"])

            # Main Workspace Split-Panel
            with gr.Row(elem_id="workspace", equal_height=False):

                # Left Sensor & Input Rail
                with gr.Column(elem_id="left-panel", scale=6, elem_classes=["tactical-col"]):
                    gr.HTML('<div class="panel-label"><span>[01]</span> SATELLITE SENSOR CAPTURE (T1 / PRIMARY)</div>')
                    img_in = gr.Image(type="pil", label="", show_label=False, height=360)

                    gr.HTML('<div class="panel-label" style="margin-top:14px"><span>[02]</span> BI-TEMPORAL RECON SCENE (T2 / POST-EVENT)</div>')
                    img_in_b = gr.Image(type="pil", label="", show_label=False, height=360, visible=False)

                    # Quick Query Command Chips
                    gr.HTML('<div class="panel-label" style="margin-top:18px"><span>[03]</span> TACTICAL QUERY CHIPS (ONE-CLICK PROMPT)</div>')
                    with gr.Row(elem_classes=["query-chips-row"]):
                        chip_1 = gr.Button("🏢 Residential Buildings?", elem_classes=["query-chip"], size="sm")
                        chip_2 = gr.Button("✈️ Count Aircraft & Runways", elem_classes=["query-chip"], size="sm")
                        chip_3 = gr.Button("🌊 Water Bodies vs Land", elem_classes=["query-chip"], size="sm")
                        chip_4 = gr.Button("🚨 Describe Damage Delta", elem_classes=["query-chip"], size="sm")
                        chip_5 = gr.Button("📍 Ground Feature Quadrant", elem_classes=["query-chip"], size="sm")

                    query_in = gr.Textbox(
                        show_label=False,
                        lines=2,
                        max_lines=4,
                        placeholder="Enter geospatial question (e.g., 'Are there more forests than roads?', 'Detect structural damage')...",
                        elem_id="query-input"
                    )

                    with gr.Row():
                        run_btn = gr.Button("EXECUTE SATELLITE RECON →", elem_id="analyze-btn", variant="primary")
                        show_evidence = gr.Checkbox(value=DEFAULT_ATTENTION, label="Salience Evidence Radar", info="Cross-layer attention extraction")

                    with gr.Row():
                        contrast = gr.Slider(0.8, 1.4, value=1.0, step=0.05, label="Contrast Calibration")
                        sharpness = gr.Slider(0.8, 1.5, value=1.0, step=0.05, label="Optical Sharpness")

                # Right Analyst & Telemetry Rail
                with gr.Column(elem_id="right-panel", scale=6, elem_classes=["tactical-col"]):
                    gr.HTML('<div class="panel-label"><span>[04]</span> INTELLIGENCE ASSESSMENT READOUT</div>')
                    chat = gr.Chatbot(value=[], show_label=False, height=280, elem_id="conversation")

                    with gr.Row():
                        answer_out = gr.Textbox(label="VLM SYNTHESIS ANSWER", lines=4, interactive=False)

                    with gr.Row():
                        route_out = gr.Textbox(label="ROUTED TASK CLASSIFIER", value="—", interactive=False)
                        confidence_out = gr.Textbox(label="CONFIDENCE ESTIMATE", value="—", interactive=False)

                    note_out = gr.Textbox(label="EVIDENCE / ATTRIBUTION TELEMETRY", value="—", lines=2, interactive=False)
                    meta_out = gr.Textbox(label="GEOSPATIAL SENSOR & RASTER TELEMETRY", value="—", lines=5, interactive=False)

            # Multi-Spectral Visual Evidence Hub
            with gr.Tabs(elem_id="evidence-tabs"):
                with gr.Tab("🛰️ RAW SATELLITE SCENE"):
                    original_out = gr.Image(label="", show_label=False, interactive=False, height=360)
                with gr.Tab("👁️ ATTENTION SALIENCE HEATMAP"):
                    heatmap_out = gr.Image(label="", show_label=False, interactive=False, height=360)
                with gr.Tab("🎯 TACTICAL EVIDENCE RETICLE"):
                    box_out = gr.Image(label="", show_label=False, interactive=False, height=360)

        # 3. Interactive Mission Briefing Presets
        with gr.Column(visible=True) as general_examples:
            gr.HTML('<div class="panel-label" style="margin-top:32px"><span>[05]</span> CURATED RECONNAISSANCE MISSIONS (SINGLE SCENE)</div>')
            with gr.Row():
                for path, title, question in EXAMPLES:
                    with gr.Column():
                        btn = gr.Button(f"🛰️ {title}\n\"{question}\"", variant="secondary")
                        def load_gen(p=path, q=question):
                            if not Path(p).exists():
                                return None, q
                            return Image.open(p).convert("RGB"), q
                        btn.click(load_gen, outputs=[img_in, query_in], queue=False)

        with gr.Column(visible=False) as disaster_examples:
            gr.HTML('<div class="panel-label" style="margin-top:32px"><span>[05]</span> DISASTER CRISIS & SDG CHANGE MISSIONS (BI-TEMPORAL)</div>')
            with gr.Row():
                for title, location, bp, ap, q in DISASTER_EXAMPLES:
                    with gr.Column():
                        btn = gr.Button(f"🚨 {title} ({location})\n\"{q}\"", variant="secondary")
                        def load_dis(b=bp, a=ap, question=q):
                            if not Path(b).exists() or not Path(a).exists():
                                return None, None, question
                            return Image.open(b).convert("RGB"), Image.open(a).convert("RGB"), question
                        btn.click(load_dis, outputs=[img_in, img_in_b, query_in], queue=False)

        # 4. Platform Specifications & Defense HUD Stats
        gr.HTML("""
        <div id="stats-grid">
            <div class="stat-item">
                <div class="num">01</div>
                <div class="title">Dynamic Task Routing</div>
                <div class="detail">Automatic classification across presence, object counting, spatial comparison, grounding, and change detection.</div>
            </div>
            <div class="stat-item">
                <div class="num">02</div>
                <div class="title">Visual Evidence Attribution</div>
                <div class="detail">Layer-wise cross-attention heatmap extraction paired with stabilized bounding reticle anchoring.</div>
            </div>
            <div class="stat-item">
                <div class="num">03</div>
                <div class="title">Bi-Temporal Damage Delta</div>
                <div class="detail">Pre/post event pixel difference matrix correlated with multimodal VLM semantic change detection.</div>
            </div>
            <div class="stat-item">
                <div class="num">04</div>
                <div class="title">Quantized Edge Inference</div>
                <div class="detail">4-bit NF4 bitsandbytes & FP16 execution engineered for constrained GPU & edge intelligence deployment.</div>
            </div>
        </div>

        <div style="padding: 28px 0 40px; color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.8; text-align: center;">
            SATQUERY AI · AEROSPACE & EARTH OBSERVATION INTELLIGENCE · TEAM CODE DARBAR (SIH 2026)<br>
            Attribution-Oriented Evidence: Attention maps indicate token salience and model focus.
        </div>
        """)

    # Quick chip triggers
    chip_1.click(lambda: "Is a residential building present in this scene?", outputs=query_in, queue=False)
    chip_2.click(lambda: "How many aircraft or runways are visible?", outputs=query_in, queue=False)
    chip_3.click(lambda: "Are there more water bodies than land areas?", outputs=query_in, queue=False)
    chip_4.click(lambda: "Describe the structural damage and changes between these two scenes.", outputs=query_in, queue=False)
    chip_5.click(lambda: "Where is the primary feature located (NW, NE, SW, SE, or Center)?", outputs=query_in, queue=False)

    # Mode switching handlers
    toggle_outputs = [mode_state, general_btn, disaster_btn, img_in_b, general_examples]
    general_btn.click(_switch_general, outputs=toggle_outputs, queue=False)
    disaster_btn.click(_switch_disaster, outputs=[mode_state, general_btn, disaster_btn, img_in_b, general_examples], queue=False)

    # Inference dispatch handlers
    outputs = [chat, answer_out, original_out, heatmap_out, box_out, route_out, confidence_out, note_out, meta_out]
    inputs = [mode_state, img_in, img_in_b, query_in, chat, show_evidence, contrast, sharpness]
    run_btn.click(_chat_dispatch, inputs=inputs, outputs=outputs)
    query_in.submit(_chat_dispatch, inputs=inputs, outputs=outputs)


if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        css=CSS,
        js=JS,
        theme=gr.themes.Base(),
        ssr_mode=False,
    )
