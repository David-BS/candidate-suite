> **⚠️ MODULE OF THE "candidate-suite" SUITE — PATH RELOCATION**
> This module lives in `modules/application-summary-generator/`. All the relative paths below
> (`scripts/…`, `assets/…`, `references/…`) are relative to THIS folder.
> From the suite root: prefix them with `modules/application-summary-generator/`
> (e.g. `python modules/application-summary-generator/scripts/<script>.py …`), or change into
> `modules/application-summary-generator/` before running. The scripts' code is UNCHANGED:
> they receive all their paths as arguments, nothing is hard-coded.

---
name: application-summary-generator
description: Generates an application summary (Markdown, optional PDF export): strengths/weaknesses, a 5-sentence pitch, key talking points. Use for "generate an application summary", "make a summary sheet", "application summary for this role".
---

# Application summary generator

Generates an application-summary **Markdown** document (strengths/weaknesses, pitch, talking points), with optional styled PDF export for forwarding and third-party use.

## ⚠️ EXECUTION RULE (NON-NEGOTIABLE)

This module produces its deliverable ONLY via its Python scripts. Never write the final document "by hand" with `create_file`. Claude's role: PREPARE the content (JSON), then RUN the `generate_application_summary.py` script, then offer/run `md_to_pdf.py`.

- ✅ Generate the content → build the JSON → run the script
- ❌ DO NOT `create_file` a hand-written .md/.docx
- ❌ DO NOT invent an output format different from the script's

## ⚠️ VAGUE REQUEST → FOLLOW THE WORKFLOW

If the request is open-ended ("help me apply," "prepare my application"), don't improvise ad-hoc documents. Identify the candidate-suite sub-modules involved, announce the deliverables, run each workflow via its scripts. Produce only the planned deliverables; offer (without generating by default) any additional document.

## ⚠️ FUNDAMENTAL RULES

1. **Prerequisite**: The `candidate-config` module must be configured. Check via `memory_user_edits view`.

2. **Output format = Markdown (.md)** by default. `.docx` is NO LONGER used (cross-machine portability issues). After generating the `.md`, **always offer the PDF export**.

3. **To generate the .md**: use the `scripts/generate_application_summary.py` script.

4. **For the PDF export**: use the `scripts/md_to_pdf.py` script.

5. **Strict structure** (3 sections):
   - **Strengths / Weaknesses** (relative to the target role)
   - **5-sentence pitch** (exactly 5)
   - **Key talking points** (5-8)

## Overview

### Inputs
- **Job posting**: raw text OR URL

### Outputs
- **`.md` file** in `/mnt/user-data/outputs/` (main deliverable)
- **`.pdf` file** optional (offered after the .md)
- **Naming**: `Application_Summary_<Name>_<Company>_<Language>.md` (then `.pdf`). In `<Name>` and `<Company>`, replace spaces with hyphens (`-`); never run words together. E.g. `Application_Summary_Jordan-Lee-Carter_Acme-Financial-Group_EN.md`.

## Workflow — 6 steps

## Structure labels (produced by the model — L6)

This generator does **not** hard-code per-language labels. **You** produce the section labels **in the run language** and pass them as `--labels-json '{...}'` (alongside `--data-json` and `--language`). The script enforces the **exact** key set below — a missing or extra key is rejected (anti-hallucination guardrail: the structure is fixed, only the wording is yours).

**Required keys** (exact set, 8): `title`, `section_sw`, `sub_strengths`, `sub_weaknesses`, `section_pitch`, `pitch_intro`, `section_tp`, `tp_intro`

Each value is the localized label for that slot (e.g. `title` → EN `"Application Summary"`, FR `"Synthèse de candidature"`, DE `"Bewerbungsübersicht"`). See `modules/cover-letter-generator/references/language_style_generic.md` for register / locale conventions (spacing, punctuation, register).

### STEP 0 — Conversation rename (suggestion)

