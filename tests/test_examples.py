"""Tier 2 — delivery acceptance ("Conditions d'Acceptation de livraison").

On every run we rebuild the long Lorem-ipsum cover letter (signed + unsigned)
and assert the non-negotiable conditions: one page (body within the 2800 cap
AND the paragraph ratios), Calibri, fused-border header, and a floating
signature present only in the signed variant. The full gallery build (all
deliverables + PDF conversions) is exercised at L2, where every converter is
present.
"""

import json
import zipfile

import pytest

from _helpers import REPO_ROOT, load_module, run_cli

BS = load_module("tooling/build_samples.py")
CL_REL = "modules/cover-letter-generator/scripts/fill_cover_letter.py"
TEMPLATE = (
    REPO_ROOT / "modules/cover-letter-generator/assets/Cover_letter_template.docx"
)


def _doc_xml(path):
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


@pytest.mark.needs_docx
def test_lorem_body_respects_cap_and_ratios():
    cl = load_module(CL_REL)
    ok, total, details = cl.check_body_cap(
        BS.lorem_letter_data(True), cl.BODY_CAP_DEFAULT
    )
    assert ok and total <= cl.BODY_CAP_DEFAULT
    assert all(not over for _, _, _, over in details)  # none over 1.2x its ratio


@pytest.mark.needs_docx
def test_signed_lorem_letter_meets_acceptance(tmp_path, signature_b64_file):
    out = tmp_path / "signed.docx"
    proc = run_cli(
        CL_REL,
        "--language",
        "en",
        "--template-path",
        str(TEMPLATE),
        "--output-path",
        str(out),
        "--data-json",
        json.dumps(BS.lorem_letter_data(True)),
        "--signature-path",
        str(signature_b64_file),
    )
    assert proc.returncode == 0, proc.stderr
    xml = _doc_xml(out)
    assert "Calibri" in xml and "w:pBdr" in xml and "wp:anchor" in xml
    assert "{{" not in xml


@pytest.mark.needs_docx
def test_unsigned_lorem_letter_has_no_signature(tmp_path):
    out = tmp_path / "unsigned.docx"
    proc = run_cli(
        CL_REL,
        "--language",
        "en",
        "--template-path",
        str(TEMPLATE),
        "--output-path",
        str(out),
        "--data-json",
        json.dumps(BS.lorem_letter_data(False)),
    )
    assert proc.returncode == 0, proc.stderr
    xml = _doc_xml(out)
    assert "wp:anchor" not in xml and "Calibri" in xml


@pytest.mark.needs_docx
@pytest.mark.needs_markdown
@pytest.mark.needs_wkhtmltopdf
@pytest.mark.needs_libreoffice
def test_build_all_produces_full_gallery(tmp_path):
    names = {p.name for p in BS.build_all(tmp_path)}
    assert len(names) == 16
    assert sum(n.endswith(".docx") for n in names) == 2  # signed + unsigned
    assert sum(n.endswith(".pdf") for n in names) == 6  # 2 letters + 4 generators
    assert sum(n.endswith(".md") for n in names) == 4
    assert sum(n.endswith(".html") for n in names) == 4
