"""Paragraph-aware character chunking for plain-text JSONL bodies.

Corpus is already clean text (no PDF/HTML). A splitter library (LangChain,
Unstructured, etc.) is unnecessary for ~1k-char docs — prefer newline/paragraph
boundaries, then fall back to a sliding window.
"""

from __future__ import annotations

from typing import Any


def chunk_text(text: str, *, size: int = 900, overlap: int = 120) -> list[str]:
    """Split on blank lines first; window only when a paragraph exceeds `size`."""
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]

    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned]

    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(para) > size:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_window(para, size=size, overlap=overlap))
            continue
        candidate = f"{buf}\n\n{para}".strip() if buf else para
        if len(candidate) <= size:
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
            buf = para
    if buf:
        chunks.append(buf)
    return chunks


def _window(text: str, *, size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def docs_to_chunks(docs: list[dict[str, Any]], *, size: int = 900, overlap: int = 120) -> list[dict[str, Any]]:
    """Expand documents into chunk records with ACL metadata copied through."""
    out: list[dict[str, Any]] = []
    for doc in docs:
        body = str(doc.get("body") or "")
        pieces = chunk_text(body, size=size, overlap=overlap)
        tags = doc.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]
        for idx, piece in enumerate(pieces):
            out.append(
                {
                    "doc_id": str(doc.get("id") or ""),
                    "title": str(doc.get("title") or ""),
                    "department": str(doc.get("department") or ""),
                    "doc_type": str(doc.get("doc_type") or ""),
                    "sensitivity": str(doc.get("sensitivity") or ""),
                    "intended_audience": str(doc.get("intended_audience") or ""),
                    "tags": [str(t) for t in tags],
                    "author": str(doc.get("author") or ""),
                    "created_at": str(doc.get("created_at") or ""),
                    "chunk_index": idx,
                    "text": piece,
                    # Phase 3: fill via detector; empty list keeps schema stable now.
                    "pii_categories": [],
                }
            )
    return out
