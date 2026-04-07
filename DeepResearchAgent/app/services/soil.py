from __future__ import annotations

from app.db import run_query


def resolve_soil(location: str, requested_soil: str | None) -> dict:
    if requested_soil:
        return {
            "soil_type": requested_soil.lower(),
            "source": "user",
        }

    region_key = location.split(",")[-1].strip().lower()
    rows = run_query(
        "SELECT majority_soil FROM soil_defaults WHERE region = %s LIMIT 1",
        (region_key,),
    )

    if rows:
        return {"soil_type": rows[0]["majority_soil"], "source": "regional_default"}

    return {"soil_type": "loamy", "source": "fallback_default"}
