> **⚠️ MODULE OF THE "candidate-suite" SUITE — PATH RELOCATION**
> This module lives in `modules/strategic-playbook-generator/`. All the relative paths below
> (`scripts/…`, `assets/…`, `references/…`) are relative to THIS folder.
> From the suite root: prefix them with `modules/strategic-playbook-generator/`
> (e.g. `python modules/strategic-playbook-generator/scripts/<script>.py …`), or change into
> `modules/strategic-playbook-generator/` before running. The scripts' code is UNCHANGED:
> they receive all their paths as arguments, nothing is hard-coded.

---
name: strategic-playbook-generator
description: Generates a strategic application playbook (Markdown, optional PDF export): company context, pain points, positioning, per-interview-round strategy, questions to ask, tough questions. Use for "generate a playbook", "prepare my interview strategy", "strategic guide for this application".
---

# Strategic playbook generator

Generates an in-depth application-strategy **Markdown** document: company context, pain points, candidate positioning, per-round interview strategy, questions to ask, and anticipated tough questions. Styled PDF export optional.

## ⚠️ EXECUTION RULE (NON-NEGOTIABLE)

This module produces its deliverable ONLY via the `scripts/generate_playbook.py` script. Never write the playbook "by hand" with `create_file`. Claude's role: PREPARE the data (JSON), then RUN the script.

- ✅ Generate the content → build the JSON → run `generate_playbook.py`
- ✅ Offer / run the PDF export via `md_to_pdf.py`
- ❌ DO NOT `create_file` a hand-written .md/.docx
- ❌ DO NOT invent a different output format

## ⚠️ VAGUE REQUEST → FOLLOW THE WORKFLOW

If the request is open-ended ("help me apply," "prepare my strategy"), don't improvise. Identify the modules involved, announce the deliverables, run each workflow via its scripts. Produce only the planned deliverables; offer (without generating by default) any additional document.

## Prerequisites

The `candidate-config` module must be configured. Check via `memory_user_edits view` (fields `[CANDIDAT]` Full name + `[CONFIG]` CV filename).

## Web search (conditional)

The playbook is all the more relevant when it draws on up-to-date information about the company (news, strategy, organization, sector issues).

- **If the web search tool is available in the conversation** → use it automatically to enrich the company context and the sector landscape (search: company name + news, strategy, organization; sector issues).
- **If web search is NOT available** → flag it to the user and offer: *"For a richer, up-to-date playbook, enable web search (tools button). Otherwise, I'll work from the posting and your configuration."* Then continue with the available information.

Never invent facts about the company. Any factual claim from the web must be reliable; absent a source, stay on generic sector analysis clearly presented as such.

## Inputs / Outputs

**Inputs**: job posting (text or URL); optional: user-provided context, info on the recruitment process.

**Output**: a `.md` file in `/mnt/user-data/outputs/` (+ optional `.pdf`).
**Naming**: `Strategic_Playbook_<Name>_<Company>_<Language>.md`. In `<Name>` and `<Company>`, replace spaces with hyphens (`-`); never run words together. E.g. `Strategic_Playbook_Jordan-Lee-Carter_Acme-Financial-Group_EN.md`.

## Workflow — 7 steps

## Structure labels (produced by the model — L6)

This generator does **not** hard-code per-language labels. **You** produce the section labels **in the run language** and pass them as `--labels-json '{...}'` (alongside `--data-json` and `--language`). The script enforces the **exact** key set below — a missing or extra key is rejected (anti-hallucination guardrail: the structure is fixed, only the wording is yours).

**Required keys** (exact set, 20): `title`, `web_note_yes`, `web_note_no`, `usage_tip`, `s_context`, `s_pain`, `s_org`, `s_positioning`, `s_strategy`, `s_questions`, `s_tough`, `s_pitch`, `s_redlines`, `analysis`, `your_angle`, `evidence`, `round`, `focus`, `approach`, `strategy`

Each value is the label for that slot, **written by the model directly in the run language, by intent** — there is **no per-language phrase table** (L6). Render each label from what it *is*, picking the natural idiomatic term in the run language; **never transliterate an English label**. For `title`, name the deliverable by its function: *the candidate's strategic plan of approach for winning this specific role*. See `modules/cover-letter-generator/references/language_style_generic.md` for register / locale conventions (spacing, punctuation, register).

### STEP 0 — Conversation rename (suggestion)

As soon as company + position are known, BEFORE generating, **suggest renaming** the conversation to the format `📋 YYYY-MM-DD - Company - Position` (the user applies it themselves via the interface; no confirmation required, just a suggestion). Don't block the workflow: continue directly.

### STEP 1 — Config check
`memory_user_edits view` → filter `[CONFIG]`/`[CANDIDAT]`. If config is missing → ask to run `candidate-config`. Stop.

### STEP 2 — Get the posting
Raw text → continue. URL → `web_fetch`; if it fails → ask for a copy-paste.

### STEP 3 — Language + CV reading
**Language**: the run language is resolved by the orchestrator (SKILL STEP 4, sub-step 3-bis) — help-docs default to the **working/conversation language** (or the one-off override to the job's language). No char-window heuristic, no detection script. Then read the CV (`view` on `[CONFIG] CV filename`).

### STEP 4 — Conditional web search
Apply the "Web search (conditional)" rule above.

### STEP 5 — Building the playbook content
See `references/playbook_structure.md` for the section details. The playbook includes (adapt as relevant):
1. Company / entity context
2. Major pain points (what they're really trying to solve) + response angle
3. Organizational landscape / dynamics (who decides, typical tensions)
4. Candidate positioning (key messages with proof)
5. Per-round interview strategy
6. Questions to ask the recruiter
7. Anticipated tough questions + response strategies
8. 30-second pitch
9. Watch-outs / red lines before accepting

**Present a content summary to the user** for validation before generation.

### STEP 6 — Generating the .md
Build the JSON and run:
```bash
python scripts/generate_playbook.py \
  --language <code> \
  --output-path /mnt/user-data/outputs/<filename>.md \
  --data-json '<full_json>' \
  --labels-json '<labels_json — exact key set, values localized in the run language>'
```
Present the `.md` with `present_files`.

### STEP 7 — Offer the PDF export
Always offer:
```
The playbook is ready in Markdown. Would you also like a PDF version?
```
If yes:
```bash
python scripts/md_to_pdf.py --input <filename>.md --output <filename>.pdf --title "<deliverable title>"
```
Present the `.pdf`.


### FINAL STEP — Offer to add to the tracker

Once the deliverable(s) are produced and presented, **offer to add this application to the tracker** via the `application-tracker` module:
> "Would you like me to add this application (Company — Position) to your tracker?"

It's an offer, never forced. If the user accepts, delegate to `application-tracker` (workflow B: upsert an entry with date, company, position, language, and the produced deliverables). Don't make this offer more than once per application.


## Available scripts

| Script | Usage |
|--------|-------|
| `generate_playbook.py --language X --output-path X.md --data-json '...' --labels-json '...'` | Generates the .md |
| `md_to_pdf.py --input X.md --output X.pdf [--title "..."]` | Converts to styled PDF |

## References
- `references/playbook_structure.md`: detailed section structure + expected JSON

## Important rules
- ALWAYS read memory first
- ALWAYS validate the content before generation
- ALWAYS offer the PDF after the .md
- `.md` format only (never .docx)
- Web search: auto if available, otherwise offered
- No factual invention about the company
- Generic sector analysis clearly presented as such
