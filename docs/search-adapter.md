# Local corpus + arXiv retrieval

From the plugin directory:

```bash
python scripts/search_papers.py --queries 'memory selection|vision language action' \
  --sources local arxiv --max-papers 20 --start-year 2024 --end-year 2026 \
  --timeout 10 --budget-seconds 25 --json /tmp/paper-search.json
```

The script also works by absolute path from any working directory. It prints one
JSON report to stdout; `--json` optionally saves the same report. Omit `--sources`
for the default `local arxiv`. Use `--sources local` for offline operation. This
adapter does not register Semantic Scholar, OpenAlex, other remote connectors,
or model-memory nominations.

## Local index

`PAPER_SEARCH_LOCAL_DB` selects an existing SQLite index, defaulting to
`/data/paper_index/local_papers.db`. The adapter opens `mode=ro`, enables
`query_only`, and executes a parameterized FTS5 query with `LIMIT`. It never builds
or repairs an index, walks PDF directories, reads every corpus row into Python,
or copies PDFs. Returned `pdf_path` is a reference, not proof the file exists or
has been read. The report cannot overwrite the configured index.

The currently supported schema is:

- `papers`: `id`, `title`, `abstract`, `authors` (JSON list), `venue`, `year`,
  `url`, `pdf_path`, `corpus`, `keywords`, `title_source`, `abstract_source`.
- `papers_fts`: FTS5 on `title`, `abstract`, `keywords`, `authors`, external content
  `papers`, `content_rowid='id'`.

No index is distributed. Other machines can point the variable at an index with
this schema, or use only arXiv. Missing and incompatible indexes are reported
separately. Unknown publication years are excluded when a year filter is active.

## Queries, limits and network behavior

Queries are **plain keywords**, separated by `|`; words within each query are
ANDed. They are not raw SQLite/arXiv query expressions. Provide 1–8 distinct
queries, each at most 512 characters and 32 tokens. Narrow synonyms and separate
cross-field queries are preferable to one long sentence.

`--max-papers` (1–100) caps each source/query request and the final merged list.
Results are interleaved across attempts before deduplication to prevent the
first broad query consuming every display slot. DOI, arXiv IDs without version
suffixes, and normalized titles are used for deduplication; every source/query
reference remains in `provenance`. Title matching is a heuristic: original
source references remain available for identity checks.

arXiv uses one Atom request per query, at least 3.1 seconds between sequential
requests in this invocation, no automatic retries, and a 2 MiB response ceiling.
Independent simultaneous plugin invocations are not coordinated; avoid concurrent
arXiv search processes. Request format follows the
[official arXiv API manual](https://info.arxiv.org/help/api/user-manual.html).

`--timeout` (default 10, maximum 60 seconds) bounds SQLite work and individual
network socket operations. `--budget-seconds` (default 25, maximum 300) stops
starting further work when the scheduling budget is exhausted; waiting for the
arXiv request interval also counts. **This is not a hard process wall-time
deadline:** DNS, TLS, or an already active socket read can overshoot it. The
report includes elapsed time and explicit outcomes for skipped queries. Use a
host process deadline if strict wall-time termination is required.

## Reading the report

`sources.<name>.attempts[]` preserves the outcome of every query:

| Source | Status | Meaning |
|---|---|---|
| local | `ok` | Matching index records returned |
| local | `empty` | Query completed with no matching records |
| local | `missing_index` | Configured database does not exist |
| local | `error` | Schema, SQLite, access, or budget failure |
| arxiv | `ok` | Valid Atom paper records returned |
| arxiv | `empty` | Valid feed, no matching records |
| arxiv | `timeout` | Request timeout or remaining scheduling budget exhausted |
| arxiv | `rate_limited` | HTTP 429; no immediate retry |
| arxiv | `unavailable` | Transport, HTTP, malformed/incomplete response, or API error |

A source with one successful and one failed query can have `status: ok` and
`partial: true`; inspect its attempts. `coverage.failed_sources` identifies
sources with any failed/skipped attempts. `coverage.limited` records query or
display truncation. `coverage.partial` is true for either failure or truncation.
Even when false, it only means the requested bounded operations completed; it
does not mean literature coverage is exhaustive.

Exit status 0 means a report was produced, including a report where sources
failed. Invalid CLI arguments or an unwritable output file return a nonzero
status. Consumers must inspect coverage and source statuses.

All output has `evidence_status: retrieval_only`. A hit is an index/API record,
not a checked scientific claim. Model recollection belongs in a separate
nomination record; first resolve source identity, then fetch/read the relevant
content to check claim support, direction, and applicable system. An empty
result never establishes novelty or the absence of relevant prior work.

## Verification and provenance

The offline unit suite uses temporary real SQLite FTS5 databases and recorded
Atom fixtures. It exercises missing/empty/error distinctions, read-only behavior,
year filtering, result caps, malformed/timeout/429 transport, cross-source
deduplication/provenance, partial coverage, and the executable CLI:

```bash
python -m unittest discover -s tests -p test_search.py -v
```

On 2026-10-17, the actual local index returned results for `memory selection`
and `vision language action` in about 0.013 seconds. One bounded live arXiv
request returned `timeout` (about 9.8 seconds with an 8-second socket timeout).
This verifies graceful degradation in that environment, **not successful live
arXiv retrieval**. Atom parsing is verified offline.

This adapter was independently implemented from the observed database schema
and public arXiv API contract. Existing local `paper-search` scripts were read
for interface discovery; their source was not copied or bundled. No license is
assumed for those unrelated scripts or the paper corpus. The new adapter follows
this repository's license; paper content and metadata retain their own rights.
