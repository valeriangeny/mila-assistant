"""Eval persona mapping (inputs.caller → AgentContext)."""

from __future__ import annotations

import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parents[1] / "evals"
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

from dataset_io import caller_dict_from_row, context_from_inputs  # noqa: E402


def test_context_defaults_unauthenticated() -> None:
    ctx = context_from_inputs({"messages": [{"role": "human", "content": "hi"}]})
    assert ctx.auth_mode == "unauthenticated"
    assert ctx.role == "employee"


def test_context_from_caller() -> None:
    ctx = context_from_inputs(
        {
            "messages": [{"role": "human", "content": "hi"}],
            "caller": {
                "auth_mode": "authenticated",
                "role": "hr",
                "mila_user_id": "u_priya",
                "mila_user_name": "Priya Shah",
            },
        }
    )
    assert ctx.auth_mode == "authenticated"
    assert ctx.authenticated is True
    assert ctx.role == "hr"
    assert ctx.mila_user_id == "u_priya"


def test_caller_promoted_from_metadata() -> None:
    caller = caller_dict_from_row(
        {"messages": []},
        {"auth_mode": "incognito", "role": "employee"},
    )
    assert caller["auth_mode"] == "incognito"
