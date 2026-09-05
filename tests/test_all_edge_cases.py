import os
import pytest
import numpy as np
from PIL import Image, ImageDraw

from satquery.validator.validator import InputValidator
from satquery.models.engine import RemoteSensingVLMEngine
from satquery.tools.vqa import VQATool
from satquery.tools.grounding import GroundingTool
from satquery.tools.change_detection import ChangeDetectionTool
from satquery.tools.fusion import OpticalSARFusionTool
from satquery.agent.graph import SatQueryController

# -----------------------------------------------------------------------------
# 1. Image Validator Edge Case Tests
# -----------------------------------------------------------------------------
class TestValidatorEdgeCases:
    def test_grayscale_l_mode(self):
        """Grayscale (SAR / Thermal IR) should be cleanly normalized to 3-channel RGB."""
        img = Image.new("L", (150, 150), color=128)
        norm = InputValidator.load_image(img)
        assert norm.mode == "RGB"
        assert norm.size == (150, 150)

    def test_rgba_alpha_blending(self):
        """RGBA GeoTIFF with alpha channel should blend cleanly onto white RGB."""
        img = Image.new("RGBA", (200, 200), color=(100, 150, 200, 128))
        norm = InputValidator.load_image(img)
        assert norm.mode == "RGB"
        assert norm.size == (200, 200)

    def test_16bit_integer_scaling(self):
        """16-bit integer satellite arrays should be normalized to uint8 RGB."""
        arr = np.linspace(0, 65535, 10000, dtype=np.uint16).reshape((100, 100))
        img = Image.fromarray(arr)
        norm = InputValidator.load_image(img)
        assert norm.mode == "RGB"
        assert norm.size == (100, 100)

    def test_extreme_aspect_ratio(self):
        """Swath or panoramic satellite strips (e.g. 1000x80) should load without error."""
        img = Image.new("RGB", (1000, 80), color=(30, 80, 40))
        norm_imgs, scenario, meta = InputValidator.validate_inputs([img])
        assert len(norm_imgs) == 1
        assert scenario == "single_image"
        assert meta["dimensions"] == [(1000, 80)]

    def test_pair_dimension_auto_resizing(self):
        """Images of mismatched sizes in a pair should auto-align to matching dimensions."""
        img1 = Image.new("RGB", (300, 300), color=(50, 100, 50))
        img2 = Image.new("RGB", (450, 400), color=(80, 80, 80))
        norm_imgs, scenario, _ = InputValidator.validate_inputs([img1, img2], user_intent_hint="Compare before and after")
        assert len(norm_imgs) == 2
        assert scenario == "bi_temporal_pair"
        assert norm_imgs[0].size == norm_imgs[1].size == (300, 300)

    def test_empty_image_error(self):
        """Empty byte payload should raise a ValueError gracefully."""
        with pytest.raises(ValueError):
            InputValidator.load_image(b"")

    def test_solid_black_and_solid_white_images(self):
        """Pure black and pure white extremes should not crash the normalizer."""
        black = Image.new("RGB", (100, 100), (0, 0, 0))
        white = Image.new("RGB", (100, 100), (255, 255, 255))
        norm_b = InputValidator.load_image(black)
        norm_w = InputValidator.load_image(white)
        assert norm_b.size == (100, 100)
        assert norm_w.size == (100, 100)

    def test_small_chip_and_large_chip_scaling(self):
        """Extreme resolutions (32x32 and 2000x2000) should be validated smoothly."""
        small = Image.new("RGB", (32, 32), (50, 100, 50))
        large = Image.new("RGB", (2000, 2000), (50, 100, 50))
        norm_s, _, _ = InputValidator.validate_inputs([small])
        norm_l, _, _ = InputValidator.validate_inputs([large])
        assert norm_s[0].size == (32, 32)
        assert norm_l[0].size == (2000, 2000)

