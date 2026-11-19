"""Detect PII spans at ingest (Presidio → assignment categories).

Stores Unicode code-point offsets compatible with Python ``str`` slicing.
``instructions/pii_labels.jsonl`` is never read here.
"""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

PRESIDIO_TO_CATEGORY: dict[str, str] = {
    "PERSON": "name",
    "EMAIL_ADDRESS": "contact",
    "PHONE_NUMBER": "contact",
    "LOCATION": "contact",
    "IP_ADDRESS": "contact",
    "US_SSN": "identifier",
    "US_ITIN": "identifier",
    "US_PASSPORT": "identifier",
    "US_DRIVER_LICENSE": "identifier",
    "DATE_TIME": "identifier",
    "CREDIT_CARD": "financial",
    "IBAN_CODE": "financial",
    "US_BANK_NUMBER": "financial",
    "CRYPTO": "financial",
}

# Doc types whose bodies are typically sensitive narrative even without NER hits.
SENSITIVE_DOC_TYPES: frozenset[str] = frozenset(
    {
        "performance_review",
        "pip",
        "termination_letter",
        "employee_profile",
        "offer_letter",
        "compensation_memo",
    }
)

_ANALYZE_ENTITIES = list(PRESIDIO_TO_CATEGORY.keys())


def pii_detection_enabled() -> bool:
    """``MILA_SKIP_PII=1`` disables detection (faster local/dev)."""
    return (os.environ.get("MILA_SKIP_PII") or "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }


@lru_cache(maxsize=1)
def _analyzer():
    """Prefer ``en_core_web_sm`` (smaller than Presidio's default lg)."""
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
    )
    return AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["en"])


def _regex_spans(text: str) -> list[dict[str, Any]]:
    """Supplement Presidio for structured PII."""
    patterns: list[tuple[str, str]] = [
        ("contact", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        (
            "contact",
            r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b",
        ),
        ("identifier", r"\b\d{3}-\d{2}-\d{4}\b"),
        (
            "financial",
            r"\b(?:\$\s?)?\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b",
        ),
    ]
    spans: list[dict[str, Any]] = []
    for category, pattern in patterns:
        for match in re.finditer(pattern, text):
            spans.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "category": category,
                    "score": 0.5,
                }
            )
    return spans


def _presidio_spans(text: str) -> list[dict[str, Any]]:
    try:
        engine = _analyzer()
        results = engine.analyze(
            text=text,
            language="en",
            entities=_ANALYZE_ENTITIES,
        )
    except Exception as exc:  # noqa: BLE001 — missing model / first-run issues
        logger.warning("Presidio analyze failed (%s); using regex-only PII", exc)
        return []

    spans: list[dict[str, Any]] = []
    for hit in results:
        category = PRESIDIO_TO_CATEGORY.get(hit.entity_type)
        if not category:
            continue
        spans.append(
            {
                "start": int(hit.start),
                "end": int(hit.end),
                "category": category,
                "score": float(hit.score),
            }
        )
    return spans


def _merge_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort and drop overlapping spans (keep longer / higher-score first)."""
    if not spans:
        return []
    ordered = sorted(
        spans,
        key=lambda s: (
            s["start"],
            -(s["end"] - s["start"]),
            -float(s.get("score") or 0),
        ),
    )
    merged: list[dict[str, Any]] = []
    for span in ordered:
        if merged and span["start"] < merged[-1]["end"]:
            continue
        merged.append(
            {
                "start": int(span["start"]),
                "end": int(span["end"]),
                "category": str(span["category"]),
            }
        )
    return merged


def detect_pii_spans(
    text: str,
    *,
    doc_type: str = "",
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return ``(pii_spans, pii_categories)`` for one chunk."""
    body = text or ""
    if not body or not pii_detection_enabled():
        return [], []

    dtype = (doc_type or "").strip().lower()
    if dtype in SENSITIVE_DOC_TYPES:
        # One full-chunk span: role policy allow → raw; redact/refuse → empty/drop.
        spans = [{"start": 0, "end": len(body), "category": "sensitive_narrative"}]
        return spans, ["sensitive_narrative"]

    spans = _merge_spans(_presidio_spans(body) + _regex_spans(body))
    categories = sorted({s["category"] for s in spans})
    return spans, categories


def annotate_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return chunks with ``pii_spans`` and ``pii_categories`` filled."""
    out: list[dict[str, Any]] = []
    for chunk in chunks:
        spans, categories = detect_pii_spans(
            str(chunk.get("text") or ""),
            doc_type=str(chunk.get("doc_type") or ""),
        )
        annotated = dict(chunk)
        annotated["pii_spans"] = spans
        annotated["pii_categories"] = categories
        out.append(annotated)
    return out
