"""
Generates a Markdown "posting brief" — the job-posting dossier captured at
application intake (PB-1).

The brief is an internal working document, not an outgoing deliverable: it
records the offer so the application has a single, durable reference. It holds
a header (company, position, recruiter, city, capture date, source URL, posting
language), the *verbatim* posting body, and a short model-extracted digest (key
requirements + deadline).

Usage (filename is SCRIPT-OWNED — prefer --output-dir):
    python generate_posting_brief.py \\
        --language en|fr \\
        --output-dir /mnt/user-data/outputs \\
        --data-json '<json_string>' \\
        --labels-json '<json_string>' \\
        [--timezone Europe/Paris]

    # --output-path is accepted as a fallback (e.g. the acceptance gallery),
    # but hand-composed names are discouraged: the script names the file from
    # (company, position, capture date) so the format never drifts.

The --data-json JSON must contain:
    - company_name, job_title          (critical: empty / __MISSING__ -> exit 2)
    - posting_body                      (critical: the offer text, verbatim)
    - posting_language                  (human-readable, e.g. "English")
    - requirements : [str, ...]         (key requirements, model-extracted)
    - recruiter_name (opt), recruiter_title (opt), city (opt),
      source_url (opt), deadline (opt)

The capture date is built BY THE SCRIPT (today's local date for the candidate,
resolved via --timezone, ISO YYYY-MM-DD) — never supplied by the model, so it
cannot drift or be invented. The same date is used in the filename.

Extraction (header fields, digest) is the MODEL's job; there is no regex.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Language-neutral sentinel for a critical field the model could not fill
# (same contract as fill_cover_letter, LNG-2 S3b): empty or sentinel -> exit 2.
# The model asks the user; it never invents company / position / posting body.
MISSING_SENTINEL = "__MISSING__"

# Fixed label set = the deliverable's STRUCTURE. The model supplies the localized
# VALUES via --labels-json (target language); the script only enforces that the
# key set is EXACTLY this — no invented or omitted section (anti-hallucination
# guardrail). The structure is fixed; only the linguistic realization is the model's.
REQUIRED_LABELS = {
    "title",
    "s_meta",
    "l_company",
    "l_position",
    "l_recruiter",
    "l_city",
    "l_captured",
    "l_source",
    "l_language",
    "s_digest",
    "sub_requirements",
    "sub_deadline",
    "s_posting",
}


def iso639_1(value):
    """Validate --language as an ISO 639-1 *form*: two lowercase letters.

    Open by design (LNG-1 L5) — no maintained list, no external dependency.
    Post-L6 there is no per-language lock: the generator validates the
    model-provided label *key set* (`--labels-json`), not the language.
    `--language` is form-validated metadata only; any ISO code works.
    """
    if not re.fullmatch(r"[a-z]{2}", value or ""):
        raise argparse.ArgumentTypeError(
            f"--language must be a 2-letter ISO 639-1 code (lowercase), e.g. en, fr; got: {value!r}"
        )
    return value


def resolve_timezone(name):
    """Resolve an IANA timezone name to a ZoneInfo, with a safe fallback.

    The model resolves the candidate's locale to an IANA name and passes it; the
    script only strikes the clock (model = zone, script = clock — same boundary
    as manage_tracker). An unknown/empty name warns and falls back to
    Europe/Paris so a capture date is never the reason generation fails.
    """
    if name:
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            print(
                f"⚠️  Unknown timezone {name!r}; falling back to Europe/Paris.",
                file=sys.stderr,
            )
    return ZoneInfo("Europe/Paris")


def _slug(value):
    """ASCII-safe filename token: keep word characters, collapse the rest to '-'."""
    s = re.sub(r"[^\w]+", "-", (value or "").strip(), flags=re.UNICODE)
    return s.strip("-") or "untitled"


def resolve_output_path(args, company, position, captured_date):
    """Decide the output path. SCRIPT-OWNED naming (DRV/script-owned discipline).

    - If --output-path is provided, respect it (fallback / gallery / back-compat).
    - Otherwise build `Posting_Brief_<Company>_<Position>_<YYYYMMDD>.md` in
      --output-dir (default: current folder). The model never hand-composes it.
    """
    explicit = getattr(args, "output_path", None)
    if explicit:
        return str(explicit)
    out_dir = getattr(args, "output_dir", None) or "."
    stamp = captured_date.replace("-", "")
    name = f"Posting_Brief_{_slug(company)}_{_slug(position)}_{stamp}.md"
    return str(Path(out_dir) / name)


def _is_missing(value):
    """A critical field is missing if it is empty or the language-neutral sentinel."""
    return not value or str(value).strip() in ("", MISSING_SENTINEL)


def generate_brief_md(labels, data, captured_date):
    """Generates the complete Markdown content."""
    t = labels
    parts = []

    parts.append(f"# {t['title']}\n")

    # === HEADER (at a glance) ===
    parts.append(f"## {t['s_meta']}\n")
    recruiter_name = data.get("recruiter_name", "").strip()
    recruiter_title = data.get("recruiter_title", "").strip()
    if recruiter_name and recruiter_title:
        recruiter = f"{recruiter_name}, {recruiter_title}"
    else:
        recruiter = recruiter_name or recruiter_title or "—"
    rows = [
        (t["l_company"], data.get("company_name", "")),
        (t["l_position"], data.get("job_title", "")),
        (t["l_recruiter"], recruiter),
        (t["l_city"], data.get("city", "").strip() or "—"),
        (t["l_captured"], captured_date),
        (t["l_source"], data.get("source_url", "").strip() or "—"),
        (t["l_language"], data.get("posting_language", "").strip() or "—"),
    ]
    for label, value in rows:
        parts.append(f"- **{label}:** {value}")
    parts.append("")

    # === DIGEST (model-extracted) ===
    parts.append(f"## {t['s_digest']}\n")
    parts.append(f"### {t['sub_requirements']}\n")
    for req in data.get("requirements", []):
        parts.append(f"- {req}")
    parts.append("")
    parts.append(f"### {t['sub_deadline']}\n")
    parts.append(f"{data.get('deadline', '').strip() or '—'}\n")

    # === POSTING (verbatim body) ===
    parts.append(f"## {t['s_posting']}\n")
    parts.append(data.get("posting_body", ""))

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generates a job-posting brief (dossier) in Markdown"
    )
    parser.add_argument(
        "--language",
        required=True,
        type=iso639_1,
        metavar="LANG",
        help="ISO 639-1 language code (lowercase), e.g. en, fr",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (the filename is built by the script)",
    )
    parser.add_argument(
        "--output-path",
        help="Explicit output .md path (fallback; hand-composed names discouraged)",
    )
    parser.add_argument("--data-json", required=True)
    parser.add_argument(
        "--labels-json",
        required=True,
        help="JSON object of structure labels in the target language (exact key set required)",
    )
    parser.add_argument(
        "--timezone",
        default=None,
        help="IANA timezone for the capture date (e.g. Europe/Paris); safe fallback if unknown",
    )

    args = parser.parse_args()

    if not args.output_dir and not args.output_path:
        print("❌ Provide --output-dir (preferred) or --output-path.", file=sys.stderr)
        sys.exit(1)

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
        "company_name",
        "job_title",
        "posting_language",
        "requirements",
        "posting_body",
    ]
    missing = [f for f in required if f not in data]
    if missing:
        print(f"❌ Missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)

    # Critical fields must be real values — never empty, never the sentinel.
    # The model asks the user instead of inventing a company / position / body.
    critical = ["company_name", "job_title", "posting_body"]
    bad = [f for f in critical if _is_missing(data.get(f))]
    if bad:
        print(
            f"❌ Critical field(s) empty or unresolved ({MISSING_SENTINEL}): {bad}. "
            "Ask the user — do not invent.",
            file=sys.stderr,
        )
        sys.exit(2)

    tz = resolve_timezone(args.timezone)
    captured_date = datetime.now(tz).strftime("%Y-%m-%d")

    md_content = generate_brief_md(labels, data, captured_date)

    output_path = Path(
        resolve_output_path(
            args, data["company_name"], data["job_title"], captured_date
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding="utf-8")

    print(f"✅ Posting brief (Markdown) generated: {output_path}")
    print(f"   {output_path}")
    print(f"   - captured: {captured_date}")
    print(f"   - {len(data.get('requirements', []))} key requirement(s)")
    print(f"   - posting body: {len(data.get('posting_body', ''))} chars (verbatim)")
    print("\n💡 To export to PDF:")
    print(
        f"   python md_to_pdf.py --input {output_path} --output {output_path.with_suffix('.pdf')}"
    )


if __name__ == "__main__":
    main()
