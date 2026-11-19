"""Knowledge retrieval tool backed by Qdrant."""

from __future__ import annotations

import json

from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime

from mila_agent.access_policy import normalize_role
from mila_agent.context import AgentContext, resolve_auth_mode
from mila_agent.qdrant_search import search_knowledge


def _context_from_runtime(runtime: ToolRuntime[AgentContext] | None) -> AgentContext:
    if runtime is None:
        return AgentContext()
    ctx = getattr(runtime, "context", None)
    if isinstance(ctx, AgentContext):
        return ctx
    if isinstance(ctx, dict):
        return AgentContext(
            auth_mode=ctx.get("auth_mode") or "unauthenticated",
            authenticated=bool(ctx.get("authenticated")),
            role=str(ctx.get("role") or "employee"),
            mila_user_id=str(ctx.get("mila_user_id") or ""),
            mila_user_name=str(ctx.get("mila_user_name") or ""),
        )
    cfg = getattr(runtime, "config", None) or {}
    configurable = cfg.get("configurable") if isinstance(cfg, dict) else None
    if isinstance(configurable, dict):
        return AgentContext(
            auth_mode=configurable.get("auth_mode") or "unauthenticated",
            authenticated=bool(configurable.get("authenticated")),
            role=str(configurable.get("role") or "employee"),
            mila_user_id=str(configurable.get("mila_user_id") or ""),
            mila_user_name=str(configurable.get("mila_user_name") or ""),
        )
    return AgentContext()


def _role_for_search(ctx: AgentContext) -> str:
    mode = resolve_auth_mode(ctx)
    if mode == "incognito":
        return "public"
    return normalize_role(ctx.role)


@tool
def retrieve_knowledge(
    query: str,
    runtime: ToolRuntime[AgentContext],
) -> str:
    """Search the internal knowledge base for documents relevant to the query.

    Requires auth_mode authenticated or incognito. Unauthenticated calls return
    status=auth_required (call prompt_sign_in). Access filters use the verified
    role, or public when incognito.
    """
    ctx = _context_from_runtime(runtime)
    mode = resolve_auth_mode(ctx)

    if mode == "unauthenticated":
        return json.dumps(
            {
                "status": "auth_required",
                "action": "prompt_sign_in",
                "message": (
                    "Caller is unauthenticated. Call prompt_sign_in so the user can "
                    "sign in or continue as incognito (public role), then retry."
                ),
                "query": query,
                "auth_mode": mode,
                "hits": [],
            }
        )

    role = _role_for_search(ctx)
    try:
        payload = search_knowledge(query, role=role)
    except Exception as exc:  # noqa: BLE001 — surface to the agent
        payload = {
            "status": "error",
            "message": str(exc),
            "query": query,
            "role": role,
            "auth_mode": mode,
            "hits": [],
        }
    else:
        if isinstance(payload, dict):
            payload = {**payload, "auth_mode": mode, "role": role}
    return json.dumps(payload)
