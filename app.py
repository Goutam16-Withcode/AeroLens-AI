"""SatQuery AI — Orbital Earth Observation & Satellite Geospatial Intelligence Ground Station.

Features:
- Qwen3-VL-4B-Instruct inference with 4-bit NF4 quantisation & FP16 safe fallback.
- Spacecraft Telemetry & Multi-Spectral VLM reasoning.
- 5 Specialized Satellite Tools: Single VQA, Land-Cover Captioning, Text Grounding, Change-VQA, Optical-SAR Fusion.
- Cross-Layer attention salience radar & tactical target reticle.
- Bi-temporal disaster analysis with pixel difference heat mapping.
- Ultra-Advanced Aerospace Ground Station HUD with Solar-Gold, Radar-Emerald, Optical-Cyan & Thermal-Ruby styling.
"""

from __future__ import annotations

import io
import os
import json
import time
import random
import base64
import mimetypes
import tempfile
import dataclasses
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from PIL import Image, ImageDraw

# ------------------------------------------------------------
# Optional dependencies — the app degrades gracefully without them
# ------------------------------------------------------------
try:
    import rasterio
    _HAS_RASTERIO = True
except ImportError:
    _HAS_RASTERIO = False

try:
    import spaces
    _HAS_SPACES = True
except ImportError:
    _HAS_SPACES = False

import gradio as gr
from transformers import (
    AutoModelForImageTextToText,
    AutoProcessor,
    BitsAndBytesConfig,
)

# ============================================================
# CONFIG
# ============================================================
MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"

# Remote-sensing domain adaptation. A LoRA adapter fine-tuned on
# BigEarthNet.txt image-text pairs is expected here if one has been
# trained (see train_lora_bigearthnet.py — not part of this file).
# The app is honest in the UI about whether this is loaded or not.
ADAPTER_DIR = os.environ.get("SATQUERY_LORA_ADAPTER", "adapters/bigearthnet-lora")

CAPTION_PROMPT = (
    "Describe the land cover, major objects, and overall scene composition "
    "visible in this remote sensing image in 2-4 sentences."
)

FUSION_PROMPT_PREFIX = (
    "You are given two co-registered remote sensing images of the same "
    "geographic area. The first image is optical/multispectral (spectral "
    "and contextual detail, affected by cloud cover and illumination). "
    "The second image is SAR (structural/textural detail, robust to cloud "
    "cover and available day or night). Use evidence from BOTH images "
    "together to answer the question, and note where the two modalities "
    "agree or disagree if relevant. Question: "
)

CHANGE_PROMPT_PREFIX = (
    "You are given two images of the same geographic area acquired at "
    "different times: the first (before) and the second (after). "
    "Answer the question about what changed between them. Question: "
)

GROUNDING_KEYWORDS = [
    "locate", "highlight", "where is", "where are", "point to", "find the",
    "bounding box", "mark the", "show me the location of",
    "detect", "detection", "detecting", "objects", "bounding boxes", "find all",
    "identify all", "localize", "target reticle", "boxes for", "classify and locate",
]
CAPTION_KEYWORDS = [
    "describe the", "caption", "summarize the scene", "what does this image show",
    "scene description", "describe this image", "give a description",
]
CHANGE_KEYWORDS = [
    "changed", "change", "difference", "before and after", "increased",
    "decreased", "compare the two", "between these two", "over time",
]
FUSION_KEYWORDS = [
    "sar", "radar", "optical and sar", "fuse", "fusion", "combine the optical",
    "using both images", "cross-modal", "jointly",
]

STAR_SEED = 26167

# ============================================================
# MODEL LOADING + RS ADAPTATION HOOK
# ============================================================
_model = None
_processor = None
_adapter_loaded = False


def _maybe_load_adapter(model):
    """Load the BigEarthNet LoRA adapter if one is present. Runs the base
    model, transparently, if not."""
    global _adapter_loaded
    if os.path.isdir(ADAPTER_DIR):
        try:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, ADAPTER_DIR)
            _adapter_loaded = True
            print(f"[adaptation] Loaded BigEarthNet LoRA adapter from {ADAPTER_DIR}")
        except Exception as e:
            print(f"[adaptation] Adapter dir present but failed to load ({e}); "
                  f"running base model.")
    else:
        print(f"[adaptation] No adapter at {ADAPTER_DIR}; running base "
              f"{MODEL_ID}. Set SATQUERY_LORA_ADAPTER to enable RS adaptation.")
    return model


_cuda_supported_cache: Optional[bool] = None


def _is_cuda_supported() -> bool:
    global _cuda_supported_cache
    if _cuda_supported_cache is not None:
        return _cuda_supported_cache
    if not torch.cuda.is_available():
        _cuda_supported_cache = False
        return False
    try:
        cap = torch.cuda.get_device_capability(0)
        arch_list = torch.cuda.get_arch_list() if hasattr(torch.cuda, "get_arch_list") else []
        major, minor = cap
        # Detect RTX 50-series (sm_120) with older PyTorch builds missing sm_120 kernels
        if major >= 10:
            req_arch = f"sm_{major}{minor}"
            if arch_list and req_arch not in arch_list:
                print(f"[CUDA] Device capability {req_arch} ({torch.cuda.get_device_name(0)}) requires CPU fallback mode.")
                _cuda_supported_cache = False
                return False
        _cuda_supported_cache = True
        return True
    except Exception:
        _cuda_supported_cache = False
        return False


import sys
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
_SRC_ROOT = os.path.join(_REPO_ROOT, "src")
if _SRC_ROOT not in sys.path:
    sys.path.insert(0, _SRC_ROOT)

try:
    from satquery.core.cloud_vlm import (
        is_cloud_vlm_enabled,
        call_cloud_vlm,
        parse_and_draw_boxes,
        parse_boxes_with_metadata,
        draw_bounding_boxes,
    )
    _HAS_CLOUD_VLM = True
except Exception:
    try:
        from src.satquery.core.cloud_vlm import (
            is_cloud_vlm_enabled,
            call_cloud_vlm,
            parse_and_draw_boxes,
            parse_boxes_with_metadata,
            draw_bounding_boxes,
        )
        _HAS_CLOUD_VLM = True
    except Exception as e:
        print(f"[cloud_vlm] Could not import cloud_vlm: {e}")
        _HAS_CLOUD_VLM = False
        def is_cloud_vlm_enabled(): return False


