# Changelog — candidate-suite

Format inspired by "Keep a Changelog." Simplified semantic versioning:
fix → patch (`0.3.x`); feature addition → minor (`0.x.0`).

> **Language note.** Entries up to and including **[0.7.0] — 2026-06-02** are written in
> **French**, the language in which the suite was originally developed. From the public-diffusion
> transition (**[0.8.0]**) onward, new entries are written in **English**. Past French entries
> are kept as-is (historical record) and are not retranslated. Section keywords map as:
> Ajouté → Added · Modifié → Changed · Corrigé → Fixed · Déprécié → Deprecated ·
> Supprimé → Removed · Sécurité → Security · Validé → Validated · Documentation → Documentation.

## [0.19.0] — 2026-06-06

### Changed
- **DRV-7 (option A) — dashboard conversation column redesigned (web).** Each conversation now renders as a compact glyph instead of a date label: `↗` linked (clickable, opens the conversation), `◆` current conversation (non-clickable — no self-link possible), `✗` deleted (non-clickable, greyed). Each linked conversation is individually clickable (already the engine behaviour; only the visual token changed). Conversations are ordered **most-recent-first**. Web tooltip = the full date, plus the single captured title (`realTitle`) attached to the **most-recent linked** conversation only — there is no per-conversation title in the data model yet, so older conversations show date-only rather than a misattributed title. Legend updated to the three glyphs (existing label keys reused — no label-contract change). `isRowDeleted()` (whole-row greying) is unaffected: it keys off marker state, not rendering.
- **Desktop rendering kept as-is** (full selectable marker to find/copy in the sidebar): a clickable glyph would open the browser, and the no-link constraint there is unchanged. The most-recent-first ordering applies to both surfaces.
- **Glyphs are Unicode** (`↗ ◆ ✗`), recolourable and surface-safe — the dashboard has no icon webfont (it already uses `◆/✗/📋/↻`). Robustness floor: no dependency on an unguaranteed font.

### Notes
- Per-conversation title/deliverable mapping (so the tooltip could show *which* deliverable lives in *which* conversation) requires extending the data model (a title per conversation marker, captured at reconcile). Tracked as a separate item; out of scope here. Once it lands, these same glyphs gain real per-conversation titles for free.
- Behavioural verification: renderConv exercised under Node (11 assertions — states, ordering, title attribution, non-clickable ◆/✗, desktop unchanged). CI guard (`tests/test_build_dashboard.py`) asserts the glyph/ordering wiring in the generated HTML, since the harness has no JS engine.



### Changed
- **Cover-letter template de-French-ified (minimal pass).** The place-and-date line was a hardcoded `{{SENDER_CITY}}, {{DATE_LETTER}}` composite — a continental/French tic (mandatory city + comma) baked into the layout. It is now a **single `{{DATE_LINE}}` slot the model composes in the target locale's convention** (e.g. `Paris, le 6 juin 2026`, `New York, June 6, 2026`, or a date-only line where the locale omits the city). The date was already model-supplied, so this only merges two values into one model-composed line — no script-owned formatting handed over. `sender_city` stays a slot for the sender address block. Body alignment (justify) left as-is: acceptable for the majority of the 11 default languages, and changing it would swap one bias for another. Regenerated `assets/Cover_letter_template.docx` accordingly.
- **Data contract:** `--data-json` now carries `date_line` instead of `date_letter`. Updated `fill_cover_letter.py` (placeholder map, required fields, docstring), `generate_templates.py` (template + placeholder list), the cover-letter `GUIDE.md`, the gallery (`tooling/build_samples.py`) and the test fixture. No migration: the value was always composed per letter by the model, never stored.

### Documentation
- **`letter_conventions.md`:** new `DATE_LINE` section (model composes place+date per locale; city optional for date-only locales) and a **"Layout & direction" known-limitation note** — the template is LTR; for an RTL target language reachable only via the "Other… (ISO code)" option (Arabic, Hebrew, Persian, Urdu…), the block layout is not mirrored (content correct, arrangement LTR). None of the 11 default interface languages is RTL, so this never affects them. Closes the cover-letter localization topic: text conventions were already agnostic (model-driven for any language); only the layout's continental tic needed neutralizing.



### Added
- **`manage_tracker.py --timezone <IANA>`** on every file-writing subcommand (`init`, `upsert`, `bulk`, `batch-status`, `reconcile`). The filename timestamp zone is now a parameter the model resolves from the candidate locale, instead of a hardcoded constant. New `resolve_timezone()` helper: validates the IANA name via `zoneinfo`, and on an unknown/malformed name warns on stderr and falls back to `Europe/Paris` — a filename op never aborts (robustness floor). No city→zone table (mapping a place to its zone is a model task, same reason LNG-1 dropped the language tables).

### Changed
- **Locale resolution chain documented (LNG-1 / L1 realized).** The tracker timestamp and the model-composed dates (conversation `◆` marker, conversation-title suggestion) now follow one chain: profile `City` → else host-provided session location → else `Europe/Paris`. The model maps the locale to an IANA zone and passes `--timezone`; the script stamps the instant (model = zone, script = clock). Wired in `SKILL.md`, `candidate-config/GUIDE.md` (locale block reworded — the previous text wrongly implied `zoneinfo` maps a city name) and `application-tracker/GUIDE.md`.

### Fixed
- **DST-naive snippet removed from `application-tracker/GUIDE.md`.** The conversation-marker date instruction still told the model to compute the date with a fixed `timezone(timedelta(hours=2))` offset (wrong half the year). Replaced with a `zoneinfo`-based one-liner on the resolved IANA zone (DST-handled). Closes the residual the L1 code fix (`0.8.0`) had left in the doc.
- **Hardcoded "Paris" delinked from all instruction surfaces.** Stray "Paris time" / "Paris date" references in `SKILL.md`, `application-tracker/GUIDE.md` and the `manage_tracker.py` usage comment now read "candidate's local date/time". Example candidate data (fictional Paris address/city) is unchanged — it is illustrative, not logic.



### Changed
- **EN-canonical code sweep completed (closes the "infra 100% EN" gap).** Every remaining runtime `print`/error/help message still in French was translated to English across the 5 generators, the 4 `md_to_pdf.py`, `docx_to_pdf.py`, `fill_cover_letter.py`, `manage_tracker.py` and the 3 candidate-config setup scripts. A two-pass scan (accents **and** accent-free French in string literals) now returns zero residuals — the earlier accent-only claim had missed accent-free French. Stray French JS identifier renamed (`repere` -> `marker`) in `build_dashboard.py`. One French fragment kept on purpose: a comment in `fill_cover_letter.py` quoting the removed `"a completer"` placeholder word-list (historical record).

### Fixed
- **Quick-reference `key_stats` renders structured items.** The loop assumed a list of strings and dumped raw Python dicts when the model supplied `{stat, context}` objects; it now tolerates both shapes (mirrors `pick()` for `top_points`): `- **<figure>** -- <context>`.
- **Stale French tracker status example.** `manage_tracker.py` docstring `"status":"Entretien"` -> EN-canonical `"Interview scheduled"`.
- **Acceptance gallery: five identical Lorem paragraphs.** `tooling/build_samples.py` `lorem()` always restarted from the same word, so the five body paragraphs were prefixes of one another. It now takes a per-paragraph `start` offset -> five visibly distinct paragraphs at the same ratio targets (15/22/26/22/15).
- **Acceptance gallery: invisible signature.** `signature_b64()` returned an 8x4 px PNG, so the *signed* letter variant showed no visible signature. It now draws a real cursive paraphe (quadratic Beziers, RGBA, hand-encoded PNG, stdlib-only) -- the signed sample shows a legible signature.

