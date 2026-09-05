import base64
from io import BytesIO
from typing import Dict, Any, List
from PIL import Image
from satquery.tools.base import BaseTool
from satquery.models.engine import RemoteSensingVLMEngine
from satquery.core.schemas import BoundingBox

class VQATool(BaseTool):
    name = "vqa_captioning"
    description = "Answers natural language questions and provides structured, in-depth scene analysis for satellite and remote sensing imagery."
    
    def __init__(self):
        self.engine = RemoteSensingVLMEngine.get_instance()
        
    def run(self, images: List[Image.Image], query: str, **kwargs) -> Dict[str, Any]:
        if not images:
            return {"answer": "No satellite image provided for VQA analysis.", "confidence": 0.0}
            
        img = images[0]
        is_caption_query = any(k in query.lower() for k in ["caption", "describe", "overview", "what this image shows", "what is shown", "summary", "explain it"])
        
        answer = self.engine.query(img, query, system_prefix=True)
            
        # Confidence heuristic based on domain keyword presence
        rs_keywords = ["water", "vegetation", "urban", "runway", "building", "river", "forest", "field", "structure", "road", "terrain", "insat", "thermal", "cloud", "infrared", "sensor", "satellite"]
        keyword_hits = sum(1 for kw in rs_keywords if kw in answer.lower())
        confidence = min(0.98, max(0.85, 0.80 + (keyword_hits * 0.02)))
        
        # Extract salient scene candidate bounding boxes for visual evidence
        m = self.engine._analyze_imagery_spectrum(img)
        raw_candidates = m.get("detected_objects", [])[:6]
        
        bboxes_list = [
            BoundingBox(
                ymin=b["ymin"], xmin=b["xmin"], ymax=b["ymax"], xmax=b["xmax"],
                label=b.get("label", "salient_structure")
            ) for b in raw_candidates
        ]
        
        return {
            "answer": answer,
            "task": "captioning" if is_caption_query else "vqa",
            "confidence": round(confidence, 2),
            "evidence": {
                "analyzed_image_size": f"{img.width}x{img.height}",
                "bboxes": [b.model_dump() for b in bboxes_list],
                "cloud_pct": m.get("cloud_pct", 0.0),
                "veg_pct": m.get("veg_pct", 0.0),
                "water_pct": m.get("water_pct", 0.0),
                "urban_pct": m.get("urban_pct", 0.0)
            }
        }
