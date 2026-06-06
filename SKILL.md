---
name: candidate-suite
version: 0.17.0
updated: 2026-06-06
description: "All-in-one suite for preparing job applications and interviews, bundled as a single module: cover letter, interview prep, application summary, strategic playbook, one-page reference card, and application tracking, plus candidate-profile configuration. Single entry point: it shows a selection widget, then generates each deliverable through its sub-module's script. Use whenever the user wants to apply for a role, prepare an application or an interview, get tools for a job posting, configure the skill or update their CV or profile, generate a cover letter, produce a summary, playbook, or reference card, track applications or view their application dashboard (e.g. asking where their applications stand), or makes any open-ended request for job-application help. These are intents, not required wordings: match the user's intent regardless of the language the request is written in."
---

# candidate-suite

`Version 0.16.6 — 2026-06-05`

**candidate-suite** is an **all-in-one** suite: a single module to install that bundles the orchestrator (this root) and 7 specialized sub-modules. Faced with a job-application request, this skill shows a **selection widget** that turns the vague request into an explicit command, then generates each deliverable through the relevant sub-module's script. **Nothing is written by hand.**

## 🗺️ Suite architecture — path convention (READ FIRST)

This skill is a container. The orchestrator lives at the root; the specialized workflows live in `modules/<name>/`, each with its `GUIDE.md` (detailed instructions), its `scripts/`, and optionally its `assets/` / `references/`.

**Path rule, everywhere:**
- Root scripts: `python scripts/<script>.py …`
- A module's scripts: `python modules/<name>/scripts/<script>.py …`
- A module's resources (templates, references): `modules/<name>/assets/…`, `modules/<name>/references/…`
- For a workflow's details, read `modules/<name>/GUIDE.md` first. The paths in it are relative to the module folder → prefix them with `modules/<name>/`.

The modules' Python code is unchanged: each script receives all its paths as arguments, nothing is hard-coded. Moving folders therefore breaks no script.

### Module map

| Deliverable / need | Module | Main script |
|---|---|---|
| Profile / CV / signature / templates config | `modules/candidate-config` | `setup_workflow.py`, `setup_signature.py`, `generate_templates.py` |
| Strategic playbook | `modules/strategic-playbook-generator` | `generate_playbook.py` (+ `md_to_pdf.py`) |
| Application summary | `modules/application-summary-generator` | `generate_application_summary.py` (+ `md_to_pdf.py`) |
| Interview prep | `modules/interview-prep-generator` | `generate_interview_prep.py` (+ `md_to_pdf.py`) |
| Cover letter (.docx) | `modules/cover-letter-generator` | `fill_cover_letter.py` (templates in `assets/`) |
| One-page reference card | `modules/quick-reference-generator` | `generate_quick_reference.py` (+ `md_to_pdf.py`) |
| Application tracking | `modules/application-tracker` | `manage_tracker.py`, `build_dashboard.py` |

## ⚠️ WHY THIS WIDGET — DO NOT IMPROVISE

Open-ended application requests have historically triggered improvisation (writing by hand, inventing, over-delivering). Nothing is generated until the user has specified their choices in the widget, which then composes a closed, directive prompt.

Absolute rule: faced with an open-ended application request, **show the widget first**.

## Language (principle)

**Language is not stored as a candidate preference, and there is no frozen default.** Needs resolve from **two rules + one override**, with a **memory-preference precedence** on top:

