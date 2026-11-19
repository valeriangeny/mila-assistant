"""Unit tests for role → PII span anonymization (no Qdrant / Presidio)."""

from __future__ import annotations

import pytest

from mila_agent.pii_policy import (
    anonymize_hit,
    anonymize_hits,
    anonymize_text,
    llm_safe_hit,
    pii_action_for,
)


def test_pii_action_matrix_smoke() -> None:
    assert pii_action_for("public", "name") == "mask"
    assert pii_action_for("public", "sensitive_narrative") == "refuse"
    assert pii_action_for("employee", "name") == "allow"
    assert pii_action_for("employee", "contact") == "mask"
    assert pii_action_for("hr", "financial") == "allow"
    assert pii_action_for("security", "financial") == "mask"
    assert pii_action_for("unknown", "contact") == "mask"  # → employee


def test_mask_name_for_public() -> None:
    text = "Priya contacted support."
    spans = [{"start": 0, "end": 5, "category": "name"}]
    safe, refused, transformations = anonymize_text(text, spans, role="public")
    assert not refused
    assert safe.startswith("<NAME>")
    assert "Priya" not in safe
    assert transformations[0]["original"] == "Priya"
    assert transformations[0]["replacement"] == "<NAME>"


def test_allow_name_for_employee() -> None:
    text = "Priya contacted support."
    spans = [{"start": 0, "end": 5, "category": "name"}]
    safe, refused, transformations = anonymize_text(text, spans, role="employee")
    assert not refused
    assert safe == text
    assert transformations == []


def test_redact_identifier() -> None:
    text = "SSN 123-45-6789 on file."
    spans = [{"start": 4, "end": 15, "category": "identifier"}]
    safe, refused, transformations = anonymize_text(text, spans, role="employee")
    assert not refused
    assert "123-45-6789" not in safe
    assert "SSN" in safe
    assert transformations[0]["action"] == "redact"
    assert transformations[0]["original"] == "123-45-6789"


def test_refuse_sensitive_narrative_for_public() -> None:
    text = "Performance notes about Dana."
    spans = [{"start": 0, "end": len(text), "category": "sensitive_narrative"}]
    safe, refused, transformations = anonymize_text(text, spans, role="public")
    assert refused
    assert safe == ""
    assert transformations == []


def test_anonymize_hit_drops_refused() -> None:
    hit = {
        "doc_id": "DOC-1",
        "text": "secret review",
        "pii_spans": [
            {"start": 0, "end": 13, "category": "sensitive_narrative"},
        ],
    }
    assert anonymize_hit(hit, role="public") is None
    kept = anonymize_hit(hit, role="hr")
    assert kept is not None
    assert kept["text"] == "secret review"
    assert kept["pii_applied"] is True
    assert "pii_spans" not in kept


def test_llm_safe_hit_strips_audit() -> None:
    hit = anonymize_hit(
        {
            "doc_id": "DOC-1",
            "text": "a@b.com",
            "pii_spans": [{"start": 0, "end": 7, "category": "contact"}],
        },
        role="employee",
    )
    assert hit is not None
    assert hit["_pii_transformations"]
    safe = llm_safe_hit(hit)
    assert "_pii_transformations" not in safe
    assert "a@b.com" not in safe["text"]


def test_anonymize_hits_filters() -> None:
    hits = [
        {
            "doc_id": "a",
            "text": "Priya email x@y.com",
            "pii_spans": [
                {"start": 0, "end": 5, "category": "name"},
                {"start": 12, "end": 19, "category": "contact"},
            ],
        },
        {
            "doc_id": "b",
            "text": "narrative",
            "pii_spans": [
                {"start": 0, "end": 9, "category": "sensitive_narrative"},
            ],
        },
    ]
    out = anonymize_hits(hits, role="public")
    assert len(out) == 1
    assert out[0]["doc_id"] == "a"
    assert "Priya" not in out[0]["text"]
    assert "x@y.com" not in out[0]["text"]


@pytest.mark.parametrize(
    "role",
    ["public", "employee", "engineering", "hr", "security"],
)
def test_missing_spans_passthrough(role: str) -> None:
    text = "No labels here."
    safe, refused, transformations = anonymize_text(text, [], role=role)
    assert not refused
    assert safe == text
    assert transformations == []
