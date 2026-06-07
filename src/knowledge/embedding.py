from __future__ import annotations

import hashlib
import math
import re


DEFAULT_EMBEDDING_DIM = 128


def embed_text(text: str, dim: int = DEFAULT_EMBEDDING_DIM) -> list[float]:
    """Deterministic local embedding fallback.

    This is not a semantic model, but it gives stable vector retrieval without
    requiring a cloud embedding provider during local/private deployment.
    """
    vector = [0.0] * dim
    tokens = tokenize(text)
    for token in tokens:
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(item * item for item in vector)) or 1.0
    return [round(item / norm, 6) for item in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    return sum(left[index] * right[index] for index in range(size))


def tokenize(text: str) -> list[str]:
    normalized = text.lower()
    parts = re.findall(r"[\u4e00-\u9fff]{1,2}|[a-z0-9_+-]+", normalized)
    return [part.strip() for part in parts if part.strip()]
