export interface ExecutionTrace {
  task: string;
  tools_used: string[];
  parameters: Record<string, any>;
  input_summary: Record<string, any>;
  confidence: number;
  warnings: string[];
  rs_adaptation: string;
  elapsed_seconds: number;
  timestamp: string;
}

export interface EvidencePayload {
  slot1_original: string | null;
  slot2_attention_or_diff: string | null;
  slot3_reticle_or_sar: string | null;
  slot4_after: string | null;
}

export interface AnalysisResponse {
  answer: string;
  evidence: EvidencePayload;
  trace: ExecutionTrace | null;
  trace_markdown?: string;
  error?: string;
}

export interface BenchmarkMission {
  id: string;
  title: string;
  category: string;
  mission_tag: string;
  image_a: string;
  modality_a: string;
  image_b: string | null;
  modality_b: string;
  query: string;
  image_a_preview?: string | null;
  image_b_preview?: string | null;
}

export interface SystemStatus {
  status: string;
  downlink_freq: string;
  orbit: string;
  model_id: string;
  device: string;
  adaptation: string;
  gpu_name: string;
  timestamp: string;
}
