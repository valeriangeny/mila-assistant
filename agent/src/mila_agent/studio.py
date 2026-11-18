"""Compiled graph export for LangGraph Agent Server / Studio (`langgraph dev`)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_config = Path(__file__).resolve().parents[2] / "config"
# Local secrets must win over langgraph.json / empty placeholders.
load_dotenv(_config / ".env")
load_dotenv(_config / ".env.local", override=True)
load_dotenv(_config / ".env.local2sandbox", override=False)

# Empty GOOGLE_API_KEY= must not block AI Studio; also ignore blank after load.
if not (os.environ.get("GOOGLE_API_KEY") or "").strip():
    os.environ.pop("GOOGLE_API_KEY", None)

from mila_agent.graph import build_agent  # noqa: E402

graph = build_agent()
