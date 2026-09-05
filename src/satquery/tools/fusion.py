import cv2
import base64
import numpy as np
from io import BytesIO
from typing import Dict, Any, List
from PIL import Image

from satquery.tools.base import BaseTool
from satquery.models.engine import RemoteSensingVLMEngine

class OpticalSARFusionTool(BaseTool):
    name = "optical_sar_fusion"
    description = "Fuses Sentinel-2 Optical and Sentinel-1 SAR (Radar) multi-sensor imagery for all-weather feature extraction."
    
    def __init__(self):
        self.engine = RemoteSensingVLMEngine.get_instance()
        
    def _create_fused_composite(self, optical_img: Image.Image, sar_img: Image.Image):
        """
        Creates a multi-sensor composite:
        - Side-by-side view (Optical | SAR | Fused RGB Composite)
        - Fused image where SAR backscatter enhances optical cloud-penetration and structural edges.
        """
        opt_arr = np.array(optical_img.convert("RGB"))
        sar_arr = np.array(sar_img.convert("L"))
        
        # Match dimensions if needed
        if opt_arr.shape[:2] != sar_arr.shape[:2]:
            sar_arr = cv2.resize(sar_arr, (opt_arr.shape[1], opt_arr.shape[0]))
            
        # Create Fused False-Color (R: Optical Red, G: Optical Green, B: SAR Radar Intensity)
        fused_arr = np.zeros_like(opt_arr)
        fused_arr[:, :, 0] = opt_arr[:, :, 0] # Red from optical
        fused_arr[:, :, 1] = opt_arr[:, :, 1] # Green from optical
        fused_arr[:, :, 2] = sar_arr           # Blue from SAR backscatter
        
        fused_img = Image.fromarray(fused_arr, mode="RGB")
        
        # 3-panel comparison panorama
        w, h = optical_img.size
        sbs = Image.new("RGB", (w * 3, h))
        sbs.paste(optical_img, (0, 0))
        sbs.paste(sar_img.convert("RGB"), (w, 0))
        sbs.paste(fused_img, (w * 2, 0))
        
        return fused_img, sbs

    def run(self, images: List[Image.Image], query: str, **kwargs) -> Dict[str, Any]:
        if len(images) < 2:
            return {"answer": "Optical-SAR fusion requires two co-registered images (Optical Sentinel-2 and SAR Sentinel-1).", "confidence": 0.0}
            
        optical_img, sar_img = images[0], images[1]
        fused_img, sbs_img = self._create_fused_composite(optical_img, sar_img)
        
        # Dual-image multimodal synthesis prompt
        fusion_prompt = (
            f"You are given two co-registered satellite images of the same location:\n"
            f"- Image 1: Sentinel-2 Optical (visible RGB spectrum, land-cover colors, subject to cloud cover)\n"
            f"- Image 2: Sentinel-1 Synthetic Aperture Radar / SAR (cloud-penetrating radar backscatter: smooth water appears dark, metallic/urban corner structures appear bright white)\n\n"
            f"User Analytical Query: '{query}'\n\n"
            f"Synthesize the multi-sensor observations into a comprehensive remote-sensing assessment. "
            f"Explicitly explain how combining optical spectral data with SAR radar backscatter overcomes single-sensor limitations (e.g. penetrating cloud cover, resolving water boundaries, distinguishing built-up structures)."
        )
        
        synthesis = self.engine.multi_image_query([optical_img, sar_img], fusion_prompt, system_prefix=True)
        
        # Encode visual artifacts to base64
        buf_fused = BytesIO()
        fused_img.save(buf_fused, format="PNG")
        fused_b64 = "data:image/png;base64," + base64.b64encode(buf_fused.getvalue()).decode("utf-8")
        
        buf_sbs = BytesIO()
        sbs_img.save(buf_sbs, format="JPEG", quality=90)
        sbs_b64 = "data:image/jpeg;base64," + base64.b64encode(buf_sbs.getvalue()).decode("utf-8")
        
        full_answer = (
            f"### 📡 Multi-Modal Optical–SAR Fusion Analysis\n\n"
            f"• **Sentinel-2 Optical**: Spectral color reflectance and surface texture\n"
            f"• **Sentinel-1 SAR**: Active radar backscatter, cloud penetration, dielectric roughness\n\n"
            f"{synthesis}"
        )
        
        return {
            "answer": full_answer,
            "task": "optical_sar_fusion",
            "confidence": 0.95,
            "evidence": {
                "overlay_image_base64": fused_b64,
                "side_by_side_base64": sbs_b64
            }
        }
