from PIL import Image, ImageDraw
from satquery.tools.change_detection import ChangeDetectionTool
from satquery.tools.grounding import GroundingTool

def test_change_detection_pixel_diff():
    tool = ChangeDetectionTool()
    t1 = Image.new("RGB", (200, 200), (40, 100, 40))
    t2 = t1.copy()
    draw = ImageDraw.Draw(t2)
    draw.rectangle([50, 50, 150, 150], fill=(200, 200, 200)) # Change in center
    
    overlay, mask, change_pct, num_zones = tool._compute_pixel_diff(t1, t2)
    assert change_pct > 15.0
    assert num_zones >= 1
    assert overlay.size == (200, 200)

def test_grounding_bbox_overlay():
    tool = GroundingTool()
    img = Image.new("RGB", (300, 300), (50, 120, 60))
    boxes = [{"ymin": 0.2, "xmin": 0.2, "ymax": 0.5, "xmax": 0.5, "label": "airplane"}]
    annotated = tool._draw_bboxes(img, boxes)
    assert annotated.size == (300, 300)