### Documentation
- **GUIDE label de-freezing.** The four `.md`-generator GUIDEs prescribed per-language label phrases (e.g. `title -> FR "Playbook strategique"`), contradicting the surface contract. They now describe each `title` by its function and tell the model to render it idiomatically in the run language without transliterating an English label; the frozen `--title "..."` examples are neutralized to `"<deliverable title>"`.
- **Recruiter/company extraction doc reconciled.** `cover-letter-generator/GUIDE.md` rule #3 still said "always use the dedicated script", contradicting STEP 4 (model-driven, no script) and the removal note. Reconciled to model-driven extraction.

### Tests
- **TST-1 updated in the same commit** (gate stays green): the quick-reference gallery sample now feeds `key_stats` as `{stat, context}` so the acceptance gallery exercises the new rendering; added tests for dict/string `key_stats` rendering, five distinct Lorem paragraphs, and a visible (non-placeholder) sample signature.

### Validated
- 20 scripts compile; FR residual scan (accents + accent-free) = 0; **115 tests pass** (3 new); E2E cover-letter test confirms floating-signature embedding (`word/media`, `wp:anchor`) and five distinct paragraphs.

## [0.16.5] — 2026-06-05

> Note — version `0.16.4` was consumed by a release **tag** publishing the acceptance gallery with the skill left unchanged at `0.16.3` (release asset `candidate-suite-0-16-3.skill`). The skill version resumes at `0.16.5`; no skill `0.16.4` was ever published.

### Fixed
- **Selection widget now prints a text fallback (robustness floor), like the other rendered surfaces.** `build_selector.py` was the only widget surface shipping without the canonical `[TEXT FALLBACK …]` stdout block that `build_preferences`, `build_guide` and `build_dashboard` already carried — so a silent blank render of the selector (observed at low model effort) left no text recourse. It now prints the canonical, numbered deliverable list (imposed order, localized labels, "already generated" tag) on every run, relayed unconditionally as a parallel text channel; a numeric/text reply is handled exactly like the widget's Generate click. `SKILL.md` STEP 3/4 wired accordingly. No `LABELS_EN` key added — surface contract unchanged.

### Changed
- **Harmonized the tracker-guide floor to the silent-failure doctrine.** `build_guide.py` previously read "if it does, relay" (operationally undetectable for a silent failure); it is now UNCONDITIONAL but deliberately LIGHT — a brief outline (tabs in order) on every run plus a ready-made prompt the user can send to expand the full guide on demand, instead of dumping the full prose by default.

### Documentation
- `SKILL.md`: the rendered-surfaces note now states that preferences/guide/dashboard also print a text floor — unconditional for silently-failing surfaces, reactive for the dashboard (observable hang).

## [0.16.3] — 2026-06-04

### Changed
- **Adopted `ruff` for linting and formatting (CI quality stage).** The package now passes `ruff check` and `ruff format`. Behavior-neutral: lint cleanup (removed unused imports, dropped `f` prefixes on placeholder-less f-strings, removed a stray walrus assignment, renamed an ambiguous loop variable) plus a one-time formatting pass across all 20 scripts. No logic changed; all 20 scripts compile. `E402` (import-not-at-top) is ignored by config — see `pyproject.toml`.

### Added
- `pyproject.toml` — central `ruff` (lint + format) and `pytest` configuration (repo meta; not part of the packaged skill).

## [0.16.2] — 2026-06-04

### Changed
- **Placeholder identity unified (completes the [0.16.1] neutralization).** The configuration references still carried a second fictional candidate alongside the one used in the naming examples. The whole package now uses a single fictional candidate — `Jordan Lee-Carter` (a compound, hyphenated surname, which also carries the name-disambiguation / hyphenation lesson into the config docs) — across `candidate-config/references/` (`data_extraction.md`, `header_styles.md`, `memory_format.md`): example name, CV filename, signature filename, email, and LinkedIn slug. `Jane Smith` is kept deliberately as the distinct *recruiter* placeholder (a different role). Docs only, zero behavior change.

### Validated
- Census: a single candidate identity package-wide; the only remaining `Jane` is the recruiter placeholder. 20 scripts compile.

## [0.16.1] — 2026-06-04

### Changed
- **Example data neutralized package-wide (DEP-2 closeout — shareable package).** Every illustrative trace of the maintainer's real identity (name, CV filename, postal address, demo employers) was replaced by a neutral fictional candidate and fictional companies, so the `.skill` artifact itself is safe to publish; real data lives only in the user's own project files, never in the package. Scope: docstrings, help text, naming-convention examples, and dashboard/tracker demo rows — no executable logic. The fictional candidate is `Jordan Lee-Carter`; demo/example employers became `Acme Financial Group` / `Globex`, aligned with the `Acme` placeholder already used in the engine's JSON docstrings. Naming examples keep their pedagogical value (a compound hyphenated surname, and a multi-word company with an abbreviation trap). FR address-format examples keep a neutral French street so the formatting lesson is preserved.

### Validated
- Exhaustive census across text surfaces (not word-list detection): zero residual maintainer identity and zero real company name. Positive control confirms the fictional placeholders are consistently in place. 20 scripts compile. Engine logic untouched — no personal data was ever in executable code; this closeout only neutralized docs and examples.

### Notes
- The hard-coded `/mnt/...` and `/home/claude` defaults remain (Claude-environment coupling) — not personal data; they belong to DEP-4 (isolate environment adapters), kept out of this DEP-2 scope on purpose.

## [0.16.0] — 2026-06-04

### Changed
- **`fill_cover_letter.py` placeholder guard → structural sentinel (LNG-2 S3b).** The multilingual placeholder word-list (`à compléter`/`to complete`/`tbd`/`xxxx`/`votre adresse`/… — FR/EN only, brittle elsewhere) is **removed**. A critical field is now refused (exit 2) when it is **empty** OR equals the language-neutral sentinel `MISSING_SENTINEL = "__MISSING__"`. The contract is structural, not lexical: the orchestrator never invents a placeholder (it asks the user); if it must call the script without a mandatory datum, it passes `__MISSING__` for a clean refusal. The block's diagnostics were also rebased English-canonical.
- **`md_to_pdf.py` (quick-ref) 2-column layout → structural marker (LNG-2 S3b).** The "key stats" and "checklist" sections were 2-columned by matching their heading text against an FR/EN title list — language-coupled. Now `generate_quick_reference.py` tags those two fixed-slot headings with a `col2` class via attr_list (`## <label> {: .col2 }`), and `md_to_pdf._columnize_sections` targets `<h2 class="…col2…">` **structurally**, regardless of the (model-supplied) label language.

### Documentation
- `cover-letter-generator/GUIDE.md` ("Mandatory data" note → sentinel contract) and `SKILL.md` ("Missing mandatory data" → structural enforcement) updated to match the code.

### Validated
- 20 scripts compile. `fill_cover_letter`: `__MISSING__` in a critical field → exit 2 (English diagnostic); a valid payload → exit 0; a former FR placeholder ("à compléter") is **no longer** rejected lexically (exit 0) — intended, the guard is now structural. Quick-ref pipeline (md → HTML → columnize) with **German** labels → both `col2` sections become `<table class="cols2">` (2/2), proving the FR/EN title coupling is gone.

### Milestone
- **LNG-2 complete** (S1 tracker engine · S2 the 4 UI surfaces · S3 model-driven extraction + structural sentinels). The whole skill is now English-canonical with localization handled at the surface by the model; French survives only in real persisted data (job titles), translated at the surface.



### Removed
- **`extract_recruiter_info.py` and `extract_cv_info.py` retired (LNG-2 S3a — model-driven extraction).** Both were FR/EN regex/keyword extractors (French postal codes, "Rue/Avenue" street keywords, "À propos de"/"Company:" label patterns, accented name heuristics) — language-coupled and brittle outside FR/EN. Per the standing decision *"recruiter/CV extraction = a model capability, never FR regex"*, reading meaning from a posting or a CV is *fond* (a model task); the scripts owned no *forme*. No code called them (orchestrator-only, via the GUIDEs), so removal is clean. Package now 43 files (was 45).

