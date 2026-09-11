"""Generate sample images for Gradio UI examples and disaster examples."""

import os
import numpy as np
from PIL import Image, ImageDraw

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")
DISASTER_DIR = os.path.join(ROOT_DIR, "disaster_examples")

os.makedirs(EXAMPLES_DIR, exist_ok=True)
os.makedirs(DISASTER_DIR, exist_ok=True)

# 1. General Examples
def make_general_samples():
    # scene_535: residential buildings
    img = Image.new("RGB", (512, 512), (70, 120, 60))
    d = ImageDraw.Draw(img)
    # road
    d.rectangle([230, 0, 280, 512], fill=(100, 100, 105))
    # residential buildings
    for (x, y) in [(80, 80), (140, 80), (80, 200), (140, 200), (350, 120), (350, 260)]:
        d.rectangle([x, y, x + 40, y + 40], fill=(190, 80, 70), outline=(50, 50, 50))
    img.save(os.path.join(EXAMPLES_DIR, "scene_535.png"))

    # scene_545: forests vs roads
    img = Image.new("RGB", (512, 512), (30, 80, 35))
    d = ImageDraw.Draw(img)
    d.line([(0, 256), (512, 280)], fill=(120, 120, 120), width=12)
    img.save(os.path.join(EXAMPLES_DIR, "scene_545.png"))

    # scene_498: water areas vs farmlands
    img = Image.new("RGB", (512, 512), (140, 170, 90))
    d = ImageDraw.Draw(img)
    d.ellipse([100, 80, 420, 440], fill=(40, 90, 160))
    img.save(os.path.join(EXAMPLES_DIR, "scene_498.png"))

    # scene_479: small road
    img = Image.new("RGB", (512, 512), (180, 150, 110))
    d = ImageDraw.Draw(img)
    d.line([(50, 0), (450, 512)], fill=(90, 85, 80), width=6)
    img.save(os.path.join(EXAMPLES_DIR, "scene_479.png"))

# 2. Disaster Pairs
def make_disaster_samples():
    pairs = [
        ("tsunami_before.tiff", "tsunami_after.tiff", "coast"),
        ("landslide_before.tiff", "landslide_after.tiff", "slope"),
        ("earthquake_before.tiff", "earthquake_after.tiff", "urban"),
        ("famine_before.tiff", "famine_after.tiff", "vegetation"),
        ("arable_land_before.tiff", "arable_land_after.tiff", "farmland"),
        ("water_rise_before.tiff", "water_rise_after.tiff", "flood"),
    ]

    for before_name, after_name, ptype in pairs:
        b_img = Image.new("RGB", (384, 384), (50, 110, 60))
        a_img = Image.new("RGB", (384, 384), (50, 110, 60))
        db = ImageDraw.Draw(b_img)
        da = ImageDraw.Draw(a_img)

        if ptype == "coast":
            # Before: coastline with buildings
            db.rectangle([0, 0, 180, 384], fill=(30, 80, 160)) # ocean
            db.rectangle([200, 50, 240, 90], fill=(200, 180, 160))
            db.rectangle([260, 50, 300, 90], fill=(200, 180, 160))
            db.rectangle([200, 150, 240, 190], fill=(200, 180, 160))
            # After: flooded inland, buildings destroyed
            da.rectangle([0, 0, 280, 384], fill=(50, 70, 90)) # inundated water/mud
        elif ptype == "slope":
            # Before: green mountain slope
            db.rectangle([0, 0, 384, 384], fill=(40, 120, 50))
            # After: brown landslide scar
            da.rectangle([0, 0, 384, 384], fill=(40, 120, 50))
            da.polygon([(150, 0), (280, 0), (320, 384), (100, 384)], fill=(150, 100, 60))
        elif ptype == "urban":
            # Before: neat grid of buildings
            for y in range(40, 340, 60):
                for x in range(40, 340, 60):
                    db.rectangle([x, y, x + 40, y + 40], fill=(210, 200, 190))
                    # After: damaged/collapsed debris in center
                    if 100 <= x <= 220 and 100 <= y <= 220:
                        da.rectangle([x, y, x + 40, y + 40], fill=(120, 110, 100))
                    else:
                        da.rectangle([x, y, x + 40, y + 40], fill=(210, 200, 190))
        elif ptype == "vegetation":
            # Before: lush green
            db.rectangle([0, 0, 384, 384], fill=(45, 135, 55))
            # After: dried brown vegetation
            da.rectangle([0, 0, 384, 384], fill=(160, 140, 80))
        elif ptype == "farmland":
            # Before: green fields
            db.rectangle([0, 0, 384, 384], fill=(60, 150, 60))
            # After: concrete structures built over
            da.rectangle([0, 0, 384, 384], fill=(60, 150, 60))
            da.rectangle([100, 100, 280, 280], fill=(130, 130, 140))
        elif ptype == "flood":
            # Before: small river
            db.rectangle([0, 0, 384, 384], fill=(90, 140, 70))
            db.line([(0, 192), (384, 192)], fill=(30, 80, 160), width=24)
            # After: wide flooding
            da.rectangle([0, 0, 384, 384], fill=(90, 140, 70))
            da.rectangle([0, 80, 384, 304], fill=(40, 75, 130))

        b_img.save(os.path.join(DISASTER_DIR, before_name))
        a_img.save(os.path.join(DISASTER_DIR, after_name))

if __name__ == "__main__":
    make_general_samples()
    make_disaster_samples()
    print("Generated sample assets in examples/ and disaster_examples/")
