# Datasets and experimentations (evals)

Quick reference for dataset names, example shape, and CLI. Full strategy: **[evaluation-strategy.md](./evaluation-strategy.md)**.

Offline experiments for the Mila agent. No dedicated HTTP/auth endpoint — `evals/run_eval.py` calls the graph in-process and injects a mock caller.

## Datasets

| Name | Purpose | Needs Qdrant? |
| --- | --- | --- |
| `mila-smoke-v1` | Auth gate + basic retrieve (unauth / incognito / employee) | Yes (except pure unauth) |
| `mila-roles-v1` | Logged-in RBAC allow vs reject | Yes |
| `mila-pii-v1` | Mask / allow contact by role; public cannot see internal roster | Yes |
| `mila-safety-v1` | Out-of-guideline: code exec, prompt injection, hate, violence | No |
| `mila-adversarial-v1` | Corpus injection / authority spoof (ADV-* docs) | Yes + `--include-adversarial` |

Local goldens: `agent/evals/datasets/<name>/examples.json`.

## Example shape

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
    "auth_mode": "authenticated",
    "role": "hr"
  }
}
```

| Field | Role |
| --- | --- |
| `inputs.messages` | User turn (Studio-compatible `messages` schema) |
| `inputs.caller` | Mock `AgentContext` — required for eval persona (`target` only sees inputs) |
| `outputs.reference` / `trajectory` | Judges + static trajectory check |
| `metadata.expect` | `positive` \| `negative` polarity for LLM judges |
| `metadata.slice` | Filter in LangSmith UI (`auth_gate`, `allow`, `mask`, …) |

Personas align with `instructions/users.json`. Sync copies `caller` fields into metadata when needed.

`prompt_sign_in` is a CopilotKit frontend tool — not on the eval graph. Smoke unauth expects `retrieve_knowledge` → `auth_required`, then a refusal to invent knowledge.

## Deterministic Mila evaluators

| Key | Source of truth |
| --- | --- |
| `rbac_hits_allowed` | `access_policy.document_allowed` on every retrieve hit |
| `rbac_dataset_docs` | `forbidden_doc_ids`, `required_doc_ids`, `answer_must_not_contain` |
| `pii_masked_not_in_answer` | Retrieve audit originals (mask/redact) + `must_not_contain` ∉ answer |
| `pii_allowed_present_in_answer` | `must_contain` ⊆ answer |

`target()` attaches `outputs.retrieve` from `retrieve_audit` (not LLM-visible tool JSON).

## Run

```bash
cd ingest && uv run mila-ingest --recreate

cd ../agent
uv run python evals/sync_dataset.py --name mila-smoke-v1 --push --yes
uv run python evals/run_eval.py --name mila-smoke-v1 --sync

uv run python evals/run_eval.py --name mila-roles-v1 --sync
uv run python evals/run_eval.py --name mila-pii-v1 --sync
uv run python evals/run_eval.py --name mila-safety-v1 --sync

# after ADV ingest:
cd ../ingest && uv run mila-ingest --recreate --include-adversarial
cd ../agent && uv run python evals/run_eval.py --name mila-adversarial-v1 --sync
```

Requires `LANGSMITH_API_KEY` and Gemini in `agent/config/.env*`.

Pytest: `MILA_EVAL_DATASET=mila-smoke-v1 uv run pytest -m langsmith`.

## Adversarial

`mila-adversarial-v1` probes **retrieved-doc** abuse (role elevation, SYSTEM fences, fake CISO/FAQ overrides, PII-append notes). Separate from `mila-safety-v1` (user-message abuse). Requires Qdrant rebuilt with `--include-adversarial`.

## Related

- [LangSmith UI](./langsmith.md) (platform screenshots)
- [Evaluation strategy](./evaluation-strategy.md)
- [Guardrails](./guardrails.md)
- [OAuth + RBAC](./oauth-rbac.md)
- [PII](./pii.md)
- [Architecture](./architecture.md)