- **Working language = the conversation language.** Reply in — and default the **help-doc deliverables** (playbook, application summary, interview prep, reference card) to — **the language the user writes in**. Nothing is stored. (This is what makes "a German user in Germany" work with no configuration.)
- **Interface language = the conversation language too.** The selection widget and the UI render in it. The widget carries a language selector (the 11 official Claude interface languages + "Other…"); **changing it re-displays the widget** in the chosen language (STEP 3). This control does **not** affect the deliverables language — the two axes are independent. Other **rendered surfaces** (the tracking dashboard, the preferences panel, the tracker guide) localize their visible labels the same way — the model supplies the exact label set via `--labels-json`, structure/`sendPrompt`/`print` stay English-canonical — but carry **no selector** (LNG-2 S2, option B): the remembered (else conversation) language propagates to them, and the entry widget is where the user switches it. Like the entry widget, **each of these rendered surfaces also prints a canonical text floor** to stdout (`[TEXT FALLBACK …]`) to relay as a parallel text channel: **unconditionally** for the silently-failing surfaces (preferences panel, tracker guide — a blank render is undetectable), **reactively** for the dashboard (observable hang: show the board, relay the printed table only if it does not render). The content is the **script's** output — never regenerate it from memory.
- **Letter language = the offer's language, detected by the model and confirmed** (see STEP 4, sub-step 3-bis). Volatile, per application.
- **Override (one-off):** the user may steer the help-docs to the job's language instead (e.g. rehearsing an English-language interview in English). A per-run choice, never a stored preference.
- **Ambiguity → ask.** Never fall back to a frozen preference or a hardcoded default.
- **Memory-preference precedence.** If the user has asked Claude to remember a language choice (memory active) — for the deliverables and/or the interface — that stored preference **takes precedence over auto-detection, silently** (no re-ask), and pre-selects the widget's language selector. The preference lives in **Claude's memory**, never in the skill config (the skill stores no language key); "forget that preference" reverts to detection.

How a chosen language is *realized* (register, idiom, dates, numbers, spacing, labels; and for the letter, salutation / subject / closing) is governed by the style resources `modules/cover-letter-generator/references/language_style_generic.md` (all deliverables) and `…/references/letter_conventions.md` (letter only). There is **no** keyword/accent detector and **no** per-language table: the model reads the offer directly.

## Workflow

### STEP 1 — Config + memory items
1. `memory_user_edits view` → retrieve the candidate profile (`[CANDIDAT]`, `[CONFIG]`).
2. If config is missing → follow `modules/candidate-config/GUIDE.md` first, then come back here.
3. **Detect the memory state**: data present → memory active; empty / paused → inactive. This drives the widget (editable block vs "memory paused" message, "remember" checkbox, signature options).
4. **Resolve the files (CV + signature)** — SIG-1:
   ```bash
   python scripts/resolve_files.py \
     --cv-name "<[CONFIG] CV filename>" \
     --signature-name "<[CONFIG] Signature filename>"
   ```
   The persistent signature lives in a **project file** (base64 `.txt`), **never in memory**: memory is capped at 500 characters, far below the ~14,000 of a base64 signature — so the `[CONFIG] Signature base64` key is **deprecated**. The resolver tries, in order, session upload → project file (**no Google Drive** — 0.4.2, cf. DRV cluster), and returns a status for each file: `present_upload` / `present_project` / `referenced_missing` / `none`. If the signature is `present_*`, the letter can be signed **without re-upload** (see STEP 4.2); if `referenced_missing`, flag it without blocking. For the widget: `--signature-in-memory true` if the signature status is `present_project` or `present_upload`, otherwise `false`.
5. **Gather the relevant memory items** for the widget block (if memory is active): name/profile, CV, address, ongoing applications, preferences. Each item has `id`, `label`, `value`. Present as "non-exhaustive," never as an audit.

### STEP 2 — Already-produced deliverables
Look in `/mnt/user-data/outputs/` for already-generated deliverables (`Strategic_Playbook_*`, `Application_Summary_*`, `Interview_Prep_*`, `Cover_Letter_*`, `Quick_Reference_*`) to pre-check / grey out the boxes.

