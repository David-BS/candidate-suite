"""Tier 1 — application-tracking engine (manage_tracker.py).

Functional guarantee under test: the tracker never corrupts the user's data —
no duplicate applications, the first-activity date is preserved, statuses are
not clobbered by the default, conversation links accumulate, and the
reconciliation (promote / delete / floor) is deterministic.

Two styles, as agreed: white-box (import) for the pure helpers, black-box
(subprocess) for the CLI contract the orchestrator relies on.
"""

import json
import re

from _helpers import load_module, run_cli

MT_REL = "modules/application-tracker/scripts/manage_tracker.py"
MT = load_module(MT_REL)


def _row(**kw):
    """A full CSV row (all fields), overridden by kw."""
    row = {f: "" for f in MT.FIELDNAMES}
    row.update(kw)
    return row


# --------------------------------------------------------------------------- #
# White-box — pure helpers (multi-value handling, keys, normalization)
# --------------------------------------------------------------------------- #


def test_split_multi_handles_list_string_and_none():
    assert MT.split_multi(["a", " b ", ""]) == ["a", "b"]
    assert MT.split_multi("a ; b ; ; c") == ["a", "b", "c"]
    assert MT.split_multi(None) == []


def test_dedup_is_case_insensitive_first_wins():
    assert MT._dedup(["CV", "cv", "Letter"]) == ["CV", "Letter"]


def test_merge_multi_is_union_existing_first():
    assert MT.merge_multi("a ; b", "b ; c") == "a ; b ; c"


def test_entry_key_normalizes_and_excludes_date():
    k1 = MT.entry_key({"company": " Acme ", "position": "HoE", "date": "2026-01-01"})
    k2 = MT.entry_key({"company": "acme", "position": " hoe ", "date": "2099-12-31"})
    assert k1 == ("acme", "hoe") == k2  # case/space-insensitive, date irrelevant


def test_clean_entry_defaults_status_to_applied():
    e = MT.clean_entry({"company": "Acme", "position": "HoE"})
    assert e["status"] == "Applied"
    assert set(e) == set(MT.FIELDNAMES)


# --------------------------------------------------------------------------- #
# White-box — upsert merge semantics (the no-corruption core)
# --------------------------------------------------------------------------- #


def test_upsert_same_key_does_not_duplicate_and_unions_multifields():
    existing = [
        _row(
            date="2026-05-20",
            company="Acme",
            position="HoE",
            deliverables="cover_letter",
            status="Applied",
        )
    ]
    new = [
        {
            "date": "2026-06-01",
            "company": "acme",
            "position": "hoe",
            "deliverables": ["interview_prep"],
        }
    ]
    merged = MT.upsert_entries(existing, new)
    assert len(merged) == 1  # same (company, position) key, case-insensitive
    assert merged[0]["date"] == "2026-05-20"  # first activity preserved
    assert "cover_letter" in merged[0]["deliverables"]
    assert "interview_prep" in merged[0]["deliverables"]  # union


def test_upsert_default_status_does_not_override_existing():
    existing = [_row(company="Acme", position="HoE", status="Interview scheduled")]
    new = [{"company": "Acme", "position": "HoE", "deliverables": ["cover_letter"]}]
    merged = MT.upsert_entries(existing, new)
    assert (
        merged[0]["status"] == "Interview scheduled"
    )  # default 'Applied' must not clobber


def test_apply_status_changes_by_key_counts_applied():
    existing = [_row(company="Acme", position="HoE", status="Applied")]
    rows, applied = MT.apply_status_changes(
        existing, [{"company": "Acme", "position": "HoE", "status": "Offer"}]
    )
    assert applied == 1
    assert rows[0]["status"] == "Offer"


# --------------------------------------------------------------------------- #
# White-box — marker parsing + reconciliation (promote / delete / floor)
# --------------------------------------------------------------------------- #


def test_parse_marker_recognizes_all_states():
    assert MT.parse_marker("2026-05-20 \u25c6") == ("2026-05-20", "current", "")
    assert MT.parse_marker("2026-05-20 \u2192 u1") == ("2026-05-20", "linked", "u1")
    assert MT.parse_marker("2026-05-20 \u2717") == ("2026-05-20", "deleted", "")
    assert MT.parse_marker("2026-05-20") == ("2026-05-20", "bare", "")


def test_reconcile_promotes_current_to_linked_by_key():
    existing = [
        _row(
            date="2026-05-20",
            company="Acme",
            position="HoE",
            conversation="2026-05-20 \u25c6",
        )
    ]
    scan = [
        {
            "uuid": "u1",
            "date": "2026-05-20",
            "company": "Acme",
            "position": "HoE",
            "title": "chat",
        }
    ]
    rows, summary = MT.reconcile(existing, scan)
    assert summary["promoted"] == 1
    assert "\u2192 u1" in rows[0]["conversation"]  # ◆ became → u1


def test_reconcile_does_not_promote_by_title_only_by_key():
    existing = [
        _row(
            date="2026-05-20",
            company="Acme",
            position="HoE",
            conversation="2026-05-20 \u25c6",
        )
    ]
    scan = [
        {
            "uuid": "u1",
            "date": "2026-05-20",
            "company": "Globex",
            "position": "Dir",
            "title": "chat",
        }
    ]  # different key
    rows, summary = MT.reconcile(existing, scan, add_new=False)
    assert summary["promoted"] == 0
    assert "\u25c6" in rows[0]["conversation"]  # stays current


