"""
Configures the candidate's handwritten signature for use by cover-letter-generator.

Workflow:
1. Takes an input image (PNG, JPG, GIF, BMP).
2. Validates the format (reads the image with Pillow).
3. Automatically resizes if needed to fit under the memory limit
   (~55 KB image, i.e. ~75 KB in base64).
4. Encodes to base64 and writes the result to stdout (to be stored in memory
   via memory_user_edits).

Safety timeout: 10 seconds max on resizing. Beyond that, the script stops with
an instructions message to reduce the image manually.

Usage:
    python setup_signature.py --input-path /path/to/signature.png
    → writes the base64 to stdout (to capture for memory_user_edits)

    python setup_signature.py --input-path /path/to/signature.png --output-path /tmp/sig.b64
    → writes the base64 to a file (useful for debugging)

The produced base64 is meant to be stored in memory under the key
`[CONFIG] Signature base64`, and used by fill_cover_letter.py via
--signature-base64.
"""

import argparse
import base64
import io
import signal
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print(
        "❌ Pillow requis : pip install Pillow --break-system-packages", file=sys.stderr
    )
    sys.exit(1)


# Limits for memory storage
# Memory accepts 100,000 characters per entry; we keep a margin
# for the other data. Target: base64 ≤ 75,000 chars (≈ 55 KB image).
MAX_BASE64_CHARS = 75_000
MAX_IMAGE_BYTES = 55_000

# Target dimensions for a signature (4.3 × 3 cm at 200 DPI ≈ 340 × 240 px,
# largely sufficient for the intended use in the cover letter).
TARGET_MAX_WIDTH = 800
TARGET_MAX_HEIGHT = 600

# Accepted formats
ACCEPTED_FORMATS = {"PNG", "JPEG", "JPG", "GIF", "BMP"}

# Timeout on the resize (seconds)
RESIZE_TIMEOUT_SECONDS = 10


class ResizeTimeout(Exception):
    """Exception raised if resizing exceeds the timeout."""

    pass


def _timeout_handler(signum, frame):
    raise ResizeTimeout()


def resize_with_timeout(img, max_width, max_height, target_bytes, output_format):
    """Progressively resizes the image until it reaches the size target.
    Raises ResizeTimeout if the process takes too long.
    """
    # Install a POSIX alarm (Linux/macOS only; sufficient for
    # the Claude environment)
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(RESIZE_TIMEOUT_SECONDS)
    try:
        # First pass: cap the max dimensions
        img.thumbnail((max_width, max_height), Image.LANCZOS)

        # If already small, encode and check
        buf = io.BytesIO()
        save_kwargs = {}
        if output_format in ("JPEG", "JPG"):
            save_kwargs = {"quality": 85, "optimize": True}
        elif output_format == "PNG":
            save_kwargs = {"optimize": True}
        img.save(buf, format=output_format, **save_kwargs)
        size = buf.tell()

        # Iterate if still too big: reduce dimensions then quality
        attempts = 0
        while size > target_bytes and attempts < 6:
            attempts += 1
            # Reduce by 20% each iteration
            new_w = int(img.width * 0.8)
            new_h = int(img.height * 0.8)
            if new_w < 100 or new_h < 50:
                break  # don't go too low
            img = img.resize((new_w, new_h), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format=output_format, **save_kwargs)
            size = buf.tell()

        return buf.getvalue(), img.size
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


