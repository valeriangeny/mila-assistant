# Evaluation, datasets, and experiments

Offline LangSmith evaluation for the Mila agent: metrics, golden shape, experiment flow, and how that differs from unit tests and live chat.

Pipeline: local `examples.json` → `sync_dataset` → `client.evaluate(target)` → static + LLM + deterministic judges. Covers **verified caller role**, **RBAC**, and **PII**.

## Goals

| Goal | Coverage |
| --- | --- |
| Auth gates | `mila-smoke-v1` (unauth / incognito / employee) |
| Doc RBAC allow & reject | `mila-roles-v1` + deterministic doc/policy checks |
| PII mask / allow / no leak | `mila-pii-v1` + retrieve-audit originals |
| User-message abuse | `mila-safety-v1` (negative polarity) |
| Indirect injection (corpus) | `mila-adversarial-v1` (after ADV ingest) |

Out of scope here: browser OIDC e2e (Playwright), Presidio precision vs `pii_labels.jsonl` ([pii.md](./pii.md)), online evaluators on every production trace.

## Pipeline

```text
agent/evals/datasets/<name>/examples.json   # git source of truth
        │
        ▼  sync_dataset.py --push
LangSmith dataset (same name, workspace-scoped)
        │
        ▼  run_eval.py [--sync]
target(inputs) → run_agent(..., context=caller)
        │
        ▼
experiment project (e.g. mila-smoke-…)
        + evaluators → scores on each example
```

| Piece | Path |
| --- | --- |
| Sync CLI | `agent/evals/sync_dataset.py` |
| Experiment CLI | `agent/evals/run_eval.py` |
| I/O + schemas | `agent/evals/dataset_io.py` |
| Judges | `agent/evals/evaluators.py` |
| Pytest marker | `tests/test_eval_langsmith.py` (`-m langsmith`) |

Local JSON is canonical; use `sync_dataset.py` for full replace. Inspect experiments in the LangSmith UI (or MCP) after a run.

No dedicated eval HTTP/auth endpoint. `target` invokes the graph in-process and injects `AgentContext` from `inputs.caller` (`instructions/users.json` personas — not the mock IdP).

## Datasets

One LangSmith dataset per concern.

| Name | Purpose | Qdrant? |
| --- | --- | --- |
| `mila-smoke-v1` | Auth gate + basic retrieve | Yes (except pure unauth) |
| `mila-roles-v1` | Logged-in RBAC allow vs reject | Yes |
| `mila-pii-v1` | Contact mask vs HR allow; public blocked | Yes |
| `mila-safety-v1` | Code exec, jailbreak, hate, violence | No |
| `mila-adversarial-v1` | Retrieved-doc injection / authority spoof | Yes + `--include-adversarial` |

Local paths: `agent/evals/datasets/<name>/examples.json`.  
Catalog: `DATASET_CATALOG` in `dataset_io.py`. Default CLI name: `mila-smoke-v1`.

Datasets are workspace-scoped (not bound to a Studio agent). Experiments attach to a dataset via `evaluate`. Live tracing uses `LANGSMITH_PROJECT` separately.

### Example shape

```json
{
  "id": "roles-hr-allows-perf-review",
  "inputs": {
    "messages": [{ "role": "human", "content": "…" }],
    "caller": {
      "auth_mode": "authenticated",
      "role": "hr",
      "mila_user_id": "u_priya",
      "mila_user_name": "Priya Shah"
    }
  },
  "outputs": {
    "reference": "What a good answer looks like…",
    "trajectory": [{ "tool": "retrieve_knowledge" }]
  },
  "metadata": {
    "slice": "allow",
    "expect": "positive",
    "role": "hr",
    "required_doc_ids": ["DOC-0034"],
    "forbidden_doc_ids": [],
    "must_contain": [],
    "must_not_contain": [],
    "answer_must_not_contain": []
  }
}
```

| Field | Role |
| --- | --- |
| `inputs.messages` | User turn (Studio-compatible `messages` schema) |
| `inputs.caller` | Mock `AgentContext` — LangSmith `target` only receives **inputs** |
| `outputs.reference` | Intent for LLM judges |
| `outputs.trajectory` | Expected tool subsequence |
| `metadata.expect` | `positive` \| `negative` polarity |
| `metadata.slice` | UI filter (`auth_gate`, `allow`, `mask`, …) |
| `metadata.*_doc_ids` / `must_*` | Deterministic RBAC/PII expectations |

