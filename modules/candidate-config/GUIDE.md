> **⚠️ MODULE OF THE "candidate-suite" SUITE — PATH RELOCATION**
> This module lives in `modules/candidate-config/`. All the relative paths below
> (`scripts/…`, `assets/…`, `references/…`) are relative to THIS folder.
> From the suite root: prefix them with `modules/candidate-config/`
> (e.g. `python modules/candidate-config/scripts/<script>.py …`), or change into
> `modules/candidate-config/` before running. The scripts' code is UNCHANGED:
> they receive all their paths as arguments, nothing is hard-coded.

---
name: candidate-config
description: Manages the configuration for professional job applications: personal data, CV, signature, cover-letter templates. Use for "configure my skill", "update my CV", "show my config", "reset my config".
---

# Candidate config

Configuration for professional applications: personal data, reference files, storage mode.

## ⚠️ FUNDAMENTAL RULE

**For critical outputs (questions, recap), run the `scripts/setup_workflow.py` script and display the result as-is. NEVER reformat, paraphrase, or invent the content.**

## ⚠️ ROUTING TO THE OTHER MODULES

This module manages ONLY the configuration. If the user asks to produce application deliverables (letter, interview prep, summary, playbook, reference card) — including via a vague request ("help me apply to X") — don't improvise: route to the dedicated modules and run their workflows via their scripts:
- Cover letter → `cover-letter-generator`
- Interview prep → `interview-prep-generator`
- Application summary → `application-summary-generator`
- Strategic playbook → `strategic-playbook-generator`
- 1-page reference card → `quick-reference-generator`

## Simple principle

- **If the user provides their own cover-letter templates** → respect them as-is, full stop. No questions about formatting.
- **If the user provides no templates** → generate the defaults in **Hybrid** mode (3 compact lines) with `scripts/generate_templates.py`. No question to the user, no invention.

## Quick overview

- **2 storage modes**: project file (default) / stateless (no Drive) → `references/storage_options.md`
- **Personal data**: stored in `memory_user_edits` → `references/memory_format.md`
- **Reference files**: CV, signature (base64), EN+FR templates

## Initial setup workflow — 5 BLOCKING steps

When the user says `"Configure my skill"`, follow these 5 steps in order. **One step at a time.**

### STEP 1 — Storage mode

Run:
```bash
python scripts/setup_workflow.py storage_question
```

Display the result **as-is**. Wait for the answer. Save:
```
[CONFIG] Storage method: <project_files|stateless>
```

> **No Google Drive.** The Drive storage mode was removed (a connector call can hang the session — see `references/storage_options.md`). Only two modes remain: **project file** (persistent) and **stateless** (session-only). There is no `Drive integration` toggle.

### STEP 2 — Personal data

**If a CV is provided**:
1. Read the CV **directly** (`view` / the file-reading skill) and **extract the fields yourself, in any language** — name, email, phone, address (street, postal code, city), LinkedIn, GitHub. Reading the CV is a model task (*fond*); there is no regex extractor.
2. **If the extracted name has 3+ words** (e.g. "Jordan Lee Carter"), run:
   ```bash
   python scripts/setup_workflow.py name_check --extracted-name "Jordan Lee Carter"
   ```
   Display the result as-is. Wait for the answer.
3. Present the extracted data concisely for validation
4. If the address is missing from the CV: ask for it
5. Wait for the user's validation

**If no CV**: ask for the info manually.

Save each field with the `[CANDIDAT]` prefix (see `references/memory_format.md`).

Fields: `First name`, `Last name`, `Full name`, `Street`, `Postal code`, `City`, `Email`, `Phone`, `LinkedIn`.

> **Language & locale (LNG-1 / L1).** The profile stores **no language** — there is no language
> field and no frozen default. The working language follows the **conversation**; the letter
> language follows the **confirmed offer** (persisted per-application in the tracker, not here).
> See `SKILL.md` (Language principle + STEP 4 sub-step 3-bis). The only locale the profile
> carries is **temporal**, and it is **derived, not stored**: the existing `City` field yields
> the timezone via `zoneinfo` (e.g. `City` → `Europe/Paris`, DST-handled) used for the tracker
> filename timestamp. No timezone field to fill.

### STEP 3 — Signature

**Current model (SIG-1): the signature is a base64 `.txt` file dropped into the project files, read by its name in each conversation.**

> ⚠️ **Deprecated:** the old `[CONFIG] Signature base64` key (signature stored in memory) is abandoned. Memory is capped at 500 characters, far below the ~14,000 of a base64 signature: it can't hold it. No longer write or read `[CONFIG] Signature base64`. Persistence goes through a **project file**, never memory.

