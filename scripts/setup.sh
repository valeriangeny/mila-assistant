#!/usr/bin/env bash
# Start Qdrant (if needed) and (re)load the knowledge corpus.
#
# Usage (from repo root):
#   ./scripts/setup.sh
#   ./scripts/setup.sh --adversarial
#   ./scripts/setup.sh --docker
#   ./scripts/setup.sh --docker --adversarial --skip-pii
#
# Ingest is intentionally separate from `docker compose up`: it recreates the
# collection and may download embedding / NER models on first run.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

USE_DOCKER=0
ADVERSARIAL=0
SKIP_PII=0

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --docker) USE_DOCKER=1 ;;
    --adversarial) ADVERSARIAL=1 ;;
    --skip-pii) SKIP_PII=1 ;;
    -h | --help) usage 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage 1
      ;;
  esac
  shift
done

INGEST_ARGS=(--recreate)
if [[ "$ADVERSARIAL" -eq 1 ]]; then
  INGEST_ARGS+=(--include-adversarial)
fi

export_env_for_ingest() {
  if [[ "$SKIP_PII" -eq 1 ]]; then
    export MILA_SKIP_PII=1
  fi
}

ensure_qdrant() {
  if curl -sf "http://127.0.0.1:6333/readyz" >/dev/null 2>&1; then
    echo "setup> Qdrant already ready on :6333"
    return
  fi
  echo "setup> starting Qdrant via docker compose…"
  docker compose up -d qdrant
  echo "setup> waiting for Qdrant…"
  for _ in $(seq 1 60); do
    if curl -sf "http://127.0.0.1:6333/readyz" >/dev/null 2>&1; then
      echo "setup> Qdrant ready"
      return
    fi
    sleep 1
  done
  echo "setup> Qdrant did not become ready on :6333" >&2
  exit 1
}

seed_agent_env() {
  local example="$ROOT/agent/config/.env.example"
  local local_env="$ROOT/agent/config/.env.local"
  if [[ -f "$example" && ! -f "$local_env" ]]; then
    cp "$example" "$local_env"
    echo "setup> created agent/config/.env.local from .env.example (add GOOGLE_API_KEY)"
  fi
}

ingest_local() {
  echo "setup> ingest via local uv (${INGEST_ARGS[*]})…"
  export_env_for_ingest
  (
    cd "$ROOT/ingest"
    uv sync
    uv run mila-ingest "${INGEST_ARGS[@]}"
  )
}

ingest_docker() {
  echo "setup> ingest via compose profile (${INGEST_ARGS[*]})…"
  export_env_for_ingest
  # Override the default profile command so --include-adversarial can be passed.
  docker compose --profile ingest run --rm \
    -e "MILA_SKIP_PII=${MILA_SKIP_PII:-}" \
    ingest uv run mila-ingest "${INGEST_ARGS[@]}"
}

seed_agent_env
ensure_qdrant

if [[ "$USE_DOCKER" -eq 1 ]]; then
  ingest_docker
else
  if ! command -v uv >/dev/null 2>&1; then
    echo "setup> uv not found; re-run with --docker or install https://docs.astral.sh/uv/" >&2
    exit 1
  fi
  ingest_local
fi

echo "setup> done — collection mila_docs is ready for the agent"
