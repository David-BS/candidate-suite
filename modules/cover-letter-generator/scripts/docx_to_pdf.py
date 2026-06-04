"""
Converts a .docx to .pdf via LibreOffice headless.

Usage:
    python docx_to_pdf.py --input /path/Cover_Letter_....docx \\
        [--output /path/Cover_Letter_....pdf] [--outdir /path/]

- If --output is provided, the final PDF takes that path/name.
- Otherwise, the PDF is created in --outdir (default: the .docx's folder) with
  the same base name as the .docx.

Exit codes:
    0 = success
    1 = input file not found
    3 = LibreOffice unavailable (the letter stays available as .docx)
    4 = timeout
    5 = conversion failure
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_soffice():
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path:
            return path
    return None


def convert(input_path, output_path=None, outdir=None):
    inp = Path(input_path)
    if not inp.exists():
        print(f"❌ Fichier introuvable : {inp}", file=sys.stderr)
        sys.exit(1)

    soffice = find_soffice()
    if not soffice:
        print(
            "❌ LibreOffice introuvable : conversion .docx → PDF impossible "
            "dans cet environnement.",
            file=sys.stderr,
        )
        print("   → La lettre reste parfaitement utilisable en .docx.", file=sys.stderr)
        sys.exit(3)

    target_dir = (
        Path(outdir)
        if outdir
        else (Path(output_path).parent if output_path else inp.parent)
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    # Isolated temporary profile: avoids lock conflicts if LibreOffice
    # is already used elsewhere in the session.
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            soffice,
            "--headless",
            f"-env:UserInstallation=file://{profile}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(target_dir),
            str(inp),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            print("❌ Conversion expirée (LibreOffice).", file=sys.stderr)
            sys.exit(4)

    produced = target_dir / (inp.stem + ".pdf")
    if not produced.exists():
        print("❌ Échec de la conversion .docx → PDF.", file=sys.stderr)
        if res.stdout.strip():
            print(res.stdout, file=sys.stderr)
        if res.stderr.strip():
            print(res.stderr, file=sys.stderr)
        sys.exit(5)

    if output_path and Path(output_path).resolve() != produced.resolve():
        shutil.move(str(produced), str(output_path))
        produced = Path(output_path)

    print(f"✅ PDF généré : {produced}")
    return produced


def main():
    ap = argparse.ArgumentParser(description="Converts a .docx to PDF (LibreOffice).")
    ap.add_argument("--input", required=True, help="Source .docx path")
    ap.add_argument("--output", default="", help="Output PDF path (optional)")
    ap.add_argument("--outdir", default="", help="Output folder (optional)")
    args = ap.parse_args()
    convert(args.input, args.output or None, args.outdir or None)


if __name__ == "__main__":
    main()
