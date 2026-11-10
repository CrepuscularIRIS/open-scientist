#!/usr/bin/env python3
"""Verdicts for the property-test layer (Open Scientist 0.9, ml domain) — a quick check, not a gate of rigour.

Reads <run>/phase1/anchor_tests.json (one record per tested anchor: does the anchor's claimed property hold on
this project's real code path, frozen checkpoint, no training?), and with --write prunes clearly-failed anchors
from <run>/phase1/classical_anchors.json (kept under `killed_by_test`) and writes the done marker.

  T2.pass true  -> PASS        T2.pass false -> KILL        T2.pass null / missing -> UNTESTABLE (kept)
Idea borrowed from TCSExam (arXiv 2611.07962): run a claim through a script before trusting prose about it.

  python3 scripts/property_check.py --dir <run_dir> [--write]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def verdict(t: dict) -> str:
    p = (t.get("T2") or {}).get("pass")
    return "UNTESTABLE" if p is None else ("PASS" if p else "KILL")


def check(run: Path) -> dict:
    tests = json.loads((run / "phase1" / "anchor_tests.json").read_text()).get("tests", [])
    return {t["obj_id"]: verdict(t) for t in tests}


def rewrite_anchors(run: Path, res: dict) -> None:
    ap = run / "phase1" / "classical_anchors.json"
    anchors = json.loads(ap.read_text())
    order = anchors.get("order", [])
    anchors["order"] = [dict(o, property_test=res[o["obj_id"]]) if o["obj_id"] in res else o
                        for o in order if res.get(o["obj_id"]) != "KILL"]
    gone = {o["obj_id"] for o in order if res.get(o["obj_id"]) == "KILL"}
    anchors["killed_by_test"] = sorted(set(anchors.get("killed_by_test", [])) | gone)
    ap.write_text(json.dumps(anchors, ensure_ascii=False, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    run = a.dir.resolve()
    try:
        res = check(run)
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"property_check: unreadable input: {e}", file=sys.stderr)
        return 2
    if a.write:
        rewrite_anchors(run, res)
        (run / "phase1" / ".property_tests_done").write_text("")
    print(json.dumps({"verdicts": res}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
