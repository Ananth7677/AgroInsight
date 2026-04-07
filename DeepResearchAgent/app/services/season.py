from __future__ import annotations

from datetime import datetime


def detect_season(location: str, now: datetime | None = None) -> dict:
    now = now or datetime.utcnow()
    month = now.month
    lower = location.lower()

    # intentionally simple regional mapping for prototype
    if "india" in lower:
        if month in (6, 7, 8, 9):
            season = "monsoon/kharif"
            rainfall = "high"
        elif month in (10, 11, 12, 1):
            season = "rabi"
            rainfall = "low-moderate"
        else:
            season = "zaid"
            rainfall = "moderate"
    elif "usa" in lower or "united states" in lower:
        if month in (12, 1, 2):
            season = "winter"
            rainfall = "region-dependent"
        elif month in (3, 4, 5):
            season = "spring"
            rainfall = "moderate"
        elif month in (6, 7, 8):
            season = "summer"
            rainfall = "low-moderate"
        else:
            season = "fall"
            rainfall = "moderate"
    else:
        season = "location-specific"
        rainfall = "unknown"

    return {
        "location": location,
        "month": month,
        "season": season,
        "rainfall_profile": rainfall,
    }
