import time
import logging
from typing import Dict, Any, List
from PIL import Image

from satquery.agent.state import AgentState
from satquery.core.schemas import SatQueryResult, VisualEvidence, BoundingBox, ExecutionStepLog
from satquery.tools.vqa import VQATool
from satquery.tools.grounding import GroundingTool
from satquery.tools.change_detection import ChangeDetectionTool
from satquery.tools.fusion import OpticalSARFusionTool

logger = logging.getLogger("satquery.agent")

class SatQueryController:
    """
    Agentic LangGraph controller that routes user queries and imagery to
    specialized remote sensing tools and unifies multimodal outputs.
    """
    
    def __init__(self):
        self.vqa_tool = VQATool()
        self.grounding_tool = GroundingTool()
        self.change_tool = ChangeDetectionTool()
        self.fusion_tool = OpticalSARFusionTool()
        self._build_graph()
        
    def _build_graph(self):
        """Constructs the LangGraph state machine."""
        try:
            from langgraph.graph import StateGraph, END
            workflow = StateGraph(AgentState)
            
            workflow.add_node("router", self._router_node)
            workflow.add_node("execute_tool", self._tool_execution_node)
            workflow.add_node("synthesize", self._synthesize_node)
            
            workflow.set_entry_point("router")
            workflow.add_edge("router", "execute_tool")
            workflow.add_edge("execute_tool", "synthesize")
            workflow.add_edge("synthesize", END)
            
            self.app = workflow.compile()
            self._use_langgraph = True
        except Exception as e:
            logger.warning(f"LangGraph compile fallback to direct pipeline: {e}")
            self._use_langgraph = False

    def _classify_intent(self, query: str, scenario: str, num_images: int) -> str:
        """Determines the appropriate tool based on query semantics and input imagery."""
        q_low = query.lower()
        
        # Dual-image priority routing
        if num_images >= 2:
            if scenario == "optical_sar_pair" or any(k in q_low for k in ["sar", "radar", "fusion", "sentinel-1", "sentinel-2"]):
                return "fusion"
            if scenario == "bi_temporal_pair" or any(k in q_low for k in ["change", "compare", "difference", "before", "after", "time", "deforest"]):
                return "change_detection"
                
        # Grounding / Localization keywords (including common typos like 'locte')
        grounding_keywords = [
            "locate", "locte", "find", "where", "highlight", "detect", "bounding box", 
            "bbox", "coordinates", "position of", "point to", "point out", "show me where", 
            "mark", "pinpoint", "box all", "draw box"
        ]
        if any(k in q_low for k in grounding_keywords):
            return "grounding"
            
        # Default single-image VQA & captioning
        return "vqa"

    def _router_node(self, state: AgentState) -> Dict[str, Any]:
        t0 = time.time()
        tool_name = self._classify_intent(
            state["query"], 
            state.get("input_scenario", "single_image"),
            len(state.get("images", []))
        )
        duration = (time.time() - t0) * 1000.0
        
        log = ExecutionStepLog(
            step="intent_routing",
            duration_ms=round(duration, 2),
            status="success",
            details={"selected_tool": tool_name, "scenario": state.get("input_scenario")}
        )
        logs = list(state.get("execution_logs", []))
        logs.append(log)
        
        return {"selected_tool": tool_name, "execution_logs": logs}

    def _tool_execution_node(self, state: AgentState) -> Dict[str, Any]:
        t0 = time.time()
        tool_name = state["selected_tool"]
        images = state["images"]
        query = state["query"]
        
        if tool_name == "grounding":
            raw_res = self.grounding_tool.run(images, query)
        elif tool_name == "change_detection":
            raw_res = self.change_tool.run(images, query)
        elif tool_name == "fusion":
            raw_res = self.fusion_tool.run(images, query)
        else:
            raw_res = self.vqa_tool.run(images, query)
            
        duration = (time.time() - t0) * 1000.0
        log = ExecutionStepLog(
            step=f"tool_execution_{tool_name}",
            duration_ms=round(duration, 2),
            status="success",
            details={"tool": tool_name, "confidence": raw_res.get("confidence", 0.8)}
        )
        logs = list(state.get("execution_logs", []))
        logs.append(log)
        
        return {"raw_tool_result": raw_res, "execution_logs": logs}

    def _synthesize_node(self, state: AgentState) -> Dict[str, Any]:
        t0 = time.time()
        raw = state["raw_tool_result"]
        tool_name = state["selected_tool"]
        
        evidence_dict = raw.get("evidence", {})
        bboxes_raw = evidence_dict.get("bboxes", [])
        bboxes = [BoundingBox(**b) if isinstance(b, dict) else b for b in bboxes_raw]
        
        evidence = VisualEvidence(
            overlay_image_base64=evidence_dict.get("overlay_image_base64"),
            change_mask_base64=evidence_dict.get("change_mask_base64"),
            side_by_side_base64=evidence_dict.get("side_by_side_base64"),
            bboxes=bboxes,
            stats=evidence_dict
        )
        
        duration = (time.time() - t0) * 1000.0
        log = ExecutionStepLog(
            step="output_synthesis",
            duration_ms=round(duration, 2),
            status="success"
        )
        logs = list(state.get("execution_logs", []))
        logs.append(log)
        
        final_result = SatQueryResult(
            answer=raw.get("answer", "Analysis complete."),
            task=raw.get("task", tool_name),
            tool_used=tool_name,
            confidence=raw.get("confidence", 0.85),
            evidence=evidence,
            execution_log=logs
        )
        
        return {"final_result": final_result}

    def process_query(self, query: str, images: List[Image.Image], input_scenario: str = "single_image") -> SatQueryResult:
        """Main entry point to execute the SatQuery pipeline."""
        initial_state: AgentState = {
            "query": query,
            "images": images,
            "input_scenario": input_scenario,
            "selected_tool": "",
            "raw_tool_result": {},
            "final_result": None,
            "execution_logs": []
        }
        
        if self._use_langgraph:
            final_state = self.app.invoke(initial_state)
            return final_state["final_result"]
        else:
            s1 = self._router_node(initial_state)
            initial_state.update(s1)
            s2 = self._tool_execution_node(initial_state)
            initial_state.update(s2)
            s3 = self._synthesize_node(initial_state)
            return s3["final_result"]
