"""Knowledge retrieval tool backed by Qdrant."""

from __future__ import annotations

import json

from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime

from mila_agent.access_policy import normalize_role
from mila_agent.context import AgentContext
from mila_agent.qdrant_search import search_knowledge


def _role_from_runtime(runtime: ToolRuntime[AgentContext] | None) -> str:
    if runtime is None:
        return normalize_role(None)
    ctx = getattr(runtime, "context", None)
    if ctx is not None:
        role = getattr(ctx, "role", None) or (ctx.get("role") if isinstance(ctx, dict) else None)
        if role:
            return normalize_role(str(role))
    cfg = getattr(runtime, "config", None) or {}
    configurable = cfg.get("configurable") if isinstance(cfg, dict) else None
    if isinstance(configurable, dict) and configurable.get("role"):
        return normalize_role(str(configurable["role"]))
    return normalize_role(None)


@tool
def retrieve_knowledge(
    query: str,
    runtime: ToolRuntime[AgentContext],
) -> str:
    """Search the internal knowledge base for documents relevant to the query.

    Access uses the caller's verified role from auth context (not a model-chosen
    role). Hits are filtered in Qdrant via intended_audience + sensitivity
    allow-lists (see access_policy).
    """
    role = _role_from_runtime(runtime)
    try:
        payload = search_knowledge(query, role=role)
    except Exception as exc:  # noqa: BLE001 — surface to the agent
        payload = {
            "status": "error",
            "message": str(exc),
            "query": query,
            "role": role,
            "hits": [],
        }
    return json.dumps(payload)
