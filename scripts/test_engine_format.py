"""
SatQuery AI — Model Output Format Verification Script
Tests Ollama's moondream model with various satellite prompts (VQA, Grounding, Location)
to inspect the raw response format (coordinates vs descriptive text).
"""

import sys
import json
import base64
import requests
from io import BytesIO
from PIL import Image, ImageDraw

def create_synthetic_satellite_image() -> bytes:
    """Creates a synthetic 512x512 satellite-like image with distinct features."""
    img = Image.new("RGB", (512, 512), color=(45, 110, 50))  # Green vegetation background
    draw = ImageDraw.Draw(img)
    
    # Draw a river / water body (blue)
    draw.polygon([(0, 200), (200, 220), (350, 280), (512, 310), (512, 380), (350, 340), (200, 290), (0, 260)], fill=(30, 80, 180))
    
    # Draw an urban / runway concrete area (gray)
    draw.rectangle([300, 50, 480, 180], fill=(160, 160, 160), outline=(200, 200, 200), width=2)
    
    # Draw airplane-like shapes on runway (white)
    draw.polygon([(340, 100), (360, 100), (350, 70)], fill=(255, 255, 255))
    draw.polygon([(420, 130), (440, 130), (430, 100)], fill=(255, 255, 255))
    
    # Draw agricultural fields (yellowish-brown)
    draw.rectangle([40, 40, 180, 160], fill=(180, 160, 60), outline=(140, 120, 40), width=2)
    
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()

def query_ollama(image_bytes: bytes, prompt: str, base_url: str = "http://localhost:11434", model: str = "moondream") -> dict:
    """Sends a query to Ollama /api/generate endpoint."""
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False
    }
    
    try:
        response = requests.post(f"{base_url}/api/generate", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Could not connect to Ollama at {base_url}. Is Ollama running?"}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 60)
    print("SatQuery AI — Moondream Output Format Tester")
    print("=" * 60)
    
    print("\n1. Generating synthetic satellite image (runway with planes, river, fields)...")
    image_bytes = create_synthetic_satellite_image()
    print("   Done (512x512 JPEG).")
    
    test_prompts = [
        ("VQA / Scene Description", "Describe the land cover and main features in this satellite image."),
        ("Grounding (Airplanes)", "Locate the airplanes in this image. Specify their positions or coordinates if possible."),
        ("Grounding (Water Body)", "Where is the river or water body located in this image?"),
        ("Structured Point/BBox Query", "Detect all airplanes. Return their location in [ymin, xmin, ymax, xmax] or (x,y) format.")
    ]
    
    for category, prompt in test_prompts:
        print("\n" + "-" * 50)
        print(f"Testing: {category}")
        print(f"Prompt:  \"{prompt}\"")
        print("-" * 50)
        
        result = query_ollama(image_bytes, prompt)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            print("\nNote: If Ollama is not running, start it in a separate terminal with:")
            print("  ollama run moondream")
            break
        else:
            raw_response = result.get("response", "")
            print(f"✅ Response:\n{raw_response}")
            print(f"\nDuration: {result.get('total_duration', 0) / 1e9:.2f}s")

if __name__ == "__main__":
    main()
