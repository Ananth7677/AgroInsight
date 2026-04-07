from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings

logger = logging.getLogger(__name__)


def synthesize_with_gemini(prompt: str) -> tuple[str, float]:
    """Returns (text, cost_estimate_usd). Falls back to rule text if API key missing."""
    if not settings.gemini_api_key:
        return (
            "Gemini key not configured. Returned deterministic recommendation from rule-based fallback.",
            0.0,
        )

    from langchain_google_genai import ChatGoogleGenerativeAI

    messages = [
        SystemMessage(
            content="You are an agronomy + market research analyst. Be concise and practical."
        ),
        HumanMessage(content=prompt),
    ]

    try:
        model = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.1,
            max_output_tokens=256,
        )
        resp = model.invoke(messages)
        text = resp.content if isinstance(resp.content, str) else str(resp.content)

        # cheap estimate for demo reporting
        est_tokens = max(1, len(prompt + text) // 4)
        est_cost = round(est_tokens / 1_000_000 * 0.35, 6)
        return text, est_cost
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini call failed for model '%s': %s", settings.gemini_model, exc)
        return (
            f"Returned deterministic recommendation from rule-based fallback. (Gemini unavailable: {exc})",
            0.0,
        )
