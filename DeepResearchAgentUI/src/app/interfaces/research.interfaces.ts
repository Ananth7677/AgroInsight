export interface ResearchRequest {
  query: string;
  session_id?: string | null;
  location?: string | null;
  soil_type?: string | null;
  ip_address?: string | null;
}

export interface ResearchResponse {
  session_id: string;
  recommendation: string;
  suggested_follow_up_questions: string[];
  structured: Record<string, unknown>;
  retrieved_context_tokens: number;
  prompt_tokens_estimate: number;
  session_cost_estimate_usd: number;
  memory_events_saved: number;
  constraints_ok: boolean;
}