### Changed
- **Recruiter/company extraction is now model-driven** (`cover-letter-generator` STEP 4): the model extracts `company_name` / `job_title` / `recruiter_name` / `recruiter_title` / `company_city` directly from the posting, in any language, and passes them to `fill_cover_letter.py` (which still validates — empty `company_name` refused, exit 2). The guidance that was attached to the script (reliable company-name read, unknown-recruiter handling, localized recruiter default supplied by the model) is preserved, now unconditioned on a script.
- **CV extraction is now model-driven** (`candidate-config` STEP 2): the model reads the CV directly (`view` / file-reading skill) and extracts the fields itself, in any language. `setup_workflow.py name_check` (3+ word name disambiguation) is unchanged.

### Documentation
- `cover-letter-generator/GUIDE.md` (STEP 4 rewritten model-driven + scripts table, with a "Removed (LNG-2 S3)" note), `candidate-config/GUIDE.md` (STEP 2 read-directly + scripts table), `candidate-config/references/data_extraction.md` (read-directly method, language-agnostic field guide — regex strategies removed), `SKILL.md` (module map: `extract_cv_info.py` dropped from candidate-config).

### Validated
- 20 scripts compile (was 22; two extractors removed). No code references the removed scripts; only the intentional "Removed" note remains in the cover-letter GUIDE.

### Remaining (S3)
- S3b — structural sentinels: `fill_cover_letter.py` placeholder rejection (multilingual word-list → structural sentinel) + `md_to_pdf.py` quick-ref "key figures" 2-column layout (FR/EN heading match → structural marker, coordinated with `generate_quick_reference.py`).



### Changed
- **`build_preferences.py` and `build_guide.py` rebased English-canonical with a localization surface (LNG-2 S2, surfaces 3/4 and 4/4 — S2 complete).** Both follow the same surface contract as `build_selector`/`build_dashboard`: HTML structure, `sendPrompt` directives and `print()` are English-canonical (never localized); all visible labels were externalized (`LABELS_EN` — 17 keys for the preferences panel, 58 for the tracker guide) and are localized by the model via the new optional `--labels-json` (exact key set, errors out on missing/extra); new `--ui-lang` arg accepted as metadata. **Option B** for both: no interface-language selector — the remembered (else conversation) language propagates via the memory-preference precedence, the switching affordance stays on the entry selection widget.
  - **Preferences panel**: the 6 button `sendPrompt` directives (edit / signature / tracker flows) are now English-canonical; the guided-flow prompts read the same on Claude's side regardless of interface language.
  - **Tracker guide**: a prose-heavy surface — each visible text block is a label key; prose values keep their inline markup (`<strong>`, mono `<span>`), injected via `innerHTML`, so the model translates the text and preserves the tags. The legend and document lists are rendered from lead/description label pairs with fixed styling.

### Documentation
- `SKILL.md` (Language principle generalized to all rendered surfaces + scripts table row for `build_preferences`), tracker `GUIDE.md` (scripts table row for `build_guide`) and candidate-config `GUIDE.md` (preferences-panel localization note) updated to match the code.

### Validated
- 22 scripts compile. Preferences panel: English default → no residual French cat-C, English labels + English `sendPrompt` directives; localized run (exact 17-key set) → labels injected, directives still English; partial `--labels-json` → errors out. Tracker guide: English default → no residual French cat-C; localized run (exact 58-key set) → all labels injected, inline markup preserved in prose blocks; partial and extra-key `--labels-json` → both error out.

### Remaining
- LNG-2 S2 done (4/4 surfaces). Next: S3 — model-driven extraction (`extract_recruiter_info` / `extract_cv_info`) + structural-sentinel irritants.



### Changed
- **`build_dashboard.py` rebased English-canonical with a localization surface (LNG-2 S2, surface 2/4).** The HTML structure, every `sendPrompt` directive (Save, Guide, Refresh) and the `print()` output are now English-canonical (Claude-facing, never localized). All visible labels were externalized to `LABELS_EN` (47-key exhaustive set) and are localized by the model via the new optional `--labels-json` — when supplied it must carry the **exact** key set (errors out on missing/extra), so no half-localized UI. New `--ui-lang` arg accepted as metadata. Following **option B** (confirmed with the user): this surface carries **no interface-language selector** — the remembered (else conversation) language propagates via the memory-preference precedence, and the switching affordance stays on the entry selection widget. Statuses remain **canonical English** in the data, the engine and the `sendPrompt`; only their **display text** is localized via the `status_*` labels (option values stay canonical).

### Documentation
- Tracker `GUIDE.md` (workflow A localization note + statuses note + scripts table), `references/tracker_format.md` (English-canonical header labels + a Localization paragraph) and `SKILL.md` (Language principle: rendered surfaces localize via `--labels-json`, no selector) updated to match the code.

### Validated
- 22 scripts compile. Dashboard generation tested: English default (no `--labels-json`) → no residual French cat-C, English labels and directives present; localized run (`--labels-json` with the exact 47-key French set) → labels injected, `sendPrompt`/`print` still English, `STATUSES` values and the per-row `<select>` options stay canonical English (only `STATUS_LABELS` maps the display text); partial and extra-key `--labels-json` → both error out listing missing/extra; `--readonly` (ephemeral) OK. One remaining French JS comment (`/* cache best-effort … */`) translated in passing (cat-A hygiene).

### Remaining (S2)
- 2 surfaces left on the same pattern: `build_preferences`, `build_guide`.



### Added
- **Interface-language selector in the selection widget (LNG-2 S2, surface 1/4).** The widget now carries a language control listing the 11 official Claude interface languages (endonyms) + "Other… (ISO code)". Default = the remembered language preference (memory) if any, else the conversation language. Changing it **re-displays the widget** in the chosen language; the deliverables language is governed separately and is unaffected. Single source of truth for the list (`UI_LANGUAGES` in `build_selector.py`), to be kept in sync with Anthropic by a CI/CD step at deployment (never fetched at runtime).

### Changed
- **`build_selector.py` rebased English-canonical with a localization surface.** The HTML structure, the `sendPrompt` directive and `print()` output are now English-canonical (Claude-facing, never localized). Visible labels default to English (`LABELS_EN`, exhaustive key set) and are localized by the model via the new optional `--labels-json` — when supplied it must carry the **exact** key set (errors out on missing/extra, mirroring the L6 generators), so no half-localized UI. New `--ui-lang` arg pre-selects the language control. `SKILL.md` STEP 3 wires the contract (resolve interface language = memory preference else conversation; translate the exact key set; re-run on selector change).
- **Language principle (`SKILL.md`) extended:** the interface language is now an axis distinct from the deliverables/letter languages, with an explicit **memory-preference precedence** — a remembered choice overrides auto-detection silently (either axis), and is stored in Claude's memory, never in the skill config.
- **Signature directive corrected (SIG-1 reconciliation):** the widget's cover-letter signature instruction no longer references the **deprecated** `[CONFIG] Signature base64` memory key; it points to the resolver (project file / session upload → `--signature-base64`), consistent with the project-file signature model since 0.9.0.

### Validated
- 22 scripts compile. Widget generation tested: English default (no `--labels-json`) → English UI + 11-language selector + English-canonical directive; localized run (`--labels-json` with the exact 36-key set) → labels injected, directive still English; partial `--labels-json` → errors out listing missing/extra; `--ui-lang fr` pre-selects French. No residual French cat-C in the script (only the language endonyms remain, by design).

## [0.11.0] — 2026-06-04

