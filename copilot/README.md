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
# http://localhost:4000
```

`copilot/.env.local`:

```bash
LANGGRAPH_URL=http://127.0.0.1:2024
LANGGRAPH_GRAPH_ID=mila_agent
OIDC_ISSUER=http://127.0.0.1:8090/default
OIDC_CLIENT_ID=mila-copilot
APP_ORIGIN=http://127.0.0.1:4000
```

Mock IdP (persona picker; config in [`mock-oauth2/`](../mock-oauth2/)):

```bash
docker compose --profile auth up -d mock-oauth2-server
```

Then open http://localhost:4000 and use **Sign in** in the top bar, or say
“sign me in” in chat for the in-chat auth demo (card → mock IdP redirect).

Chat continuity: OIDC login returns to `/?thread=<id>` (also mirrored in
`localStorage` as `mila.copilot.threadId`) so CopilotKit reconnects the same
thread after the IdP round-trip. Browse via the same host as `APP_ORIGIN`
(e.g. `http://127.0.0.1:4000`, not `localhost`) so storage and cookies align.

Or bring everything up with root `docker compose up --build`.
