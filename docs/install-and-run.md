# Install, build, and run

How to get Mila Assistant running from a clean clone: prerequisites, local build + run, and Docker Compose. For design notes see [architecture](./architecture.md); for corpus ingest details see [`ingest/README.md`](../ingest/README.md).

## Prerequisites

| Tool | Used for |
| --- | --- |
| [Docker](https://docs.docker.com/get-docker/) + Compose v2 | Qdrant, full stack, mock IdP |
| [uv](https://docs.astral.sh/uv/) | Agent + ingest (Python) |
| Node **≥ 22** + [Yarn 1](https://classic.yarnpkg.com/) | Copilot UI (local path) |
| Gemini auth | `GOOGLE_API_KEY` (AI Studio) **or** Vertex (`GOOGLE_CLOUD_PROJECT` + ADC) |

Optional: [LangSmith](https://smith.langchain.com/) API key for tracing/evals; mock OIDC is Compose profile `auth`.

## What is dockerized?

| Piece | Dockerized? | How |
| --- | --- | --- |
| **Qdrant** | Yes | Official `qdrant/qdrant` image |
| **Agent** (LangGraph) | Yes | `agent/Dockerfile` → Compose service `agent` |
| **Copilot** (Next.js) | Yes | `copilot/Dockerfile` → Compose service `copilot` |
| **Ingest** | Yes (one-shot) | Compose **profile** `ingest` — `uv` image + bind mount; no custom Dockerfile |
| **Mock OIDC** | Yes (optional) | Compose **profile** `auth` — Navikt image + [`mock-oauth2/`](../mock-oauth2/) config |
| **E2E (Playwright)** | No | Runs on the host against local/compose URLs |
| **Terraform / Cloud Run** | N/A | Packaged for GCP (`infra/`), not local Compose |

Default `docker compose up --build` starts **qdrant + agent + copilot**. Ingest and auth are opt-in profiles so empty-index and IdP are explicit steps.

## Populate Qdrant (required for retrieval)

Compose does **not** auto-load the corpus. After Qdrant is up, run ingest once (or whenever you change `instructions/*.jsonl`).

**Recommended helper** (from repo root):

```bash
./scripts/setup.sh              # start Qdrant if needed + ingest main corpus
./scripts/setup.sh --adversarial  # also include ADV-* injection docs
./scripts/setup.sh --docker       # ingest via Compose profile (no local uv)
./scripts/setup.sh --skip-pii     # faster smoke (skips Presidio)
```

Manual equivalents:

```bash
# Local uv
docker compose up -d qdrant
cd ingest && uv sync && uv run mila-ingest --recreate

# Compose one-shot
docker compose --profile ingest run --rm ingest
```

Why a `setup.sh` instead of baking ingest into `docker compose up`? Ingest is **destructive** (`--recreate`), downloads embedding/NER models on first run, and is intentionally separate from long-running services. A script documents that boundary without surprising operators who only wanted to restart the UI.

---

## Path A — Docker (build + run)

Best for reviewers: build images and run the chat stack with few host tools.

```bash
# 1) LLM credentials for Compose (repo root .env is auto-loaded)
cp agent/config/.env.example .env   # or export in the shell
# edit: set GOOGLE_API_KEY=…  (or Vertex vars)

# 2) Build & start Qdrant + agent + copilot
docker compose up --build

# 3) Other terminal — load the index
./scripts/setup.sh --docker

# Optional mock IdP for Sign in
docker compose --profile auth up -d mock-oauth2-server
```

| Service | URL |
| --- | --- |
| Copilot UI | http://127.0.0.1:4000 |
| Agent Server | http://127.0.0.1:2024 |
| Qdrant | http://127.0.0.1:6333 |
| Mock OIDC | http://127.0.0.1:8090 (profile `auth`) |

Rebuild after code changes: `docker compose up --build`. Stop: `docker compose down` (add `-v` to wipe the Qdrant volume).

Individual image builds:

```bash
docker build -t mila-agent:local ./agent
docker build -f copilot/Dockerfile -t mila-copilot:local .
```

---

## Path B — Local build + run

Best for day-to-day agent/UI development (hot reload).

### 1. Env

```bash
cd agent
cp config/.env.example config/.env.local
# set GOOGLE_API_KEY or Vertex project in config/.env.local
```

Copilot (optional overrides in `copilot/.env.local`):

```bash
LANGGRAPH_URL=http://127.0.0.1:2024
LANGGRAPH_GRAPH_ID=mila_agent
OIDC_ISSUER=http://127.0.0.1:8090/default
OIDC_CLIENT_ID=mila-copilot
APP_ORIGIN=http://127.0.0.1:4000
```

### 2. Index

```bash
./scripts/setup.sh
# or: docker compose up -d qdrant && (cd ingest && uv sync && uv run mila-ingest --recreate)
```

### 3. Agent Server

```bash
cd agent
uv sync --extra dev
uv run langgraph dev --no-browser --no-reload   # :2024, graph mila_agent
```

### 4. Copilot UI

```bash
# repo root
yarn install
yarn dev:copilot   # :4000
```

### 5. Optional auth

```bash
docker compose --profile auth up -d mock-oauth2-server
```

Browse **http://127.0.0.1:4000** (same host as `APP_ORIGIN`, not `localhost`, so cookies/thread storage align).

### Local “build” only

```bash
cd agent && uv sync --extra dev
yarn install && yarn build:copilot
```

Production-style Copilot image still uses `copilot/Dockerfile` (Next standalone).

---

## Hybrid (common)

| Want | Do |
| --- | --- |
| Only vector DB in Docker | `docker compose up -d qdrant` + local agent/UI |
| Full stack in Docker | Path A |
| Auth while developing locally | Compose profile `auth` + local agent/UI |

Agent must reach Qdrant at `QDRANT_URL` (`http://127.0.0.1:6333` locally; `http://qdrant:6333` inside Compose).

---

## Smoke checks

1. `curl -sf http://127.0.0.1:6333/readyz` → Qdrant up  
2. After ingest, Qdrant collection `mila_docs` has points (`collection_points` printed by `mila-ingest`)  
3. Open Copilot → ask a company-policy question as a signed-in employee  
4. Unauthenticated chat should hit the auth gate, not invent corpus facts  

Evals (optional): [`evals.md`](./evals.md) — needs LangSmith + Gemini + an ingested index (`--include-adversarial` for `mila-adversarial-v1`).

## Related

- [`scripts/setup.sh`](../scripts/setup.sh) — Qdrant up + ingest  
- [`agent/README.md`](../agent/README.md) · [`copilot/README.md`](../copilot/README.md) · [`ingest/README.md`](../ingest/README.md)  
- [OAuth + RBAC](./oauth-rbac.md) · [PII](./pii.md) · [Guardrails](./guardrails.md)
