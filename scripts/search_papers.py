#!/usr/bin/env python3
"""Retrieve discovery leads from a read-only local corpus and arXiv."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from open_scientist.search import DEFAULT_DB, search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", required=True, help="1–8 plain keyword queries separated by |")
    parser.add_argument("--sources", nargs="+", choices=("local", "arxiv"), default=["local", "arxiv"])
    parser.add_argument("--max-papers", type=int, default=20, help="Final display cap and per-query request cap (1–100)")
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--timeout", type=float, default=10, help="Per-request/SQLite timeout in seconds (up to 60)")
    parser.add_argument("--budget-seconds", type=float, default=25, help="Scheduling budget in seconds (up to 300)")
    parser.add_argument("--json", type=Path, help="Also save the JSON report to this file")
    args = parser.parse_args()
    if args.json:
        index = Path(os.environ.get("PAPER_SEARCH_LOCAL_DB", DEFAULT_DB)).expanduser().resolve()
        target = args.json.expanduser().resolve()
        if target == index or (target.exists() and index.exists() and target.samefile(index)):
            parser.error("JSON output must not overwrite the local paper index")
        args.json = target
    try:
        result = search(args.queries.split("|"), sources=args.sources, max_papers=args.max_papers,
                        start_year=args.start_year, end_year=args.end_year, timeout=args.timeout,
                        budget_seconds=args.budget_seconds)
    except ValueError as exc:
        parser.error(str(exc))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json:
        try:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            parser.exit(2, f"Could not write JSON report: {exc}\n")
    print(text)
    # A source failure is data in the report, not an unparseable CLI exception.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
