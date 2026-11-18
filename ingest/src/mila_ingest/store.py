"""Qdrant collection create + upsert."""

from __future__ import annotations

import hashlib
import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from mila_ingest.schema import DEFAULT_COLLECTION, EMBEDDING_DIM


def get_qdrant_url() -> str:
    return (os.environ.get("QDRANT_URL") or "http://127.0.0.1:6333").rstrip("/")


def get_collection() -> str:
    return (os.environ.get("QDRANT_COLLECTION") or DEFAULT_COLLECTION).strip()


def connect() -> QdrantClient:
    return QdrantClient(url=get_qdrant_url(), check_compatibility=False)


def ensure_collection(client: QdrantClient, collection: str | None = None) -> str:
    name = collection or get_collection()
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=qm.VectorParams(size=EMBEDDING_DIM, distance=qm.Distance.COSINE),
        )
    # Indexes for Phase 3 RBAC filters (safe to recreate).
    for field in ("sensitivity", "intended_audience", "department", "doc_id"):
        try:
            client.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )
        except Exception:  # noqa: BLE001 — already exists / older server
            pass
    return name


def point_id(doc_id: str, chunk_index: int) -> str:
    """Stable UUID-ish id from doc + chunk (Qdrant accepts unsigned int or UUID)."""
    digest = hashlib.sha1(f"{doc_id}#{chunk_index}".encode()).hexdigest()
    # Format as UUID: 8-4-4-4-12
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def upsert_chunks(
    client: QdrantClient,
    chunks: list[dict[str, Any]],
    vectors: list[list[float]],
    *,
    collection: str | None = None,
    batch_size: int = 64,
) -> int:
    if len(chunks) != len(vectors):
        raise ValueError("chunks and vectors length mismatch")
    name = ensure_collection(client, collection)
    total = 0
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_vectors = vectors[i : i + batch_size]
        points = [
            qm.PointStruct(
                id=point_id(c["doc_id"], int(c["chunk_index"])),
                vector=vec,
                payload=c,
            )
            for c, vec in zip(batch_chunks, batch_vectors, strict=True)
        ]
        client.upsert(collection_name=name, points=points, wait=True)
        total += len(points)
    return total
