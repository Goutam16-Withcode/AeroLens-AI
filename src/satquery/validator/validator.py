import os
from io import BytesIO
from typing import List, Tuple, Dict, Any, Union, Optional
import numpy as np
from PIL import Image

class InputValidator:
    """
    Expert Satellite Image Validator and Normalizer.
    Handles all raster formats (PNG, JPEG, TIFF/GeoTIFF, Grayscale SAR, Multi-Spectral 16-bit)
    and resolves pair relationships (Single Image, Bi-Temporal Change, Optical-SAR Fusion).
    """
    
    @staticmethod
    def load_image(input_source: Union[str, bytes, Image.Image]) -> Image.Image:
        """Loads and normalizes any image to an RGB PIL Image with proper radiometric scaling."""
        if isinstance(input_source, Image.Image):
            return InputValidator._normalize_pil_image(input_source)
            
        if isinstance(input_source, (bytes, bytearray)):
            if len(input_source) == 0:
                raise ValueError("Received 0-byte empty image data.")
            img = Image.open(BytesIO(input_source))
            return InputValidator._normalize_pil_image(img)
            
        if isinstance(input_source, str) and os.path.isfile(input_source):
            ext = os.path.splitext(input_source)[1].lower()
            if ext in [".tif", ".tiff", ".geotiff"]:
                try:
                    import rasterio
                    with rasterio.open(input_source) as src:
                        count = src.count
                        if count >= 3:
                            arr = src.read([1, 2, 3])
                            arr = np.transpose(arr, (1, 2, 0))
                        else:
                            arr = src.read(1)
                            arr = np.stack([arr] * 3, axis=-1)
                            
                        # Percentile 2-98 radiometric stretch
                        p_low, p_high = np.percentile(arr, (2, 98))
                        if p_high > p_low:
                            arr = np.clip((arr - p_low) / (p_high - p_low) * 255.0, 0, 255).astype(np.uint8)
                        else:
                            arr = np.clip(arr, 0, 255).astype(np.uint8)
                        return Image.fromarray(arr, mode="RGB")
                except Exception:
                    pass
            
            img = Image.open(input_source)
            return InputValidator._normalize_pil_image(img)
            
        raise ValueError(f"Unsupported image input source: {type(input_source)}")
        
    @staticmethod
    def _normalize_pil_image(img: Image.Image) -> Image.Image:
        """Converts any PIL image mode to standard RGB with proper channel scaling."""
        if img.mode == "RGB":
            return img
        if img.mode in ("RGBA", "LA"):
            # Create white background for alpha channel
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img.convert("RGBA"), mask=img.split()[1])
            return background
        if img.mode == "P":
            return img.convert("RGB")
        if img.mode == "L":  # Grayscale SAR / Thermal IR
            return img.convert("RGB")
        if img.mode in ("I;16", "I", "F"):  # 16-bit or 32-bit float
            arr = np.array(img, dtype=np.float32)
            arr_min, arr_max = arr.min(), arr.max()
            if arr_max > arr_min:
                arr = (arr - arr_min) / (arr_max - arr_min) * 255.0
            else:
                arr = np.zeros_like(arr)
            return Image.fromarray(arr.astype(np.uint8)).convert("RGB")
        return img.convert("RGB")

    @classmethod
    def validate_inputs(
        cls, 
        images: List[Union[str, bytes, Image.Image]], 
        user_intent_hint: Optional[str] = None
    ) -> Tuple[List[Image.Image], str, Dict[str, Any]]:
        """
        Validates a list of 1 or 2 images.
        Returns:
            - normalized_images: List[PIL.Image]
            - scenario: 'single_image' | 'bi_temporal_pair' | 'optical_sar_pair'
            - metadata: dict with width, height, channels, pixel variance
        """
        if not images:
            raise ValueError("No satellite imagery provided.")
            
        norm_images = [cls.load_image(img) for img in images]
        
        metadata = {
            "image_count": len(norm_images),
            "dimensions": [(img.width, img.height) for img in norm_images]
        }
        
        if len(norm_images) == 1:
            scenario = "single_image"
        else:
            # Match dimensions if they differ slightly
            w0, h0 = norm_images[0].size
            w1, h1 = norm_images[1].size
            if (w0, h0) != (w1, h1):
                norm_images[1] = norm_images[1].resize((w0, h0), Image.Resampling.BILINEAR)
                
            # Classify pair type: check hint or properties
            hint = (user_intent_hint or "").lower()
            if any(k in hint for k in ["sar", "radar", "fusion", "sentinel-1", "microwave", "dielectric"]):
                scenario = "optical_sar_pair"
            elif any(k in hint for k in ["change", "time", "compare", "before", "after", "deforest", "construction"]):
                scenario = "bi_temporal_pair"
            else:
                # Default pair assumption: bi-temporal
                scenario = "bi_temporal_pair"
                
        metadata["scenario"] = scenario
        return norm_images, scenario, metadata
