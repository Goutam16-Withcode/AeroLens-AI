"""SatQuery — improved satellite VQA + evidence + bi-temporal analysis.

Features
--------
- Qwen3-VL-4B-Instruct inference with 4-bit quantisation.
- Question routing: VQA / counting / comparison / grounding / change.
- Optional evidence extraction: attention heatmap + stabilized evidence box.
- Bi-temporal disaster analysis with a semantic-safe pixel-difference baseline.
- Lightweight confidence estimate (explicitly a heuristic, not calibrated probability).
- Optional GeoTIFF metadata extraction when rasterio is installed.
- Fast path: attention extraction can be disabled to reduce inference overhead.
- Gradio UI suitable for Hugging Face Spaces.

Project assets expected by default:
    examples/scene_*.png
    disaster_examples/*_before.tiff
    disaster_examples/*_after.tiff

The application does not claim that attention is an object detector. Evidence is
presented as model-attribution / visual-change evidence.
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
# Narrow Gradio/Python 3.12+ cleanup workaround used by the original Space.
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
# CONFIG
# =============================================================================

MODEL_ID = os.getenv("SATQUERY_MODEL_ID", "Qwen/Qwen3-VL-4B-Instruct")
MAX_NEW_TOKENS = int(os.getenv("SATQUERY_MAX_NEW_TOKENS", "128"))
DEFAULT_ATTENTION = os.getenv("SATQUERY_SHOW_EVIDENCE", "1") != "0"

# Keep examples easy to replace with real project assets.
EXAMPLES: list[tuple[str, str]] = [
    ("examples/scene_535.png", "Is a residential building present?"),
    ("examples/scene_545.png", "Are there more forests than roads in the image?"),
    ("examples/scene_498.png", "Are there more large water areas than farmlands?"),
    ("examples/scene_479.png", "Is there a small road?"),
]

DISASTER_EXAMPLES: list[tuple[str, str, str, str]] = [
    (
        "Tsunami — Palu, Indonesia (2018)",
        "disaster_examples/tsunami_before.tiff",
        "disaster_examples/tsunami_after.tiff",
        "Describe the change caused by the tsunami between these two scenes.",
    ),
    (
        "Landslide — example pair",
        "disaster_examples/landslide_before.tiff",
        "disaster_examples/landslide_after.tiff",
        "Describe what changed on the slope between these two images.",
    ),
    (
        "Earthquake — example pair",
        "disaster_examples/earthquake_before.tiff",
        "disaster_examples/earthquake_after.tiff",
        "How many buildings appear damaged or collapsed in the second image compared to the first?",
    ),
    (
        "Drought — example pair",
        "disaster_examples/famine_before.tiff",
        "disaster_examples/famine_after.tiff",
        "Describe the change in vegetation health between these two images.",
    ),
    (
        "Arable land loss — example pair",
        "disaster_examples/arable_land_before.tiff",
        "disaster_examples/arable_land_after.tiff",
        "Has farmland been converted to built-up area between the two images?",
    ),
    (
        "Rising water level — example pair",
        "disaster_examples/water_rise_before.tiff",
        "disaster_examples/water_rise_after.tiff",
        "Has the water area increased between these two images?",
    ),
]


# =============================================================================
# MODEL CACHE
# =============================================================================

_model = None
_processor = None


def _load():
    """Load model and processor exactly once per Space process."""
    global _model, _processor
    if _model is not None:
        return _model, _processor

    print(f"Loading {MODEL_ID}...")
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    _model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID,
        quantization_config=quant,
        device_map="auto",
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
    """Deterministic first-pass router.

    This is deliberately transparent. It is not presented as a learned classifier.
    """
    q = (query or "").strip().lower()
    if temporal or any(k in q for k in (
        "before", "after", "changed", "change", "damage", "damaged",
        "destroyed", "collapsed", "increase", "decrease", "lost",
    )):
        return "change detection"
    if any(k in q for k in ("how many", "how much", "count", "number of")):
        return "counting"
    if any(k in q for k in ("more", "less", "fewer", "greater", "larger", "compare", "versus", "vs")):
        return "comparison"
    if any(k in q for k in ("where", "which area", "which region", "location", "located")):
        return "grounding"
    if any(k in q for k in ("is there", "are there", "present", "visible", "contains", "contain")):
        return "presence"
    return "general VQA"


# =============================================================================
# IMAGE / GEO HELPERS
# =============================================================================


def _safe_rgb(image: Image.Image) -> Image.Image:
    if not isinstance(image, Image.Image):
        raise TypeError("Expected a PIL image")
    return image.convert("RGB")


def _preprocess_image(image: Image.Image, contrast: float = 1.0, sharpness: float = 1.0) -> Image.Image:
    """Optional display/model preprocessing; defaults preserve the original image."""
    out = _safe_rgb(image)
    if abs(contrast - 1.0) > 1e-6:
        out = ImageEnhance.Contrast(out).enhance(float(contrast))
    if abs(sharpness - 1.0) > 1e-6:
        out = ImageEnhance.Sharpness(out).enhance(float(sharpness))
    return out


def _geo_metadata(path: str | None) -> dict[str, str]:
    """Read lightweight GeoTIFF metadata when a real filesystem path is available."""
    if not path or not HAS_RASTERIO or not Path(path).exists():
        return {}
    try:
        with rasterio.open(path) as src:
            bounds = src.bounds
            return {
                "driver": str(src.driver),
                "crs": str(src.crs) if src.crs else "unknown",
                "width": str(src.width),
                "height": str(src.height),
                "bands": str(src.count),
                "resolution": f"{src.res[0]:.3f} × {src.res[1]:.3f}",
                "bounds": f"{bounds.left:.5f}, {bounds.bottom:.5f}, {bounds.right:.5f}, {bounds.top:.5f}",
            }
    except Exception as exc:
        print("Geo metadata warning:", exc)
        return {}


def metadata_text(image: Image.Image, source_path: str | None = None) -> str:
    meta = _geo_metadata(source_path)
    base = [
        f"Dimensions: {image.width} × {image.height}px",
        f"Mode: {image.mode}",
    ]
    if meta:
        base += [
            f"CRS: {meta['crs']}",
            f"Raster: {meta['width']} × {meta['height']} | {meta['bands']} band(s)",
            f"Resolution: {meta['resolution']}",
            f"Bounds: {meta['bounds']}",
        ]
    else:
        base.append("GeoTIFF metadata: unavailable for this upload")
    return "\n".join(base)


# =============================================================================
# ATTENTION EVIDENCE
# =============================================================================


def _force_eager_attention(model):
    """Temporarily force eager attention because attention tensors are required."""
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
        # Conservative fallback: only use the most frequent token if it looks
        # like a repeated visual placeholder. Otherwise return an empty tensor.
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

    # Use the final quarter of layers, averaged over heads and generation steps.
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
            # [batch, heads, query, key] -> average heads for last query token.
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
    c = (46, 210, 220)
    draw.rectangle((px0, py0, px1, py1), outline=c, width=line)
    L = max(12, round(min(W, H) * 0.045))
    for sx, sy in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        hx = 1 if sx == px0 else -1
        vy = 1 if sy == py0 else -1
        draw.line((sx, sy, sx + hx * L, sy), fill=c, width=line + 1)
        draw.line((sx, sy, sx, sy + vy * L), fill=c, width=line + 1)
    return out


def _overlay(image: Image.Image, attn_1d: np.ndarray, grid: tuple[int, int], alpha: float = 0.45) -> Image.Image:
    import matplotlib
    h, w = grid
    arr = attn_1d.reshape(h, w)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    heat = Image.fromarray((arr * 255).astype(np.uint8)).resize(image.size, Image.BILINEAR)
    cmap = matplotlib.colormaps["jet"]
    heat_rgb = (cmap(np.asarray(heat) / 255.0)[:, :, :3] * 255).astype(np.uint8)
    return Image.blend(image.convert("RGB"), Image.fromarray(heat_rgb), alpha=alpha)


# =============================================================================
# CONFIDENCE — HEURISTIC, NOT A CALIBRATED PROBABILITY
# =============================================================================


def estimate_confidence(answer: str, route: str, evidence_available: bool) -> tuple[int, str]:
    """Return a transparent heuristic confidence estimate.

    This intentionally avoids pretending that raw generation probabilities are
    calibrated. It should be replaced by a validated confidence model for research use.
    """
    a = (answer or "").strip().lower()
    score = 58
    if a:
        score += 8
    if any(x in a for x in ("i cannot", "cannot determine", "uncertain", "not clear", "unclear")):
        score -= 28
    if any(x in a for x in ("yes", "no", "approximately", "visible", "present")):
        score += 7
    if route == "counting":
        score -= 4  # exact counting is intrinsically harder for a VLM-only path
    if route == "grounding":
        score -= 2
    if evidence_available:
        score += 6
    score = max(10, min(94, score))
    label = "high" if score >= 75 else "moderate" if score >= 55 else "low"
    return score, label


# =============================================================================
# TEMPORAL ANALYSIS
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


def _diff_overlay(image_b: Image.Image, diff_arr: np.ndarray, alpha: float = 0.45) -> Image.Image:
    import matplotlib
    arr = diff_arr.copy()
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    heat = Image.fromarray((arr * 255).astype(np.uint8)).resize(image_b.size, Image.BILINEAR)
    cmap = matplotlib.colormaps["jet"]
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
    c = (255, 153, 51)
    draw.rectangle((px0, py0, px1, py1), outline=c, width=line)
    L = max(12, round(min(W, H) * 0.045))
    for sx, sy in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        hx = 1 if sx == px0 else -1
        vy = 1 if sy == py0 else -1
        draw.line((sx, sy, sx + hx * L, sy), fill=c, width=line + 1)
        draw.line((sx, sy, sx, sy + vy * L), fill=c, width=line + 1)
    return out


def analyze_temporal(image_a, image_b, query):
    if image_a is None or image_b is None:
        return "Upload both the before and after scenes.", None, None, None, "", ""
    if not query or not query.strip():
        return "Enter a question about the change between these two scenes.", None, None, None, "", ""
    model, processor = _load()
    answer = _extract_temporal(model, processor, _safe_rgb(image_a), _safe_rgb(image_b), query.strip())
    diff = _diff_map(image_a, image_b)
    return (
        answer,
        image_a,
        _diff_overlay(image_b, diff),
        _diff_box(image_b, diff),
        "change detection",
        "Change map is a pixel-difference baseline; it is not a semantic change detector.",
    )

if HAS_SPACES:
    analyze_temporal = spaces.GPU(analyze_temporal)


# =============================================================================
# MAIN ANALYSIS
# =============================================================================


def analyze(image, query, show_evidence, contrast, sharpness):
    if image is None:
        return "Upload a satellite image first.", None, None, None, "—", "—", "—", "—"
    if not query or not query.strip():
        return "Enter a question about the image.", image, image, image, "—", "—", "—", "—"

    route = route_question(query)
    processed = _preprocess_image(image, contrast, sharpness)
    answer, attn, grid = _generate_answer(processed, query.strip(), bool(show_evidence))

    heatmap = processed if attn is None or grid is None else _overlay(processed, attn, grid)
    box = processed if attn is None or grid is None else _evidence_box(processed, attn, grid)
    confidence, confidence_label = estimate_confidence(answer, route, attn is not None and grid is not None)

    evidence_note = (
        "Attention-guided visual evidence; not a guaranteed detector."
        if attn is not None and grid is not None
        else "Evidence disabled or unavailable for this inference."
    )
    return (
        answer,
        processed,
        heatmap,
        box,
        route,
        f"{confidence}% ({confidence_label})",
        evidence_note,
        metadata_text(processed),
    )

if HAS_SPACES:
    analyze = spaces.GPU(analyze)


def _chat_dispatch(mode, image_a, image_b, query, history, show_evidence, contrast, sharpness):
    history = list(history or [])
    if not query or not query.strip():
        return history, "Enter a question.", image_a, image_a, image_a, "—", "—", "—", "—"

    if mode == "disaster":
        answer, before, diff_heat, diff_box, route, note = analyze_temporal(image_a, image_b, query)
        if before is None:
            return history, answer, image_a, image_a, image_a, route, "—", note, "—"
        history += [
            {"role": "user", "content": query.strip()},
            {"role": "assistant", "content": answer},
        ]
        confidence, label = estimate_confidence(answer, route, diff_heat is not None)
        return history, answer, before, diff_heat, diff_box, route, f"{confidence}% ({label})", note, metadata_text(before)

    result = analyze(image_a, query, show_evidence, contrast, sharpness)
    answer, original, heatmap, box, route, confidence, note, metadata = result
    history += [
        {"role": "user", "content": query.strip()},
        {"role": "assistant", "content": answer},
    ]
    return history, answer, original, heatmap, box, route, confidence, note, metadata


# =============================================================================
# UI
# =============================================================================


def _image_data_uri(path: str) -> str:
    if not Path(path).exists():
        return ""
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _thumb_data_uri(path: str, max_dim: int = 640) -> str:
    if not Path(path).exists():
        return ""
    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((max_dim, max_dim))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""


def _make_star_field(count: int = 260) -> str:
    rng = random.Random(26167)
    stars = []
    for _ in range(count):
        x = rng.uniform(0, 100); y = rng.uniform(0, 100)
        size = rng.uniform(0.7, 1.6)
        opacity = rng.uniform(0.25, 0.75)
        stars.append(
            f'<span class="satq-star" style="--x:{x:.2f}%;--y:{y:.2f}%;--size:{size:.2f}px;--opacity:{opacity:.2f}"></span>'
        )
    return '<div class="satq-stars" aria-hidden="true">' + ''.join(stars) + '</div>'


STAR_FIELD_HTML = _make_star_field()

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&family=Roboto+Mono:wght@400;500&display=swap');
:root{--void:#05090d;--panel:#0c141c;--rule:#1c2831;--paper:#edf2f0;--dim:#7c8f97;--nir:#e8503a;--water:#2e7d8f;--saffron:#ff9933;}
html,body,.gradio-container{background:var(--void)!important;color:var(--paper)!important;font-family:Archivo,system-ui,sans-serif!important}
.gradio-container>div,.gradio-container>.main,.wrap,.contain,.app{background:transparent!important}
footer,.footer,.built-with,.show-api{display:none!important}
#page{max-width:1180px;margin:auto;padding:0 24px;position:relative;z-index:1}
.satq-stars{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden}
.satq-star{position:absolute;left:var(--x);top:var(--y);width:var(--size);height:var(--size);background:#dce8e7;border-radius:50%;opacity:var(--opacity);box-shadow:0 0 5px #2e7d8f}
#nav{display:flex;justify-content:space-between;align-items:center;padding:26px 0 0}
#nav .mark{font-size:42px;font-weight:800;letter-spacing:-.05em}.mark em{font-style:normal;color:var(--nir)}
#hero{padding:68px 0 42px;max-width:850px}.kicker{font:11px Roboto Mono,monospace;color:var(--saffron);letter-spacing:.1em}.kicker:before{content:'— ';opacity:.6}
#hero h1{font-size:clamp(40px,6vw,68px);line-height:1;letter-spacing:-.045em;margin:18px 0}.hero-accent{color:var(--nir)}
#hero p{font-size:17px;line-height:1.6;color:var(--dim);max-width:68ch}
#sheet{border:1px solid var(--rule);background:linear-gradient(180deg,rgba(255,153,51,.04),transparent 180px),var(--panel);position:relative;box-shadow:0 24px 70px -30px #000}
#sheet>.gr-row,#sheet>.gr-column{position:relative;z-index:1}
#modebar{border-bottom:1px solid var(--rule);padding:14px 18px!important}
#mode-general,#mode-disaster{border-radius:0!important;border:1px solid var(--rule)!important;background:transparent!important;color:var(--paper)!important}
#mode-general.primary,#mode-disaster.primary{background:var(--nir)!important;color:#0b1014!important}
#workspace{padding:0!important}.col{padding:24px!important}
#left{border-right:1px solid var(--rule)}
.fieldname{font:10px Roboto Mono,monospace;color:var(--dim);letter-spacing:.12em;margin-bottom:8px}
#query textarea{background:transparent!important;border:0!important;border-bottom:1px solid var(--rule)!important;border-radius:0!important;color:var(--paper)!important;font-size:18px!important}
#run{background:var(--nir)!important;color:#0b1014!important;border:0!important;border-radius:0!important;font-weight:800!important}
#conversation{border:1px solid var(--rule)!important;background:#071017!important}
#conversation .message{font-size:15px!important;line-height:1.5!important}
.gradio-container [data-testid="image"],.gradio-container .image-container{border:1px solid var(--rule)!important;border-radius:0!important;background:#070c0f!important}
#evidence-tabs{border:1px solid var(--rule)!important}.tab-nav button{color:var(--dim)!important}.tab-nav button.selected{color:var(--saffron)!important}
#stats{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--rule);margin-top:34px}
.stat{padding:20px;border-right:1px solid var(--rule)}.stat:last-child{border-right:0}.stat .n{font-size:28px;font-weight:800}.stat small{display:block;color:var(--dim);line-height:1.45;margin-top:6px}
#note{color:var(--dim);font:12px Roboto Mono,monospace;line-height:1.55}
#meta{white-space:pre-wrap;color:var(--dim);font:12px Roboto Mono,monospace;line-height:1.6}
@media(max-width:850px){#left{border-right:0;border-bottom:1px solid var(--rule)}#stats{grid-template-columns:1fr 1fr}}
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


with gr.Blocks(title="SatQuery — Geospatial Intelligence", css=CSS, js=JS, theme=gr.themes.Base()) as demo:
    gr.HTML(STAR_FIELD_HTML)
    with gr.Column(elem_id="page"):
        gr.HTML("""
        <div id="nav"><div class="mark">SAT<em>Q</em>RY</div><div style="font:11px Roboto Mono;color:#7c8f97">REMOTE-SENSING VISION</div></div>
        <section id="hero"><div class="kicker">LIVE SCENE ANALYSIS</div><h1>Ask a satellite image.<br><span class="hero-accent">Show the evidence.</span></h1><p>Multimodal satellite-image question answering with optional attention evidence and bi-temporal disaster analysis.</p></section>
        """)

        with gr.Column(elem_id="sheet"):
            mode_state = gr.State("general")
            with gr.Row(elem_id="modebar"):
                general_btn = gr.Button("GENERAL INQUIRY", elem_id="mode-general", variant="primary")
                disaster_btn = gr.Button("DISASTER / SDG", elem_id="mode-disaster", variant="secondary")

            with gr.Row(elem_id="workspace", equal_height=False):
                with gr.Column(elem_id="left", scale=6, elem_classes=["col"]):
                    gr.HTML('<div class="fieldname">SCENE</div>')
                    img_in = gr.Image(type="pil", label="", show_label=False, height=360)
                    img_in_b = gr.Image(type="pil", label="AFTER SCENE", show_label=False, height=360, visible=False)
                    gr.HTML('<div class="fieldname" style="margin-top:18px">QUESTION</div>')
                    query_in = gr.Textbox(show_label=False, lines=2, max_lines=4, placeholder="Ask about buildings, roads, vegetation, water, counting, comparison…", elem_id="query")
                    with gr.Row():
                        run_btn = gr.Button("ANALYZE →", elem_id="run", variant="primary")
                        show_evidence = gr.Checkbox(value=DEFAULT_ATTENTION, label="Show evidence", info="Runs attention extraction")
                    with gr.Row():
                        contrast = gr.Slider(0.8, 1.4, value=1.0, step=0.05, label="Contrast")
                        sharpness = gr.Slider(0.8, 1.5, value=1.0, step=0.05, label="Sharpness")

                with gr.Column(elem_id="right", scale=6, elem_classes=["col"]):
                    gr.HTML('<div class="fieldname">CONVERSATION</div>')
                    chat = gr.Chatbot(value=[], show_label=False, height=300, elem_id="conversation", type="messages")
                    with gr.Row():
                        answer_out = gr.Textbox(label="ANSWER", lines=5, interactive=False)
                    with gr.Row():
                        route_out = gr.Textbox(label="ROUTED TASK", value="—", interactive=False)
                        confidence_out = gr.Textbox(label="EST. CONFIDENCE", value="—", interactive=False)
                    gr.Markdown("", elem_id="note")
                    note_out = gr.Textbox(label="EVIDENCE / LIMITATION", value="—", lines=2, interactive=False)
                    meta_out = gr.Textbox(label="SCENE METADATA", value="—", lines=5, interactive=False)

            with gr.Tabs(elem_id="evidence-tabs"):
                with gr.Tab("ORIGINAL"):
                    original_out = gr.Image(label="", show_label=False, interactive=False, height=330)
                with gr.Tab("ATTENTION / CHANGE"):
                    heatmap_out = gr.Image(label="", show_label=False, interactive=False, height=330)
                with gr.Tab("EVIDENCE BOX"):
                    box_out = gr.Image(label="", show_label=False, interactive=False, height=330)

        with gr.Column(visible=True) as general_examples:
            gr.HTML('<div class="fieldname" style="margin-top:30px">GENERAL EXAMPLES</div>')
            with gr.Row():
                for i, (path, question) in enumerate(EXAMPLES):
                    btn = gr.Button(question, variant="secondary")
                    uri = _image_data_uri(path)
                    if uri:
                        btn.elem_id = f"example-{i}"
                        CSS += ""
                    def load_general(p=path, q=question):
                        if not Path(p).exists():
                            return None, q
                        return Image.open(p).convert("RGB"), q
                    btn.click(load_general, outputs=[img_in, query_in], queue=False)

        with gr.Column(visible=False) as disaster_examples:
            gr.HTML('<div class="fieldname" style="margin-top:30px">DISASTER / SDG EXAMPLES</div>')
            with gr.Row():
                for i, (label, bp, ap, q) in enumerate(DISASTER_EXAMPLES):
                    btn = gr.Button(label, variant="secondary")
                    def load_disaster(b=bp, a=ap, question=q):
                        if not Path(b).exists() or not Path(a).exists():
                            return None, None, question
                        return Image.open(b).convert("RGB"), Image.open(a).convert("RGB"), question
                    btn.click(load_disaster, outputs=[img_in, img_in_b, query_in], queue=False)

        gr.HTML("""
        <div id="stats">
          <div class="stat"><div class="n">01</div><small>Transparent question routing for presence, counting, comparison, grounding and change analysis.</small></div>
          <div class="stat"><div class="n">02</div><small>Optional attention evidence without presenting attention as a guaranteed detector.</small></div>
          <div class="stat"><div class="n">03</div><small>Bi-temporal before/after reasoning with a clearly labeled pixel-difference baseline.</small></div>
          <div class="stat"><div class="n">04</div><small>4-bit Qwen3-VL inference designed for constrained GPU environments.</small></div>
        </div>
        <div style="padding:30px 0 60px;color:#7c8f97;font:12px Roboto Mono;line-height:1.7">
          SatQuery — Team Code Darbar · SIH 2026<br>
          Evidence is attribution-oriented. Exact object counting and semantic change detection should be backed by dedicated detectors/segmentation models before being treated as measurement.
        </div>
        """)

    toggle_outputs = [mode_state, general_btn, disaster_btn, img_in_b, general_examples]
    general_btn.click(_switch_general, outputs=toggle_outputs, queue=False)
    disaster_btn.click(_switch_disaster, outputs=[mode_state, general_btn, disaster_btn, img_in_b, general_examples], queue=False)

    outputs = [chat, answer_out, original_out, heatmap_out, box_out, route_out, confidence_out, note_out, meta_out]
    inputs = [mode_state, img_in, img_in_b, query_in, chat, show_evidence, contrast, sharpness]
    run_btn.click(_chat_dispatch, inputs=inputs, outputs=outputs)
    query_in.submit(_chat_dispatch, inputs=inputs, outputs=outputs)


if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        ssr_mode=False,
    )
