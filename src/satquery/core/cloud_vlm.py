"""SatQuery AI — Cloud Vision-Language Model (VLM) Engine via OpenRouter.

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
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

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
    if not key and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
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
                        elif "bbox" in item and isinstance(item["bbox"], list) and len(item["bbox"]) == 4:
                            coords = [float(x) for x in item["bbox"]]
                        elif all(k in item for k in ("ymin", "xmin", "ymax", "xmax")):
                            coords = [float(item["ymin"]), float(item["xmin"]), float(item["ymax"]), float(item["xmax"])]

                        if coords:
                            xmin, ymin, xmax, ymax = _normalize_box(coords, w, h)
                            if (xmax - xmin) > 4 and (ymax - ymin) > 4:
                                key = (xmin // 4, ymin // 4, xmax // 4, ymax // 4)
                                if key not in seen_boxes:
                                    seen_boxes.add(key)
                                    color = get_category_color(label)
                                    results.append({
                                        "id": f"det_{len(results) + 1}",
                                        "label": str(label).strip(),
                                        "category": str(label).strip().title(),
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

    return results


def draw_bounding_boxes(img: Image.Image, bboxes: List[Dict[str, Any]]) -> Image.Image:
    """Draw aerospace tactical HUD bounding boxes with semi-transparent fills, outer strokes, corner reticles, and label badges."""
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
        fill_color = (color[0], color[1], color[2], 50)  # ~20% opacity tinted fill
        border_color = (color[0], color[1], color[2], 240)

        # 1. Semi-transparent fill + solid outer border
        draw.rectangle([xmin, ymin, xmax, ymax], fill=fill_color, outline=border_color, width=3)

        # 2. Tactical Corner Reticles / Crosshairs
        box_w = xmax - xmin
        box_h = ymax - ymin
        arm = max(6, min(18, box_w // 4, box_h // 4))
        reticle_color = (255, 255, 255, 250)
        draw.line([(xmin, ymin), (xmin + arm, ymin)], fill=reticle_color, width=4)
        draw.line([(xmin, ymin), (xmin, ymin + arm)], fill=reticle_color, width=4)
        draw.line([(xmax, ymin), (xmax - arm, ymin)], fill=reticle_color, width=4)
        draw.line([(xmax, ymin), (xmax, ymin + arm)], fill=reticle_color, width=4)
        draw.line([(xmin, ymax), (xmin + arm, ymax)], fill=reticle_color, width=4)
        draw.line([(xmin, ymax), (xmin, ymax - arm)], fill=reticle_color, width=4)
        draw.line([(xmax, ymax), (xmax - arm, ymax)], fill=reticle_color, width=4)
        draw.line([(xmax, ymax), (xmax, ymax - arm)], fill=reticle_color, width=4)

        # 3. Label Tag Badge with dark contrast backing
        tag_text = f"{label.upper()} #{idx + 1} ({int(conf * 100)}%)"
        tag_h = 20
        tag_w = max(70, len(tag_text) * 7 + 12)
        tag_y1 = max(0, ymin - tag_h - 2)
        tag_y2 = tag_y1 + tag_h

        draw.rectangle([xmin, tag_y1, xmin + tag_w, tag_y2], fill=(15, 23, 42, 230), outline=border_color, width=1)
        draw.text((xmin + 6, tag_y1 + 3), tag_text, fill=(255, 255, 255, 255))

    return overlay.convert("RGB")


def parse_and_draw_boxes(img: Image.Image, text: str) -> Optional[Image.Image]:
    """Parse bounding boxes in text and render reticle. Returns annotated PIL Image."""
    w, h = img.size
    bboxes = extract_bounding_boxes(text, w, h)
    if not bboxes:
        return None
    return draw_bounding_boxes(img, bboxes)


def parse_boxes_with_metadata(img: Image.Image, text: str) -> Tuple[Optional[Image.Image], List[Dict[str, Any]]]:
    """Parse bounding boxes in text, return BOTH the annotated PIL Image and structured object metadata."""
    w, h = img.size
    bboxes = extract_bounding_boxes(text, w, h)
    if not bboxes:
        return None, []
    annotated = draw_bounding_boxes(img, bboxes)
    return annotated, bboxes


def call_cloud_vlm(
    prompt: str,
    image_a: Image.Image,
    image_b: Optional[Image.Image] = None,
    system_instruction: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 500,
) -> str:
    """Send image(s) and prompt to OpenRouter Cloud VLM API."""
    key = get_api_key()
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://github.com/SatQuery/SatQuery-AI",
        "X-Title": "SatQuery AI Remote Sensing Intelligence",
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

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": content})

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
