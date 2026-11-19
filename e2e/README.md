# Mila auth Playwright scenarios

Three auth flows against the local CoAgent UI + mock IdP.

| Spec | Trigger |
| --- | --- |
| `auth-top-bar.spec.ts` | Top-bar **Sign in** |
| `auth-chat-prompt.spec.ts` | Chat “sign me in” / Continue as incognito |
| `auth-implicit-rag.spec.ts` | Knowledge question → `auth_required` → sign-in card |

## Prerequisites

```bash
# Terminal A — mock IdP
docker compose --profile auth up -d mock-oauth2-server

# Terminal B — Agent Server (chat + RAG flows)
cd agent && uv run langgraph dev

# Terminal C — CoAgent UI
yarn dev:copilot
```

`copilot/.env.local` must point at the agent (`LANGGRAPH_URL`) and mock OIDC.

## Run

```bash
cd e2e
yarn install
yarn install:browsers
yarn test                 # all auth specs
yarn test auth-top-bar    # OIDC only (no LLM)
```

Top-bar tests need only UI + mock IdP. Chat / RAG specs need a live agent
(and Gemini). Skip them when the agent is down:

```bash
yarn test auth-top-bar
```
