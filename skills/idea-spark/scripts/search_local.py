"""Local corpus search connector.

Why: the machine already holds ~80K published papers as PDFs on /data
(OpenReview dumps + CCF-A 2026 proceedings). Querying them costs no network,
no credentials and ~40ms, and every hit is a peer-reviewed venue record whose
full text is already on disk — which is what the published tier of Phase 0
retrieval used to buy from OpenAlex / Semantic Scholar.

The index itself lives in the paper-search skill (`local_corpus.py`, SQLite
FTS5). This connector adapts it to the idea-spark hit schema.

I/O:
  python3 -m scripts.search_local --queries '["...","..."]' --window-months 6 --out hits.json

Granularity caveat: the corpora record a venue YEAR, never a submission date,
so `published_iso` is empty and the window filter compares YEARS. A 0-6mo
window therefore means "this venue year", not "the last 180 days".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# The FTS index and its builder live in the paper-search skill; both skills are
# installed side by side under ~/.claude/skills/.
_DEFAULT_INDEX_SCRIPTS = Path.home() / ".claude" / "skills" / "paper-search" / "scripts"


def _load_corpus_module():
    """Import local_corpus from wherever the paper-search skill is installed."""
    try:
        import local_corpus                      # already importable
        return local_corpus
    except ImportError:
        pass
    candidate = Path(os.environ.get("PAPER_SEARCH_SCRIPTS_DIR",
                                    str(_DEFAULT_INDEX_SCRIPTS))).expanduser()
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
    try:
        import local_corpus
        return local_corpus
    except ImportError as exc:
        raise ImportError(
            f"local_corpus.py not found in {candidate}. Install the paper-search "
            f"skill, or point PAPER_SEARCH_SCRIPTS_DIR at its scripts/ directory."
        ) from exc


def normalize_title(t: str) -> str:
    return re.sub(r'\W+', ' ', (t or '').lower()).strip()[:80]


def search(query: str, max_results: int = 100, since_year: int = 0,
           until_year: int = 0) -> list[dict]:
    """Query the local index and return records in the idea-spark hit schema.

    Args:
        query: One search query.
        max_results: Cap on returned records.
        since_year: Earliest venue year to keep (0 = no lower bound).
        until_year: Latest venue year to keep (0 = no upper bound).

    Returns:
        Hit dicts carrying the standard connector fields plus `pdf_path`.
    """
    corpus = _load_corpus_module()
    rows = corpus.search(
        query,
        start_year=since_year or 1990,
        end_year=until_year or 2100,
        max_results=max_results,
    )
    out = []
    for row in rows:
        title = row.get("title") or ""
        pdf_path = row.get("pdf_path") or ""
        source_id = Path(pdf_path).stem if pdf_path else normalize_title(title)[:60]
        out.append({
            'title': title,
            'title_norm': normalize_title(title),
            'abstract': row.get("abstract") or "",
            'year': row.get("year"),
            'venue': row.get("venue") or "",
            'authors': row.get("authors") or [],
            'citations': None,          # the corpora carry no citation data
            'source': 'local',
            'source_id': source_id,
            'doi': '',
            'paper_url': row.get("url") or "",
            'published_iso': '',        # venue-YEAR granularity only, see module docstring
            'pdf_path': pdf_path,       # full text already on disk — no fetch needed
        })
    return out


def in_window(paper: dict, since: datetime, until: datetime) -> bool:
    """Year-granularity window test: the corpora have no finer date than the venue year."""
    year = paper.get('year')
    if not year:
        return True                     # undated record: keep, never silently drop
    return since.year <= int(year) <= until.year


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--queries', required=True, help='JSON list of query strings')
    ap.add_argument('--window-months', type=int, default=24,
                    help='Window-max in months (papers older than this are excluded)')
    ap.add_argument('--window-min-months', type=int, default=0,
                    help='Window-min in months (papers newer than this are excluded)')
    ap.add_argument('--as-of', default='',
                    help='YYYY-MM-DD: backdate the window reference date; default = real now')
    ap.add_argument('--max-per-query', type=int, default=50)
    ap.add_argument('--max-results', type=int, default=0,
                    help='Final cap on output (0 = no cap)')
    ap.add_argument('--published-only', action='store_true',
                    help='No-op: every local record is a published venue paper')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    from scripts._time_guard import resolve_now
    now = resolve_now(args.as_of)

    queries = json.loads(args.queries)
    since = now - timedelta(days=30 * args.window_months)
    until = now - timedelta(days=30 * args.window_min_months)
    per_query = []
    for q in queries:
        try:
            hits = search(q, max_results=args.max_per_query,
                          since_year=since.year, until_year=until.year)
        except Exception as e:
            print(f'  local {q!r} failed: {e}', file=sys.stderr)
            per_query.append([])
            continue
        per_query.append([h for h in hits if in_window(h, since, until)])

    from scripts._merge import interleave_by_query
    merged = interleave_by_query(per_query, lambda h: h.get('title_norm'),
                                 args.max_results, queries=queries)
    if len(queries) > 1:
        print(f'  local: {sum(len(p) for p in per_query)} in-window across '
              f'{len(queries)} queries -> {len(merged)} kept (round-robin)', file=sys.stderr)
    Path(args.out).write_text(json.dumps(merged, ensure_ascii=False, indent=1))
    print(f'wrote {args.out} with {len(merged)} unique papers', file=sys.stderr)


if __name__ == '__main__':
    main()
