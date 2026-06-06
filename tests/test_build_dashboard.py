"""Tier 1 — DRV-7 conversation-column rendering guard.

renderConv is client-side JS, so CI (pytest, no JS engine) can only assert the
wiring is present in the generated HTML. Behavioural correctness (states,
most-recent-first ordering, realTitle attributed to the most-recent LINKED
conversation only, non-clickable ◆/✗) is verified out-of-band with Node.
"""

from _helpers import run_cli

DASH = "modules/application-tracker/scripts/build_dashboard.py"


def test_drv7_web_column_uses_glyphs_ordering_and_drops_old_tooltip(tmp_path):
    out = tmp_path / "dash.html"
    proc = run_cli(DASH, "--output-path", str(out))
    assert proc.returncode == 0, proc.stderr
    html = out.read_text(encoding="utf-8")
    # Compact open-glyph per linked conversation (web) — new in 0.17→DRV-7.
    assert "\\u2197" in html
    # Most-recent-first ordering wired.
    assert "items.sort" in html
    # The old date-text web tooltip (title = date) is retired in favour of the
    # date (+ most-recent-linked title) tooltip.
    assert "rawLabel||url" not in html
