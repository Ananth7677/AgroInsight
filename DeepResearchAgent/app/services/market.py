from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Dict, List

from app.db import run_query


def market_snapshot(location: str) -> Dict:
    region_key = location.split(",")[-1].strip().lower()
    rows = run_query(
        """
        SELECT crop, month, avg_price
        FROM market_prices
        WHERE region = %s
        ORDER BY crop, month DESC
        """,
        (region_key,),
    )

    grouped: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        grouped[row["crop"]].append(float(row["avg_price"]))

    trends = {}
    for crop, prices in grouped.items():
        recent = prices[:3]
        prior = prices[3:6] if len(prices) >= 6 else prices[3:]
        recent_avg = mean(recent) if recent else 0.0
        prior_avg = mean(prior) if prior else recent_avg
        delta = recent_avg - prior_avg
        direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
        trends[crop] = {
            "recent_avg": round(recent_avg, 2),
            "prior_avg": round(prior_avg, 2),
            "delta": round(delta, 2),
            "trend": direction,
        }

    return {
        "region": region_key,
        "trends": trends,
    }
