# candidate-suite

An all-in-one Claude **skill** for preparing job applications and interviews:
cover letter, interview prep, application summary, strategic playbook, one-page
reference card, and application tracking, plus candidate-profile configuration.
A single entry point shows a selection widget, then generates each deliverable
through its sub-module's script.

---

## Install (for users) — no coding required

1. Go to the [**Releases**](../../releases) page.
2. Download the latest **`candidate-suite-<version>.skill`** asset.
3. Add it to your Claude project / install it as a skill in the Claude app.

That's it. The package contains **only fictional placeholder data**; you provide
your own profile, CV, and signature inside Claude — they stay in your own project
files and are never part of this package or repository.

---

## Privacy

- The published `.skill` and this repository ship **fictional placeholder data
  only** (`Jordan Lee-Carter`, `Acme Financial Group`, …).
- Your real data (CV, signature, application tracker CSV) lives in **your Claude
  project files**, not here. The [`.gitignore`](.gitignore) also blocks those file
  patterns as a safety net.

---

## Repository layout

```
.
├── SKILL.md  CHANGELOG.md  scripts/  modules/  references/   ← the skill (this is what gets packaged)
├── tooling/build_skill.py        ← formal packager → builds the .skill
├── examples/profile.example.md   ← placeholder profile (configuration shape)
├── tests/                        ← TST-1 acceptance suite (planned)
├── docs/                         ← roadmap and design notes
├── .github/workflows/release.yml ← CI: build + attach .skill on tag
├── README.md   .gitignore
```

Only the skill source (`SKILL.md`, `CHANGELOG.md`, `scripts/`, `modules/`,
`references/`) is packaged into the `.skill`. The meta folders never enter the
package.

---

## Build & release (for maintainers)

Build a `.skill` locally (output in `dist/`, which is git-ignored):

```bash
python tooling/build_skill.py
# -> dist/candidate-suite-<x-y-z>.skill   (version read from SKILL.md)
```

Cut a release (CI builds and attaches the asset automatically):

```bash
# 1. bump `version:` in SKILL.md and add a CHANGELOG entry
# 2. tag and push
git tag v0.16.2
git push origin v0.16.2
# GitHub Actions builds the .skill and publishes it on the Releases page
```

Packaging contract: archive entries prefixed `candidate-suite/`, DEFLATED,
excluding `__pycache__/`, `*.pyc`, `.DS_Store`. The Claude app registers the
skill on its frontmatter `name`, so a new build with the same `name` replaces it
in place.
