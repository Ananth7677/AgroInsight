from __future__ import annotations

import json
from pathlib import Path

from app.dbo.connection import get_conn


def seed_reference_data() -> None:
    base = Path(__file__).resolve().parents[2]
    soil_json = base / "data" / "soil_defaults.json"
    prices_csv = base / "data" / "crop_prices.csv"

    if soil_json.exists():
        items = json.loads(soil_json.read_text(encoding="utf-8"))
        with get_conn() as conn:
            with conn.cursor() as cur:
                for region, soil in items.items():
                    cur.execute(
                        """
                        INSERT INTO soil_defaults(region, majority_soil)
                        VALUES (%s, %s)
                        ON CONFLICT(region) DO UPDATE SET majority_soil = EXCLUDED.majority_soil;
                        """,
                        (region.lower(), soil.lower()),
                    )
            conn.commit()

    if prices_csv.exists():
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM market_prices;")
                existing = cur.fetchone()[0]
                if existing == 0:
                    rows = []
                    for line in prices_csv.read_text(encoding="utf-8").splitlines()[1:]:
                        region, crop, month, avg_price = [x.strip() for x in line.split(",")]
                        rows.append((region.lower(), crop.lower(), month, float(avg_price)))
                    cur.executemany(
                        "INSERT INTO market_prices(region, crop, month, avg_price) VALUES (%s, %s, %s, %s)",
                        rows,
                    )
            conn.commit()
