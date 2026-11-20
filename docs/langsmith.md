# LangSmith — evals, tracing, and monitoring

How Mila uses the LangSmith UI for offline evaluation and live observability. CLI sync/run details: [evals.md](./evals.md). Strategy: [evaluation-strategy.md](./evaluation-strategy.md).

Workspace: cloud LangSmith (**Datasets & Experiments**, **Tracing**, **Monitoring**). Tracing project for local Agent Server chat: `Mila Agent - local:2024` (see `LANGSMITH_PROJECT` in `agent/config/.env*`).

## Evals — datasets

Filter **Datasets & Experiments** for `mila-*`. Each row is a golden set synced from `agent/evals/datasets/<name>/examples.json`.

| Dataset | Typical use |
| --- | --- |
| `mila-smoke-v1` | Auth gate + basic retrieve |
| `mila-roles-v1` | RBAC allow / reject |
| `mila-pii-v1` | Mask / allow / refuse |
| `mila-safety-v1` | User-message abuse |
| `mila-adversarial-v1` | Retrieved-doc injection |

![LangSmith datasets list filtered to mila](./screenshots/langsmith/01-datasets-list.png)

## Evals — experiments on a dataset

Open a dataset → **Experiments**. Charts summarize feedback averages, latency, and tokens across runs. Example: `mila-roles-v1` after `run_eval.py --name mila-roles-v1 --sync`.

![mila-roles-v1 experiments overview](./screenshots/langsmith/02-dataset-experiments.png)

## Evals — compare view

Open an experiment (or **Compare**) to see per-example inputs, reference outputs, model outputs, and judge scores (green = 1.0, red = 0.0). Example: `mila-adversarial-retry-d4d0109f` on `mila-adversarial-v1`.

![Adversarial experiment compare table](./screenshots/langsmith/03-experiment-compare.png)

## Evals — drill into a run (trace + feedback)

Select a row to open the run: left **Trace** (hooks, agent, Gemini calls), right **Feedback** (deterministic + LLM judges such as `rbac_dataset_docs`, `intent_satisfied`).

![Experiment row with Trace and Feedback panels](./screenshots/langsmith/04-experiment-trace-feedback.png)

## Observability — monitoring live traces

Chat against the Agent Server with `LANGSMITH_TRACING=true` lands in the tracing project. **Monitoring** aggregates trace count, latency (P50/P99), and error rate over time (separate from offline experiments).

![Monitoring dashboard for Mila Agent local project](./screenshots/langsmith/05-monitoring.png)

Studio (`…/studio/?baseUrl=http://127.0.0.1:2024`) is for interactive graph debugging; it is not a substitute for experiment compare or monitoring charts.

## Related

- [Datasets and experimentations (evals)](./evals.md)
- [Evaluation strategy](./evaluation-strategy.md)
- [Install, build, and run](./install-and-run.md)
- [Screenshots](./screenshots.md) (Copilot UI flow)
