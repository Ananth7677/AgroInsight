from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Request

from app.config import settings
from app.core.cache import TTLCache
from app.core.workflow import get_workflow
from app.models import ResearchRequest, ResearchResponse
from app.services.conversation import (
    build_conversation_context,
    ensure_session,
    list_sessions,
    get_recent_turns,
    get_last_assistant_metadata,
    save_turn,
)
from app.services.query_parser import extract_location_from_query
from app.services.query_parser import (
    extract_explicit_crops,
    extract_explicit_crop,
    extract_soil_from_query,
    has_deictic_crop_reference,
    is_compare_query,
    is_harmful_query,
    is_smalltalk_or_offtopic_query,
    is_weather_query,
    normalize_location_text,
    rewrite_query_with_focus_crop,
)

router = APIRouter(tags=["research"])
response_cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)


@router.get("/sessions/{session_id}/history")
def get_session_history(session_id: str, limit: int = 20) -> dict:
    safe_limit = max(1, min(limit, 100))
    turns = get_recent_turns(session_id=session_id, limit=safe_limit)
    return {
        "session_id": session_id,
        "count": len(turns),
        "turns": turns,
    }


@router.get("/sessions")
def get_sessions(limit: int = 50) -> dict:
    safe_limit = max(1, min(limit, 200))
    sessions = list_sessions(limit=safe_limit)
    return {
        "count": len(sessions),
        "sessions": sessions,
    }


def _cache_key(
    session_id: str,
    query: str,
    effective_location: str | None,
    focus_crop: str | None,
    soil_type: str | None,
    ip_address: str | None,
) -> str:
    payload = {
        "session_id": session_id,
        "query": query.strip().lower(),
        "location": (effective_location or "").strip().lower(),
        "focus_crop": (focus_crop or "").strip().lower(),
        "soil_type": (soil_type or "").strip().lower(),
        "ip_address": (ip_address or "").strip().lower(),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("/research", response_model=ResearchResponse)
def run_research(req: ResearchRequest, request: Request) -> ResearchResponse:
    session_id = ensure_session(req.session_id)

    forwarded_for = request.headers.get("x-forwarded-for", "")
    forwarded_ip = forwarded_for.split(",")[0].strip() if forwarded_for else None
    client_ip = forwarded_ip or (request.client.host if request.client else None)

    last_assistant_meta = get_last_assistant_metadata(session_id)

    normalized_query, inferred_location = extract_location_from_query(req.query)
    normalized_query, inferred_soil = extract_soil_from_query(normalized_query)
    harmful_mode = is_harmful_query(normalized_query)
    smalltalk_mode = is_smalltalk_or_offtopic_query(normalized_query)
    weather_mode = is_weather_query(normalized_query)
    if harmful_mode:
        query_mode = "harmful"
    elif smalltalk_mode:
        query_mode = "smalltalk"
    elif weather_mode:
        query_mode = "weather"
    else:
        query_mode = "crop"
    compare_crops = extract_explicit_crops(normalized_query)
    compare_intent = is_compare_query(normalized_query)
    if compare_intent and len(compare_crops) < 2:
        previous_candidates = (last_assistant_meta.get("top_candidates") or [])[:2]
        if len(previous_candidates) >= 2:
            compare_crops = [str(c).lower() for c in previous_candidates]
    compare_mode = compare_intent and len(compare_crops) >= 2

    explicit_crop = extract_explicit_crop(normalized_query)
    previous_focus_crop = (
        last_assistant_meta.get("focus_crop")
        or (last_assistant_meta.get("top_candidates") or [None])[0]
    )
    focus_crop = None
    if not compare_mode and not weather_mode:
        focus_crop = explicit_crop or (
            previous_focus_crop if has_deictic_crop_reference(normalized_query) else None
        )
    normalized_query = rewrite_query_with_focus_crop(normalized_query, focus_crop)

    explicit_location = normalize_location_text(req.location)
    effective_location = explicit_location or inferred_location or last_assistant_meta.get("location")
    effective_soil = req.soil_type or inferred_soil or last_assistant_meta.get("soil_type")
    effective_ip = req.ip_address or client_ip
    conversation_context = build_conversation_context(session_id, limit=8)

    key = _cache_key(
        session_id=session_id,
        query=normalized_query,
        effective_location=effective_location,
        focus_crop=focus_crop,
        soil_type=effective_soil,
        ip_address=effective_ip,
    )

    if settings.cache_enabled:
        cached = response_cache.get(key)
        if cached:
            return ResearchResponse(**cached)

    workflow = get_workflow()
    state = workflow.invoke(
        {
            "session_id": session_id,
            "query": normalized_query,
            "query_mode": query_mode,
            "location": effective_location,
            "focus_crop": focus_crop,
            "compare_crops": compare_crops,
            "soil_type": effective_soil,
            "ip_address": effective_ip,
            "conversation_context": conversation_context,
        }
    )

    structured = {
        "location": state.get("location"),
        "season_info": state.get("season_info"),
        "soil_info": state.get("soil_info"),
        "market_info": state.get("market_info"),
        "sub_questions": state.get("sub_questions"),
        "focus_crop": state.get("focus_crop"),
        "compare_crops": state.get("compare_crops", []),
        "top_candidates": state.get("top_candidates", []),
        "retrieved_memories_count": len(state.get("retrieved_memories", [])),
    }

    response = ResearchResponse(
        session_id=session_id,
        recommendation=state.get("recommendation", "No recommendation available."),
        suggested_follow_up_questions=state.get("suggested_follow_up_questions", []),
        structured=structured,
        retrieved_context_tokens=state.get("retrieved_context_tokens", 0),
        prompt_tokens_estimate=state.get("prompt_tokens_estimate", 0),
        session_cost_estimate_usd=state.get("session_cost_estimate_usd", 0.0),
        memory_events_saved=state.get("memory_events_saved", 0),
        constraints_ok=state.get("constraints_ok", False),
    )

    save_turn(
        session_id=session_id,
        role="user",
        content=req.query,
        metadata={
            "normalized_query": normalized_query,
            "resolved_location": state.get("location"),
            "focus_crop": state.get("focus_crop"),
            "soil_type": state.get("soil_info", {}).get("soil_type"),
        },
    )
    save_turn(
        session_id=session_id,
        role="assistant",
        content=response.recommendation,
        metadata={
            "location": state.get("location"),
            "season": state.get("season_info", {}).get("season"),
            "focus_crop": state.get("focus_crop"),
            "compare_crops": state.get("compare_crops", []),
            "top_candidates": state.get("top_candidates", []),
            "soil_type": state.get("soil_info", {}).get("soil_type"),
            "market_region": state.get("market_info", {}).get("region"),
            "suggested_follow_up_questions": response.suggested_follow_up_questions,
        },
    )

    if settings.cache_enabled:
        response_cache.set(key, response.model_dump())

    return response
