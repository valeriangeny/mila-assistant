# mila-ingest

Load `instructions/*.jsonl` into **Qdrant** using **local FastEmbed** (`BAAI/bge-small-en-v1.5`, 384-d). No embedding API key.

## Setup

```bash
docker compose up -d qdrant

cd ingest
uv sync
uv run mila-ingest --recreate
# optional adversarial corpus:
uv run mila-ingest --recreate --include-adversarial
```

First run downloads the ONNX model into a local cache; later runs are offline.

## Env

| Var | Default |
| --- | --- |
| `QDRANT_URL` | `http://127.0.0.1:6333` |
| `QDRANT_COLLECTION` | `mila_docs` |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` |

Payload per point: `doc_id`, `title`, `department`, `doc_type`, `sensitivity`, `intended_audience`, `tags`, `author`, `created_at`, `chunk_index`, `text`, `pii_categories` (empty until Phase 3).

## Chunking

Corpus bodies are already plain text (~0.4–3k chars). We split on paragraphs, then a small character window — no Unstructured/LangChain splitter dependency.
