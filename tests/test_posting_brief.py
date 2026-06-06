"""Tier 1 — posting-brief generator (PB-1).

Functional guarantees under test: the generator enforces its contract before
producing anything (exact interface label set, ISO-639-1 language *form*,
required content fields), refuses an empty/sentinel critical field (exit 2,
the model must ask not invent), and OWNS its filename — given --output-dir it
builds `Posting_Brief_<Company>_<Position>_<YYYYMMDD>.md` and prints the path.
The capture timezone resolves to a safe fallback rather than crashing.
"""

import argparse
import json

import pytest

from _helpers import load_module, run_cli

REL = "modules/posting-brief-generator/scripts/generate_posting_brief.py"


def _valid_labels():
    """A complete label set with dummy values, derived from the script itself."""
    return {k: k for k in load_module(REL).REQUIRED_LABELS}


def _valid_data(**overrides):
    d = {
        "company_name": "Acme Financial Group",
        "job_title": "Head of Engineering",
        "posting_language": "English",
        "requirements": ["10+ years leadership", "Payments modernization"],
        "posting_body": "Acme is hiring a Head of Engineering. Apply by 30 June 2026.",
    }
    d.update(overrides)
    return d


# --- language form validation (pure helper, imported) ---------------------- #


@pytest.mark.parametrize("code", ["en", "fr", "de", "ja"])
def test_validate_language_accepts_iso_form(code):
    assert load_module(REL).iso639_1(code) == code


@pytest.mark.parametrize("bad", ["EN", "e", "eng", "f1", "", "en-US"])
def test_validate_language_rejects_non_iso_form(bad):
    with pytest.raises((ValueError, argparse.ArgumentTypeError)):
        load_module(REL).iso639_1(bad)


# --- timezone resolution (pure helper) ------------------------------------- #


def test_resolve_timezone_valid_and_safe_fallback():
    m = load_module(REL)
    assert m.resolve_timezone("Europe/Paris").key == "Europe/Paris"
    # empty / None / invalid never raise — they fall back, so name generation
    # is never the reason the brief fails (same floor as the tracker, 0.17.0).
    assert m.resolve_timezone("").key == "Europe/Paris"
    assert m.resolve_timezone(None).key == "Europe/Paris"
    assert m.resolve_timezone("Nope/Nowhere").key == "Europe/Paris"


# --- label-set + required-field contract (subprocess) ---------------------- #


def test_missing_label_key_is_rejected(tmp_path):
    keys = list(load_module(REL).REQUIRED_LABELS)
    labels = {k: k for k in keys[1:]}  # drop one
    proc = run_cli(
        REL,
        "--language",
        "en",
        "--output-dir",
        str(tmp_path),
        "--data-json",
        "{}",
        "--labels-json",
        json.dumps(labels),
    )
    assert proc.returncode != 0


def test_extra_label_key_is_rejected(tmp_path):
    labels = _valid_labels()
    labels["__bogus_key__"] = "x"
    proc = run_cli(
        REL,
        "--language",
        "en",
        "--output-dir",
        str(tmp_path),
        "--data-json",
        "{}",
        "--labels-json",
        json.dumps(labels),
    )
    assert proc.returncode != 0


def test_missing_required_data_is_rejected(tmp_path):
    proc = run_cli(
        REL,
        "--language",
        "en",
        "--output-dir",
        str(tmp_path),
        "--data-json",
        "{}",
        "--labels-json",
        json.dumps(_valid_labels()),
    )
    assert proc.returncode != 0  # complete label set, but no content fields


def test_invalid_language_form_is_rejected_by_cli(tmp_path):
    proc = run_cli(
        REL,
        "--language",
        "EN",
        "--output-dir",
        str(tmp_path),
        "--data-json",
        "{}",
        "--labels-json",
        json.dumps(_valid_labels()),
    )
    assert proc.returncode == 2  # argparse type-validation error


def test_requires_an_output_target():
    proc = run_cli(
        REL,
        "--language",
        "en",
        "--data-json",
        json.dumps(_valid_data()),
        "--labels-json",
        json.dumps(_valid_labels()),
    )
    assert proc.returncode != 0  # neither --output-dir nor --output-path


# --- critical-field sentinel (LNG-2 S3b contract) -------------------------- #


@pytest.mark.parametrize("field", ["company_name", "job_title", "posting_body"])
@pytest.mark.parametrize("bad", ["__MISSING__", ""])
def test_critical_field_empty_or_sentinel_is_rejected(field, bad, tmp_path):
    proc = run_cli(
        REL,
        "--language",
        "en",
        "--output-dir",
        str(tmp_path),
        "--data-json",
        json.dumps(_valid_data(**{field: bad})),
        "--labels-json",
        json.dumps(_valid_labels()),
    )
    assert proc.returncode == 2  # ask the user, never invent
    assert not list(tmp_path.glob("*.md"))  # nothing written


# --- script-owned filename (DRV / script-owned discipline) ----------------- #


def test_script_owned_filename_and_printed_path(tmp_path):
    proc = run_cli(
        REL,
        "--language",
        "en",
        "--output-dir",
        str(tmp_path),
        "--data-json",
        json.dumps(_valid_data()),
        "--labels-json",
        json.dumps(_valid_labels()),
    )
    assert proc.returncode == 0, proc.stderr

    files = list(tmp_path.glob("Posting_Brief_*.md"))
    assert len(files) == 1  # the script named it itself
    name = files[0].name
    assert "Acme" in name and "Head" in name  # company + position slugged in
    assert name.endswith(".md")
    assert files[0].name in proc.stdout  # path printed for present_files

    text = files[0].read_text(encoding="utf-8")
    assert "Acme Financial Group" in text  # header
    assert "Apply by 30 June 2026" in text  # verbatim body preserved


def test_output_path_fallback_is_honored(tmp_path):
    out = tmp_path / "explicit.md"
    proc = run_cli(
        REL,
        "--language",
        "en",
        "--output-path",
        str(out),
        "--data-json",
        json.dumps(_valid_data()),
        "--labels-json",
        json.dumps(_valid_labels()),
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()  # explicit path respected (gallery / back-compat)
