"""Acceptance gallery — one example of every deliverable, from fictional data.

Run at release time (see release.yml); the resulting folder is zipped and
attached to the GitHub Release so each version ships a reviewable set of
"delivery acceptance" pieces ("Conditions d'Acceptation de livraison"):
inspect on sight that nothing visible broke.

What it produces (all data is FICTIONAL — Jordan Lee-Carter / Acme):
- a long cover letter filled with Lorem ipsum calibrated to ~2800 chars and the
  paragraph ratios (15/22/26/22/15), in two variants: signed / unsigned, each
  as .docx and .pdf;
- one of each Markdown deliverable (summary / interview / playbook / quick-ref),
  each as .md and .pdf;
- the four HTML surfaces (dashboard, preferences=config, selector, guide),
  wrapped in a base-CSS review harness so they render close to the in-app look
  (the surfaces themselves stay unchanged — they rely on the app's design
  tokens; the harness only *supplies* those tokens for standalone viewing).

The companion test `tests/test_examples.py` regenerates the cover letters in a
temp dir on every run and asserts the acceptance conditions, so a regression is
caught even between releases.
"""

import argparse
import glob
import json
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    REPO_ROOT / "modules/cover-letter-generator/assets/Cover_letter_template.docx"
)
SEED_CSV = REPO_ROOT / "tests/_data/tracker_seed.csv"

# Body-paragraph character targets = ratio (15/22/26/22/15) × 2800.
RATIO_TARGETS = {
    "paragraph_1_intro": 420,
    "paragraph_2_current": 616,
    "paragraph_3_experience": 728,
    "paragraph_4_value": 616,
    "paragraph_5_closing": 420,
}

_LOREM = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam "
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo "
    "consequat duis aute irure dolor in reprehenderit in voluptate velit esse "
    "cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non "
    "proident sunt in culpa qui officia deserunt mollit anim id est laborum "
).split()


def lorem(target):
    """A Lorem ipsum string just under `target` chars, on a word boundary."""
    words, total, i = [], 0, 0
    while True:
        w = _LOREM[i % len(_LOREM)]
        if total + len(w) + 1 > target:
            break
        words.append(w)
        total += len(w) + 1
        i += 1
    text = " ".join(words)
    return text[:1].upper() + text[1:] + "."


def lorem_letter_data(signed):
    """Cover-letter payload: realistic header (fictional), Lorem ipsum body sized
    to the ratio targets. `signed` only documents the variant; the signature is
    passed separately via --signature-path."""
    data = {
        "sender_name": "Jordan Lee-Carter",
        "sender_street": "12 Rue de l'Exemple",
        "sender_postal_code": "75000",
        "sender_city": "Paris",
        "sender_email": "jordan.lee@example.com",
        "sender_phone": "+33 6 00 00 00 00",
        "sender_linkedin": "linkedin.com/in/jordan-lee-carter",
        "sender_full_name": "Jordan Lee-Carter",
        "recruiter_name": "Jane Smith",
        "recruiter_title": "Head of Talent",
        "company_name": "Acme Financial Group",
        "date_letter": "5 June 2026",
        "job_title": "Head of Engineering",
        "greeting": "Dear Ms Smith,",
        "subject_label": "Subject:",
        "closing": "Yours sincerely,",
    }
    for field, target in RATIO_TARGETS.items():
        data[field] = lorem(int(target * 0.98))
    return data


def signature_b64():
    """A valid fictional signature PNG (8x4, stdlib only), base64-encoded."""
    import base64
    import struct
    import zlib

    w, h = 8, 4

    def _chunk(tag, payload):
        c = tag + payload
        return (
            struct.pack(">I", len(payload))
            + c
            + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _ in range(h))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )
    return base64.b64encode(png).decode()


# --- review harness: supply the app design tokens for standalone viewing ---- #

