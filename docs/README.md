# Mila Assistant — design docs

Design and implementation notes for the take-home prototype. Code lives under `agent/`, `copilot/`, `ingest/`, and `infra/`; this folder explains the decisions.

| Doc | Covers |
| --- | --- |
| [Architecture](./architecture.md) | System layout, request flow, frontend shell, thread restore |
| [OAuth + RBAC](./oauth-rbac.md) | Mock OIDC, session cookie, `auth_mode`, role → document filters |
| [PII handling](./pii.md) | Detect at ingest, store spans, anonymize before LLM by role |
| [Evaluation strategy](./evaluation-strategy.md) | Datasets, experiments, judges, CLI, vs unit/e2e |
| [Evals](./evals.md) | Short dataset + CLI cheat sheet |
| [Guardrails](./guardrails.md) | Injection / safety options (design); recommended MVP |

Assignment brief and corpus: [`../instructions/`](../instructions/).