### Changed
- **Tracker status vocabulary is now English-canonical.** `DEFAULT_STATUS` / `DEFAULT_STATUSES` and every status-keyed branch in `manage_tracker.py` and `build_dashboard.py` moved from French to the canonical English set: `Applied`, `Interview scheduled`, `In progress`, `Offer`, `Rejected`, `Withdrawn` (was `Candidaté`, `Entretien planifié`, `En cours`, `Offre`, `Refusé`, `Abandonné`). Dashboard counters/charts that keyed on French substrings (`indexOf("entretien")`, `counts["Offre"]`, default `"Candidaté"`) were rewired to the English vocabulary. First slice of the wider English-canonical rebase — surface localization of the *displayed* labels is a later step, so until then the dashboard renders English status labels.
- **Marker internal state renamed `ici` → `current`** across `parse_marker` / `format_marker` / `reconcile` (English-canonical code identifier; no on-disk change — the glyph `◆` is unchanged).

### Removed
- **Legacy French marker backward-compat dropped.** Marker regexes are now **glyph-only** (`◆` current, `✗` deleted); the former tokens `(ici)` / `(supprimée)` are no longer parsed. The live tracker CSV was migrated to glyphs + English statuses out of band (no migration code in the engine — the suite ships English-native and keeps no transition crutch).

### Validated
- 22 scripts compile. `parse_marker` / `format_marker` unit tests pass for all four states (incl. confirmation that legacy `(ici)` / `(supprimée)` now parse as `bare`). Reconcile re-tested on the three DRV-5 scenarios (promotion `◆ → uuid`, floor-driven `✗`, sub-floor undetermined) — logic intact after the rename + compat removal. Dashboard rebuilt from the migrated CSV: embedded `STATUSES` English, counters coherent (14 / 10 Applied / 4 Withdrawn), `✗` markers rendered; cat-C French display strings intentionally untouched (reserved for the UI-surface step).

### Documentation
- `references/tracker_format.md` and `modules/application-tracker/GUIDE.md`: status vocabulary updated to English; the DRV-9 note rewritten as **glyph-only** (the backward-compat sentence removed).

## [0.10.1] — 2026-06-04

### Changed
- **cat-A infrastructure is now exhaustively English — package-wide, every comment syntax.** Completes what [0.9.1] aimed at but did not fully reach. Translated to English: residual French in **CSS `/* */` comments** inside `md_to_pdf.py`'s `build_css` (×4 copies — `Labels Question / Réponse`, `TIP encadré`, `Titres sémantiques de puces`, `H3 sémantiques`, `TIP liseré`); **trailing `//` comments** in `build_dashboard.py` (`clé -> nouveau statut`, `-1 décroissant`, `lecture initiale faite`); the full set of line-start **`//` JS comments** in `build_dashboard.py` / `build_selector.py`; secondary **docstring usage placeholders** (`<fichier.pdf>`, `"Titre"`, `<chemin_cv>`, `<texte_offre>`); and the remaining `#` comments / docstrings / argparse `description`+`help` across all 22 scripts. **Comments, docstrings and argparse help only — zero behavior change.**

### Validated
- **Exhaustive extraction, not detection.** Earlier passes relied on a French-wordlist scan blind to accent-less / stop-word-less French (e.g. `# Forces (titre vert)`) and only inspected line-start `#`/`//`, so they missed trailing `//`, every CSS `/* */`, and secondary docstring placeholders — which is why residuals kept resurfacing. This pass **extracts 100 % of every comment surface** — `#` (tokenize), `//` incl. trailing, `/* */`, `<!-- -->` (regex over source), docstrings + argparse (AST) — and reviews each item by eye. The result is a **closed, enumerated census**: re-scan confirms **0 cat-A French**; every remaining French token is an enumerated cat-B data literal (`Candidaté`, `Rue/Avenue`, `(supprimée)`, `chiffres clés`, `Adresse à compléter`…) or cat-C rendered UI (`print` / HTML / `sendPrompt`, frozen until LNG-1). 22 scripts compile; sampled `--help` render English.

## [0.10.0] — 2026-06-03

### Changed
- **DRV-9 — conversation markers are now language-agnostic glyphs.** The French tokens `(ici)` / `(supprimée)` are replaced by `◆` (current / not yet linked) and `✗` (deleted); the linked form `<date> → {uuid}` is unchanged. Glyphs chosen to collide with neither the CSV separator `,`, the intra-cell separator ` ; `, nor the arrow. Touches `manage_tracker.py` (writing **and** parsing — the DRV-5 reconcile core) and `build_dashboard.py` (detection, rendering, current-marker suffix).

### Added
- **Backward-compatible auto-migration.** The parser still reads the legacy FR tokens and re-emits **every** marker in glyph form on the next reconcile, so existing CSVs migrate in place — no manual step. `format_marker()` centralizes the canonical (glyph) rendering. Proven on the real tracker (3 `(supprimée)` → `✗`, 11 links preserved, zero spurious promotion/deletion).
- **Dashboard legend is now mandatory** (the glyphs are mute): `◆` current · `→` linked · `✗` deleted, surface-adaptive.

### Validated
- Re-test of the DRV-5 scenarios on glyphs — **1a** promotion (`◆`/legacy `(ici)` → linked), **1b** floor-driven deletion (linked → `✗`), **1c** floor undetermined (stays) — plus migration of legacy tokens and round-trip of pre-existing glyphs: all pass. Docs updated (`tracker_format.md`, tracker `GUIDE.md`, `SKILL.md`) — doc-follows-code. 22 scripts compile.

## [0.9.1] — 2026-06-03

### Documentation
- **Cluster-0 cat-A completed — infrastructure is now 100% English.** A residual batch of French comments and docstrings (left over from the 0.8.3 pass — mostly in the splice-recovered `manage_tracker.py` and the four `md_to_pdf.py`, plus a few others) was translated to English: ~26 `#` comments and ~11 docstrings. **Comments/docstrings only — no behavior change.** Deliberately preserved: data-French literals (cat-B: `Service Recrutement`, `Adresse à compléter`, `Candidaté`, `Cordialement`, `Madame, Monsieur`…) and user-facing FR strings (cat-C: print/HTML). One stale docstring referencing a hardcoded `'Réponse :'` label was corrected — that label is model-provided via `--labels-json` since L6. Exhaustive re-scan (tokenize + AST): zero residual cat-A French; 22 scripts compile.

## [0.9.0] — 2026-06-03

### Added
- **Multi-language (L6) — the suite is now language-agnostic end to end.** Any ISO 639-1 language works (not only `fr`/`en`): the model produces the localized realization in the run language; the scripts enforce only the fixed structure. The single-language assets that used to gate this (per-language label tables, language-suffixed templates) are gone.

### Changed
- **`.md` generators: per-language `TEXTS` tables removed → structure labels supplied by the model.** The four generators (application-summary, interview-prep, strategic-playbook, quick-reference) no longer carry a hand-maintained `TEXTS[lang]` dict. Labels are passed via a new **required `--labels-json`** argument; the script validates the key set is **exactly** the generator's fixed `REQUIRED_LABELS` (a missing or extra key is rejected). Anti-hallucination counterweight: the structure is frozen, only the wording is the model's. Replaces the former `language not in TEXTS` 2nd lock.
- **Cover letter: two language-suffixed templates collapsed into one neutral template.** `generate_templates.py` now emits a single `Cover_letter_template.docx`; the language-baked spots became placeholders `{{SUBJECT_LABEL}}`, `{{GREETING}}` (single — was `{{GREETING_FR}}`/`{{GREETING_EN}}`), `{{CLOSING}}`, filled by the model in the run language. The 9 non-negotiable formatting rules (Calibri, A4, fused header borders, floating signature…) are untouched.
- **Recruiter default now model-provided, not script-baked.** `fill_cover_letter.py` no longer injects a hardcoded `Service Recrutement`/`Recruitment Department` default; the model supplies a localized `recruiter_name` when the recruiter is unknown. The orphan-comma cleanup (empty title) is kept and is language-agnostic.
- **Config schema: `Template EN/FR filename` → single `Template filename`.** Reflected in `candidate-config/GUIDE.md`, `memory_format.md`, `storage_options.md`, `setup_workflow.py` (recap + JSON contract). Users relying on the bundled template (no project template file) need **no migration**: resolution falls back to the single bundled neutral template.

