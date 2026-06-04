# Application assistant flow

## Overview

`candidate-suite` is the suite's **orchestrator**. It generates no document
itself: it captures the user's choices through a selection widget, then the
widget composes a directive prompt that Claude executes by delegating to the
specialized **sub-modules**.

```
Open-ended request
   │
   ▼
[Claude] reads memory + config + already-generated deliverables
   │
   ▼
[Widget] memory block + job posting + checkboxes  ← the user selects
   │  (on Generate)
   ▼
[sendPrompt] closed, visible, ordered prompt
   │
   ▼
[Claude] Mode A: single global analysis → generates each deliverable via its script
   │
   ▼
[Widget] re-displayed (deliverables marked "already generated") → can be re-run
```

## The 6 standard deliverables (fixed ids)

| id | Sub-module | Note |
|----|------------|------|
| strategic_playbook | strategic-playbook-generator | |
| application_summary | application-summary-generator | |
| interview_prep | interview-prep-generator | |
| cover_letter | cover-letter-generator | .docx |
| quick_reference | quick-reference-generator | condenses the others → second to last |
| add_to_tracker | application-tracker | always last |

## Enforced generation order

`strategic_playbook → application_summary → interview_prep → cover_letter →
quick_reference → add_to_tracker`

The quick reference (quick_reference) condenses the other documents, so it must
be generated after them. Adding to the tracker comes at the very end (an
application exists once its tools have been produced).

## Format of the prompt composed by the widget

The Generate button builds a text message (sent via `sendPrompt`, so visible in
the chat) of this shape:

```
Generate the following application tools by running the scripts of the
corresponding sub-modules (one deliverable = one sub-module, via its Python
script; write nothing by hand):
1. <deliverable label>  [module: <module-id>]
2. <deliverable label>  [module: <module-id>]
...

Follow the stated order (the quick reference last, since it condenses the
others; adding to the tracker at the very end). Mode A: single global analysis
(CV + job posting + web if available), then generate everything without
intermediate validation. Offer PDF export at the end.

Job posting:
<text pasted by the user, if provided>
```

> The deliverable labels and the surrounding wording are rendered in the **UI
> language** (the widget's user-facing strings). This document describes the
> *structure*, not a specific configuration's rendered text. The `[module: …]`
> tag carries the language-neutral sub-module id used for routing.

## Memory block — format

`--memory-json` expects a list of `{id, label, value}` objects:
```json
[
  {"id": "profile", "label": "Profile", "value": "Jordan Lee-Carter — 12 yrs in IT, Acme Financial Group"},
  {"id": "cv", "label": "CV", "value": "CV_Jordan_Lee-Carter.docx"},
  {"id": "applications", "label": "Tracked applications", "value": "6"}
]
```
Claude fills this block from its memory. Presented as "non-exhaustive."
Empty list → the widget shows "no items in memory."
Memory paused (`--memory-active false`) → the widget shows "Memory paused."

## Enhancements beyond the 6 deliverables

The skill offers no non-standard deliverables through the widget. If a
complementary analysis seems relevant (for example a stakeholder angle on an
exposed role), Claude proposes it verbally **after** generation, and the user
decides at that point.
