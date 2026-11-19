# App architecture

Permission-aware RAG chat for aliM AI Institute: Next.js + CopilotKit UI, LangGraph agent, Qdrant knowledge base, Gemini for generation.

## Components

| Layer | Path | Responsibility |
| --- | --- | --- |
| Chat UI | `copilot/` | Next.js App Router, CopilotKit sidebar, auth UX, thread persistence |
| Auth routes | `copilot/src/app/api/auth/*` | OIDC login/callback/logout/me; sealed session cookie |
| Copilot runtime | `copilot/src/app/api/copilotkit` | Bridges browser → LangGraph Agent Server |
| Agent | `agent/` | ReAct graph (`mila_agent`), tools, RBAC-filtered retrieve |
| Ingest | `ingest/` | Chunk corpus → FastEmbed → Qdrant payloads |
| IdP (local) | `infra/mock-oauth2/` | Mock OIDC for four personas |
| Vector DB | Qdrant | Chunks + ACL metadata (`sensitivity`, `intended_audience`, …) |

## High-level diagram

```mermaid
flowchart TB
  subgraph browser["Browser"]
    UB[UserBar / Sign in]
    CS[CopilotSidebar]
    LS[(localStorage<br/>threadId + message cache)]
  end

  subgraph next["Next.js · copilot :4000"]
    AuthAPI["/api/auth/*"]
    CK["/api/copilotkit"]
    Sess[HMAC session cookie]
  end

  IdP["Mock OIDC<br/>:8090"]

  subgraph agent["LangGraph Agent Server :2024"]
    Graph[mila_agent ReAct]
    Tools[retrieve_knowledge<br/>+ auth demo tools]
    Policy[access_policy]
  end

  Q[(Qdrant :6333)]
  Gemini[Gemini LLM]

  UB --> AuthAPI
  AuthAPI <--> IdP
  AuthAPI --> Sess
  CS --> CK
  LS -.-> CS
  CK --> Graph
  Sess -.->|auth_mode, role via<br/>CopilotKit properties| CK
  Graph --> Tools
  Tools --> Policy
  Policy --> Q
  Graph <--> Gemini
```

## Frontend shell

`Providers` (`copilot/src/app/providers.tsx`) owns the composition:

1. **UserBar** — session identity, role, Sign in / Sign out.
2. **CopilotKit** — `threadId` from `usePersistentThreadId`, `properties` from `agentProperties(user, authMode)`.
3. **ThreadMessageCache** — mirrors transcript to `localStorage` so OIDC redirects do not wipe history.
4. **FlushThreadOnLogin** — writes messages immediately before leaving for the IdP.
5. **ChatAuthDemo** — generative-UI tools: `prompt_sign_in`, `prompt_switch_user`; dismiss → `auth_mode=incognito`.
6. **CopilotSidebar** — chat surface; welcome label is auth-agnostic and suppressed when cached messages exist.

```mermaid
flowchart LR
  page[page.tsx] --> providers[Providers]
  providers --> bar[UserBar]
  providers --> ck[CopilotKit]
  ck --> cache[ThreadMessageCache]
  ck --> flush[FlushThreadOnLogin]
  ck --> demo[ChatAuthDemo]
  ck --> side[CopilotSidebar]
```

## Chat request path

1. User sends a message in the sidebar.
2. Browser → `POST /api/copilotkit` with agent `mila_agent` and `properties` (`auth_mode`, `role`, `mila_user_id`, …).
3. CopilotKit Runtime → LangGraph Agent Server (`LANGGRAPH_URL`).
4. CopilotKit maps matching property keys into LangGraph `AgentContext`.
5. Model may call `retrieve_knowledge` → Qdrant filter from `access_policy` → grounded reply.

Unauthenticated retrieve returns `status=auth_required` so the agent can call `prompt_sign_in` instead of searching.

## Thread restore across OIDC

OIDC is a full-page redirect. To keep one conversation:

- Stable `threadId` in `localStorage` (+ `?thread=` on `returnTo`).
- Message cache keyed by thread; re-applied if the live transcript is shorter after reconnect.
- Do not remount CopilotKit on auth alone (key is `threadId` only).
- Sign-out / user switch clears thread + message caches via `destroyClientThreadState`.

## Data plane (ingest → retrieve)

```text
documents.jsonl  →  chunk + PII detect + FastEmbed  →  Qdrant points
                                         payload: text, ACL fields, pii_spans, …
retrieve_knowledge  →  vector search + role filter  →  anonymize by role  →  LLM
```

Embeddings: in-process FastEmbed (`BAAI/bge-small-en-v1.5`). Gemini is used only for chat generation.

## Related

- [OAuth + RBAC](./oauth-rbac.md)
- [PII handling](./pii.md)