### Documentation
- **SIG-1 reconciled** in `cover-letter-generator/GUIDE.md`: the legacy "base64-in-memory / Drive priority" wording (kept as a flagged marker) is replaced by the authoritative model — session upload → project file, **never** memory, **never** Drive; `[CONFIG] Signature base64` deprecated.
- **Orchestration contract documented**: `SKILL.md` 3-bis (labels produced by the model in the run language, passed via `--labels-json` / data-json), each generator `GUIDE.md` (its exact label key set + updated command line), the cover-letter `GUIDE.md` (neutral-template resolution, localized `subject_label`/`greeting`/`closing`), and `letter_conventions.md` (neutral placeholders). The `iso639_1` docstrings updated: `--language` is form-validated **metadata only** — no per-language lock.

### Validated
- **German, end to end.** Each `.md` generator renders German section titles from model-supplied labels with the structure fixed; an incomplete label set is rejected listing the exact missing keys. German cover letter: `Betreff: Leiter Technik`, `Sehr geehrte Damen und Herren,`, `Mit freundlichen Grüßen,`, orphan comma cleaned, **zero residual placeholder**, layout intact. `fr`/`en` unchanged. All 22 scripts compile; no stale `TEXTS` / `_EN`/`_FR` reference remains.

## [0.8.3] — 2026-06-03

