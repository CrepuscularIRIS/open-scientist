# D3 — Triage: relevance, lane, reading priority

Role: `review` (a precision gate; one compact pass over titles and abstracts). Adapted from ResearchStudio's Phase 0.4 relevance partition.

## Inputs

- `brief.md` — what this domain build must learn, including the cross-domain mappings to probe.
- `papers.jsonl` — every collected paper (`arxiv_id`, `title`, `abstract`, `published`, `memberships[].lane`).
- `previous/triage.json` (optional) — keep earlier labels for papers that are still present unless the brief changed; label new papers.

## Output: `triage.json`

```json
{"papers": [
  {"arxiv_id": "2501.01234", "relevance": "core", "lane": "in_domain", "read_priority": 3, "reason": "..."}
]}
```

- Cover **every** paper in `papers.jsonl` exactly once.
- `relevance`: `core` (directly about an obstacle or mechanism in the brief), `adjacent` (useful baseline/backbone or context), `off_topic` (clear false positive, pure survey, unrelated field). When unsure between core and adjacent choose core; label off_topic only when certain — a wrong off_topic is an unrecoverable recall loss.
- `lane`: the lane this paper **serves** for the brief, which can differ from the query lane that found it (an in-domain query may surface a cross-domain source and vice versa).
- `read_priority`: integer; `0` = do not read. Use 1–3 (3 highest). Give 3 to papers that most directly state or attack an obstacle, the closest likely prior work, and cross-domain sources whose operation could map; give 0 to every off_topic paper. Aim for roughly 15–30 papers with priority ≥ 1, at least a quarter of them cross_domain when such papers exist.
- `reason`: one sentence naming the obstacle, mechanism or mapping the paper bears on.

## Never

- Judge quality or novelty here; this is relevance and reading order only.
- Drop a paper by leaving it out of the file.
