"""AeroLens AI — Cloud Vision-Language Model (VLM) Engine via OpenRouter.

Provides zero-startup, high-throughput cloud inference for remote sensing:
- Single-image VQA & Land-cover captioning
- Multi-object detection & visual grounding with precision bounding boxes
- Bi-temporal change-VQA with multi-image prompt & pixel-difference evidence
- Optical-SAR cross-modal fusion with multi-spectral evidence
"""

from __future__ import annotations

import io
import os
import re
import json
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash-vl:free")
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Aerospace Multi-Class Color Palette (RGBA & HEX)
CATEGORY_COLORS: Dict[str, Tuple[int, int, int]] = {
    "airplane": (16, 185, 129),       # Neon Emerald
    "aircraft": (16, 185, 129),
    "plane": (16, 185, 129),
    "tank": (245, 158, 11),           # Solar Gold
    "storage_tank": (245, 158, 11),
    "fuel": (245, 158, 11),
    "silo": (245, 158, 11),
    "ship": (6, 182, 212),            # Electric Cyan
    "vessel": (6, 182, 212),
    "boat": (6, 182, 212),
    "marine": (6, 182, 212),
    "building": (244, 63, 94),        # Ruby Crimson
    "structure": (244, 63, 94),
    "residential": (244, 63, 94),
    "facility": (244, 63, 94),
    "roof": (244, 63, 94),
    "vehicle": (168, 85, 247),        # Violet Purple
    "car": (168, 85, 247),
    "truck": (168, 85, 247),
    "container": (168, 85, 247),
    "bridge": (249, 115, 22),         # Deep Orange
    "crossing": (249, 115, 22),
    "runway": (132, 204, 22),         # Lime
    "water": (59, 130, 246),          # Cerulean Blue
    "vegetation": (22, 163, 74),      # Sage Green
    "forest": (22, 163, 74),
    "default": (217, 119, 6),         # Tactical Amber
}


def get_category_color(label: str) -> Tuple[int, int, int]:
    lbl = (label or "").lower().strip()
    for k, color in CATEGORY_COLORS.items():
        if k in lbl:
            return color
    return CATEGORY_COLORS["default"]


def get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        candidate_paths = [
            Path(".env"),
            Path(__file__).resolve().parents[3] / ".env",
            Path(__file__).resolve().parents[2] / ".env",
            Path(__file__).resolve().parents[1] / ".env",
        ]
        for env_path in candidate_paths:
            if env_path.exists():
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip().startswith("OPENROUTER_API_KEY="):
                                parsed_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                                if parsed_key:
                                    return parsed_key
                except Exception:
                    pass
    return key or API_KEY


def is_cloud_vlm_enabled() -> bool:
    return bool(get_api_key())


def pil_to_data_uri(img: Image.Image, max_size: int = 1024) -> str:
    """Resize PIL image if too large and convert to base64 JPEG URI."""
    img_copy = img.copy().convert("RGB")
    w, h = img_copy.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        img_copy = img_copy.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    
    buf = io.BytesIO()
    img_copy.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _normalize_box(c: List[float], w: int, h: int) -> Tuple[int, int, int, int]:
    """Given 4 coordinates [y1, x1, y2, x2] or [x1, y1, x2, y2], return pixel (xmin, ymin, xmax, ymax)."""
    max_val = max(c)
    if max_val <= 1.05:
        # Normalized 0.0 .. 1.0 (assuming [ymin, xmin, ymax, xmax])
        y1, x1, y2, x2 = c[0] * h, c[1] * w, c[2] * h, c[3] * w
    elif max_val <= 1005:
        # Normalized 0 .. 1000 (Qwen-VL / Gemini detection standard)
        y1, x1, y2, x2 = (c[0] / 1000.0) * h, (c[1] / 1000.0) * w, (c[2] / 1000.0) * h, (c[3] / 1000.0) * w
    else:
        # Pixel coordinates
        y1, x1, y2, x2 = c[0], c[1], c[2], c[3]

    xmin = max(0, min(int(round(x1)), int(round(x2))))
    ymin = max(0, min(int(round(y1)), int(round(y2))))
    xmax = min(w, max(int(round(x1)), int(round(x2))))
    ymax = min(h, max(int(round(y1)), int(round(y2))))
    return xmin, ymin, xmax, ymax


