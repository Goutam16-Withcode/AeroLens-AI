from PIL import Image
from satquery.agent.graph import SatQueryController

def test_intent_classification():
    controller = SatQueryController()
    
    # Grounding query
    res = controller._classify_intent("Where is the airport runway and airplanes?", "single_image", 1)
    assert res == "grounding"
    
    # Change query
    res_change = controller._classify_intent("What changed between these two dates?", "bi_temporal_pair", 2)
    assert res_change == "change_detection"
    
    # Fusion query
    res_fusion = controller._classify_intent("Combine SAR radar and optical imagery", "optical_sar_pair", 2)
    assert res_fusion == "fusion"
    
    # VQA query
    res_vqa = controller._classify_intent("What is the primary land cover shown?", "single_image", 1)
    assert res_vqa == "vqa"
