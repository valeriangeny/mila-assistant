# LangSmith eval datasets

Offline experiments for the Mila agent (same harness pattern as the todo-app evals). No dedicated HTTP/auth endpoint — `evals/run_eval.py` calls the graph in-process and injects a mock caller.

## Datasets

| Name | Purpose | Needs Qdrant? |
| --- | --- | --- |
| `mila-smoke-v1` | Auth gate + basic retrieve (unauth / incognito / employee) | Yes (except pure unauth) |
| `mila-roles-v1` | Logged-in RBAC allow vs reject | Yes |
| `mila-pii-v1` | Mask / allow contact by role; public cannot see internal roster | Yes |
| `mila-safety-v1` | Out-of-guideline: code exec, prompt injection, hate, violence | No |
| `mila-adversarial-v1` | **Future** — corpus injection after `mila-ingest --include-adversarial` | Yes + ADV docs |

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
| `inputs.messages` | User turn (Studio-compatible) |
| `inputs.caller` | Mock `AgentContext` — **required for eval persona** (LangSmith `target` only sees inputs) |
| `outputs.reference` / `trajectory` | Judges + static trajectory check |
| `metadata.expect` | `positive` \| `negative` polarity for LLM judges |
| `metadata.slice` | Filter in LangSmith UI (`auth_gate`, `allow`, `mask`, …) |

Personas align with `instructions/users.json`. Sync also copies `caller` fields into metadata for filtering if you only authored one side.

`prompt_sign_in` is a CopilotKit frontend tool — not registered on the eval graph. Smoke unauth cases expect `retrieve_knowledge` → `auth_required`, then a refusal to invent knowledge (not a frontend tool call).

## Deterministic Mila evaluators

| Key | Source of truth |
| --- | --- |
| `rbac_hits_allowed` | `access_policy.document_allowed` on every retrieve hit (algo) |
| `rbac_dataset_docs` | Dataset metadata: `forbidden_doc_ids`, `required_doc_ids`, `answer_must_not_contain` |
| `pii_masked_not_in_answer` | Retrieve **audit** originals (mask/redact) + optional `must_not_contain` ∉ answer |
| `pii_allowed_present_in_answer` | `must_contain` ⊆ answer (e.g. HR email) |

`target()` attaches `outputs.retrieve` from a side-channel (`retrieve_audit`), not from the LLM-visible tool JSON — originals must not be re-injected into the model.

## Run

```bash
# Index first (roles / pii / smoke happy-path)
cd ingest && uv run mila-ingest --recreate

cd ../agent
uv run python evals/sync_dataset.py --name mila-smoke-v1 --push --yes
uv run python evals/run_eval.py --name mila-smoke-v1 --sync

# Other suites
uv run python evals/run_eval.py --name mila-roles-v1 --sync
uv run python evals/run_eval.py --name mila-pii-v1 --sync
uv run python evals/run_eval.py --name mila-safety-v1 --sync
```

Requires `LANGSMITH_API_KEY` and Gemini (`GOOGLE_API_KEY` or Vertex ADC) in `agent/config/.env*`.

Pytest: `MILA_EVAL_DATASET=mila-smoke-v1 uv run pytest -m langsmith`.

## Adversarial (later)

Keep `mila-adversarial-v1` empty until ADV docs are ingested. Cases should ask questions that retrieve poisoned bodies and assert the agent does **not** elevate role / dump PII / follow “CEO override” instructions. Separate from `mila-safety-v1` (user-message abuse vs retrieved-doc abuse).

## Related

- [OAuth + RBAC](./oauth-rbac.md)
- [PII](./pii.md)
- [Architecture](./architecture.md)
