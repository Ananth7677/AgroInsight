export interface SessionTurn {
  role: 'user' | 'assistant' | string;
  content: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
}

export interface SessionHistoryResponse {
  session_id: string;
  count: number;
  turns: SessionTurn[];
}

export interface SessionSummary {
  id: string;
  created_at: string;
  updated_at: string;
  turn_count: number;
}

export interface SessionsResponse {
  count: number;
  sessions: SessionSummary[];
}
