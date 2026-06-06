> **⚠️ MODULE OF THE "candidate-suite" SUITE — PATH RELOCATION**
> This module lives in `modules/interview-prep-generator/`. All the relative paths below
> (`scripts/…`, `assets/…`, `references/…`) are relative to THIS folder.
> From the suite root: prefix them with `modules/interview-prep-generator/`
> (e.g. `python modules/interview-prep-generator/scripts/<script>.py …`), or change into
> `modules/interview-prep-generator/` before running. The scripts' code is UNCHANGED:
> they receive all their paths as arguments, nothing is hard-coded.

---
name: interview-prep-generator
description: Generates interview-preparation help (Markdown, optional PDF export) with Q&A for 2 interviews (motivation screening + skills validation). Use for "prepare my interviews", "likely questions for this role".
---

# Interview prep generator

Generates an interview-preparation **Markdown** document (2 sets of Q&A), with optional styled PDF export for forwarding and third-party use.

## ⚠️ EXECUTION RULE (NON-NEGOTIABLE)

This module produces its deliverable ONLY via its Python scripts. Never write the final document "by hand" with `create_file`. Claude's role: PREPARE the content (JSON), then RUN the `generate_interview_prep.py` script, then offer/run `md_to_pdf.py`.

- ✅ Generate the content → build the JSON → run the script
- ❌ DO NOT `create_file` a hand-written .md/.docx
- ❌ DO NOT invent an output format different from the script's

## ⚠️ VAGUE REQUEST → FOLLOW THE WORKFLOW

If the request is open-ended ("help me apply," "prepare my interviews"), don't improvise ad-hoc documents. Identify the candidate-suite sub-modules involved, announce the deliverables, run each workflow via its scripts. Produce only the planned deliverables; offer (without generating by default) any additional document.

## ⚠️ FUNDAMENTAL RULES

1. **Prerequisite**: The `candidate-config` module must be configured. Check via `memory_user_edits view`.

2. **Output format = Markdown (.md)** by default. `.docx` is NO LONGER used (cross-machine portability issues). After generating the `.md`, **always offer the PDF export**.

3. **To generate the .md**: use the `scripts/generate_interview_prep.py` script.

4. **For the PDF export**: use the `scripts/md_to_pdf.py` script (Markdown → styled HTML → PDF via wkhtmltopdf chain).

5. **2 distinct interviews**:
   - **Interview 1: Screening (motivation)** — candidate's "why," motivation, cultural fit
   - **Interview 2: Skills validation** — technical/domain skills, fit against the requirements

## Overview

### Inputs
- **Job posting**: raw text OR URL
- **Optional**: context on the recruitment process

### Outputs
- **`.md` file** in `/mnt/user-data/outputs/` (main deliverable)
- **`.pdf` file** optional (offered after the .md)
- **Naming**: `Interview_Prep_<Name>_<Company>_<Language>.md` (then `.pdf`). In `<Name>` and `<Company>`, replace spaces with hyphens (`-`); never run words together. E.g. `Interview_Prep_Jordan-Lee-Carter_Acme-Financial-Group_EN.md`.

## Workflow — 6 steps

## Structure labels (produced by the model — L6)

This generator does **not** hard-code per-language labels. **You** produce the section labels **in the run language** and pass them as `--labels-json '{...}'` (alongside `--data-json` and `--language`). The script enforces the **exact** key set below — a missing or extra key is rejected (anti-hallucination guardrail: the structure is fixed, only the wording is yours).

**Required keys** (exact set, 7): `title`, `screening_header`, `screening_objective`, `competence_header`, `competence_objective`, `question_label`, `answer_label`

Each value is the label for that slot, **written by the model directly in the run language, by intent** — there is **no per-language phrase table** (L6). Render each label from what it *is*, picking the natural idiomatic term in the run language; **never transliterate an English label**. For `title`, name the deliverable by its function: *a guide to prepare for this interview*. See `modules/cover-letter-generator/references/language_style_generic.md` for register / locale conventions (spacing, punctuation, register).

### STEP 0 — Conversation rename (suggestion)

As soon as company + position are known, BEFORE generating, **suggest renaming** the conversation to the format `📋 YYYY-MM-DD - Company - Position` (the user applies it themselves via the interface; no confirmation required, just a suggestion). Don't block the workflow: continue directly.

