"""
CSV engine for the application-tracking dashboard.

This script makes NO network / connector call. It only manipulates the CONTENT
of the CSV file:
- init   : create an empty CSV (headers only)
- upsert : add / update ONE application
- bulk   : add / update SEVERAL applications (historical init)
- batch-status : apply several status changes at once
                 (comes from the dashboard's "Enregistrer" button)

Persistence (0.5.0 / DRV-4): the CSV lives in the **project files**, versioned by
the timestamp in its name (`Applications_Tracker_YYYY-MM-DD_HHMM.csv`). No Google
Drive. The write ritual is manual on the user's side: the assistant regenerates the
CSV → present_files → the user adds it to the project → deletes the previous version
spotted by its name.

Application key: (company, position), normalized — **the date is NOT part of the
key** (DRV-4). The same application resumed another day stays the same row. The
"is this really the same application?" call is made by the ASSISTANT (which asks
when in doubt), not by a rigid key; this script only provides the mechanical write
target (company, position).

ACCUMULATIVE fields (union, never overwritten):
- conversation : one marker per run/conversation, labeled **by date** (no time),
                 e.g. "2026-05-28 → 55beb831-…" (bare UUID) or "2026-05-28 ◆";
                 separated by " ; ".
                 This is the bridge to the archive (deliverables live in their
                 conversation — "conversation = archive", see roadmap).
- deliverables : union of the deliverable types produced across runs.
Other fields (language, status, notes) are overwritten by a non-empty value.
The date is that of the FIRST activity (preserved on merge).

CSV columns (fixed order):
    date, company, position, language, status, deliverables, conversation, notes

Usage:
    # The SCRIPT builds the timestamped name (Paris time) — pass --output-dir,
    # NOT a hand-composed name. Read the printed path to present the file.
    python manage_tracker.py init --output-dir /home/claude

    python manage_tracker.py upsert \\
        --input-path suivi.csv --output-dir /home/claude \\
        --entry-json '{"date":"2026-05-28","company":"Acme","position":"SWE",
                       "deliverables":["cover_letter"],
                       "conversation":"2026-05-28 → 55beb831-9e77-4a54-84d1-8b652e6f85ae"}'

    python manage_tracker.py bulk \\
        --input-path suivi.csv --output-dir /home/claude \\
        --entries-json '[{...},{...}]'

    python manage_tracker.py batch-status \\
        --input-path suivi.csv --output-dir /home/claude \\
        --changes-json '[{"company":"Acme","position":"SWE","status":"Interview scheduled"}]'

    # (--output-path is still accepted as a fallback, but manual naming is
    #  discouraged: it's the source of the `20260530` vs `2026-05-30` drift.)

If --input-path is absent/empty, we start from an empty CSV.
deliverables and conversation can be a JSON list or a string; stored
in CSV as a string separated by " ; ".
"""

import argparse
import csv
import io
import json
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path


FIELDNAMES = [
    "date",
    "company",
    "position",
    "language",
    "status",
    "deliverables",
    "conversation",
    "title",
    "notes",
]

# `title` (DRV-5): the REAL title of the most recently linked conversation, captured at
# scan and REWRITTEN on every reconcile. It's a volatile DISPLAY field (the desktop
# dashboard prefers it to the fabricated marker `📋 …`), NEVER an identity key. The key
# stays (company, position). Empty until a reconcile has captured a real title.

DEFAULT_STATUS = "Applied"
MULTI_SEP = " ; "
# Multi-value fields accumulated as a union across runs.
MULTI_FIELDS = ("deliverables", "conversation")


def split_multi(val):
    """Splits a multi value (list or ';'-separated string) into clean items."""
    if val is None:
        return []
    if isinstance(val, list):
        items = [str(x).strip() for x in val]
    else:
        items = [x.strip() for x in str(val).split(";")]
    return [x for x in items if x]


def normalize_multi(val):
    """List or string → CSV-safe string separated by MULTI_SEP, deduplicated."""
    return MULTI_SEP.join(_dedup(split_multi(val)))


def _dedup(items):
    """Case-insensitive deduplication, first-occurrence order preserved."""
    out, seen = [], set()
    for it in items:
        key = it.lower()
        if key not in seen:
            out.append(it)
            seen.add(key)
    return out


def merge_multi(existing_val, new_val):
    """Union of two multi-value fields (existing first, then new)."""
    return MULTI_SEP.join(_dedup(split_multi(existing_val) + split_multi(new_val)))


