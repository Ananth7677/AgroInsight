from app.services.planner import decompose_query


def test_decompose_query_has_four_steps():
    parts = decompose_query("which crop should i plant now")
    assert len(parts) == 4
    assert "location and season" in parts[0].lower()
    assert "soil" in parts[1].lower()
    assert "historical market" in parts[2].lower()
