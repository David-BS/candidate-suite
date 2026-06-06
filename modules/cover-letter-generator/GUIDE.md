> **⚠️ MODULE OF THE `candidate-suite` SUITE — PATH RELOCATION**
> This module lives in `modules/cover-letter-generator/`. All relative paths below
> (`scripts/…`, `assets/…`, `references/…`) are relative to THIS folder.
> From the suite root: prefix them with `modules/cover-letter-generator/`
> (e.g. `python modules/cover-letter-generator/scripts/<script>.py …`), or `cd` into
> `modules/cover-letter-generator/` before running. The scripts' code is UNCHANGED:
> they all receive every path as an argument, nothing is hard-coded.

---
name: cover-letter-generator
description: Generates a .docx cover letter from a job posting and writes the 5 mandatory paragraphs in the run language. The run language is resolved and confirmed by the orchestrator (see SKILL.md), not detected here. Use for "generate a cover letter", "write a cover letter".
---

# Cover letter generator

Generates a personalised cover letter (`.docx`) from a job posting, building on the user configuration managed by the `candidate-config` module.

> **LNG-1 socle note (review draft).** This GUIDE has been refactored to the model-agnostic
> language socle: there is **no language-detection script** here anymore (`detect_language.py`
> was removed — L4). The run language is **resolved and confirmed by the orchestrator** (see
> `SKILL.md`, STEP 4 sub-step *3-bis*) and arrives as `--language <code>`. The realisation of a
> chosen language (salutation, subject, closing, date, spacing, register) is governed by
> `references/letter_conventions.md` + `references/language_style_generic.md`, **not** by an
> enumerated FR/EN table. `fr` / `en` and **any ISO language** work — multi-language is supported (**L6 landed**): the
> model produces the localized labels/strings and a **single neutral template** is filled. The
> signature behaviour below is the reconciled SIG-1 model (project file, never memory/Drive).

## ⚠️ VAGUE REQUEST → FOLLOW THE WORKFLOW

If the request is open-ended ("help me apply", "prepare my application"), do not improvise ad-hoc documents. Identify the candidate-suite sub-modules involved, announce the deliverables, run each workflow through its scripts. Never write the final deliverable "by hand" with `create_file`: always go through the scripts. Produce only the planned deliverables; offer (without generating by default) any additional document.

## ⚠️ FUNDAMENTAL RULES

1. **Prerequisite**: the `candidate-config` module must be configured. Check by reading `memory_user_edits view` at the start. If data is missing, tell the user to configure first.

2. **To fill the template**: always use the script `scripts/fill_cover_letter.py`. NEVER generate the `.docx` by hand with ad-hoc python-docx.

3. **Run language vs. recruiter/company extraction**: the **run language is already resolved by the orchestrator** (`SKILL.md`, STEP 4 *3-bis*) and passed in as `--language` — **this module does not detect language**. For recruiter/company extraction, the model reads the posting directly (STEP 4) — no script, no regex; never invent unverified details.

4. **For the paragraphs**: generate them **in the run language** (the value passed as `--language`). Follow the mandatory structure (see `references/paragraph_structure.md`).

## Overview

