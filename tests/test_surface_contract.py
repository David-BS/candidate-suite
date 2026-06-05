"""Tier 1 — interface-label surface contract (LNG-2).

Functional guarantee under test: no half-localized interface. Each surface
defaults to the English label set; if a localized set is supplied via
--labels-json it must carry the EXACT key set (any missing or extra key is
rejected), so a surface is either fully English or fully localized — never
partial.
"""

import json

import pytest

from _helpers import load_module, run_cli

# Surfaces that default to LABELS_EN and accept an optional exact --labels-json.
SURFACES = [
    "scripts/build_selector.py",
    "scripts/build_preferences.py",
    "modules/application-tracker/scripts/build_guide.py",
    "modules/application-tracker/scripts/build_dashboard.py",
]


def _en_keys(rel):
    return list(load_module(rel).LABELS_EN)


@pytest.mark.parametrize("rel", SURFACES)
def test_default_to_english_without_labels_json(rel, tmp_path):
    out = tmp_path / "out.html"
    proc = run_cli(rel, "--output-path", str(out))
    assert proc.returncode == 0, proc.stderr
    assert out.exists()


@pytest.mark.parametrize("rel", SURFACES)
def test_exact_label_set_is_accepted(rel, tmp_path):
    labels = {k: k for k in _en_keys(rel)}
    out = tmp_path / "out.html"
    proc = run_cli(rel, "--output-path", str(out), "--labels-json", json.dumps(labels))
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("rel", SURFACES)
def test_missing_label_key_is_rejected(rel, tmp_path):
    keys = _en_keys(rel)
    labels = {k: k for k in keys[1:]}  # drop exactly one key
    out = tmp_path / "out.html"
    proc = run_cli(rel, "--output-path", str(out), "--labels-json", json.dumps(labels))
    assert proc.returncode != 0


@pytest.mark.parametrize("rel", SURFACES)
def test_extra_label_key_is_rejected(rel, tmp_path):
    labels = {k: k for k in _en_keys(rel)}
    labels["__bogus_key__"] = "x"
    out = tmp_path / "out.html"
    proc = run_cli(rel, "--output-path", str(out), "--labels-json", json.dumps(labels))
    assert proc.returncode != 0
