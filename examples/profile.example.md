# Example candidate profile (placeholder)

This file contains **fictional placeholder data only** (`Jordan Lee-Carter`).
It is committed to the repository on purpose, as documentation of the expected
configuration shape. **Never put your real data here** — your real profile is
stored in Claude's memory and in your own Claude project files, not in this repo.

To configure the skill, run the `candidate-config` workflow and provide your own
values; the lines below show the structure each entry follows.

```
[CONFIG] Storage method: project_files
[CONFIG] CV filename: CV_Jordan_Lee-Carter.docx
[CONFIG] Signature filename: signature_jordan_b64.txt
[CONFIG] Template filename: Cover_letter_template.docx
[CONFIG] Header style: hybrid
[CANDIDAT] First name: Jordan
[CANDIDAT] Last name: Lee-Carter
[CANDIDAT] Full name: Jordan Lee-Carter
[CANDIDAT] Street: 12 rue de la Paix
[CANDIDAT] Postal code: 75001
[CANDIDAT] City: Paris
[CANDIDAT] Email: jordan.lee@example.com
[CANDIDAT] Phone: +33 6 12 34 56 78
[CANDIDAT] LinkedIn: https://linkedin.com/in/jordan-lee-carter
```

Field reference: see `modules/candidate-config/references/memory_format.md`.