def entry_key(entry):
    """Write key: normalized (company, position). The date is NOT in the key."""
    return (
        str(entry.get("company", "")).strip().lower(),
        str(entry.get("position", "")).strip().lower(),
    )


def clean_entry(raw):
    """Normalizes an incoming entry (dict) to the CSV schema."""
    entry = {f: "" for f in FIELDNAMES}
    for f in FIELDNAMES:
        if f in raw and raw[f] is not None:
            if f in MULTI_FIELDS:
                entry[f] = normalize_multi(raw[f])
            else:
                entry[f] = str(raw[f]).strip()
    if not entry["status"]:
        entry["status"] = DEFAULT_STATUS
    return entry


def parse_csv(text):
    """Parses the CSV content into a list of dicts. Tolerant if empty/malformed."""
    entries = []
    if not text or not text.strip():
        return entries
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        entry = {f: (row.get(f, "") or "").strip() for f in FIELDNAMES}
        entries.append(entry)
    return entries


def render_csv(entries):
    """Generates the CSV content (with header), sorted by descending date."""
    sorted_entries = sorted(
        entries,
        key=lambda e: (e.get("date", ""), e.get("company", "")),
        reverse=True,
    )
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    for e in sorted_entries:
        writer.writerow({f: e.get(f, "") for f in FIELDNAMES})
    return buf.getvalue()


def upsert_entries(existing, new_entries):
    """Merges new_entries into existing (update if same (company, position), else add).

    - conversation / deliverables : ACCUMULATED (union, never overwritten);
    - date : PRESERVED (first activity) — not overwritten by a later run;
    - other fields : overwritten by a non-empty value (status: not by the default)."""
    by_key = {entry_key(e): e for e in existing}
    for raw in new_entries:
        ne = clean_entry(raw)
        k = entry_key(ne)
        if k in by_key:
            merged = dict(by_key[k])
            for field in FIELDNAMES:
                val = ne.get(field, "")
                if field in MULTI_FIELDS:
                    merged[field] = merge_multi(merged.get(field, ""), val)
                elif field == "date":
                    # first activity: never overwrite an existing date
                    if not merged.get("date"):
                        merged["date"] = val
                elif val and not (
                    field == "status" and val == DEFAULT_STATUS and merged.get("status")
                ):
                    merged[field] = val
            by_key[k] = merged
        else:
            by_key[k] = ne
    return list(by_key.values())


def apply_status_changes(existing, changes):
    """Applies a list of status changes (batch from the dashboard).
    Each change: {company, position, status}."""
    by_key = {entry_key(e): e for e in existing}
    applied = 0
    for ch in changes:
        k = entry_key(ch)
        new_status = str(ch.get("status", "")).strip()
        if k in by_key and new_status:
            by_key[k]["status"] = new_status
            applied += 1
    return list(by_key.values()), applied


# ---------------------------------------------------------------------------
# DRV-5 — Reconciliation (`reconcile` mode)
#
# Moves the reconciliation logic OUT of the assistant's HEAD and into the
# code, deterministic and testable. This is the root cause of DRV-6: as long as the
# `✗` marking relied on the assistant's diligence, it could
# be missed (and it was, on 30/05).
#
# The assistant does the SCAN (only it has `conversation_search`/`recent_chats` —
# zero connector here) and passes the result as JSON; this script applies the
# mechanical reconciliation. Decisions frozen upstream:
#   • Promotion `◆ → {uuid}` by key (company, position) — NEVER by title.
#   • `✗` driven by a scan FLOOR (invariant below), and
#     MANDATORY when the case is conclusive (DRV-6 symmetry).
#   • The title is a volatile display field (`title` column), never a key.
#   • Union of links: one application may have several conversations.
# ---------------------------------------------------------------------------

ARROW = "\u2192"  # →
# Language-agnostic marker glyphs (DRV-9). ◆ = current / not yet linked;
# ✗ = deleted. Linked state (date → uuid) is unchanged. Glyph-only since the CSV
# migration: the legacy FR-token backward-compat was dropped (EN-canonical).
HERE_GLYPH = "\u25c6"  # ◆
DEL_GLYPH = "\u2717"  # ✗
ICI_RE = re.compile(r"\u25C6")
DEL_RE = re.compile(r"\u2717")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
CANONICAL_PREFIX = "\U0001f4cb"  # 📋


