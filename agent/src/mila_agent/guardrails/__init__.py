"""Composable guardrails (LangGraph pre/post_model hooks + retrieve wrap).

Build a catalog of rails, then enable a subset via ``MILA_GUARDRAILS``
(comma-separated names). Hooks mirror LangChain middleware points without
requiring the full ``langchain`` agents package.
"""

from __future__ import annotations

from mila_agent.guardrails.compose import (
    GUARDRAIL_CATALOG,
    apply_retrieve_sanitizers,
    default_enabled_names,
    enabled_guardrails,
    make_post_model_hook,
    make_pre_model_hook,
    sanitize_retrieved_text,
)

__all__ = [
    "GUARDRAIL_CATALOG",
    "apply_retrieve_sanitizers",
    "default_enabled_names",
    "enabled_guardrails",
    "make_post_model_hook",
    "make_pre_model_hook",
    "sanitize_retrieved_text",
]
