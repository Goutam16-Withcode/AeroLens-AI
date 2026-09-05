from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    ymin: float = Field(..., description="Top boundary, normalized 0.0 to 1.0")
    xmin: float = Field(..., description="Left boundary, normalized 0.0 to 1.0")
    ymax: float = Field(..., description="Bottom boundary, normalized 0.0 to 1.0")
    xmax: float = Field(..., description="Right boundary, normalized 0.0 to 1.0")
    label: str = Field("target", description="Class label of the detected object")
    confidence: Optional[float] = Field(None, description="Detection confidence score")

class ExecutionStepLog(BaseModel):
    step: str
    duration_ms: float
    status: str
    details: Optional[Dict[str, Any]] = None

class VisualEvidence(BaseModel):
    overlay_image_base64: Optional[str] = None
    change_mask_base64: Optional[str] = None
    side_by_side_base64: Optional[str] = None
    bboxes: List[BoundingBox] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)

class SatQueryResult(BaseModel):
    answer: str
    task: str
    tool_used: str
    confidence: float
    evidence: VisualEvidence = Field(default_factory=VisualEvidence)
    execution_log: List[ExecutionStepLog] = Field(default_factory=list)