def parse_marker(m):
    """Parses a conversation marker → (date, state, uuid).

    state ∈ {'current', 'linked', 'deleted', 'bare'}. uuid is non-empty only for
    'linked'. We store ONLY the bare UUID after the arrow (the title lives in the
    `title` column, not in the marker)."""
    m = (m or "").strip()
    date_m = DATE_RE.search(m)
    date = date_m.group(1) if date_m else ""
    if DEL_RE.search(m):
        return date, "deleted", ""
    if ARROW in m:
        uuid = m.split(ARROW, 1)[1].strip()
        return date, "linked", uuid
    if ICI_RE.search(m):
        return date, "current", ""
    return date, "bare", ""


def make_linked(date, uuid):
    return "%s %s %s" % (date, ARROW, uuid)


def format_marker(date, state, uuid=""):
    """Canonical (glyph) rendering of a marker: 'current' -> '<date> ◆',
    'deleted' -> '<date> ✗', 'linked' -> '<date> → <uuid>', 'bare' -> '<date>'."""
    if state == "linked":
        return make_linked(date, uuid)
    if state == "deleted":
        return "%s %s" % (date, DEL_GLYPH)
    if state == "current":
        return "%s %s" % (date, HERE_GLYPH)
    return date


def dedup_markers(markers):
    """Dedup of markers. Links are deduplicated BY UUID (the first activity — the
    oldest date — is kept); the others by string."""
    out, seen_uuid, seen_str = [], {}, set()
    for m in markers:
        date, state, uid = parse_marker(m)
        if state == "linked" and uid:
            if uid in seen_uuid:
                idx = seen_uuid[uid]
                ex_date, _, _ = parse_marker(out[idx])
                if date and (not ex_date or date < ex_date):
                    out[idx] = make_linked(date, uid)
                continue
            seen_uuid[uid] = len(out)
            out.append(make_linked(date, uid) if date else m)
        else:
            key = m.strip().lower()
            if key in seen_str:
                continue
            seen_str.add(key)
            out.append(m.strip())
    return out


def _index_scan(scan):
    """Builds the scan indexes. Returns (uuids, by_uuid, by_key, floor).

    - by_uuid : uuid → {date, title, company, position}
    - by_key  : (comp_lc, pos_lc) → list of entries {uuid, date, title, ...}
                (UNION — an application can have several conversations)
    - floor   : oldest enumerated date (= min of the scan dates).
                Invariant: everything ≥ floor has been enumerated, so an
                absence ≥ floor is CONCLUSIVE."""
    uuids, by_uuid, by_key, dates = set(), {}, {}, []
    for s in scan:
        uid = str(s.get("uuid", "")).strip()
        d = str(s.get("date", "")).strip()
        comp = str(s.get("company", "")).strip()
        pos = str(s.get("position", "")).strip()
        title = str(s.get("title", "")).strip()
        if uid:
            uuids.add(uid)
            by_uuid[uid] = {"date": d, "title": title, "company": comp, "position": pos}
        if d:
            dates.append(d)
        if comp and pos and uid:
            by_key.setdefault((comp.lower(), pos.lower()), []).append(
                {
                    "uuid": uid,
                    "date": d,
                    "title": title,
                    "company": comp,
                    "position": pos,
                }
            )
    floor = min(dates) if dates else ""
    return uuids, by_uuid, by_key, floor


def _most_recent_title(uuids, by_uuid):
    """Real title of the most recent linked conversation (captured at scan)."""
    best_date, best_title = "", ""
    for u in uuids:
        info = by_uuid.get(u)
        if info and info.get("title") and info["date"] >= best_date:
            best_date, best_title = info["date"], info["title"]
    return best_title


