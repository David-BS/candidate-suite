"""
Generates a Markdown interview-preparation document.
The Markdown uses styling conventions recognized by md_to_pdf.py
(palette, boxed/bordered tips) for an optional styled PDF export.

Usage:
    python generate_interview_prep.py \\
        --language en|fr \\
        --output-path /path/to/output.md \\
        --data-json '<json_string>'

The --data-json JSON must contain:
    - candidate_name, job_title, company_name, date
    - screening_questions : [{"question": "...", "answer": "...", "tip": "..."(opt)}, ...]
    - competence_questions : [{"question": "...", "answer": "...", "tip": "..."(opt)}, ...]
    - opening_tip_screening (opt), opening_tip_competence (opt), closing_tip (opt)

Markdown conventions produced (interpreted by md_to_pdf.py):
    - Boxed tips (α)    : > [!TIP-BOX] text
    - Bordered tips (γ.3) : > [!TIP] text
    - Question/Answer labels via colored <span>
"""

import argparse
import re


def iso639_1(value):
    """Validate --language as an ISO 639-1 *form*: two lowercase letters.

    Open by design (LNG-1 L5) — no maintained list, no external dependency. Post-L6 there is no per-language lock: the .md generators validate the
    model-provided label *key set* (`--labels-json`), not the language, and the letter
    fills a single neutral template. `--language` is form-validated metadata only; any
    ISO code works.
    """
    if not re.fullmatch(r"[a-z]{2}", value or ""):
        raise argparse.ArgumentTypeError(
            f"--language must be a 2-letter ISO 639-1 code (lowercase), e.g. en, fr; got: {value!r}"
        )
    return value


import json
import sys
from pathlib import Path


# Fixed label set = the deliverable's STRUCTURE. The model supplies the localized
# VALUES via --labels-json (target language); the script only enforces that the
# key set is EXACTLY this — no invented or omitted section (anti-hallucination
# guardrail). The structure is fixed; only the linguistic realization is the model's.
REQUIRED_LABELS = {
    "title",
    "screening_header",
    "screening_objective",
    "competence_header",
    "competence_objective",
    "question_label",
    "answer_label",
}


def format_answer(answer_text):
    """Formats the answer. If it contains lines starting with -, • or *,
    they are converted into clean Markdown bullets.
    Otherwise, a simple paragraph.
    Returns the Markdown with the colored answer-label span (`{answer_label}` placeholder, filled by the caller).
    """
    lines = answer_text.split("\n")
    has_bullets = any(line.strip().startswith(("-", "•", "*")) for line in lines)

    if has_bullets:
        intro_lines = []
        bullet_lines = []
        in_bullets = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("-", "•", "*")):
                in_bullets = True
                bullet_lines.append(stripped.lstrip("-•* ").strip())
            elif not in_bullets:
                intro_lines.append(line)

        intro = " ".join(ln.strip() for ln in intro_lines if ln.strip())

        md = '<span class="a-label">{answer_label} :</span>'
        if intro:
            md += f" {intro}"
        md += "\n\n"
        for bullet in bullet_lines:
            md += f"- {bullet}\n"
        return md
    else:
        return f'<span class="a-label">{{answer_label}} :</span> {answer_text}\n'


def build_question_block(q_label, a_label, index, qa):
    """Builds the Markdown block for a question/answer + optional tip."""
    question = qa.get("question", "")
    answer = qa.get("answer", "")
    tip = qa.get("tip")

    md = f'<p><span class="q-label">{q_label} {index} —</span> <strong>{question}</strong></p>\n\n'

    # Answer (handles bullets)
    answer_md = format_answer(answer).replace("{answer_label}", a_label)
    md += answer_md + "\n"

    # Contextual tip (γ.3)
    if tip:
        md += f"> [!TIP] {tip}\n\n"

    return md


def generate_interview_prep_md(labels, data):
    """Generates the complete Markdown content."""
    t = labels

    parts = []

    # Title + meta
    parts.append(f"# {t['title']}\n")
    parts.append(
        f'<p class="meta">{data.get("candidate_name", "")} — {data.get("job_title", "")} — {data.get("company_name", "")}</p>'
    )
    parts.append(f'<p class="meta-date">{data.get("date", "")}</p>\n')

    # === INTERVIEW 1 ===
    parts.append(f"## {t['screening_header']}\n")
    parts.append(f"*{t['screening_objective']}*\n")

    opening_screening = data.get("opening_tip_screening")
    if opening_screening:
        parts.append(f"> [!TIP-BOX] {opening_screening}\n")

    for i, qa in enumerate(data.get("screening_questions", []), start=1):
        parts.append(
            build_question_block(t["question_label"], t["answer_label"], i, qa)
        )

    # === INTERVIEW 2 ===
    parts.append(f"## {t['competence_header']}\n")
    parts.append(f"*{t['competence_objective']}*\n")

    opening_competence = data.get("opening_tip_competence")
    if opening_competence:
        parts.append(f"> [!TIP-BOX] {opening_competence}\n")

    for i, qa in enumerate(data.get("competence_questions", []), start=1):
        parts.append(
            build_question_block(t["question_label"], t["answer_label"], i, qa)
        )

    # Closing tip
    closing = data.get("closing_tip")
    if closing:
        parts.append(f"> [!TIP-BOX] {closing}\n")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generates an interview-prep document in Markdown"
    )
    parser.add_argument(
        "--language",
        required=True,
        type=iso639_1,
        metavar="LANG",
        help="ISO 639-1 language code (lowercase), e.g. en, fr",
    )
    parser.add_argument("--output-path", required=True, help="Output .md path")
    parser.add_argument("--data-json", required=True)
    parser.add_argument(
        "--labels-json",
        required=True,
        help="JSON object of structure labels in the target language (exact key set required)",
    )

    args = parser.parse_args()

    try:
        data = json.loads(args.data_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        labels = json.loads(args.labels_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON (labels): {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(labels, dict) or set(labels) != REQUIRED_LABELS:
        got = set(labels) if isinstance(labels, dict) else set()
        print(
            f"❌ Invalid labels — missing: {sorted(REQUIRED_LABELS - got)}; extra: {sorted(got - REQUIRED_LABELS)}",
            file=sys.stderr,
        )
        sys.exit(1)

    required = [
        "candidate_name",
        "job_title",
        "company_name",
        "date",
        "screening_questions",
        "competence_questions",
    ]
    missing = [f for f in required if f not in data]
    if missing:
        print(f"❌ Missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)

    md_content = generate_interview_prep_md(labels, data)

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding="utf-8")

    print(f"✅ Interview prep (Markdown) generated: {output_path}")
    print(f"   - {len(data.get('screening_questions', []))} screening questions")
    print(f"   - {len(data.get('competence_questions', []))} competence questions")
    print("\n💡 To export to PDF:")
    print(
        f"   python md_to_pdf.py --input {output_path} --output {output_path.with_suffix('.pdf')}"
    )


if __name__ == "__main__":
    main()
