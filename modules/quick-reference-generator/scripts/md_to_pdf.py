"""
Converts a Markdown file into a styled PDF, applying the application documents'
visual identity (semantic palette, boxed/bordered tips, lightbulb icon).

Usage:
    python md_to_pdf.py --input <file.md> --output <file.pdf> [--title "Title"]

Markdown conventions recognized for enriched styling:
    - Headings # ## ###  → colored hierarchy
    - Tip lines (see below) → amber boxes or borders

Convention for TIPS in the source Markdown:
    - Boxed tip (α)    : line starting with  `> [!TIP-BOX] text`
    - Bordered tip (γ.3) : line starting with  `> [!TIP] text`

These markers are turned into styled HTML before PDF conversion.

Convention for the SEMANTIC COLORS of bullet titles:
    - `- **[+]** Title — content`  → title in green (strength / positive)
    - `- **[-]** Title — content`  → title in orange (weakness / caution)
    - `- **[Q]** ...`              → question label in purple (handled via headings)
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import markdown


# === PALETTE (identical to the previous docx chart) ===
TITLE_COLOR = "#1F4E79"  # Navy blue
QUESTION_COLOR = "#7030A0"  # Violet
ANSWER_COLOR = "#2E7D32"  # Pine green
STRENGTH_COLOR = "#2E7D32"  # Green
WEAKNESS_COLOR = "#C77700"  # Orange
TIP_TEXT_COLOR = "#6B3D00"  # Dark amber
TIP_BG = "#FFF4E5"  # Light beige
TIP_BORDER = "#C77700"  # Amber
GREY_COLOR = "#595959"  # Slate grey


# Lightbulb icon as inline SVG (vector, renders perfectly in PDF)
LIGHTBULB_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 64 64" style="vertical-align:-2px;margin-right:4px;"><ellipse cx="32" cy="25" rx="14" ry="17" fill="#FFF4E5" stroke="#6B3D00" stroke-width="3"/><path d="M26 24 Q32 18 38 24" fill="none" stroke="#6B3D00" stroke-width="2"/><line x1="25" y1="42" x2="39" y2="42" stroke="#6B3D00" stroke-width="3"/><line x1="26" y1="47" x2="38" y2="47" stroke="#6B3D00" stroke-width="3"/><line x1="27" y1="52" x2="37" y2="52" stroke="#6B3D00" stroke-width="3"/><path d="M27 53 Q32 60 37 53" fill="none" stroke="#6B3D00" stroke-width="3"/></svg>"""


def inline_md_to_html(text):
    """Converts simple inline markdown (bold, italic, code) to HTML.
    Used for the content of tips and semantic bullets that don't go
    through the main markdown engine."""
    import re as _re

    # **bold** -> <strong>
    text = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # *italic* -> <em>  (avoid catching the ** already handled)
    text = _re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    # `code` -> <code>
    text = _re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def preprocess_checkboxes(md_text):
    """Turns markdown task lists `- [ ]` / `- [x]` into visual HTML checkboxes.
    The standard markdown engine doesn't handle them; we replace them with a symbol."""
    import re as _re

    lines = md_text.split("\n")
    out = []
    for line in lines:
        m = _re.match(r"^(\s*)-\s*\[([ xX])\]\s*(.+)$", line)
        if m:
            indent, mark, rest = m.group(1), m.group(2), m.group(3)
            box = "\u2611" if mark.lower() == "x" else "\u2610"  # ☑ / ☐
            out.append(f'{indent}- <span class="checkbox">{box}</span> {rest}')
        else:
            out.append(line)
    return "\n".join(out)


