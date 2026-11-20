# Mila Assistant — design docs

Design and implementation notes for the take-home prototype. Code lives under `agent/`, `copilot/`, `ingest/`, and `infra/`; this folder explains the decisions.

| Doc | Covers |
| --- | --- |
| [Install, build, and run](./install-and-run.md) | Prerequisites; local (recommended) vs Docker Compose |
| [Architecture](./architecture.md) | System layout, request flow, frontend shell, thread restore |
| [OAuth + RBAC](./oauth-rbac.md) | Mock OIDC, session cookie, `auth_mode`, role → document filters |
| [PII handling](./pii.md) | Detect at ingest, store spans, anonymize before LLM by role |
| [Evaluation strategy](./evaluation-strategy.md) | Datasets, experiments, judges, CLI, vs unit/e2e |
| [Datasets and experimentations (evals)](./evals.md) | Dataset names, example shape, sync/run CLI cheat sheet |
| [Guardrails](./guardrails.md) | Composable rails + hooks diagram |

## Screenshots

| Doc | Covers |
| --- | --- |
| [Screenshots](./screenshots.md) | Copilot UI: start → in-chat sign-in → OAuth → ask → RBAC reject |
| [LangSmith UI](./langsmith.md) | Evals + observability (datasets, experiments, traces, monitoring) |

Assignment brief and corpus: [`../instructions/`](../instructions/).
