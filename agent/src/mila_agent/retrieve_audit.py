"""Side-channel for last retrieve result (eval only).

Tool JSON must stay LLM-safe (masked text, no original PII). Evaluators still
need originals + hit ACL metadata, so ``search_knowledge`` records an audit
blob here that ``run_eval.target`` attaches to experiment outputs.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_last_retrieve_audit: ContextVar[dict[str, Any] | None] = ContextVar(
    "mila_last_retrieve_audit",
    default=None,
)


def clear_retrieve_audit() -> None:
    _last_retrieve_audit.set(None)


def set_retrieve_audit(payload: dict[str, Any]) -> None:
    _last_retrieve_audit.set(payload)


def get_retrieve_audit() -> dict[str, Any] | None:
    return _last_retrieve_audit.get()