def test_reconcile_marks_deleted_when_linked_absent_above_floor():
    existing = [
        _row(
            date="2026-05-20",
            company="Acme",
            position="HoE",
            conversation="2026-05-20 \u2192 u_old",
        )
    ]
    scan = [
        {
            "uuid": "u_other",
            "date": "2026-05-20",
            "company": "Acme",
            "position": "HoE",
            "title": "t",
        }
    ]
    rows, summary = MT.reconcile(existing, scan)  # floor = 2026-05-20
    assert summary["deleted"] == 1  # u_old absent & >= floor → conclusive
    assert "\u2717" in rows[0]["conversation"]


def test_reconcile_keeps_linked_below_floor_undetermined():
    existing = [
        _row(company="Acme", position="HoE", conversation="2026-05-01 \u2192 u_old")
    ]
    scan = [
        {
            "uuid": "u_x",
            "date": "2026-05-20",
            "company": "Acme",
            "position": "HoE",
            "title": "t",
        }
    ]  # floor = 2026-05-20
    rows, summary = MT.reconcile(existing, scan)
    assert summary["deleted"] == 0  # u_old date < floor → not conclusive
    assert "u_old" in rows[0]["conversation"]


def test_reconcile_adds_new_application_from_scan():
    rows, summary = MT.reconcile(
        [],
        [
            {
                "uuid": "u1",
                "date": "2026-05-22",
                "company": "Globex",
                "position": "Director of Engineering",
                "title": "t",
            }
        ],
    )
    assert summary["new"] == 1
    assert rows[0]["company"] == "Globex"
    assert rows[0]["status"] == "Applied"
    assert "u1" in rows[0]["conversation"]


# --------------------------------------------------------------------------- #
# Black-box — CLI contract (the orchestrator relies on exit codes + files)
# --------------------------------------------------------------------------- #


def test_cli_init_creates_header_only_timestamped_csv(tmp_path):
    proc = run_cli(MT_REL, "init", "--output-dir", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    files = list(tmp_path.glob("Applications_Tracker_*.csv"))
    assert len(files) == 1
    # filename convention: no dashes in the date segment (YYYYMMDD_HHMM)
    assert re.fullmatch(r"Applications_Tracker_\d{8}_\d{4}\.csv", files[0].name)
    lines = files[0].read_text(encoding="utf-8").strip().splitlines()
    assert lines == [",".join(MT.FIELDNAMES)]  # header only, no rows


def test_cli_upsert_same_key_no_duplicate(tmp_path):
    seed = tmp_path / "seed.csv"
    run_cli(MT_REL, "init", "--output-path", str(seed))
    out1 = tmp_path / "o1.csv"
    run_cli(
        MT_REL,
        "upsert",
        "--input-path",
        str(seed),
        "--output-path",
        str(out1),
        "--entry-json",
        json.dumps(
            {
                "date": "2026-05-20",
                "company": "Acme",
                "position": "HoE",
                "deliverables": ["cover_letter"],
            }
        ),
    )
    out2 = tmp_path / "o2.csv"
    proc = run_cli(
        MT_REL,
        "upsert",
        "--input-path",
        str(out1),
        "--output-path",
        str(out2),
        "--entry-json",
        json.dumps(
            {
                "date": "2026-06-01",
                "company": "acme",
                "position": "hoe",
                "deliverables": ["interview_prep"],
            }
        ),
    )
    assert proc.returncode == 0, proc.stderr
    rows = MT.parse_csv(out2.read_text(encoding="utf-8"))
    assert len(rows) == 1
    assert rows[0]["date"] == "2026-05-20"
    assert "cover_letter" in rows[0]["deliverables"]
    assert "interview_prep" in rows[0]["deliverables"]


def test_cli_batch_status_applies_to_existing_row(tmp_path, seed_csv):
    out = tmp_path / "o.csv"
    changes = json.dumps(
        [
            {
                "company": "Acme Financial Group",
                "position": "Head of Engineering",
                "status": "Offer",
            }
        ]
    )
    proc = run_cli(
        MT_REL,
        "batch-status",
        "--input-path",
        str(seed_csv),
        "--output-path",
        str(out),
        "--changes-json",
        changes,
    )
    assert proc.returncode == 0, proc.stderr
    rows = MT.parse_csv(out.read_text(encoding="utf-8"))
    acme = next(r for r in rows if r["company"] == "Acme Financial Group")
    assert acme["status"] == "Offer"


def test_cli_invalid_json_exits_1(tmp_path):
    proc = run_cli(
        MT_REL,
        "upsert",
        "--output-path",
        str(tmp_path / "o.csv"),
        "--entry-json",
        "{not valid json}",
    )
    assert proc.returncode == 1
    assert "JSON" in proc.stderr


def test_cli_reconcile_emits_machine_summary(tmp_path, seed_csv):
    out = tmp_path / "o.csv"
    scan = json.dumps(
        [
            {
                "uuid": "11111111-1111-1111-1111-111111111111",
                "date": "2026-05-18",
                "company": "Globex",
                "position": "Director of Engineering",
                "title": "Globex chat",
            }
        ]
    )
    proc = run_cli(
        MT_REL,
        "reconcile",
        "--input-path",
        str(seed_csv),
        "--output-path",
        str(out),
        "--scan-json",
        scan,
    )
    assert proc.returncode == 0, proc.stderr
    block = proc.stdout.split("---RECONCILE-SUMMARY-JSON---")[1]
    block = block.split("---END-RECONCILE-SUMMARY-JSON---")[0].strip()
    summary = json.loads(block)
    assert {"promoted", "deleted", "new", "floor", "linked_added", "hygiene"} <= set(
        summary
    )