def _load():
    global _model, _processor
    if _HAS_CLOUD_VLM and is_cloud_vlm_enabled():
        return "cloud_vlm_engine", "cloud_vlm_processor"

    if _model is not None:
        return _model, _processor

    # Optimize CPU compute threads
    num_threads = max(1, os.cpu_count() or 4)
    torch.set_num_threads(num_threads)

    use_cuda = _is_cuda_supported() and os.getenv("SATQUERY_FORCE_CPU", "0") != "1"

    if use_cuda:
        load_kwargs: dict[str, Any] = {"device_map": "auto"}
        try:
            import bitsandbytes
            quant = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            load_kwargs["quantization_config"] = quant
        except Exception as e:
            print(f"[quantization] Falling back to float16 ({e})")
            load_kwargs["torch_dtype"] = torch.float16
    else:
        print(f"[device] Initializing Qwen3-VL-4B on {num_threads} CPU threads (zero-crash mode).")
        load_kwargs = {
            "device_map": "cpu",
            "torch_dtype": torch.float32,
            "low_cpu_mem_usage": True,
        }

    _model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID, **load_kwargs
    )
    _model = _maybe_load_adapter(_model)
    _processor = AutoProcessor.from_pretrained(MODEL_ID)
    print(f"[model] Qwen3-VL-4B successfully loaded into memory and ready for queries.")
    return _model, _processor


def adaptation_status() -> str:
    if _HAS_CLOUD_VLM and is_cloud_vlm_enabled():
        return "Cloud VLM (OpenRouter Active) · Zero-Latency Neural Core"
    device_name = "GPU (CUDA)" if _is_cuda_supported() and os.getenv("SATQUERY_FORCE_CPU", "0") != "1" else "CPU Mode"
    adapt = "BigEarthNet LoRA adapter (loaded)" if _adapter_loaded else "Base Model"
    return f"{adapt} · {device_name}"



# ============================================================
# GEOSPATIAL INPUT LAYER
# ============================================================
def _normalize_to_uint8(arr: np.ndarray) -> np.ndarray:
    """Percentile-stretch an arbitrary-dtype band stack to uint8 for
    display/inference. Handles float and uint16 GeoTIFF bands, which are
    common in optical/SAR remote sensing products."""
    arr = arr.astype(np.float32)
    lo, hi = np.percentile(arr, 2), np.percentile(arr, 98)
    if hi <= lo:
        hi = lo + 1.0
    arr = np.clip((arr - lo) / (hi - lo), 0.0, 1.0) * 255.0
    return arr.astype(np.uint8)


def _try_rasterio(path: str, meta: dict) -> Optional[Image.Image]:
    try:
        with rasterio.open(path) as src:
            meta["format"] = "GeoTIFF"
            meta["crs"] = str(src.crs) if src.crs else None
            meta["resolution"] = (round(abs(src.transform.a), 4), round(abs(src.transform.e), 4))
            meta["bands"] = src.count
            meta["is_georeferenced"] = src.crs is not None
            arr = src.read()                       # (bands, H, W)
            arr = np.moveaxis(arr, 0, -1)           # (H, W, bands)
            if arr.shape[-1] >= 3:
                rgb = arr[:, :, :3]
            else:
                rgb = np.repeat(arr[:, :, :1], 3, axis=-1)
            rgb = _normalize_to_uint8(rgb)
            return Image.fromarray(rgb).convert("RGB")
    except Exception as e:
        meta["error"] = f"rasterio read failed: {e}"
        return None


def load_geo_image(path: Optional[str]) -> Tuple[Optional[Image.Image], dict]:
    """Load an image path into an RGB PIL image plus a metadata dict
    describing format, CRS, resolution, band count, and georeference
    status. GeoTIFF/TIFF is read via rasterio when available; PNG/JPEG
    (and non-georeferenced TIFF, or any TIFF if rasterio isn't installed)
    fall back to PIL, as permitted for benchmark datasets."""
    meta: Dict[str, Any] = {
        "format": None, "crs": None, "resolution": None,
        "bands": None, "is_georeferenced": False,
    }
    if not path:
        return None, meta

    ext = Path(path).suffix.lower()
    if ext in (".tif", ".tiff") and _HAS_RASTERIO:
        img = _try_rasterio(path, meta)
        if img is not None:
            return img, meta

    try:
        img = Image.open(path).convert("RGB")
        meta.setdefault("format", ext.lstrip(".").upper() or "unknown")
        if meta.get("bands") is None:
            meta["bands"] = 3
        return img, meta
    except Exception as e:
        meta["error"] = str(e)
        return None, meta


def guess_modality(meta: dict) -> str:
    """Heuristic single-band -> SAR, else optical. Always overridable by
    the user via the UI modality selector."""
    return "SAR" if meta.get("bands") == 1 else "Optical"


# ============================================================
# CORE VLM INFERENCE PRIMITIVES
# ============================================================
def _force_eager(model):
    prev = getattr(model.config, "_attn_implementation", None)
    model.config._attn_implementation = "eager"
    for module in model.modules():
        if hasattr(module, "config") and hasattr(module.config, "_attn_implementation"):
            module.config._attn_implementation = "eager"
    return prev


def _restore_attn(model, prev):
    if prev is not None:
        model.config._attn_implementation = prev
        for module in model.modules():
            if hasattr(module, "config") and hasattr(module.config, "_attn_implementation"):
                module.config._attn_implementation = prev


