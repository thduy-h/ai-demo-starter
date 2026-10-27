from __future__ import annotations

import numpy as np

from ..core.errors import InvalidInputError


def normalize_embedding(vector: np.ndarray) -> np.ndarray:
    arr = np.asarray(vector, dtype=np.float32)
    if arr.ndim != 1 or not np.isfinite(arr).all():
        raise InvalidInputError("Embedding must be a finite 1-D vector")
    norm = float(np.linalg.norm(arr.astype(np.float64)))
    if norm == 0:
        raise InvalidInputError("Embedding has zero norm")
    return (arr.astype(np.float64) / norm).astype(np.float32)


def cosine_similarity(query: np.ndarray, gallery: np.ndarray) -> np.ndarray:
    q = np.asarray(query, dtype=np.float32)
    g = np.asarray(gallery, dtype=np.float32)
    if q.ndim != 1 or g.ndim != 2 or g.shape[1] != q.shape[0]:
        raise InvalidInputError("Embedding shape mismatch")
    if not np.isfinite(q).all() or not np.isfinite(g).all():
        raise InvalidInputError("Embeddings must be finite")
    q64, g64 = q.astype(np.float64), g.astype(np.float64)
    qn = np.linalg.norm(q64)
    gn = np.linalg.norm(g64, axis=1)
    if qn == 0 or np.any(gn == 0):
        raise InvalidInputError("Zero norm embedding")
    return np.clip((g64 @ q64) / (gn * qn), -1, 1).astype(np.float32)
