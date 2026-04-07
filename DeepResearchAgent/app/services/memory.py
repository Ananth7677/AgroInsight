from __future__ import annotations

import json
from typing import Dict, List

from app.db import run_many, run_query
from app.services.embedding import hash_embedding, to_pgvector_literal


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def retrieve_memories(query: str, max_tokens: int, top_k: int = 8) -> tuple[list[dict], str, int]:
    emb = to_pgvector_literal(hash_embedding(query))
    rows = run_query(
        """
        SELECT id, event_type, content, metadata, created_at,
               (embedding <=> %s::vector) AS distance
        FROM memory_events
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """,
        (emb, emb, top_k),
    )

    selected: List[dict] = []
    context_lines: List[str] = []
    used = 0

    for row in rows:
        snippet = f"[{row['event_type']}] {row['content']}"
        t = estimate_tokens(snippet)
        if used + t > max_tokens:
            continue
        used += t
        selected.append(dict(row))
        context_lines.append(snippet)

    return selected, "\n".join(context_lines), used


def save_memory_events(events: List[Dict]) -> int:
    payload = []
    for e in events:
        content = e.get("content", "")
        payload.append(
            (
                e.get("event_type", "session"),
                content,
                json.dumps(e.get("metadata", {})),
                to_pgvector_literal(hash_embedding(content)),
            )
        )

    if not payload:
        return 0

    run_many(
        """
        INSERT INTO memory_events(event_type, content, metadata, embedding)
        VALUES (%s, %s, %s::jsonb, %s::vector)
        """,
        payload,
    )
    return len(payload)
