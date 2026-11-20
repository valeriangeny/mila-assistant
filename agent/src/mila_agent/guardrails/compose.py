"""Catalog + enablement + LangGraph hook factories."""

from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

from mila_agent.guardrails.egress import after_model_egress_injection
from mila_agent.guardrails.injection import sanitize_retrieved_text
from mila_agent.guardrails.types import Guardrail
from mila_agent.guardrails.user_safety import (
    after_model_user_safety,
    before_model_user_safety,
)

# Re-export for callers that only import compose / package root.
__all__ = [
    "GUARDRAIL_CATALOG",
    "default_enabled_names",
    "enabled_guardrails",
    "make_post_model_hook",
    "make_pre_model_hook",
    "sanitize_retrieved_text",
]


def _untrusted_framing_before(state: Mapping[str, Any]) -> dict[str, Any]:
    """Soft rail: no state change; presence documents the prompt-layer defense.

    Real framing lives in ``build_system_prompt``. This rail exists so the
    catalog can show A (prompt) as an explicit, toggleable entry.
    """
    del state
    return {}


GUARDRAIL_CATALOG: dict[str, Guardrail] = {
    "injection_sanitize": Guardrail(
        name="injection_sanitize",
        description="Strip INTERNAL_NOTE / SYSTEM fences from retrieve hits (wrap_tool).",
        sanitize_hit_text=sanitize_retrieved_text,
        tags=("retrieve", "t1"),
    ),
    "untrusted_framing": Guardrail(
        name="untrusted_framing",
        description="System-prompt untrusted-body rule (documented no-op hook).",
        before_model=_untrusted_framing_before,
        tags=("prompt", "t1"),
    ),
    "user_safety": Guardrail(
        name="user_safety",
        description="Refuse clear violence / hate / destructive-code user asks.",
        before_model=before_model_user_safety,
        after_model=after_model_user_safety,
        tags=("user", "t2"),
    ),
    "egress_injection": Guardrail(
        name="egress_injection",
        description="Rewrite finals that look like injection compliance.",
        after_model=after_model_egress_injection,
        tags=("egress", "t1"),
    ),
}


def default_enabled_names() -> list[str]:
    return [
        "injection_sanitize",
        "untrusted_framing",
        "user_safety",
        "egress_injection",
    ]


def enabled_guardrails(names: Sequence[str] | None = None) -> list[Guardrail]:
    """Resolve enabled rails from ``names`` or ``MILA_GUARDRAILS`` env.

    Empty env → defaults. ``MILA_GUARDRAILS=off`` / ``none`` → no rails.
    Unknown names are skipped.
    """
    if names is None:
        raw = (os.environ.get("MILA_GUARDRAILS") or "").strip()
        if not raw:
            names = default_enabled_names()
        elif raw.lower() in {"off", "none", "0", "false"}:
            names = []
        else:
            names = [p.strip() for p in raw.split(",") if p.strip()]
    out: list[Guardrail] = []
    for name in names:
        rail = GUARDRAIL_CATALOG.get(name)
        if rail is not None:
            out.append(rail)
    return out


def _merge_updates(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    if not patch:
        return base
    merged = dict(base)
    for key, value in patch.items():
        if key == "messages" and key in merged and isinstance(value, list):
            # Append message ops in order (RemoveMessage + AIMessage pairs).
            merged[key] = list(merged[key]) + list(value)
        else:
            merged[key] = value
    return merged


def make_pre_model_hook(rails: Sequence[Guardrail] | None = None):
    active = list(rails) if rails is not None else enabled_guardrails()

    def pre_model_hook(state: Mapping[str, Any]) -> dict[str, Any]:
        update: dict[str, Any] = {}
        # LangGraph requires messages or llm_input_messages — pass through
        # llm_input_messages from state if a rail set them; else echo messages.
        for rail in active:
            if rail.before_model is None:
                continue
            update = _merge_updates(update, rail.before_model(state))
        if "messages" not in update and "llm_input_messages" not in update:
            update["llm_input_messages"] = list(state.get("messages") or [])
        return update

    return pre_model_hook


def make_post_model_hook(rails: Sequence[Guardrail] | None = None):
    active = list(rails) if rails is not None else enabled_guardrails()

    def post_model_hook(state: Mapping[str, Any]) -> dict[str, Any]:
        update: dict[str, Any] = {}
        # Apply after_model in order; later rails see prior message rewrites
        # only via state — re-build a working view when messages were patched.
        working: dict[str, Any] = dict(state)
        for rail in active:
            if rail.after_model is None:
                continue
            patch = rail.after_model(working)
            if not patch:
                continue
            update = _merge_updates(update, patch)
            if "messages" in patch:
                # Approximate working messages for the next rail: apply removes.
                working = {**working, **patch}
        return update

    return post_model_hook


def apply_retrieve_sanitizers(
    text: str,
    rails: Sequence[Guardrail] | None = None,
) -> tuple[str, list[str]]:
    """Run all enabled ``sanitize_hit_text`` rails in catalog order."""
    active = list(rails) if rails is not None else enabled_guardrails()
    body = text or ""
    flags: list[str] = []
    for rail in active:
        if rail.sanitize_hit_text is None:
            continue
        body, more = rail.sanitize_hit_text(body)
        flags.extend(more)
    return body, flags
