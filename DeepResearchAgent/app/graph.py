from __future__ import annotations

import json
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from app.config import settings
from app.models import ResearchState
from app.services.geo import infer_location
from app.services.llm import synthesize_with_gemini
from app.services.market import market_snapshot
from app.services.memory import estimate_tokens, retrieve_memories, save_memory_events
from app.services.planner import decompose_query
from app.services.recommender import rule_based_candidates
from app.services.season import detect_season
from app.services.soil import resolve_soil


def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("query_mode") == "harmful":
        return {
            "sub_questions": [
                "Is this a harmful request?",
                "Return refusal response only.",
            ]
        }
    if state.get("query_mode") == "smalltalk":
        return {
            "sub_questions": [
                "Is this query outside agriculture decision support?",
                "How should the assistant redirect to supported question types?",
            ]
        }
    if state.get("query_mode") == "weather":
        return {
            "sub_questions": [
                f"What is the near-term weather outlook for {state.get('location') or 'the location'}?",
                "How could this weather pattern affect field operations in the next 7-10 days?",
                "What practical precautions should be taken for sowing/irrigation decisions?",
            ]
        }
    return {"sub_questions": decompose_query(state["query"]) }


def build_crop_assessment(crop: str, location: str, season_info: Dict[str, Any], soil_info: Dict[str, Any], market_info: Dict[str, Any], query: str) -> str:
    trends = market_info.get("trends", {})
    crop_info = trends.get(crop, {})
    trend_text = crop_info.get("trend", "unknown")
    delta = crop_info.get("delta")
    season = season_info.get("season", "unknown")
    rainfall = season_info.get("rainfall_profile", "unknown")
    soil = soil_info.get("soil_type", "unknown")

    suitability_parts = []
    suitability_parts.append(f"**Crop:** {crop.title()}")
    suitability_parts.append(f"**Location:** {location}")
    suitability_parts.append(f"**Season:** {season} ({rainfall} rainfall)")
    suitability_parts.append(f"**Soil:** {soil}")

    if trend_text == "up":
        market_note = f"positive market trend (delta {delta:+.2f})" if isinstance(delta, (int, float)) else "positive market trend"
    elif trend_text == "down":
        market_note = f"weakening market trend (delta {delta:+.2f})" if isinstance(delta, (int, float)) else "weakening market trend"
    else:
        market_note = "insufficient market trend data"

    is_suitable = False
    reasons = []

    if crop in {"corn", "maize"} and season in {"spring", "zaid", "summer"}:
        is_suitable = True
        reasons.append("Season aligns with planting window")
    if crop == "wheat" and season in {"rabi", "winter", "spring"}:
        is_suitable = True
        reasons.append("Season is workable for a small-grain crop")
    if crop in {"soybean", "groundnut"} and soil in {"black", "alluvial", "loamy"}:
        is_suitable = True
        reasons.append("Soil is favorable for oilseeds/legumes")
    if crop in trends:
        reasons.append(f"Market shows {market_note}")

    verdict = "Yes" if is_suitable else "Maybe"
    rationale_lines = []
    for reason in reasons[:4]:
        rationale_lines.append(f"* {reason}")
    if not rationale_lines:
        rationale_lines.append("* Limited signal data available, so use local agronomy validation.")

    return (
        f"**Verdict:** {verdict}, it is a reasonable time to consider {crop}.\n\n"
        f"**Why:**\n"
        + "\n".join(rationale_lines)
        + f"\n\n**Market Note:** {market_note}."
    )


def context_node(state: Dict[str, Any]) -> Dict[str, Any]:
    location = infer_location(state.get("location"), state.get("ip_address"))
    season_info = detect_season(location)
    soil_info = resolve_soil(location, state.get("soil_type"))
    market_info = market_snapshot(location)

    memory_budget = int(settings.max_context_tokens * 0.6)
    retrieved_memories, retrieved_context, retrieved_context_tokens = retrieve_memories(
        state["query"],
        max_tokens=memory_budget,
    )

    return {
        "location": location,
        "season_info": season_info,
        "soil_info": soil_info,
        "market_info": market_info,
        "retrieved_memories": retrieved_memories,
        "retrieved_context": retrieved_context,
        "retrieved_context_tokens": retrieved_context_tokens,
    }


def reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    query_mode = state.get("query_mode", "crop")
    if query_mode == "harmful":
        recommendation = "Sorry, I can't assist with that."
        prompt_tokens = estimate_tokens(recommendation)
        return {
            "reasoning": json.dumps({"mode": "harmful"}),
            "recommendation": recommendation,
            "focus_crop": None,
            "compare_crops": [],
            "top_candidates": [],
            "suggested_follow_up_questions": [],
            "session_cost_estimate_usd": 0.0,
            "constraints_ok": True,
            "prompt_tokens_estimate": prompt_tokens,
        }

    if query_mode == "smalltalk":
        recommendation = (
            "I’m doing well, thanks. I’m specialized for agriculture decisions. "
            "Ask me about crop suitability, profitability comparison, soil-based recommendations, "
            "or short-term weather impact on planting."
        )
        follow_ups = [
            "Which crop is suitable now in Hassan with black soil?",
            "Compare profitability of rice vs soybean for next 3 months.",
            "How can next 10-day weather affect sowing decisions in my location?",
        ]
        prompt_tokens = estimate_tokens(recommendation)
        return {
            "reasoning": json.dumps({"mode": "smalltalk"}),
            "recommendation": recommendation,
            "focus_crop": None,
            "compare_crops": [],
            "top_candidates": [],
            "suggested_follow_up_questions": follow_ups,
            "session_cost_estimate_usd": 0.0,
            "constraints_ok": True,
            "prompt_tokens_estimate": prompt_tokens,
        }

    trends = state["market_info"].get("trends", {})
    candidates = rule_based_candidates(
        state["season_info"]["season"],
        state["soil_info"]["soil_type"],
        trends,
    )

    focus_crop = (state.get("focus_crop") or "").lower().strip() or None
    compare_crops = [c.lower().strip() for c in (state.get("compare_crops") or []) if c]
    if focus_crop:
        if focus_crop in candidates:
            candidates = [focus_crop] + [c for c in candidates if c != focus_crop]
        else:
            candidates = [focus_crop] + candidates

    q = state["query"].lower()
    precaution_mode = any(k in q for k in ["aware", "risk", "careful", "disease", "pest", "precaution"])
    compare_mode = len(compare_crops) >= 2 and any(k in q for k in ["compare", "vs", "versus", "profitability", "better than"])
    explicit_crop_mode = bool(focus_crop) and not compare_mode

    if query_mode == "weather":
        location = state["location"]
        season = state["season_info"].get("season", "unknown")
        rainfall = state["season_info"].get("rainfall_profile", "unknown")
        soil = state["soil_info"].get("soil_type", "unknown")
        recommendation = (
            f"Weather outlook for {location} (next ~10 days): no live forecast API is configured, "
            f"so this is season-based guidance. Current season is {season} with {rainfall} rainfall profile. "
            f"For {soil} soil, avoid heavy sowing before a confirmed rainfall window and keep irrigation flexible. "
            "If possible, validate with a local forecast source before field operations."
        )
        follow_ups = [
            "Should I delay sowing by a week based on this weather outlook?",
            "What irrigation plan should I follow for the next 10 days?",
            "Given this weather pattern, which crop is less risky now?",
        ]
        prompt_tokens = estimate_tokens(recommendation)
        return {
            "reasoning": json.dumps({"mode": "weather", "location": location, "season": season}),
            "recommendation": recommendation,
            "focus_crop": None,
            "compare_crops": [],
            "top_candidates": [],
            "suggested_follow_up_questions": follow_ups,
            "session_cost_estimate_usd": 0.0,
            "constraints_ok": state["retrieved_context_tokens"] <= settings.max_context_tokens,
            "prompt_tokens_estimate": prompt_tokens,
        }

    recent_turns = (state.get("conversation_context", "").splitlines())[-4:]
    short_memory = state.get("retrieved_context", "").splitlines()[:4]
    market_trends = state["market_info"].get("trends", {})
    top_trends = {
        crop: info
        for crop, info in list(market_trends.items())[:4]
    }

    base_reasoning = {
        "query": state["query"],
        "location": state["location"],
        "season": state["season_info"],
        "soil": state["soil_info"],
        "top_trends": top_trends,
        "recent_context": recent_turns,
        "memory_snippets": short_memory,
        "compare_crops": compare_crops,
        "focus_crop": focus_crop,
        "rule_candidates": candidates[:3],
    }

    if compare_mode:
        prompt = (
            "Compare ONLY the requested crops using the provided trend data and location context. "
            "Output concise bullets: expected 3-month profitability direction, key cost/risk notes, and final pick with why.\n"
            f"{json.dumps(base_reasoning, ensure_ascii=False)}"
        )
    elif explicit_crop_mode:
        prompt = (
            "Answer ONLY about the focus crop. Do NOT suggest other crops as the main answer. "
            "State whether now is a good time to plant it, with season/soil/market rationale.\n"
            f"{json.dumps(base_reasoning, ensure_ascii=False)}"
        )
    elif focus_crop and precaution_mode:
        prompt = (
            "Given the structured facts, answer ONLY for the focus crop. "
            "Provide practical precautions: soil prep, seed rate, sowing window, irrigation, pest/disease watch-outs, "
            "nutrient plan, and downside risks. Keep concise bullet points.\n"
            f"{json.dumps(base_reasoning, ensure_ascii=False)}"
        )
    else:
        prompt = (
            "Given the following structured facts, propose best crops and short rationale.\n"
            "Respect historical trend signal over spot price.\n"
            f"{json.dumps(base_reasoning, ensure_ascii=False)}"
        )
    if explicit_crop_mode and not precaution_mode:
        llm_text = build_crop_assessment(
            crop=focus_crop,
            location=state["location"],
            season_info=state["season_info"],
            soil_info=state["soil_info"],
            market_info=state["market_info"],
            query=state["query"],
        )
        est_cost = 0.0
    else:
        llm_text, est_cost = synthesize_with_gemini(prompt)

    prompt_tokens = estimate_tokens(prompt + llm_text)
    constraints_ok = (
        state["retrieved_context_tokens"] <= settings.max_context_tokens
        and est_cost <= settings.max_session_cost_usd
    )

    if compare_mode:
        recommendation = f"Comparison ({' vs '.join(compare_crops[:3])}): {llm_text}"
    elif explicit_crop_mode:
        recommendation = f"Focus crop: {focus_crop}. {llm_text}"
    elif focus_crop and precaution_mode:
        recommendation = f"Focus crop: {focus_crop}. Model note: {llm_text}"
    else:
        recommendation = (
            f"Top candidates: {', '.join(candidates[:3])}. "
            f"Model note: {llm_text}"
        )

    follow_ups = [
        f"Compare profitability of {candidates[0]} vs {candidates[1] if len(candidates) > 1 else candidates[0]} for next 3 months.",
        "What are the input costs, irrigation needs, and risk factors for the top 3 crops?",
        "If market trend reverses next month, what crop switch strategy should I use?",
    ]

    return {
        "reasoning": json.dumps(base_reasoning),
        "recommendation": recommendation,
        "focus_crop": focus_crop,
        "compare_crops": compare_crops,
        "top_candidates": candidates[:3],
        "suggested_follow_up_questions": follow_ups,
        "session_cost_estimate_usd": est_cost,
        "constraints_ok": constraints_ok,
        "prompt_tokens_estimate": prompt_tokens,
    }


def memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    events = [
        {
            "event_type": "query",
            "content": state["query"],
            "metadata": {"location": state.get("location")},
        },
        {
            "event_type": "result",
            "content": state.get("recommendation", ""),
            "metadata": {
                "constraints_ok": state.get("constraints_ok", False),
                "cost": state.get("session_cost_estimate_usd", 0.0),
            },
        },
    ]
    saved = save_memory_events(events)
    return {"memory_events_saved": saved}


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("plan", plan_node)
    graph.add_node("context", context_node)
    graph.add_node("synthesize", reasoning_node)
    graph.add_node("memory", memory_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "context")
    graph.add_edge("context", "synthesize")
    graph.add_edge("synthesize", "memory")
    graph.add_edge("memory", END)

    return graph.compile()