# -----------------------------------------------------------------------------
# 2. Remote Sensing & Meteorological Engine Tests
# -----------------------------------------------------------------------------
class TestRemoteSensingEngine:
    @pytest.fixture
    def engine(self):
        return RemoteSensingVLMEngine.get_instance()

    def test_meteorological_insat3ds_detection(self, engine):
        """Simulate an INSAT-3DS thermal IR satellite image with dark banner and clouds."""
        img = Image.new("RGB", (500, 500), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.ellipse([100, 100, 250, 250], fill=(240, 240, 240))
        draw.ellipse([300, 200, 420, 320], fill=(220, 220, 220))
        
        response = engine.query(img, "What this image shows and explain it")
        assert "INSAT-3DS" in response or "Thermal Infrared" in response
        assert "Cloud-Top Brightness Temperature" in response
        assert "Convective" in response or "convective" in response

    def test_locate_airplanes(self, engine):
        """Airfield query should locate airplanes with normalized coordinates."""
        img = Image.new("RGB", (400, 400), color=(60, 60, 60))
        narrative, bboxes = engine.detect(img, "airplane")
        assert len(bboxes) >= 1
        assert "airplane" in bboxes[0]["label"]
        for b in bboxes:
            assert 0.0 <= b["ymin"] <= b["ymax"] <= 1.0
            assert 0.0 <= b["xmin"] <= b["xmax"] <= 1.0

    def test_locate_storage_tanks(self, engine):
        """Storage tank grounding should return circular tank coordinates."""
        img = Image.new("RGB", (400, 400), color=(80, 80, 80))
        narrative, bboxes = engine.detect(img, "fuel storage tank")
        assert len(bboxes) >= 1
        assert "storage_tank" in bboxes[0]["label"]

    def test_locate_ships(self, engine):
        """Ship grounding should return vessel coordinates."""
        img = Image.new("RGB", (400, 400), color=(20, 40, 90))
        narrative, bboxes = engine.detect(img, "ship")
        assert len(bboxes) >= 1
        assert "ship" in bboxes[0]["label"]

    def test_locate_buildings(self, engine):
        """Building grounding should return rooftop coordinates."""
        img = Image.new("RGB", (400, 400), color=(70, 70, 70))
        narrative, bboxes = engine.detect(img, "building")
        assert len(bboxes) >= 1
        assert "building" in bboxes[0]["label"]

    def test_locate_bridges(self, engine):
        """Bridge grounding should return bridge coordinates."""
        img = Image.new("RGB", (400, 400), color=(50, 80, 100))
        narrative, bboxes = engine.detect(img, "bridge")
        assert len(bboxes) >= 1
        assert "bridge" in bboxes[0]["label"]

    def test_locate_water_bodies(self, engine):
        """Water body grounding should return water coordinates."""
        img = Image.new("RGB", (400, 400), color=(30, 80, 150))
        narrative, bboxes = engine.detect(img, "river")
        assert len(bboxes) >= 1
        assert "water" in bboxes[0]["label"]

    def test_locate_forest_canopy(self, engine):
        """Forest grounding should return canopy coordinates."""
        img = Image.new("RGB", (400, 400), color=(30, 120, 40))
        narrative, bboxes = engine.detect(img, "forest")
        assert len(bboxes) >= 1
        assert "forest" in bboxes[0]["label"] or "veg" in bboxes[0]["label"]

    def test_locate_clouds_convective_cores(self, engine):
        """Convective cloud grounding should return storm centroid coordinates."""
        img = Image.new("RGB", (400, 400), color=(40, 40, 40))
        narrative, bboxes = engine.detect(img, "convective storm")
        assert len(bboxes) >= 1
        assert "convective" in bboxes[0]["label"]

    def test_locate_vehicles_cars(self, engine):
        """Vehicle grounding should return car coordinates."""
        img = Image.new("RGB", (400, 400), color=(80, 80, 80))
        narrative, bboxes = engine.detect(img, "cars and vehicles")
        assert len(bboxes) >= 1
        assert "vehicle" in bboxes[0]["label"]

    def test_optical_sar_fusion_physics(self, engine):
        """Optical-SAR fusion query should explain C-band radar and cloud penetration."""
        opt = Image.new("RGB", (256, 256), color=(40, 120, 40))
        sar = Image.new("L", (256, 256), color=100)
        resp = engine.multi_image_query([opt, sar.convert("RGB")], "Fuse optical and SAR imagery")
        assert "Sentinel-1" in resp or "SAR" in resp
        assert "Cloud" in resp or "cloud" in resp or "radar" in resp

    def test_counting_query_rsvqa(self, engine):
        """Counting questions should return quantitative inventories."""
        img = Image.new("RGB", (256, 256), color=(40, 120, 40))
        resp = engine.query(img, "How many buildings and river channels are visible?")
        assert "RSVQA" in resp or "Inventory" in resp or "Building" in resp
        assert "river" in resp.lower() or "building" in resp.lower()

# -----------------------------------------------------------------------------
# 3. Tool Pipeline & Multi-Modal Verification
# -----------------------------------------------------------------------------
class TestToolPipelines:
    def test_vqa_tool_comprehensive(self):
        tool = VQATool()
        img = Image.new("RGB", (300, 300), color=(45, 90, 45))
        res = tool.run([img], "Describe the vegetation and terrain in this satellite scene")
        assert res["task"] in ("vqa", "captioning")
        assert res["confidence"] >= 0.80
        assert "analyzed_image_size" in res["evidence"]
        assert "bboxes" in res["evidence"]

    def test_grounding_tool_locate_user_phrasings(self):
        """Test diverse user query phrasings for locating things."""
        tool = GroundingTool()
        img = Image.new("RGB", (300, 300), color=(50, 120, 50))
        
        phrasings = [
            "locate all airplanes on the apron",
            "where are the fuel storage tanks located?",
            "find the river channel",
            "highlight all buildings",
            "detect the bridge across the water",
            "locte the planes" # Typo tolerance
        ]
        for query in phrasings:
            res = tool.run([img], query)
            assert res["task"] == "grounding"
            assert len(res["evidence"]["bboxes"]) >= 1
            assert res["evidence"]["overlay_image_base64"].startswith("data:image/png;base64,")

    def test_change_detection_tool(self):
        tool = ChangeDetectionTool()
        t1 = Image.new("RGB", (200, 200), (30, 90, 30))
        t2 = t1.copy()
        draw = ImageDraw.Draw(t2)
        draw.rectangle([40, 40, 140, 140], fill=(220, 220, 220)) # New construction
        
        res = tool.run([t1, t2], "What construction changes occurred between T1 and T2?")
        assert res["task"] == "change_detection"
        assert res["evidence"]["change_percentage"] > 10.0
        assert res["evidence"]["num_change_zones"] >= 1
        assert res["evidence"]["overlay_image_base64"].startswith("data:image/png;base64,")
        assert res["evidence"]["side_by_side_base64"].startswith("data:image/jpeg;base64,")

    def test_change_detection_zero_difference(self):
        """Identical image pair should return 0.0% change."""
        tool = ChangeDetectionTool()
        t1 = Image.new("RGB", (150, 150), (60, 120, 60))
        t2 = t1.copy()
        res = tool.run([t1, t2], "Detect changes")
        assert res["evidence"]["change_percentage"] == 0.0
        assert res["evidence"]["num_change_zones"] == 0

    def test_optical_sar_fusion_tool(self):
        tool = OpticalSARFusionTool()
        opt = Image.new("RGB", (200, 200), (50, 100, 50))
        sar = Image.new("RGB", (200, 200), (120, 120, 120))
        res = tool.run([opt, sar], "Delineate the water boundary beneath cloud cover using SAR")
        assert res["task"] == "optical_sar_fusion"
        assert res["confidence"] >= 0.90
        assert res["evidence"]["overlay_image_base64"].startswith("data:image/png;base64,")

# -----------------------------------------------------------------------------
# 4. Agent Controller & State Machine Tests
# -----------------------------------------------------------------------------
class TestAgentController:
    def test_full_pipeline_vqa(self):
        controller = SatQueryController()
        img = Image.new("RGB", (256, 256), color=(40, 100, 40))
        res = controller.process_query(
            query="What this image shows and explain it",
            images=[img],
            input_scenario="single_image"
        )
        assert res.tool_used == "vqa"
        assert len(res.answer) > 50
        assert len(res.execution_log) >= 3

    def test_full_pipeline_grounding_user_queries(self):
        controller = SatQueryController()
        img = Image.new("RGB", (256, 256), color=(50, 50, 50))
        
        # Test "locate the things user asks"
        queries = [
            "Where is the airplane parked?",
            "Locate the fuel storage tanks",
            "Find all buildings",
            "locte the airplanes"
        ]
        for q in queries:
            res = controller.process_query(
                query=q,
                images=[img],
                input_scenario="single_image"
            )
            assert res.tool_used == "grounding"
            assert res.evidence.overlay_image_base64 is not None
            assert len(res.evidence.bboxes) >= 1

    def test_full_pipeline_change_detection(self):
        controller = SatQueryController()
        t1 = Image.new("RGB", (200, 200), (30, 80, 30))
        t2 = Image.new("RGB", (200, 200), (180, 180, 180))
        res = controller.process_query(
            query="What changes occurred between before and after?",
            images=[t1, t2],
            input_scenario="bi_temporal_pair"
        )
        assert res.tool_used == "change_detection"
        assert res.evidence.side_by_side_base64 is not None

    def test_full_pipeline_optical_sar_fusion(self):
        controller = SatQueryController()
        opt = Image.new("RGB", (200, 200), (40, 110, 40))
        sar = Image.new("RGB", (200, 200), (90, 90, 90))
        res = controller.process_query(
            query="Combine Sentinel-1 SAR radar and Sentinel-2 optical",
            images=[opt, sar],
            input_scenario="optical_sar_pair"
        )
        assert res.tool_used == "fusion"
        assert res.evidence.overlay_image_base64 is not None
