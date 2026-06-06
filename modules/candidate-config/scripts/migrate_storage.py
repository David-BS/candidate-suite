"""
Local helper utilities for storage handling.

Used for local Python operations only (copying files between folders, base64
encoding, listing project files). No connector / no Google Drive.

Usage:
    python migrate_storage.py <action> <args...>

Actions:
    encode_signature <input_image>          : Convert an image to base64
    copy_to_outputs <source_path>           : Copy a file to /mnt/user-data/outputs/
    list_project_files                      : List the project files
"""

import sys
import base64
import shutil
from pathlib import Path


def encode_signature(input_path):
    """Converts an image (PNG, JPG) to base64 for text storage"""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"❌ File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    with open(input_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")

    output_path = input_file.parent / f"{input_file.stem}_b64.txt"
    with open(output_path, "w") as f:
        f.write(encoded)

    print(f"✅ Signature encoded: {output_path}")
    print(f"📊 Base64 size: {len(encoded)} characters")
    return str(output_path)


def copy_to_outputs(source_path):
    """Copies a file to /mnt/user-data/outputs/"""
    source = Path(source_path)
    if not source.exists():
        print(f"❌ Source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path("/mnt/user-data/outputs/")
    output_dir.mkdir(parents=True, exist_ok=True)

    dest = output_dir / source.name
    shutil.copy2(source, dest)

    print(f"✅ File copied: {dest}")
    return str(dest)


def list_project_files():
    """Lists the files available in /mnt/project/"""
    project_dir = Path("/mnt/project/")
    if not project_dir.exists():
        print("❌ Pas de dossier projet", file=sys.stderr)
        return

    files = sorted(project_dir.iterdir())
    print(f"📁 Fichiers du projet ({len(files)}) :")
    for f in files:
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            print(f"  • {f.name} ({size_kb:.1f} KB)")


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    args = sys.argv[2:]

    if action == "encode_signature":
        if len(args) < 1:
            print(
                "Usage: python migrate_storage.py encode_signature <input_image>",
                file=sys.stderr,
            )
            sys.exit(1)
        encode_signature(args[0])

    elif action == "copy_to_outputs":
        if len(args) < 1:
            print(
                "Usage: python migrate_storage.py copy_to_outputs <source_path>",
                file=sys.stderr,
            )
            sys.exit(1)
        copy_to_outputs(args[0])

    elif action == "list_project_files":
        list_project_files()

    else:
        print(f"❌ Action inconnue : {action}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
