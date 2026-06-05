"""Tier 2 — cover letter (fill_cover_letter.py). Requires python-docx.

Functional guarantee under test: the most visible deliverable is never produced
incomplete, never overflows one page, and keeps its non-negotiable layout. The
script refuses missing/sentinel critical data and an over-cap body, and the
generated .docx preserves the Calibri font, the fused-border header (no Word
table) and a floating (anchored) signature.
"""

import json
import zipfile

import pytest

from _helpers import REPO_ROOT, load_module, run_cli

CL_REL = "modules/cover-letter-generator/scripts/fill_cover_letter.py"
TEMPLATE = (
    REPO_ROOT / "modules/cover-letter-generator/assets/Cover_letter_template.docx"
)
DATA_FILE = REPO_ROOT / "tests/_data/cover_letter.json"


def _data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _document_xml(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        return z.read("word/document.xml").decode("utf-8")


def _run(tmp_path, data, *extra):
    out = tmp_path / "letter.docx"
    proc = run_cli(
        CL_REL,
        "--language",
        "en",
        "--template-path",
        str(TEMPLATE),
        "--output-path",
        str(out),
        "--data-json",
        json.dumps(data),
        *extra,
    )
    return proc, out


# --- pure helpers (import) ------------------------------------------------- #


@pytest.mark.needs_docx
def test_build_replacements_maps_keys_including_legacy_name():
    cl = load_module(CL_REL)
    repl = cl.build_replacements({"sender_name": "X", "paragraph_4_value": "V"})
    assert repl["{{SENDER_NAME}}"] == "X"
    assert repl["{{PARAGRAPH_4_ACHIEVEMENTS}}"] == "V"  # legacy placeholder name
    assert cl.build_replacements({"company_name": None})["{{COMPANY_NAME}}"] == ""


@pytest.mark.needs_docx
def test_check_body_cap_detects_overflow():
    cl = load_module(CL_REL)
    empty = {k: "" for k, _ in cl.BODY_PARAGRAPHS}
    ok, total, _ = cl.check_body_cap(empty, 2800)
    assert ok and total == 0
    over = dict(empty, paragraph_1_intro="x" * 4000)
    ok2, total2, _ = cl.check_body_cap(over, 2800)
    assert not ok2 and total2 == 4000


# --- CLI contract + .docx structural invariants (subprocess) --------------- #


@pytest.mark.needs_docx
def test_valid_payload_produces_structural_docx(tmp_path):
    proc, out = _run(tmp_path, _data())
    assert proc.returncode == 0, proc.stderr
    xml = _document_xml(out)
    assert "{{" not in xml  # every placeholder replaced
    assert "Calibri" in xml  # font preserved
    assert "w:pBdr" in xml  # fused-border header (no Word table)


@pytest.mark.needs_docx
def test_signature_is_floating_anchored(tmp_path, signature_b64_file):
    proc, out = _run(tmp_path, _data(), "--signature-path", str(signature_b64_file))
    assert proc.returncode == 0, proc.stderr
    assert "wp:anchor" in _document_xml(out)  # floating, never inline


@pytest.mark.needs_docx
def test_sentinel_in_critical_field_is_refused(tmp_path):
    proc, _ = _run(tmp_path, dict(_data(), paragraph_1_intro="__MISSING__"))
    assert proc.returncode == 2  # refuses an incomplete letter


@pytest.mark.needs_docx
def test_blank_critical_field_is_refused(tmp_path):
    proc, _ = _run(tmp_path, dict(_data(), company_name="   "))
    assert proc.returncode == 2


@pytest.mark.needs_docx
def test_missing_required_field_exits_1(tmp_path):
    d = _data()
    del d["company_name"]
    proc, _ = _run(tmp_path, d)
    assert proc.returncode == 1


@pytest.mark.needs_docx
def test_body_over_cap_is_rejected(tmp_path):
    proc, _ = _run(tmp_path, dict(_data(), paragraph_3_experience="x" * 3000))
    assert proc.returncode == 2  # one-page guardrail


@pytest.mark.needs_docx
def test_invalid_language_form_is_rejected(tmp_path):
    out = tmp_path / "l.docx"
    bad = run_cli(
        CL_REL,
        "--language",
        "EN",
        "--template-path",
        str(TEMPLATE),
        "--output-path",
        str(out),
        "--data-json",
        json.dumps(_data()),
    )
    assert bad.returncode == 2  # argparse iso639_1 type error
