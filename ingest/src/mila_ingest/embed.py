"""Local embeddings via FastEmbed (no API key / quota)."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Sequence

from fastembed import TextEmbedding

from mila_ingest.schema import DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIM


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    name = os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    return TextEmbedding(model_name=name)


def embed_texts(
    texts: Sequence[str],
    *,
    model: str | None = None,
    batch_size: int = 64,
) -> list[list[float]]:
    """Embed passage texts (ingest path)."""
    if model and model != os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL):
        # Allow one-off model override without poisoning the cache.
        emb = TextEmbedding(model_name=model)
    else:
        emb = _model()
    vectors: list[list[float]] = []
    for vec in emb.embed(list(texts), batch_size=batch_size):
        values = list(map(float, vec))
        if len(values) != EMBEDDING_DIM:
            raise RuntimeError(
                f"Expected dim {EMBEDDING_DIM}, got {len(values)} "
                f"(set EMBEDDING_DIM/collection to match the model)"
            )
        vectors.append(values)
    return vectors