def main():
    parser = argparse.ArgumentParser(
        description="Configures the signature for cover-letter-generator"
    )
    parser.add_argument(
        "--input-path",
        required=True,
        help="Path to the signature image (PNG/JPG/GIF/BMP)",
    )
    parser.add_argument(
        "--output-path",
        default="",
        help="If provided, writes the base64 to this file (otherwise stdout)",
    )
    args = parser.parse_args()

    in_path = Path(args.input_path)
    if not in_path.exists():
        print(f"❌ File not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    # Load the image
    try:
        img = Image.open(in_path)
        img.load()  # force full loading
    except Exception as e:
        print(f"❌ Impossible de lire l'image : {e}", file=sys.stderr)
        print("   Accepted formats: PNG, JPG, GIF, BMP.", file=sys.stderr)
        sys.exit(1)

    if img.format not in ACCEPTED_FORMATS:
        print(f"❌ Unsupported format: {img.format}", file=sys.stderr)
        print(
            f"   Accepted formats: {', '.join(sorted(ACCEPTED_FORMATS))}.",
            file=sys.stderr,
        )
        sys.exit(1)

    original_size = in_path.stat().st_size
    original_dims = img.size
    out_format = "PNG" if img.format == "PNG" else "JPEG"

    # If the image is already under the limit, no need to resize
    if original_size <= MAX_IMAGE_BYTES and max(img.size) <= max(
        TARGET_MAX_WIDTH, TARGET_MAX_HEIGHT
    ):
        # Encode directly
        with open(in_path, "rb") as f:
            raw_bytes = f.read()
        final_size = original_size
        final_dims = original_dims
        print(
            f"✅ Image already optimal: {final_size} bytes, {final_dims[0]}×{final_dims[1]} px",
            file=sys.stderr,
        )
    else:
        # Resizing needed
        print(
            f"ℹ️ Image to resize: {original_size} bytes, {original_dims[0]}×{original_dims[1]} px",
            file=sys.stderr,
        )
        print(
            f"   Target: ≤ {MAX_IMAGE_BYTES} bytes, max {TARGET_MAX_WIDTH}×{TARGET_MAX_HEIGHT} px",
            file=sys.stderr,
        )
        print("   (This may take a few seconds...)", file=sys.stderr)

        # Convert RGBA → RGB when outputting JPEG (no alpha)
        if out_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = bg

        try:
            raw_bytes, final_dims = resize_with_timeout(
                img, TARGET_MAX_WIDTH, TARGET_MAX_HEIGHT, MAX_IMAGE_BYTES, out_format
            )
            final_size = len(raw_bytes)
            print(
                f"✅ Resized: {final_size} bytes, {final_dims[0]}×{final_dims[1]} px",
                file=sys.stderr,
            )
        except ResizeTimeout:
            print(
                f"⏱️ Timeout: resizing exceeded {RESIZE_TIMEOUT_SECONDS} seconds.",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print("To continue, choose an option:", file=sys.stderr)
            print("", file=sys.stderr)
            print("  1. Resize the image yourself, then re-run:", file=sys.stderr)
            print(
                "     - Target: under 500 KB, dimensions ~600×400 px max",
                file=sys.stderr,
            )
            print("     - macOS: Preview → Tools → Adjust Size", file=sys.stderr)
            print("     - Windows: Paint → Resize", file=sys.stderr)
            print("     - Online: tinypng.com, squoosh.app", file=sys.stderr)
            print("", file=sys.stderr)
            print(
                "  2. Proceed without a signature for now and reconfigure later.",
                file=sys.stderr,
            )
            sys.exit(3)

    # Encode to base64
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    if len(b64) > MAX_BASE64_CHARS:
        print(
            f"❌ Image still too large after optimization: {len(b64)} base64 chars",
            file=sys.stderr,
        )
        print(
            f"   (limit: {MAX_BASE64_CHARS}). Provide a simpler image.",
            file=sys.stderr,
        )
        sys.exit(4)

    # Output
    if args.output_path:
        Path(args.output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_path).write_text(b64, encoding="ascii")
        print(f"✅ Signature encoded: {args.output_path}", file=sys.stderr)
        print(
            f"   {len(b64)} base64 characters (≈ {len(raw_bytes) / 1024:.1f} KB decoded)",
            file=sys.stderr,
        )
    else:
        # Stdout: just the base64, for easy capture
        print(b64)
        print(f"ℹ️ {len(b64)} base64 characters produced.", file=sys.stderr)
        print("   To store in memory via: memory_user_edits add", file=sys.stderr)
        print("   under the key: [CONFIG] Signature base64", file=sys.stderr)


if __name__ == "__main__":
    main()
