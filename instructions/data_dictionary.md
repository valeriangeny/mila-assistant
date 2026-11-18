# Data Dictionary

This dataset contains synthetic internal documents for a hypothetical AI research lab, **aliM AI Institute**. All names, emails, addresses, phone numbers, salaries, identifiers, and incidents are fabricated. No real personal data is present.

## Files

- `documents.jsonl` — one document per line, JSON-encoded. This is the main corpus (~90 documents).
- `adversarial_documents.jsonl` — a separate corpus (~12 documents) intended for testing resilience to indirect prompt injection, role-elevation, contradictory/superseded content, and similar adversarial material. The main corpus does not contain adversarial documents.
- `users.json` — sample user identities for the simulated auth layer.
- `pii_labels.jsonl` — ground-truth PII labels keyed by `id`. Provided as a convenience for inspection and evaluation; not intended to drive runtime detection.
- `data_dictionary.md` — this file.

## Document schema

Each line in `documents.jsonl` (and `adversarial_documents.jsonl`) is a JSON object with the following fields:

| Field | Type | Description |
|---|---|---|
| `id` | string | Stable document identifier (e.g., `DOC-0042`, `ADV-0001`). |
| `title` | string | Human-readable title. |
| `department` | string | Owning team. One of `general`, `hr`, `engineering`, `security`. |
| `doc_type` | string | Document category (see below). |
| `sensitivity` | string | One of `public`, `internal`, `confidential`, `restricted`. |
| `intended_audience` | string | The author's intended readership (see below). |
| `tags` | string[] | Free-form tags. |
| `author` | string | Document author. |
| `created_at` | string | ISO-8601 date. |
| `body` | string | Document content as plain text or lightly-formatted markdown. |

## Sensitivity levels

| Level | Intent |
|---|---|
| `public` | Safe to share company-wide. May still contain incidental personal data that requires handling. |
| `internal` | All employees, but not external parties. |
| `confidential` | Limited to a specific audience (e.g., HR comp data, security incident details). |
| `restricted` | Tightly scoped (e.g., active investigations, executive-only material). |

Sensitivity is a signal, not a permission. How `sensitivity` interacts with `intended_audience` to form the effective access policy for each role is a design decision the candidate makes.

## Intended audience

`intended_audience` reflects who the author wrote the document for. It does not directly encode roles — the mapping from audience to your role model is part of what you are deciding.

Values appearing in this dataset:

| Value | Meaning |
|---|---|
| `company-wide` | Intended for any employee. |
| `people-ops` | Intended for the People Operations / HR team. |
| `engineering` | Intended for the engineering org. |
| `security` | Intended for the security team. |
| `engineering-and-security` | Shared between engineering and security. |
| `people-ops-and-security` | Shared between People Operations and security. |
| `function-leads` | Intended for leadership across functions (HR, engineering, security), excluding baseline employees. |

## Roles (in `users.json`)

| Role | Description |
|---|---|
| `employee` | Baseline role for all staff. |
| `hr` | People Operations. |
| `engineering` | Engineering staff. |
| `security` | Security and trust team. |

A user may hold more than one role in principle. The provided sample users each hold exactly one. Your system decides how roles compose to grant or deny access.

## Document types (`doc_type`)

Non-exhaustive list of values appearing in this dataset:

- General: `policy`, `handbook`, `all_hands_notes`, `faq`, `announcement`, `team_page`, `org_chart`, `onboarding`, `benefits`.
- HR: `offer_letter`, `compensation_memo`, `performance_review`, `pip`, `termination_letter`, `employee_profile`.
- Engineering: `rfc`, `runbook`, `architecture`, `postmortem`, `oncall_rotation`, `style_guide`, `api_spec`.
- Security: `incident_report`, `pentest_finding`, `access_review`, `vulnerability_disclosure`, `threat_model`, `vendor_review`, `audit_log_excerpt`, `legal_memo`.

## PII labels (`pii_labels.jsonl`)

Ground-truth labels of personal information present in each document body. Each line is:

```json
{"id": "DOC-0042", "pii": ["name", "contact", "financial"]}
```

Only documents with at least one PII category appear in the file. Categories:

| Category | Covers |
|---|---|
| `name` | Full names of individuals. |
| `contact` | Email addresses, phone numbers, residential addresses. |
| `identifier` | Government-issued identifiers (SSN-like, SIN-like), dates of birth. |
| `financial` | Compensation, payroll, banking. |
| `sensitive_narrative` | Free-form sensitive text including medical notes and performance evaluations. |

These labels are provided so you can inspect the corpus and grade your detection logic offline. Your system should detect PII independently; do not consume `pii_labels.jsonl` at runtime.

## Adversarial content

`adversarial_documents.jsonl` is a separate corpus designed to test resilience to indirect prompt injection, role-elevation attempts, contradictory or superseded content, authority spoofing, and similar adversarial material. It uses the same schema as `documents.jsonl` but its IDs are prefixed `ADV-` rather than `DOC-`. Treat it as part of the corpus during ingestion if you intend to demonstrate adversarial resilience.

## Hardcoded users

`users.json` contains four sample identities, one per role. Treat the role as authoritative for the simulated auth layer.
