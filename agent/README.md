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
| Evals | LangSmith datasets (optional) |

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
