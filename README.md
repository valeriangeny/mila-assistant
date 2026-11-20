# Mila Assistant

Permission-aware internal knowledge assistant for the hypothetical **aliM AI Institute** (take-home prototype).

## Layout

| Path | Role |
| --- | --- |
| [`docs/`](docs/) | Design notes: [architecture](docs/architecture.md), [OAuth + RBAC](docs/oauth-rbac.md), [PII](docs/pii.md), [evaluation](docs/evaluation-strategy.md), [guardrails](docs/guardrails.md) |
| [`instructions/`](instructions/) | Assignment brief + corpus |
| [`agent/`](agent/) | LangGraph + Gemini agent (`mila_agent`) |
| [`copilot/`](copilot/) | Next.js + CopilotKit chat UI |
| [`ingest/`](ingest/) | Corpus → Qdrant |
| [`mock-oauth2/`](mock-oauth2/) | Local mock OIDC IdP (Compose profile `auth`) |
| [`infra/`](infra/) | GCP Terraform (agent + copilot / IAP) |

**Install / build / run (local + Docker):** [`docs/install-and-run.md`](docs/install-and-run.md)  
Design index: [`docs/README.md`](docs/README.md)

## Quick start

```bash
# Credentials for Compose (or use agent/config/.env.local for local agent)
cp agent/config/.env.example .env   # set GOOGLE_API_KEY=…

# Load corpus into Qdrant (starts Qdrant if needed)
./scripts/setup.sh

# Option A — full stack in Docker
docker compose up --build

# Option B — local agent + UI (Qdrant still via Docker)
cd agent && uv sync --extra dev && uv run langgraph dev --no-browser --no-reload
# other terminal:
yarn install && yarn dev:copilot
```

| Service | URL |
| --- | --- |
| Copilot | http://127.0.0.1:4000 |
| Agent Server | http://127.0.0.1:2024 |
| Qdrant | http://127.0.0.1:6333 |

Embeddings use **FastEmbed** in-process (`BAAI/bge-small-en-v1.5`) — no embed API key. Gemini is only for the chat LLM.

See [`ingest/README.md`](ingest/README.md). RBAC: [`docs/oauth-rbac.md`](docs/oauth-rbac.md). PII: [`docs/pii.md`](docs/pii.md).

## Screenshots

- [Copilot UI flow](docs/screenshots.md) — start → in-chat sign-in → OAuth → ask → RBAC reject  
- [LangSmith UI](docs/langsmith.md) — datasets, experiments, traces, monitoring  

Assignment: [`instructions/Take-Home Assignment.md`](instructions/Take-Home%20Assignment.md).
