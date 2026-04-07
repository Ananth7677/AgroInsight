from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=5)
    location: Optional[str] = None
    soil_type: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None


class ResearchResponse(BaseModel):
    session_id: str
    recommendation: str
    suggested_follow_up_questions: List[str] = []
    structured: Dict[str, Any]
    retrieved_context_tokens: int
    prompt_tokens_estimate: int
    session_cost_estimate_usd: float
    memory_events_saved: int
    constraints_ok: bool


class ResearchState(TypedDict, total=False):
    query: str
    query_mode: str
    session_id: str
    location: Optional[str]
    soil_type: Optional[str]
    ip_address: Optional[str]
    focus_crop: Optional[str]
    compare_crops: List[str]
    top_candidates: List[str]
    conversation_context: str
    sub_questions: List[str]
    season_info: Dict[str, Any]
    market_info: Dict[str, Any]
    soil_info: Dict[str, Any]
    retrieved_memories: List[Dict[str, Any]]
    retrieved_context: str
    retrieved_context_tokens: int
    reasoning: str
    recommendation: str
    suggested_follow_up_questions: List[str]
    constraints_ok: bool
    session_cost_estimate_usd: float
    memory_events_saved: int
