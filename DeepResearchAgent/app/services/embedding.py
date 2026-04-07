from __future__ import annotations

import hashlib
from typing import List


def hash_embedding(text: str, dim: int = 64) -> List[float]:
    """Cheap deterministic embedding so the demo runs without external embedding APIs."""
    vec = [0.0] * dim
    tokens = text.lower().split()
    if not tokens:
        return vec

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i in range(dim):
            vec[i] += (digest[i % len(digest)] - 128) / 128.0

    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def to_pgvector_literal(vec: List[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
