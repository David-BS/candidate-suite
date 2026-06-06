"""
Generates a Quick Reference Card (1-page sheet) in Markdown.
PDF export possible via md_to_pdf.py.

Usage:
    python generate_quick_reference.py \\
        --language en|fr \\
        --output-path /path/to/output.md \\
        --data-json '<json_string>'

See references/quickref_structure.md for the JSON structure.
Only the metadata (candidate_name, job_title, company_name, date) is mandatory;
all content sections are optional.
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
    "s_pitch",
    "s_stats",
    "s_points",
    "s_qa",
    "s_questions",
    "s_checklist",
    "evidence",
}


def pick(d, *keys):
    """Returns the first non-empty value among several possible key names.
    Tolerates the naming variants Claude might use.
    """
    if not isinstance(d, dict):
        return ""
    for k in keys:
        v = d.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


# Warnings collected during generation (empty entries ignored)
warnings = []


def generate_quickref_md(labels, data):
    t = labels
    parts = []
    warnings.clear()

    # Header
    parts.append(f"# {t['title']}\n")
    parts.append(
        f'<p class="meta">{data.get("candidate_name", "")} — {data.get("job_title", "")} — {data.get("company_name", "")}</p>'
    )
    parts.append(f'<p class="meta-date">{data.get("date", "")}</p>\n')

    # Short pitch (boxed to highlight it)
    if data.get("pitch_short"):
        parts.append(f"## {t['s_pitch']}\n")
        parts.append(f"> [!TIP-BOX] {data['pitch_short']}\n")

    # Key stats (2-column layout downstream → structural marker .col2, language-neutral)
    if data.get("key_stats"):
        parts.append(f"## {t['s_stats']} {{: .col2 }}\n")
        for stat in data["key_stats"]:
            if isinstance(stat, dict):
                fig = pick(stat, "stat", "figure", "value", "number", "kpi")
                ctx = pick(stat, "context", "detail", "label", "description")
                parts.append(f"- **{fig}** — {ctx}" if ctx else f"- {fig}")
            else:
                parts.append(f"- {stat}")
        parts.append("")

    # Top points
    if data.get("top_points"):
        rendered = []
        for i, tp in enumerate(data["top_points"], start=1):
            point = pick(tp, "point", "title", "argument", "text")
            ev = pick(tp, "evidence", "proof", "context", "detail")
            if not point:
                warnings.append(f"top_points[{i}] ignored: empty 'point' field")
                continue
            if ev:
                rendered.append(f"{i}. **{point}** — {t['evidence']} : {ev}")
            else:
                rendered.append(f"{i}. **{point}**")
        if rendered:
            parts.append(f"## {t['s_points']}\n")
            parts.extend(rendered)
            parts.append("")

    # Quick Q&A
    if data.get("quick_qa"):
        rendered = []
        for i, qa in enumerate(data["quick_qa"], start=1):
            q = pick(qa, "q", "question", "Q")
            a = pick(qa, "a", "answer", "A", "response")
            if not q and not a:
                warnings.append(f"quick_qa[{i}] ignored: empty question and answer")
                continue
            if q and a:
                rendered.append(f"- **{q}** → {a}")
            elif q:
                rendered.append(f"- **{q}**")
            else:
                rendered.append(f"- {a}")
        if rendered:
            parts.append(f"## {t['s_qa']}\n")
            parts.extend(rendered)
            parts.append("")

    # Questions to ask
    if data.get("questions_to_ask"):
        parts.append(f"## {t['s_questions']}\n")
        for q in data["questions_to_ask"]:
            parts.append(f"- {q}")
        parts.append("")

    # Checklist (checkboxes; 2-column layout downstream → structural marker .col2)
    if data.get("checklist"):
        parts.append(f"## {t['s_checklist']} {{: .col2 }}\n")
        for item in data["checklist"]:
            parts.append(f"- [ ] {item}")
        parts.append("")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generates a quick reference card in Markdown"
    )
    parser.add_argument(
        "--language",
        required=True,
        type=iso639_1,
        metavar="LANG",
        help="ISO 639-1 language code (lowercase), e.g. en, fr",
    )
    parser.add_argument("--output-path", required=True)
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

    required = ["candidate_name", "job_title", "company_name", "date"]
    missing = [f for f in required if f not in data]
    if missing:
        print(f"❌ Missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)

    # Completeness validation: a reference card that condenses the other docs
    # must be substantial. We reject a near-empty card (e.g.: only key_stats).
    content_sections = [
        "pitch_short",
        "key_stats",
        "top_points",
        "quick_qa",
        "questions_to_ask",
        "checklist",
    ]
    filled = [k for k in content_sections if data.get(k)]
    has_pitch = bool(data.get("pitch_short"))
    # Criterion: pitch present AND at least 4 of 6 content sections
    if not has_pitch or len(filled) < 4:
        print("❌ Incomplete reference card — generation refused.", file=sys.stderr)
        print(
            f"   Filled sections: {filled or 'none'} ({len(filled)}/6).",
            file=sys.stderr,
        )
        print(
            "   The reference card CONDENSES the other documents: it must contain at least",
            file=sys.stderr,
        )
        print(
            "   the pitch (pitch_short) AND at least 4 sections among: pitch_short, key_stats,",
            file=sys.stderr,
        )
        print("   top_points, quick_qa, questions_to_ask, checklist.", file=sys.stderr)
        print(
            "   → Take the key points from the already-generated documents (playbook, summary,",
            file=sys.stderr,
        )
        print(
            "     interview prep) and regenerate with a complete JSON.", file=sys.stderr
        )
        sys.exit(2)

    md_content = generate_quickref_md(labels, data)

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding="utf-8")

    sections = [
        k
        for k in [
            "pitch_short",
            "key_stats",
            "top_points",
            "quick_qa",
            "questions_to_ask",
            "checklist",
        ]
        if data.get(k)
    ]
    print(f"✅ Quick reference card (Markdown) generated: {output_path}")
    print(f"   - {len(sections)} sections: {', '.join(sections)}")

    # Warn about ignored empty entries (avoids silent "**** →")
    if warnings:
        print(f"\n⚠️  {len(warnings)} entry(ies) ignored (empty or misnamed):")
        for w in warnings:
            print(f"   - {w}")
        print("   → Check the JSON: expected keys are 'point'/'evidence' (top_points)")
        print("     and 'q'/'a' (quick_qa). Regenerate with the fields filled.")

    print("\n💡 To export to PDF:")
    print(
        f"   python md_to_pdf.py --input {output_path} --output {output_path.with_suffix('.pdf')}"
    )


if __name__ == "__main__":
    main()
