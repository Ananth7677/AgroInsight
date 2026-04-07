from __future__ import annotations

from typing import List


def decompose_query(query: str) -> List[str]:
    # simple deterministic decomposition for constrained-token workflows
    return [
        f"What location and season context is needed for: {query}?",
        f"What soil compatibility constraints apply to: {query}?",
        f"What historical market trend constraints apply to: {query}?",
        "What is the final crop recommendation balancing agronomy + price trend?",
    ]
