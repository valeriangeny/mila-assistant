"""Retrieve tool auth_mode gate (no Qdrant)."""

from __future__ import annotations

import json

from langgraph.prebuilt import ToolRuntime

from mila_agent.context import AgentContext
from mila_agent.retrieve import retrieve_knowledge


def _runtime(ctx: AgentContext) -> ToolRuntime[AgentContext]:
    return ToolRuntime(
        state={},
        context=ctx,
        config={},
        stream_writer=lambda *_a, **_k: None,
        tool_call_id="test-call",
        store=None,
    )


def test_unauthenticated_returns_auth_required() -> None:
    raw = retrieve_knowledge.func(
        "what is the vacation policy?",
        _runtime(AgentContext(auth_mode="unauthenticated")),
    )
    payload = json.loads(raw)
    assert payload["status"] == "auth_required"
    assert payload["action"] == "prompt_sign_in"
    assert payload["hits"] == []


def test_incognito_uses_public_role(monkeypatch) -> None:
    seen: dict[str, str] = {}

    def fake_search(query: str, role: str):
        seen["query"] = query
        seen["role"] = role
        return {"status": "ok", "query": query, "role": role, "hits": []}

    monkeypatch.setattr("mila_agent.retrieve.search_knowledge", fake_search)
    raw = retrieve_knowledge.func(
        "welcome handbook",
        _runtime(AgentContext(auth_mode="incognito", role="employee")),
    )
    payload = json.loads(raw)
    assert seen["role"] == "public"
    assert payload["role"] == "public"
    assert payload["auth_mode"] == "incognito"


def test_authenticated_uses_verified_role(monkeypatch) -> None:
    seen: dict[str, str] = {}

    def fake_search(query: str, role: str):
        seen["role"] = role
        return {"status": "ok", "query": query, "role": role, "hits": []}

    monkeypatch.setattr("mila_agent.retrieve.search_knowledge", fake_search)
    raw = retrieve_knowledge.func(
        "comp bands",
        _runtime(
            AgentContext(
                auth_mode="authenticated",
                authenticated=True,
                role="hr",
                mila_user_id="u_priya",
                mila_user_name="Priya Shah",
            )
        ),
    )
    payload = json.loads(raw)
    assert seen["role"] == "hr"
    assert payload["role"] == "hr"
    assert payload["auth_mode"] == "authenticated"
