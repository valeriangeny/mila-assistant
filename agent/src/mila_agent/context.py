"""Per-run caller context (verified auth + role from UI / Studio)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AuthMode = Literal["unauthenticated", "authenticated", "incognito"]


@dataclass
class AgentContext:
    """Injected via LangGraph ``context`` / CopilotKit ``config.configurable``.

    CopilotKit maps matching ``context_schema`` keys from
    ``forwardedProps.config.configurable`` into Runtime.context.

    ``auth_mode``:
    - ``unauthenticated`` — no session, no guest opt-in; retrieve must refuse.
    - ``authenticated`` — mock OIDC session; use verified ``role``.
    - ``incognito`` — user dismissed sign-in; use ``public`` role filters.
    """

    auth_mode: AuthMode = "unauthenticated"
    # Kept for older clients / Studio; prefer auth_mode.
    authenticated: bool = False
    role: str = "employee"
    mila_user_id: str = ""
    mila_user_name: str = ""


def resolve_auth_mode(ctx: AgentContext) -> AuthMode:
    """Normalize auth_mode, falling back to ``authenticated`` bool for compat."""
    mode = (ctx.auth_mode or "").strip().lower()
    if mode in {"unauthenticated", "authenticated", "incognito"}:
        return mode  # type: ignore[return-value]
    if ctx.authenticated:
        return "authenticated"
    return "unauthenticated"
