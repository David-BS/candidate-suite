"""Tier 3 — DOCX→PDF via LibreOffice (docx_to_pdf.py).

Functional guarantee under test: a clean error code on a missing input, and —
when LibreOffice is present — a real PDF is produced from a .docx.
"""

import pytest

from _helpers import REPO_ROOT, run_cli

DX_REL = "modules/cover-letter-generator/scripts/docx_to_pdf.py"
TEMPLATE = (
    REPO_ROOT / "modules/cover-letter-generator/assets/Cover_letter_template.docx"
)


def test_missing_input_exits_1(tmp_path):
    proc = run_cli(
        DX_REL, "--input", str(tmp_path / "nope.docx"), "--outdir", str(tmp_path)
    )
    assert proc.returncode == 1


@pytest.mark.needs_libreoffice
def test_conversion_produces_pdf(tmp_path):
    proc = run_cli(DX_REL, "--input", str(TEMPLATE), "--outdir", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    pdfs = list(tmp_path.glob("*.pdf"))
    assert pdfs and pdfs[0].stat().st_size > 0