_HARNESS_CSS = """
:root {
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  --color-background-primary: #ffffff;
  --color-background-secondary: #f5f4ee;
  --color-background-info: #eef4fb;
  --color-border-primary: #d9d7ce;
  --color-border-secondary: #e5e3da;
  --color-border-tertiary: #ecebe4;
  --color-border-info: #c7dbf0;
  --color-text-primary: #1f1e1c;
  --color-text-secondary: #4a4a44;
  --color-text-tertiary: #84847b;
  --color-text-success: #2f7a4d;
  --color-text-info: #2563a8;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--color-text-primary);
  background: #faf9f5;
  margin: 0;
  padding: 24px;
}
.cs-review { max-width: 760px; margin: 0 auto; }
.cs-review button {
  font: inherit; cursor: pointer; padding: 6px 12px;
  border: 0.5px solid var(--color-border-primary);
  border-radius: var(--border-radius-md);
  background: var(--color-background-primary);
  color: var(--color-text-primary);
}
.cs-banner {
  max-width: 760px; margin: 0 auto 16px; padding: 8px 12px;
  border: 0.5px solid var(--color-border-info);
  background: var(--color-background-info);
  color: var(--color-text-info);
  border-radius: var(--border-radius-md);
  font: 13px/1.4 -apple-system, sans-serif;
}
"""

_HARNESS_JS = (
    "window.sendPrompt = window.sendPrompt || function (t) {"
    " alert('(review harness) sendPrompt would send:\\n\\n' + t); };"
)


def wrap_html(fragment, title):
    """Wrap a surface fragment in a self-contained page with the base CSS."""
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title} — review</title>\n<style>{_HARNESS_CSS}</style>\n</head>\n<body>\n"
        f'<div class="cs-banner">Review harness — fictional data. Base CSS supplied '
        f"locally; in the app these tokens come from the host theme.</div>\n"
        f'<div class="cs-review">\n{fragment}\n</div>\n'
        f"<script>{_HARNESS_JS}</script>\n</body>\n</html>\n"
    )


# --- generator payloads (fictional) ---------------------------------------- #

_BASE = {
    "candidate_name": "Jordan Lee-Carter",
    "job_title": "Head of Engineering",
    "company_name": "Acme Financial Group",
    "date": "5 June 2026",
}

