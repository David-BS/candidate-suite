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


# --- gallery exercises the 0.16.6 novelties -------------------------------- #


def test_lorem_paragraphs_are_distinct():
    """The five Lorem body paragraphs must be visibly different, not prefixes of
    one another (0.16.6: per-paragraph offset in build_samples.lorem)."""
    data = BS.lorem_letter_data(True)
    paras = [
        data[f]
        for f in (
            "paragraph_1_intro",
            "paragraph_2_current",
            "paragraph_3_experience",
            "paragraph_4_value",
            "paragraph_5_closing",
        )
    ]
    assert len(set(paras)) == 5


def test_sample_signature_is_visible():
    """The fictional gallery signature must be a real, visible image — far larger
    than the old 8x4 placeholder dot (0.16.6)."""
    import base64
    import struct

    png = base64.b64decode(BS.signature_b64())
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", png[16:24])  # IHDR
    assert width >= 100 and height >= 40
    assert len(png) > 200
