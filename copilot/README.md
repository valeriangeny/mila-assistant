# copilot (CopilotKit)

Next.js chat UI + CopilotKit runtime BFF over the self-hosted **LangGraph Agent Server** (`mila_agent`).

This is **not** LangGraph Platform. CopilotKit talks to our Agent Server URL; LangSmith is optional tracing on the agent side only.

## Local

```bash
# Terminal 1 — Agent Server (from agent/)
uv sync --extra dev
uv run langgraph dev

# Terminal 2 — copilot (repo root)
yarn install
yarn dev:copilot
# http://localhost:3001
```

`copilot/.env.local`:

```bash
LANGGRAPH_URL=http://127.0.0.1:2024
LANGGRAPH_GRAPH_ID=mila_agent
```

Or bring everything up with root `docker compose up --build`.
