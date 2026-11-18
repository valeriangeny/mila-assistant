# Mila Assistant

Permission-aware internal knowledge assistant for the hypothetical **aliM AI Institute** (take-home prototype).

## Layout

| Path | Role |
| --- | --- |
| [`instructions/`](instructions/) | Assignment brief + corpus |
| [`agent/`](agent/) | LangGraph + Gemini agent (`mila_agent`) |
| [`copilot/`](copilot/) | Next.js + CopilotKit chat UI |
| [`infra/`](infra/) | Terraform (parked; previous stack) |

## Phase 1 stack

```bash
# Option A — compose (Qdrant + agent image + copilot)
export GOOGLE_API_KEY=…   # or Vertex ADC vars
docker compose up --build

# Option B — local agent + UI
cd agent && uv sync --extra dev
cp config/.env.example config/.env.local
uv run langgraph dev          # :2024, graph mila_agent

# other terminal (repo root)
yarn install && yarn dev:copilot   # :3001
```

| Service | URL |
| --- | --- |
| Qdrant | http://127.0.0.1:6333 |
| Agent Server | http://127.0.0.1:2024 |
| Copilot | http://127.0.0.1:3001 |

## Vector DB (Qdrant) + local embeddings

Embeddings use **FastEmbed** in-process (`BAAI/bge-small-en-v1.5`) — no embed API key. Gemini is only for the chat LLM.

```bash
docker compose up -d qdrant
cd ingest && uv sync
uv run mila-ingest --recreate
```

Or: `docker compose --profile ingest run --rm ingest`

See [`ingest/README.md`](ingest/README.md). Next: RBAC + PII policy.

See [`instructions/Take-Home Assignment.md`](instructions/Take-Home%20Assignment.md).
