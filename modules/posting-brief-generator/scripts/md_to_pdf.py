"""
Converts a posting-brief Markdown file into a styled PDF, applying the
application documents' visual identity (same palette as the other deliverables).

Usage:
    python md_to_pdf.py --input <file.md> --output <file.pdf> [--title "Title"]

This is a deliberately lighter converter than the other modules': the posting
brief has no tips or semantic (+/-) bullets, only headings, a header list and
the verbatim posting body. No hard-coded rendered label — fully language-neutral.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import markdown

# === PALETTE (shared with the other deliverables) ===
TITLE_COLOR = "#1F4E79"  # Navy blue
GREY_COLOR = "#595959"  # Slate grey


def build_css():
    """Generates the visual-identity CSS (subset shared with the other PDFs)."""
    return f"""
    @page {{
        size: A4;
        margin: 2cm 2.2cm;
    }}
    body {{
        font-family: 'Aptos', 'Segoe UI', 'Calibri', 'Helvetica Neue', Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #1a1a1a;
    }}
    h1 {{
        color: {TITLE_COLOR};
        font-size: 21pt;
        font-weight: bold;
        margin-bottom: 4px;
        margin-top: 0;
    }}
    h2 {{
        color: {TITLE_COLOR};
        font-size: 15pt;
        font-weight: bold;
        margin-top: 22px;
        margin-bottom: 8px;
        border-bottom: 1px solid #d9e1ec;
        padding-bottom: 3px;
    }}
    h3 {{
        font-size: 12.5pt;
        font-weight: bold;
        margin-top: 14px;
        margin-bottom: 6px;
    }}
    p {{
        margin: 6px 0;
        text-align: justify;
    }}
    ul, ol {{
        margin: 6px 0;
        padding-left: 22px;
    }}
    li {{
        margin: 4px 0;
        text-align: justify;
    }}
    strong {{ font-weight: bold; }}
    em {{ font-style: italic; }}
    blockquote {{
        border-left: 3px solid #d9e1ec;
        margin: 8px 0;
        padding-left: 12px;
        color: {GREY_COLOR};
    }}
    code {{
        background-color: #f4f4f4;
        padding: 1px 4px;
        border-radius: 3px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 10pt;
    }}
    """


def convert(input_path, output_path, title=None):
    """Converts the Markdown into a styled PDF."""
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    md_text = input_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(md_text, extensions=["extra", "sane_lists", "nl2br"])

    doc_title = title or input_path.stem
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{doc_title}</title>
<style>{build_css()}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    html_tmp = input_path.with_suffix(".tmp.html")
    html_tmp.write_text(full_html, encoding="utf-8")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "wkhtmltopdf",
            "--quiet",
            "--encoding",
            "utf-8",
            "--enable-local-file-access",
            "--margin-top",
            "18mm",
            "--margin-bottom",
            "16mm",
            "--margin-left",
            "0",
            "--margin-right",
            "0",
            str(html_tmp),
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )

    html_tmp.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"❌ wkhtmltopdf error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ PDF generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Converts a posting-brief Markdown file into a styled PDF"
    )
    parser.add_argument("--input", required=True, help="Source .md file")
    parser.add_argument("--output", required=True, help="Output .pdf file")
    parser.add_argument("--title", default=None, help="Document title (metadata)")
    args = parser.parse_args()

    convert(args.input, args.output, args.title)


if __name__ == "__main__":
    main()
