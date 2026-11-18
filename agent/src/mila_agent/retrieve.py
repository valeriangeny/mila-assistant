"""Knowledge retrieval tool.

Phase 1: stub that accepts `role` (for future RBAC pre-filters) but does not
query Qdrant yet. Phase 2 wires Qdrant; Phase 3 enforces policy.
"""

from __future__ import annotations

import json
from typing import Literal

from langchain_core.tools import tool

Role = Literal["employee", "hr", "engineering", "security"]


@tool
def retrieve_knowledge(
    query: str,
    role: Role = "employee",
) -> str:
    """Search the internal knowledge base for documents relevant to the query.

    Always pass the caller's verified role. Authorization filters will use it;
    do not invent a more privileged role.
    """
    payload = {
        "status": "not_indexed",
        "message": (
            "Ingest has not populated Qdrant yet. No documents retrieved. "
            "Answer only from general knowledge is disallowed — say you have "
            "no accessible sources."
        ),
        "query": query,
        "role": role,
        "hits": [],
    }
    return json.dumps(payload)
