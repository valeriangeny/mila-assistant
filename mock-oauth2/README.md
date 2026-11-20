# Mock OAuth2 / OIDC (local IdP)

Repo-root config for local Sign in (not GCP Terraform).  
[navikt/mock-oauth2-server](https://github.com/navikt/mock-oauth2-server) in Docker — no local Java.  
Issues tokens for the four sample users in `instructions/users.json` (passwordless persona picker).

## Start

```bash
# from repo root
docker compose --profile auth up -d mock-oauth2-server
```

| URL | Purpose |
| --- | --- |
| http://127.0.0.1:8090/default/.well-known/openid-configuration | OIDC discovery |
| http://127.0.0.1:8090/default/jwks | JWKS (JWT verify) |
| http://127.0.0.1:8090/default/authorize | Authorization (shows login) |
| http://127.0.0.1:8090/isalive | Health |

Inside Compose, other services use `http://mock-oauth2-server:8080`.

## Users (login username → role claim)

| Username | `sub` | `role` |
| --- | --- | --- |
| `alice` | `u_alice` | `employee` |
| `priya` | `u_priya` | `hr` |
| `marcus` | `u_marcus` | `engineering` |
| `dana` | `u_dana` | `security` |

Edit `config.json` to change claims; edit `login.html` for the picker UI. Restart the container after changes.

## Wired into CoAgent (top bar)

1. `docker compose --profile auth up -d mock-oauth2-server`
2. Open http://127.0.0.1:4000 → **Sign in** (top bar) **or** say “sign me in” in chat
3. Pick a persona on the mock IdP page → redirect back with session cookie
4. CopilotKit sends `role` / `mila_user_id` as LangGraph context for retrieve filters

In-chat demo tools: `prompt_sign_in` (unauthenticated / incognito) and
`prompt_switch_user` (authenticated). Dismiss → `auth_mode=incognito` + role
`public`. Playwright: `e2e/tests/auth-*.spec.ts`.

Interactive login sets JWT `sub` to the username (`alice`, …). CoAgent maps that
to `instructions/users.json` personas (role, email, display name) after JWKS
verify — mock `tokenCallbacks` only match token-*request* params, so they do not
fire on the authorization-code exchange.

OIDC client settings (see `copilot/.env.local`):

- Issuer: `http://127.0.0.1:8090/default`
- Client id: `mila-copilot`
- Redirect: `http://127.0.0.1:4000/api/auth/callback`

**Studio:** use Assistants or fixed context for personas — Studio does not drive this login UI.
