import pytest
from PIL import Image
from satquery.validator.validator import InputValidator

def test_input_validator_single_image():
    img = Image.new("RGB", (256, 256), color=(50, 100, 50))
    norm_images, scenario, meta = InputValidator.validate_inputs([img])
    assert len(norm_images) == 1
    assert scenario == "single_image"
    assert meta["image_count"] == 1

def test_input_validator_dual_pair_routing():
    img1 = Image.new("RGB", (256, 256), color=(50, 100, 50))
    img2 = Image.new("RGB", (300, 300), color=(80, 80, 80))
    
    # Bi-temporal hint
    norm_images, scenario, _ = InputValidator.validate_inputs([img1, img2], user_intent_hint="What changed between before and after?")
    assert len(norm_images) == 2
    assert scenario == "bi_temporal_pair"
    assert norm_images[0].size == norm_images[1].size  # Auto resized
    
    # SAR / Fusion hint
    _, scenario_sar, _ = InputValidator.validate_inputs([img1, img2], user_intent_hint="Combine Sentinel-1 SAR and Sentinel-2 optical")
    assert scenario_sar == "optical_sar_pair"
