# Source routing — which connector handles which query type

Retrieval in this install is TWO sources: the local corpora and arXiv. The
OpenAlex / Semantic Scholar / OpenReview connectors still ship in `scripts/`
but are unregistered in `scripts/run.py` (`CONNECTORS`); re-enabling one means
uncommenting its entry there AND adding its job back to
`PHASE0_RETRIEVAL_JOBS`.

## Local corpora — [scripts/search_local.py](../scripts/search_local.py)

- **Strength**: ~80K ACCEPTED papers from NeurIPS / ICLR / ICML / ACL / EMNLP /
  NAACL / CVPR / ICCV / ECCV / AAAI / COLING, 2021-2026, sitting on `/data` as
  PDFs. Real venue, real year, abstracts for the venues whose dumps carried
  them, and — uniquely — the **full text already on disk** (`pdf_path`), so the
  Phase 0 full-text tier fetches nothing over the network for these papers.
- **Use for**: the published tier (`local_published`, 6-24mo) AND as the second
  engine on the freshness window (`local_recent`, 0-6mo), where it contributes
  the current venue year's accepted papers — concurrent work that arXiv's
  lexical ranking routinely misses.
- **Auth**: none. **Rate**: none — a query is a local SQLite FTS5 lookup (~40ms).
- **Index**: `~/.claude/skills/paper-search/scripts/local_corpus.py`
  (`build` / `stats` / `query`), default DB `/data/paper_index/local_papers.db`.
  Rebuild after adding PDFs; `local_extract.py` fills titles/abstracts that
  only exist inside the PDFs.
- **Caveat**: venue-YEAR granularity only. There is no submission date, so
  `published_iso` is empty and every window filter degrades to a YEAR
  comparison — a "0-6mo" window means "this venue year". Citation counts do not
  exist in the corpora (`citations: None`); never rank local records by them.

## arXiv — [scripts/search_arxiv.py](../scripts/search_arxiv.py)

- **Strength**: freshest preprints, no auth, full abstracts.
- **Use for**: 6-month freshness scan in map mode; 6-month focused window in
  collision mode. The only source that sees work published in the last weeks.
- **Auth**: none.
- **Rate**: requests spaced >= 4s apart (cross-process lockfile) with 429
  backoff. This pacing, not the search itself, is what makes Phase 0 take
  minutes.

## Source selection rules

```
mode=map:        arXiv(0-6mo) + local_recent(0-6mo) + local_published(6-24mo)
mode=collision:  arXiv(0-6mo) + local(0-6mo)
```

The freshness window stays DUAL-ENGINE on purpose — arXiv's ranking is weak and
one retriever is a single point of failure (design-notes.md). If a source is
unavailable, continue with the other and emit a `lit_source_unavailable: <source>`
warning. Do not silently skip.

## Dedup priority order

When the same paper appears in both sources after title-normalization:

1. Prefer **local** — it is the ACCEPTED version: real venue, real year, and a
   PDF on disk. `scripts/dedup_merge.py` backfills a missing abstract from the
   losing record, so preferring local never costs an abstract.
2. Then **arXiv** (preprint metadata drifts after publication).

Note the dedup key is `(title_norm, year)`: an arXiv preprint from 2025 and its
ICLR-2026 accepted version do NOT collapse, because the years differ. That is
upstream behaviour, and it means a paper can legitimately appear twice with
different venues.