As soon as company + position are known, BEFORE generating, **suggest renaming** the conversation to the format `📋 YYYY-MM-DD - Company - Position` (the user applies it themselves via the interface; no confirmation required, just a suggestion). Don't block the workflow: continue directly.

### STEP 1 — Config check
1. `memory_user_edits view`, filter `[CONFIG]` and `[CANDIDAT]`
2. Check: `[CANDIDAT]` Full name; `[CONFIG]` Storage method, CV filename
3. If missing → ask to configure `candidate-config` first. Stop.

### STEP 2 — Get the posting
- **Raw text** → continue
- **URL** → `web_fetch`; if it fails → ask for a copy-paste

### STEP 3 — Language + CV reading
1. **Language**: the run language is resolved by the orchestrator (SKILL STEP 4, sub-step 3-bis) — help-docs default to the **working/conversation language** (or the one-off override to the job's language). No char-window heuristic, no detection script.
2. Read the CV (`view` on `[CONFIG] CV filename`)

### STEP 4 — Generating the 3 sections
See `references/summary_structure.md` for the details.

- **Strengths** (5 max): aligned with the posting, backed by the CV, distinctive
- **Weaknesses** (3 max): honest, with a constructive angle (area for growth)
- **Pitch**: exactly 5 sentences (identity / current role / value / why this company / call to action)
- **Talking points** (5-8): arguments to use in the interview, with quantified proof
- **Tips**: **targeted** contextual advice (2-4 max)

**Present everything to the user** for validation before generating the file.

### STEP 5 — Generating the .md

Build the JSON and run:
```bash
python scripts/generate_application_summary.py \
  --language <code> \
  --output-path /mnt/user-data/outputs/<filename>.md \
  --data-json '<full_json>' \
  --labels-json '<labels_json — exact key set, values localized in the run language>'
```

**MANDATORY fields**:
- `candidate_name`, `job_title`, `company_name`, `date`
- `strengths`: `[{"title": "...", "context": "..."}, ...]`
- `weaknesses`: `[{"title": "...", "approach": "..."}, ...]`
- `pitch`: a list of **5** strings
- `talking_points`: `[{"title": "...", "content": "..."}, ...]`

**OPTIONAL fields (tips)**:
- `opening_tip`, `tip_after_pitch`: structuring advice (rendered as **callout boxes** in the PDF)
- `tip_after_weaknesses`, `tip_after_talking_points`: tactical advice (rendered as **side notes**)

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
  --title "Application Summary"
```

The PDF applies the house style (strengths in green, weaknesses in orange, tips, lightbulb icon). Present the `.pdf` with `present_files`.


### FINAL STEP — Offer to add to the tracker

Once the deliverable(s) are produced and presented, **offer to add this application to the tracker** via the `application-tracker` module:
> "Would you like me to add this application (Company — Position) to your tracker?"

It's an offer, never forced. If the user accepts, delegate to `application-tracker` (workflow B: upsert an entry with date, company, position, language, and the produced deliverables). Don't make this offer more than once per application.


## Supported user commands

- `"Generate an application summary for this posting: <text>"`: full workflow
- `"Make a summary sheet"`: full workflow
- `"Export to PDF"`: convert an existing .md
- `"Redo the pitch"` / `"Add a talking point about <topic>"`: regenerate

## Available scripts

| Script | Usage |
|--------|-------|
| `generate_application_summary.py --language X --output-path X.md --data-json '...' --labels-json '...'` | Generates the .md |
| `md_to_pdf.py --input X.md --output X.pdf [--title "..."]` | Converts .md → styled PDF |

## References

- `references/summary_structure.md`: detailed structure of the 3 sections

## Important rules

- **ALWAYS** read memory first
- **ALWAYS** validate before generation
- **ALWAYS** offer the PDF after the .md
- **.md format** only (never .docx)
- **Pitch = exactly 5 sentences**
- Strengths and talking points based on the real CV (not invented)
- Honest but constructive weaknesses
- **Targeted** tips (2-4 max)
