"""Compiled graph export for LangGraph Agent Server / Studio (`langgraph dev`)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

_config = Path(__file__).resolve().parents[2] / "config"


def _load_config_env() -> None:
    """Merge config files without clobbering process exports (Compose / shell)."""
    preset = set(os.environ)
    merged: dict[str, str] = {}
    for path in (
        _config / ".env",
        _config / ".env.local",
        _config / ".env.local2sandbox",
    ):
        if not path.is_file():
            continue
        for key, value in dotenv_values(path).items():
            if value is not None:
                merged[key] = value
    for key, value in merged.items():
        if key not in preset:
            os.environ[key] = value


_load_config_env()

# Empty GOOGLE_API_KEY= must not block AI Studio; also ignore blank after load.
if not (os.environ.get("GOOGLE_API_KEY") or "").strip():
    os.environ.pop("GOOGLE_API_KEY", None)

from mila_agent.graph import build_agent  # noqa: E402

graph = build_agent()
