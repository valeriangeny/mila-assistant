"""Guardrail protocol — pick which hooks each rail implements."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, MutableMapping, Sequence

# state in → partial state update out (LangGraph node style)
HookFn = Callable[[Mapping[str, Any]], dict[str, Any]]
# (text) → (safe_text, flags)
SanitizeFn = Callable[[str], tuple[str, list[str]]]


@dataclass(frozen=True, slots=True)
class Guardrail:
    """One named policy that may hook one or more points."""

    name: str
    description: str = ""
    before_model: HookFn | None = None
    after_model: HookFn | None = None
    sanitize_hit_text: SanitizeFn | None = None
    tags: Sequence[str] = field(default_factory=tuple)


GuardrailMap = MutableMapping[str, Guardrail]