### STEP 3 — Show the widget
```bash
python scripts/build_selector.py --output-path /home/claude/widget.html \
  --memory-json '[{"id":"profile","label":"Profile","value":"…"}, …]' \
  --memory-active true \
  --signature-in-memory true \
  --already-done-json '["strategic_playbook", …]' \
  --ui-lang <interface-language code> \
  --labels-json '{ …LABELS_EN key set, values in the interface language… }'
```
**Interface language (surface contract).** Resolve the interface language = the **remembered preference** if any (memory), else the **conversation language**; set `--ui-lang` to its code. If it is **English**, omit `--labels-json` (the script's English-canonical labels are used). Otherwise translate the **exact `LABELS_EN` key set** (defined in `build_selector.py`) into that language and pass it as `--labels-json` — the script enforces the exact key set (errors out on any missing/extra). The widget **structure**, its `sendPrompt` **directive** and its `print` output stay **English-canonical**; only the visible labels are localized. **If the user changes the widget's language selector, re-run STEP 3** with the new `--ui-lang`/`--labels-json` (deliverables language unchanged).

Read the produced HTML, display it with the visualization tool, **then stop**: wait for the choices and the Generate click. Generate nothing before then.

**Text-floor (robustness, unconditional).** `build_selector.py` also prints to stdout a canonical, numbered deliverable list (marked `[TEXT FALLBACK — relay this numbered list to the user]`). The widget is a harness-rendered surface that can come out as a blank skeleton and **fails silently** (nothing signals it), so **always** relay that list to the user as a parallel text channel — in the interface language, on **every** run, even when you expect the widget to work — and invite them to reply with the item numbers (e.g. "1 and 4"). The list is the **script's** output: relay it, **never** regenerate it from memory (wrong order / labels / omissions are exactly what the floor prevents). The widget is an **additive** layer on top of this floor, never a replacement: do **not** suppress the list when you think the widget will work — you cannot detect an empty render, so the accepted cost is showing both. A numeric/text reply is a **first-class input, equal to the Generate click** (handled in STEP 4).

### STEP 4 — Handle the composed prompt
Input arrives one of two **equivalent** ways: (a) the **Generate click** — the widget sends (via `sendPrompt`) a visible message: chosen deliverables, posting, possibly modified candidate data, signature instruction if the letter is checked; or (b) a **text-floor reply** (STEP 3) — the user answers with item numbers, which you map to deliverables via the imposed order printed by `build_selector.py`, asking for the posting / signature if not already provided. Both are handled identically. On receipt:

1. **"SAVE to memory" instruction** → apply via `memory_user_edits replace`. **"ONE-OFF use"** → don't touch memory.
2. **Signature instruction** → follow exactly. Default source: the **file resolved in STEP 1.4**. If the signature is `present_project` (or `present_upload`), pass its path to `fill_cover_letter.py --signature-path <resolved path>` → signed letter **without re-upload**. The session upload (`present_upload`) takes precedence if the user has just attached a signature. Making the signature persistent = placing the base64 `.txt` in the **project files** (manual user action), **not** in memory (`[CONFIG] Signature base64` deprecated). `setup_signature.py` is still useful for producing the base64 `.txt` from an image. If the status is `referenced_missing` / `none` and the user wants a signed letter, ask them to attach / place the signature.
3. **Single global analysis**: read CV + posting, web search if available, produce the substantive analysis in one pass. **Anti-freeze guardrail (FIX-FREEZE):** use only the CV **resolved in STEP 1.4** (`present_upload` / `present_project`). If the CV is `referenced_missing` / `none`, **stop and ask the user** to attach their CV (or place it in the project files) — **never** try to read it through a connector / Google Drive. A connector call can't be bounded by instruction: it can hang with no return and freeze the session (this is the root cause of FIX-FREEZE).

   **3-bis. Resolve the run language** (after the single global analysis, before generating anything). The analysis already read the offer; as a **free by-product of that read**, the model identifies the offer's language — more reliable than any keyword heuristic, and the model's strong suit.
   - **Letter on the bill?** If `cover_letter` is among the chosen deliverables, resolve the **letter language**: *(resume path)* if this application is already in the tracker, read its `language` column — *meaning the confirmed offer/letter language* — treating the read as **opportunistic, never blocking** (FIX-FREEZE: if the tracker isn't readable, skip to detection, don't stall); a value present → **silent reuse**, no re-ask. *(Fresh path)* present the language **the model detected from the offer** as a pre-filled hint and **confirm once** ("I'll write the letter in <detected language> — correct?"). The confirmation is the **deterministic anchor** that turns the agnostic read into a concrete value. **Re-ask only on a signal:** offer changed, explicit request for another target language, or genuine ambiguity.
   - **Help-docs language:** default to the **working / conversation language**, unless the user applied the one-off override to the job's language. Not stored (volatile).
   - **Fix the concrete value(s) for the run** (detection → confirmation → frozen value); confirm **once**, never deliverable by deliverable.
   - **Circulate the value:** pass it as `--language <code>` to each script below (letter = confirmed **offer** language; help-docs = **working** language, or the override). any ISO 639-1 code works (**L6**): there are no per-language assets anymore — the scripts are language-agnostic and the model supplies the labels/strings in the run language.
   - **Beyond `--language` (labels contract — L6):** each deliverable's **structure labels** are produced **by the model in the run language** and passed to its script — `--labels-json '{...}'` for the four `.md` generators (the script enforces the **exact** key set — no invented/omitted section), and `subject_label` / `greeting` / `closing` in the letter's `--data-json`. See each module `GUIDE.md` + `references/language_style_generic.md`.
   - **Persist (letter only, opportunistic):** when the letter language was confirmed and the application is (or is being) added to the tracker, write it to the tracker `language` column for silent reuse on resume. Letter-only without a tracker → persist nothing. Help-doc language is **never** persisted.
4. **Generate each chosen deliverable**, in the mandatory order below, **through the module's script** (never by hand). Read the module's `GUIDE.md` for the details, and prefix its paths with `modules/<name>/`:
   - `strategic_playbook` → `modules/strategic-playbook-generator`
   - `application_summary` → `modules/application-summary-generator`
   - `interview_prep` → `modules/interview-prep-generator`
   - `cover_letter` → `modules/cover-letter-generator` (templates: `modules/cover-letter-generator/assets/`)
   - `quick_reference` → `modules/quick-reference-generator` (**always last among the documents**: it condenses the others)
   - `add_to_tracker` → `modules/application-tracker` (**always at the very end**) — conversation marker **`YYYY-MM-DD ◆`** (today's local date for the candidate, **no time**, no UUID at write time), key **(company, position)**; persistence via the **project-file ritual**. **The filename is built by the script** (`manage_tracker.py … --output-dir /home/claude`, never a hand-composed `--output-path`): it generates `Applications_Tracker_YYYYMMDD_HHMM.csv` (no dashes in the date, aligned with the app's normalization) and **prints the path** → present **that** file via `present_files`, the user adds it to the project and deletes the old one; **no connector**. Details: its `GUIDE.md`.
5. Respect the dependencies (reference card after the documents it condenses).
6. No intermediate validation between deliverables.
7. Offer PDF export at the end, then, if the user agrees, generate the PDFs of **all** produced deliverables:
   - `.md` deliverables (playbook, summary, interview prep, reference card) → the relevant module's `md_to_pdf.py`;
   - **cover letter `.docx`** (#7) → `python modules/cover-letter-generator/scripts/docx_to_pdf.py --input <letter.docx> --output <letter.pdf>` (LibreOffice; if unavailable the script exits with code 3 and the letter stays usable as `.docx`). Don't forget the letter in the PDF batch.
8. **Suggest the canonical conversation title** `📋 YYYY-MM-DD - Company - Position`, **systematically as soon as a deliverable is generated from a job description** — whatever the flow: full guided flow **OR** creation of a single specific document. The trigger is the **presence of a job description** (so not pure configuration actions: profile, signature, which are tied to no posting). **Title date = date of first activity if the application is already tracked, otherwise today's date** (candidate's local date — same locale resolution as the tracker timestamp) → a **time-stable title** (resuming on another day suggests the same title). It is a **suggestion for the user to apply**: the assistant **cannot rename** the conversation itself. This marker makes it findable in the **sidebar** (on desktop, conversation links aren't clickable). If the conversation already has this name, the suggestion lands correctly — zero cost.

### STEP 5 — Closing recap + re-run
Before offering a re-run, give a **closing recap**:

**Level 1 — always (this run):** list the deliverables produced in this run with their **download links**; explicitly name the standard types **not yet produced** (playbook, summary, interview prep, letter, reference card) and offer to generate them; remind of the free-text shortcut ("just generate the reference card").

**Level 2 — if a tracker exists (cross-cutting):** from the tracker (column `deliverables` + dated `conversation` markers), recall what has already been done for this application across conversations.

**Links to a conversation in the recap:** use `https://claude.ai/chat/{uuid}` — clickable **everywhere** (in-app on desktop, tab on web), unlike the dashboard (Link column clickable on web only). Possible only when the **UUID is known** (already-refreshed entries); otherwise cite the dated marker without a link. Never `claude://`.

Then **re-run**: re-display the widget (STEP 3) with the produced deliverables marked "already generated," and offer "Do you want to generate other documents, or start over by changing your choices?".

## Targeted requests (no widget)
If the user explicitly asks for **a single** deliverable or a config action ("just generate the cover letter," "update my CV," "where do my applications stand"), go straight to the relevant module via its map above and its `GUIDE.md`, without going through the widget.

## Missing mandatory data → ask, never invent
If a piece of data classified as **mandatory** (address, full name, email, company…) is missing from both memory AND the CV, **ask the user** for it. Never fill it with an invented placeholder, and a placeholder on an outgoing document is a fault. `fill_cover_letter.py` enforces this **structurally** (LNG-2 S3b): it refuses (exit 2) any critical field that is empty or equals the language-neutral sentinel `__MISSING__` — no multilingual word-list. The company name, however, is inferred from the posting by Claude (reliable reading) rather than asked for.

## No non-standard deliverables
The suite produces exclusively the **6 standard deliverables** of the widget. No "suggestions" area. If a relevant enhancement appears, **propose it verbally after generation**, never via an upfront checkbox.

## Technical limits
- The widget doesn't read memory: Claude fills the block via `--memory-json`.
- The Generate button sends a prompt (`sendPrompt`) that Claude then handles; the widget runs no script.
- This skill's triggering depends on Claude (no skill self-launches). On an occasional miss, explicitly invoke "use candidate-suite."

## Scripts (root)
| Script | Usage |
|--------|-------|
| `resolve_files.py --cv-name … --signature-name … [--uploads-dir …] [--project-dir …] [--output-path …]` | Locates CV + signature (upload → project; **no Drive**) and returns a JSON status (`present_upload`/`present_project`/`referenced_missing`/`none`). Core of SIG-1. On `referenced_missing`, the orchestrator **asks for the file** (never a connector call). |
| `build_selector.py --output-path W.html [--memory-json …] [--memory-active true/false] [--signature-in-memory true/false] [--already-done-json …] [--ui-lang code] [--labels-json '{…}']` | Generates the selection widget (English-canonical base; `--labels-json` localizes the visible labels in the interface language, exact key set) |
| `build_preferences.py --output-path W.html [--config-json …] [--sig-current project|session|none] [--tracker-current project|session|none] [--ui-lang code] [--labels-json '{…}']` | Generates the preferences panel (profile + file status + signature/tracker toggles; English-canonical base, `--labels-json` localizes the visible labels, exact key set, no selector) |

## References
- `references/assistant_flow.md`: details of the flow and the composed-prompt format
- `modules/<name>/GUIDE.md`: detailed workflow of each module