_GENERATORS = {
    "03_application_summary": {
        "module": "application-summary-generator",
        "labels": {
            "title": "Application Summary",
            "section_sw": "Strengths & Weaknesses",
            "sub_strengths": "Strengths",
            "sub_weaknesses": "Weaknesses",
            "section_pitch": "Pitch (5 sentences)",
            "pitch_intro": "Your concise positioning:",
            "section_tp": "Talking Points",
            "tp_intro": "Key messages to land:",
        },
        "data": dict(
            _BASE,
            strengths=[
                {
                    "title": "Scaled delivery",
                    "context": "Led a 150-person agile org across 8 squads.",
                },
                {
                    "title": "Payments at scale",
                    "context": "Ran engines at 2B+ tx/year, 99%+ SLA.",
                },
            ],
            weaknesses=[
                {
                    "title": "Public speaking",
                    "approach": "Coached; now presents to steering committees.",
                }
            ],
            pitch=[
                "I lead large banking-IT organisations.",
                "I ship reliable payment platforms at scale.",
                "I cut incidents by 80% through engineering rigour.",
                "I align squads around product outcomes.",
                "I would bring that to Acme's modernisation.",
            ],
            talking_points=[
                {
                    "title": "Reliability",
                    "content": "99%+ SLA on critical payment flows.",
                },
                {
                    "title": "Transformation",
                    "content": "Drove a SAFe transition across 14 teams.",
                },
            ],
        ),
    },
    "04_interview_prep": {
        "module": "interview-prep-generator",
        "labels": {
            "title": "Interview Preparation",
            "screening_header": "Screening Questions",
            "screening_objective": "Goal: confirm fit and motivation.",
            "competence_header": "Competency Questions",
            "competence_objective": "Goal: show depth with concrete examples.",
            "question_label": "Question",
            "answer_label": "Suggested answer",
        },
        "data": dict(
            _BASE,
            screening_questions=[
                {
                    "question": "Why Acme?",
                    "answer": "Your payments modernisation matches my track record.",
                    "tip": "Tie to a concrete Acme initiative.",
                },
                {
                    "question": "Why leave your current role?",
                    "answer": "Seeking broader scope on a platform transformation.",
                },
            ],
            competence_questions=[
                {
                    "question": "Describe a major incident you handled.",
                    "answer": "Led the response to a payment outage; cut recurrence by 80%.",
                },
                {
                    "question": "How do you run an agile org at scale?",
                    "answer": "Product squads + transversal chapters, clear outcome metrics.",
                },
            ],
        ),
    },
    "05_strategic_playbook": {
        "module": "strategic-playbook-generator",
        "labels": {
            "title": "Strategic Playbook",
            "web_note_yes": "Based on web research.",
            "web_note_no": "No web research — verify externally.",
            "usage_tip": "Use before and during the interview.",
            "s_context": "Company Context",
            "s_pain": "Pain Points",
            "s_org": "Org Landscape",
            "s_positioning": "Positioning",
            "s_strategy": "Interview Strategy",
            "s_questions": "Questions to Ask",
            "s_tough": "Tough Questions",
            "s_pitch": "30-Second Pitch",
            "s_redlines": "Red Lines",
            "analysis": "Analysis",
            "your_angle": "Your angle",
            "evidence": "Evidence",
            "round": "Round",
            "focus": "Focus",
            "approach": "Approach",
            "strategy": "Strategy",
        },
        "data": dict(
            _BASE,
            web_research_done=True,
            company_context="Acme is a mid-size European bank modernising its payments stack.",
            pain_points=[
                {
                    "title": "Legacy core",
                    "analysis": "Monolith slows delivery.",
                    "your_angle": "I've led incremental strangler migrations.",
                }
            ],
            org_landscape="The CIO leads ~600 people; the platform tribe is reorganising around product squads.",
            positioning=[
                {
                    "message": "Reliability-first leader",
                    "evidence": "80% incident reduction on payment engines.",
                }
            ],
            interview_strategy=[
                {
                    "round": "First round",
                    "focus": "Track record",
                    "approach": "Lead with measurable outcomes.",
                }
            ],
            questions_to_ask=[
                "How is the platform tribe structured?",
                "What does success look like in 6 months?",
            ],
            tough_questions=[
                {
                    "question": "Your team is large — are you hands-on?",
                    "strategy": "Show selective deep dives on critical systems.",
                }
            ],
            thirty_second_pitch="I help banking-IT organisations ship reliable payment platforms at scale, cutting incidents while accelerating delivery.",
            red_lines=[
                "No relocation outside Île-de-France.",
                "Need ownership of the platform roadmap.",
            ],
        ),
    },
    "06_quick_reference": {
        "module": "quick-reference-generator",
        "labels": {
            "title": "Quick Reference Card",
            "s_pitch": "Pitch",
            "s_stats": "Key Stats",
            "s_points": "Top Points",
            "s_qa": "Quick Q&A",
            "s_questions": "Questions to Ask",
            "s_checklist": "Checklist",
            "evidence": "Evidence",
        },
        "data": dict(
            _BASE,
            pitch_short="20 years in banking IT; led payment platforms at 2B+ tx/year, 99%+ SLA.",
            key_stats=[
                "2B+ transactions/year",
                "99%+ SLA",
                "80% incident reduction",
                "150-person org",
            ],
            top_points=[
                {
                    "point": "Reliability at scale",
                    "evidence": "99%+ SLA on critical flows.",
                },
                {
                    "point": "Transformation",
                    "evidence": "SAFe rollout across 14 teams.",
                },
                {"point": "Cost discipline", "evidence": "€32M budget managed."},
            ],
            quick_qa=[
                {"q": "Why Acme?", "a": "Payments modernisation fits my track record."},
                {"q": "Biggest strength?", "a": "Scaling reliable delivery."},
            ],
            questions_to_ask=[
                "How is the tribe structured?",
                "What are the top 3 priorities?",
            ],
            checklist=[
                "Re-read the JD",
                "Prepare 2 STAR stories",
                "List 5 questions",
                "Confirm logistics",
            ],
        ),
    },
}

