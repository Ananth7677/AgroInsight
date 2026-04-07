from __future__ import annotations

import re
from typing import Optional, Tuple


LOCATION_ALIASES = {
    "hassan": "Hassan, India",
    "ames": "Ames, United States",
    "chicago": "Chicago, United States",
    "missouri": "Missouri, United States",
    "california": "California, United States",
    "texas": "Texas, United States",
    "illinois": "Illinois, United States",
    "kansas": "Kansas, United States",
    "nebraska": "Nebraska, United States",
    "mississippi": "Mississippi, United States",
    "bangalore": "Bengaluru, India",
    "bengaluru": "Bengaluru, India",
    "karnataka": "Karnataka, India",
    "iowa": "Iowa, United States",
    "usa": "United States",
    "us": "United States",
    "india": "India",
}

CROP_ALIASES = [
    "rice",
    "maize",
    "soybean",
    "soyabean",
    "groundnut",
    "wheat",
    "mustard",
    "chickpea",
    "barley",
    "cotton",
    "sorghum",
    "millet",
    "pulses",
    "corn",
]

SOIL_ALIASES = {
    "red soil": "red",
    "black soil": "black",
    "alluvial soil": "alluvial",
    "loamy soil": "loamy",
    "sandy soil": "sandy",
    "clay soil": "clay",
    "red": "red",
    "black": "black",
    "alluvial": "alluvial",
    "loamy": "loamy",
    "sandy": "sandy",
    "clay": "clay",
}


def extract_location_from_query(query: str) -> Tuple[str, Optional[str]]:
    """Return (cleaned_query, inferred_location) from casual query text."""
    lowered = query.lower().strip()
    inferred: Optional[str] = None

    # check longer aliases first
    for alias in sorted(LOCATION_ALIASES.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            inferred = LOCATION_ALIASES[alias]
            lowered = re.sub(rf"\b{re.escape(alias)}\b", " ", lowered)
            break

    # cleanup common noise after alias removal
    cleaned = re.sub(r"\s+", " ", lowered).strip(" ,.?")
    if not cleaned:
        cleaned = query.strip()

    return cleaned, inferred


def normalize_location_text(location: str | None) -> str | None:
    if not location:
        return None
    key = location.strip().lower()
    return LOCATION_ALIASES.get(key, location)


def extract_explicit_crop(query: str) -> Optional[str]:
    q = query.lower()
    for crop in CROP_ALIASES:
        if re.search(rf"\b{re.escape(crop)}\b", q):
            return "soybean" if crop == "soyabean" else crop
    return None


def extract_explicit_crops(query: str) -> list[str]:
    q = query.lower()
    found: list[str] = []
    for crop in CROP_ALIASES:
        if re.search(rf"\b{re.escape(crop)}\b", q) and crop not in found:
            found.append("soybean" if crop == "soyabean" else crop)
    return found


def is_compare_query(query: str) -> bool:
    q = query.lower()
    markers = ["compare", " vs ", "versus", "profitability", "better than"]
    return any(m in q for m in markers)


def is_weather_query(query: str) -> bool:
    q = query.lower()
    markers = [
        "weather",
        "temperature",
        "rainfall",
        "forecast",
        "next 10 days",
        "next 7 days",
        "humidity",
        "wind",
    ]
    return any(m in q for m in markers)


def is_smalltalk_or_offtopic_query(query: str) -> bool:
    q = query.lower().strip()

    agri_markers = [
        "crop",
        "soil",
        "season",
        "rain",
        "weather",
        "plant",
        "sow",
        "fertilizer",
        "irrigation",
        "profit",
        "price",
        "yield",
        "candidate",
        "maize",
        "corn",
        "soybean",
        "soyabean",
        "wheat",
        "rice",
        "millet",
        "pulses",
    ]
    has_agri_signal = any(m in q for m in agri_markers)

    follow_up_decision_markers = [
        "which",
        "best",
        "better",
        "recommend",
        "suggest",
        "top",
        "pick",
        "go with",
        "among",
        "between",
        "suitable",
    ]
    has_follow_up_decision_signal = any(m in q for m in follow_up_decision_markers)

    smalltalk_patterns = [
        r"\bhow are you\b",
        r"\bhello\b",
        r"\bhi\b",
        r"\bhey\b",
        r"\bwho are you\b",
        r"\bwhat are you\b",
        r"\bthank you\b",
        r"\bthanks\b",
    ]
    if any(re.search(p, q) for p in smalltalk_patterns):
        if has_agri_signal or has_follow_up_decision_signal:
            return False
        return True

    off_topic_patterns = [
        r"\btell me a joke\b",
        r"\bmovie recommendation\b",
        r"\bwrite code\b",
        r"\bsolve leetcode\b",
        r"\bsing a song\b",
        r"\bcelebrity\b",
    ]
    if any(re.search(p, q) for p in off_topic_patterns):
        return not has_agri_signal

    return False


def is_harmful_query(query: str) -> bool:
    q = query.lower()
    harmful_markers = [
        "kill",
        "bomb",
        "explode",
        "demolish",
        "destroy",
        "attack",
        "weapon",
        "drone strike",
        "how to do it",
    ]
    return any(m in q for m in harmful_markers)


def has_deictic_crop_reference(query: str) -> bool:
    q = query.lower()
    patterns = [
        r"\bthis crop\b",
        r"\bthat crop\b",
        r"\bthe crop\b",
        r"\bit\b",
    ]
    return any(re.search(p, q) for p in patterns)


def rewrite_query_with_focus_crop(query: str, focus_crop: str | None) -> str:
    if not focus_crop:
        return query

    q = query
    q = re.sub(
        rf"\b(?:this|that|the)\s+crop\s+{re.escape(focus_crop)}\b",
        focus_crop,
        q,
        flags=re.IGNORECASE,
    )
    q = re.sub(r"\bthis crop\b", focus_crop, q, flags=re.IGNORECASE)
    q = re.sub(r"\bthat crop\b", focus_crop, q, flags=re.IGNORECASE)
    q = re.sub(r"\bthe crop\b", focus_crop, q, flags=re.IGNORECASE)
    q = re.sub(r"\bit\b", focus_crop, q, flags=re.IGNORECASE)
    q = re.sub(rf"\b{re.escape(focus_crop)}(?:\s+{re.escape(focus_crop)})+\b", focus_crop, q, flags=re.IGNORECASE)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def extract_soil_from_query(query: str) -> tuple[str, Optional[str]]:
    lowered = query.lower().strip()
    inferred: Optional[str] = None

    for alias in sorted(SOIL_ALIASES.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            inferred = SOIL_ALIASES[alias]
            lowered = re.sub(rf"\b{re.escape(alias)}\b", " ", lowered)
            break

    cleaned = re.sub(r"\s+", " ", lowered).strip(" ,.?")
    if not cleaned:
        cleaned = query.strip()

    return cleaned, inferred
