from __future__ import annotations

from typing import Dict, List


def rule_based_candidates(season: str, soil: str, trends: Dict) -> List[str]:
    season = season.lower()
    soil = soil.lower()

    pool = []
    if "kharif" in season or "monsoon" in season:
        pool.extend(["rice", "maize", "soybean", "groundnut"])
    elif "rabi" in season or "winter" in season:
        pool.extend(["wheat", "mustard", "chickpea", "barley"])
    elif "summer" in season:
        pool.extend(["cotton", "sorghum", "millet", "maize"])
    else:
        pool.extend(["maize", "millet", "pulses"])

    if "black" in soil:
        pool.extend(["cotton", "soybean"])
    elif "red" in soil:
        pool.extend(["groundnut", "millet"])
    elif "alluvial" in soil or "loamy" in soil:
        pool.extend(["wheat", "rice", "sugarcane"])

    trend_up = [crop for crop, info in trends.items() if info.get("trend") == "up"]
    ranked = [c for c in pool if c in trend_up] + [c for c in pool if c not in trend_up]

    dedup = []
    for c in ranked:
        if c not in dedup:
            dedup.append(c)
    return dedup[:5]
