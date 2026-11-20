"""CLI: load JSONL corpus → chunk → embed → Qdrant."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import dotenv_values

from mila_ingest.chunk import docs_to_chunks
from mila_ingest.embed import embed_texts
from mila_ingest.pii_detect import annotate_chunks, pii_detection_enabled
from mila_ingest.store import connect, get_collection, get_qdrant_url, upsert_chunks


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_env() -> None:
    """Load file env without clobbering process exports (Compose sets QDRANT_URL)."""
    root = _repo_root()
    preset = set(os.environ)
    merged: dict[str, str] = {}
    for path in (
        root / ".env",
        root / "agent" / "config" / ".env.local",
        root / "ingest" / ".env",
    ):
        if not path.is_file():
            continue
        for key, value in dotenv_values(path).items():
            if value is not None:
                merged[key] = value
    for key, value in merged.items():
        if key not in preset:
            os.environ[key] = value


def _load_jsonl(path: Path) -> list[dict]:
    docs: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            docs.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return docs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ingest aliM corpus into Qdrant")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="Directory with documents.jsonl (default: <repo>/instructions)",
    )
    parser.add_argument(
        "--include-adversarial",
        action="store_true",
        help="Also ingest adversarial_documents.jsonl",
    )
    parser.add_argument("--recreate", action="store_true", help="Drop collection before upsert")
    args = parser.parse_args(argv)

    _load_env()
    corpus_dir = args.corpus or (_repo_root() / "instructions")
    main_path = corpus_dir / "documents.jsonl"
    if not main_path.is_file():
        raise SystemExit(f"Missing corpus file: {main_path}")

    docs = _load_jsonl(main_path)
    if args.include_adversarial:
        adv = corpus_dir / "adversarial_documents.jsonl"
        if adv.is_file():
            docs.extend(_load_jsonl(adv))
        else:
            print(f"warn> adversarial file not found: {adv}", file=sys.stderr)

    chunks = docs_to_chunks(docs)
    print(
        f"ingest> docs={len(docs)} chunks={len(chunks)} "
        f"qdrant={get_qdrant_url()} collection={get_collection()}",
        flush=True,
    )
    if not chunks:
        raise SystemExit("No chunks produced")

    if pii_detection_enabled():
        print("ingest> detecting PII…", flush=True)
        chunks = annotate_chunks(chunks)
        tagged = sum(1 for c in chunks if c.get("pii_spans"))
        print(f"ingest> pii_chunks_with_spans={tagged}/{len(chunks)}", flush=True)
    else:
        print("ingest> PII detection skipped (MILA_SKIP_PII)", flush=True)

    client = connect()
    collection = get_collection()
    if args.recreate:
        try:
            client.delete_collection(collection)
            print(f"ingest> deleted collection {collection}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"ingest> delete skipped: {exc}", flush=True)

    print("ingest> embedding…", flush=True)
    vectors = embed_texts([c["text"] for c in chunks])
    print("ingest> upserting…", flush=True)
    n = upsert_chunks(client, chunks, vectors, collection=collection)
    info = client.get_collection(collection)
    print(
        f"ingest> done points={n} collection_points={info.points_count}",
        flush=True,
    )


if __name__ == "__main__":
    main()