_SURFACES = {
    "07_dashboard": {
        "script": "modules/application-tracker/scripts/build_dashboard.py",
        "args": ["--input-path", str(SEED_CSV)],
        "title": "Application Dashboard",
    },
    "08_preferences_config": {
        "script": "scripts/build_preferences.py",
        "args": [],
        "title": "Preferences (configuration)",
    },
    "09_selector": {
        "script": "scripts/build_selector.py",
        "args": [],
        "title": "Deliverable Selector",
    },
    "10_guide": {
        "script": "modules/application-tracker/scripts/build_guide.py",
        "args": ["--candidate-name", "Jordan Lee-Carter"],
        "title": "Tracker Guide",
    },
}


def _run(rel, *args):
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / rel), *map(str, args)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{rel} failed (exit {proc.returncode}):\n{proc.stderr}")
    return proc


def build_all(output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    produced = []

    # Cover letters: signed + unsigned, .docx + .pdf
    sig_file = out / ".signature_b64.txt"
    sig_file.write_text(signature_b64(), encoding="utf-8")
    cl = "modules/cover-letter-generator/scripts/fill_cover_letter.py"
    d2p = "modules/cover-letter-generator/scripts/docx_to_pdf.py"
    for name, signed in (
        ("01_cover_letter_lorem_signed", True),
        ("02_cover_letter_lorem_unsigned", False),
    ):
        docx = out / f"{name}.docx"
        extra = ["--signature-path", str(sig_file)] if signed else []
        _run(
            cl,
            "--language",
            "en",
            "--template-path",
            TEMPLATE,
            "--output-path",
            docx,
            "--data-json",
            json.dumps(lorem_letter_data(signed)),
            *extra,
        )
        _run(d2p, "--input", docx, "--output", out / f"{name}.pdf")
        produced += [docx, out / f"{name}.pdf"]
    sig_file.unlink(missing_ok=True)

    # Markdown deliverables: .md + .pdf
    for name, spec in _GENERATORS.items():
        gen = glob.glob(
            str(REPO_ROOT / f"modules/{spec['module']}/scripts/generate_*.py")
        )[0]
        gen_rel = str(Path(gen).relative_to(REPO_ROOT))
        md = out / f"{name}.md"
        _run(
            gen_rel,
            "--language",
            "en",
            "--output-path",
            md,
            "--data-json",
            json.dumps(spec["data"], ensure_ascii=False),
            "--labels-json",
            json.dumps(spec["labels"], ensure_ascii=False),
        )
        conv = list(
            (REPO_ROOT / f"modules/{spec['module']}/scripts").glob("md_to_pdf.py")
        )
        if conv:
            conv_rel = str(conv[0].relative_to(REPO_ROOT))
            _run(conv_rel, "--input", md, "--output", out / f"{name}.pdf")
            produced.append(out / f"{name}.pdf")
        produced.append(md)

    # HTML surfaces, wrapped in the review harness
    tmp_html = out / ".surface.html"
    for name, spec in _SURFACES.items():
        _run(spec["script"], "--output-path", tmp_html, *spec["args"])
        styled = out / f"{name}.html"
        styled.write_text(
            wrap_html(tmp_html.read_text(encoding="utf-8"), spec["title"]),
            encoding="utf-8",
        )
        produced.append(styled)
    tmp_html.unlink(missing_ok=True)

    return produced


def main():
    ap = argparse.ArgumentParser(
        description="Build the acceptance gallery (fictional samples)."
    )
    ap.add_argument("--output-dir", default="dist/samples")
    ap.add_argument(
        "--zip", default="", help="Optional path to also write a .zip of the gallery."
    )
    args = ap.parse_args()

    produced = build_all(args.output_dir)
    print(f"✅ {len(produced)} sample(s) written to {args.output_dir}")
    for p in produced:
        print(f"   - {Path(p).name}")

    if args.zip:
        zpath = Path(args.zip)
        zpath.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in produced:
                z.write(p, arcname=Path(p).name)
        print(f"✅ zipped → {zpath}")


if __name__ == "__main__":
    main()
