"""
Generates a strategic application Playbook in Markdown.
PDF export possible via md_to_pdf.py.

Usage:
    python generate_playbook.py \\
        --language en|fr \\
        --output-path /path/to/output.md \\
        --data-json '<json_string>'

See references/playbook_structure.md for the JSON structure.
All content sections are optional; only the metadata
(candidate_name, job_title, company_name, date) is mandatory.
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
    if not re.fullmatch(r'[a-z]{2}', value or ''):
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
    'title',
    'web_note_yes',
    'web_note_no',
    'usage_tip',
    's_context',
    's_pain',
    's_org',
    's_positioning',
    's_strategy',
    's_questions',
    's_tough',
    's_pitch',
    's_redlines',
    'analysis',
    'your_angle',
    'evidence',
    'round',
    'focus',
    'approach',
    'strategy',
}


def generate_playbook_md(labels, data):
    t = labels
    parts = []

    # Header
    parts.append(f"# {t['title']}\n")
    parts.append(f'<p class="meta">{data.get("candidate_name", "")} — {data.get("job_title", "")} — {data.get("company_name", "")}</p>')
    parts.append(f'<p class="meta-date">{data.get("date", "")}</p>\n')

    # Web research note
    web_done = data.get('web_research_done', False)
    parts.append(f"*{t['web_note_yes'] if web_done else t['web_note_no']}*\n")

    # Usage tip at the top
    parts.append(f"> [!TIP-BOX] {t['usage_tip']}\n")

    # 1. Context
    if data.get('company_context'):
        parts.append(f"## {t['s_context']}\n")
        parts.append(data['company_context'] + "\n")

    # 2. Pain points
    if data.get('pain_points'):
        parts.append(f"## {t['s_pain']}\n")
        for i, pp in enumerate(data['pain_points'], start=1):
            parts.append(f"### {i}. {pp.get('title', '')}\n")
            if pp.get('analysis'):
                parts.append(f"**{t['analysis']} :** {pp['analysis']}\n")
            if pp.get('your_angle'):
                parts.append(f"> [!TIP] **{t['your_angle']} :** {pp['your_angle']}\n")

    # 3. Org landscape
    if data.get('org_landscape'):
        parts.append(f"## {t['s_org']}\n")
        parts.append(data['org_landscape'] + "\n")

    # 4. Positioning
    if data.get('positioning'):
        parts.append(f"## {t['s_positioning']}\n")
        for pos in data['positioning']:
            msg = pos.get('message', '')
            ev = pos.get('evidence', '')
            parts.append(f"- **{msg}** — {t['evidence']} : {ev}")
        parts.append("")

    # 5. Interview strategy
    if data.get('interview_strategy'):
        parts.append(f"## {t['s_strategy']}\n")
        for strat in data['interview_strategy']:
            parts.append(f"### {strat.get('round', '')}\n")
            if strat.get('focus'):
                parts.append(f"**{t['focus']} :** {strat['focus']}\n")
            if strat.get('approach'):
                parts.append(f"{strat['approach']}\n")

    # 6. Questions to ask
    if data.get('questions_to_ask'):
        parts.append(f"## {t['s_questions']}\n")
        for q in data['questions_to_ask']:
            parts.append(f"- {q}")
        parts.append("")

    # 7. Tough questions
    if data.get('tough_questions'):
        parts.append(f"## {t['s_tough']}\n")
        for i, tq in enumerate(data['tough_questions'], start=1):
            parts.append(f"**{i}. {tq.get('question', '')}**\n")
            if tq.get('strategy'):
                parts.append(f"> [!TIP] **{t['strategy']} :** {tq['strategy']}\n")

    # 8. 30-second pitch
    if data.get('thirty_second_pitch'):
        parts.append(f"## {t['s_pitch']}\n")
        parts.append(data['thirty_second_pitch'] + "\n")

    # 9. Red lines
    if data.get('red_lines'):
        parts.append(f"## {t['s_redlines']}\n")
        for rl in data['red_lines']:
            parts.append(f"- {rl}")
        parts.append("")

    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(description="Generates a strategic playbook in Markdown")
    parser.add_argument('--language', required=True, type=iso639_1,
                        metavar='LANG', help='ISO 639-1 language code (lowercase), e.g. en, fr')
    parser.add_argument('--output-path', required=True)
    parser.add_argument('--data-json', required=True)
    parser.add_argument('--labels-json', required=True,
                        help='JSON object of structure labels in the target language (exact key set required)')
    args = parser.parse_args()

    try:
        data = json.loads(args.data_json)
    except json.JSONDecodeError as e:
        print(f"❌ JSON invalide : {e}", file=sys.stderr)
        sys.exit(1)

    try:
        labels = json.loads(args.labels_json)
    except json.JSONDecodeError as e:
        print(f"❌ JSON invalide (labels) : {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(labels, dict) or set(labels) != REQUIRED_LABELS:
        got = set(labels) if isinstance(labels, dict) else set()
        print(f"❌ Libellés invalides — manquants: {sorted(REQUIRED_LABELS - got)} ; en trop: {sorted(got - REQUIRED_LABELS)}", file=sys.stderr)
        sys.exit(1)

    required = ['candidate_name', 'job_title', 'company_name', 'date']
    missing = [f for f in required if f not in data]
    if missing:
        print(f"❌ Champs obligatoires manquants : {missing}", file=sys.stderr)
        sys.exit(1)

    md_content = generate_playbook_md(labels, data)

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding='utf-8')

    # Count the present sections
    sections = [k for k in ['company_context', 'pain_points', 'org_landscape',
                            'positioning', 'interview_strategy', 'questions_to_ask',
                            'tough_questions', 'thirty_second_pitch', 'red_lines']
                if data.get(k)]
    print(f"✅ Playbook stratégique (Markdown) généré : {output_path}")
    print(f"   - {len(sections)} sections : {', '.join(sections)}")
    print(f"   - Recherche web : {'oui' if data.get('web_research_done') else 'non'}")
    print(f"\n💡 Pour exporter en PDF :")
    print(f"   python md_to_pdf.py --input {output_path} --output {output_path.with_suffix('.pdf')}")


if __name__ == '__main__':
    main()
