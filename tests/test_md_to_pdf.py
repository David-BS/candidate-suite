"""Tier 3 — Markdown→PDF for the quick-reference card (md_to_pdf.py).

Functional guarantee under test: the language-neutral two-column layout (driven
by the structural `col2` marker, not by matching FR/EN titles) is applied
deterministically, the script fails cleanly on a missing input, and — when the
converter binary is present — a non-empty PDF is produced.
"""

import pytest

from _helpers import load_module, run_cli

MD_REL = "modules/quick-reference-generator/scripts/md_to_pdf.py"


@pytest.mark.needs_markdown
def test_columnize_turns_col2_section_into_two_column_table():
    mod = load_module(MD_REL)
    html = (
        '<h2 class="col2">Stats</h2>\n<ul><li>a</li><li>b</li><li>c</li><li>d</li></ul>'
    )
    out = mod._columnize_sections(html)
    assert "<table" in out  # split into a side-by-side table
    assert out.count("<ul>") >= 2  # two columns


@pytest.mark.needs_markdown
def test_columnize_leaves_plain_section_untouched():
    mod = load_module(MD_REL)
    html = "<h2>Plain</h2>\n<ul><li>a</li></ul>"
    assert mod._columnize_sections(html) == html  # no col2 marker → unchanged


@pytest.mark.needs_markdown
def test_missing_input_exits_1(tmp_path):
    proc = run_cli(
        MD_REL,
        "--input",
        str(tmp_path / "nope.md"),
        "--output",
        str(tmp_path / "o.pdf"),
    )
    assert proc.returncode == 1


@pytest.mark.needs_markdown
@pytest.mark.needs_wkhtmltopdf
def test_conversion_produces_nonempty_pdf(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("# Title\n\nHello world\n", encoding="utf-8")
    out = tmp_path / "o.pdf"
    proc = run_cli(MD_REL, "--input", str(md), "--output", str(out))
    assert proc.returncode == 0, proc.stderr
    assert out.exists() and out.stat().st_size > 0
    assert out.read_bytes()[:5] == b"%PDF-"
