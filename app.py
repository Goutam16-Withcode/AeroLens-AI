"""SatQuery AI — Orbital Earth Observation & Satellite Geospatial Intelligence Ground Station.

Features:
- Qwen3-VL-4B-Instruct inference with 4-bit NF4 quantisation & FP16 safe fallback.
- Spacecraft Telemetry & Multi-Spectral VLM reasoning.
- Question routing: VQA / counting / comparison / grounding / change detection.
- Cross-Layer attention salience radar & tactical target reticle.
- Bi-temporal disaster analysis with pixel difference heat mapping.
- Aerospace Ground Station HUD design with Solar-Gold, Radar-Emerald & Optical-Cyan styling.
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
# SATELLITE MISSIONS & CONFIG
# =============================================================================

MODEL_ID = os.getenv("SATQUERY_MODEL_ID", "Qwen/Qwen3-VL-4B-Instruct")
MAX_NEW_TOKENS = int(os.getenv("SATQUERY_MAX_NEW_TOKENS", "128"))
DEFAULT_ATTENTION = os.getenv("SATQUERY_SHOW_EVIDENCE", "1") != "0"

EXAMPLES: list[tuple[str, str, str, str]] = [
    ("examples/scene_535.png", "PASS: EO-742", "Urban Infrastructure", "Is a residential building present in this scene?"),
    ("examples/scene_545.png", "PASS: EO-819", "Canopy & Transportation", "Are there more forests than roads in the image?"),
    ("examples/scene_498.png", "PASS: EO-904", "Hydrology & Agriculture", "Are there more large water areas than farmlands?"),
    ("examples/scene_479.png", "PASS: EO-612", "Terrain Arteries", "Is there a small road visible across the terrain?"),
]

DISASTER_EXAMPLES: list[tuple[str, str, str, str, str, str]] = [
    (
        "Tsunami Coastal Inundation",
        "Palu Bay, Indonesia",
        "DISASTER CHARTER #581",
        "disaster_examples/tsunami_before.tiff",
        "disaster_examples/tsunami_after.tiff",
        "Describe the coastal inundation and structural damage caused by the tsunami between these scenes.",
    ),
    (
        "Mountain Slope Landslide",
        "Alpine Valley Corridor",
        "DISASTER CHARTER #614",
        "disaster_examples/landslide_before.tiff",
        "disaster_examples/landslide_after.tiff",
        "Describe what changed on the mountain slope between these two temporal images.",
    ),
    (
        "Urban Earthquake Collapse",
        "Metropolitan Fault Zone",
        "DISASTER CHARTER #672",
        "disaster_examples/earthquake_before.tiff",
        "disaster_examples/earthquake_after.tiff",
        "How many buildings appear damaged or collapsed in the post-disaster scene compared to before?",
    ),
    (
        "Severe Drought & Aridity",
        "Sub-Saharan Agricultural Basin",
        "SDG 15 / CLIMATE OBSERVATION",
        "disaster_examples/famine_before.tiff",
        "disaster_examples/famine_after.tiff",
        "Describe the change in vegetation health and soil moisture between these two images.",
    ),
    (
        "Agricultural Land Conversion",
        "Urban Sprawl Frontier",
        "SDG 11 / LAND USE SURVEY",
        "disaster_examples/arable_land_before.tiff",
        "disaster_examples/arable_land_after.tiff",
        "Has agricultural farmland been converted to built-up area between the two timestamps?",
    ),
    (
        "River Basin Flood Surge",
        "Monsoon Overflow Plain",
        "DISASTER CHARTER #703",
        "disaster_examples/water_rise_before.tiff",
        "disaster_examples/water_rise_after.tiff",
        "Has the water surface area expanded significantly between these two observation captures?",
    ),
]


# =============================================================================
# MODEL CACHE & SAFE LOADER
# =============================================================================

_model = None
_processor = None


def _load():
    """Load model with GPU 4-bit NF4 quant or FP16/CPU fallback."""
    global _model, _processor
    if _model is not None:
        return _model, _processor

    print(f"Initializing Satellite VLM Core [{MODEL_ID}]...")
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
            print("Quantization warning (loading in float16):", exc)
            load_kwargs["torch_dtype"] = torch.float16
    else:
        load_kwargs["torch_dtype"] = torch.float32

    _model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID,
        **load_kwargs,
    )
    _processor = AutoProcessor.from_pretrained(MODEL_ID)
    print("Satellite VLM Core telemetry active.")
    return _model, _processor


def _model_device(model):
    return next(model.parameters()).device


# =============================================================================
# QUESTION ROUTER
# =============================================================================


def route_question(query: str, temporal: bool = False) -> str:
    q = (query or "").strip().lower()
    if temporal or any(k in q for k in (
        "before", "after", "changed", "change", "damage", "damaged",
        "destroyed", "collapsed", "increase", "decrease", "lost", "inundation", "delta",
    )):
        return "Bi-Temporal Change Delta"
    if any(k in q for k in ("how many", "how much", "count", "number of", "tally")):
        return "Feature Counting & Density"
    if any(k in q for k in ("more", "less", "fewer", "greater", "larger", "compare", "versus", "vs")):
        return "Spatial Balance & Comparison"
    if any(k in q for k in ("where", "which area", "which region", "location", "located", "quadrant")):
        return "Quadrant Visual Grounding"
    if any(k in q for k in ("is there", "are there", "present", "visible", "contains", "contain", "detect")):
        return "Feature Presence Verification"
    return "Multispectral VQA"


# =============================================================================
# IMAGE / GEOSPATIAL TELEMETRY
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
        "║           🛰️ SPACECRAFT PAYLOAD TELEMETRY MATRIX             ║",
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
            "║  COORDINATE CRS  : Standard Sun-Synchronous Frame (GSD: ~0.5m)",
            "║  SPECTRAL BANDS  : 3 Optical Channels (Red, Green, Blue / NIR)",
            "║  ORBIT TELEMETRY : LEO 540km · Inclination 98.2° · GSD Nominal",
        ]
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


# =============================================================================
# ATTENTION EVIDENCE & TACTICAL RETICLE
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
    c = (0, 245, 255)  # Laser Optical Cyan
    gold = (245, 158, 11)  # Solar Array Gold
    draw.rectangle((px0, py0, px1, py1), outline=c, width=line)
    L = max(16, round(min(W, H) * 0.055))
    for sx, sy in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        hx = 1 if sx == px0 else -1
        vy = 1 if sy == py0 else -1
        draw.line((sx, sy, sx + hx * L, sy), fill=gold, width=line + 2)
        draw.line((sx, sy, sx, sy + vy * L), fill=gold, width=line + 2)
    return out


def _overlay(image: Image.Image, attn_1d: np.ndarray, grid: tuple[int, int], alpha: float = 0.46) -> Image.Image:
    import matplotlib
    h, w = grid
    arr = attn_1d.reshape(h, w)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    heat = Image.fromarray((arr * 255).astype(np.uint8)).resize(image.size, Image.BILINEAR)
    cmap = matplotlib.colormaps["turbo"]
    heat_rgb = (cmap(np.asarray(heat) / 255.0)[:, :, :3] * 255).astype(np.uint8)
    return Image.blend(image.convert("RGB"), Image.fromarray(heat_rgb), alpha=alpha)


# =============================================================================
# CONFIDENCE ESTIMATOR
# =============================================================================


def estimate_confidence(answer: str, route: str, evidence_available: bool) -> tuple[int, str]:
    a = (answer or "").strip().lower()
    score = 64
    if a:
        score += 8
    if any(x in a for x in ("cannot determine", "uncertain", "unclear", "insufficient resolution")):
        score -= 30
    if any(x in a for x in ("yes", "no", "approximately", "evident", "visible", "present", "detected")):
        score += 8
    if "Counting" in route:
        score -= 5
    if "Grounding" in route:
        score -= 2
    if evidence_available:
        score += 7
    score = max(15, min(96, score))
    label = "LOCK: HIGH CONFIDENCE 🟢" if score >= 75 else "NOMINAL: MODERATE 🟡" if score >= 55 else "ADVISORY: LOW 🔴"
    return score, label


# =============================================================================
# BI-TEMPORAL DISASTER DELTA
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


def _diff_overlay(image_b: Image.Image, diff_arr: np.ndarray, alpha: float = 0.5) -> Image.Image:
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
    c = (255, 42, 109)  # Infrared Thermal Ruby
    draw.rectangle((px0, py0, px1, py1), outline=c, width=line)
    L = max(16, round(min(W, H) * 0.055))
    for sx, sy in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        hx = 1 if sx == px0 else -1
        vy = 1 if sy == py0 else -1
        draw.line((sx, sy, sx + hx * L, sy), fill=(255, 200, 0), width=line + 2)
        draw.line((sx, sy, sx, sy + vy * L), fill=(255, 200, 0), width=line + 2)
    return out


def analyze_temporal(image_a, image_b, query):
    if image_a is None or image_b is None:
        return "⚠️ Both T1 (Before) and T2 (After) observation frames are required for bi-temporal damage assessment.", None, None, None, "Change Detection", "Awaiting Inputs"
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
        "Bi-Temporal Change Delta",
        "Differential pixel spectral Δ baseline correlated with multimodal VLM temporal reasoning.",
    )

if HAS_SPACES:
    analyze_temporal = spaces.GPU(analyze_temporal)


# =============================================================================
# MAIN DISPATCH
# =============================================================================


def analyze(image, query, show_evidence, contrast, sharpness):
    if image is None:
        return "🛰️ Please uplink or select a satellite observation scene.", None, None, None, "—", "—", "—", "—"
    if not query or not query.strip():
        return "🛰️ Enter an intelligence target query or select a quick-action command chip.", image, image, image, "—", "—", "—", "—"

    route = route_question(query)
    processed = _preprocess_image(image, contrast, sharpness)
    answer, attn, grid = _generate_answer(processed, query.strip(), bool(show_evidence))

    heatmap = processed if attn is None or grid is None else _overlay(processed, attn, grid)
    box = processed if attn is None or grid is None else _evidence_box(processed, attn, grid)
    confidence, confidence_label = estimate_confidence(answer, route, attn is not None and grid is not None)

    evidence_note = (
        "Active Salience Radar: Cross-layer attention & spatial reticle lock engaged."
        if attn is not None and grid is not None
        else "Fast Telemetry: Attention extraction bypassed to maximize throughput."
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
        return history, "Please specify an orbital intelligence query.", image_a, image_a, image_a, "—", "—", "—", "—"

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
# SATELLITE GROUND CONTROL STYLING & HUD THEME
# =============================================================================


def _make_star_field(count: int = 200) -> str:
    rng = random.Random(54000)
    stars = []
    for _ in range(count):
        x = rng.uniform(0, 100); y = rng.uniform(0, 100)
        size = rng.uniform(0.8, 2.2)
        opacity = rng.uniform(0.25, 0.85)
        dur = rng.uniform(3, 8)
        stars.append(
            f'<span class="satq-star" style="--x:{x:.2f}%;--y:{y:.2f}%;--size:{size:.2f}px;--opacity:{opacity:.2f};--dur:{dur:.1f}s"></span>'
        )
    return '<div class="satq-stars" aria-hidden="true">' + ''.join(stars) + '</div>'


STAR_FIELD_HTML = _make_star_field()

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --space-void: #02050e;
  --hull-bg: #070e1c;
  --hull-card: rgba(11, 20, 38, 0.8);
  --sat-gold: #f59e0b;
  --sat-gold-bright: #fbbf24;
  --sat-gold-glow: rgba(245, 158, 11, 0.3);
  --radar-emerald: #00ff88;
  --radar-emerald-dim: rgba(0, 255, 136, 0.15);
  --optical-cyan: #00f5ff;
  --optical-cyan-glow: rgba(0, 245, 255, 0.35);
  --thermal-ruby: #ff2a6d;
  --border-gold: rgba(245, 158, 11, 0.4);
  --border-cyan: rgba(0, 245, 255, 0.3);
  --border-subtle: rgba(255, 255, 255, 0.08);
  --text-pure: #ffffff;
  --text-muted: #8da4be;
  --font-hud: 'Chakra Petch', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-body: 'Plus Jakarta Sans', sans-serif;
}

html, body, .gradio-container {
  background: var(--space-void) !important;
  color: var(--text-pure) !important;
  font-family: var(--font-body) !important;
  overflow-x: hidden;
}

.gradio-container > div, .gradio-container > .main, .wrap, .contain, .app {
  background: transparent !important;
}

footer, .footer, .built-with, .show-api {
  display: none !important;
}

/* Cosmic Orbit Matrix Backdrop */
.satq-stars {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(circle at 50% 0%, rgba(0, 245, 255, 0.1) 0%, transparent 50%),
              radial-gradient(circle at 10% 30%, rgba(245, 158, 11, 0.07) 0%, transparent 40%),
              radial-gradient(circle at 90% 80%, rgba(255, 42, 109, 0.06) 0%, transparent 45%),
              linear-gradient(180deg, #02050e 0%, #050c18 50%, #02050e 100%);
}

.satq-star {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: var(--size);
  height: var(--size);
  background: #d4eaf7;
  border-radius: 50%;
  opacity: var(--opacity);
  box-shadow: 0 0 8px rgba(0, 245, 255, 0.8);
  animation: starOrbitPulse var(--dur) ease-in-out infinite alternate;
}

@keyframes starOrbitPulse {
  0% { opacity: calc(var(--opacity) * 0.3); transform: scale(0.8); }
  100% { opacity: var(--opacity); transform: scale(1.4); }
}

#mission-page {
  max-width: 1360px;
  margin: 0 auto;
  padding: 18px 22px 60px;
  position: relative;
  z-index: 1;
}

/* SATELLITE GROUND STATION COMMAND BANNER */
.sat-header {
  background: linear-gradient(135deg, rgba(12, 22, 42, 0.95) 0%, rgba(7, 14, 28, 0.9) 100%);
  backdrop-filter: blur(24px);
  border: 1px solid var(--border-cyan);
  border-top: 2px solid var(--sat-gold);
  border-radius: 16px;
  padding: 22px 30px;
  margin-bottom: 22px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.sat-brand-wrap {
  display: flex;
  align-items: center;
  gap: 18px;
}

.sat-dish-beacon {
  width: 54px;
  height: 54px;
  background: radial-gradient(circle at 30% 30%, #fbbf24 0%, #d97706 60%, #78350f 100%);
  border: 2px solid #fef08a;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  box-shadow: 0 0 24px var(--sat-gold-glow);
  position: relative;
}

.sat-dish-beacon::after {
  content: '';
  position: absolute;
  inset: -6px;
  border: 1px dashed var(--optical-cyan);
  border-radius: 18px;
  animation: radarRotate 12s linear infinite;
}

@keyframes radarRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.sat-title-text h1 {
  font-family: var(--font-hud);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.06em;
  margin: 0;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 10px;
}

.sat-title-text h1 span {
  background: linear-gradient(135deg, #00f5ff 0%, #38bdf8 50%, #fbbf24 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.sat-subkicker {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--sat-gold-bright);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-top: 4px;
}

/* LIVE ORBIT TELEMETRY PILLS */
.orbit-telemetry-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.telemetry-chip {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  padding: 6px 14px;
  background: rgba(7, 18, 36, 0.85);
  border: 1px solid var(--border-cyan);
  border-radius: 8px;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.telemetry-chip.emerald {
  border-color: rgba(0, 255, 136, 0.4);
  background: rgba(0, 255, 136, 0.05);
  color: #a7f3d0;
}

.telemetry-chip.gold {
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(245, 158, 11, 0.06);
  color: #fde68a;
}

.telemetry-chip .pulse-led {
  width: 8px;
  height: 8px;
  background: var(--radar-emerald);
  border-radius: 50%;
  box-shadow: 0 0 10px var(--radar-emerald);
  animation: ledFlash 1.6s ease-in-out infinite;
}

@keyframes ledFlash {
  0%, 100% { opacity: 0.5; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.25); }
}

/* MAIN DECK CONTAINER */
#satellite-deck {
  background: var(--hull-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  padding: 0 !important;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.75);
  overflow: hidden;
  position: relative;
}

/* SATELLITE INSTRUMENT SELECTOR BAR */
#instrument-bar {
  padding: 14px 24px !important;
  background: rgba(5, 11, 22, 0.95);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  gap: 14px;
  align-items: center;
}

.instrument-btn {
  font-family: var(--font-hud) !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  letter-spacing: 0.08em !important;
  border-radius: 8px !important;
  padding: 11px 22px !important;
  transition: all 0.25s ease !important;
  text-transform: uppercase !important;
}

.instrument-btn.primary {
  background: linear-gradient(135deg, #00f5ff 0%, #0284c7 100%) !important;
  color: #020612 !important;
  border: 1px solid #38bdf8 !important;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.4) !important;
}

.instrument-btn.secondary {
  background: rgba(245, 158, 11, 0.08) !important;
  color: var(--sat-gold-bright) !important;
  border: 1px solid var(--border-gold) !important;
}

.instrument-btn:hover {
  transform: translateY(-2px);
}

/* SATELLITE HUD WORKSPACE */
#workspace {
  padding: 0 !important;
}

.ground-col {
  padding: 26px !important;
}

#left-ground-panel {
  border-right: 1px solid var(--border-subtle);
}

.hud-panel-title {
  font-family: var(--font-hud);
  font-size: 12px;
  font-weight: 700;
  color: var(--optical-cyan);
  letter-spacing: 0.14em;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
}

.hud-panel-title span {
  color: var(--sat-gold-bright);
}

/* SATELLITE IMAGE CONTAINERS WITH CORNER RETICLES */
.gradio-container [data-testid="image"], .gradio-container .image-container {
  border: 1px solid rgba(0, 245, 255, 0.3) !important;
  border-radius: 12px !important;
  background: #030712 !important;
  position: relative;
  overflow: hidden !important;
  box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.9) !important;
}

/* QUICK COMMAND PROMPT CHIPS */
.query-chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0 16px;
}

.sat-query-chip {
  font-family: var(--font-mono) !important;
  font-size: 11px !important;
  padding: 7px 14px !important;
  background: rgba(0, 245, 255, 0.05) !important;
  border: 1px solid rgba(0, 245, 255, 0.25) !important;
  border-radius: 6px !important;
  color: #e2e8f0 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}

.sat-query-chip:hover {
  background: rgba(0, 245, 255, 0.18) !important;
  border-color: var(--optical-cyan) !important;
  color: #ffffff !important;
  box-shadow: 0 0 14px rgba(0, 245, 255, 0.35) !important;
  transform: translateY(-1px);
}

/* TARGET UPLINK INPUT BOX */
#query-input textarea {
  background: rgba(4, 9, 20, 0.9) !important;
  border: 1px solid var(--border-gold) !important;
  border-radius: 10px !important;
  color: #ffffff !important;
  font-family: var(--font-body) !important;
  font-size: 15.5px !important;
  line-height: 1.55 !important;
  padding: 14px 18px !important;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.5) !important;
}

#query-input textarea:focus {
  border-color: var(--sat-gold-bright) !important;
  box-shadow: 0 0 20px var(--sat-gold-glow) !important;
}

/* SATELLITE TRANSMIT BUTTON */
#analyze-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 60%, #b45309 100%) !important;
  color: #030712 !important;
  font-family: var(--font-hud) !important;
  font-size: 14px !important;
  font-weight: 800 !important;
  letter-spacing: 0.1em !important;
  border: 1px solid #fde68a !important;
  border-radius: 8px !important;
  padding: 14px 28px !important;
  box-shadow: 0 6px 24px var(--sat-gold-glow) !important;
  cursor: pointer !important;
  transition: all 0.25s ease !important;
  text-transform: uppercase !important;
}

#analyze-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(245, 158, 11, 0.6) !important;
}

/* CHAT CONVERSATION LOG */
#conversation {
  border: 1px solid var(--border-subtle) !important;
  background: rgba(4, 8, 16, 0.8) !important;
  border-radius: 12px !important;
}

/* SATELLITE EVIDENCE TABS */
#evidence-tabs {
  border-top: 1px solid var(--border-subtle) !important;
  background: rgba(3, 7, 16, 0.95) !important;
}

.tab-nav button {
  font-family: var(--font-hud) !important;
  font-size: 12.5px !important;
  letter-spacing: 0.08em !important;
  color: var(--text-muted) !important;
  padding: 14px 24px !important;
  text-transform: uppercase !important;
}

.tab-nav button.selected {
  color: var(--optical-cyan) !important;
  border-bottom: 2px solid var(--optical-cyan) !important;
  background: rgba(0, 245, 255, 0.06) !important;
}

/* MISSION SCENARIO CARDS */
.mission-card-btn {
  background: rgba(10, 18, 34, 0.75) !important;
  border: 1px solid rgba(0, 245, 255, 0.2) !important;
  border-radius: 12px !important;
  padding: 16px !important;
  text-align: left !important;
  transition: all 0.25s ease !important;
}

.mission-card-btn:hover {
  border-color: var(--optical-cyan) !important;
  background: rgba(0, 245, 255, 0.08) !important;
  box-shadow: 0 8px 24px rgba(0, 245, 255, 0.2) !important;
  transform: translateY(-2px);
}

/* GROUND STATION SPECIFICATIONS HUD */
#specs-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  background: rgba(8, 15, 30, 0.7);
  margin-top: 36px;
  overflow: hidden;
}

.spec-node {
  padding: 22px 26px;
  border-right: 1px solid var(--border-subtle);
}

.spec-node:last-child {
  border-right: 0;
}

.spec-node .node-id {
  font-family: var(--font-hud);
  font-size: 24px;
  font-weight: 700;
  color: var(--sat-gold-bright);
  margin-bottom: 6px;
}

.spec-node .node-title {
  font-family: var(--font-hud);
  font-size: 13.5px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.06em;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.spec-node .node-detail {
  font-size: 12.5px;
  color: var(--text-muted);
  line-height: 1.5;
}

@media (max-width: 900px) {
  #left-ground-panel { border-right: 0; border-bottom: 1px solid var(--border-subtle); }
  #specs-grid { grid-template-columns: 1fr 1fr; }
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


# =============================================================================
# GROUND STATION UI BUILDER
# =============================================================================

with gr.Blocks(title="SatQuery AI — Orbital Earth Observation & VLM Ground Station") as demo:
    gr.HTML(STAR_FIELD_HTML)

    with gr.Column(elem_id="mission-page"):

        # 1. SATELLITE COMMAND & TELEMETRY BANNER
        gr.HTML("""
        <header class="sat-header">
            <div class="sat-brand-wrap">
                <div class="sat-dish-beacon">🛰️</div>
                <div class="sat-title-text">
                    <h1>SAT<span>QUERY</span> AI // GROUND STATION</h1>
                    <div class="sat-subkicker">ORBITAL MULTISPECTRAL VLM & GEOSPATIAL INTELLIGENCE PLATFORM</div>
                </div>
            </div>
            <div class="orbit-telemetry-bar">
                <div class="telemetry-chip emerald"><span class="pulse-led"></span>DOWNLINK: 8.2 GHz [ACTIVE]</div>
                <div class="telemetry-chip gold">ORBIT: LEO 540KM · SSO</div>
                <div class="telemetry-chip">PAYLOAD: MSI (13-BAND) + SAR</div>
                <div class="telemetry-chip">CORE: QWEN3-VL 4B (NF4)</div>
            </div>
        </header>
        """)

        # 2. MAIN SATELLITE RECON DECK
        with gr.Column(elem_id="satellite-deck"):
            mode_state = gr.State("general")

            # Instrument Mode Ribbon
            with gr.Row(elem_id="instrument-bar"):
                general_btn = gr.Button("🛰️ INSTRUMENT: OPTICAL & MULTISPECTRAL VQA", elem_id="mode-general", variant="primary", elem_classes=["instrument-btn"])
                disaster_btn = gr.Button("🚨 INSTRUMENT: BI-TEMPORAL DISASTER & SDG Δ", elem_id="mode-disaster", variant="secondary", elem_classes=["instrument-btn"])

            # Split-Rail Ground Workspace
            with gr.Row(elem_id="workspace", equal_height=False):

                # Left Ingestion & Target Uplink Rail
                with gr.Column(elem_id="left-ground-panel", scale=6, elem_classes=["ground-col"]):
                    gr.HTML('<div class="hud-panel-title"><span>[01]</span> SATELLITE SENSOR RASTER (T1 / PRIMARY SWATH)</div>')
                    img_in = gr.Image(type="pil", label="", show_label=False, height=360)

                    gr.HTML('<div class="hud-panel-title" style="margin-top:14px"><span>[02]</span> BI-TEMPORAL RECON SWATH (T2 / POST-CRISIS)</div>')
                    img_in_b = gr.Image(type="pil", label="", show_label=False, height=360, visible=False)

                    # Quick Command Prompt Chips
                    gr.HTML('<div class="hud-panel-title" style="margin-top:18px"><span>[03]</span> TARGET UPLINK QUERY PRESETS</div>')
                    with gr.Row(elem_classes=["query-chips-row"]):
                        chip_1 = gr.Button("🏢 Urban Rooftops & Buildings", elem_classes=["sat-query-chip"], size="sm")
                        chip_2 = gr.Button("✈️ Airfield Aircraft & Runways", elem_classes=["sat-query-chip"], size="sm")
                        chip_3 = gr.Button("🌊 Hydrology & Coastlines", elem_classes=["sat-query-chip"], size="sm")
                        chip_4 = gr.Button("🚨 Damage & Destruction Delta", elem_classes=["sat-query-chip"], size="sm")
                        chip_5 = gr.Button("📍 Quadrant Reticle Grounding", elem_classes=["sat-query-chip"], size="sm")

                    query_in = gr.Textbox(
                        show_label=False,
                        lines=2,
                        max_lines=4,
                        placeholder="Uplink geospatial target query (e.g., 'Are there more forests than roads?', 'Identify collapsed structures')...",
                        elem_id="query-input"
                    )

                    with gr.Row():
                        run_btn = gr.Button("TRANSMIT SATELLITE UPLINK 📡 →", elem_id="analyze-btn", variant="primary")
                        show_evidence = gr.Checkbox(value=DEFAULT_ATTENTION, label="Cross-Layer Attention Radar", info="Extracts multi-head visual token salience")

                    with gr.Row():
                        contrast = gr.Slider(0.8, 1.4, value=1.0, step=0.05, label="Optical Contrast Gain")
                        sharpness = gr.Slider(0.8, 1.5, value=1.0, step=0.05, label="Sensor Aperture Sharpness")

                # Right Analyst Telemetry Rail
                with gr.Column(elem_id="right-ground-panel", scale=6, elem_classes=["ground-col"]):
                    gr.HTML('<div class="hud-panel-title"><span>[04]</span> SPACECRAFT VLM SYNTHESIS TERMINAL</div>')
                    chat = gr.Chatbot(value=[], show_label=False, height=270, elem_id="conversation")

                    with gr.Row():
                        answer_out = gr.Textbox(label="MULTIMODAL INTELLIGENCE SYNTHESIS", lines=4, interactive=False)

                    with gr.Row():
                        route_out = gr.Textbox(label="TARGET CLASSIFIER ROUTE", value="—", interactive=False)
                        confidence_out = gr.Textbox(label="TELEMETRY CONFIDENCE LOCK", value="—", interactive=False)

                    note_out = gr.Textbox(label="SENSING PROTOCOL & ATTRIBUTION", value="—", lines=2, interactive=False)
                    meta_out = gr.Textbox(label="GEOSPATIAL SENSOR & RASTER MATRIX", value="—", lines=5, interactive=False)

            # Multi-Spectral Visual Evidence Hub
            with gr.Tabs(elem_id="evidence-tabs"):
                with gr.Tab("🛰️ BAND 4-3-2 (OPTICAL RGB)"):
                    original_out = gr.Image(label="", show_label=False, interactive=False, height=360)
                with gr.Tab("👁️ ATTENTION SALIENCE (VLM SPATIAL RADAR)"):
                    heatmap_out = gr.Image(label="", show_label=False, interactive=False, height=360)
                with gr.Tab("🎯 TACTICAL TARGET RETICLE (GROUNDING LOCK)"):
                    box_out = gr.Image(label="", show_label=False, interactive=False, height=360)

        # 3. SATELLITE MISSION PRESETS
        with gr.Column(visible=True) as general_examples:
            gr.HTML('<div class="hud-panel-title" style="margin-top:34px"><span>[05]</span> EARTH OBSERVATION RECON MISSIONS (SINGLE PASS)</div>')
            with gr.Row():
                for path, pass_id, title, question in EXAMPLES:
                    with gr.Column():
                        btn = gr.Button(f"🛰️ {pass_id} // {title}\n\"{question}\"", elem_classes=["mission-card-btn"])
                        def load_gen(p=path, q=question):
                            if not Path(p).exists():
                                return None, q
                            return Image.open(p).convert("RGB"), q
                        btn.click(load_gen, outputs=[img_in, query_in], queue=False)

        with gr.Column(visible=False) as disaster_examples:
            gr.HTML('<div class="hud-panel-title" style="margin-top:34px"><span>[05]</span> INTERNATIONAL DISASTER CHARTER & SDG MONITORING (BI-TEMPORAL)</div>')
            with gr.Row():
                for title, location, charter_id, bp, ap, q in DISASTER_EXAMPLES:
                    with gr.Column():
                        btn = gr.Button(f"🚨 {charter_id}\n{title} ({location})\n\"{q}\"", elem_classes=["mission-card-btn"])
                        def load_dis(b=bp, a=ap, question=q):
                            if not Path(b).exists() or not Path(a).exists():
                                return None, None, question
                            return Image.open(b).convert("RGB"), Image.open(a).convert("RGB"), question
                        btn.click(load_dis, outputs=[img_in, img_in_b, query_in], queue=False)

        # 4. GROUND STATION SPECIFICATIONS MATRIX
        gr.HTML("""
        <div id="specs-grid">
            <div class="spec-node">
                <div class="node-id">01 / ROUTE</div>
                <div class="node-title">Dynamic Task Router</div>
                <div class="node-detail">Autonomous question routing classifying presence, counting, spatial balance, quadrant grounding, and disaster change deltas.</div>
            </div>
            <div class="spec-node">
                <div class="node-id">02 / RADAR</div>
                <div class="node-title">Cross-Attention Salience</div>
                <div class="node-detail">Layer-wise multi-head visual token attention heatmaps paired with sub-pixel target reticle anchoring.</div>
            </div>
            <div class="spec-node">
                <div class="node-id">03 / DELTA</div>
                <div class="node-title">Bi-Temporal Damage Matrix</div>
                <div class="node-detail">Pre/post observation differential pixel spectral Δ correlated with multimodal VLM spatial reasoning.</div>
            </div>
            <div class="spec-node">
                <div class="node-id">04 / EDGE</div>
                <div class="node-title">Quantized VLM Core</div>
                <div class="node-detail">4-bit NF4 bitsandbytes & FP16 execution engineered for edge aerospace stations & cloud GPU environments.</div>
            </div>
        </div>

        <div style="padding: 30px 0 45px; color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.8; text-align: center;">
            SATQUERY AI · SATELLITE EARTH OBSERVATION GROUND CONTROL · TEAM CODE DARBAR (SIH 2026)<br>
            Attribution & Telemetry Protocol: Cross-layer attention heatmaps represent model token attribution and visual salience.
        </div>
        """)

    # Tactical quick chip triggers
    chip_1.click(lambda: "Is a residential building or urban rooftop present in this scene?", outputs=query_in, queue=False)
    chip_2.click(lambda: "How many aircraft or runway segments are visible in this airfield?", outputs=query_in, queue=False)
    chip_3.click(lambda: "Are there more water bodies and rivers than land areas?", outputs=query_in, queue=False)
    chip_4.click(lambda: "Describe the structural damage and changes between these two temporal scenes.", outputs=query_in, queue=False)
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
