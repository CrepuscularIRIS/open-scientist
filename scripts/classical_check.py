#!/usr/bin/env python3
"""Deterministic completeness check of the classical-recall layer (Open Scientist 0.8).

For every `priority` object in <run>/phase1/classical/recall.json, checks that the deep report
(<obj_id>.md) and its record (<obj_id>.json) carry the user's five visible deliverables
(skills/classical-recall/references/modeling-standard.md). It checks presence, not quality: quality is
judged by the card-level verifier (S7) and by the experiment. Missing items -> status "incomplete";
`lead` (abstract-only) records are never anchors. Prints a JSON summary; rc=0 always unless input is unreadable.

  python3 scripts/classical_check.py --dir <run_dir> [--write]   # --write: stamp check results into each <obj_id>.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ANCHOR = ("authors", "year", "venue", "url", "read_location")
FIELDS = ("construction", "property", "conditions", "mismatch", "entry", "cost", "refuted_by")
COST = ("params", "compute", "data", "storage")
LABELS = ("[原理论]", "[迁移推导]")


def missing(rec: dict, md: str) -> list[str]:
    out = [f"anchor.{k}" for k in ANCHOR if not (rec.get("anchor") or {}).get(k)]
    out += [k for k in FIELDS if not rec.get(k)]
    out += [f"cost.{k}" for k in COST if not (rec.get("cost") or {}).get(k)]
    out += [f"label {l}" for l in LABELS if l not in md]
    year = (rec.get("anchor") or {}).get("year")
    if year and not isinstance(year, int):
        out.append("anchor.year must be an int")
    return out


def check(run: Path) -> dict:
    cdir = run / "phase1" / "classical"
    recall = json.loads((cdir / "recall.json").read_text())
    objs = [o for o in recall.get("candidates", recall if isinstance(recall, list) else [])
            if o.get("tier") == "priority"]
    res = {}
    for o in objs:
        oid = o["obj_id"]
        jp, mp = cdir / f"{oid}.json", cdir / f"{oid}.md"
        if not jp.exists() or not mp.exists():
            res[oid] = {"status": "incomplete", "missing": ["report file"]}
            continue
        rec = json.loads(jp.read_text())
        miss = missing(rec, mp.read_text())
        status = "lead" if rec.get("status") == "lead" else ("modeled" if not miss else "incomplete")
        res[oid] = {"status": status, "missing": miss}
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    try:
        res = check(a.dir.resolve())
    except (OSError, ValueError, KeyError) as e:
        print(f"classical_check: unreadable input: {e}", file=sys.stderr)
        return 2
    if a.write:
        cdir = a.dir.resolve() / "phase1" / "classical"
        for oid, r in res.items():
            p = cdir / f"{oid}.json"
            if p.exists():
                rec = json.loads(p.read_text())
                p.write_text(json.dumps({**rec, "check": r}, ensure_ascii=False, indent=1))
    print(json.dumps({"modeled": [k for k, v in res.items() if v["status"] == "modeled"], "objects": res},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
