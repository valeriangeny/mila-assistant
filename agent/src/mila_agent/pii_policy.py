"""Role → PII category handling (mask / redact / refuse / allow).

Document RBAC (``access_policy``) decides which chunks are visible. This module
decides what to do with **spans inside** those chunks before text reaches the LLM.

Spans are produced at ingest (Presidio → assignment categories) and stored on
the Qdrant payload. Offsets are Unicode code-point indices (Python ``str``).

Do **not** load ``instructions/pii_labels.jsonl`` here — offline eval only.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping

from mila_agent.access_policy import normalize_role

PiiCategory = Literal[
    "name",
    "contact",
    "identifier",
    "financial",
    "sensitive_narrative",
]

PiiAction = Literal["allow", "mask", "redact", "refuse"]

PII_CATEGORIES: frozenset[str] = frozenset(
    {
        "name",
        "contact",
        "identifier",
        "financial",
        "sensitive_narrative",
    }
)

# (role → category → action). Unknown categories default to mask.
# Align with docs/pii.md; hr gets the broadest allow; public is strictest.
_ROLE_PII: Mapping[str, Mapping[str, PiiAction]] = {
    "public": {
        "name": "mask",
        "contact": "mask",
        "identifier": "redact",
        "financial": "redact",
        "sensitive_narrative": "refuse",
    },
    "employee": {
        "name": "allow",
        "contact": "mask",
        "identifier": "redact",
        "financial": "redact",
        "sensitive_narrative": "redact",
    },
    "engineering": {
        "name": "allow",
        "contact": "mask",
        "identifier": "redact",
        "financial": "redact",
        "sensitive_narrative": "redact",
    },
    "hr": {
        "name": "allow",
        "contact": "allow",
        "identifier": "allow",
        "financial": "allow",
        "sensitive_narrative": "allow",
    },
    "security": {
        "name": "allow",
        "contact": "allow",
        "identifier": "allow",
        "financial": "mask",
        "sensitive_narrative": "allow",
    },
}


def pii_action_for(role: str | None, category: str) -> PiiAction:
    """Return the policy action for a verified role and PII category."""
    key = normalize_role(role)
    table = _ROLE_PII.get(key) or _ROLE_PII["employee"]
    cat = (category or "").strip().lower()
    if cat in table:
        return table[cat]
    return "mask"


def _mask_token(category: str) -> str:
    cat = (category or "PII").strip().upper() or "PII"
    return f"<{cat}>"


def _normalize_span(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    try:
        start = int(raw["start"])
        end = int(raw["end"])
    except (KeyError, TypeError, ValueError):
        return None
    if start < 0 or end < start:
        return None
    category = str(raw.get("category") or raw.get("entity_type") or "pii").lower()
    return {"start": start, "end": end, "category": category}


def anonymize_text(
    text: str,
    spans: list[Any] | None,
    *,
    role: str | None,
) -> tuple[str, bool]:
    """Apply role policy to ``text`` using stored spans.

    Returns ``(safe_text, refused)``. When ``refused`` is True the caller should
    drop the hit (a span required ``refuse`` for this role).
    """
    body = text or ""
    normalized: list[dict[str, Any]] = []
    for raw in spans or []:
        span = _normalize_span(raw)
        if span is None:
            continue
        # Clamp to text bounds (stale offsets after edits).
        span["start"] = min(span["start"], len(body))
        span["end"] = min(span["end"], len(body))
        if span["end"] <= span["start"]:
            continue
        normalized.append(span)

    for span in normalized:
        if pii_action_for(role, span["category"]) == "refuse":
            return "", True

    # Apply from the end so earlier offsets stay valid.
    ordered = sorted(normalized, key=lambda s: (s["start"], s["end"]), reverse=True)
    out = body
    for span in ordered:
        action = pii_action_for(role, span["category"])
        if action == "allow":
            continue
        start, end = span["start"], span["end"]
        if action == "mask":
            replacement = _mask_token(span["category"])
        else:  # redact
            replacement = ""
        out = out[:start] + replacement + out[end:]

    # Collapse gaps left by redact; keep single newlines.
    while "  " in out:
        out = out.replace("  ", " ")
    out = out.strip()

    return out, False


def anonymize_hit(hit: Mapping[str, Any], *, role: str | None) -> dict[str, Any] | None:
    """Return a copy of ``hit`` with role-safe ``text``, or ``None`` if refused."""
    safe, refused = anonymize_text(
        str(hit.get("text") or ""),
        hit.get("pii_spans") if isinstance(hit.get("pii_spans"), list) else [],
        role=role,
    )
    if refused:
        return None
    out = dict(hit)
    out["text"] = safe
    out["pii_applied"] = True
    return out


def anonymize_hits(
    hits: list[Mapping[str, Any]],
    *,
    role: str | None,
) -> list[dict[str, Any]]:
    """Anonymize each hit; drop hits that policy refuses."""
    out: list[dict[str, Any]] = []
    for hit in hits:
        safe = anonymize_hit(hit, role=role)
        if safe is not None:
            out.append(safe)
    return out
