from __future__ import annotations

from app.dbo.connection import get_conn
from app.dbo.schema_core import create_core_schema
from app.dbo.schema_sessions import create_session_schema
from app.dbo.seed import seed_reference_data


def init_db() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            create_core_schema(cur)
            create_session_schema(cur)
        conn.commit()

    seed_reference_data()
