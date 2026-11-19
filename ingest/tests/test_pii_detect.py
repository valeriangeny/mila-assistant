"""Ingest PII detection (regex + sensitive doc types; Presidio optional)."""

from __future__ import annotations

from mila_ingest.pii_detect import annotate_chunks, detect_pii_spans


def test_regex_email_and_ssn(monkeypatch) -> None:
    monkeypatch.delenv("MILA_SKIP_PII", raising=False)
    monkeypatch.setattr(
        "mila_ingest.pii_detect._presidio_spans",
        lambda _text: [],
    )
    text = "Reach alex@alim.example or SSN 123-45-6789."
    spans, cats = detect_pii_spans(text, doc_type="faq")
    assert "contact" in cats
    assert "identifier" in cats
    assert any(s["category"] == "contact" for s in spans)
    assert any(s["category"] == "identifier" for s in spans)
    # Offsets slice correctly.
    for span in spans:
        assert text[span["start"] : span["end"]]


def test_sensitive_doc_type_whole_chunk(monkeypatch) -> None:
    monkeypatch.delenv("MILA_SKIP_PII", raising=False)
    text = "Confidential performance notes."
    spans, cats = detect_pii_spans(text, doc_type="performance_review")
    assert cats == ["sensitive_narrative"]
    assert spans == [{"start": 0, "end": len(text), "category": "sensitive_narrative"}]


def test_skip_env(monkeypatch) -> None:
    monkeypatch.setenv("MILA_SKIP_PII", "1")
    spans, cats = detect_pii_spans("alex@alim.example", doc_type="faq")
    assert spans == []
    assert cats == []


def test_annotate_chunks(monkeypatch) -> None:
    monkeypatch.delenv("MILA_SKIP_PII", raising=False)
    monkeypatch.setattr(
        "mila_ingest.pii_detect._presidio_spans",
        lambda _text: [],
    )
    chunks = [
        {
            "doc_id": "DOC-1",
            "doc_type": "faq",
            "text": "Email me at alex@alim.example please.",
            "pii_categories": [],
            "pii_spans": [],
        }
    ]
    out = annotate_chunks(chunks)
    assert out[0]["pii_categories"]
    assert out[0]["pii_spans"]
