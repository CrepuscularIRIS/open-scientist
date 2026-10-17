#!/usr/bin/env python3
"""JSON CLI fallback over the exact same Store as the MCP server."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from open_scientist.records import KINDS, Store


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    put = commands.add_parser("put")
    put.add_argument("--kind", choices=sorted(KINDS), required=True)
    put.add_argument("--record-id", required=True)
    put.add_argument("--expected-version", required=True, type=int)
    put.add_argument("--payload-file", required=True, help="JSON file or - for stdin")
    get = commands.add_parser("get")
    get.add_argument("record_id")
    get.add_argument("--version", type=int)
    listing = commands.add_parser("list")
    listing.add_argument("--kind", choices=sorted(KINDS))
    history = commands.add_parser("history")
    history.add_argument("record_id")
    context = commands.add_parser("context")
    context.add_argument("--subject-id")
    context.add_argument("--subject-version", type=int)
    args = parser.parse_args(argv)
    try:
        store = Store(args.project_root)
        if args.command == "put":
            source = sys.stdin.read() if args.payload_file == "-" else Path(args.payload_file).read_text(encoding="utf-8")
            result = store.put(args.kind, args.record_id, json.loads(source), args.expected_version)
        elif args.command == "get":
            result = store.get(args.record_id, args.version)
        elif args.command == "list":
            result = store.list(args.kind)
        elif args.command == "history":
            result = store.history(args.record_id)
        else:
            if (args.subject_id is None) != (args.subject_version is None):
                raise ValueError("--subject-id and --subject-version must be provided together")
            subject = {"id": args.subject_id, "version": args.subject_version} if args.subject_id else None
            result = store.context(subject)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