### Removed
- **Google Drive documentation and dead mechanics.** The code had already dropped every Drive path (0.4.2); what remained was stale *documentation* describing Drive as a live option. Deleted `modules/candidate-config/references/migration.md` (its 3-mode, Drive-centric migration matrix contradicted `storage_options.md`'s "2 modes"). Removed the now-vestigial **`[CONFIG] Drive integration`** key (no longer defined or documented anywhere) and the `[CONFIG] Drive folder ID` example + the `google_drive` value from the `Storage method` enum in `memory_format.md`.

### Changed
- **candidate-config `GUIDE.md` realigned onto the real, Drive-free flows.** Sections `[3]`/`[4]`/`[5]` rewritten from a non-existent Drive UI into the actual project-based tracker actions (`track_project` = persistent versioned CSV in the project files + manual add/delete ritual + dashboard/guide · `track_session` = read-only session view · `track_guide`). Storage enum reduced to `project_files | stateless`; the preferences-panel intro drops the Drive toggle (only `Signature persistence` persists; tracker mode is per-action). `storage_options.md` reduced to the 2 live modes and translated to English (keeps the "Google Drive — REMOVED" guardrail). `migrate_storage.py` docstring → English, marked a local-only utility (no connector). `data_extraction.md` drops the "On Google Drive" CV location.
- **Cluster-0 (cat-A) — script infrastructure now natively English.** All Python **module docstrings, function/class docstrings, and full-line `#` comments** across the 22 scripts translated FR→EN. Preserved verbatim: user-facing strings (print/HTML/`sendPrompt` prompts/errors = cat-C, left FR this pass), data-French literals (`Candidaté`, `Service Recrutement`, `Adresse à compléter`, FR status values, FR UI button labels), code identifiers, CLI flags, JSON/memory keys (`[CONFIG]`/`[CANDIDAT]`), status values (`present_upload`/…), and marker tokens (`(ici)`, `(supprimée)`, `📋`, `{uuid}`, `[!TIP-BOX]`, `[+]`/`[-]`/`[Q]`).

### Validated
- All 45 scripts compile. Code integrity verified against the 0.8.2 baseline (AST structure, docstrings excluded) — **no code change** beyond docstrings/comments. Smoke tests: tracker naming (`Applications_Tracker_YYYYMMDD_HHMM.csv`, Europe/Paris DST), config recap, `--language` ISO form-validation (`de` accepted in form, `EN` rejected), Drive sweep (guardrails only). Drive guardrail mentions ("no Drive / never reintroduce a connector") intentionally kept.

## [0.8.2] — 2026-06-03

### Changed
- **Reverted the 0.8.1 French trigger phrases in the frontmatter `description`.** Enumerating per-language command phrases reintroduces exactly the language adherence LNG-1 removes — it would next require German, Danish, … keyword lists, ad infinitum. The description stays in English (the dispatch lingua franca) but describes **intents, not required wordings**, and explicitly instructs intent-matching **regardless of the request's language**. Cross-lingual dispatch relies on the model's semantic matching — the same bet LNG-1 makes for language detection — and is validated empirically (real-condition triggering test), not by keyword stuffing. (0.8.0's intent-based description was the principled one; 0.8.1 is superseded.)

## [0.8.1] — 2026-06-03

### Fixed
- **Skill triggering (frontmatter `description`).** The 0.8.0 English-only description dropped the literal French command phrases, leaving dispatch on French requests (e.g. « Où en sont mes candidatures ? ») to rely on an unguaranteed FR→EN semantic mapping. The description is now **bilingual**: the English semantic summary (for diffusion) **plus** the explicit French trigger phrases (for reliable dispatch on the user's actual French commands). The trigger phrases are the one piece of "infrastructure" that must match the *user's* language rather than be English-native.

## [0.8.0] — 2026-06-03

### Added
- **LNG-1 language socle (L1–L5): model-agnostic language handling.** `SKILL.md` now carries an explicit **Language principle** + STEP 4 sub-step **3-bis** (resolve the run language): working language = the conversation language; the **letter** language is the offer's, identified by the model and **confirmed once**, then persisted in the tracker `language` column for silent reuse on resume; one-off override of help-docs to the job's language; ambiguity → ask; **no frozen default**.
- **Two agnostic style resources** under `modules/cover-letter-generator/references/`: `language_style_generic.md` (register/idiom/locale formats, all deliverables) and `letter_conventions.md` (epistolary specifics, letter only). They replace the former hand-maintained per-language tables.
- **`--language` accepts an open ISO 639-1 code** (form-validated, two lowercase letters) on all 5 generators; `en`/`fr` stay valid (no migration). The deterministic rejection of a not-yet-supported language remains the downstream 2nd lock (`TEXTS` / template resolution) until the multi-language assets land (L6).

### Changed
- **Cluster-0: infrastructure translated to native English** — `SKILL.md`, `references/assistant_flow.md`, every module `GUIDE.md` and structure reference, and the `candidate-config` references (`memory_format`, `header_styles`, `data_extraction`). Widget/UI labels and a few parked files stay French in this build.
- **cover-letter `GUIDE` refactored onto the agnostic socle** — no in-module language detection; the run language is resolved by the orchestrator and passed as `--language`.
- **Tracker filename prefix** renamed `Suivi_Candidatures_` → `Applications_Tracker_` (`manage_tracker.py` + `build_guide.py`).
- **`build_selector`**: composed-prompt tag `[skill: …]` → `[module: …]`; widget label "Playbook stratégique" → "Stratégie d'approche".

### Fixed
- **Tracker filename timestamp** now uses `zoneinfo("Europe/Paris")` (DST-correct) instead of a hardcoded UTC+2 offset (which was wrong in winter).

### Removed
- **`detect_language.py`** (cover-letter-generator) — the model identifies the offer's language by reading it, confirmed once; no keyword/accent heuristic anywhere.
- **`language_conventions.md`** — superseded by the two agnostic style resources above.

### Notes
- **Interim consolidated build, not the final diffusion release.** Deliberately deferred: L6 multi-language asset de-freezing (`TEXTS[lang]` + a single neutral `.docx` template), DRV-9 agnostic conversation markers, Drive-section cleanup (`migration.md` / `storage_options.md`), script-docstring translation, and the PII sweep for public diffusion. No package code was test-validated in real conditions yet beyond the bundled test suite.

---

<!--
  ▼▼▼  FROZEN FRENCH HISTORY BELOW (unchanged, not retranslated)  ▼▼▼
-->

## [0.7.0] — 2026-06-02

### Ajouté
- **DRV-8 — préférences d'affichage persistées dans le dashboard.** Le dashboard mémorise
  désormais les **préférences d'affichage** de l'utilisateur (colonne + sens de tri, filtre
  statut, filtre langue, recherche) entre deux ouvertures, via `window.storage` (clé
  `candidate-suite:dashboard:ui-prefs`, privée). Implémenté entièrement dans
  `build_dashboard.py` (`loadUIPrefs`/`saveUIPrefs`/`applyUIPrefs`), greffé sur l'état d'UI
  existant — aucun composant séparé. Lecture initiale après `populateFilters()` et avant le
  premier `render()` ; `get()` enveloppé d'un `try/catch` (il **lève** si la clé est absente).
- **Ligne de partage stricte (décision figée) :** `window.storage` = **cache d'affichage
  uniquement**. La donnée métier (candidatures) reste dans le **CSV de projet**, seule source
  de vérité lue par `manage_tracker.py` ; DRV-5 (réconciliation) inchangé. Règle d'or : si le
  cache et le CSV divergent, **le CSV gagne**. Mettre la donnée métier dans `window.storage`
  rendrait le moteur Python aveugle → explicitement interdit.
- **Dégradation propre :** best-effort de bout en bout. `window.storage` absent (aperçu hors
  app, mode éphémère, autre outil) → défauts appliqués, aucune erreur.
  `localStorage`/`sessionStorage` interdits (bloqués dans les artefacts).

### Validé
- Aller-retour écriture → persistance → relecture confirmé **en réel** sur desktop **et** web
  (02/06), stockage observé **partagé entre surfaces**. Tests automatiques : aller-retour, clé
  absente, storage indisponible, robustesse `applyUIPrefs` — tous verts.

### Documentation
- Section « Préférences d'affichage persistées (DRV-8) » ajoutée au `GUIDE.md` du tracker ;
  section « Limites techniques » mise à jour (filtres/tri désormais persistés ; seule la
  donnée métier passe par la boucle d'écriture CSV).

## [0.6.2] — 2026-05-31

### Modifié
- **`GUIDE.md` workflow E — durcissement du rafraîchir (3 garde-fous).** Gravé après
  validation Phase 1 en réel : (1) le repère `(ici)` se promeut **seulement depuis une
  autre conversation** (la courante est exclue de son propre `recent_chats` ; un UUID lu
  dans le texte n'est pas une énumération fiable → ne jamais promouvoir dessus) ; (2) pour
  une candidature **déjà suivie**, reprendre la clé `(société, poste)` **exacte du CSV** —
  ne pas la ré-inférer du titre (sinon doublon, le risque n°1) ; (3) **plancher** : paginer
  jusqu'à passer sous le plus ancien repère du CSV, **avertir** si le cap est atteint sans
  y parvenir (« détection de suppression partielle »). Doc seule ; aucun effet moteur.

## [0.6.1] — 2026-05-31

### Modifié
- **Dashboard — ligne grisée pour les candidatures perdues.** Si **tous** les repères
  de conversation d'une candidature sont `(supprimée)` (plus aucun lien vivant ni
  `(ici)`), le **fond de toute la ligne** passe en gris léger
  (`--color-background-secondary`) pour la repérer d'un coup d'œil. Une ligne qui
  conserve au moins une conversation vivante reste normale. Tri et édition de statut
  inchangés. Détection via `isRowDeleted()` dans `build_dashboard.py`. Doc :
  `tracker_format.md`. Aucun effet sur le moteur ni le schéma.

## [0.6.0] — 2026-05-31

### Ajouté
- **DRV-5 — mode `reconcile` dans `manage_tracker.py`** (réconciliation déterministe).
  La logique de rapprochement sort de la tête de l'assistant et passe dans le code,
  testée (44 assertions). L'assistant fournit le scan en JSON
  (`[{uuid,date,company,position,title}]`, sans connecteur) ; le script applique :
  - **Promotion `(ici) → {uuid}`** par clé **(société, poste)** — jamais par titre —,
    en place, **sans doublon** ; date du repère préservée.
  - **Union des liens** : une candidature reprise un autre jour (nouvel UUID, même
    société/poste) accumule ses conversations sur la même ligne.
  - **Marquage `(supprimée)` piloté par un PLANCHER de scan** (= plus ancienne date
    énumérée) : un repère lié absent **et** de date **≥ plancher** est concluant →
    marquage **OBLIGATOIRE** ; date **< plancher** → indéterminé, inchangé. *Corrige
    la cause-racine de DRV-6 : le marquage ne dépend plus de la diligence de l'assistant.*
  - **Nouvelles candidatures** créées depuis le scan ; **non destructif** (statuts/notes
    préservés).
  - **Rapport d'hygiène de nommage** en sous-produit (titre réel ≠ canonique → titre
    actuel / proposé / lien), bloc `---RECONCILE-SUMMARY-JSON---` lisible par l'assistant.
- **Colonne `title`** (schéma CSV) : vrai titre de la conversation liée la plus récente,
  capté/réécrit à chaque reconcile. Champ d'**affichage**, **jamais une clé**.

### Modifié
- **Dashboard — repère desktop : préférence au VRAI titre.** `renderConv` reçoit
  `e.title` et l'affiche s'il est connu ; **repli** sur le repère fabriqué
  `📋 date - société - poste` sinon. Robuste même si l'utilisateur n'a pas renommé la
  conversation (le repère fabriqué supposait un renommage manuel).
- **Suggestion de titre canonique SYSTÉMATIQUE** (`SKILL.md` ÉTAPE 4, point 8) : proposée
  dès qu'un livrable est généré **à partir d'une description de poste**, quel que soit le
  flux (guidé complet ou doc unique) ; exclut la pure config. **Date du titre = première
  activité si la candidature est déjà suivie, sinon date du jour** (titre stable dans le
  temps). Suggestion à appliquer par l'utilisateur (l'assistant ne renomme pas).
- **Docs alignées** : `GUIDE.md` (workflow E réécrit autour du script, table des champs +
  colonne `title`, table des scripts + `reconcile`, repère desktop), `tracker_format.md`
  (colonne `title`, section Rafraîchir, repère desktop).

### Notes
- Limite d'environnement (inchangée) : l'assistant ne peut ni **renommer une conversation**
  ni **écrire dans le projet** ; le rituel d'ajout manuel et la suggestion de titre restent
  la parade. Souhait remonté côté produit via le feedback (pouce), non automatisable ici.

## [0.5.9] — 2026-05-31

### Modifié
- **Guide — menu « Ajouter au projet » : image raster → reconstitution HTML.**
  L'asset `add_to_project.png` (capture base64 ~10 Ko) est **supprimé** ; le menu
  est désormais **reconstitué en HTML/CSS** dans `build_guide.py` (rendu net,
  léger, portable, sans dépendance binaire), **aligné à droite** du texte. Retrait
  du paramètre `--screenshot-path` et de l'embarquage base64. Corrige aussi
  l'**image surdimensionnée** de la 0.5.8 (qui était étirée en `width:100%`).
  Guide ~18 Ko (vs ~31).
- **Guide — texte du rituel d'ajout au projet reformulé** (onglet « fichier de
  suivi ») : décrit explicitement le menu en haut à droite du visualiseur (bouton
  « Copier ⌄ » → « Ajouter au projet »), puis la suppression de l'ancienne version
  sur le projet.
- **Dashboard — colonne Lien en desktop : repère exact.** Au lieu d'afficher la
  date avec une infobulle « barre latérale », le dashboard affiche en desktop le
  **repère exact** `📋 AAAA-MM-JJ - Société - Poste` (texte sélectionnable d'un
  clic) à retrouver/copier dans la barre latérale. `renderConv` reçoit désormais
  société + poste ; légende adaptée. En web, le lien cliquable est conservé.

### Note
- Supersède le paquet 0.5.8 (déployé) : la 0.5.9 emporte le correctif de taille
  d'image. « DRV-3 (modèle de lien) validé en desktop réel » consigné dans la
  roadmap (test surface/lien concluant : lien de chat → bascule in-app en desktop).

## [0.5.8] — 2026-05-30

### Ajouté
- **Guide du suivi — capture « Ajouter au projet ».** L'onglet « Le fichier de
  suivi » illustre désormais le geste de persistance par une capture d'écran du
  menu déroulant (recadrée sur le bouton « Copier ⌄» + le menu, palette 64
  couleurs, 240×135, ~10 Ko). `build_guide.py` l'embarque en base64 si l'asset
  `modules/application-tracker/assets/add_to_project.png` est présent (nouveau
  paramètre `--screenshot-path`, défaut sur l'asset ; bloc vide si absent — rien
  en dur, portable). Guide ~31 Ko.

### Modifié
- **Guide du suivi — onglet « Le tableau de bord ».** Encadré explicite sur le
  cycle du statut : valeur par défaut « Candidaté » à l'ajout, modifiable par le
  seul utilisateur (l'assistant ne change jamais un statut de lui-même), et
  séquence choisir → Enregistrer → ajouter au projet la nouvelle version
  présentée. Puces « Menu Statut » et « Enregistrer » reformulées dans le même
  sens. Aucun effet fonctionnel.

## [0.5.7] — 2026-05-30

### Corrigé
- **Purge de l'ancien nom « Candidature Suite » dans le corps de la skill.** Le
  `SKILL.md` (titre H1 + phrase d'intro) et 3 GUIDE de sous-modules
  (`cover-letter-generator`, `interview-prep-generator`,
  `application-summary-generator`) référençaient encore l'ancien nom propre. Remplacé
  par le nom réel `candidate-suite`. Le mot « candidature » au **sens propre** (l'acte
  de postuler : « demande de candidature », « synthèse de candidature », etc.) est
  **conservé**. Aucun effet fonctionnel. Supersède le paquet 0.5.6 (non déployé).

## [0.5.6] — 2026-05-30

### Corrigé
- **Frontmatter YAML valide.** Le champ `description:` contenait des deux-points
  non échappés → YAML invalide pour un parseur strict (le `quick_validate` du
  packager officiel échouait). La valeur est désormais **entre guillemets doubles**
  (guillemets internes échappés `\"`, apostrophes et deux-points sans souci). Le
  loader de l'app tolérait déjà ; ce correctif débloque les loaders stricts (utile
  avant DEP-4).

### Ajouté
- **Override de surface — `build_dashboard.py --surface auto|desktop|web`.** Complète
  le point d'entrée `window.__SURFACE__` existant : `auto` (défaut) garde la détection
  userAgent ; `desktop`/`web` forcent le rendu des liens (filet pour préférence ferme
  ou tests). Documenté dans `application-tracker/GUIDE.md` (section Surface & liens).

> Note : 0.5.3 (alignement nommage CSV sans tirets), 0.5.4 (DRV-6 marquage
> `(supprimée)` obligatoire) et 0.5.5 (timestamps UTC+2) sont tracées dans le
> journal de la roadmap ; ce CHANGELOG les a sautées et reprend ici à 0.5.6.

## [0.5.2] — 2026-05-30

### Corrigé
- **Nomenclature du fichier de suivi fabriquée par le script.** La consigne durcie
  en 0.5.1 ne suffisait pas : le nom restait **composé à la main** par l'assistant,
  d'où la dérive observée `Suivi_Candidatures_20260530_1605.csv` (date collée) au
  lieu de `…_2026-05-30_1605.csv`. `manage_tracker.py` **génère désormais lui-même**
  le nom horodaté (`Suivi_Candidatures_AAAA-MM-JJ_HHMM.csv`, **heure de Paris** via
  `zoneinfo`, date à tirets) quand on lui passe **`--output-dir`**, et **imprime le
  chemin retenu** ; l'assistant présente ce fichier sans jamais formater le nom.
  `--output-path` conservé comme **échappatoire** (rétro-compat). Même principe que
  le correctif `HH:MM` : ce que l'assistant compose à la main dérive → on le confie
  au script. Docs alignées : `SKILL.md` (ÉTAPE 4), `GUIDE.md` (workflows B/C, bulk,
  versionnage, tableau de référence), `tracker_format.md`, docstrings
  `manage_tracker.py`.

## [0.5.1] — 2026-05-30

### Corrigé
- **Repère conversation sans heure.** Le gabarit `AAAA-MM-JJ HH:MM` du champ
  `conversation` produisait un `HH:MM` **littéral** quand il était recopié tel quel
  par `add_to_tracker` (vu dans un dashboard : « 05-30 HH »). La convention passe à
  **`AAAA-MM-JJ` (date seule)** dans les trois états (`(ici)`, `→ {uuid}`,
  `(supprimée)`) : l'état `(ici)` suffit à désigner la conversation courante, et la
  cellule n'affiche de toute façon que `MM-JJ`. Mis à jour : `SKILL.md` (ÉTAPE 4),
  `tracker_format.md`, `application-tracker/GUIDE.md`, exemples de `build_guide.py`
  et docstrings de `manage_tracker.py`.
- **Rendu de la colonne Lien robuste** (`build_dashboard.py`) : `renderConv` extrait
  désormais la date ISO de tête (`\d{4}-\d{2}-\d{2}`) et affiche `MM-JJ` en ignorant
  tout résidu (heure, gabarit non substitué). Une donnée héritée « …-30 HH:MM »
  s'affiche proprement « 05-30 ».

### Renforcé
- **Nomenclature du fichier de suivi.** Format de nom rendu explicite et
  non-ambigu — `Suivi_Candidatures_AAAA-MM-JJ_HHMM.csv`, **date avec tirets**, heure
  `HHMM` sans séparateur (ex. `…_2026-05-30_1605.csv`), via
  `TZ=Europe/Paris date +%Y-%m-%d_%H%M`. Anti-dérive explicite : ne jamais produire
  la date collée (`20260530`). Consignes alignées dans `SKILL.md`, `GUIDE.md`,
  `tracker_format.md`.

## [0.5.0] — 2026-05-30

### Ajouté
- **DRV-4 — Suivi par fichier de projet.** Le suivi est un CSV versionné
  (`Suivi_Candidatures_AAAA-MM-JJ_HHMM.csv`) dans les fichiers du projet ;
  rituel d'écriture à noms horodatés uniques (régénérer → l'utilisateur ajoute au
  projet → supprime l'ancien). Clé d'écriture **(société, poste)** (la date sort de
  la clé) ; `deliverables` et `conversation` **accumulés** (union) ; date = première
  activité (préservée).
- **Colonne `conversation` multi-valeurs datée, 3 états** : `(ici)` (courant, écrit
  par `add_to_tracker`), `→ {uuid}` (lié), `(supprimée)` (lien invalidé). Stockage
  de l'**UUID** (pas d'URL).
- **Dashboard** (`build_dashboard.py`) : colonne Lien multi-états + **légende** ;
  **détection de surface** (`Electron`/`Claude` dans le `userAgent` → desktop = texte,
  web = lien `https://claude.ai/chat/{uuid}` cliquable) ; boutons **Guide
  d'utilisation** et **↻ Rafraîchir** (`sendPrompt`).
- **Guide du suivi** (`build_guide.py`) en 3 onglets, centré « comment retrouver ses
  livrables » (conversation = archive ; barre latérale par date + titre).
- **Recap de clôture** (`SKILL.md` ÉTAPE 5, niveaux 1/2) avec liens `https://` en
  chat (cliquables in-app en desktop, onglet en web).

### Modifié
- `SKILL.md` : ÉTAPE 4 `add_to_tracker` (écriture `AAAA-MM-JJ HH:MM (ici)`, clé
  société/poste, rituel fichier-projet) ; ÉTAPE 8 (renommage = repère barre latérale).
- `tracker_format.md` et `application-tracker/GUIDE.md` réécrits au modèle
  fichier-projet (workflows A→E, dont rafraîchir).
- `build_preferences.py` : section suivi (`--tracker-current project|session|none`).

### Corrigé
- **FIX-FREEZE — gel à la génération si un fichier référencé manque.** `resolve_files.py`
  ne propose plus de recours Drive (suppression de `--drive-available` et du signal
  `drive_check_suggested`) ; `SKILL.md` ÉTAPE 4.3 ajoute un garde-fou explicite :
  CV `referenced_missing`/`none` → **s'arrêter et demander**, jamais de lecture via
  connecteur (un appel connecteur n'est pas bornable par instruction).

### Supprimé
- **Google Drive, intégralement** : résolveur, `storage_question`, `storage_options.md`,
  helper `manage_tracker.py cleanup-plan` (DRV-2). Plus aucun appel connecteur.

### Spécifié (non implémenté — fast-follow)
- **DRV-5 — Rafraîchir le suivi par scan des conversations** (`conversation_search`/
  `recent_chats`, ~100 conversations, modifiable) : **réconciliation par rapprochement**
  (`(ici)` → `→ {uuid}`, sans doublon), marquage `(supprimée)` **sur énumération
  complète uniquement** (règle de prudence), fusion non destructive + confirmation.
  Reste à coder un **mode « réconcilier »** dans `manage_tracker.py`.

### Connu (dette)
- Frontmatter `description` (SKILL.md) : deux-points non échappés → YAML invalide pour
  un parseur strict (le loader réel tolère ; packagé en zip maison). À fiabiliser avant DEP-4.

## [0.4.1] — 2026-05-29

### Ajouté
- **SIG-1 — Signature persistante via fichier de projet.** Nouveau résolveur
  `scripts/resolve_files.py` : localise CV + signature dans l'ordre upload de
  session → fichier de projet → (Drive conditionnel) et renvoie un statut JSON
  par fichier (`present_upload` / `present_project` / `referenced_missing` /
  `none`). Piloté par config (`[CONFIG] CV filename`, `[CONFIG] Signature
  filename`), aucune valeur en dur, répertoires paramétrables (esprit DEP-2/DEP-4).
- **Flux lettre câblé sur le résolveur** (`SKILL.md` ÉTAPE 1.4 / 4.2) : la
  signature `present_project` est passée à `fill_cover_letter.py --signature-path`
  → **lettre signée sans ré-upload**. Vérifié de bout en bout (image embarquée
  dans le `.docx` produit).
- **Panneau de préférences** (`build_preferences.py`) : pastilles de **statut
  réel des fichiers** + source du template (champs optionnels `badge` /
  `badgeKind` par élément de config).

### Modifié
- **GUIDE `candidate-config` ÉTAPE 3** réconcilié sur le modèle fichier-de-projet ;
  note de réconciliation SIG-1 close ; description de `setup_signature.py` corrigée.

### Déprécié
- `[CONFIG] Signature base64` (signature en mémoire) : la mémoire est plafonnée à
  500 caractères, inutilisable pour ~14 000 car. de base64. La persistance passe
  désormais par un **fichier de projet**, jamais par la mémoire.



### Ajouté
- **LIV-1 — Garde-fou « une page » de la lettre.** Plafond dur de 2 800 caractères
  sur le corps (somme des 5 paragraphes, espaces compris) dans `fill_cover_letter.py` :
  refus `exit 2` au dépassement, avec le détail par paragraphe et le marquage du
  paragraphe à raccourcir en priorité. Ratios soft 15/22/26/22/15 (cibles
  §1 420 / §2 616 / §3 728 / §4 616 / §5 420, ±20 %). Réglable via `--body-cap`.
  Identique FR/EN. Consigne « budget une page » ajoutée à l'ÉTAPE 5 du GUIDE
  `cover-letter-generator`. Vérifié : 3 112 car. → refus (P4 prioritaire) ;
  2 800 car. → généré, rendu 1 page confirmé.
- **Panneau de préférences** (`scripts/build_preferences.py`, nouveau). Rend visible
  `candidate-config` (profil en lecture + bouton Modifier) et expose deux réglages
  via boutons-actions `sendPrompt` : signature [Non / Oui], Drive [Avoir un suivi /
  Ne pas utiliser / Voir le guide]. Entièrement paramétré (rien en dur).
- **Guide du suivi Drive en onglets** (`modules/application-tracker/scripts/build_guide.py`,
  nouveau) : fichier de suivi, tableau de bord (aperçu + champs/boutons), arborescence
  des dossiers. Paramétré.
- **Helper de ménage du suivi** (`manage_tracker.py`, commande `cleanup-plan`).
  À partir des versions trouvées (`search_files`), désigne la plus récente à garder
  (`modifiedTime`) et liste les obsolètes à supprimer. Logique pure, aucune action
  Drive ; suppression manuelle par l'utilisateur.
- **Flux guidés [1]–[5]** documentés dans le GUIDE `candidate-config`, avec deux
  nouveaux champs : `Signature persistence: project|session` et `Drive integration: on|off`.

### Décidé (conception actée)
- **SIG-1 — signature persistante via fichier de projet.** Pipeline image *ou* base64
  → redimensionnement si nécessaire → `.txt` base64 nommé `<basename>_<ext>_b64.txt`,
  déposé manuellement dans le projet (la skill lit le projet, n'y écrit pas).
  Seuil ~15 000 caractères / largeur ~600 px, réglable.
- **DRV-1 — archivage Drive.** Format `Documents_generes/<Candidat>/<AAAA-MM-JJ - Société - poste>/`,
  fichiers `Type_Candidat_Entreprise_Langue` ; dossier réutilisé si la candidature est
  relancée ; niveau « candidat » pour l'usage multi-candidats.
- **DRV-2 — prolifération du suivi.** L'écrasement de fichier Drive est **impossible**
  avec le connecteur (testé : `create_file` crée un doublon, aucun outil de mise à jour).
  Résolution → helper de ménage, et non « fichier unique ».
- **Drive désactivé par défaut**, activation explicite valant autorisation lecture/écriture
  du fichier de suivi (cadre de consentement livré en 0.3.2).

### Connu (à faire, non bloquant)
- Entrée « Préférences » pas encore branchée dans le widget de sélection principal
  (`build_selector.py`).
- Réconciliation SIG-1 du GUIDE `candidate-config` : l'ÉTAPE 3 et la section
  « 3 modes de stockage » décrivent encore l'ancien modèle (signature en mémoire,
  `Storage method`) — signalées par un encart, à réécrire dans une passe dédiée.

## [0.3.2] — 2026-05-29

### Corrigé / Ajouté
- Signature flottante (validée sous Word).
- Fiche mémo 2 colonnes (tient sur 1 page).
- Destinataire propre : `recruiter_title` non critique + nettoyage de la virgule orpheline.
- Tracker : horodatage heure de Paris (`TZ=Europe/Paris`), autorité `modifiedTime` pour
  le choix du fichier le plus récent, consentement = activation du mode persistant.

## [0.3.1]

### Corrigé / Ajouté
- Défaut du nom de recruteur + nettoyage de la virgule orpheline.
- LinkedIn (résolu côté CV, consigne « URL verbatim » en filet).
- Refus des valeurs-placeholder (`exit 2`) + consigne « demander, jamais inventer ».
- Robustesse de l'extraction du nom d'entreprise.
- Signature sur la même ligne que le nom (1 page).
- LIV-2 — export PDF de la lettre (`docx_to_pdf.py`, LibreOffice ; sortie propre
  si LibreOffice indisponible).
