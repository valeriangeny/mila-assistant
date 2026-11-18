"""Interactive CLI for the Mila knowledge assistant."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from mila_agent.graph import build_agent, run_agent_async


def _agent_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _config_dir() -> Path:
    return _agent_root() / "config"


def _resolve_env_path(env_file: str) -> Path:
    path = Path(env_file)
    if path.is_absolute():
        return path
    candidates = [_config_dir() / path.name, _config_dir() / path, _agent_root() / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit(f"Env file not found: {env_file} (looked under agent/config/)")


def _load_env(env_file: str | None) -> Path | None:
    config = _config_dir()
    load_dotenv(config / ".env")
    # Local secrets win over empty placeholders / shell leftovers.
    load_dotenv(config / ".env.local", override=True)
    if env_file:
        path = _resolve_env_path(env_file)
        load_dotenv(path, override=True)
        return path
    if not (os.environ.get("GOOGLE_API_KEY") or "").strip():
        os.environ.pop("GOOGLE_API_KEY", None)
    return config / ".env.local" if (config / ".env.local").is_file() else None


def _auth_mode() -> str:
    if (os.environ.get("GOOGLE_API_KEY") or "").strip():
        return "api-key (AI Studio)"
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT") or "?"
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    return f"vertex ADC ({project} / {location})"


async def _async_main() -> None:
    print(f"auth> {_auth_mode()}", flush=True)
    print("building> agent…", flush=True)
    agent = build_agent()
    print(
        "Mila assistant (Gemini + LangGraph). Empty line or Ctrl-D to exit.\n",
        flush=True,
    )
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            break
        try:
            print("…", flush=True)
            out = await run_agent_async(line, agent=agent)
        except Exception as exc:  # noqa: BLE001 — CLI surface
            print(f"error> {exc}", file=sys.stderr)
            continue
        traj = out["trajectory"]
        if traj:
            tools = ", ".join(f"{t['tool']}" for t in traj)
            print(f"tools> {tools}")
        print(f"agent> {out['answer']}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mila knowledge assistant CLI")
    parser.add_argument(
        "--env",
        default=os.environ.get("MILA_AGENT_ENV"),
        help="Env file under agent/config/ (default: .env.local if present)",
    )
    args = parser.parse_args()
    loaded = _load_env(args.env)
    if loaded:
        print(f"env> {loaded}", flush=True)
    if not os.environ.get("GOOGLE_API_KEY") and not (
        os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
    ):
        try:
            import subprocess

            project = subprocess.check_output(
                ["gcloud", "config", "get-value", "project"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if project and project != "(unset)":
                os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project)
        except Exception:  # noqa: BLE001
            pass

    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
