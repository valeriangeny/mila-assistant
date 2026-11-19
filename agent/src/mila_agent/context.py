"""Per-run caller context (verified role from auth / Studio configurable)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentContext:
    """Injected via LangGraph ``context`` / CopilotKit ``config.configurable``.

    CopilotKit maps matching ``context_schema`` keys from
    ``forwardedProps.config.configurable`` into Runtime.context.
    """

    authenticated: bool = False
    role: str = "employee"
    mila_user_id: str = ""
    mila_user_name: str = ""
