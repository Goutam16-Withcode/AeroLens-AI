"""
SatQuery AI — Benchmark Dataset Manager
Generates and manages sample datasets for all problem-statement benchmarks:
1. VRSBench (data/samples/vrsbench/) — High-res optical airfield with parked aircraft, fuel tanks, runway.
2. RSVQA (data/samples/rsvqa/) — Multi-feature land cover (river, residential rooftops, agricultural plots).
3. CDVQA (data/samples/cdvqa/) — Bi-temporal (T1 2023 vs T2 2025) before/after change detection pair.
4. BigEarthNet (data/samples/bigearthnet/) — Co-registered Sentinel-2 Optical + Sentinel-1 SAR Radar pair.
5. INSAT-3DS (data/samples/insat3ds/) — Meteorological Thermal Infrared TIR1 @ 10.83 µm with convective cloud dynamics.
"""

import os
import sys
import json
import argparse
import numpy as np
from PIL import Image, ImageDraw

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(ROOT_DIR, "data", "samples")

def ensure_dirs():
    for name in ["vrsbench", "rsvqa", "cdvqa", "bigearthnet", "insat3ds"]:
        os.makedirs(os.path.join(SAMPLES_DIR, name), exist_ok=True)

# -----------------------------------------------------------------------------
# 1. VRSBench Benchmark Sample
# -----------------------------------------------------------------------------
def build_vrsbench_sample():
    vrs_dir = os.path.join(SAMPLES_DIR, "vrsbench")
    img = Image.new("RGB", (512, 512), (48, 108, 52))
    draw = ImageDraw.Draw(img)
    
    # Runway & Taxiway
    draw.rectangle([100, 0, 220, 512], fill=(70, 70, 75))
    draw.line([(160, 0), (160, 512)], fill=(230, 230, 100), width=3)
    draw.rectangle([220, 200, 420, 300], fill=(85, 85, 90)) # Apron
    
    # Airplanes parked on apron
    draw.polygon([(260, 230), (255, 270), (265, 270)], fill=(245, 245, 245))
    draw.polygon([(240, 250), (280, 250), (260, 245)], fill=(240, 240, 240))
    draw.polygon([(340, 230), (335, 270), (345, 270)], fill=(245, 245, 245))
    draw.polygon([(320, 250), (360, 250), (340, 245)], fill=(240, 240, 240))
    
    # Storage tanks
    draw.ellipse([340, 60, 400, 120], fill=(220, 220, 225), outline=(100, 100, 100), width=2)
    draw.ellipse([420, 60, 480, 120], fill=(220, 220, 225), outline=(100, 100, 100), width=2)
    
    img_path = os.path.join(vrs_dir, "vrsbench_sample_01.png")
    img.save(img_path)
    
    meta = {
        "dataset": "VRSBench",
        "title": "Airfield & Infrastructure Grounding",
        "samples": [{
            "id": 1,
            "filename": "vrsbench_sample_01.png",
            "caption": "An airfield with a north-south asphalt runway, aircraft apron, parked airplanes, and fuel tanks.",
            "preset_queries": [
                "Locate and highlight all parked airplanes on the apron.",
                "Where are the circular fuel storage tanks positioned relative to the runway?",
                "Describe the overall airfield layout and surrounding land cover."
            ],
            "ground_truth_bboxes": [
                {"label": "airplane", "ymin": 0.44, "xmin": 0.46, "ymax": 0.54, "xmax": 0.56},
                {"label": "airplane", "ymin": 0.44, "xmin": 0.62, "ymax": 0.54, "xmax": 0.71},
                {"label": "storage_tank", "ymin": 0.11, "xmin": 0.66, "ymax": 0.24, "xmax": 0.78},
                {"label": "storage_tank", "ymin": 0.11, "xmin": 0.82, "ymax": 0.24, "xmax": 0.94}
            ]
        }]
    }
    with open(os.path.join(vrs_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("  [+] VRSBench:   data/samples/vrsbench/vrsbench_sample_01.png")

# -----------------------------------------------------------------------------
# 2. RSVQA Benchmark Sample
# -----------------------------------------------------------------------------
def build_rsvqa_sample():
    rsv_dir = os.path.join(SAMPLES_DIR, "rsvqa")
    img = Image.new("RGB", (512, 512), (60, 130, 60))
    draw = ImageDraw.Draw(img)
    
    # River
    draw.polygon([(0, 320), (180, 300), (320, 360), (512, 330), (512, 420), (320, 450), (180, 390), (0, 410)], fill=(35, 95, 175))
    # Agricultural plots
    draw.rectangle([20, 30, 180, 180], fill=(195, 175, 75), outline=(120, 100, 30), width=2)
    draw.rectangle([200, 30, 320, 180], fill=(160, 140, 50), outline=(120, 100, 30), width=2)
    # Residential cluster
    roof_colors = [(180, 60, 50), (160, 70, 60), (190, 80, 70), (70, 70, 80)]
    coords = [(380, 40), (430, 45), (375, 100), (435, 110), (390, 160), (445, 170)]
    for (x, y), c in zip(coords, roof_colors * 2):
        draw.rectangle([x, y, x + 35, y + 35], fill=c, outline=(40, 40, 40), width=1)
        
    img_path = os.path.join(rsv_dir, "rsvqa_sample_01.png")
    img.save(img_path)
    
    meta = {
        "dataset": "RSVQA",
        "title": "Land Cover & Infrastructure Counting",
        "samples": [{
            "id": 1,
            "filename": "rsvqa_sample_01.png",
            "preset_queries": [
                "What types of land use are visible in this scene?",
                "How many residential buildings are clustered in the northeast quadrant?",
                "Is there a natural water body dividing the landscape?"
            ]
        }]
    }
    with open(os.path.join(rsv_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("  [+] RSVQA:      data/samples/rsvqa/rsvqa_sample_01.png")

# -----------------------------------------------------------------------------
# 3. CDVQA Bi-temporal Change Detection Sample
# -----------------------------------------------------------------------------
def build_cdvqa_sample():
    cd_dir = os.path.join(SAMPLES_DIR, "cdvqa")
    
    # T1: Forest & River (2023)
    t1 = Image.new("RGB", (512, 512), (35, 100, 40))
    d1 = ImageDraw.Draw(t1)
    d1.polygon([(0, 180), (220, 200), (512, 190), (512, 270), (220, 280), (0, 260)], fill=(30, 80, 160))
    
    # T2: Forest cleared + New industrial building & bridge (2025)
    t2 = t1.copy()
    d2 = ImageDraw.Draw(t2)
    d2.rectangle([80, 40, 280, 160], fill=(185, 160, 120), outline=(130, 110, 80), width=2)
    d2.rectangle([120, 60, 240, 140], fill=(130, 130, 135), outline=(60, 60, 60), width=2)
    d2.rectangle([210, 190, 250, 280], fill=(150, 150, 155), outline=(50, 50, 50), width=2)
    
    t1.save(os.path.join(cd_dir, "t1_before_2023.png"))
    t2.save(os.path.join(cd_dir, "t2_after_2025.png"))
    
    meta = {
        "dataset": "CDVQA",
        "title": "Bi-temporal Infrastructure & Land-Cover Change",
        "samples": [{
            "id": 1,
            "t1_filename": "t1_before_2023.png",
            "t2_filename": "t2_after_2025.png",
            "preset_queries": [
                "What major construction and land-cover changes occurred between T1 and T2?",
                "Identify and quantify the newly constructed structures and road/bridge crossings.",
                "Compare the vegetation density in the northern quadrant between both timestamps."
            ]
        }]
    }
    with open(os.path.join(cd_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("  [+] CDVQA:      data/samples/cdvqa/t1_before_2023.png & t2_after_2025.png")

# -----------------------------------------------------------------------------
# 4. BigEarthNet Optical + SAR Co-registered Sample
# -----------------------------------------------------------------------------
def build_bigearthnet_sample():
    ben_dir = os.path.join(SAMPLES_DIR, "bigearthnet")
    
    optical = Image.new("RGB", (512, 512), (40, 115, 45))
    d_opt = ImageDraw.Draw(optical)
    d_opt.ellipse([150, 150, 420, 400], fill=(25, 75, 145)) # Water reservoir
    for y in range(80, 420, 70):
        d_opt.rectangle([40, y, 100, y + 45], fill=(175, 170, 165)) # Urban structures
    cloud = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d_c = ImageDraw.Draw(cloud)
    d_c.ellipse([200, 180, 460, 360], fill=(240, 245, 255, 160))
    optical = Image.alpha_composite(optical.convert("RGBA"), cloud).convert("RGB")
    
    sar_arr = np.full((512, 512), 65, dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    water_mask = ((x - 285)**2 / (135**2) + (y - 275)**2 / (125**2)) <= 1.0
    sar_arr[water_mask] = 15 # Water specular reflectance (dark)
    for y_pos in range(80, 420, 70):
        sar_arr[y_pos:y_pos+45, 40:100] = 235 # Double bounce reflection (bright)
        
    speckle = np.random.normal(0, 10, (512, 512)).astype(np.int16)
    sar_arr = np.clip(sar_arr.astype(np.int16) + speckle, 0, 255).astype(np.uint8)
    sar_img = Image.fromarray(sar_arr, mode="L").convert("RGB")
    
    optical.save(os.path.join(ben_dir, "sentinel2_optical.png"))
    sar_img.save(os.path.join(ben_dir, "sentinel1_sar.png"))
    
    meta = {
        "dataset": "BigEarthNet",
        "title": "Sentinel-2 Optical + Sentinel-1 SAR Multi-Sensor Fusion",
        "samples": [{
            "id": 1,
            "optical_filename": "sentinel2_optical.png",
            "sar_filename": "sentinel1_sar.png",
            "preset_queries": [
                "Use both optical and SAR imagery to delineate the water boundary beneath the cloud cover.",
                "Compare the structural backscatter in SAR with the optical land-cover classification.",
                "Explain how multi-modal fusion improves feature confidence over optical-only analysis."
            ]
        }]
    }
    with open(os.path.join(ben_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("  [+] BigEarthNet: data/samples/bigearthnet/sentinel2_optical.png & sentinel1_sar.png")

# -----------------------------------------------------------------------------
# 5. INSAT-3DS Geostationary Meteorological Thermal IR Sample
# -----------------------------------------------------------------------------
def build_insat3ds_sample():
    insat_dir = os.path.join(SAMPLES_DIR, "insat3ds")
    
    # 512x512 Grayscale Thermal IR full-disc image with dark header banner
    img = Image.new("RGB", (512, 512), (32, 32, 32))
    draw = ImageDraw.Draw(img)
    
    # Top banner with title text
    draw.rectangle([0, 0, 512, 45], fill=(10, 10, 10))
    draw.text((15, 12), "INSAT-3DS IMG, Thermal Infrared1 Count (10.83 um) L1C Mercator", fill=(220, 220, 220))
    
    # Convective cloud clusters (high count, bright cold cloud tops)
    draw.ellipse([80, 90, 240, 230], fill=(245, 245, 245))
    draw.ellipse([140, 150, 310, 310], fill=(235, 235, 235))
    draw.ellipse([270, 180, 440, 330], fill=(225, 225, 225))
    draw.ellipse([160, 360, 380, 460], fill=(240, 240, 240)) # ITCZ band
    
    img_path = os.path.join(insat_dir, "insat3ds_tir1_sample.png")
    img.save(img_path)
    
    meta = {
        "dataset": "INSAT-3DS",
        "title": "ISRO / IMD INSAT-3DS Thermal Infrared-1 (TIR1 @ 10.83 um)",
        "samples": [{
            "id": 1,
            "filename": "insat3ds_tir1_sample.png",
            "preset_queries": [
                "What this image shows and explain it.",
                "Analyze the deep convective cloud clusters and cloud-top brightness temperatures.",
                "Describe the regional synoptic atmospheric dynamics over the Indian subcontinent and Bay of Bengal."
            ]
        }]
    }
    with open(os.path.join(insat_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("  [+] INSAT-3DS:  data/samples/insat3ds/insat3ds_tir1_sample.png")

def main():
    parser = argparse.ArgumentParser(description="Prepare SatQuery AI benchmark sample datasets")
    parser.add_argument("--stream-hf", action="store_true", help="Also attempt live streaming from Hugging Face")
    args = parser.parse_args()
    
    print("=" * 65)
    print("SatQuery AI - Populating Local Benchmark Datasets")
    print("=" * 65)
    ensure_dirs()
    build_vrsbench_sample()
    build_rsvqa_sample()
    build_cdvqa_sample()
    build_bigearthnet_sample()
    build_insat3ds_sample()
    print("=" * 65)
    print(f"All benchmark datasets ready in: {SAMPLES_DIR}")

if __name__ == "__main__":
    main()
