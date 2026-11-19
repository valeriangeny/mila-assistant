# Mila Assistant

Permission-aware internal knowledge assistant for the hypothetical **aliM AI Institute** (take-home prototype).

## Layout

| Path | Role |
| --- | --- |
| [`docs/`](docs/) | Design notes: [architecture](docs/architecture.md), [OAuth + RBAC](docs/oauth-rbac.md), [PII](docs/pii.md) |
| [`instructions/`](instructions/) | Assignment brief + corpus |
| [`agent/`](agent/) | LangGraph + Gemini agent (`mila_agent`) |
| [`copilot/`](copilot/) | Next.js + CopilotKit chat UI |
| [`ingest/`](ingest/) | Corpus → Qdrant |
| [`infra/`](infra/) | Mock OIDC + parked Terraform |

See [`docs/README.md`](docs/README.md) for the design index.

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
yarn install && yarn dev:copilot   # :4000
```

| Service | URL |
| --- | --- |
| Qdrant | http://127.0.0.1:6333 |
| Agent Server | http://127.0.0.1:2024 |
| Copilot | http://127.0.0.1:4000 |

## Vector DB (Qdrant) + local embeddings

Embeddings use **FastEmbed** in-process (`BAAI/bge-small-en-v1.5`) — no embed API key. Gemini is only for the chat LLM.

```bash
docker compose up -d qdrant
cd ingest && uv sync
uv run mila-ingest --recreate
```

Or: `docker compose --profile ingest run --rm ingest`

See [`ingest/README.md`](ingest/README.md). RBAC: [`docs/oauth-rbac.md`](docs/oauth-rbac.md). PII design: [`docs/pii.md`](docs/pii.md).

See [`instructions/Take-Home Assignment.md`](instructions/Take-Home%20Assignment.md).
