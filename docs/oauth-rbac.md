# OAuth pattern + RBAC

How identity reaches the agent, and how document access is enforced.

## Goals

- Real OIDC login UX (local mock IdP) for four assignment personas.
- Verified **role** drives retrieval filters — not invented by the LLM.
- Guests can opt into **incognito** (`public` role) without signing in.
- Unauthenticated callers cannot search the corpus.

## Auth modes

| `auth_mode` | How entered | Role used for retrieve |
| --- | --- | --- |
| `unauthenticated` | No session, no guest opt-in | — (retrieve returns `auth_required`) |
| `authenticated` | Valid session cookie after OIDC | Session `role` (`employee` / `hr` / `engineering` / `security`) |
| `incognito` | User dismisses sign-in prompt | Forced `public` |

Defined in `agent/src/mila_agent/context.py`; derived on the client in `copilot/src/lib/auth/mode.ts`.

## OIDC flow (mock)

```mermaid
sequenceDiagram
  participant U as User
  participant UI as Copilot UI
  participant N as Next.js /api/auth
  participant IdP as Mock OIDC :8090
  participant A as LangGraph agent

  U->>UI: Sign in (bar or chat tool)
  UI->>N: GET /api/auth/login?returnTo=/?thread=…
  N->>N: PKCE + state cookies
  N->>IdP: redirect /authorize
  U->>IdP: pick persona (alice / priya / …)
  IdP->>N: /api/auth/callback?code&state
  N->>IdP: token exchange + JWKS verify id_token
  N->>N: map claims → persona; seal HMAC session cookie
  N->>UI: redirect returnTo
  UI->>A: CopilotKit properties (auth_mode, role, …)
  A->>A: retrieve_knowledge uses role filters
```

### Implementation notes

| Piece | Location |
| --- | --- |
| IdP | `infra/mock-oauth2/` — [navikt/mock-oauth2-server](https://github.com/navikt/mock-oauth2-server) |
| Login / callback / logout / me | `copilot/src/app/api/auth/*` |
| PKCE + JWKS verify | `copilot/src/lib/auth/oidc.ts` |
| Session | HMAC-sealed cookie (`copilot/src/lib/auth/session.ts`) |
| Personas | `copilot/src/lib/auth/personas.ts` ↔ `instructions/users.json` |

Login is authorization-code + PKCE (`S256`). After verify, claims are mapped to a known persona (`sub` / username → role, email, display name). Unknown subjects are rejected.

Local issuer (typical): `http://127.0.0.1:8090/default`, client `mila-copilot`, redirect `http://127.0.0.1:4000/api/auth/callback`.

### Personas

| Username | Role |
| --- | --- |
| `alice` | `employee` |
| `priya` | `hr` |
| `marcus` | `engineering` |
| `dana` | `security` |

## Passing identity into the agent

CopilotKit `properties` include:

- `auth_mode`
- `authenticated` (compat)
- `role`
- `mila_user_id` / `mila_user_name`

These land in LangGraph `AgentContext` (via CopilotKit ↔ `context_schema` / configurable). The system prompt states the mode; **enforcement is in tools**, not prompt text.

In-chat: `prompt_sign_in` / `prompt_switch_user` (generative UI). Dismiss → `incognito`.

## Document RBAC

Policy is table-driven in `agent/src/mila_agent/access_policy.py`.

A chunk is visible iff:

```text
doc.intended_audience ∈ role.audiences
AND doc.sensitivity ∈ role.sensitivities
```

`department` is **not** in the default gate. Unknown role strings fall back to `employee`. Incognito uses the explicit `public` scope (stricter than employee).

| Role | Audiences (summary) | Sensitivities |
| --- | --- | --- |
| `public` | company-wide | public |
| `employee` | company-wide | public, internal |
| `hr` | company-wide, people-ops (+ shared), function-leads | all |
| `engineering` | company-wide, engineering (+ shared), function-leads | public → confidential |
| `security` | company-wide, security (+ shared), function-leads | all |

Retrieve path:

1. Resolve `auth_mode` → refuse if unauthenticated.
2. Role = `public` if incognito, else normalized session role.
3. `qdrant_filter_for_role(role)` on payload indexes.
4. Return hits (bodies treated as **untrusted** in the system prompt — adversarial docs).

Unit tests: `agent/tests/test_access_policy.py`, `test_retrieve_auth.py`.  
E2E: `e2e/tests/auth-*.spec.ts`.

## Trust boundary (current + known gaps)

**Intended:** role comes from verified session → client properties → agent context → Qdrant filter.

**Prototype gap (called out in review):** the Agent Server currently trusts CopilotKit-forwarded properties. A hardened deployment should bind role server-side to the sealed session (or an exchanged assertion) so the browser cannot assert `role=hr` without a cookie. Same for fail-closed `AUTH_SECRET` and stricter `aud` checks on the IdP.

## Related

- [Architecture](./architecture.md)
- [PII handling](./pii.md) — field-level policy on top of document RBAC