def extract_bounding_boxes(text: str, w: int, h: int) -> List[Dict[str, Any]]:
    """Robust parser extracting labeled 2D bounding boxes across JSON, bracketed, and tagged formats."""
    results: List[Dict[str, Any]] = []
    seen_boxes: set = set()

    # 1. Try parsing JSON blocks ```json ... ``` or raw json
    json_candidates = []
    code_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    for cb in code_blocks:
        json_candidates.append(cb.strip())

    # Also search for standalone array JSON [...]
    array_matches = re.findall(r"(\[\s*\{[\s\S]*?\}\s*\])", text)
    for am in array_matches:
        json_candidates.append(am.strip())

    for candidate in json_candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "objects" in parsed:
                parsed = parsed["objects"]
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        coords = None
                        label = item.get("label") or item.get("category") or item.get("name") or "target"
                        conf = float(item.get("confidence", 0.92))

                        if "box_2d" in item and isinstance(item["box_2d"], list) and len(item["box_2d"]) == 4:
                            coords = [float(x) for x in item["box_2d"]]
                        elif "box" in item and isinstance(item["box"], list) and len(item["box"]) == 4:
                            coords = [float(x) for x in item["box"]]
                        elif "bbox" in item and isinstance(item["bbox"], list) and len(item["bbox"]) == 4:
                            coords = [float(x) for x in item["bbox"]]
                        elif all(k in item for k in ("ymin", "xmin", "ymax", "xmax")):
                            coords = [float(item["ymin"]), float(item["xmin"]), float(item["ymax"]), float(item["xmax"])]

                        label_str = str(label).strip()
                        # Discard prompt echoes or entire-scene bounding hallucinations
                        if len(label_str) > 35 or any(p in label_str.lower() for p in ("describe", "locate", "what", "how many", "is there", "remote sensing", "composition")):
                            continue

                        if coords:
                            xmin, ymin, xmax, ymax = _normalize_box(coords, w, h)
                            # Reject whole-frame boxes that span >90% of the image (scene prompt echo)
                            if (xmax - xmin) >= 0.90 * w and (ymax - ymin) >= 0.90 * h:
                                continue
                            if (xmax - xmin) > 4 and (ymax - ymin) > 4:
                                key = (xmin // 4, ymin // 4, xmax // 4, ymax // 4)
                                if key not in seen_boxes:
                                    seen_boxes.add(key)
                                    color = get_category_color(label_str)
                                    results.append({
                                        "id": f"det_{len(results) + 1}",
                                        "label": label_str,
                                        "category": label_str.title(),
                                        "confidence": round(conf, 2),
                                        "xmin": round(xmin / w, 4),
                                        "ymin": round(ymin / h, 4),
                                        "xmax": round(xmax / w, 4),
                                        "ymax": round(ymax / h, 4),
                                        "pixel_coords": [xmin, ymin, xmax, ymax],
                                        "color": f"rgb({color[0]}, {color[1]}, {color[2]})",
                                    })
        except Exception:
            pass

    # 2. Match labeled bracket patterns: e.g. "Airplane: [120, 340, 500, 600]" or "[120, 340, 500, 600] airplane"
    labeled_patterns = re.findall(
        r"([a-zA-Z\s\-]{2,20})[:\s\-]+\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]",
        text
    )
    for match in labeled_patterns:
        label = match[0].strip()
        if label.lower() in ("box", "coordinates", "loc", "point", "reticle"):
            label = "target"
        coords = [float(match[1]), float(match[2]), float(match[3]), float(match[4])]
        xmin, ymin, xmax, ymax = _normalize_box(coords, w, h)
        if (xmax - xmin) > 4 and (ymax - ymin) > 4:
            key = (xmin // 4, ymin // 4, xmax // 4, ymax // 4)
            if key not in seen_boxes:
                seen_boxes.add(key)
                color = get_category_color(label)
                results.append({
                    "id": f"det_{len(results) + 1}",
                    "label": label,
                    "category": label.title(),
                    "confidence": 0.91,
                    "xmin": round(xmin / w, 4),
                    "ymin": round(ymin / h, 4),
                    "xmax": round(xmax / w, 4),
                    "ymax": round(ymax / h, 4),
                    "pixel_coords": [xmin, ymin, xmax, ymax],
                    "color": f"rgb({color[0]}, {color[1]}, {color[2]})",
                })

    # 3. Match reverse labeled patterns: e.g. "[120, 340, 500, 600] - airplane"
    rev_patterns = re.findall(
        r"\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\](?:\s*[:\-]?\s*([a-zA-Z\s\-]{2,20}))?",
        text
    )
    for match in rev_patterns:
        coords = [float(match[0]), float(match[1]), float(match[2]), float(match[3])]
        label = (match[4] or "target").strip()
        if not label or label.lower() in ("box", "coords", "pixel"):
            label = "target"
        xmin, ymin, xmax, ymax = _normalize_box(coords, w, h)
        if (xmax - xmin) > 4 and (ymax - ymin) > 4:
            key = (xmin // 4, ymin // 4, xmax // 4, ymax // 4)
            if key not in seen_boxes:
                seen_boxes.add(key)
                color = get_category_color(label)
                results.append({
                    "id": f"det_{len(results) + 1}",
                    "label": label,
                    "category": label.title(),
                    "confidence": 0.88,
                    "xmin": round(xmin / w, 4),
                    "ymin": round(ymin / h, 4),
                    "xmax": round(xmax / w, 4),
                    "ymax": round(ymax / h, 4),
                    "pixel_coords": [xmin, ymin, xmax, ymax],
                    "color": f"rgb({color[0]}, {color[1]}, {color[2]})",
                })

    # Apply IoU Non-Maximum Suppression to remove duplicate/overlapping bounding boxes
    return apply_nms(results, iou_thresh=0.45)


def _compute_box_iou(box1: Dict[str, Any], box2: Dict[str, Any]) -> float:
    y1 = max(box1["ymin"], box2["ymin"])
    x1 = max(box1["xmin"], box2["xmin"])
    y2 = min(box1["ymax"], box2["ymax"])
    x2 = min(box1["xmax"], box2["xmax"])
    inter_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    box1_area = max(0.0, box1["ymax"] - box1["ymin"]) * max(0.0, box1["xmax"] - box1["xmin"])
    box2_area = max(0.0, box2["ymax"] - box2["ymin"]) * max(0.0, box2["xmax"] - box2["xmin"])
    union_area = box1_area + box2_area - inter_area
    if union_area <= 1e-8:
        return 0.0
    return inter_area / union_area


def apply_nms(boxes: List[Dict[str, Any]], iou_thresh: float = 0.45) -> List[Dict[str, Any]]:
    """Suppresses duplicate and overlapping bounding boxes using IoU threshold."""
    if not boxes:
        return []
    sorted_boxes = sorted(boxes, key=lambda b: float(b.get("confidence", 0.9)), reverse=True)
    selected: List[Dict[str, Any]] = []

    for b in sorted_boxes:
        area = (b["ymax"] - b["ymin"]) * (b["xmax"] - b["xmin"])
        if area > 0.85 or area < 0.0005:  # Ignore whole-scene or microscopic noise
            continue
        overlap = False
        for s in selected:
            if _compute_box_iou(b, s) > iou_thresh:
                overlap = True
                break
        if not overlap:
            selected.append(b)

    for idx, b in enumerate(selected):
        b["id"] = f"det_{idx + 1}"
    return selected


def draw_bounding_boxes(img: Image.Image, bboxes: List[Dict[str, Any]]) -> Image.Image:
    """Draw crisp aerospace tactical HUD reticles with completely transparent interiors and micro-badges."""
    w, h = img.size
    overlay = img.copy().convert("RGBA")
    draw = ImageDraw.Draw(overlay, "RGBA")

    for idx, box in enumerate(bboxes):
        if "pixel_coords" in box:
            xmin, ymin, xmax, ymax = box["pixel_coords"]
        else:
            xmin = max(0, min(w, int(box.get("xmin", 0) * w)))
            ymin = max(0, min(h, int(box.get("ymin", 0) * h)))
            xmax = max(0, min(w, int(box.get("xmax", 1) * w)))
            ymax = max(0, min(h, int(box.get("ymax", 1) * h)))

        label = box.get("label", "target")
        conf = box.get("confidence", 0.90)
        color = get_category_color(label)
        border_color = (color[0], color[1], color[2], 255)

        # 1. CRISP 2px BORDER WITH 100% TRANSPARENT INTERIOR (NO FILL TO ENSURE SATELLITE DETAILS REMAIN VISIBLE)
        draw.rectangle([xmin, ymin, xmax, ymax], fill=None, outline=border_color, width=2)

        # 2. Tactical Corner Crosshairs (L-shaped precision brackets)
        box_w = xmax - xmin
        box_h = ymax - ymin
        arm = max(5, min(14, box_w // 5, box_h // 5))
        reticle_color = (255, 255, 255, 240)
        draw.line([(xmin, ymin), (xmin + arm, ymin)], fill=reticle_color, width=3)
        draw.line([(xmin, ymin), (xmin, ymin + arm)], fill=reticle_color, width=3)
        draw.line([(xmax, ymin), (xmax - arm, ymin)], fill=reticle_color, width=3)
        draw.line([(xmax, ymin), (xmax, ymin + arm)], fill=reticle_color, width=3)
        draw.line([(xmin, ymax), (xmin + arm, ymax)], fill=reticle_color, width=3)
        draw.line([(xmin, ymax), (xmin, ymax - arm)], fill=reticle_color, width=3)
        draw.line([(xmax, ymax), (xmax - arm, ymax)], fill=reticle_color, width=3)
        draw.line([(xmax, ymax), (xmax, ymax - arm)], fill=reticle_color, width=3)

        # 3. Compact Micro Label Tag Badge with dark aerospace backing
        tag_text = f"{label.upper()} #{idx + 1}"
        tag_h = 16
        tag_w = max(50, len(tag_text) * 6 + 10)
        tag_y1 = max(2, ymin - tag_h - 2) if ymin > (tag_h + 4) else (ymin + 2)
        tag_y2 = tag_y1 + tag_h

        draw.rectangle([xmin, tag_y1, xmin + tag_w, tag_y2], fill=(15, 23, 42, 235), outline=border_color, width=1)
        draw.text((xmin + 5, tag_y1 + 1), tag_text, fill=(255, 255, 255, 255))

    return overlay.convert("RGB")


def parse_and_draw_boxes(img: Image.Image, text: str) -> Optional[Image.Image]:
    """Parse bounding boxes in text and render reticle. Returns annotated PIL Image."""
    w, h = img.size
    bboxes = extract_bounding_boxes(text, w, h)
    if not bboxes:
        return None
    return draw_bounding_boxes(img, bboxes)


def clean_narrative_text(text: str) -> str:
    """Strip raw bounding box JSON codeblocks and whole-image hallucinated prompt echoes
    from the natural language report, ensuring clean, professional Markdown output."""
    if not text:
        return ""
    # Remove ```json [ ... ] ``` or ``` [ ... ] ``` blocks
    cleaned = re.sub(r"```(?:json)?\s*\[[\s\S]*?\]\s*```\s*", "", text, flags=re.IGNORECASE)
    # Remove leading standalone [ { ... } ] arrays if at the beginning of the text
    cleaned = re.sub(r"^\s*\[\s*\{[\s\S]*?\}\s*\]\s*", "", cleaned)
    # Remove empty markdown code blocks
    cleaned = re.sub(r"```(?:json)?\s*```", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def parse_boxes_with_metadata(img: Image.Image, text: str) -> Tuple[Optional[Image.Image], List[Dict[str, Any]]]:
    """Parse bounding boxes in text, return BOTH the annotated PIL Image and structured object metadata."""
    w, h = img.size
    bboxes = extract_bounding_boxes(text, w, h)
    if not bboxes:
        return None, []
    annotated = draw_bounding_boxes(img, bboxes)
    return annotated, bboxes


DEFAULT_SYSTEM_PROMPT = (
    "You are AeroLens AI, an authoritative senior aerospace remote sensing intelligence analyst and planetary scientist. "
    "Generate exhaustive, highly detailed, publication-grade scientific intelligence dossiers for satellite and aerial earth observation imagery.\n\n"
    "CRITICAL OPERATIONAL DIRECTIVES:\n"
    "1. NEVER provide brief, superficial, or 2-to-3 bullet summaries. Every response must be an exhaustive, deeply detailed intelligence report.\n"
    "2. MANDATORY METRICS & TABLES: Include quantitative parameters, brightness temperature ranges (Kelvin and Celsius), spectral wavelengths, spatial resolutions, coordinates, and structured Markdown telemetry tables.\n"
    "3. SENSOR & SPECTRAL RIGOR: Accurately identify the satellite mission (e.g. INSAT-3D/3DS, GOES-16/18, Meteosat, Himawari, Sentinel-2, Landsat-8/9, Sentinel-1 SAR, WorldView, Gaofen) and spectral band physics (e.g. TIR-1 10.8µm thermal infrared, Water Vapor 6.9µm, Visible 0.65µm, SWIR 1.6µm, C-Band SAR 5.4GHz).\n"
    "4. ATMOSPHERIC & CLOUD DYNAMICS: Detail convective cloud systems, cumulonimbus towers, tropopause-overshooting tops, anvil cirrus shields, brightness temperature gradients (cold convective cores < 210K / -63°C appearing bright white vs warm ocean/land surfaces 295-315K appearing dark gray/black), frontal boundaries, cyclonic/anticyclonic vorticity, jet stream interaction, and wind shear.\n"
    "5. TERRESTRIAL & HYDROLOGICAL MORPHOLOGY: Explicitly identify geographic subcontinents, peninsulas, regional coastlines, mountain ranges (e.g. Himalayas, Western/Eastern Ghats), river systems (e.g. Ganges, Brahmaputra, Indus), marine waters (Arabian Sea, Bay of Bengal, Indian Ocean), arid zones (e.g. Thar Desert), and land cover categories.\n"
    "6. OPERATIONAL & HAZARD ADVISORIES: Provide concrete situational intelligence on aviation hazards (severe convective turbulence, airframe icing), maritime alerts (squall lines, gale-force winds), disaster warnings (cyclogenesis, flash flooding), and agricultural moisture patterns.\n"
    "7. Clean, professional Markdown formatting with headers (###), bold callouts, telemetry tables, and precision bulleted analyses."
)


def call_cloud_vlm(
    prompt: str,
    image_a: Image.Image,
    image_b: Optional[Image.Image] = None,
    system_instruction: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2500,
) -> str:
    """Send image(s) and prompt to OpenRouter Cloud VLM API."""
    key = get_api_key()
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://github.com/AeroLens/AeroLens-AI",
        "X-Title": "AeroLens AI Remote Sensing Intelligence",
        "Content-Type": "application/json",
    }

    content: List[Dict[str, Any]] = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": pil_to_data_uri(image_a)}},
    ]

    if image_b is not None:
        content.append({
            "type": "image_url",
            "image_url": {"url": pil_to_data_uri(image_b)},
        })

    sys_prompt = system_instruction or DEFAULT_SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content},
    ]

    candidate_models = [model, "inclusionai/ling-3.0-flash-vl:free", "google/gemini-3.5-flash-lite", "qwen/qwen3.8-flash"]

    last_err = None
    for cand_model in candidate_models:
        payload = {
            "model": cand_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }

        try:
            resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=40)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
            else:
                last_err = f"API {cand_model} HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            last_err = f"Request error ({cand_model}): {e}"
            continue

    raise RuntimeError(f"Cloud VLM inference failed across candidate models. Details: {last_err}")
