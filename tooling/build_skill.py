#!/usr/bin/env python3
"""
build_skill.py — formal packager for the candidate-suite skill.

Builds a ready-to-install `.skill` package from the skill source that lives at
the repository root. The version is read from `SKILL.md`'s frontmatter, so the
output filename is always in sync with the declared version.

Why this exists
---------------
The Claude app registers a skill on its frontmatter `name` (not on the package
filename), so installing a new build with the same `name` replaces it in place.
The package filename is free and versioned: `candidate-suite-<x-y-z>.skill`.

Packaging contract (matches the official packager):
  * archive entries are prefixed with `candidate-suite/`
  * DEFLATED compression
  * excludes `__pycache__/`, `*.pyc`, `.DS_Store`
  * includes ONLY the skill source (SKILL.md, CHANGELOG.md, scripts/, modules/,
    references/) — repo meta folders (tooling/, examples/, tests/, docs/,
    .github/) never enter the package.

Usage
-----
    python tooling/build_skill.py                 # -> dist/candidate-suite-<x-y-z>.skill
    python tooling/build_skill.py --output-dir /tmp
"""

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

ARCNAME_PREFIX = "candidate-suite"
INCLUDE = ["SKILL.md", "CHANGELOG.md", "scripts", "modules", "references"]
EXCLUDE_DIRS = {"__pycache__"}
EXCLUDE_SUFFIXES = (".pyc", ".pyo", ".DS_Store")

REPO_ROOT = Path(__file__).resolve().parent.parent


def read_version(skill_md: Path) -> str:
    """Read `version:` from the SKILL.md YAML frontmatter."""
    text = skill_md.read_text(encoding="utf-8")
    m = re.search(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", text, re.MULTILINE)
    if not m:
        sys.exit("ERROR: could not read `version:` from SKILL.md frontmatter.")
    return m.group(1)


def iter_source_files():
    """Yield (absolute_path, arcname) for every file to include, sorted, filtered."""
    for entry in INCLUDE:
        path = REPO_ROOT / entry
        if path.is_file():
            yield path, f"{ARCNAME_PREFIX}/{entry}"
        elif path.is_dir():
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
                for fn in sorted(filenames):
                    if fn.endswith(EXCLUDE_SUFFIXES):
                        continue
                    full = Path(dirpath) / fn
                    rel = full.relative_to(REPO_ROOT)
                    yield full, f"{ARCNAME_PREFIX}/{rel.as_posix()}"
        else:
            sys.exit(f"ERROR: expected source path not found: {entry}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Package the candidate-suite skill.")
    ap.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "dist"),
        help="Output directory (default: ./dist).",
    )
    args = ap.parse_args()

    skill_md = REPO_ROOT / "SKILL.md"
    if not skill_md.is_file():
        sys.exit(f"ERROR: SKILL.md not found at repo root ({REPO_ROOT}).")

    version = read_version(skill_md)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ARCNAME_PREFIX}-{version.replace('.', '-')}.skill"
    if out_path.exists():
        out_path.unlink()

    count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for full, arc in iter_source_files():
            z.write(full, arc)
            count += 1

    # integrity self-check
    with zipfile.ZipFile(out_path) as z:
        names = z.namelist()
    if not all(n.startswith(f"{ARCNAME_PREFIX}/") for n in names):
        raise RuntimeError("integrity check failed: bad arcname prefix")
    if any("__pycache__" in n or n.endswith(EXCLUDE_SUFFIXES) for n in names):
        raise RuntimeError("integrity check failed: excluded file leaked")

    print(f"Built {out_path}")
    print(f"  version : {version}")
    print(f"  entries : {count}")
    print(f"  size    : {out_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
