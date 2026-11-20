# Infra — GCP (Terraform) + local mock IdP

Mila’s cloud shape is **Copilot + LangGraph agent** behind IAP, talking to **Qdrant** and **Gemini/Vertex**. Local auth uses Compose mock OIDC at repo-root [`../mock-oauth2/`](../mock-oauth2/), not this Terraform.

This folder was trimmed from a prior Todo-app stack: **no** Cloud SQL, REST API, MCP service, or static GCS frontend.

## Layout

| Path | Role |
| --- | --- |
| **`stack/`** | Once per GCP project: APIs, Artifact Registry, WIF deploy SA, IAP OAuth settings |
| **`env/`** | Per environment: Secret Manager + agent/copilot Cloud Run + HTTPS LB/IAP |
| **`modules/`** | `project_apis`, `artifact_registry`, `github_deploy`, `secrets`, `agent` |
| **`envs/*.tfvars.example`** | Copy → `*.tfvars` (gitignored secrets) |

| Identity | State | Tfvars |
| --- | --- | --- |
| **nonprod** (stack) | `states/nonprod.tfstate` | `envs/nonprod.tfvars` |
| **sandbox** / **staging** / **prod** (env) | `states/<env>.tfstate` | `envs/<env>.tfvars` |

Env tfvars must list stack outputs (`artifact_registry_*`, `deploy_sa_email`, `iap_*`) plus **`qdrant_url`**.

## What was removed (not used by Mila)

| Removed module | Why |
| --- | --- |
| `apis` | No separate REST API Cloud Run |
| `mcp` | No Streamable-HTTP MCP service (agent uses Qdrant directly) |
| `sql_instance` / `sql_database` | Knowledge is Qdrant, not Postgres |
| `frontends` | UI is CopilotKit on Cloud Run, not a public GCS SPA bucket |

LangGraph’s **sidecar** Redis/Postgres inside the agent container (checkpointing) is unrelated to Cloud SQL and remains in `modules/agent`.

## Apply order

```bash
cd infra

# 1) Project stack (once)
cp envs/nonprod.tfvars.example envs/nonprod.tfvars   # set project_id + IAP
terraform -chdir=stack init -reconfigure -backend-config=backends/nonprod.hcl
terraform -chdir=stack apply -var-file=../envs/nonprod.tfvars
terraform -chdir=stack output

# 2) Sandbox env
cp envs/sandbox.tfvars.example envs/sandbox.tfvars
# paste stack outputs; set qdrant_url, agent_iap_host, copilot_host, LangSmith key
terraform -chdir=env init -reconfigure -backend-config=backends/sandbox.hcl
terraform -chdir=env apply -var-file=../envs/sandbox.tfvars
```

Build / push images (example):

```bash
docker build -t "$(terraform -chdir=infra/env output -raw agent_image)" ./agent
docker build -f copilot/Dockerfile -t "$(terraform -chdir=infra/env output -raw copilot_image)" .
docker push "$(terraform -chdir=infra/env output -raw agent_image)"
docker push "$(terraform -chdir=infra/env output -raw copilot_image)"
```

DNS **A** for `agent_iap_host` and `copilot_host` → `terraform -chdir=env output -raw agent_iap_ip`.

## Agent + Copilot + IAP

**IAP is stack-owned** (one OAuth client + accessor list per GCP project). Env wires Cloud Run + HTTPS LB.

Keep OAuth consent **Internal**. Accessors must be Cloud Identity / Workspace users on the org domain — not consumer Gmail.

1. Create OAuth 2.0 Web client; redirect: `https://iap.googleapis.com/v1/oauth/clientIds/<CLIENT_ID>:handleRedirect`.
2. Set `iap_*` in stack tfvars; apply stack.
3. Copy `iap_*` into env tfvars; set hosts + `qdrant_url`.
4. Point DNS at `agent_iap_ip`.

Public URLs: `agent_iap_url`, `copilot_url` (shared LB IP + IAP).

## Qdrant (next)

`qdrant_url` is an input today (Qdrant Cloud, GCE, etc.). A Terraform module for managed/self-hosted Qdrant + ingest job can land later; local/dev still uses `docker compose` + `./scripts/setup.sh`.

## Local mock IdP

Lives at repo root (`../mock-oauth2/`), not under `infra/`:

```bash
# from repo root
docker compose --profile auth up -d mock-oauth2-server
# http://127.0.0.1:8090 — see mock-oauth2/README.md
```

## Cost note

No Cloud SQL instance from this stack. Agent module still adds a small VPC for copilot Direct VPC egress + a global HTTPS LB / static IP / managed cert for IAP.
