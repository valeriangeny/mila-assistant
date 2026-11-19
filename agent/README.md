# Mila agent (LangGraph + Gemini)

Permission-aware knowledge assistant for aliM AI Institute. Phase 1: LangGraph agent with a stub `retrieve_knowledge` tool (role-aware signature; Qdrant ingest comes next).

LangSmith is optional (tracing / evals / Studio). The runner is the **LangGraph Agent Server**, not LangSmith itself.

## Stack

| Piece | Choice |
| --- | --- |
| Orchestration | LangGraph (`create_react_agent`) |
| LLM | Gemini via `langchain-google-genai` (API key or Vertex ADC) |
| Embeddings | FastEmbed `BAAI/bge-small-en-v1.5` (local, 384-d) |
| Tools | `retrieve_knowledge(query)` → Qdrant vector search (verified `role` from auth context) |
| Vector DB | Qdrant (`docker compose up -d qdrant` + `ingest/`) |
| Evals | LangSmith datasets (optional) — see [`docs/evals.md`](../docs/evals.md) |

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
cd agent
uv sync
cp config/.env.example config/.env.local   # set GOOGLE_API_KEY or Vertex project
```

## CLI

```bash
uv run mila-agent --env .env.local
```

## LangGraph Agent Server (local)

```bash
cd agent
uv sync --extra dev
# Prefer --no-reload locally: checkpoint writes under .langgraph_api otherwise
# thrash the watcher and can desync CopilotKit frontend tools (in-chat auth cards).
uv run langgraph dev --no-browser --no-reload
```

Graph id: `mila_agent`. Studio: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## Docker Compose

From repo root (agent + Qdrant + Copilot):

```bash
docker compose up --build
```

- Qdrant: http://127.0.0.1:6333
- Agent: http://127.0.0.1:2024
- Copilot UI: http://127.0.0.1:4000

Populate the index first (`cd ingest && uv run mila-ingest --recreate`) so retrieval returns hits.

## Evals (LangSmith)

Same pipeline as todo-app: local goldens under `evals/datasets/{name}/examples.json`, sync ↔ LangSmith, then `client.evaluate`. Suites: `mila-smoke-v1`, `mila-roles-v1`, `mila-pii-v1`, `mila-safety-v1` (+ empty `mila-adversarial-v1`). Notes: [`docs/evals.md`](../docs/evals.md).

Needs Qdrant ingested (`cd ingest && uv run mila-ingest --recreate`) for smoke/roles/pii; `LANGSMITH_API_KEY` + Gemini in `config/.env.local`.

```bash
cd agent
# Sync dataset (same name local ↔ remote; full override)
uv run python evals/sync_dataset.py --name mila-smoke-v1 --push --yes
uv run python evals/sync_dataset.py --name mila-smoke-v1 --pull --yes

# Run experiment (optional --sync pushes local first)
uv run python evals/run_eval.py --name mila-smoke-v1
uv run python evals/run_eval.py --name mila-smoke-v1 --sync

# Pytest fixture pushes results to LangSmith (skips if env missing)
MILA_EVAL_DATASET=mila-smoke-v1 uv run pytest -m langsmith
```

Persona is `inputs.caller` (mock `AgentContext`) — not the mock IdP. Prefer the sync **script** over LangSmith MCP for push/pull (git is source of truth; script does full replace).
