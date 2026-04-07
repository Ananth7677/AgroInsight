from __future__ import annotations

import json
from uuid import uuid4

from app.db import run_many, run_query


def ensure_session(session_id: str | None) -> str:
    if session_id:
        rows = run_query("SELECT id FROM chat_sessions WHERE id = %s", (session_id,))
        if rows:
            return session_id
    new_id = str(uuid4())
    run_many(
        "INSERT INTO chat_sessions(id) VALUES (%s)",
        [(new_id,)],
    )
    return new_id


def save_turn(session_id: str, role: str, content: str, metadata: dict | None = None) -> None:
    run_many(
        """
        INSERT INTO chat_turns(session_id, role, content, metadata)
        VALUES (%s, %s, %s, %s::jsonb)
        """,
        [(session_id, role, content, json.dumps(metadata or {}))],
    )
    run_many(
        "UPDATE chat_sessions SET updated_at = now() WHERE id = %s",
        [(session_id,)],
    )


def get_recent_turns(session_id: str, limit: int = 8) -> list[dict]:
    rows = run_query(
        """
        SELECT role, content, metadata, created_at
        FROM chat_turns
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (session_id, limit),
    )
    return list(reversed(rows))


def build_conversation_context(session_id: str, limit: int = 8) -> str:
    turns = get_recent_turns(session_id, limit=limit)
    lines: list[str] = []
    for t in turns:
        role = t.get("role", "unknown")
        content = t.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def get_last_assistant_metadata(session_id: str) -> dict:
    rows = run_query(
        """
        SELECT metadata
        FROM chat_turns
        WHERE session_id = %s AND role = 'assistant'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (session_id,),
    )
    if not rows:
        return {}
    return rows[0].get("metadata") or {}


def list_sessions(limit: int = 100) -> list[dict]:
    rows = run_query(
        """
        SELECT s.id,
               s.created_at,
               s.updated_at,
               COUNT(t.id) AS turn_count
        FROM chat_sessions s
        LEFT JOIN chat_turns t ON t.session_id = s.id
        GROUP BY s.id, s.created_at, s.updated_at
        ORDER BY s.updated_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    return rows
