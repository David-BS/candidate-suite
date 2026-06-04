> **⚠️ MODULE OF THE "candidate-suite" SUITE — PATH RELOCATION**
> This module lives in `modules/application-tracker/`. All the relative paths below
> (`scripts/…`, `assets/…`, `references/…`) are relative to THIS folder.
> From the suite root: prefix them with `modules/application-tracker/`
> (e.g. `python modules/application-tracker/scripts/<script>.py …`), or change into
> `modules/application-tracker/` before running. The scripts' code is UNCHANGED:
> they receive all their paths as arguments, nothing is hard-coded.

---
name: application-tracker
description: Application-tracking dashboard (interactive dashboard + CSV file in the project files, no connector). Displays, filters, sorts, and updates statuses. Two modes, persistent (project CSV) or ephemeral (session view). Use for "track my applications", "applications dashboard", "where do my applications stand", "add this application to the tracker", "refresh the tracker".
---

# Application tracker

Maintains and displays an **application-tracking dashboard**. Three distinct objects:
1. **Data source**: a CSV file (`Applications_Tracker_YYYYMMDD_HHMM.csv`) in the **project files** — no Google Drive, no connector.
2. **Engine**: `scripts/manage_tracker.py` (manipulates the CSV's contents: init/upsert/bulk/batch-status).
3. **Dashboard**: `scripts/build_dashboard.py` produces an interactive HTML displayed inline (counters, donuts, filterable/sortable table, batch status editing, multi-state Link column).

## ⚠️ EXECUTION RULE (NON-NEGOTIABLE)

Every manipulation goes through the scripts. Never write the CSV or the HTML "by hand." Claude's role: call the scripts, **present** the regenerated CSV (`present_files`) so the user adds it to the project, and display the dashboard via the visualization tool. **No connector call** (a connector call can freeze the session — cf. roadmap).

- ✅ CSV: via `manage_tracker.py` (init/upsert/bulk/batch-status)
- ✅ Dashboard: via `build_dashboard.py` → display the produced HTML with the visualization tool
- ❌ DO NOT write a CSV or a dashboard HTML by hand
- ❌ DO NOT call a connector (Drive, etc.)

## ⚠️ VAGUE REQUEST → FOLLOW THE WORKFLOW

If the request is open-ended, don't improvise: identify the right workflow below and run its scripts.

## Two modes

### PERSISTENT mode (default)
The source lives in a CSV in the **project files**. Additions/updates are kept via the **write ritual** (regenerate → the user adds it to the project → deletes the old one). The dashboard is **editable**.

### EPHEMERAL mode
No storage. Claude scans the conversations (`conversation_search`/`recent_chats`), builds the data on the fly, and displays a **read-only** dashboard (`--readonly`). No persistence.

**On first use, determine the mode**: ask *"Do you want persistent tracking (a tracker file in your project, recommended), or just a one-off view of this session?"*. No connector to check: persistence is a project file.

## Location (persistent mode)

- **Project files** (`/mnt/project` snapshot), **`Applications_Tracker_YYYYMMDD_HHMM.csv`** files (timestamped — see "Versioning").
- **The name's timestamp is authoritative** (no server `modifiedTime`, no Drive). At the start of a task, take the **most recent timestamped name** present in the project; if the snapshot seems stale, ask the user to re-supply the file.

## Convention for writing a conversation marker

When an application is added, the `conversation` field receives the marker of the
**current** conversation in the form **`YYYY-MM-DD ◆`** — today's date in
**UTC+2 (Paris time, CEST)**, obtained via `python3 -c "from datetime import datetime,timezone,timedelta; print(datetime.now(timezone(timedelta(hours=2))).strftime('%Y-%m-%d'))"` (**no time**:
the `◆` state alone designates the current conversation, and the cell shows only the date).
We **do not write a UUID** at write time (the assistant has no reliable access to the current
conversation's URL). It's the **refresh** (workflow E) that later promotes
`◆` → `→ {uuid}`. See `references/tracker_format.md` for the 3 states.

## Workflows

### A. Display the dashboard ("where do my applications stand?")
**Persistent mode:**
1. In `/mnt/project`, find the `Applications_Tracker_*.csv` with the **most recent timestamped name**; copy it locally (`/home/claude/suivi.csv`).
2. `python scripts/build_dashboard.py --input-path /home/claude/suivi.csv --output-path /home/claude/dashboard.html`
3. Read `dashboard.html` and display it via the visualization tool. (The dashboard **detects the surface on its own**: clickable links on web, text on desktop.)

**Interface language (surface contract — LNG-2 S2, option B).** The dashboard's HTML structure, `sendPrompt` directives and `print()` are **English-canonical** (never localized). To render the **visible labels** in another interface language, resolve it (remembered preference if any, else the conversation language), set `--ui-lang <code>`, and pass the **exact `LABELS_EN` key set** (defined in `build_dashboard.py`) translated into that language via `--labels-json` (the script errors out on any missing/extra key). If the language is **English**, omit `--labels-json`. **Statuses stay canonical English** in the data/engine/`sendPrompt`; only their display text is localized (the `status_*` labels). This surface carries **no language selector** (option B): there is nothing to re-display on a language change — the memory-preference precedence propagates the language, and the switching affordance lives on the entry selection widget.

**Ephemeral mode:**
1. `conversation_search`/`recent_chats` → find the applications (titles `📋 YYYY-MM-DD - Company - Position`).
2. Build the JSON of entries.
3. `python scripts/build_dashboard.py --data-json '[...]' --readonly --output-path /home/claude/dashboard.html` (same `--ui-lang`/`--labels-json` contract as above).
4. Display via the visualization tool.

### B. Add / update an application (persistent mode)
1. Copy the CSV with the most recent name locally → `/home/claude/suivi.csv`.
2. Compose the `entry-json`: `company`, `position`, `language`, `deliverables` (list), `conversation` = `"YYYY-MM-DD ◆"` (Paris date, no time), `date` = today.
3. `python scripts/manage_tracker.py upsert --input-path /home/claude/suivi.csv --output-dir /home/claude --entry-json '<json>'` → **the script builds the timestamped name** (`Applications_Tracker_YYYYMMDD_HHMM.csv`, no dashes in the date) and **prints the path**: present THAT file. Never compose the name by hand.
4. **Write ritual**: `present_files` of the new CSV → the user **adds it to the project** → **deletes the old version** (identified by name).
5. Optional: regenerate + display the dashboard.

### C. Batch status change (from the dashboard)
The Save button sends a message of the form:
```
Update the application tracker with these status changes:
- Globex (Director of Engineering) → Interview scheduled
- Acme Financial Group (IT & Ops) → Offer
```
Handling:
1. Copy the most recent CSV locally.
2. Build the JSON of changes: `[{company, position, status}, ...]` (**the date is not needed** — the key is (company, position)).
3. `python scripts/manage_tracker.py batch-status --input-path ... --output-dir /home/claude --changes-json '[...]'` (the script names and prints the path).
4. **Write ritual** (step 4 of workflow B). Confirm the applied changes.

### D. Initialization from history
1. `conversation_search`/`recent_chats` → past applications.
2. `python scripts/manage_tracker.py bulk --output-dir /home/claude --entries-json '[...]'` (the script names and prints the path).
3. **Write ritual**.

### E. Refresh (DRV-5) — script-driven reconciliation
Triggered by the "↻ Refresh" button (or "refresh the tracker"). **The reconciliation
logic is in `manage_tracker.py reconcile`, not in the assistant's head**: the assistant
supplies the SCAN (only it has `conversation_search` / `recent_chats`), the script
applies the matching deterministically. *This is the root fix for DRV-6: the `✗`
marking is no longer left to the assistant's diligence.*

1. **Scan** the **~100 most recent conversations** of the project (`recent_chats`
   paginated + `conversation_search`) — adjustable cap, to be **flagged to the user**
   (the tracker itself isn't capped; only the refresh's scope is).
2. For each conversation, build a JSON entry:
   `{"uuid": <uri>, "date": <updated_at YYYY-MM-DD>, "company": <company>,
   "position": <position>, "title": <REAL conversation title>}`.
   - `company`/`position`: inferred by the assistant **only** if the conversation
     is an application. A **non-application** conversation is included **with empty
     `company`/`position`**: it neither creates nor promotes anything, but it
     **counts toward the enumeration** (floor + deletion detection).
   - `title`: the **real** title, as is, **whatever its format** (NEVER assume it's
     `📋 …` — the user may not have renamed it). The script stores it in the `title`
     column (dashboard display) and uses it for the hygiene report.
3. **Call the script** (it builds the timestamped name and prints the path):
   ```
   python scripts/manage_tracker.py reconcile \
     --input-path /home/claude/suivi.csv --output-dir /home/claude \
     --scan-json '[{"uuid":"…","date":"2026-05-29","company":"Acme","position":"SWE","title":"…"}, …]'
   ```
   The script applies, deterministically:
   - **Promotion `◆ → {uuid}`** by **(company, position)** key — never by title —
     in place, no duplicate; the marker's date is preserved.
   - **Union**: any scanned conversation, for an application whose UUID isn't already
     a marker, is added (the "resumed on another day" case = new UUID, same row).
   - **`✗` marking, MANDATORY** when conclusive: marker linked, UUID absent
     from the scan, and **date ≥ floor** (floor = oldest enumerated date). Date
     **< floor** → **indeterminate**, left unchanged. *The floor invariant makes the
     marking automatic: no more risk of missing a deletion (DRV-6).*
   - **New applications**: scan keys absent from the tracker → new rows.
   - **`title`** rewritten (real title of the most recent linked conversation).
4. **Read the `---RECONCILE-SUMMARY-JSON---` block** printed by the script and **announce
   it BEFORE the write ritual**: "N links set, M ✗, K new". If the
   `hygiene` key is non-empty, present the **naming hygiene report**: for each
   listed conversation, its `current_title`, the `proposed_title` (`📋 date - company
   - position`, date = first activity) and the `https://claude.ai/chat/{uuid}` link — ready
   to copy/rename. *The assistant doesn't rename anything itself; it proposes.*
5. **Write ritual** for the regenerated CSV (`present_files` → the user adds it to the
   project → deletes the old one).

**Caution rule (deletion) — now GUARANTEED by the code**: "absent from the
scan" ≠ "deleted". The script only marks `✗` for a linked UUID **absent
AND whose date falls within the enumerated range** (≥ floor); a UUID older than
the floor stays **unchanged**. The DRV-6 symmetry ("the conclusive case MUST trigger the
marking") is held mechanically, not by diligence. ⚠️ Make sure the scan
**actually enumerates** the intended range (paginate `recent_chats`): the floor reflects
what was seen, so a scan that's too short reports a floor that's too high and leaves
deletions "indeterminate" (never a false positive, but possible false negatives if
you scan too little). *DRV-6 lesson (30/05): the dead link `ba550f4c` (SG IBP) had been
presented as valid → now impossible if its date is within the scanned range.*

**Scan guardrails — to respect on every refresh** *(hardenings validated in real conditions on 31/05, Phase 1)*:

1. **Promote `◆` only from ANOTHER conversation, never its own.** The
   current conversation **is excluded from its own `recent_chats`**: from inside
   an application, the assistant has no reliable access to its own `uri` (this is the very
   reason for the `◆` marker). A UUID read **in a conversation's content** (text) is
   **not** a reliable enumeration → **never promote on that basis** (risk of a dead
   link). So `◆` gets promoted on a refresh launched from **another** conversation (or
   a fresh conversation), where the application becomes a normally-enumerated entry. *Better
   a non-promoted `◆` than a wrong link.*

2. **Application already tracked → reuse the EXACT `(company, position)` key from the CSV, don't
   re-infer it from the title.** For UUIDs already in the tracker, compose the scan entry with
   the `company`/`position` **as written in the CSV** (not the short label from the conversation
   title). Otherwise the key doesn't match → the script thinks it's a **new** application
   and creates a **duplicate**. *This is the #1 refresh risk; it must not depend on the
   assistant's vigilance.* (Re-inference is legitimate only for an application genuinely
   **absent** from the tracker.)

3. **Floor: paginate until you go BELOW the oldest CSV marker, otherwise WARN.**
   Before calling `reconcile`, paginate `recent_chats` until the oldest enumerated date
   is **≤ the oldest CSV marker date** (otherwise some deletions stay
   "indeterminate"). If the cap (~100) is reached **without** getting there, **flag it
   explicitly**: "partial deletion detection — N markers left indeterminate
   (scan too short)", rather than implying a complete verification.

## Versioning (persistent mode)

On each write:
1. **The script builds the name**: call `manage_tracker.py … --output-dir /home/claude` (never a hand-composed `--output-path`). It generates `Applications_Tracker_YYYYMMDD_HHMM.csv` — **no dashes in the date**, `HHMM` time — and **prints the chosen path**: present exactly that file. Format aligned with the Claude app's normalization when it indexes CSVs (observed 30/05).
2. **The name is authoritative**: to choose which file to read, take the most recent timestamped name in `/mnt/project`. (No `modifiedTime`: there's no more Drive.)
3. **Unique names**: never reuse an existing name — this is what keeps the project sync from collapsing (cf. the roadmap's environment note). The user deletes the old version, identified **by name alone**.

## Persistence & consent (persistent mode)

The assistant **cannot write** to the project files: it's the user's **manual
addition of the CSV to the project** that constitutes **persistence AND
consent**, on every write, by construction — no silent write is
possible. No separate consent framework.

## Fields of an entry (CSV / JSON)

| Field | Req. | Description |
|-------|------|-------------|
| `date` | yes | "YYYY-MM-DD" — **first activity** (preserved on merge) |
| `company` | yes | Company |
| `position` | yes | Position |
| `language` | recommended | "FR"/"EN" |
| `status` | no | Default `Applied` |
| `deliverables` | no | List or text — **accumulated** (union, `a ; b`) |
| `conversation` | no | Dated marker(s) — **accumulated** (union); on write: `"YYYY-MM-DD ◆"` (date only) |
| `title` | auto | **Real title** of the most recent linked conversation, captured/rewritten at **reconcile** (DRV-5). A **display** field (the desktop dashboard prefers it to the built marker), **never a key**. Don't fill it by hand. |
| `notes` | no | Free text |

**Write key: (company, position)** — the date is NOT in the key. Merge: `deliverables`/`conversation` accumulated (union); `date` preserved; other fields overwritten by a non-empty value. The "is this the same application?" question is decided by the assistant (which **asks when in doubt**).

## Standard statuses
`Applied`, `Interview scheduled`, `In progress`, `Offer`, `Rejected`, `Withdrawn` (the dashboard offers this list; customizable via `--statuses`). *(Canonical English status vocabulary, stored in the CSV and used by the engine/`sendPrompt`. The dashboard localizes only the **displayed** label via the `status_*` keys of `--labels-json` — option values stay canonical. Cf. workflow A localization note.)*

## Surface & links (reminder)
- **Dashboard, web** → clickable Link column (`https://claude.ai/chat/{uuid}`, new tab, same account).
- **Dashboard, desktop** → Link column showing the **marker to find/copy in the sidebar** (text selectable in one click) — an `https` link would go to the browser. The marker is the **real title** of the conversation (`title` column, captured at reconcile) if known; **failing that**, the built marker `📋 YYYY-MM-DD - Company - Position`. *Robust even if the user hasn't renamed to `📋 …`.*
- **Recap in chat** (SKILL STEP 5) → `https://` links clickable **everywhere** (in-app on desktop, tab on web): this is the channel that gives clickability even on desktop.
- `claude://`: **dropped** (dead in the widget; in chat it would move the active view).
- **Force the surface**: by default the dashboard detects it (userAgent). If the user has a firm preference or for a test, pass `build_dashboard.py --surface desktop|web` (override); `--surface auto` (default) keeps detection. Reuses the `window.__SURFACE__` entry point.

## Integration with the other modules
At the end of a generation flow (STEP 5), offer to add the application to the tracker (workflow B). An offer, never forced.

## Persisted display preferences (DRV-8)

The dashboard remembers the user's **display preferences** (sort column and direction,
status filter, language filter, search text) between openings, via
`window.storage` — the persistent storage built into artifacts (key
`candidate-suite:dashboard:ui-prefs`, private to the user). Validated in real conditions on desktop +
web on 02/06 (storage shared across surfaces, an observed behavior not guaranteed by contract).

**Strict dividing line — never to cross:**
- `window.storage` = **display cache ONLY** (sort, filters, search). It **never**
  contains business data.
- The **applications** live in the **project CSV**, the only source of truth, read and
  written by `manage_tracker.py`. The reconciliation engine (workflow E, DRV-5) operates
  exclusively on the CSV.
- **Golden rule: if the cache and the CSV diverge, the CSV wins.** A filter preference
  that no longer matches any CSV value (a status/language that disappeared) is simply
  ignored by the `<select>` (falls back to "all"), with no error.

**Why this line:** putting business data into `window.storage` would make
`manage_tracker.py` (server-side) **blind** to that data (the storage lives in the
browser) — the whole DRV-5 reconciliation would collapse. The display cache, by contrast, costs
nothing to lose: at worst the user gets the default filters back, **never** a lost
application. This is precisely what makes this cache safe where a primary store would
not be.

**Clean degradation (mandatory):** the whole mechanism is best-effort. If `window.storage`
is absent (out-of-app preview, ephemeral mode, another tool), the dashboard applies the defaults
and works normally — no error, no blocking. `localStorage`/`sessionStorage`
are **forbidden** (blocked in claude.ai artifacts).

**Implementation (do not reimplement elsewhere):** entirely in `build_dashboard.py`, an
object of `loadUIPrefs` / `saveUIPrefs` / `applyUIPrefs` functions grafted onto the
**existing** UI state (`sortCol`, `sortDir`, the filter `<select>`s, `search`). Initial read
in `init()` **after** `populateFilters()` (the `<option>`s must exist) and **before** the
first `render()`. `window.storage`'s `get()` **throws** if the key is absent (it doesn't return
`null`) → mandatory `try/catch`, absence not being an error. No other layer,
no separate component.

## Important technical limits (worth knowing)
- The **dashboard cannot write** to the CSV (sandbox). The Save button sends a `sendPrompt`; Claude regenerates the CSV and the user adds it to the project. A two-step loop.
- **Filters and sort** are 100% local (instant) and now **persisted** as display preferences (DRV-8 above). Only a **status** change (business data) requires the CSV write loop.
- Ephemeral mode = **read-only**; the preferences cache degrades cleanly if there's no `window.storage`.
- `claude://` is **swallowed** by the widget's sandbox (custom link not honored) → never use it in the dashboard.


## Scripts

| Script | Usage |
|--------|-------|
| `manage_tracker.py init --output-dir /home/claude` | Blank CSV (script names it) |
| `manage_tracker.py upsert --input-path X --output-dir D --entry-json '...'` | 1 application (company/position key; script names it) |
| `manage_tracker.py bulk --input-path X --output-dir D --entries-json '[...]'` | N applications (script names it) |
| `manage_tracker.py batch-status --input-path X --output-dir D --changes-json '[...]'` | N status changes (company/position key; script names it) |
| `manage_tracker.py reconcile --input-path X --output-dir D --scan-json '[...]' [--floor YYYY-MM-DD] [--no-add-new]` | DRV-5 reconciliation: `◆→uuid` promotion, link union, `✗` on floor, new applications, `title` capture, hygiene report (script names it) |
| `build_dashboard.py --input-path X.csv --output-path D.html [--ui-lang code] [--labels-json '{…}']` | Editable dashboard (detects the surface; English-canonical base, `--labels-json` localizes the visible labels, exact key set) |
| `build_dashboard.py --data-json '[...]' --readonly --output-path D.html [--ui-lang code] [--labels-json '{…}']` | Read-only dashboard (ephemeral) |
| `build_guide.py --output-path G.html [--candidate-name …] [--ui-lang code] [--labels-json '{…}']` | Tracker usage guide (3 tabs; English-canonical base, `--labels-json` localizes the visible text, exact key set, no selector) |

## References
- `references/tracker_format.md`: CSV format, columns, 3 states, dashboard, refresh

## Important rules
- Manipulation **only via the scripts**; **no connector**
- Persistent mode = project CSV; ephemeral mode = scan + read-only
- Always **read the CSV with the most recent name before writing**
- Versioning with **unique timestamped names** (Paris time); the user adds/deletes
- **(company, position)** key → the assistant decides update vs add (asks if in doubt)
- Writing the conversation marker: `"YYYY-MM-DD ◆"` (date only); UUID set at refresh
- Only fill in **genuinely available** information
