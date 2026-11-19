"""Knowledge retrieval tool backed by Qdrant."""

from __future__ import annotations

import json
from typing import Literal

from langchain_core.tools import tool

from mila_agent.qdrant_search import search_knowledge

Role = Literal["employee", "hr", "engineering", "security"]


@tool
def retrieve_knowledge(
    query: str,
    role: Role = "employee",
) -> str:
    """Search the internal knowledge base for documents relevant to the query.

    Always pass the caller's verified role unchanged. Access is enforced in
    Qdrant via intended_audience + sensitivity allow-lists (see access_policy);
    do not invent a more privileged role.
    """
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
