"""Query Qdrant for knowledge chunks (role-filtered vector search)."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from mila_agent.access_policy import normalize_role, qdrant_filter_for_role

DEFAULT_COLLECTION = "mila_docs"
EMBEDDING_DIM = 384
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def _qdrant_url() -> str:
    return (os.environ.get("QDRANT_URL") or "http://127.0.0.1:6333").rstrip("/")


def _collection() -> str:
    return (os.environ.get("QDRANT_COLLECTION") or DEFAULT_COLLECTION).strip()


@lru_cache(maxsize=1)
def _embedder() -> TextEmbedding:
    name = os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    return TextEmbedding(model_name=name)


def _embed_query(query: str) -> list[float]:
    emb = _embedder()
    # Prefer query_embed when the model supports asymmetric query/passage vectors.
    try:
        vectors = list(emb.query_embed(query))
    except Exception:  # noqa: BLE001
        vectors = list(emb.embed([query]))
    if not vectors:
        raise RuntimeError("Empty embedding response for query")
    values = list(map(float, vectors[0]))
    if len(values) != EMBEDDING_DIM:
        raise RuntimeError(f"Expected dim {EMBEDDING_DIM}, got {len(values)}")
    return values


def search_knowledge(
    query: str,
    *,
    role: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """Vector search with payload filter from ``access_policy`` for ``role``.

    ``role`` should be a verified caller role; unknown roles fall back to
    employee (least privilege). See ``mila_agent.access_policy``.
    """
    url = _qdrant_url()
    collection = _collection()
    verified_role = normalize_role(role)
    query_filter = qdrant_filter_for_role(verified_role)
    client = QdrantClient(url=url, check_compatibility=False)

    try:
        collections = {c.name for c in client.get_collections().collections}
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "qdrant_unreachable",
            "message": f"Cannot reach Qdrant at {url}: {exc}",
            "query": query,
            "role": verified_role,
            "hits": [],
        }

    if collection not in collections:
        return {
            "status": "not_indexed",
            "message": (
                f"Collection '{collection}' missing. Run: "
                "`cd ingest && uv run mila-ingest --recreate`"
            ),
            "query": query,
            "role": verified_role,
            "hits": [],
        }

    vector = _embed_query(query)
    try:
        response = client.query_points(
            collection_name=collection,
            query=vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        points = response.points
    except AttributeError:
        points = client.search(
            collection_name=collection,
            query_vector=vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

    hits: list[dict[str, Any]] = []
    for point in points:
        payload = dict(point.payload or {})
        hits.append(
            {
                "score": float(point.score) if point.score is not None else None,
                "doc_id": payload.get("doc_id"),
                "title": payload.get("title"),
                "sensitivity": payload.get("sensitivity"),
                "intended_audience": payload.get("intended_audience"),
                "department": payload.get("department"),
                "doc_type": payload.get("doc_type"),
                "chunk_index": payload.get("chunk_index"),
                "pii_categories": payload.get("pii_categories") or [],
                "text": payload.get("text") or "",
            }
        )

    return {
        "status": "ok" if hits else "empty",
        "message": None if hits else "No matching chunks for this query under current access.",
        "query": query,
        "role": verified_role,
        "collection": collection,
        "hits": hits,
    }
