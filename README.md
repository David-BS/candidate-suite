# candidate-suite

[![Download latest release](https://img.shields.io/badge/download-latest_release-brightgreen)](https://github.com/David-BS/candidate-suite/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**An all-in-one Claude skill for preparing job applications and interviews.**
From a single job posting, it produces a complete, consistent application package —
no manual writing, no copy-pasting between prompts.

What it generates, each from its own sub-module:

- ✉️ **Cover letter** (`.docx`, print-ready)
- 🎤 **Interview prep** guide
- 📄 **Application summary**
- ♟️ **Strategic playbook**
- 🗂️ **One-page reference card**
- 📊 **Application tracker** + dashboard

Plus a guided **candidate-profile setup** (CV, signature, header style) so every
deliverable is personalized to you.

---

## How it works

Faced with a vague request like *"help me apply to this role,"* the skill shows a
**selection widget** that turns the request into explicit choices, then generates
each chosen deliverable through its sub-module's script. Nothing is written by hand
or improvised — the structure is fixed, the content is yours.

The suite is **language-agnostic**: the working language follows your conversation,
and deliverables follow the job posting's language.

---

## Scope & compatibility

candidate-suite is built for the **Anthropic Claude ecosystem** and runs inside the
Claude app. It relies on the Claude skills runtime: a sandboxed code-execution
environment that runs its bundled scripts, the in-chat selection widget, and the
app's file delivery. **It is not compatible with other AI assistants.**

The `SKILL.md` packaging format is becoming a cross-vendor standard, so the *manifest*
is portable — but this skill's engine is **script-driven**: its scripts are the source
of truth and produce every deliverable. Running it therefore requires a host that
executes those scripts and renders the widget, which today means the Claude ecosystem.
Assistants that treat skills as instructions only, or whose sandboxes lack the required
libraries, cannot run it.

---

## Download & install

> **Requirements:** a Claude account (the skill runs inside the Claude app). No
> coding or local setup required.

1. Go to the [**latest release**](https://github.com/David-BS/candidate-suite/releases/latest).
2. Download the **`candidate-suite-<version>.skill`** asset.
3. Add it to your Claude project / install it as a skill in the Claude app.

Each release also attaches a **`candidate-suite-samples-<version>.zip`** — an
acceptance gallery with one example of every deliverable (fictional data), to
preview what the skill produces.

That's it. Then just ask Claude for help with an application and follow the widget.

---

## Privacy

- The published `.skill` and this repository ship **fictional placeholder data
  only** (`Jordan Lee-Carter`, `Acme Financial Group`, …).
- **Your real data** (CV, signature, application tracker) lives in **your own Claude
  project files** — never in this package or repository.
- The [`.gitignore`](.gitignore) blocks personal-data file patterns as a safety net.

---

## Repository layout

```
.
├── SKILL.md  CHANGELOG.md  scripts/  modules/  references/   ← the skill (this is what gets packaged)
├── tooling/build_skill.py        ← formal packager → builds the .skill
├── tooling/build_samples.py      ← builds the acceptance gallery (release samples)
├── examples/profile.example.md   ← placeholder profile (configuration shape)
├── tests/                        ← acceptance suite (TST-1, pytest)
├── docs/                         ← design notes
├── .github/workflows/release.yml ← CI: build + attach .skill on tag
├── .github/dependabot.yml        ← keeps the CI actions up to date
├── README.md   LICENSE   .gitignore
```

Only the skill source (`SKILL.md`, `CHANGELOG.md`, `scripts/`, `modules/`,
`references/`) is packaged into the `.skill`. The meta folders never enter the package.

---

## Build & release (for maintainers)

Build a `.skill` locally (output in `dist/`, which is git-ignored):

```bash
python tooling/build_skill.py
# -> dist/candidate-suite-<x-y-z>.skill   (version read from SKILL.md)
```

Cut a release — CI builds the `.skill` and attaches it to the Releases page automatically:

```bash
# 1. bump `version:` in SKILL.md and add a CHANGELOG entry
# 2. tag and push
git tag v0.16.2
git push origin v0.16.2
```

Packaging contract: archive entries prefixed `candidate-suite/`, DEFLATED, excluding
`__pycache__/`, `*.pyc`, `.DS_Store`. The Claude app registers the skill on its
frontmatter `name`, so a new build with the same `name` replaces it in place.

---

## License

Released under the [MIT License](LICENSE). You're free to use, modify, and share it;
attribution is appreciated.
