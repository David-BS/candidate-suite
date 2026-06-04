# Tests — TST-1 (planned)

This folder will hold **TST-1 — the replayable user-acceptance suite**: generic,
exhaustive scenarios that exercise the whole suite end to end, to be **replayed at
every official release** as a true acceptance pass.

Status: **planned.** It will be built once the roadmap objective is reached, then
committed here and wired into the release process (see
`.github/workflows/release.yml`) so each tagged release runs it.

Scope sketch (to be refined when built):
- Config: profile setup, CV/signature resolution, header styles.
- Deliverables: cover letter (.docx), interview prep, summary, playbook, quick-ref.
- Tracker: init, upsert, batch-status, reconcile (marker promotion / deletion /
  floor), dashboard render.
- Language: model-driven extraction, surface localization, sentinel guards.
- All scenarios use fictional placeholder data only — never real candidate data.
