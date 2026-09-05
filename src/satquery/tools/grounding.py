import base64
import re
import json
from io import BytesIO
from typing import Dict, Any, List
import numpy as np
from PIL import Image, ImageDraw

from satquery.tools.base import BaseTool
from satquery.models.engine import RemoteSensingVLMEngine
from satquery.core.schemas import BoundingBox

class GroundingTool(BaseTool):
    name = "grounding_localization"
    description = "Locates target objects, structures, or natural features in satellite imagery, outputs normalized 2D bounding boxes, and draws visual overlays."
    
    def __init__(self):
        self.engine = RemoteSensingVLMEngine.get_instance()
        
    def _extract_target_entity(self, query: str) -> str:
        """Extracts the precise target entity from user query across diverse phrasing patterns."""
        patterns = [
            r"locate\s+(?:all\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+on|\s+at|\.|\?|$)",
            r"find\s+(?:all\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+on|\s+at|\.|\?|$)",
            r"where\s+is\s+(?:the\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+located|\.|\?|$)",
            r"where\s+are\s+(?:the\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+located|\.|\?|$)",
            r"highlight\s+(?:all\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+on|\s+at|\.|\?|$)",
            r"detect\s+(?:all\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+on|\s+at|\.|\?|$)",
            r"point\s+(?:out\s+)?(?:all\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+on|\s+at|\.|\?|$)",
            r"show\s+(?:me\s+)?(?:all\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+on|\s+at|\.|\?|$)",
            r"bounding\s+box\s+(?:for\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+on|\.|\?|$)",
            r"identify\s+(?:the\s+)?([a-zA-Z\s\-]+?)(?:\s+in|\s+on|\.|\?|$)"
        ]
        for p in patterns:
            m = re.search(p, query, re.IGNORECASE)
            if m:
                target = m.group(1).strip()
                target = re.sub(r"^(the|a|an|all|any|parked|visible|circular|active)\s+", "", target, flags=re.IGNORECASE)
                if len(target) > 1 and target.lower() not in ["image", "scene", "satellite", "view", "things"]:
                    return target
                    
        # Check standard remote sensing targets in query
        q_low = query.lower()
        if "airplane" in q_low or "plane" in q_low or "aircraft" in q_low or "jet" in q_low:
            return "airplane"
        if "tank" in q_low or "storage" in q_low or "fuel" in q_low or "silo" in q_low:
            return "storage_tank"
        if "ship" in q_low or "vessel" in q_low or "boat" in q_low or "marine" in q_low:
            return "ship"
        if "runway" in q_low or "taxiway" in q_low or "tarmac" in q_low or "apron" in q_low:
            return "runway"
        if "building" in q_low or "facility" in q_low or "house" in q_low or "roof" in q_low or "warehouse" in q_low:
            return "building"
        if "bridge" in q_low or "crossing" in q_low or "overpass" in q_low:
            return "bridge"
        if "water" in q_low or "river" in q_low or "reservoir" in q_low or "lake" in q_low:
            return "water_body"
        if "forest" in q_low or "tree" in q_low or "vegetation" in q_low or "green" in q_low:
            return "forest_canopy"
        if "crop" in q_low or "farm" in q_low or "field" in q_low or "agriculture" in q_low:
            return "agricultural_plot"
        if "cloud" in q_low or "storm" in q_low or "cyclone" in q_low or "convective" in q_low:
            return "convective_core"
        if "car" in q_low or "vehicle" in q_low or "truck" in q_low:
            return "vehicle"
            
        return "salient_feature"

    def _draw_bboxes(self, image: Image.Image, bboxes: List[Dict[str, Any]]) -> Image.Image:
        overlay = image.copy().convert("RGBA")
        draw = ImageDraw.Draw(overlay, "RGBA")
        w, h = image.size
        
        colors = [
            (0, 230, 118, 230),   # Neon green
            (255, 23, 68, 230),    # Crimson red
            (0, 229, 255, 230),   # Cyan
            (255, 214, 0, 230),   # Amber
            (168, 85, 247, 230),  # Purple
            (255, 109, 0, 230)    # Deep Orange
        ]
        
        for idx, box in enumerate(bboxes):
            ymin, xmin, ymax, xmax = box["ymin"], box["xmin"], box["ymax"], box["xmax"]
            x1, y1 = max(0, int(xmin * w)), max(0, int(ymin * h))
            x2, y2 = min(w, int(xmax * w)), min(h, int(ymax * h))
            color = colors[idx % len(colors)]
            fill_color = (color[0], color[1], color[2], 45)
            
            # Semi-transparent box & solid border
            draw.rectangle([x1, y1, x2, y2], fill=fill_color, outline=color, width=3)
            
            # Corner targeting reticles
            corner_len = min(18, max(5, (x2 - x1) // 4), max(5, (y2 - y1) // 4))
            draw.line([(x1, y1), (x1 + corner_len, y1)], fill=(255, 255, 255, 255), width=4)
            draw.line([(x1, y1), (x1, y1 + corner_len)], fill=(255, 255, 255, 255), width=4)
            draw.line([(x2, y2), (x2 - corner_len, y2)], fill=(255, 255, 255, 255), width=4)
            draw.line([(x2, y2), (x2, y2 - corner_len)], fill=(255, 255, 255, 255), width=4)
            
            # Label badge with dark backing
            label_text = f"{box.get('label', 'target')} #{idx+1}"
            tag_h = 22
            tag_w = max(75, len(label_text) * 8 + 14)
            tag_y1 = max(0, y1 - tag_h)
            draw.rectangle([x1, tag_y1, x1 + tag_w, tag_y1 + tag_h], fill=(15, 23, 42, 235), outline=color, width=1)
            draw.text((x1 + 6, tag_y1 + 4), label_text, fill=(255, 255, 255, 255))
            
        return overlay.convert("RGB")

    def run(self, images: List[Image.Image], query: str, **kwargs) -> Dict[str, Any]:
        if not images:
            return {"answer": "No image provided for grounding analysis.", "confidence": 0.0}
            
        img = images[0]
        target_entity = self._extract_target_entity(query)
        narrative, raw_boxes = self.engine.detect(img, target_entity)
        
        annotated_img = self._draw_bboxes(img, raw_boxes) if raw_boxes else img
        buf = BytesIO()
        annotated_img.save(buf, format="PNG")
        overlay_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
        
        num_detected = len(raw_boxes)
        structured_answer = (
            f"### 🎯 Visual Grounding & Localization Report\n\n"
            f"• **Target Entity**: `{target_entity}`\n"
            f"• **Instances Localized**: `{num_detected}`\n"
            f"• **Bounding Box Extraction**: `{num_detected} coordinates normalized to [0.0, 1.0]`\n\n"
            f"**Detailed Spatial Assessment:**\n{narrative}"
        )
        
        bboxes_list = [
            BoundingBox(
                ymin=b["ymin"], xmin=b["xmin"], ymax=b["ymax"], xmax=b["xmax"],
                label=b.get("label", target_entity)
            ) for b in raw_boxes
        ]
        
        return {
            "answer": structured_answer,
            "task": "grounding",
            "confidence": 0.94 if num_detected > 0 else 0.82,
            "evidence": {
                "bboxes": [b.model_dump() for b in bboxes_list],
                "overlay_image_base64": overlay_b64,
                "detected_count": num_detected,
                "target_entity": target_entity
            }
        }
