"""
Generates a Markdown application-summary document.
The Markdown uses styling conventions recognized by md_to_pdf.py
(palette, tips, semantic headings) for an optional styled PDF export.

Usage:
    python generate_application_summary.py \\
        --language en|fr \\
        --output-path /path/to/output.md \\
        --data-json '<json_string>'

The --data-json JSON must contain:
    - candidate_name, job_title, company_name, date
    - strengths : [{"title": "...", "context": "..."}, ...] (max 5)
    - weaknesses : [{"title": "...", "approach": "..."}, ...] (max 3)
    - pitch : [str, str, str, str, str] (exactly 5 sentences)
    - talking_points : [{"title": "...", "content": "..."}, ...] (5-8)
    - opening_tip (opt), tip_after_weaknesses (opt),
      tip_after_pitch (opt), tip_after_talking_points (opt)

Markdown conventions produced:
    - Strengths : - **[+]** **Title** — content   (green title via md_to_pdf)
    - Weaknesses : - **[-]** **Title** — content  (orange title)
    - Boxed tips (α) : > [!TIP-BOX] text
    - Bordered tips (γ.3) : > [!TIP] text
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
    "section_sw",
    "sub_strengths",
    "sub_weaknesses",
    "section_pitch",
    "pitch_intro",
    "section_tp",
    "tp_intro",
}


def generate_summary_md(labels, data):
    """Generates the complete Markdown content."""
    t = labels
    parts = []

    # Title + meta
    parts.append(f"# {t['title']}\n")
    parts.append(
        f'<p class="meta">{data.get("candidate_name", "")} — {data.get("job_title", "")} — {data.get("company_name", "")}</p>'
    )
    parts.append(f'<p class="meta-date">{data.get("date", "")}</p>\n')

    # Opening tip (α)
    opening = data.get("opening_tip")
    if opening:
        parts.append(f"> [!TIP-BOX] {opening}\n")

    # === STRENGTHS & WEAKNESSES ===
    parts.append(f"## {t['section_sw']}\n")

    # Strengths (green heading via [+])
    parts.append(f"### {t['sub_strengths']}\n")
    for item in data.get("strengths", []):
        title = item.get("title", "")
        context = item.get("context", "")
        parts.append(f"- **[+]** **{title}** — {context}")
    parts.append("")  # blank line

    # Weaknesses (orange heading via [-])
    parts.append(f"### {t['sub_weaknesses']}\n")
    for item in data.get("weaknesses", []):
        title = item.get("title", "")
        approach = item.get("approach", "")
        parts.append(f"- **[-]** **{title}** — {approach}")
    parts.append("")

    # Tip after weaknesses (γ.3)
    tip_w = data.get("tip_after_weaknesses")
    if tip_w:
        parts.append(f"> [!TIP] {tip_w}\n")

    # === PITCH ===
    parts.append(f"## {t['section_pitch']}\n")
    parts.append(f"*{t['pitch_intro']}*\n")

    pitch = data.get("pitch", [])
    for i, sentence in enumerate(pitch, start=1):
        parts.append(f"{i}. {sentence}")
    parts.append("")

    # Tip after pitch (α)
    tip_p = data.get("tip_after_pitch")
    if tip_p:
        parts.append(f"> [!TIP-BOX] {tip_p}\n")

    # === TALKING POINTS ===
    parts.append(f"## {t['section_tp']}\n")
    parts.append(f"*{t['tp_intro']}*\n")

    for tp in data.get("talking_points", []):
        title = tp.get("title", "")
        content = tp.get("content", "")
        parts.append(f"- **{title}** — {content}")
    parts.append("")

    # Final tip (γ.3)
    tip_tp = data.get("tip_after_talking_points")
    if tip_tp:
        parts.append(f"> [!TIP] {tip_tp}\n")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generates an application summary in Markdown"
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
        "strengths",
        "weaknesses",
        "pitch",
        "talking_points",
    ]
    missing = [f for f in required if f not in data]
    if missing:
        print(f"❌ Missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data["pitch"], list) or len(data["pitch"]) != 5:
        print("❌ The pitch must be exactly 5 sentences", file=sys.stderr)
        sys.exit(1)

    md_content = generate_summary_md(labels, data)

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding="utf-8")

    print(f"✅ Application summary (Markdown) generated: {output_path}")
    print(f"   - {len(data.get('strengths', []))} strengths")
    print(f"   - {len(data.get('weaknesses', []))} weaknesses")
    print(f"   - {len(data.get('pitch', []))} pitch sentences")
    print(f"   - {len(data.get('talking_points', []))} talking points")
    print("\n💡 To export to PDF:")
    print(
        f"   python md_to_pdf.py --input {output_path} --output {output_path.with_suffix('.pdf')}"
    )


if __name__ == "__main__":
    main()
