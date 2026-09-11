"""SatQuery AI — Cloud Vision-Language Model (VLM) Engine via OpenRouter.

Provides zero-startup, high-throughput cloud inference for remote sensing:
- Single-image VQA & Land-cover captioning
- Text-guided object grounding with coordinate parsing & tactical reticles
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
from PIL import Image, ImageDraw

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash-vl:free")
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")


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


def parse_and_draw_boxes(img: Image.Image, text: str) -> Optional[Image.Image]:
    """Parse bounding boxes in text [ymin, xmin, ymax, xmax] or [xmin, ymin, xmax, ymax] and render reticle."""
    w, h = img.size
    boxed_img = img.copy().convert("RGB")
    draw = ImageDraw.Draw(boxed_img)
    
    # Match patterns like [120, 340, 500, 600] or [[y1, x1, y2, x2]]
    box_patterns = re.findall(r'\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]', text)
    
    drawn_count = 0
    for coords in box_patterns:
        try:
            c = [float(x) for x in coords]
            # Check if normalized 0-1000 or 0-1
            if max(c) <= 1.0:
                y1, x1, y2, x2 = c[0] * h, c[1] * w, c[2] * h, c[3] * w
            elif max(c) <= 1000:
                y1, x1, y2, x2 = (c[0] / 1000.0) * h, (c[1] / 1000.0) * w, (c[2] / 1000.0) * h, (c[3] / 1000.0) * w
            else:
                y1, x1, y2, x2 = c[0], c[1], c[2], c[3]
            
            xmin, ymin = max(0, min(x1, x2)), max(0, min(y1, y2))
            xmax, ymax = min(w, max(x1, x2)), min(h, max(y1, y2))
            
            if xmax - xmin > 5 and ymax - ymin > 5:
                draw.rectangle([xmin, ymin, xmax, ymax], outline=(245, 158, 11), width=3)
                # Corner reticles
                arm = min(15, (xmax - xmin) / 4, (ymax - ymin) / 4)
                draw.line([(xmin, ymin), (xmin + arm, ymin)], fill=(251, 191, 36), width=4)
                draw.line([(xmin, ymin), (xmin, ymin + arm)], fill=(251, 191, 36), width=4)
                draw.line([(xmax, ymax), (xmax - arm, ymax)], fill=(251, 191, 36), width=4)
                draw.line([(xmax, ymax), (xmax, ymax - arm)], fill=(251, 191, 36), width=4)
                drawn_count += 1
        except Exception:
            continue

    return boxed_img if drawn_count > 0 else None


def call_cloud_vlm(
    prompt: str,
    image_a: Image.Image,
    image_b: Optional[Image.Image] = None,
    system_instruction: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 400,
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