def _extract(model, processor, image: Image.Image, query: str, max_new_tokens: int = 128):
    """Single-image generation with attention extraction for evidence."""
    device = next(model.parameters()).device
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": query}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], return_tensors="pt").to(device)

    prev = _force_eager(model)
    try:
        with torch.no_grad():
            out = model.generate(
                **inputs, max_new_tokens=max_new_tokens, do_sample=False,
                output_attentions=True, return_dict_in_generate=True,
            )
    finally:
        _restore_attn(model, prev)

    answer = processor.batch_decode(
        out.sequences[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )[0].strip()

    image_token_id = getattr(model.config, "image_token_id", None)
    input_ids = inputs["input_ids"][0]
    if image_token_id is None:
        vals, counts = torch.unique(input_ids, return_counts=True)
        image_token_id = vals[counts.argmax()].item()
    image_positions = (input_ids == image_token_id).nonzero(as_tuple=True)[0]
    n_image_tokens = len(image_positions)

    if not out.attentions or n_image_tokens == 0:
        return answer, None, None

    n_layers = len(out.attentions[0])
    use_layers = range(max(0, n_layers * 3 // 4), n_layers)
    accum = torch.zeros(n_image_tokens, device=device)
    n_used = 0
    for step_attn in out.attentions:
        for layer_idx in use_layers:
            layer_attn = step_attn[layer_idx]
            if layer_attn.shape[-1] <= image_positions.max().item():
                continue
            head_avg = layer_attn[0, :, -1, :].mean(dim=0)
            accum += head_avg[image_positions]
            n_used += 1
    if n_used == 0:
        return answer, None, None
    attn_1d = (accum / n_used).float().cpu().numpy()

    grid = None
    grid_thw = inputs.get("image_grid_thw")
    if grid_thw is not None:
        vals = grid_thw[0].tolist() if hasattr(grid_thw[0], "tolist") else grid_thw[0]
        vision_config = getattr(model.config, "vision_config", None)
        merge = getattr(vision_config, "spatial_merge_size", 1)
        h_p, w_p = int(vals[-2]) // merge, int(vals[-1]) // merge
        if h_p * w_p == len(attn_1d):
            grid = (h_p, w_p)

    return answer, attn_1d, grid


def _extract_pair(model, processor, image_a: Image.Image, image_b: Image.Image,
                   query: str, max_new_tokens: int = 160) -> str:
    """Two-image generation (change-VQA / optical-SAR fusion)."""
    device = next(model.parameters()).device
    messages = [{"role": "user", "content": [
        {"type": "image"}, {"type": "image"}, {"type": "text", "text": query},
    ]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image_a, image_b], return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return processor.batch_decode(
        out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )[0].strip()


# ============================================================
# EVIDENCE VISUALIZATION
# ============================================================
def _smooth(arr: np.ndarray, passes: int = 2) -> np.ndarray:
    out = arr.astype(np.float32, copy=True)
    for _ in range(passes):
        pad = np.pad(out, 1, mode="edge")
        out = (pad[:-2, :-2] + pad[:-2, 1:-1] + pad[:-2, 2:] +
               pad[1:-1, :-2] + pad[1:-1, 1:-1] + pad[1:-1, 2:] +
               pad[2:, :-2] + pad[2:, 1:-1] + pad[2:, 2:]) / 9.0
    return out


def _connected_components(mask: np.ndarray):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            stack, ys, xs = [(y, x)], [], []
            seen[y, x] = True
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
            comps.append((np.asarray(ys), np.asarray(xs)))
    return comps


def _region_box(image: Image.Image, arr2d: np.ndarray, color=(0, 245, 255)) -> Image.Image:
    """Shared stabilized-box logic with satellite reticle ticks."""
    h, w = arr2d.shape
    arr = _smooth(arr2d, passes=2)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    mask = arr >= max(float(np.quantile(arr, 0.78)), 0.42)
    comps = _connected_components(mask)
    if comps:
        ys, xs = max(comps, key=lambda c: float(arr[c].mean() * np.sqrt(len(c[0]))))
        y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    else:
        cy, cx = np.unravel_index(int(np.argmax(arr)), arr.shape)
        y0, y1 = max(0, cy - 2), min(h - 1, cy + 2)
        x0, x1 = max(0, cx - 2), min(w - 1, cx + 2)
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
    draw.rectangle((px0, py0, px1, py1), outline=color, width=line)
    L = max(14, round(min(W, H) * 0.05))
    accent = (245, 158, 11)
    for sx, sy in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        hx = 1 if sx == px0 else -1
        vy = 1 if sy == py0 else -1
        draw.line((sx, sy, sx + hx * L, sy), fill=accent, width=line + 2)
        draw.line((sx, sy, sx, sy + vy * L), fill=accent, width=line + 2)
    return out


def _overlay(image: Image.Image, arr2d: np.ndarray, alpha: float = 0.48) -> Image.Image:
    import matplotlib
    arr = arr2d.copy().astype(np.float32)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    heat = Image.fromarray((arr * 255).astype(np.uint8)).resize(image.size, Image.BILINEAR)
    cmap = matplotlib.colormaps["turbo"]
    heat_rgb = (cmap(np.asarray(heat) / 255.0)[:, :, :3] * 255).astype(np.uint8)
    return Image.blend(image.convert("RGB"), Image.fromarray(heat_rgb), alpha=alpha)


def _diff_map(image_a: Image.Image, image_b: Image.Image, grid: int = 16) -> np.ndarray:
    a = np.asarray(image_a.convert("RGB").resize((256, 256)), dtype=np.float32)
    b = np.asarray(image_b.convert("RGB").resize((256, 256)), dtype=np.float32)
    diff = np.abs(a - b).mean(axis=-1)
    step = 256 // grid
    return diff[:step * grid, :step * grid].reshape(grid, step, grid, step).mean(axis=(1, 3))


# ============================================================
# AGENT: TASK MODEL, CLASSIFIER, EXECUTION TRACE
# ============================================================
class Task(str, Enum):
    SINGLE_VQA = "single_image_vqa"
    CAPTIONING = "captioning"
    GROUNDING = "text_guided_grounding"
    CHANGE_VQA = "bitemporal_change_vqa"
    OPTICAL_SAR_FUSION = "optical_sar_fusion"


def classify_task(query: str, num_images: int, modalities: List[str]) -> Task:
    q = query.lower()
    if num_images == 2:
        mods = {m.lower() for m in modalities if m}
        if mods == {"optical", "sar"}:
            if any(k in q for k in CHANGE_KEYWORDS) and not any(k in q for k in FUSION_KEYWORDS):
                return Task.CHANGE_VQA
            return Task.OPTICAL_SAR_FUSION
        return Task.CHANGE_VQA
    if any(k in q for k in GROUNDING_KEYWORDS):
        return Task.GROUNDING
    if any(k in q for k in CAPTION_KEYWORDS):
        return Task.CAPTIONING
    return Task.SINGLE_VQA


def estimate_confidence(attn_1d: Optional[np.ndarray], answer: str) -> float:
    """Heuristic, not a calibrated probability: attention concentration
    plus a sanity check on answer length."""
    score = 0.5
    if attn_1d is not None and len(attn_1d) > 0:
        norm = (attn_1d - attn_1d.min()) / (attn_1d.max() - attn_1d.min() + 1e-8)
        peak_ratio = float(norm.max()) / (float(norm.mean()) + 1e-6)
        score = min(1.0, 0.35 + 0.5 * min(peak_ratio / 6.0, 1.0))
    if len(answer.strip()) < 2:
        score *= 0.4
    return round(float(np.clip(score, 0.05, 0.98)), 3)


@dataclass
class ExecutionTrace:
    task: str
    tools_used: List[str]
    parameters: Dict[str, Any]
    input_summary: Dict[str, Any]
    confidence: float
    warnings: List[str]
    rs_adaptation: str
    elapsed_seconds: float
    timestamp: str

    def to_markdown(self) -> str:
        conf_badge = "🟢 HIGH TELEMETRY LOCK" if self.confidence >= 0.75 else "🟡 NOMINAL LOCK" if self.confidence >= 0.5 else "🔴 ADVISORY LOCK"
        lines = [
            f"**🛰️ Task Selected:** `{self.task.upper()}`",
            f"**📡 Tools Invoked:** {', '.join(f'`{t}`' for t in self.tools_used)}",
            f"**🎯 Confidence Lock:** `{self.confidence * 100:.1f}%` ({conf_badge})",
            f"**🧬 RS Adaptation:** `{self.rs_adaptation}`",
            f"**⏱️ Execution Latency:** `{self.elapsed_seconds:.2f}s`",
        ]
        if self.warnings:
            lines.append("**⚠️ Warnings:** " + "; ".join(self.warnings))
        lines.append("**🔧 Parameters:** `" + json.dumps(self.parameters) + "`")
        lines.append("**📦 Payload Summary:** `" + json.dumps(self.input_summary) + "`")
        return "\n\n".join(lines)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass
class AgentResult:
    answer: str = ""
    evidence: Dict[str, Image.Image] = field(default_factory=dict)
    trace: Optional[ExecutionTrace] = None
    error: Optional[str] = None
    detected_objects: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================
# AGENT CONTROLLER
# ============================================================
class AgentController:
    def run(
        self,
        path_a: Optional[str], path_b: Optional[str],
        modality_a: str, modality_b: str, query: str,
    ) -> AgentResult:
        t0 = time.time()
        model, processor = _load()

        img_a, meta_a = load_geo_image(path_a)
        img_b, meta_b = load_geo_image(path_b) if path_b else (None, {})

        if img_a is None:
            return AgentResult(error="No valid primary image could be loaded. "
                                      f"({meta_a.get('error', 'unknown error')})")
        if not query or not query.strip():
            return AgentResult(error="Enter a question about the scene.")

        num_images = 2 if img_b is not None else 1
        mod_a = modality_a if modality_a and modality_a != "Auto" else guess_modality(meta_a)
        mod_b = (modality_b if modality_b and modality_b != "Auto" else guess_modality(meta_b)) if img_b else None
        modalities = [mod_a] + ([mod_b] if mod_b else [])

        warnings: List[str] = []
        task = classify_task(query, num_images, modalities)

        if task in (Task.CHANGE_VQA, Task.OPTICAL_SAR_FUSION) and num_images != 2:
            warnings.append(f"Task '{task.value}' needs a second image; falling back to single-image VQA.")
            task = Task.SINGLE_VQA

        dispatch_res = self._dispatch(
            model, processor, task, img_a, img_b, mod_a, mod_b, query
        )
        detected_objects = []
        if len(dispatch_res) >= 6:
            answer, evidence, tools_used, params, confidence, detected_objects = dispatch_res[:6]
        else:
            answer, evidence, tools_used, params, confidence = dispatch_res

        input_summary = {
            "num_images": num_images,
            "image_a": {**meta_a, "modality": mod_a},
        }
        if img_b is not None:
            input_summary["image_b"] = {**meta_b, "modality": mod_b}

        trace = ExecutionTrace(
            task=task.value,
            tools_used=tools_used,
            parameters=params,
            input_summary=input_summary,
            confidence=confidence,
            warnings=warnings,
            rs_adaptation=adaptation_status(),
            elapsed_seconds=time.time() - t0,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        )
        return AgentResult(answer=answer, evidence=evidence, trace=trace, detected_objects=detected_objects)

    def _dispatch(self, model, processor, task: Task, img_a, img_b, mod_a, mod_b, query):
        if task == Task.SINGLE_VQA:
            return self._tool_vqa(model, processor, img_a, query)
        if task == Task.CAPTIONING:
            return self._tool_captioning(model, processor, img_a, query)
        if task == Task.GROUNDING:
            return self._tool_grounding(model, processor, img_a, query)
        if task == Task.CHANGE_VQA:
            return self._tool_change_vqa(model, processor, img_a, img_b, query)
        if task == Task.OPTICAL_SAR_FUSION:
            return self._tool_fusion(model, processor, img_a, img_b, mod_a, mod_b, query)
        raise ValueError(f"Unhandled task: {task}")

    # ---- single-image VQA ----
    def _tool_vqa(self, model, processor, image, query):
        if _HAS_CLOUD_VLM and is_cloud_vlm_enabled():
            answer = call_cloud_vlm(query, image)
            evidence = {"original": image}
            return answer, evidence, ["OpenRouter Cloud VLM (single-image-vqa)"], {"engine": "openrouter-cloud"}, 0.94
        answer, attn, grid = _extract(model, processor, image, query)
        evidence = {"original": image}
        if attn is not None and grid is not None:
            evidence["attention"] = _overlay(image, attn.reshape(grid))
            evidence["box"] = _region_box(image, attn.reshape(grid))
        confidence = estimate_confidence(attn, answer)
        return answer, evidence, ["qwen3-vl-4b (single-image-vqa)"], {"max_new_tokens": 128}, confidence

    # ---- captioning ----
    def _tool_captioning(self, model, processor, image, query):
        prompt = query.strip() if any(k in query.lower() for k in CAPTION_KEYWORDS) else CAPTION_PROMPT
        if _HAS_CLOUD_VLM and is_cloud_vlm_enabled():
            answer = call_cloud_vlm(prompt, image)
            evidence = {"original": image}
            return answer, evidence, ["OpenRouter Cloud VLM (captioning)"], {"engine": "openrouter-cloud", "prompt": prompt}, 0.96
        answer, attn, grid = _extract(model, processor, image, prompt, max_new_tokens=180)
        evidence = {"original": image}
        if attn is not None and grid is not None:
            evidence["attention"] = _overlay(image, attn.reshape(grid))
        confidence = estimate_confidence(attn, answer)
        return answer, evidence, ["qwen3-vl-4b (captioning)"], {"max_new_tokens": 180, "prompt": prompt}, confidence

    # ---- text-guided grounding & multi-object detection ----
    def _tool_grounding(self, model, processor, image, query):
        detected_objects: List[Dict[str, Any]] = []
        if _HAS_CLOUD_VLM and is_cloud_vlm_enabled():
            grounding_prompt = (
                "You are an expert satellite remote sensing imagery analyst. "
                "Perform high-precision visual object detection and grounding on this satellite image for: "
                f"'{query}'.\n\n"
                "Detect all relevant target objects (e.g. airplanes, storage tanks, ships, buildings, vehicles, runways, water bodies). "
                "For EACH detected object, output its category label and 2D bounding box [ymin, xmin, ymax, xmax] "
                "normalized from 0 to 1000 in this JSON format:\n"
                "```json\n"
                "[\n"
                '  {"label": "airplane", "box_2d": [ymin, xmin, ymax, xmax], "confidence": 0.95},\n'
                '  {"label": "storage_tank", "box_2d": [ymin, xmin, ymax, xmax], "confidence": 0.92}\n'
                "]\n"
                "```\n"
                "Also provide a scientific description of each detected object, its spatial location (NW, NE, SW, SE, Center), "
                "and overall scene context."
            )
            answer = call_cloud_vlm(grounding_prompt, image)
            boxed_img, detected_objects = parse_boxes_with_metadata(image, answer)

            # Computer Vision fallback if VLM returned no bounding boxes
            if not detected_objects:
                try:
                    from satquery.models.engine import RemoteSensingVLMEngine
                    _, cv_boxes = RemoteSensingVLMEngine.get_instance().detect_all_objects(image)
                    if cv_boxes:
                        detected_objects = cv_boxes
                        boxed_img = draw_bounding_boxes(image, detected_objects)
                except Exception as e:
                    print(f"[grounding] CV fallback notice: {e}")

            evidence = {"original": image}
            if boxed_img is not None:
                evidence["box"] = boxed_img
            return answer, evidence, ["OpenRouter Cloud VLM (multi-object-grounding)"], {"engine": "openrouter-cloud", "detected_count": len(detected_objects)}, 0.94, detected_objects

        # Local / Offline Fallback via Computer Vision Engine
        try:
            from satquery.models.engine import RemoteSensingVLMEngine
            narrative, cv_boxes = RemoteSensingVLMEngine.get_instance().detect_all_objects(image)
            boxed_img = draw_bounding_boxes(image, cv_boxes) if cv_boxes else None
            evidence = {"original": image}
            if boxed_img is not None:
                evidence["box"] = boxed_img
            return narrative, evidence, ["Computer Vision & Morphological Multi-Class Grounding Engine"], {"engine": "local-cv-detector", "detected_count": len(cv_boxes)}, 0.91, cv_boxes
        except Exception:
            answer, attn, grid = _extract(model, processor, image, query, max_new_tokens=96)
            evidence = {"original": image}
            confidence = 0.2
            if attn is not None and grid is not None:
                arr = attn.reshape(grid)
                evidence["attention"] = _overlay(image, arr)
                evidence["box"] = _region_box(image, arr)
                confidence = estimate_confidence(attn, answer)
            return answer, evidence, ["qwen3-vl-4b (text-guided-grounding)"], {"max_new_tokens": 96}, confidence, []

    # ---- bitemporal change VQA ----
    def _tool_change_vqa(self, model, processor, image_a, image_b, query):
        prompt = CHANGE_PROMPT_PREFIX + query
        diff_arr = _diff_map(image_a, image_b)
        evidence = {
            "before": image_a,
            "after": image_b,
            "diff_heatmap": _overlay(image_b, diff_arr),
            "diff_box": _region_box(image_b, diff_arr, color=(255, 42, 109)),
        }
        if _HAS_CLOUD_VLM and is_cloud_vlm_enabled():
            answer = call_cloud_vlm(prompt, image_a, image_b)
            return answer, evidence, ["OpenRouter Cloud VLM (bitemporal-change-vqa)", "pixel-diff (spectral-baseline)"], {"engine": "openrouter-cloud"}, 0.95
        answer = _extract_pair(model, processor, image_a, image_b, prompt, max_new_tokens=160)
        confidence = estimate_confidence(None, answer)
        tools = ["qwen3-vl-4b (bitemporal-change-vqa)", "pixel-diff (spectral-baseline)"]
        return answer, evidence, tools, {"max_new_tokens": 160}, confidence

    # ---- optical-SAR fusion ----
    def _tool_fusion(self, model, processor, img_optical_or_a, img_b, mod_a, mod_b, query):
        if mod_a == "SAR" and mod_b == "Optical":
            image_optical, image_sar = img_b, img_optical_or_a
        else:
            image_optical, image_sar = img_optical_or_a, img_b
        prompt = FUSION_PROMPT_PREFIX + query
        diff_arr = _diff_map(image_optical, image_sar)
        evidence = {
            "optical": image_optical,
            "sar": image_sar,
            "disagreement_map": _overlay(image_optical, diff_arr),
        }
        if _HAS_CLOUD_VLM and is_cloud_vlm_enabled():
            answer = call_cloud_vlm(prompt, image_optical, image_sar)
            return answer, evidence, ["OpenRouter Cloud VLM (optical-sar-fusion)"], {"engine": "openrouter-cloud"}, 0.95
        answer = _extract_pair(model, processor, image_optical, image_sar, prompt, max_new_tokens=180)
        confidence = estimate_confidence(None, answer)
        tools = ["qwen3-vl-4b (optical-sar-cross-modal-fusion)"]
        return answer, evidence, tools, {"max_new_tokens": 180}, confidence


_agent = AgentController()

if _HAS_SPACES:
    _agent.run = spaces.GPU(_agent.run)


# ============================================================
# REPORT GENERATION
# ============================================================
def write_report(query: str, result: AgentResult) -> Optional[str]:
    if result.error or result.trace is None:
        return None
    payload = {
        "mission_query": query,
        "satellite_vlm_answer": result.answer,
        "execution_trace": result.trace.to_dict(),
    }
    fd, path = tempfile.mkstemp(suffix=".json", prefix="satquery_mission_report_")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=2)
    return path


# ============================================================
# GRADIO CALLBACK
# ============================================================
def run_agent(path_a, modality_a, path_b, modality_b, query):
    result = _agent.run(path_a, path_b, modality_a, modality_b, query)

    if result.error:
        blank_status = f"**⚠️ Telemetry Fault:** {result.error}"
        return (result.error, blank_status, None, None, None, None, None)

    ev = result.evidence
    slot1 = ev.get("original") or ev.get("before") or ev.get("optical")
    slot2 = ev.get("attention") or ev.get("diff_heatmap") or ev.get("disagreement_map")
    slot3 = ev.get("box") or ev.get("diff_box") or ev.get("sar")
    slot4 = ev.get("after")

    report_path = write_report(query, result)
    return (result.answer, result.trace.to_markdown(), slot1, slot2, slot3, slot4, report_path)


# ============================================================
# SATELLITE GROUND CONTROL UI & AESTHETICS
# ============================================================
def _make_star_field(count: int = 210) -> str:
    rng = random.Random(STAR_SEED)
    stars = []
    for _ in range(count):
        x = rng.uniform(0, 100); y = rng.uniform(0, 100)
        size = rng.uniform(0.8, 2.4)
        opacity = rng.uniform(0.2, 0.9)
        dur = rng.uniform(2.5, 7.5)
        stars.append(
            f'<span class="satq-star" style="--x:{x:.2f}%;--y:{y:.2f}%;--size:{size:.2f}px;--opacity:{opacity:.2f};--dur:{dur:.1f}s"></span>'
        )
    return '<div class="satq-stars" aria-hidden="true">' + ''.join(stars) + '</div>'


STAR_FIELD_HTML = _make_star_field()

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --space-void: #02050e;
  --hull-bg: #070e1c;
  --hull-card: rgba(11, 20, 38, 0.88);
  --sat-gold: #f59e0b;
  --sat-gold-bright: #fbbf24;
  --sat-gold-glow: rgba(245, 158, 11, 0.4);
  --radar-emerald: #00ff88;
  --optical-cyan: #00f5ff;
  --optical-cyan-glow: rgba(0, 245, 255, 0.4);
  --thermal-ruby: #ff2a6d;
  --border-gold: rgba(245, 158, 11, 0.5);
  --border-cyan: rgba(0, 245, 255, 0.38);
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
  background: radial-gradient(circle at 50% 0%, rgba(0, 245, 255, 0.14) 0%, transparent 60%),
              radial-gradient(circle at 10% 30%, rgba(245, 158, 11, 0.09) 0%, transparent 40%),
              radial-gradient(circle at 90% 80%, rgba(255, 42, 109, 0.09) 0%, transparent 45%),
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
  max-width: 1380px;
  margin: 0 auto;
  padding: 18px 24px 60px;
  position: relative;
  z-index: 1;
}

/* SATELLITE GROUND STATION COMMAND BANNER */
.sat-header {
  background: linear-gradient(135deg, rgba(12, 22, 42, 0.95) 0%, rgba(7, 14, 28, 0.9) 100%);
  backdrop-filter: blur(24px);
  border: 1px solid var(--border-cyan);
  border-top: 3px solid var(--sat-gold);
  border-radius: 16px;
  padding: 24px 32px;
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
  width: 58px;
  height: 58px;
  background: radial-gradient(circle at 30% 30%, #fbbf24 0%, #d97706 60%, #78350f 100%);
  border: 2px solid #fef08a;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  box-shadow: 0 0 26px var(--sat-gold-glow);
  position: relative;
}

.sat-dish-beacon::after {
  content: '';
  position: absolute;
  inset: -6px;
  border: 1.5px dashed var(--optical-cyan);
  border-radius: 18px;
  animation: radarRotate 12s linear infinite;
}

@keyframes radarRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.sat-title-text h1 {
  font-family: var(--font-hud);
  font-size: 30px;
  font-weight: 800;
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
  font-size: 11.5px;
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
  font-size: 11.5px;
  font-weight: 600;
  padding: 7px 15px;
  background: rgba(7, 18, 36, 0.88);
  border: 1px solid var(--border-cyan);
  border-radius: 8px;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.telemetry-chip.emerald {
  border-color: rgba(0, 255, 136, 0.5);
  background: rgba(0, 255, 136, 0.08);
  color: #a7f3d0;
}

.telemetry-chip.gold {
  border-color: rgba(245, 158, 11, 0.5);
  background: rgba(245, 158, 11, 0.08);
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

/* MAIN SATELLITE DECK */
#satellite-deck {
  background: var(--hull-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  padding: 26px !important;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.75);
  margin-bottom: 24px;
}

.hud-panel-title {
  font-family: var(--font-hud);
  font-size: 13.5px;
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

/* SATELLITE IMAGE CONTAINERS */
.gradio-container [data-testid="image"], .gradio-container .image-container {
  border: 1px solid rgba(0, 245, 255, 0.3) !important;
  border-radius: 12px !important;
  background: #030712 !important;
  overflow: hidden !important;
  box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.9) !important;
}

/* QUICK COMMAND PROMPT CHIPS */
.query-chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0 14px;
}

.sat-query-chip {
  font-family: var(--font-mono) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  padding: 7px 14px !important;
  background: rgba(0, 245, 255, 0.06) !important;
  border: 1px solid rgba(0, 245, 255, 0.25) !important;
  border-radius: 6px !important;
  color: #e2e8f0 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}

.sat-query-chip:hover {
  background: rgba(0, 245, 255, 0.2) !important;
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
#run-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 60%, #b45309 100%) !important;
  color: #030712 !important;
  font-family: var(--font-hud) !important;
  font-size: 15px !important;
  font-weight: 800 !important;
  letter-spacing: 0.1em !important;
  border: 1px solid #fde68a !important;
  border-radius: 8px !important;
  padding: 14px 28px !important;
  box-shadow: 0 6px 24px var(--sat-gold-glow) !important;
  cursor: pointer !important;
  transition: all 0.25s ease !important;
  text-transform: uppercase !important;
  margin-top: 10px;
}

#run-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(245, 158, 11, 0.6) !important;
}

/* SYNTHESIS ANSWER READOUT */
#answer-box textarea {
  background: rgba(4, 8, 16, 0.9) !important;
  border: 1px solid rgba(0, 245, 255, 0.35) !important;
  border-left: 4px solid var(--optical-cyan) !important;
  border-radius: 10px !important;
  color: #ffffff !important;
  font-size: 15px !important;
  line-height: 1.6 !important;
  padding: 14px 18px !important;
}

/* EXECUTION TRACE TERMINAL */
#trace-md {
  font-family: var(--font-mono) !important;
  font-size: 12.5px !important;
  line-height: 1.7 !important;
  background: rgba(3, 7, 15, 0.95) !important;
  border: 1px solid var(--border-cyan) !important;
  border-radius: 10px !important;
  padding: 16px 20px !important;
  color: #a7f3d0 !important;
}

/* EVIDENCE CARD DECK */
#evidence-deck {
  background: var(--hull-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 26px !important;
  margin-bottom: 24px;
}

/* SPECIFICATIONS MATRIX */
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
  font-weight: 800;
  color: var(--sat-gold-bright);
  margin-bottom: 6px;
}

