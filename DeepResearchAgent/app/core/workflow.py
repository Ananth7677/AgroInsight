from __future__ import annotations

from functools import lru_cache

from app.graph import build_graph


@lru_cache(maxsize=1)
def get_workflow():
    return build_graph()
