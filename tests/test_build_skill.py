"""Tier 1 — skill packaging integrity (tooling/build_skill.py).

Functional guarantee under test: the published .skill is clean — every entry is
under the canonical prefix, build artifacts (__pycache__, *.pyc, *.pyo,
.DS_Store) never leak in, and the archive name carries the SKILL.md version.
"""

import re
import zipfile

from _helpers import REPO_ROOT, load_module, run_cli

BUILD_REL = "tooling/build_skill.py"
BS = load_module(BUILD_REL)


def test_build_produces_clean_versioned_skill(tmp_path):
    proc = run_cli(BUILD_REL, "--output-dir", str(tmp_path))
    assert proc.returncode == 0, proc.stderr

    skills = list(tmp_path.glob("*.skill"))
    assert len(skills) == 1
    # name: candidate-suite-<version with dashes>.skill
    assert re.fullmatch(r"candidate-suite-\d+-\d+-\d+\.skill", skills[0].name)

    with zipfile.ZipFile(skills[0]) as z:
        names = z.namelist()
    assert names, "archive is empty"
    # every entry under the canonical prefix
    assert all(n.startswith(f"{BS.ARCNAME_PREFIX}/") for n in names)
    # no build artifacts leaked
    assert not any("__pycache__" in n for n in names)
    assert not any(n.endswith(BS.EXCLUDE_SUFFIXES) for n in names)


def test_version_in_name_matches_skill_md(tmp_path):
    version = None
    for line in (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("version:"):
            version = line.split(":", 1)[1].strip()
            break
    assert version, "version not found in SKILL.md"

    run_cli(BUILD_REL, "--output-dir", str(tmp_path))
    expected = f"{BS.ARCNAME_PREFIX}-{version.replace('.', '-')}.skill"
    assert (tmp_path / expected).exists()
