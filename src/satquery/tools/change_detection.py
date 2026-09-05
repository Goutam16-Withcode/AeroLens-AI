import cv2
import base64
import numpy as np
from io import BytesIO
from typing import Dict, Any, List
from PIL import Image

from satquery.tools.base import BaseTool
from satquery.models.engine import RemoteSensingVLMEngine

class ChangeDetectionTool(BaseTool):
    name = "change_detection"
    description = "Analyzes bi-temporal satellite image pairs (T1 and T2) using OpenCV diff and VLM semantic interpretation."
    
    def __init__(self):
        self.engine = RemoteSensingVLMEngine.get_instance()
        
    def _compute_pixel_diff(self, img1: Image.Image, img2: Image.Image):
        """Computes OpenCV grayscale difference, threshold mask, and contour bounding boxes."""
        cv1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2BGR)
        cv2_img = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2BGR)
        
        # Match dimensions
        if cv1.shape[:2] != cv2_img.shape[:2]:
            cv2_img = cv2.resize(cv2_img, (cv1.shape[1], cv1.shape[0]))
            
        gray1 = cv2.cvtColor(cv1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray1, gray2)
        blurred = cv2.GaussianBlur(diff, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 35, 255, cv2.THRESH_BINARY)
        
        # Morphological filtering
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        cleaned_mask = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_OPEN, kernel)
        
        total_pixels = cleaned_mask.shape[0] * cleaned_mask.shape[1]
        changed_pixels = cv2.countNonZero(cleaned_mask)
        change_pct = (changed_pixels / total_pixels) * 100.0
        
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        change_boxes = []
        h, w = cleaned_mask.shape
        for c in contours:
            if cv2.contourArea(c) > 200:
                x, y, bw, bh = cv2.boundingRect(c)
                change_boxes.append({
                    "ymin": y / h,
                    "xmin": x / w,
                    "ymax": (y + bh) / h,
                    "xmax": (x + bw) / w,
                    "area_px": cv2.contourArea(c)
                })
                
        # Heatmap overlay on T2
        overlay = cv2_img.copy()
        color_mask = np.zeros_like(cv2_img)
        color_mask[cleaned_mask > 0] = [0, 50, 255] # Red BGR
        blended = cv2.addWeighted(overlay, 0.7, color_mask, 0.6, 0)
        
        for b in change_boxes:
            bx1, by1 = int(b["xmin"] * w), int(b["ymin"] * h)
            bx2, by2 = int(b["xmax"] * w), int(b["ymax"] * h)
            cv2.rectangle(blended, (bx1, by1), (bx2, by2), (0, 255, 255), 2)
            
        blended_rgb = cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
        mask_rgb = cv2.cvtColor(cleaned_mask, cv2.COLOR_GRAY2RGB)
        
        return Image.fromarray(blended_rgb), Image.fromarray(mask_rgb), change_pct, len(change_boxes)

    def _create_side_by_side(self, t1: Image.Image, t2: Image.Image, overlay: Image.Image) -> Image.Image:
        w, h = t1.size
        combined = Image.new("RGB", (w * 3, h))
        combined.paste(t1, (0, 0))
        combined.paste(t2, (w, 0))
        combined.paste(overlay, (w * 2, 0))
        return combined

    def run(self, images: List[Image.Image], query: str, **kwargs) -> Dict[str, Any]:
        if len(images) < 2:
            return {"answer": "Change detection requires two bi-temporal images (T1 before and T2 after).", "confidence": 0.0}
            
        t1, t2 = images[0], images[1]
        overlay_img, mask_img, change_pct, num_zones = self._compute_pixel_diff(t1, t2)
        side_by_side = self._create_side_by_side(t1, t2, overlay_img)
        
        # Multi-image vision prompt
        prompt = (
            f"You are comparing two bi-temporal satellite images of the exact same location:\n"
            f"- Image 1: Earlier timestamp (T1 before)\n"
            f"- Image 2: Later timestamp (T2 after)\n\n"
            f"An automated OpenCV diff algorithm detected {change_pct:.1f}% surface change across {num_zones} regional clusters.\n"
            f"User Analytical Query: '{query}'\n\n"
            f"Perform a detailed comparative analysis:\n"
            f"1. Describe what specifically changed between T1 and T2 (e.g. vegetation clearing, urban development, new buildings, roads, water level changes).\n"
            f"2. Note the geographical locations of the major modifications."
        )
        
        semantic_narrative = self.engine.multi_image_query([t1, t2], prompt, system_prefix=True)
        
        # Base64 encoding
        buf_overlay = BytesIO()
        overlay_img.save(buf_overlay, format="PNG")
        overlay_b64 = "data:image/png;base64," + base64.b64encode(buf_overlay.getvalue()).decode("utf-8")
        
        buf_sbs = BytesIO()
        side_by_side.save(buf_sbs, format="JPEG", quality=90)
        sbs_b64 = "data:image/jpeg;base64," + base64.b64encode(buf_sbs.getvalue()).decode("utf-8")
        
        full_answer = (
            f"### 🔄 Bi-Temporal Change Detection Analysis\n\n"
            f"• **Surface Change Area**: `{change_pct:.2f}%` of scene altered\n"
            f"• **Identified Change Zones**: `{num_zones}` significant regional clusters\n\n"
            f"{semantic_narrative}"
        )
        
        return {
            "answer": full_answer,
            "task": "change_detection",
            "confidence": 0.94,
            "evidence": {
                "change_percentage": round(change_pct, 2),
                "num_change_zones": num_zones,
                "overlay_image_base64": overlay_b64,
                "side_by_side_base64": sbs_b64
            }
        }
