> **⚠️ MODULE OF THE "candidate-suite" SUITE — PATH RELOCATION**
> This module lives in `modules/quick-reference-generator/`. All the relative paths below
> (`scripts/…`, `assets/…`, `references/…`) are relative to THIS folder.
> From the suite root: prefix them with `modules/quick-reference-generator/`
> (e.g. `python modules/quick-reference-generator/scripts/<script>.py …`), or change into
> `modules/quick-reference-generator/` before running. The scripts' code is UNCHANGED:
> they receive all their paths as arguments, nothing is hard-coded.

---
name: quick-reference-generator
description: Generates a quick reference card (1 page, Markdown + PDF) condensing the other application documents: pitch, key stats, top talking points, questions to ask, checklist. Use for "generate a reference card", "quick reference card", "1-page recap sheet for my interviews".
---

# Quick reference generator

Generates a **one-page quick reference card** (Markdown, optional PDF export), to print or check right before each interview. It is a CONDENSED version of the other application documents already produced.

## ⚠️ EXECUTION RULE (NON-NEGOTIABLE)

This module produces its deliverable ONLY via the `scripts/generate_quick_reference.py` script. Never write the card "by hand" with `create_file`. Claude's role: read the sources, condense, build the JSON, run the script.

- ✅ Read the source .md files → condense → build the JSON → run the script
- ✅ Offer / run the PDF export via `md_to_pdf.py`
- ❌ DO NOT `create_file` a hand-written card
- ❌ DO NOT invent a different format

## ⚠️ VAGUE REQUEST → FOLLOW THE WORKFLOW

If the request is open-ended, don't improvise. Identify the modules involved, announce the deliverables, run each workflow via its scripts.

## Dependency: this card CONDENSES other documents

The quick reference only makes sense as a **synthesis** of the deliverables already generated
(application summary, interview prep, playbook). Its workflow therefore starts
by RETRIEVING those sources.

### Source-file lookup (auto, falls back to asking)
1. Look in `/mnt/user-data/outputs/` for this application's `.md` files:
   - `Application_Summary_*.md`
   - `Interview_Prep_*.md`
   - `Strategic_Playbook_*.md`
2. **If at least one file is found** → read it/them (`view`) and extract the elements to condense.
3. **If no file is found** → ask the user:
   *"I didn't find any application documents to condense for this role. Would you like me to generate the summary / interview prep / playbook first, or can you point me to the files to use?"*
   Do NOT fabricate a card from scratch if the intent is to condense existing documents.

## Prerequisite
The `candidate-config` module must be configured (for the candidate name, etc.).

## Inputs / Outputs

**Inputs**: the already-generated application `.md` files (summary, interview prep, playbook); the posting for context.

**Output**: a one-page `.md` in `/mnt/user-data/outputs/` (+ optional `.pdf`).
**Naming**: `Quick_Reference_<Name>_<Company>_<Language>.md`. In `<Name>` and `<Company>`, replace spaces with hyphens (`-`); never run words together. E.g. `Quick_Reference_Jordan-Lee-Carter_Acme-Financial-Group_EN.md`.

## Workflow — 6 steps

## Structure labels (produced by the model — L6)

This generator does **not** hard-code per-language labels. **You** produce the section labels **in the run language** and pass them as `--labels-json '{...}'` (alongside `--data-json` and `--language`). The script enforces the **exact** key set below — a missing or extra key is rejected (anti-hallucination guardrail: the structure is fixed, only the wording is yours).

**Required keys** (exact set, 8): `title`, `s_pitch`, `s_stats`, `s_points`, `s_qa`, `s_questions`, `s_checklist`, `evidence`

Each value is the localized label for that slot (e.g. `title` → EN `"Quick Reference Card"`, FR `"Fiche de référence rapide"`, DE `"Schnellreferenz"`). See `modules/cover-letter-generator/references/language_style_generic.md` for register / locale conventions (spacing, punctuation, register).

### STEP 1 — Config check
`memory_user_edits view`. If config is missing → ask for `candidate-config`. Stop.

### STEP 2 — Retrieve the sources to condense
Apply the "Source-file lookup" rule above. Read the .md files found.

### STEP 3 — Language detection
Language = that of the source documents (or of the posting if provided).

### STEP 4 — Condensing
From the sources, extract and condense (see `references/quickref_structure.md`):
- **pitch_short**: the pitch / story in a short form (to memorize)
- **key_stats**: 4-6 key figures to know by heart
- **top_points**: 3 points to land for sure (with proof)
- **quick_qa**: 3-5 frequent questions + express answers
- **questions_to_ask**: 4-6 strategic questions to ask
- **checklist**: final checklist before the interview

Stay CONCISE: the card must fit on **one page**. No long paragraphs, only punchy items.

⚠️ **WATCH-OUT — `top_points` and `quick_qa` fields**: these are the two sections that require real synthesis (condensing the talking points and the Q&A from the other documents). NEVER leave them as empty skeletons (`{"point":"", "evidence":""}` or `{"q":"", "a":""}`). Each entry must be fully written BEFORE calling the script:
- `top_points`: take the 3 strongest talking points from the Application Summary / Playbook, with their quantified proof.
- `quick_qa`: take the most likely interview questions (from the Interview Prep) with a one-sentence express answer.

If a source is missing to fill these fields, tell the user rather than produce empty entries.

**Completeness check**: the script prints a warning if some entries are empty. If that warning appears, DO NOT present the document as-is: fix the JSON (fill the fields) and regenerate.

**Present the condensed card to the user** for validation before generation.

### STEP 5 — Generating the .md
Build the JSON and run:
```bash
python scripts/generate_quick_reference.py \
  --language <code> \
  --output-path /mnt/user-data/outputs/<filename>.md \
  --data-json '<full_json>' \
  --labels-json '<labels_json — exact key set, values localized in the run language>'
```
Present the `.md` with `present_files`.

### STEP 6 — Offer the PDF export
Always offer the PDF (ideal for a 1-page print):
```bash
python scripts/md_to_pdf.py --input <filename>.md --output <filename>.pdf --title "Quick Reference"
```
Present the `.pdf`.

## Available scripts

| Script | Usage |
|--------|-------|
| `generate_quick_reference.py --language X --output-path X.md --data-json '...' --labels-json '...'` | Generates the .md |
| `md_to_pdf.py --input X.md --output X.pdf [--title "..."]` | Converts to styled PDF |

## References
- `references/quickref_structure.md`: card structure + expected JSON

## Important rules
- ALWAYS read memory first
- ALWAYS retrieve/condense the existing sources (don't start from scratch if the intent is to condense)
- ALWAYS validate before generation
- ALWAYS offer the PDF
- `.md` format only
- **Fit on ONE page**: concise, punchy
- Consistency with the source documents (same figures, same positioning)
