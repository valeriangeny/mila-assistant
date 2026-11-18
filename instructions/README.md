# Take-Home Challenge — Candidate Package

Welcome. This folder contains everything you need to complete the take-home.

## Read these first

1. `Take-Home Assignment.pdf` — the assignment brief (also available as `Take-Home Assignment.md`). Read this end-to-end before touching the data. It describes the prototype you are being asked to build, the four user roles, the behaviors that will be probed, the deliverables, and the evaluation criteria.
2. `data_dictionary.md` — the schema for every document, the meaning of each `sensitivity` and `intended_audience` value, the role definitions, and the PII categories. Refer back to this whenever the brief mentions "the dataset."

## Files in this folder

| File | What it is |
|---|---|
| `Take-Home Assignment.pdf` | The assignment brief. |
| `Take-Home Assignment.md` | Same brief in Markdown, for easier reading/search. |
| `data_dictionary.md` | Schema, sensitivity levels, audience values, roles, document types, and PII categories. |
| `documents.jsonl` | Main corpus, ~90 synthetic internal documents, one JSON object per line. |
| `adversarial_documents.jsonl` | A separate corpus, ~12 documents, intended for testing prompt-injection and role-elevation resilience. Same schema as the main corpus. IDs are prefixed `ADV-`. |
| `users.json` | Four sample user identities, one per role, for the simulated auth layer. |
| `pii_labels.jsonl` | Ground-truth PII labels per document. For your offline inspection and self-evaluation only — do not consume this at runtime. |

## Notes worth flagging up front

- The dataset is fully synthetic. Names, emails, phone numbers, addresses, salaries, identifiers, and incidents are fabricated.
- `intended_audience` is the document author's stated readership. It is not a role and not an access list. How you map audiences to your effective access policy, in combination with `sensitivity` and `department`, is part of what you are deciding.
- Treat the role in `users.json` as authoritative for the simulated auth layer. You do not need to implement real authentication.
- The adversarial corpus is provided in a separate file so you can choose when to ingest it and how to handle it. Whether you mix it into your main index, isolate it, or filter it during retrieval is a design choice you should be ready to defend.

## Submitting

Follow the deliverables section of the assignment brief. In short: a single archive containing your source code, a `Dockerfile` (and `docker-compose.yml` if needed) so we can run it from a clean clone, and a `README.md` covering the additional sections the brief lists.
