from __future__ import annotations

import psycopg

from app.config import settings


def get_conn():
    return psycopg.connect(settings.database_url)
