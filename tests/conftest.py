"""Pytest configuration.

Dependency markers implement the graded model: tests tagged with a dependency
they cannot satisfy are skipped (never failed). This lets the same suite run at
three levels — L0 (PR/push, stdlib + python-docx + markdown logic), L1 (release
tag, + wkhtmltopdf), L2 (major tag vX.0.0, + libreoffice) — by simply installing
more in the runner; absent tools are skipped, not red.
"""

import importlib.util
import shutil
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "_data"


def _has_module(name):
    return importlib.util.find_spec(name) is not None


def _has_binary(*names):
    return any(shutil.which(n) for n in names)


# marker name -> (human description, availability predicate)
_DEP_MARKERS = {
    "needs_docx": ("the python-docx package", lambda: _has_module("docx")),
    "needs_markdown": ("the markdown package", lambda: _has_module("markdown")),
    "needs_wkhtmltopdf": ("the wkhtmltopdf binary", lambda: _has_binary("wkhtmltopdf")),
    "needs_libreoffice": (
        "the libreoffice/soffice binary",
        lambda: _has_binary("libreoffice", "soffice"),
    ),
}


def pytest_configure(config):
    for name, (desc, _) in _DEP_MARKERS.items():
        config.addinivalue_line("markers", f"{name}: test requires {desc}")


def pytest_collection_modifyitems(config, items):
    for item in items:
        for name, (desc, available) in _DEP_MARKERS.items():
            if name in item.keywords and not available():
                item.add_marker(
                    pytest.mark.skip(reason=f"requires {desc} (not available)")
                )


@pytest.fixture
def data_dir():
    """Directory of fictional test fixtures (no real personal data)."""
    return DATA_DIR


@pytest.fixture
def seed_csv():
    """Read-only fictional seed tracker (used as --input-path; never mutated)."""
    return DATA_DIR / "tracker_seed.csv"


@pytest.fixture
def signature_b64_file(tmp_path):
    """A valid fictional signature, base64 in a file, generated at runtime.

    Generated here (stdlib only) rather than committed: signature artifacts are
    git-ignored for privacy, so the fixture must not depend on a tracked file.
    """
    import base64
    import struct
    import zlib

    w, h = 8, 4

    def _chunk(tag, data):
        c = tag + data
        return (
            struct.pack(">I", len(data))
            + c
            + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _ in range(h))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )
    path = tmp_path / "signature_b64.txt"
    path.write_text(base64.b64encode(png).decode(), encoding="utf-8")
    return path
