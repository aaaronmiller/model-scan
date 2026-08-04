#!/usr/bin/env python3
"""Extract stalled intent-archaeology batch items and validate verdicts before merge.

Diagnosis, 2026-07-30: 165 batch items across 9 batches carry ``verdict IS
NULL``. They were emitted for classification and no verdict ever came back, so
the projects they belong to have zero intents despite having human turns.
``code-claude-code-proxy`` is the worst affected: 55 unclassified of 63 batched,
which is why the gateway program had no attributed intent at all.

This is not a rejection problem. A rejected item carries a verdict. These carry
none, so the merge's ID-accounting gate never fired and the gap stayed silent.

Two subcommands:

    extract   read-only dump of pending items with full source text
    validate  check a verdicts file against the merge gates *before* merging

The validator exists because the archive already holds 252
``verifier_disagreement`` observations, all "verbatim not found in source turn".
A verbatim span that is not an exact substring of its source is rejected at
merge time. Catching that here keeps failed attempts out of the archive.

Read-only against ``archaeology.db``. Writes nothing. The merge itself is done
by the pipeline's own ``05-merge.py``, which is the only sanctioned writer.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Any

DB = Path.home() / ".intent-archaeology" / "archaeology.db"

# Vocabulary observed in the existing corpus. A verdict outside this set would
# create a new type silently, so it is rejected rather than accepted.
VALID_TYPES = {
    "directive.feature",
    "directive.constraint",
    "question",
    "bugreport",
    "correction.behavior",
    "correction.factual",
    "meta.harness",
    "preference.style",
    "noise",
}
VALID_SCOPES = {"project", "feature", "global", "file"}

MIN_VERBATIM_CHARS = 12


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def normalize(text: str) -> str:
    """Fold the differences that make an otherwise-exact quote fail.

    Only Unicode form and whitespace runs are folded. Case is preserved,
    because a verbatim span should be verbatim.
    """

    text = unicodedata.normalize("NFC", text or "")
    return " ".join(text.split())


def cmd_extract(args: argparse.Namespace) -> int:
    con = connect()
    where = "bi.verdict IS NULL"
    params: list[Any] = []
    if args.project:
        where += " AND e.project_id = ?"
        params.append(args.project)
    if args.batch:
        where += " AND bi.batch_id = ?"
        params.append(args.batch)

    rows = con.execute(
        f"""SELECT bi.batch_id, bi.event_id, e.project_id, e.ts, e.text, e.cwd
            FROM batch_item bi JOIN event e ON e.id = bi.event_id
            WHERE {where}
            ORDER BY e.ts""",
        params,
    ).fetchall()

    items = [
        {
            "id": r["event_id"],
            "batch_id": r["batch_id"],
            "project_id": r["project_id"],
            "ts": r["ts"],
            "cwd": r["cwd"],
            "text": r["text"] or "",
        }
        for r in rows
        if (r["text"] or "").strip()
    ]

    out = Path(args.out).expanduser() if args.out else None
    payload = {"pending": len(items), "items": items}
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"extracted {len(items)} pending item(s) -> {out}")
    else:
        print(json.dumps(payload, indent=1, ensure_ascii=False))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check verdicts against every gate the merge enforces, before merging."""

    raw = json.loads(Path(args.verdicts).expanduser().read_text(encoding="utf-8"))
    verdicts = raw.get("verdicts") or raw.get("items") or raw if isinstance(raw, list) else raw.get("verdicts", [])
    if isinstance(raw, dict) and not verdicts:
        verdicts = raw.get("items") or []

    con = connect()
    problems: list[str] = []
    seen: set[str] = set()
    counts: dict[str, int] = {}

    for v in verdicts:
        eid = v.get("id")
        if not eid:
            problems.append("verdict with no id")
            continue
        if eid in seen:
            problems.append(f"{eid}: duplicate verdict")
            continue
        seen.add(eid)

        vtype = (v.get("type") or "").strip()
        counts[vtype or "<missing>"] = counts.get(vtype or "<missing>", 0) + 1
        if vtype not in VALID_TYPES:
            problems.append(f"{eid}: unknown type {vtype!r}")
            continue
        if vtype == "noise":
            continue  # noise carries no statement or verbatim

        statement = (v.get("statement") or "").strip()
        verbatim = (v.get("verbatim") or "").strip()
        if not statement:
            problems.append(f"{eid}: missing statement")
        if not verbatim:
            problems.append(f"{eid}: missing verbatim")
            continue
        if len(verbatim) < MIN_VERBATIM_CHARS:
            problems.append(f"{eid}: verbatim too short ({len(verbatim)} chars)")

        scope = v.get("scope")
        if scope is not None and scope not in VALID_SCOPES:
            problems.append(f"{eid}: unknown scope {scope!r}")

        row = con.execute("SELECT text FROM event WHERE id = ?", (eid,)).fetchone()
        if row is None:
            problems.append(f"{eid}: no such event")
            continue

        source = normalize(row["text"] or "")
        if normalize(verbatim) not in source:
            # This is the failure mode behind all 252 existing
            # verifier_disagreement observations.
            problems.append(f"{eid}: verbatim not found in source turn")

    # ID accounting: the merge requires every submitted id to return a verdict.
    if args.batch:
        submitted = {
            r["event_id"]
            for r in con.execute(
                "SELECT event_id FROM batch_item WHERE batch_id = ? AND verdict IS NULL",
                (args.batch,),
            )
        }
        missing = submitted - seen
        if missing and not args.allow_partial:
            problems.append(
                f"{len(missing)} pending item(s) in {args.batch} have no verdict; "
                "merge will reject as silent omission (use --allow-partial to check anyway)"
            )

    print(f"verdicts: {len(verdicts)}")
    for t, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {t:<24} {c}")
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)")
        for p in problems[:40]:
            print(f"  - {p}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        return 1
    print("\nOK: all gates pass; safe to merge")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ia_repair", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="dump pending batch items")
    ex.add_argument("--project")
    ex.add_argument("--batch")
    ex.add_argument("--out")
    ex.set_defaults(func=cmd_extract)

    va = sub.add_parser("validate", help="check verdicts before merging")
    va.add_argument("--verdicts", required=True)
    va.add_argument("--batch")
    va.add_argument("--allow-partial", action="store_true")
    va.set_defaults(func=cmd_validate)

    args = ap.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