Sync promotes `caller` ↔ metadata when only one side is authored.

`prompt_sign_in` is a CopilotKit frontend tool — not on the eval graph. Unauth smoke expects `retrieve_knowledge` → `auth_required`, then a refusal to invent knowledge.

## Experiments

One `client.evaluate` run against a named dataset:

1. Optional `--sync` pushes local goldens.
2. For each example, `target(inputs)` returns:

   ```python
   {
     "answer": str,
     "trajectory": [{"tool", "args"}, ...],
     "retrieve": { ... }  # side-channel audit
   }
   ```

3. Each evaluator returns `{key, score, comment?}` (0.0 / 0.5 / 1.0).
4. Results appear as a LangSmith experiment (prefix ≈ dataset name). There is no separate local HTML report — the experiment page is the report.

Infra: `LANGSMITH_API_KEY`, Gemini (`GOOGLE_API_KEY` or Vertex ADC), and for RAG suites a populated Qdrant (`mila-ingest --recreate`).

## Evaluators

Wired in `DEFAULT_EVALUATORS` (`run_eval.py`).

### Generic (static + LLM)

| Key | Type | Checks |
| --- | --- | --- |
| `answer_min_chars` | Static | Answer length ≥ `EVAL_MIN_ANSWER_CHARS` (default 20) |
| `trajectory_subsequence` | Static | Expected tools in order; optional arg match; empty expected ⇒ no tools |
| `trajectory_llm_judge` | LLM | Tools match task / reference |
| `intent_satisfied` | LLM | Polarity-aware whole-behavior |
| `final_response_judge` | LLM | Final text vs reference |

### Mila deterministic

| Key | Source of truth |
| --- | --- |
| `rbac_hits_allowed` | `access_policy.document_allowed` on every retrieve hit |
| `rbac_dataset_docs` | `forbidden_doc_ids` / `required_doc_ids` / `answer_must_not_contain` |
| `pii_masked_not_in_answer` | Audit mask/redact **originals** (+ `must_not_contain`) ∉ answer |
| `pii_allowed_present_in_answer` | `must_contain` ⊆ answer |

**Retrieve audit:** tool JSON stays LLM-safe (masked text only). `search_knowledge` records originals + ACL on a contextvar (`retrieve_audit`); `target` copies that into `outputs.retrieve`.

Algo RBAC only validates returned hits (empty hits skip-pass). Dataset `forbidden_doc_ids` / phrase bans catch leaks and invention without retrieval.

## Layers vs unit tests

| Layer | What |
| --- | --- |
| Unit | `test_access_policy`, `test_pii_policy`, `test_retrieve_auth`, `test_mila_evaluators`, `test_guardrails` |
| Offline detector | Presidio vs `pii_labels.jsonl` (not agent LangSmith) |
| LangSmith experiment | Full agent + judges + optional Qdrant |
| Browser e2e | OIDC / in-chat auth (`e2e/`) |

## CLI

```bash
cd ingest && uv run mila-ingest --recreate   # RAG suites

cd ../agent
uv run python evals/sync_dataset.py --name mila-smoke-v1 --push --yes
uv run python evals/run_eval.py --name mila-smoke-v1 --sync

uv run python evals/run_eval.py --name mila-roles-v1 --sync
uv run python evals/run_eval.py --name mila-pii-v1 --sync
uv run python evals/run_eval.py --name mila-safety-v1 --sync

cd ../ingest && uv run mila-ingest --recreate --include-adversarial
cd ../agent && uv run python evals/run_eval.py --name mila-adversarial-v1 --sync

MILA_EVAL_DATASET=mila-smoke-v1 uv run pytest -m langsmith
```

Env: `LANGSMITH_API_KEY`, Gemini, `QDRANT_URL` as needed — `agent/config/.env.local`.

## Future

- Optional per-dataset evaluator lists.
- Dedicated LangSmith workspace for Mila (optional hygiene).

## Related

- [LangSmith UI](./langsmith.md) (evals + monitoring screenshots)
- [Datasets and experimentations (evals)](./evals.md)
- [Guardrails](./guardrails.md)
- [PII](./pii.md)
- [OAuth + RBAC](./oauth-rbac.md)
- [Architecture](./architecture.md)
- [`agent/README.md`](../agent/README.md) § Evals
