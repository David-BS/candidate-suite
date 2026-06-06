> **⚠️ MODULE OF THE "candidate-suite" SUITE — PATH RELOCATION**
> This module lives in `modules/posting-brief-generator/`. All the relative paths below
> (`scripts/…`, `references/…`) are relative to THIS folder.
> From the suite root: prefix them with `modules/posting-brief-generator/`
> (e.g. `python modules/posting-brief-generator/scripts/<script>.py …`), or change into
> `modules/posting-brief-generator/` before running. The scripts' code is UNCHANGED:
> they receive all their paths as arguments, nothing is hard-coded.

---
name: posting-brief-generator
description: Generates a job-posting brief (dossier) in Markdown captured at application intake: header (company, position, recruiter, city, capture date, source, language), the verbatim posting body, and a short model-extracted digest (key requirements + deadline). Produced automatically when an application is opened; can be regenerated on explicit request.
---

# Posting brief generator

Generates a **posting brief** — the job-posting dossier captured at application
**intake**. It is an internal working document (not an outgoing deliverable):
it preserves the offer so the application keeps a single, durable reference.

## ⚠️ EXECUTION RULE (NON-NEGOTIABLE)

This module produces its deliverable ONLY via its Python scripts. Never write the final document "by hand" with `create_file`. Claude's role: PREPARE the content (JSON), then RUN the `generate_posting_brief.py` script, then offer/run `md_to_pdf.py`.

- ✅ Extract the content → build the JSON → run the script
- ❌ DO NOT `create_file` a hand-written .md
- ❌ DO NOT invent an output format different from the script's

## ⚠️ AUTOMATIC AT INTAKE — NOT A WIDGET CHOICE

Unlike the six standard deliverables, the posting brief is **not** a selection-widget
checkbox. The orchestrator (SKILL STEP 4) produces it **automatically, first**, as soon
as an application is opened from a job posting, reusing the offer already read in the
single global analysis. It is **idempotent**: skip it if a `Posting_Brief_<Company>_<Position>_*`
already exists in `/mnt/user-data/outputs/` for this application. Regenerate it only on an
**explicit** user request ("redo the posting brief", "capture this offer again").

## ⚠️ FUNDAMENTAL RULES

1. **Prerequisite**: a job posting (raw text or URL). No CV / config is required — the
   brief is about the *offer*, not the candidate.

2. **Output format = Markdown (.md)** in `/mnt/user-data/outputs/`. Offer the PDF export
   afterwards (it is also included in the orchestrator's end-of-run PDF batch, STEP 7).

3. **Filename is SCRIPT-OWNED**: pass `--output-dir /mnt/user-data/outputs` and let the
   script build `Posting_Brief_<Company>_<Position>_<YYYYMMDD>.md` and **print the path**.
   Read the printed path to present the file. Never hand-compose `--output-path`.

4. **Verbatim body**: `posting_body` is the offer text **copied as-is** (not summarized,
   not rephrased). The digest is *in addition*, never a replacement.

5. **Extraction = the model's job**, in any language, **no regex**. Header fields and the
   digest (key requirements, deadline) are read from the offer by you.

6. **Critical fields** (`company_name`, `job_title`, `posting_body`) must be real values:
   the script refuses (exit 2) an empty value or the neutral sentinel `__MISSING__` — ask
   the user, never invent.

## Overview

### Inputs
- **Job posting**: raw text OR URL (the orchestrator already has it from the global analysis)

### Outputs
- **`.md` file** in `/mnt/user-data/outputs/` (the brief)
- **`.pdf` file** optional (offered after the .md / batch in STEP 7)
- **Naming** (script-owned): `Posting_Brief_<Company>_<Position>_<YYYYMMDD>.md`

### Tracker
The brief's id is **`posting_brief`**. When the application is added to the tracker
(`add_to_tracker`), include `posting_brief` in the `deliverables` list.

## Structure labels (produced by the model — L6)

This generator does **not** hard-code per-language labels. **You** produce the section/field
labels **in the run language** (the working/conversation language) and pass them as
`--labels-json '{...}'` (alongside `--data-json` and `--language`). The script enforces the
**exact** key set below — a missing or extra key is rejected (anti-hallucination guardrail:
the structure is fixed, only the wording is yours).

**Required keys** (exact set, 13): `title`, `s_meta`, `l_company`, `l_position`,
`l_recruiter`, `l_city`, `l_captured`, `l_source`, `l_language`, `s_digest`,
`sub_requirements`, `sub_deadline`, `s_posting`

Each value is the label for that slot, **written by the model directly in the run language,
by intent** — there is **no per-language phrase table** (L6). Render each label from what it
*is* (e.g. `title` = names the document as a job-posting brief/dossier; `s_posting` = the full
job posting; `sub_deadline` = application deadline). **Never transliterate an English label.**
See `modules/cover-letter-generator/references/language_style_generic.md` for register / locale
conventions.

## Workflow

### STEP 1 — Get the posting
- **Raw text** → continue
- **URL** → `web_fetch`; if it fails → ask for a copy-paste

### STEP 2 — Extract (model, no regex)
From the offer, read out:
- **Header**: `company_name`, `job_title`, `recruiter_name` / `recruiter_title` (if any),
  `city` (if any), `source_url` (if any), `posting_language` (human-readable, e.g. "English").
- **Digest**: `requirements` (the key requirements, a short list), `deadline` (if stated).
- **Body**: `posting_body` = the offer text **verbatim**.

The capture date is **not** yours: the script stamps today's local date (resolve the IANA
timezone the same way as the tracker — candidate's city → session locale → fallback — and pass
`--timezone`).

### STEP 3 — Generate the .md

Build the JSON and run:
```bash
python scripts/generate_posting_brief.py \
  --language <code> \
  --output-dir /mnt/user-data/outputs \
  --data-json '<full_json>' \
  --labels-json '<labels_json — exact key set, values localized in the run language>' \
  --timezone <IANA, e.g. Europe/Paris>
```

**Read the printed path** and present the `.md` with `present_files`.

### STEP 4 — Offer the PDF export

**After presenting the .md, offer**:
```
The posting brief is ready in Markdown. Would you also like a PDF version?
```
If yes (or as part of the orchestrator's end-of-run PDF batch), run:
```bash
python scripts/md_to_pdf.py \
  --input /mnt/user-data/outputs/<filename>.md \
  --output /mnt/user-data/outputs/<filename>.pdf \
  --title "<deliverable title>"
```
Present the `.pdf` with `present_files`.

## Supported user commands

- *(automatic)*: produced first by the orchestrator at intake (SKILL STEP 4)
- `"Redo the posting brief"` / `"Capture this offer again"`: regenerate
- `"Export the brief to PDF"`: convert an existing .md

## Available scripts

| Script | Usage |
|--------|-------|
| `generate_posting_brief.py --language X --output-dir DIR --data-json '...' --labels-json '...' [--timezone TZ]` | Generates the .md (script-owned filename) |
| `md_to_pdf.py --input X.md --output X.pdf [--title "..."]` | Converts .md → styled PDF |

## References

- `references/posting_brief_structure.md`: detailed structure of the brief

## Important rules

- **AUTOMATIC at intake**, first; **idempotent** (skip if already present); regenerate only on explicit request
- **.md format** in `/mnt/user-data/outputs/`; offer the PDF after
- **Filename is script-owned** (`--output-dir`, read the printed path)
- **Body verbatim**; the digest is additive
- **Extraction by the model**, any language, **no regex**
- **Critical fields** empty / `__MISSING__` → exit 2: ask, never invent
