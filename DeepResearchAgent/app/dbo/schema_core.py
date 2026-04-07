from __future__ import annotations


def create_core_schema(cur) -> None:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_events (
            id BIGSERIAL PRIMARY KEY,
            event_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            embedding vector(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS market_prices (
            id BIGSERIAL PRIMARY KEY,
            region TEXT NOT NULL,
            crop TEXT NOT NULL,
            month DATE NOT NULL,
            avg_price NUMERIC NOT NULL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS soil_defaults (
            id BIGSERIAL PRIMARY KEY,
            region TEXT UNIQUE NOT NULL,
            majority_soil TEXT NOT NULL
        );
        """
    )

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_events_embedding ON memory_events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_market_prices_region_crop_month ON market_prices(region, crop, month);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_soil_defaults_region ON soil_defaults(region);"
    )