def reconcile(existing, scan, floor=None, add_new=True):
    """Reconciles the tracker with a conversation scan.

    Returns (rows, summary). summary = {promoted, deleted, new, floor, linked_added,
    hygiene:[{uuid, current_title, proposed_title, company, position, date}]}.

    Non-destructive: statuses, notes and first-activity dates are preserved.
    """
    scanned_uuids, by_uuid, by_key, scan_floor = _index_scan(scan)
    if floor is None or not str(floor).strip():
        floor = scan_floor
    floor = str(floor).strip()

    rows = [dict(r) for r in existing]
    promoted = deleted = linked_added = 0

    for row in rows:
        k = entry_key(row)
        cands = by_key.get(k, [])
        recent = max(cands, key=lambda c: c["date"]) if cands else None
        markers = split_multi(row.get("conversation", ""))
        out_markers = []
        for m in markers:
            date, state, uid = parse_marker(m)
            if state == "current":
                if recent and recent["uuid"]:
                    out_markers.append(
                        make_linked(date or recent["date"], recent["uuid"])
                    )
                    promoted += 1
                else:
                    out_markers.append(
                        format_marker(date, "current") if date else m
                    )  # not found → stays current (◆)
            elif state == "linked":
                # ✗ marking MANDATORY if conclusive: linked, absent from the
                # scan, and date ≥ floor (hence within the enumerated slice).
                if (
                    uid
                    and uid not in scanned_uuids
                    and floor
                    and date
                    and date >= floor
                ):
                    out_markers.append(format_marker(date, "deleted"))
                    deleted += 1
                else:
                    out_markers.append(m)  # present, or < floor (undetermined)
            else:
                # deleted stays ✗; a bare date is left untouched
                out_markers.append(
                    format_marker(date, "deleted") if state == "deleted" else m
                )

        # Union: add any scanned conversation for this key whose UUID
        # is not already a marker (application resumed another day, etc.).
        present = {
            parse_marker(x)[2] for x in out_markers if parse_marker(x)[1] == "linked"
        }
        for c in cands:
            if c["uuid"] and c["uuid"] not in present:
                out_markers.append(make_linked(c["date"], c["uuid"]))
                present.add(c["uuid"])
                linked_added += 1

        out_markers = dedup_markers(out_markers)
        row["conversation"] = MULTI_SEP.join(out_markers)

        # title: real title of the most recent linked conv (rewritten each run).
        linked_here = [
            parse_marker(x)[2] for x in out_markers if parse_marker(x)[1] == "linked"
        ]
        best = _most_recent_title(linked_here, by_uuid)
        if best:
            row["title"] = best

    # New applications: scan keys absent from the tracker.
    new_count = 0
    if add_new:
        existing_keys = {entry_key(r) for r in rows}
        for key, cands in by_key.items():
            if key in existing_keys:
                continue
            recent = max(cands, key=lambda c: c["date"])
            new_row = {f: "" for f in FIELDNAMES}
            new_row["date"] = recent["date"]
            new_row["company"] = recent["company"]
            new_row["position"] = recent["position"]
            new_row["status"] = DEFAULT_STATUS
            new_row["conversation"] = MULTI_SEP.join(
                dedup_markers([make_linked(c["date"], c["uuid"]) for c in cands])
            )
            new_row["title"] = _most_recent_title([c["uuid"] for c in cands], by_uuid)
            rows.append(new_row)
            new_count += 1

    # Naming-hygiene report: real title vs canonical
    # `📋 {first-activity date} - company - position` (date STABLE over time).
    hygiene = []
    for row in rows:
        comp, pos, d0 = (
            row.get("company", ""),
            row.get("position", ""),
            row.get("date", ""),
        )
        canonical = "%s %s - %s - %s" % (CANONICAL_PREFIX, d0, comp, pos)
        for m in split_multi(row.get("conversation", "")):
            date, state, uid = parse_marker(m)
            if state != "linked" or not uid:
                continue
            info = by_uuid.get(uid)
            if not info:
                continue
            real = (info.get("title") or "").strip()
            if real and real != canonical:
                hygiene.append(
                    {
                        "uuid": uid,
                        "current_title": real,
                        "proposed_title": canonical,
                        "company": comp,
                        "position": pos,
                        "date": d0,
                    }
                )

    summary = {
        "promoted": promoted,
        "deleted": deleted,
        "new": new_count,
        "linked_added": linked_added,
        "floor": floor,
        "hygiene": hygiene,
    }
    return rows, summary


def load_input(input_path):
    if input_path and Path(input_path).exists():
        return Path(input_path).read_text(encoding="utf-8")
    return ""


def resolve_output_path(args):
    """The SCRIPT builds the unique timestamped name (never the assistant by hand).

    - If --output-path is provided, we respect it (fallback / backward-compat).
    - Otherwise we generate `Applications_Tracker_YYYYMMDD_HHMM.csv` (no dashes in
      the date) in --output-dir (default: current folder).
    No-dash format: aligned with the normalization the Claude app applies when
    indexing CSV files in a project (observed on 2026-05-30).
    Paris time (Europe/Paris, DST handled) — pure stdlib (zoneinfo), zero external dependency.
    The chosen path is printed by every command → the assistant presents THAT
    file, without ever composing the name itself.
    """
    explicit = getattr(args, "output_path", None)
    if explicit:
        return explicit
    out_dir = getattr(args, "output_dir", None) or "."
    stamp = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y%m%d_%H%M")
    return str(Path(out_dir) / f"Applications_Tracker_{stamp}.csv")


def write_output(output_path, content):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def cmd_init(args):
    out = resolve_output_path(args)
    write_output(out, render_csv([]))
    print(f"✅ Blank tracker CSV created: {out}")


