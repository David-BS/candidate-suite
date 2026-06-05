"""Shared test helpers: locate, run (black-box) and import (white-box) skill scripts."""

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def script_path(relpath):
    """Absolute path to a skill script, relative to the repository root."""
    p = REPO_ROOT / relpath
    assert p.exists(), f"script not found: {p}"
    return p


def run_cli(relpath, *args, timeout=120):
    """Run a skill script as a subprocess — tests the real CLI contract.

    Returns the CompletedProcess (.returncode / .stdout / .stderr)."""
    return subprocess.run(
        [sys.executable, str(script_path(relpath)), *map(str, args)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def load_module(relpath, name=None):
    """Import a skill script by path — for white-box unit tests of pure helpers."""
    path = script_path(relpath)
    spec = importlib.util.spec_from_file_location(name or path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
