from app.services import market


def test_market_snapshot_trend_calculation(monkeypatch):
    fake_rows = [
        {"crop": "corn", "month": "2026-04-01", "avg_price": 25},
        {"crop": "corn", "month": "2026-03-01", "avg_price": 24},
        {"crop": "corn", "month": "2026-02-01", "avg_price": 23},
        {"crop": "corn", "month": "2026-01-01", "avg_price": 22},
        {"crop": "corn", "month": "2025-12-01", "avg_price": 21},
        {"crop": "corn", "month": "2025-11-01", "avg_price": 20},
    ]

    def fake_run_query(sql, params):
        assert params == ("united states",)
        return fake_rows

    monkeypatch.setattr(market, "run_query", fake_run_query)

    snapshot = market.market_snapshot("Nebraska, United States")
    corn = snapshot["trends"]["corn"]

    assert snapshot["region"] == "united states"
    assert corn["trend"] == "up"
    assert corn["delta"] > 0
