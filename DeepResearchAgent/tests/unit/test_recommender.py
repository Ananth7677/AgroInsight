from app.services.recommender import rule_based_candidates


def test_rule_based_candidates_prioritize_upward_trend():
    trends = {
        "maize": {"trend": "up"},
        "soybean": {"trend": "up"},
        "rice": {"trend": "down"},
    }
    candidates = rule_based_candidates("monsoon/kharif", "black", trends)
    assert candidates[0] in {"maize", "soybean"}
    assert "rice" in candidates


def test_rule_based_candidates_returns_max_five():
    trends = {k: {"trend": "up"} for k in ["maize", "soybean", "rice", "cotton", "millet", "pulses"]}
    candidates = rule_based_candidates("summer", "loamy", trends)
    assert len(candidates) <= 5
