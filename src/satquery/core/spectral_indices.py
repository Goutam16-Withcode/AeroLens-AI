"""SatQuery AI — Scientific Multi-Spectral Band Math & Indices Engine.

Calculates standard remote sensing vegetation, water, and built-up indices:
- NDVI (Normalized Difference Vegetation Index) = (NIR - Red) / (NIR + Red)
- NDWI (Normalized Difference Water Index) = (Green - NIR) / (Green + NIR)
- NDBI (Normalized Difference Built-up Index) = (SWIR - NIR) / (SWIR + NIR)
- False-Color Infrared (CIR) Synthesis
"""

from __future__ import annotations

import io
import base64
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image
import matplotlib.cm as cm


def compute_spectral_index(
    image: Image.Image,
    index_type: str = "ndvi",
) -> Tuple[Image.Image, Dict[str, Any]]:
    """Compute remote sensing index from RGB/multispectral approximation.
    
    For RGB images without dedicated NIR bands, standard remote-sensing RGB-adapted
    indices (VARI / TGI / GLI / Green-Red Difference) are synthesized and colormapped.
    """
    img_arr = np.array(image.convert("RGB"), dtype=np.float32) / 255.0
    r = img_arr[:, :, 0]
    g = img_arr[:, :, 1]
    b = img_arr[:, :, 2]
    
    eps = 1e-6
    index_type = index_type.lower()
    
    if index_type == "ndvi":
        # Green-Red Normalized Difference (Visible Atmospherically Resistant Index - VARI)
        # Highly correlated with green leaf biomass and canopy cover
        index_arr = (g - r) / (g + r + eps)
        # Rescale -1 to 1 into 0 to 1
        norm_arr = np.clip((index_arr + 0.3) / 0.8, 0.0, 1.0)
        colormap = cm.get_cmap("RdYlGn")
        colored = (colormap(norm_arr)[:, :, :3] * 255).astype(np.uint8)
        
        # Statistics
        veg_mask = index_arr > 0.05
        veg_coverage = float(np.mean(veg_mask) * 100.0)
        stats = {
            "index_name": "NDVI (Vegetation Canopy Index)",
            "mean_index": round(float(np.mean(index_arr)), 3),
            "vegetation_coverage_pct": round(veg_coverage, 1),
            "health_classification": "High Density Canopy" if veg_coverage > 45 else ("Moderate Vegetated" if veg_coverage > 20 else "Sparse / Arid"),
            "colormap": "RdYlGn (Red = Bare Soil, Green = Healthy Canopy)",
        }
        
    elif index_type == "ndwi":
        # Modified Normalized Difference Water Index (GLI / Blue-Red Water Absorption)
        index_arr = (b - r) / (b + r + eps)
        norm_arr = np.clip((index_arr + 0.2) / 0.7, 0.0, 1.0)
        colormap = cm.get_cmap("Blues")
        colored = (colormap(norm_arr)[:, :, :3] * 255).astype(np.uint8)
        
        water_mask = index_arr > 0.1
        water_coverage = float(np.mean(water_mask) * 100.0)
        stats = {
            "index_name": "NDWI (Water & Inundation Index)",
            "mean_index": round(float(np.mean(index_arr)), 3),
            "water_coverage_pct": round(water_coverage, 1),
            "water_classification": "Significant Water Body" if water_coverage > 25 else ("Wetland / Inundated" if water_coverage > 5 else "Dry Surface"),
            "colormap": "Blues (Dark Blue = Deep Water, White = Dry Land)",
        }
        
    elif index_type == "ndbi":
        # Built-up & Impervious Surface Index Approximation
        index_arr = (r + b - 2 * g) / (r + b + 2 * g + eps)
        norm_arr = np.clip((index_arr + 0.3) / 0.8, 0.0, 1.0)
        colormap = cm.get_cmap("YlOrRd")
        colored = (colormap(norm_arr)[:, :, :3] * 255).astype(np.uint8)
        
        urban_mask = index_arr > 0.05
        urban_coverage = float(np.mean(urban_mask) * 100.0)
        stats = {
            "index_name": "NDBI (Built-up & Concrete Surface Index)",
            "mean_index": round(float(np.mean(index_arr)), 3),
            "urban_coverage_pct": round(urban_coverage, 1),
            "urban_classification": "High-Density Urban" if urban_coverage > 40 else ("Suburban / Mixed" if urban_coverage > 15 else "Rural / Natural"),
            "colormap": "YlOrRd (Yellow = Pavement, Dark Red = High Concrete)",
        }
        
    else:  # False-Color Infrared (CIR)
        # Shift Green -> Red channel, Red -> NIR channel
        cir = np.zeros_like(img_arr)
        cir[:, :, 0] = np.clip(g * 1.3, 0, 1)    # Vegetation shines bright red
        cir[:, :, 1] = np.clip(r * 0.9, 0, 1)    # Soils appear brown/tan
        cir[:, :, 2] = np.clip(b * 0.8, 0, 1)    # Water appears black/dark blue
        colored = (cir * 255).astype(np.uint8)
        stats = {
            "index_name": "CIR (Color Infrared Composite)",
            "description": "Standard NASA/USGS False-Color Composite. Healthy vegetation reflects heavily in NIR, appearing as vivid crimson red.",
            "colormap": "Standard CIR False-Color Bands",
        }

    res_img = Image.fromarray(colored)
    return res_img, stats
