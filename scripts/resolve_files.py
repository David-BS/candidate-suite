#!/usr/bin/env python3
"""resolve_files.py — File resolver (CV + signature) for candidate-suite.

SIG-1: signature persistence (and making the CV available) does NOT go through
memory (capped at 500 characters, hence unsuitable for a base64 signature of
about 14,000 characters) but through a **project file** that the skill re-reads
each conversation. This script only **locates** each file and **reports its
status**; it does not read the content and generates nothing. It is the
orchestrator (SKILL.md) that then decides what to do with it — typically passing
the signature path to `fill_cover_letter.py --signature-path`.

No value is hardcoded: the file names come from the config
(`[CONFIG] CV filename`, `[CONFIG] Signature filename`) and are passed as arguments.
The directories are parameterizable to stay portable (see DEP-2 / DEP-4).

Resolution order, per file (first found wins):
    1. session upload    → status "present_upload"   (priority: the user just
                           attached the file in the conversation)
    2. project file      → status "present_project"  (one-time setup: dropped
                           once into the project files)

No Google Drive access: the skill makes NO connector call (0.4.2 — total Drive
removal, see roadmap DRV cluster). If a file is referenced but not found locally,
the status is "referenced_missing" and it is up to the orchestrator to **stop and
ask the user for the file** — never a silent read via a connector (that was the
cause of the FIX-FREEZE hang: a connector call cannot be bounded by
instruction).

Possible statuses:
    present_upload      the file is in the session uploads folder
    present_project     the file is in the project files
    referenced_missing  a name is configured but the file is absent on disk
    none                no name configured (nothing to resolve)

Usage:
    python scripts/resolve_files.py \
        --cv-name "CV_Jordan_Lee-Carter.docx" \
        --signature-name "Signature-DBS_jpg_b64.txt" \
        [--uploads-dir /mnt/user-data/uploads] \
        [--project-dir /mnt/project] \
        [--output-path /home/claude/files.json]

Output: a JSON object on stdout (and in --output-path if provided). Exit code
always 0 — it's a status reporter, not a guardrail.
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_UPLOADS_DIR = "/mnt/user-data/uploads"
DEFAULT_PROJECT_DIR = "/mnt/project"


def resolve_one(name, uploads_dir, project_dir):
    """Resolves a single file and returns a status dict."""
    result = {
        "name": name or "",
        "status": "none",
        "path": None,
        "source": None,
    }

    if not name or not str(name).strip():
        return result

    name = str(name).strip()

    # 1. Session upload (high priority: the user just attached it)
    upload_path = Path(uploads_dir) / name
    if upload_path.is_file():
        result.update(status="present_upload", path=str(upload_path), source="upload")
        return result

    # 2. Project file (one-time setup)
    project_path = Path(project_dir) / name
    if project_path.is_file():
        result.update(status="present_project", path=str(project_path), source="project")
        return result

    # 3. Referenced but not found locally → the orchestrator ASKS for the file.
    #    No Drive fallback (no connector): see docstring / FIX-FREEZE.
    result["status"] = "referenced_missing"
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Resolves the location of the CV and signature (upload → project; no Drive)."
    )
    parser.add_argument("--cv-name", default="", help="CV filename (from [CONFIG] CV filename).")
    parser.add_argument("--signature-name", default="",
                        help="Base64 signature .txt filename (from [CONFIG] Signature filename).")
    parser.add_argument("--uploads-dir", default=DEFAULT_UPLOADS_DIR)
    parser.add_argument("--project-dir", default=DEFAULT_PROJECT_DIR)
    parser.add_argument("--output-path", default="",
                        help="If provided, also writes the JSON to this file.")
    args = parser.parse_args()

    payload = {
        "cv": resolve_one(args.cv_name, args.uploads_dir, args.project_dir),
        "signature": resolve_one(args.signature_name, args.uploads_dir, args.project_dir),
    }

    out = json.dumps(payload, ensure_ascii=False, indent=2)
    print(out)

    if args.output_path:
        Path(args.output_path).write_text(out + "\n", encoding="utf-8")

    # Human-readable summary on stderr (useful in debug, doesn't interfere with the JSON stdout)
    for key in ("cv", "signature"):
        f = payload[key]
        label = key.upper()
        if f["status"] in ("present_project", "present_upload"):
            where = "projet" if f["status"] == "present_project" else "upload"
            print(f"  {label} : présent ({where}) → {f['path']}", file=sys.stderr)
        elif f["status"] == "referenced_missing":
            print(f"  {label} : référencé mais absent ({f['name']}) — à demander à l'utilisateur",
                  file=sys.stderr)
        else:
            print(f"  {label} : aucun nom configuré", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