def preprocess_tips(md_text):
    """Turns tip markers into styled HTML.

    > [!TIP-BOX] text   → α box (beige background + thick border)
    > [!TIP] text       → γ.3 border (thin left border, amber bold text)

    Markers can span several consecutive lines starting with '>'.
    """
    lines = md_text.split("\n")
    output = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Boxed-tip detection (α)
        m_box = re.match(r"^>\s*\[!TIP-BOX\]\s*(.*)$", line)
        m_inline = re.match(r"^>\s*\[!TIP\]\s*(.*)$", line)

        if m_box:
            content = m_box.group(1).strip()
            # Collect continuation lines
            j = i + 1
            while (
                j < len(lines)
                and lines[j].startswith(">")
                and not re.match(r"^>\s*\[!TIP", lines[j])
            ):
                content += " " + lines[j].lstrip("> ").strip()
                j += 1
            html = (
                f'<div class="tip-box">{LIGHTBULB_SVG}'
                f'<span class="tip-box-label">Astuce — </span>'
                f'<span class="tip-box-text">{inline_md_to_html(content)}</span></div>'
            )
            output.append(html)
            i = j
            continue

        elif m_inline:
            content = m_inline.group(1).strip()
            j = i + 1
            while (
                j < len(lines)
                and lines[j].startswith(">")
                and not re.match(r"^>\s*\[!TIP", lines[j])
            ):
                content += " " + lines[j].lstrip("> ").strip()
                j += 1
            html = (
                f'<div class="tip-inline">{LIGHTBULB_SVG}'
                f'<span class="tip-inline-label">Tip : </span>'
                f'<span class="tip-inline-text">{inline_md_to_html(content)}</span></div>'
            )
            output.append(html)
            i = j
            continue

        output.append(line)
        i += 1

    return "\n".join(output)


def preprocess_semantic_bullets(md_text):
    """Turns semantic bullet markers into colored HTML.

    - **[+]** Title — content  → bullet with green title
    - **[-]** Title — content  → bullet with orange title
    """
    lines = md_text.split("\n")
    output = []
    for line in lines:
        # [+] strength (green)
        m_plus = re.match(r"^(\s*)-\s*\*\*\[\+\]\*\*\s*(.+)$", line)
        m_minus = re.match(r"^(\s*)-\s*\*\*\[-\]\*\*\s*(.+)$", line)

        if m_plus:
            indent, rest = m_plus.group(1), m_plus.group(2)
            # Split title — content
            output.append(
                f'{indent}- <span class="strength-title">{inline_md_to_html(rest)}</span>'
            )
        elif m_minus:
            indent, rest = m_minus.group(1), m_minus.group(2)
            output.append(
                f'{indent}- <span class="weakness-title">{inline_md_to_html(rest)}</span>'
            )
        else:
            output.append(line)

    return "\n".join(output)


def build_css():
    """Generates the visual-identity CSS."""
    return f"""
    @page {{
        size: A4;
        margin: 0.5cm 2.2cm;
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
    /* Semantic H3 added via preprocessing classes if needed */
    .meta {{
        color: {GREY_COLOR};
        font-size: 10.5pt;
        margin-top: 0;
        margin-bottom: 2px;
    }}
    .meta-date {{
        color: {GREY_COLOR};
        font-size: 9.5pt;
        font-style: italic;
        margin-top: 0;
        margin-bottom: 16px;
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

    /* Question / Answer labels */
    .q-label {{ color: {QUESTION_COLOR}; font-weight: bold; }}
    .a-label {{ color: {ANSWER_COLOR}; font-weight: bold; }}

    /* Semantic bullet titles */
    .strength-title strong:first-child,
    .strength-title {{ }}
    .strength-title {{ color: inherit; }}
    .strength-title b, .strength-title strong {{ color: {STRENGTH_COLOR}; }}
    .weakness-title b, .weakness-title strong {{ color: {WEAKNESS_COLOR}; }}

    /* Boxed TIP (α style) */
    .tip-box {{
        background-color: {TIP_BG};
        border-left: 4px solid {TIP_BORDER};
        padding: 8px 12px;
        margin: 12px 0;
        font-size: 10pt;
        color: {TIP_TEXT_COLOR};
        border-radius: 2px;
    }}
    .tip-box-label {{ font-weight: bold; color: {TIP_TEXT_COLOR}; }}
    .tip-box-text {{ color: {TIP_TEXT_COLOR}; }}

    /* Bordered TIP (γ.3 style) */
    .tip-inline {{
        border-left: 2px solid {TIP_BORDER};
        padding: 2px 10px;
        margin: 8px 0 8px 12px;
        font-size: 10pt;
    }}
    .tip-inline-label {{ font-weight: bold; color: {TIP_TEXT_COLOR}; }}
    .tip-inline-text {{ font-weight: bold; color: {TIP_TEXT_COLOR}; }}

    blockquote {{
        border-left: 3px solid #d9e1ec;
        margin: 8px 0;
        padding-left: 12px;
        color: {GREY_COLOR};
    }}
    .checkbox {{ font-size: 12pt; margin-right: 2px; }}
    code {{
        background-color: #f4f4f4;
        padding: 1px 4px;
        border-radius: 3px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 10pt;
    }}
    """


