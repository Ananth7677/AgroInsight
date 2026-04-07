from __future__ import annotations

from typing import Iterable, List, Tuple

from psycopg.rows import dict_row

from app.dbo.connection import get_conn


def run_query(sql: str, params: Tuple | None = None) -> List[dict]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())


def run_many(sql: str, params: Iterable[Tuple]) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, list(params))
        conn.commit()