**If a signature image is provided** (PNG, JPG, GIF or BMP) — produce the reusable `.txt`:
```bash
python scripts/setup_signature.py --input-path /mnt/user-data/uploads/<filename>
```
The script validates the format, resizes if needed (10 s safety timeout, threshold ~15,000 chars / ~600 px width), encodes to base64, and writes a file named `<basename>_<ext>_b64.txt`.

Then, return and remember the **name** (not the content):
1. Present the `.txt` via `present_files` and explain to the user that they must **drop it into the project files themselves** (the module reads the project but cannot write to it).
2. `memory_user_edits add`:
   - `[CONFIG] Signature persistence: project`
   - `[CONFIG] Signature filename: <name of the .txt>`

**For each letter afterward**: `resolve_files.py` (root) locates this file in the project (status `present_project`) and its path is passed to `fill_cover_letter.py --signature-path` → signed letter **without re-upload**. No signature in memory.

⚠️ **Error handling for `setup_signature.py`**:
- Exit 3 (timeout) → follow the displayed instructions (manual reduction or skip).
- Exit 4 (image too large after optimization) → ask for a simpler image.
- Exit 1 (unsupported format or unreadable file) → ask for another image.

**If no signature**: drop nothing. The letter is generated without an image (handwritten signature afterward). Set `[CONFIG] Signature persistence: session`.

**Change / remove**:
- Change: regenerate the `.txt` and re-drop it into the project (it replaces the old one on the project-files side).
- Remove: take the file out of the project files and set `[CONFIG] Signature persistence: session`.

⚠️ **Public diffusion**: the signature stays **personal** (a file in the user's project), never embedded in the module. Outside a project, or with memory paused, the module invites the user to provide a one-off signature for the session (status `present_upload`), with no persistence.


### STEP 4 — Templates (simplified logic)

**Case A: The user provided .docx templates in the conversation**
- ✅ **Respect them as-is.** Don't modify anything. Don't re-generate anything.
- ✅ Depending on the storage mode:
  - **Project file**: ask the user to upload them into the project
  - **Stateless**: they stay in the conversation
- Save:
  - `[CONFIG] Template filename: <template_filename>`
  - `[CONFIG] Templates source: user_provided`

**Case B: The user did NOT provide templates**
- ✅ Briefly inform: "No template provided, I'm generating the default templates in Hybrid mode."
- ✅ **Do NOT ask which style to choose.** Hybrid mode is the default, full stop.
- ✅ Run:
  ```bash
  python scripts/generate_templates.py --style hybrid /mnt/user-data/outputs/
  ```
- Present the 2 files with `present_files`
- Depending on the mode:
  - **Project file**: ask for upload into the project
  - **Stateless**: keep locally
- Save:
  - `[CONFIG] Template filename: Cover_letter_template.docx`
  - `[CONFIG] Templates source: generated_hybrid`

### STEP 5 — Final recap

Build a JSON dict with all the data, then run:
```bash
python scripts/setup_workflow.py final_recap --json '<json_string>'
```

Display the result **as-is**.

The JSON must contain: `full_name`, `street`, `postal_code`, `city`, `email`, `phone`, `linkedin`, `storage_method`, `cv_filename`, `signature_filename`, `template_filename`, `templates_source`.

## Supported user commands

### Viewing
- `"Show my config"`:
  1. `memory_user_edits view`
  2. Filter `[CONFIG]` and `[CANDIDAT]` lines
  3. Build the JSON and run `setup_workflow.py final_recap`

### Updating personal data
- `"Change my [field]"`:
  1. `memory_user_edits view` for the line number
  2. Ask for the new value
  3. `memory_user_edits replace`

### Updating files
- `"Update my CV"`: ask for the new file, update according to the storage mode
- `"Update my signature"`: ask for the new image, encode to base64, update
- `"Update my templates"`:
  - If the user provides new templates → respect them
  - Otherwise → regenerate with `generate_templates.py --style hybrid`

### Storage migration
- `"Switch to [mode]"`: only two modes exist (project file ↔ stateless). Switching is just updating `[CONFIG] Storage method` — the files stay where they are; for stateless, clear the file-reference keys (`[CONFIG] CV filename`, etc.). No data migration, no Drive.

### Reset
- `"Reset my config"`:
  1. **Confirm explicitly** with the user (destructive action)
  2. `memory_user_edits view`
  3. Delete all `[CONFIG]` and `[CANDIDAT]` entries (descending order)

## Preferences (candidate-suite panel) — guided flows

The preferences panel (`scripts/build_preferences.py`, at the suite root) exposes **action buttons** that compose a prompt via `sendPrompt`. On receiving one, follow the flows below. The only persisted config field for storage is the signature's:

```
[CONFIG] Signature persistence: project | session
```

The **tracker** mode (persistent project file vs session-only view) is chosen per action via the buttons below — it is **not** a stored toggle, and there is **no** `Drive integration` field (Drive removed).

**Localization (surface contract, LNG-2 S2 — option B).** The panel's HTML structure, its `sendPrompt` directives and its `print()` are **English-canonical** (never localized). To render its **visible labels** in another interface language, resolve it (remembered preference if any, else the conversation language), set `--ui-lang <code>`, and pass the **exact `LABELS_EN` key set** (defined in `build_preferences.py`) translated via `--labels-json` (the script errors out on any missing/extra key); omit `--labels-json` for English. This surface carries **no language selector** (interface language isn't a candidate-config field — nothing is stored); the memory-preference precedence propagates it, and the switching affordance lives on the entry selection widget.