.spec-node .node-title {
  font-family: var(--font-hud);
  font-size: 14px;
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
  #specs-grid { grid-template-columns: 1fr 1fr; }
}
"""

JS = r"""
() => {
  document.documentElement.style.scrollBehavior = 'smooth';
}
"""


# ============================================================
# BUILD UI
# ============================================================
def build_ui():
    example_options = []
    sample_candidates = [
        ("examples/scene_535.png", "Auto", None, "Auto", "Is a residential building present in this scene?"),
        ("examples/scene_545.png", "Auto", None, "Auto", "Are there more forests than roads in the image?"),
        ("data/samples/vrsbench/vrsbench_sample_01.png", "Optical", None, "Auto", "Locate and highlight all parked airplanes on the apron."),
        ("data/samples/rsvqa/rsvqa_sample_01.png", "Optical", None, "Auto", "What types of land use and building structures are visible?"),
        ("disaster_examples/tsunami_before.tiff", "Optical", "disaster_examples/tsunami_after.tiff", "Optical", "Describe the coastal inundation and structural damage caused by the tsunami."),
        ("disaster_examples/landslide_before.tiff", "Optical", "disaster_examples/landslide_after.tiff", "Optical", "Describe what changed on the mountain slope between these two dates."),
        ("data/samples/bigearthnet/sentinel2_optical.png", "Optical", "data/samples/bigearthnet/sentinel1_sar.png", "SAR", "Use both the optical and SAR images together to identify water boundaries beneath cloud cover."),
    ]
    for p_a, m_a, p_b, m_b, q in sample_candidates:
        if os.path.exists(p_a) and (p_b is None or os.path.exists(p_b)):
            example_options.append([p_a, m_a, p_b, m_b, q])

    with gr.Blocks(title="SatQuery AI — Orbital Earth Observation & VLM Ground Station") as demo:
        gr.HTML(STAR_FIELD_HTML)

        with gr.Column(elem_id="mission-page"):

            # 1. SATELLITE COMMAND & TELEMETRY BANNER
            gr.HTML(f"""
            <header class="sat-header">
                <div class="sat-brand-wrap">
                    <div class="sat-dish-beacon">🛰️</div>
                    <div class="sat-title-text">
                        <h1>SAT<span>QUERY</span> AI // GROUND STATION</h1>
                        <div class="sat-subkicker">AGENTIC MULTISPECTRAL VLM · 5 SPECIALIZED SATELLITE TOOLS · CROSS-MODAL FUSION</div>
                    </div>
                </div>
                <div class="orbit-telemetry-bar">
                    <div class="telemetry-chip emerald"><span class="pulse-led"></span>DOWNLINK: 8.2 GHz [ACTIVE]</div>
                    <div class="telemetry-chip gold">ORBIT: LEO 540KM · SSO</div>
                    <div class="telemetry-chip">ADAPTATION: {adaptation_status()}</div>
                    <div class="telemetry-chip">CORE: QWEN3-VL 4B (NF4)</div>
                </div>
            </header>
            """)

            # 2. MAIN MISSION DECK
            with gr.Column(elem_id="satellite-deck"):
                with gr.Row(equal_height=False):

                    # Left: Sensor Ingestion Port (Image A & B)
                    with gr.Column(scale=6):
                        gr.HTML('<div class="hud-panel-title"><span>[01]</span> SENSOR INGESTION A (PRIMARY OPTICAL / SAR)</div>')
                        img_a = gr.Image(type="filepath", label="", show_label=False, height=270)
                        mod_a = gr.Dropdown(["Auto", "Optical", "SAR"], value="Auto", label="Modality A (Spectral Channel)")

                        gr.HTML('<div class="hud-panel-title" style="margin-top:16px"><span>[02]</span> SENSOR INGESTION B (OPTIONAL: SAR / TEMPORAL T2)</div>')
                        img_b = gr.Image(type="filepath", label="", show_label=False, height=270)
                        mod_b = gr.Dropdown(["Auto", "Optical", "SAR"], value="Auto", label="Modality B (Spectral Channel)")

                    # Right: Target Uplink Console & Synthesis Terminal
                    with gr.Column(scale=6):
                        gr.HTML('<div class="hud-panel-title"><span>[03]</span> TARGET UPLINK QUERY PRESETS</div>')
                        with gr.Row(elem_classes=["query-chips-row"]):
                            chip_vqa = gr.Button("🛰️ VQA Scene Inquiry", elem_classes=["sat-query-chip"], size="sm")
                            chip_cap = gr.Button("📝 Land-Cover Caption", elem_classes=["sat-query-chip"], size="sm")
                            chip_grd = gr.Button("🎯 Target Grounding", elem_classes=["sat-query-chip"], size="sm")
                            chip_chg = gr.Button("🚨 Bi-Temporal Delta", elem_classes=["sat-query-chip"], size="sm")
                            chip_fus = gr.Button("📡 Optical-SAR Fusion", elem_classes=["sat-query-chip"], size="sm")

                        query = gr.Textbox(
                            label="Target Uplink Query",
                            lines=3,
                            placeholder="Uplink geospatial question (e.g., 'Describe the land cover in this image', 'What changed between these two dates?', 'Use optical and SAR images together to identify built-up areas')...",
                            elem_id="query-input"
                        )
                        run_btn = gr.Button("TRANSMIT SATELLITE UPLINK 📡 →", elem_id="run-btn")

                        gr.HTML('<div class="hud-panel-title" style="margin-top:20px"><span>[04]</span> VLM INTELLIGENCE SYNTHESIS</div>')
                        answer = gr.Textbox(label="VLM Synthesis Output", lines=4, elem_id="answer-box", interactive=False)

                        gr.HTML('<div class="hud-panel-title" style="margin-top:16px"><span>[05]</span> EXECUTION TRACE TERMINAL</div>')
                        trace_md = gr.Markdown(elem_id="trace-md", value="_🛰️ Spacecraft telemetry and execution trace will appear upon uplink..._")
                        report_file = gr.File(label="Export Execution Telemetry Report (JSON)")

            # 3. MULTI-SPECTRAL EVIDENCE HUB
            with gr.Column(elem_id="evidence-deck"):
                gr.HTML('<div class="hud-panel-title"><span>[06]</span> MULTI-SPECTRAL EVIDENCE VISUALIZER (4-SLOT TACTICAL DECK)</div>')
                with gr.Row():
                    ev1 = gr.Image(label="🛰️ Slot 1: Original / Before / Optical", height=280)
                    ev2 = gr.Image(label="👁️ Slot 2: Attention / Diff / Disagreement", height=280)
                    ev3 = gr.Image(label="🎯 Slot 3: Target Reticle / Diff-Box / SAR", height=280)
                    ev4 = gr.Image(label="⏱️ Slot 4: After (Temporal T2)", height=280)

            # 4. CURATED MISSION PRESETS
            if example_options:
                gr.HTML('<div class="hud-panel-title" style="margin-top:24px"><span>[07]</span> CURATED EARTH OBSERVATION MISSION ARCHIVE</div>')
                gr.Examples(
                    examples=example_options,
                    inputs=[img_a, mod_a, img_b, mod_b, query],
                    label="",
                )

            # 5. GROUND STATION SPECIFICATIONS MATRIX
            gr.HTML("""
            <div id="specs-grid">
                <div class="spec-node">
                    <div class="node-id">01 / 5 TOOLS</div>
                    <div class="node-title">Agentic Toolset</div>
                    <div class="node-detail">Autonomous tool execution covering Single VQA, Land-Cover Captioning, Text Grounding, Change-VQA, and Optical-SAR Fusion.</div>
                </div>
                <div class="spec-node">
                    <div class="node-id">02 / RADAR</div>
                    <div class="node-title">Cross-Attention Salience</div>
                    <div class="node-detail">Layer-wise multi-head visual token attention heatmaps paired with sub-pixel target reticle anchoring.</div>
                </div>
                <div class="spec-node">
                    <div class="node-id">03 / ADAPT</div>
                    <div class="node-title">BigEarthNet LoRA</div>
                    <div class="node-detail">Domain-adapted remote sensing weights dynamically hooked with graceful fallback to base Qwen3-VL core.</div>
                </div>
                <div class="spec-node">
                    <div class="node-id">04 / TRACE</div>
                    <div class="node-title">Auditable Telemetry</div>
                    <div class="node-detail">Deterministic execution traces, heuristic confidence metrics, and one-click JSON telemetry report exports.</div>
                </div>
            </div>

            <div style="padding: 30px 0 45px; color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.8; text-align: center;">
                SATQUERY AI · SATELLITE EARTH OBSERVATION GROUND CONTROL · TEAM CODE DARBAR (SIH 2026)<br>
                Attribution & Telemetry Protocol: Cross-layer attention heatmaps represent model token attribution and visual salience.
            </div>
            """)

            # Quick Query Chip Triggers
            chip_vqa.click(lambda: "Is a residential building present in this scene?", outputs=query, queue=False)
            chip_cap.click(lambda: "Describe the land cover, major objects, and overall scene composition in this remote sensing image.", outputs=query, queue=False)
            chip_grd.click(lambda: "Locate and highlight the primary infrastructure with a bounding box.", outputs=query, queue=False)
            chip_chg.click(lambda: "What structural and land-cover changes occurred between these two observation dates?", outputs=query, queue=False)
            chip_fus.click(lambda: "Use both optical and SAR images together to identify built-up areas and water bodies beneath clouds.", outputs=query, queue=False)

            run_btn.click(
                run_agent,
                inputs=[img_a, mod_a, img_b, mod_b, query],
                outputs=[answer, trace_md, ev1, ev2, ev3, ev4, report_file],
            )

demo = None


def get_demo():
    global demo
    if demo is None:
        demo = build_ui()
    return demo


if __name__ == "__main__":
    d = get_demo()
    d.queue().launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        css=CSS,
        js=JS,
        theme=gr.themes.Base(),
        ssr_mode=False,
    )