### Expected inputs
- **Job posting**: pasted raw text OR a URL
- **Optional**: recruiter name, recruiter title (otherwise: attempt extraction, then ask)
- **Optional**: custom date (otherwise: today's date)
- **Run language**: received as `--language <code>` from the orchestrator (not an input of this module)

### Outputs produced
- **`.docx` file**: finalised cover letter with signature, written to `/mnt/user-data/outputs/`
- **Optional PDF (#7)**: if the user asks for PDF export, convert the `.docx` via `python scripts/docx_to_pdf.py --input <letter.docx> --output <letter.pdf>` (LibreOffice headless). Keep the same base name as the `.docx`. If LibreOffice is unavailable (exit 3), the letter is still delivered as `.docx`.
- **Naming**: `Cover_Letter_<Name>_<Company>_<LANG>.docx`. In `<Name>` and `<Company>`, replace spaces with hyphens (`-`) for readability; never run words together. E.g. `Cover_Letter_Jordan-Lee-Carter_Acme-Financial-Group_EN.docx` (not `JordanLeeCarter_AcmeFinancialGroup`). `<LANG>` is the resolved run language code.

### Data sources
- **Candidate data**: `memory_user_edits` (prefix `[CANDIDAT]`)
- **Configuration**: `memory_user_edits` (prefix `[CONFIG]`)
- **CV**: file referenced in `[CONFIG] CV filename`
- **Signature**: resolved by `resolve_files.py` (SIG-1) — see note below
- **Template**: resolved by language — see note below

### Signature resolution
> Signature resolution is owned by the SIG-1 resolver (`resolve_files.py`): the signature comes
> from **session upload → project file** (base64 `.txt`), **never** from memory and **never**
> from Google Drive. The `[CONFIG] Signature base64` memory key is **deprecated** (memory is
> capped at 500 chars, far below the ~14,000 of a base64 signature). The orchestrator passes the
> resolved path to `fill_cover_letter.py --signature-path <path>` → signed letter **without
> re-upload**. If no signature is available, the script removes the `{{SIGNATURE_IMAGE}}`
> placeholder cleanly and the letter is delivered unsigned (the user signs by hand).

### Template resolution
The module ships its own self-contained **neutral** template in `assets/` (`Cover_letter_template.docx`). Logic for the template passed to `--template-path`:

1. **If the user supplied a template** (referenced in `[CONFIG] Template filename`, stored in the project files) → use it first (respect the user's choice).
2. **Otherwise** (no user template, or not found) → use the module's bundled neutral template: `assets/Cover_letter_template.docx` (the common case when the user relies on the bundled template — no project file needed).

⚠️ There is ALWAYS a template available (the bundled one at minimum). So **NEVER** fall back to a hand-built `.docx` with python-docx: if the user template is missing, take the bundled one, full stop. The module works autonomously with **no Drive dependency**.

> **L6 (landed).** There is now **a single neutral, parameterised template** whose content is
> localised by the model in the run language (subject label, salutation, closing are
> placeholders) — the **visual skeleton stays a non-negotiable asset** (the 9 formatting rules:
> Calibri, A4, fused header borders, floating signature…). It works for `fr`/`en`/any language.

## Workflow — 6 BLOCKING steps

### STEP 0 — Conversation rename (suggestion)

As soon as company + position are known, BEFORE generating, **suggest renaming** the conversation to: `📋 YYYY-MM-DD - Company - Position` (the user applies it themselves through the interface; no confirmation required, just a suggestion). Do not block the workflow: continue straight on.

### STEP 1 — Configuration check

1. Read memory: `memory_user_edits view`
2. Filter the `[CONFIG]` and `[CANDIDAT]` lines
3. Check the presence of the **mandatory** fields:
   - `[CANDIDAT]`: First name, Last name, Full name, Street, Postal code, City, Email, Phone, LinkedIn
   - `[CONFIG]`: Storage method, CV filename, Signature filename, Template filename

4. **If data is missing**, tell the user:
   ```
   Incomplete configuration. Here is what is missing:
   - <list of missing fields>

   Run the candidate-config module first to set up your profile.
   ```
   Stop the workflow.

5. **If configuration is OK**, go to STEP 1.5.

### STEP 1.5 — Critical-data check

Before continuing, verify that the data actually needed to fill the template is **all present and non-empty**. This step is a **safety net**: normally the data comes from the orchestrator's widget (which may be an editable block) or from memory; this check guarantees no critical field slips through silently.

**Critical data** (the letter cannot be filled correctly without it):
- `sender_full_name`
- `sender_street`
- `sender_postal_code`
- `sender_city`
- `sender_email`
- `recruiter_title` (the name may stay generic if unknown, the title may not)
- `company_name`

**Behaviour**:
- If **all critical data is present** → go straight to STEP 2 (no superfluous recap).
- If **at least one critical field is missing** → stop the workflow and ask the user explicitly:
  ```
  Before generating the letter, I need to complete a few details:
  - <list of missing fields with clear labels>

  Here is what I already have: <short summary of the present data>

  Can you provide the missing items?
  ```
  Never generate the letter with empty critical fields or default/placeholder values.

  Note (LNG-2 S3b — structural sentinel): `fill_cover_letter.py` rejects (exit 2) any critical field that is **empty** OR equals the language-neutral sentinel `__MISSING__`. The former multilingual placeholder word-list ("to complete"/"à compléter"/"TBD"…) is **gone** — it was FR/EN-only and brittle. The contract is now structural: **never invent a placeholder**; when a mandatory field (address, etc.) is missing, **ask the user** and re-run. If you ever call the script without a mandatory datum, pass `__MISSING__` in that field to force a clean refusal rather than inventing a value.

### STEP 2 — Retrieve the job posting

**Case A: posting provided as raw text** (in the user message)
→ Go straight to STEP 3.

**Case B: posting provided as a URL**
1. Try `web_fetch` on the URL
2. **If scraping succeeds**: extract the posting text, go to STEP 3
3. **If scraping fails** (LinkedIn, protected sites, etc.): ask the user to copy-paste the posting content

### STEP 3 — Run language (already resolved)

> **Changed by LNG-1 (L3/L4).** This step used to run `detect_language.py` on the first
> ~500 characters. That script is **removed**. The orchestrator has already identified the
> offer's language **by reading it** (a free by-product of the single global analysis) and
> **confirmed it once** with the user; it passes the result as `--language <code>`.

No detection happens here. Take the `--language <code>` value handed down by the orchestrator. That value governs:
- the template used (`assets/Cover_letter_template_<LANG>.docx` for `fr` / `en`; one neutral template after L6),
- the language of the 5 paragraphs,
- the salutation and closing,
- the date format and spacing.

How each of these is realised in the target language is specified in `references/letter_conventions.md` (letter-specific) and `references/language_style_generic.md` (register, idiom, locale formats — all deliverables). Do **not** re-enumerate per-language rules here.

### STEP 4 — Recruiter and company extraction (model-driven)

The single global analysis already read the posting. As a **free by-product of that read**, extract these fields **yourself, in any language** — no script, no regex (reading meaning from the posting is a model task / *fond*; the script only renders / *forme*):

```json
{
  "company_name": "Acme Corp",
  "job_title": "Senior Software Engineer",
  "recruiter_name": "Jane Smith" or null,
  "recruiter_title": "Head of Engineering" or null,
  "company_city": "Paris" or null
}
```

Pass them to `fill_cover_letter.py`.

**`company_name` (required)**: postings are often in prose with no explicit "Company:" label — **determine the company name from the posting text** (a reliable read you do well, in any language). Ask the user only if it is genuinely unfindable or ambiguous. Never pass an empty `company_name` (`fill_cover_letter.py` refuses, exit 2).

**Unknown recruiter**: if no named recruiter and no department is explicitly given in the posting, **leave `recruiter_name` AND `recruiter_title` empty** — NEVER invent a name, a department or a "team" (deriving "Modernisation team…" from the job title is an unverified invention on an outgoing letter). In that case **you** provide a localised recruiter-default yourself in `recruiter_name` (in the run language, e.g. `Service Recrutement` / `Recruitment Department` / `Personalabteilung`) — the script **no longer injects one**; it just renders a clean recipient block (no orphan comma when the title is empty). Only fill `recruiter_title` if the posting explicitly names a department or a title. For the salutation, provide the localised default in `greeting` — see `references/letter_conventions.md` (e.g. `Dear Hiring Manager,` for `en`, `Madame, Monsieur,` for `fr`).

> **Recruiter default (L6).** `fill_cover_letter.py` **no longer** carries a hardcoded FR/EN
> recruiter-default: the model supplies a localised `recruiter_name` in the run language when
> the recruiter is unknown (see `references/letter_conventions.md`). The script only cleans the
> recipient block (orphan comma) when the title is empty — language-agnostic.

**Contact data (#2)**: copy the email, phone and especially the LinkedIn URL **verbatim** from the CV or memory (copy-paste), never retype from memory. A transcription error — a missing hyphen in the LinkedIn URL, say — goes unnoticed but ends up on an outgoing letter.

### STEP 5 — Generate the 5 paragraphs

⚠️ **CRUCIAL**: the 5 paragraphs must follow a **strict structure**, **in the run language**, building on the user's CV and the posting.

See `references/paragraph_structure.md` for the full details.

**Structure (validated Option A)**:
1. **§1 — Hook**: target role + years of experience + quick fit
2. **§2 — Current role**: key responsibilities + parallels with the target role
3. **§3 — Relevant prior experience**: track record that consolidates the application
4. **§4 — Value proposition**: what the candidate CONCRETELY brings to the company (with quantified proof from the past). Company-benefit oriented, not CV.
5. **§5 — Closing**: specific motivation for the company + availability + thanks

**📏 "One-page" budget (aim for it from the first generation)**:
The letter must fit on **a single page**. The total of the 5 paragraphs (body, spaces included) must stay **≤ 2800 characters** — a calibrated value validated in Word, **language-neutral** (the same cap whatever the language). Beyond that, the letter overflows onto a second page.

Indicative per-paragraph targets (ratio × 2800, ±20 % tolerance):

| Paragraph | Target |
|---|---|
| §1 Hook | ~420 |
| §2 Current role | ~616 |
| §3 Experience | ~728 |
| §4 Value proposition | ~616 |
| §5 Closing | ~420 |

- **§4 is the trap**: it tends to balloon (proof accumulation). Keep it within target.
- `fill_cover_letter.py` **REFUSES (exit 2)** if the total exceeds the cap, indicating which paragraph to shorten first. Aiming for the budget up front avoids the round-trip.
- To fit: **shorten the content** — **never** reduce margins or font. Cap adjustable via `--body-cap`.

**Steps**:
1. Read the CV content (`view` on the file referenced in `[CONFIG] CV filename`)
2. Analyse the job posting
3. Generate the 5 paragraphs following the structure above
4. **Present the 5 paragraphs to the user** for validation/adjustment before filling the template

**Presentation format** (in the run language):
```
📝 I've generated the 5 paragraphs. Read them and tell me what you'd like to adjust.

§1 — Hook
<content>

§2 — Current role
<content>

§3 — Prior experience
<content>

§4 — Value proposition
<content>

§5 — Closing
<content>

Do you approve, or would you like me to adjust anything?
```

Wait for approval or adjustments. Iterate if needed.

### STEP 6 — Fill the template and generate the .docx

Once the paragraphs are approved, run:
```bash
python scripts/fill_cover_letter.py \
  --language <code> \
  --template-path <template_path> \
  --signature-path <signature_b64_path> \
  --output-path <output_path> \
  --data-json '<json_with_all_data>'
```

For `--template-path`, apply the **template resolution** (see the dedicated section above):
- the user template if it exists (project files),
- otherwise the bundled **neutral** template: `assets/Cover_letter_template.docx` (path relative to the module root) — the common case when the user relies on the bundled template.

If the signature is unavailable, the script handles the absence (placeholder ignored): do not block on it.

The `--data-json` must contain:
- All candidate data (sender_name, sender_street, etc.)
- Recipient data (recruiter_name, recruiter_title, company_name)
- **`date_line`** — the place-and-date line, **composed by the model in the target locale's convention** (e.g. `Paris, le 6 juin 2026` / `New York, June 6, 2026` / date-only `6 June 2026` where the locale omits the city); date formatting per `references/language_style_generic.md`. `sender_city` is still supplied for the **sender address block**.
- Job title (job_title)
- **Localized letter strings, produced by the model in the run language** — `subject_label` (objet label incl. its separator + trailing space, e.g. `Poste : ` / `Position: ` / `Betreff: `), `greeting` (salutation), `closing` (e.g. `Cordialement,` / `Sincerely,` / `Mit freundlichen Grüßen,`); see `references/letter_conventions.md`
- The 5 paragraphs (paragraph_1_intro, paragraph_2_current, paragraph_3_experience, paragraph_4_value, paragraph_5_closing)

The script:
- Loads the template
- Replaces the placeholders (preserving multiple runs)
- Inserts the signature image under the name
- Saves the `.docx` to the output path

**Output filename**: `Cover_Letter_<Name>_<Company>_<LANG>.docx` (spaces in compound names replaced by hyphens).

Present the final file with `present_files`.

### FINAL STEP — Offer to add to the tracker

Once the letter is produced and presented, **offer to add this application to the tracker** via the `application-tracker` module:
> "Would you like me to add this application (Company — Position) to your tracker?"

It is an offer, never imposed. If the user accepts, delegate to `application-tracker` (workflow B). Do not make this offer more than once per application.

## Supported user commands

- `"Generate a cover letter for this posting: <text>"`: full workflow
- `"Create a cover letter for this role"` (then provide the posting): full workflow
- `"Redo paragraph X"`: regenerate a specific paragraph
- `"Change the recruiter to <name>"`: update and regenerate
- `"Make the tone more formal"` or `"more enthusiastic"`: regenerate with a tone instruction

## Available scripts

| Script | Usage |
|--------|-------|
| `fill_cover_letter.py --language X --template-path X --signature-path X --output-path X --data-json '...'` | Fills the template and inserts the signature |

> **Removed (L4):** `detect_language.py` — language is resolved by the orchestrator, not by a
> script in this module.
> **Removed (LNG-2 S3):** `extract_recruiter_info.py` — recruiter/company/position/city are now
> extracted by the model directly from the posting (any language), per STEP 4. No regex extractor.

## References (for technical details)

- `references/paragraph_structure.md`: detailed structure of the 5 paragraphs (with per-paragraph examples). The **section set is frozen**; only the wording is produced by the model (LNG-1 anti-hallucination counterweight).
- `references/letter_conventions.md`: letter-specific language realisation (salutation, subject, closing, recipient default, date format, spacing) — agnostic, replaces the former `language_conventions.md`.
- `references/language_style_generic.md`: generic register / idiom / locale formats for all deliverables.

## Important rules

- **ALWAYS** read memory first to retrieve the config
- **ALWAYS** ask for validation of the 5 paragraphs before the final fill
- **NEVER** generate the `.docx` without going through `fill_cover_letter.py`
- **NEVER** improvise on the 5-paragraph structure (follow `paragraph_structure.md`)
- **§4 must be company-benefit oriented**, not CV (crucial difference)
- **Language realisation** (salutation, closing, date format, spacing — e.g. non-breaking spaces before `: ; ? !` in French; `27 May 2026` vs `27 mai 2026`) is governed by `references/letter_conventions.md`, not enumerated here. The template already carries the language's spacing.
- **The run language** is whatever the orchestrator resolved and passed as `--language`; this module never detects it.
