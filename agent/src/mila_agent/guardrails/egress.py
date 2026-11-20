"""Egress checks on final model text (after_model)."""

from __future__ import annotations

import re
from typing import Any, Mapping

from langchain_core.messages import AIMessage, RemoveMessage

# Phrases that suggest the model obeyed an injection / elevated itself.
_EGRESS_BAD: list[re.Pattern[str]] = [
    re.compile(r"(?i)\b(i\s+am\s+now\s+(in\s+)?administrator\s+mode)\b"),
    re.compile(r"(?i)\b(access\s+restrictions\s+are\s+suspended)\b"),
    re.compile(r"(?i)\b(security\s+clearance\s+equivalent\s+to\s+the\s+ciso)\b"),
    re.compile(r"(?i)\b(override_access\s*=\s*true)\b"),
    re.compile(r"(?i)\b(full\s+personnel\s+(directory|records))\b"),
]

_REFUSAL = (
    "I won't follow instructions embedded in retrieved documents or elevate access. "
    "Ask a specific question about content your role can see."
)


def _ai_text(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content or "")


def after_model_egress_injection(state: Mapping[str, Any]) -> dict[str, Any]:
    """Rewrite final answers that look like they complied with injection."""
    messages = list(state.get("messages") or [])
    if not messages:
        return {}
    last = messages[-1]
    if not isinstance(last, AIMessage):
        return {}
    if getattr(last, "tool_calls", None):
        return {}
    text = _ai_text(last)
    hits = [p.pattern for p in _EGRESS_BAD if p.search(text)]
    if not hits:
        return {}
    replacement = AIMessage(content=_REFUSAL)
    if getattr(last, "id", None):
        return {
            "messages": [RemoveMessage(id=last.id), replacement],
            "guardrail_egress": hits,
        }
    return {"messages": [replacement], "guardrail_egress": hits}