> ✅ **SIG-1 reconciliation (0.4.1):** STEP 3 describes the current model — signature = **base64 `.txt` file dropped into the project files**, read by its name via `resolve_files.py`. The `[CONFIG] Signature base64` key (signature in memory) is **deprecated**. *(The former "3 storage modes" legacy and the Drive sections are now resolved: Drive removed, `migration.md` deleted, `storage_options.md` reduced to the 2 live modes.)*

### [1] Signature — "No, this conversation only"
Set `[CONFIG] Signature persistence: session`. Confirm in one sentence. For each signed letter, ask for the image, encode it for that letter only (no storage).

### [2] Signature — "Yes, via a project" (guided)
1. **Check the project context.** Outside a project, simply explain that a project is needed (it's the only place where a reusable file can be dropped), and offer the step-by-step for creating one.
2. **Encode.** Ask for the image (or an already-prepared base64). Run `scripts/setup_signature.py --input-path <image>`: it resizes if needed (threshold ~15,000 chars / ~600 px width) then encodes. If the input is already base64 under the threshold → passthrough; above → decode, resize, re-encode.
3. **Return.** Write the `.txt` named `<basename>_<ext>_b64.txt`, present it via `present_files`, and explain to the user that they must **drop it into the project files themselves** (the module reads the project but cannot write to it).
4. **Remember.** `[CONFIG] Signature persistence: project` + `[CONFIG] Signature filename: <name of the .txt>`.

### [3] Tracking — "Persistent (project file)" (guided) — `track_project`
1. **Check the project context.** Persistence requires a project (the only place a reusable file can live). Outside a project, explain how to create one; enable nothing until ready.
2. **Set up the tracker.** If no tracker file exists, `modules/application-tracker/scripts/manage_tracker.py init` → it builds the timestamped `Applications_Tracker_YYYYMMDD_HHMM.csv` and **prints the path**.
3. **Explain the ritual** (no Drive, no connector): the module **reads** the project but cannot write to it — so it regenerates the versioned CSV, presents it via `present_files`, and **the user adds it to the project and deletes the previous version** (identified by its unique timestamped name). This manual add is what grants **persistence AND consent**.
4. **Offer the dashboard** (`modules/application-tracker/scripts/build_dashboard.py`) and **the guide** (`build_guide.py`).

### [4] Tracking — "Session view only" — `track_session`
No persistence: a **read-only session snapshot**. Claude scans the conversations / reads what's provided and renders a read-only dashboard for this session. Nothing is stored; confirm in one sentence.

### [5] Tracking — "See the guide" — `track_guide`
Purely informative (changes no setting): generate and display `modules/application-tracker/scripts/build_guide.py` — where the tracker file lives (project files), what the dashboard does, and how to update it (regenerate the versioned CSV, add it to the project, delete the old one).

## Available scripts

| Script | Usage |
|--------|-------|
| `setup_workflow.py` | Critical outputs (questions, recap) |
| `generate_templates.py --style hybrid [output_dir]` | Default EN+FR templates |
| `setup_signature.py --input-path <image>` | Image → base64 `.txt` file `<basename>_<ext>_b64.txt` (auto-resize), to drop into the project files |
| `migrate_storage.py encode_signature <image>` | (legacy) JPG/PNG → base64 file — prefer setup_signature.py |
| `migrate_storage.py copy_to_outputs <source>` | Copies to outputs |
| `migrate_storage.py list_project_files` | Lists project files |

## References (for technical details)

- `references/storage_options.md`: the 3 storage modes in detail
- `references/migration.md`: migration procedures between modes
- `references/memory_format.md`: exact format of the memory entries
- `references/data_extraction.md`: extraction from the CV

## Important rules

- **Always `view` memory before `remove`/`replace`** (line numbers can change)
- **Always validate** with the user before a destructive action (reset, migration)
- **Mandatory prefixes**: `[CONFIG]` (technical) and `[CANDIDAT]` (personal)
- **Forbidden sensitive data**: SSN, passwords, account numbers
- **If templates provided by the user**: respect them as-is, don't modify
- **If templates not provided**: generate the defaults in Hybrid, don't ask for the style
- **Scope**: configuration ONLY (cover-letter generation = a separate module)
- **For critical outputs (steps 1, 5): ALWAYS run setup_workflow.py and display the result as-is**
