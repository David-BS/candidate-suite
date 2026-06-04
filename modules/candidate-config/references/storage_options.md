# Persistence options

This skill supports **2 persistence modes** for the candidate's reference files.
**No connector** (a connector call can hang the session — see the roadmap). Textual
data (name, address, email) is stored in Claude's memory (via `memory_user_edits`),
independently of the chosen mode.

## 1. Project file (recommended)

### Description
The files (CV, signature, templates, tracker) are placed by the user in the current
**Claude project**'s files. They are then automatically available across every
conversation of the project.

### Access
- Files available under `/mnt/project/`
- Read: the `view` tool
- Write: **NOT POSSIBLE from Claude** (read-only) — the user adds/removes the files
  manually. That manual add is what grants **persistence AND consent**.

### Advantages
- Available to all Claude users (Pro, Team, Enterprise)
- No external setup, no connector
- The data stays inside the Claude environment
- Persistent across conversations of the same project

### Limits
- Scoped to one project (recreate it for another project)
- No write from Claude: regenerate then re-upload (unique timestamped-name ritual for
  the tracker)

### User workflow
1. Create a Claude project
2. Drop the needed files (CV, signature, templates; tracker if applicable)
3. Configure via this skill
4. Normal use across every conversation of the project

### Expected file list
- `CV_Full_<Name>.docx` (or .pdf)
- `Signature-<Initials>_jpg_b64.txt` (base64-encoded signature)
- `Cover_letter_template.docx` (neutral, single)
- (tracker) `Applications_Tracker_YYYY-MM-DD_HHMM.csv`

## 2. Stateless

### Description
No storage: the user re-uploads the needed files each session. In this mode the
tracker is a read-only **session view**.

### Advantages
- No setup
- Useful for a one-off trial

### Limits
- Everything must be re-provided each conversation
- No tracker persistence

## Google Drive — REMOVED

The Google Drive mode (and every connector) was **removed**: a connector call cannot
be bounded by instruction and can **hang the session** (spinner, unresponsive
`Stop`). Persistence now goes exclusively through the **project file**. Never
reintroduce a connector dependency without re-reading the roadmap note "Known
environment risk — hang on MCP connector call".
