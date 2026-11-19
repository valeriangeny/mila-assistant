"""Shared collection / payload schema (must match agent retrieve)."""

from __future__ import annotations

DEFAULT_COLLECTION = "mila_docs"
# BAAI/bge-small-en-v1.5 via FastEmbed
EMBEDDING_DIM = 384
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Payload keys stored on every Qdrant point (ACL + PII).
PAYLOAD_KEYS = (
    "doc_id",
    "title",
    "department",
    "doc_type",
    "sensitivity",
    "intended_audience",
    "tags",
    "author",
    "created_at",
    "chunk_index",
    "text",
    "pii_categories",
    "pii_spans",
)