### STEP 1 — Config check
1. `memory_user_edits view`, filter `[CONFIG]` and `[CANDIDAT]`
2. Check: `[CANDIDAT]` Full name, Email, LinkedIn; `[CONFIG]` Storage method, CV filename
3. If missing → ask to configure `candidate-config` first. Stop.

### STEP 2 — Get the posting
- **Raw text** → continue
- **URL** → `web_fetch`; if it fails (LinkedIn, protected sites) → ask for a copy-paste

### STEP 3 — Language + CV reading
1. **Language**: the run language is resolved by the orchestrator (SKILL STEP 4, sub-step 3-bis) — help-docs default to the **working/conversation language** (or the one-off override to the job's language). No char-window heuristic, no detection script.
2. Read the CV (`view` on the `[CONFIG] CV filename` file)

### STEP 4 — Generating the Q&A
See `references/interview_structure.md` for the question types.

- 8-10 questions per interview (~16-20 total)
- **Personalized** answers built from the CV and the posting, **truthful** (no invention)
- STAR format encouraged for interview 2 (use `-` bullets in the answer)
- **Tips**: add **targeted** contextual advice (not systematic) on high-stakes questions

**Present the Q&A to the user** for validation before generating the file.

### STEP 5 — Generating the .md

Build the JSON and run:
```bash
python scripts/generate_interview_prep.py \
  --language <code> \
  --output-path /mnt/user-data/outputs/<filename>.md \
  --data-json '<full_json>' \
  --labels-json '<labels_json — exact key set, values localized in the run language>'
```

**MANDATORY fields**:
- `candidate_name`, `job_title`, `company_name`, `date`
- `screening_questions`: `[{"question": "...", "answer": "..."}, ...]`
- `competence_questions`: `[{"question": "...", "answer": "..."}, ...]`

**OPTIONAL fields (tips)**:
- `opening_tip_screening`, `opening_tip_competence`, `closing_tip`: structuring advice (rendered as **callout boxes** in the PDF)
- On each question, a `"tip": "..."` field: tactical advice (rendered as a **side note** in the PDF)

**Tip dosage**: at most 6-8 tips in the whole document. Tips targeted on high-stakes questions ("tell me about yourself," weaknesses, salary, behavioral questions).

Present the `.md` with `present_files`.

### STEP 6 — Offer the PDF export

**After presenting the .md, always offer**:
```
The document is ready in Markdown. Would you also like a PDF version
(handier for forwarding and printing)?
```

If yes, run:
```bash
python scripts/md_to_pdf.py \
  --input /mnt/user-data/outputs/<filename>.md \
  --output /mnt/user-data/outputs/<filename>.pdf \
  --title "<deliverable title>"
```

The PDF automatically applies the house style (semantic palette, callout/side-note tips, lightbulb icon). Present the `.pdf` with `present_files`.


### FINAL STEP — Offer to add to the tracker

Once the deliverable(s) are produced and presented, **offer to add this application to the tracker** via the `application-tracker` module:
> "Would you like me to add this application (Company — Position) to your tracker?"

It's an offer, never forced. If the user accepts, delegate to `application-tracker` (workflow B: upsert an entry with date, company, position, language, and the produced deliverables). Don't make this offer more than once per application.


## Supported user commands

- `"Prepare my interviews for this posting: <text>"`: full workflow
- `"Generate interview prep"`: full workflow
- `"Export to PDF"`: convert an existing .md
- `"Redo the screening"` / `"Add a question about <topic>"`: regenerate

## Available scripts

| Script | Usage |
|--------|-------|
| `generate_interview_prep.py --language X --output-path X.md --data-json '...' --labels-json '...'` | Generates the .md |
| `md_to_pdf.py --input X.md --output X.pdf [--title "..."]` | Converts .md → styled PDF |

## References

- `references/interview_structure.md`: question types per interview + best practices

## Important rules

- **ALWAYS** read memory first
- **ALWAYS** validate the Q&A before generation
- **ALWAYS** offer the PDF after the .md
- **.md format** only (never .docx)
- **Truthful** answers (based on the CV)
- Questions **matched to the role's seniority level**
- **Targeted** tips, not systematic (max 6-8)
