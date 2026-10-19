"""Command line for per-venue OpenReview outcome collection, export and linking."""
from __future__ import annotations

import argparse
from http.client import HTTPException
import json
import sqlite3
import sys

from forge.vendor.openreview_export import export, link
from forge.vendor.openreview_labels import Labels, Transport, read_credentials


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Explicit label store directory, separate from installed plugin")
    subs = parser.add_subparsers(dest="command", required=True)
    harvest = subs.add_parser("harvest", help="Collect or resume whole venue-years; no PDFs or model calls")
    harvest.add_argument("--venue", action="append", required=True, help="e.g. ICLR.cc/2025/Conference; repeatable")
    harvest.add_argument("--env-file", help="File with OPENREVIEW_USERNAME / OPENREVIEW_PASSWORD")
    harvest.add_argument("--page-size", type=int, default=100)
    harvest.add_argument("--max-pages", type=int, help="Stop after N pages; the venue is reported partial")
    harvest.add_argument("--refresh", action="store_true",
                         help="Start a new pass from offset 0 (always restarts); plain reruns resume. Old passes stay")
    subs.add_parser("status")
    out = subs.add_parser("export", help="Write a topic subset plus full venue denominators")
    out.add_argument("--output", required=True)
    out.add_argument("--venue")
    out.add_argument("--query", help="Terms that must all appear in title, abstract or keywords")
    out.add_argument("--primary-area")
    out.add_argument("--no-review-text", action="store_true")
    out.add_argument("--allow-partial", action="store_true", help="Export a venue without a completed pass; marked complete=false")
    links = subs.add_parser("link", help="Propose same_work links to an arXiv corpus export")
    links.add_argument("--corpus-export", required=True)
    args = parser.parse_args(argv)
    try:
        with Labels(args.root) as labels:
            if args.command == "harvest":
                transport = Transport(*read_credentials(args.env_file))
                result = labels.harvest(args.venue, transport, page_size=args.page_size,
                                        max_pages=args.max_pages, refresh=args.refresh)
            elif args.command == "export":
                result = export(labels, args.output, venue=args.venue, query=args.query,
                                primary_area=args.primary_area, review_text=not args.no_review_text,
                                allow_partial=args.allow_partial)
            elif args.command == "link":
                result = link(labels, args.corpus_export)
            else:
                result = labels.report()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.command == "harvest" and not result["collection_ok"] else 0
    except (OSError, ValueError, HTTPException, sqlite3.Error) as exc:
        print(f"openreview: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