def _columnize_sections(html):
    "Lays out 2-column section lists to reclaim height (reference card fitting on\none page). Targets sections by a STRUCTURAL marker (LNG-2 S3b): the heading carries\nthe class `col2`, emitted by generate_quick_reference via attr_list — language-neutral,\nno FR/EN title matching. Since wkhtmltopdf (old WebKit) does not honor `column-count`,\nwe split the list into two <ul> placed side by side in a 2-cell table (reliable\nrendering). Alters neither the .md nor the other sections."
    import re as _re

    def to_table(m):
        prefix, ul_inner = m.group(1), m.group(2)
        items = _re.findall(r"<li>.*?</li>", ul_inner, _re.S)
        if len(items) < 2:
            return m.group(0)  # nothing to split
        half = (len(items) + 1) // 2
        left = "".join(items[:half])
        right = "".join(items[half:])
        return (
            prefix + '<table class="cols2"><tr>'
            f"<td><ul>{left}</ul></td><td><ul>{right}</ul></td>"
            "</tr></table>"
        )

    # Any <h2> carrying the `col2` class, immediately followed by a <ul>.
    pat = r'(<h2[^>]*\bclass="[^"]*\bcol2\b[^"]*"[^>]*>.*?</h2>\s*)<ul>(.*?)</ul>'
    html = _re.sub(pat, to_table, html, flags=_re.S)
    return html


def convert(input_path, output_path, title=None):
    """Converts the Markdown into a styled PDF."""
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"❌ Fichier introuvable : {input_path}", file=sys.stderr)
        sys.exit(1)

    md_text = input_path.read_text(encoding="utf-8")

    # Convert Markdown -> HTML
    md_text = preprocess_checkboxes(md_text)
    md_text = preprocess_tips(md_text)
    md_text = preprocess_semantic_bullets(md_text)

    # Conversion Markdown -> HTML
    html_body = markdown.markdown(md_text, extensions=["extra", "sane_lists", "nl2br"])

    # 2 columns on sections carrying the structural .col2 marker (height gain)
    html_body = _columnize_sections(html_body)

    # Complete HTML document
    doc_title = title or input_path.stem
    full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{doc_title}</title>
<style>{build_css()}
table.cols2 {{ width: 100%; border-collapse: collapse; margin-top: 4px; }}
table.cols2 td {{ width: 50%; vertical-align: top; padding: 0 14px 0 0; }}
table.cols2 ul {{ margin: 0; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    # Write the temporary HTML
    html_tmp = input_path.with_suffix(".tmp.html")
    html_tmp.write_text(full_html, encoding="utf-8")

    # Convert HTML -> PDF via wkhtmltopdf
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "wkhtmltopdf",
            "--quiet",
            "--encoding",
            "utf-8",
            "--enable-local-file-access",
            "--margin-top",
            "5mm",
            "--margin-bottom",
            "5mm",
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

    # Clean up the temporary HTML
    html_tmp.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"❌ Erreur wkhtmltopdf : {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ PDF généré : {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Converts a Markdown file into a styled PDF"
    )
    parser.add_argument("--input", required=True, help="Source .md file")
    parser.add_argument("--output", required=True, help="Output .pdf file")
    parser.add_argument("--title", default=None, help="Document title (metadata)")
    args = parser.parse_args()

    convert(args.input, args.output, args.title)


if __name__ == "__main__":
    main()
