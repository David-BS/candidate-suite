"""Tier 1 — Markdown deliverable generators (summary / interview / playbook / quick-ref).

Functional guarantee under test: each generator enforces its contract before
producing anything — the interface label set must be exact, the language is a
validated ISO 639-1 form, and required content fields must be present. This is
what prevents a broken or half-localized deliverable.
"""

import argparse
import json

import pytest

from _helpers import load_module, run_cli

GENERATORS = [
    "modules/application-summary-generator/scripts/generate_application_summary.py",
    "modules/interview-prep-generator/scripts/generate_interview_prep.py",
    "modules/strategic-playbook-generator/scripts/generate_playbook.py",
    "modules/quick-reference-generator/scripts/generate_quick_reference.py",
]


def _valid_labels(rel):
    """A complete label set with dummy values, derived from the script itself."""
    return {k: k for k in load_module(rel).REQUIRED_LABELS}


# --- language form validation (pure helper, imported) ---------------------- #


@pytest.mark.parametrize("rel", GENERATORS)
@pytest.mark.parametrize("code", ["en", "fr", "de", "ja"])
def test_validate_language_accepts_iso_form(rel, code):
    assert load_module(rel).iso639_1(code) == code


@pytest.mark.parametrize("rel", GENERATORS)
@pytest.mark.parametrize("bad", ["EN", "e", "eng", "f1", "", "en-US"])
def test_validate_language_rejects_non_iso_form(rel, bad):
    with pytest.raises((ValueError, argparse.ArgumentTypeError)):
        load_module(rel).iso639_1(bad)


# --- label-set + required-field contract (subprocess) ---------------------- #


@pytest.mark.parametrize("rel", GENERATORS)
def test_missing_label_key_is_rejected(rel, tmp_path):
    keys = list(load_module(rel).REQUIRED_LABELS)
    labels = {k: k for k in keys[1:]}  # drop one
    out = tmp_path / "o.md"
    proc = run_cli(
        rel,
        "--language",
        "en",
        "--output-path",
        str(out),
        "--data-json",
        "{}",
        "--labels-json",
        json.dumps(labels),
    )
    assert proc.returncode != 0


@pytest.mark.parametrize("rel", GENERATORS)
def test_extra_label_key_is_rejected(rel, tmp_path):
    labels = _valid_labels(rel)
    labels["__bogus_key__"] = "x"
    out = tmp_path / "o.md"
    proc = run_cli(
        rel,
        "--language",
        "en",
        "--output-path",
        str(out),
        "--data-json",
        "{}",
        "--labels-json",
        json.dumps(labels),
    )
    assert proc.returncode != 0


@pytest.mark.parametrize("rel", GENERATORS)
def test_missing_required_data_is_rejected(rel, tmp_path):
    out = tmp_path / "o.md"
    proc = run_cli(
        rel,
        "--language",
        "en",
        "--output-path",
        str(out),
        "--data-json",
        "{}",
        "--labels-json",
        json.dumps(_valid_labels(rel)),
    )
    assert proc.returncode != 0  # complete label set, but no content fields


@pytest.mark.parametrize("rel", GENERATORS)
def test_invalid_language_form_is_rejected_by_cli(rel, tmp_path):
    out = tmp_path / "o.md"
    proc = run_cli(
        rel,
        "--language",
        "EN",
        "--output-path",
        str(out),
        "--data-json",
        "{}",
        "--labels-json",
        json.dumps(_valid_labels(rel)),
    )
    assert proc.returncode == 2  # argparse type-validation error


# --- quick-ref key_stats rendering (0.16.6) -------------------------------- #

QUICKREF = "modules/quick-reference-generator/scripts/generate_quick_reference.py"


def test_quickref_key_stats_accepts_dicts_and_strings():
    """key_stats tolerates {stat, context} dicts (rendered as a bold figure + a
    dash + context) as well as plain strings (back-compat). Regression guard for
    the 0.16.6 fix where structured items were dumped as raw Python dicts."""
    qr = load_module(QUICKREF)
    labels = {k: k for k in qr.REQUIRED_LABELS}
    md = qr.generate_quickref_md(
        labels,
        {
            "key_stats": [
                {"stat": "2B+ tx/year", "context": "payment platforms"},
                "99%+ SLA",
            ]
        },
    )
    text = md if isinstance(md, str) else "\n".join(md)
    assert "- **2B+ tx/year** — payment platforms" in text  # dict → figure + context
    assert "- 99%+ SLA" in text  # plain string still supported
    assert "{'stat'" not in text and "{\"stat\"" not in text  # never a raw dict dump