def cmd_upsert(args):
    existing = parse_csv(load_input(args.input_path))
    try:
        entry = json.loads(args.entry_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    merged = upsert_entries(existing, [entry])
    out = resolve_output_path(args)
    write_output(out, render_csv(merged))
    print(f"✅ Application added/updated. Total: {len(merged)} row(s).")
    print(f"   {out}")


def cmd_bulk(args):
    existing = parse_csv(load_input(args.input_path))
    try:
        new_entries = json.loads(args.entries_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(new_entries, list):
        print("❌ entries-json must be a JSON list", file=sys.stderr)
        sys.exit(1)
    merged = upsert_entries(existing, new_entries)
    out = resolve_output_path(args)
    write_output(out, render_csv(merged))
    print(
        f"✅ {len(new_entries)} application(s) processed. Total: {len(merged)} row(s)."
    )
    print(f"   {out}")


def cmd_batch_status(args):
    existing = parse_csv(load_input(args.input_path))
    try:
        changes = json.loads(args.changes_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(changes, list):
        print("❌ changes-json must be a JSON list", file=sys.stderr)
        sys.exit(1)
    merged, applied = apply_status_changes(existing, changes)
    out = resolve_output_path(args)
    write_output(out, render_csv(merged))
    print(f"✅ {applied} status change(s) applied. Total: {len(merged)} row(s).")
    print(f"   {out}")


def cmd_reconcile(args):
    existing = parse_csv(load_input(args.input_path))
    try:
        scan = json.loads(args.scan_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON (scan): {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(scan, list):
        print("❌ scan-json must be a JSON list", file=sys.stderr)
        sys.exit(1)
    rows, summary = reconcile(
        existing,
        scan,
        floor=getattr(args, "floor", None),
        add_new=not getattr(args, "no_add_new", False),
    )
    out = resolve_output_path(args)
    write_output(out, render_csv(rows))

    print("✅ Reconciliation applied.")
    print(f"   • {summary['promoted']} marker(s) ◆ → linked")
    print(f"   • {summary['linked_added']} link(s) added (union)")
    print(f"   • {summary['new']} new application(s)")
    print(f"   • {summary['deleted']} conversation(s) marked ✗")
    print(f"   • scan floor: {summary['floor'] or '(empty scan)'}")
    if summary["hygiene"]:
        print(f"   • {len(summary['hygiene'])} conversation(s) to rename (hygiene)")
    print(f"   Total: {len(rows)} row(s).")
    print(f"   {out}")
    # Machine block so the assistant composes the recap / hygiene report.
    print("---RECONCILE-SUMMARY-JSON---")
    print(json.dumps(summary, ensure_ascii=False))
    print("---END-RECONCILE-SUMMARY-JSON---")


def main():
    parser = argparse.ArgumentParser(description="CSV engine for application tracking")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--output-path", default="")
    p.add_argument("--output-dir", default=".")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("upsert")
    p.add_argument("--input-path", default="")
    p.add_argument("--output-path", default="")
    p.add_argument("--output-dir", default=".")
    p.add_argument("--entry-json", required=True)
    p.set_defaults(func=cmd_upsert)

    p = sub.add_parser("bulk")
    p.add_argument("--input-path", default="")
    p.add_argument("--output-path", default="")
    p.add_argument("--output-dir", default=".")
    p.add_argument("--entries-json", required=True)
    p.set_defaults(func=cmd_bulk)

    p = sub.add_parser("batch-status")
    p.add_argument("--input-path", default="")
    p.add_argument("--output-path", default="")
    p.add_argument("--output-dir", default=".")
    p.add_argument("--changes-json", required=True)
    p.set_defaults(func=cmd_batch_status)

    p = sub.add_parser("reconcile")
    p.add_argument("--input-path", default="")
    p.add_argument("--output-path", default="")
    p.add_argument("--output-dir", default=".")
    p.add_argument(
        "--scan-json",
        required=True,
        help='JSON: [{"uuid","date","company","position","title"}, ...]. '
        "An entry without company+position serves only enumeration "
        "(floor + deletion detection), without creating/promoting.",
    )
    p.add_argument(
        "--floor",
        default="",
        help="Scan floor YYYY-MM-DD (default: min of the scan dates). "
        "Any linked marker ≥ floor and absent = conclusive → ✗.",
    )
    p.add_argument(
        "--no-add-new",
        action="store_true",
        help="Do not create new applications from the scan.",
    )
    p.set_defaults(func=cmd_reconcile)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
