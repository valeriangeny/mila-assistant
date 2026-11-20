"""Direct user-message abuse heuristics (before_model)."""

from __future__ import annotations

import re
from typing import Any, Mapping

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage

_ABUSE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(?i)\b(how\s+(can|do|could|would)\s+i\s+(physically\s+)?(attack|hurt|kill)|"
            r"physically\s+attack|"
            r"build\s+(a\s+)?bomb|make\s+explosives)\b"
        ),
        "violence",
    ),
    (
        re.compile(
            r"(?i)\b(racist\s+rant|insult\s+\w+\s+by\s+(race|ethnicity)|"
            r"hate\s+speech\s+about)\b"
        ),
        "hate",
    ),
    (
        re.compile(
            r"(?i)\b(delete\s+all\s+files|rm\s+-rf\s+/|run\s+python\s+that\s+deletes)\b"
        ),
        "destructive_code",
    ),
]

_REFUSAL = (
    "I can't help with that request. I'm Mila, an internal knowledge assistant — "
    "ask about company documents you are allowed to access."
)


def _last_human_text(state: Mapping[str, Any]) -> str:
    messages = state.get("messages") or []
    for message in reversed(list(messages)):
        if isinstance(message, HumanMessage):
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
    return ""


def detect_user_abuse(text: str) -> str | None:
    for pattern, label in _ABUSE_PATTERNS:
        if pattern.search(text or ""):
            return label
    return None


def before_model_user_safety(state: Mapping[str, Any]) -> dict[str, Any]:
    """If the latest user turn is clearly abusive, short-circuit with a refusal.

    Returns ``llm_input_messages`` so history is unchanged but the model only
    sees a forced safe framing; also stashes ``guardrail_user_abuse`` on state.
    """
    text = _last_human_text(state)
    label = detect_user_abuse(text)
    if not label:
        return {}
    # Force a one-shot refusal path: replace LLM input with a tiny transcript.
    return {
        "llm_input_messages": [
            HumanMessage(
                content=(
                    f"(guardrail={label}) The user asked for disallowed help. "
                    "Reply with exactly this refusal and nothing else:\n"
                    f"{_REFUSAL}"
                )
            )
        ],
        "guardrail_user_abuse": label,
    }


def after_model_user_safety(state: Mapping[str, Any]) -> dict[str, Any]:
    """If abuse was flagged, ensure the visible assistant message is the refusal."""
    if not state.get("guardrail_user_abuse"):
        return {}
    messages = list(state.get("messages") or [])
    if not messages:
        return {"messages": [AIMessage(content=_REFUSAL)]}
    last = messages[-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        # Still tool-calling — leave alone; next turn will re-apply.
        return {}
    if isinstance(last, AIMessage) and getattr(last, "id", None):
        return {
            "messages": [
                RemoveMessage(id=last.id),
                AIMessage(content=_REFUSAL),
            ]
        }
    return {"messages": [AIMessage(content=_REFUSAL)]}
