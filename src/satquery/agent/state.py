from typing import List, Dict, Any, Optional, TypedDict
from PIL import Image
from satquery.core.schemas import SatQueryResult, ExecutionStepLog

class AgentState(TypedDict):
    query: str
    images: List[Image.Image]
    input_scenario: str  # 'single_image' | 'bi_temporal_pair' | 'optical_sar_pair'
    selected_tool: str   # 'vqa' | 'grounding' | 'change_detection' | 'fusion'
    raw_tool_result: Dict[str, Any]
    final_result: Optional[SatQueryResult]
    execution_logs: List[ExecutionStepLog]
