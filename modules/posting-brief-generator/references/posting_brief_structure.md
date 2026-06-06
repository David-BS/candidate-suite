# Structure of the posting brief

The posting brief is the job-posting dossier captured at application **intake**.
It is an internal working document: it preserves the offer (so the application
keeps one durable reference) and adds a short, model-extracted digest.

Three sections, in this fixed order.

## Section 1 — Header ("at a glance")

A compact key/value list. Field labels come from `--labels-json`; values come
from `--data-json`, except the **capture date**, which the script stamps itself.

| Slot | Label key | Value source | Notes |
|------|-----------|--------------|-------|
| Company | `l_company` | `company_name` | **critical** (empty / `__MISSING__` → exit 2) |
| Position | `l_position` | `job_title` | **critical** |
| Recruiter | `l_recruiter` | `recruiter_name` (+ `recruiter_title`) | optional → `—` if absent |
| City | `l_city` | `city` | optional → `—` |
| Captured | `l_captured` | *script* (today, local date, `YYYY-MM-DD`) | never model-supplied |
| Source | `l_source` | `source_url` | optional → `—` |
| Language | `l_language` | `posting_language` | human-readable, e.g. "English" |

The header section title is `s_meta`.

## Section 2 — Digest (model-extracted)

Section title `s_digest`, with two sub-sections:

- **Key requirements** (`sub_requirements`): `requirements`, a short list of the
  offer's must-haves (a handful of bullets, the model's reading of the posting —
  not a copy of every line). Distinctive and concrete, not generic.
- **Deadline** (`sub_deadline`): `deadline` if the offer states one, else `—`.

The digest is **additive**: it never replaces the verbatim body below.

## Section 3 — Posting (verbatim)

Section title `s_posting`. The value is `posting_body`: the offer text **copied
as-is** — not summarized, not rephrased, not truncated. This is the archival
purpose of the brief. If the offer came from a URL, this is the fetched text.

`posting_body` is **critical** (empty / `__MISSING__` → exit 2): without the
offer there is nothing to capture.

## Example header (EN)

```
## At a glance
- **Company:** Acme Financial Group
- **Position:** Head of Engineering
- **Recruiter:** Jane Smith, Head of Talent
- **City:** Paris
- **Captured:** 2026-06-06
- **Source:** https://careers.example.com/head-of-engineering
- **Language:** English
```

## Example digest (EN)

```
## Digest
### Key requirements
- 10+ years leading engineering organizations at scale
- Proven payments / fintech platform modernization
- Fluent French and English

### Application deadline
30 June 2026
```
