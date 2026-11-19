# mila-ingest

Load `instructions/*.jsonl` into **Qdrant** using **local FastEmbed** (`BAAI/bge-small-en-v1.5`, 384-d). No embedding API key.

## Setup

```bash
docker compose up -d qdrant

cd ingest
uv sync   # includes en-core-web-sm for Presidio NER
uv run mila-ingest --recreate
# optional adversarial corpus:
uv run mila-ingest --recreate --include-adversarial
```

First run downloads the FastEmbed ONNX model (spaCy `en_core_web_sm` comes from `uv sync`); later runs are offline.

PII: Presidio (+ regex) runs at ingest and writes `pii_spans` / `pii_categories` next to raw `text`. The agent anonymizes by role at retrieve — see [`docs/pii.md`](../docs/pii.md).

## Env

| Var | Default |
| --- | --- |
| `QDRANT_URL` | `http://127.0.0.1:6333` |
| `QDRANT_COLLECTION` | `mila_docs` |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` |
| `MILA_SKIP_PII` | unset — set `1` to skip detection |

Payload per point: `doc_id`, `title`, `department`, `doc_type`, `sensitivity`, `intended_audience`, `tags`, `author`, `created_at`, `chunk_index`, `text`, `pii_categories`, `pii_spans`.

## Chunking

Corpus bodies are already plain text (~0.4–3k chars). We split on paragraphs, then a small character window — no Unstructured/LangChain splitter dependency.
