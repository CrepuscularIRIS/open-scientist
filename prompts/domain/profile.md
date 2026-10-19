# D7 — Domain profile: reviewer expectations, collision lexicon, cross-domain map

Role: `review`. Three files that later steps use instead of generic rubrics: what this field demands of a paper, which words to search when checking whether an idea already exists, and which cross-domain transfers are on the table.

## Inputs

- `brief.md`, `cards/` (index + card files), `readings/*.json`.
- `profile/baselines.json` — deterministic registry of baselines/datasets/metrics the readings use, with counts.
- `profile/timeline.json` — deterministic per-card dates, `recent_share` (fraction of member papers in the corpus's last 12 months) and corpus span.
- `labels.jsonl` (optional) — official outcomes, one row per submission event (paper, venue, year, outcome).
- `reviews.jsonl` (optional) — review text: `{review_id, paper_ref, text, source}` per review or meta-review. Only this file makes an expectation `observed_in_reviews`.
- `previous/profile/` (optional) — the version being revised.

## Output 1: `profile/expectations.json`

What a reviewer in **this** field expects (replaces Companion's generic 7 dimensions and RS's static rubric as the first check; the generic dimensions stay as a fallback):

```json
{"expectations": [
  {"id": "E01", "text": "Compare against DreamerV3 on DMC at equal environment steps", "kind": "baseline",
   "applies_when": "an empirical claim that a planning method improves return on continuous control",
   "evidence": [{"kind": "paper_practice", "ref": "2501.01234"}, {"kind": "paper_practice", "ref": "2406.05555"},
                {"kind": "paper_practice", "ref": "2409.04444"}, {"kind": "review", "ref": "R12", "quote": "No comparison to DreamerV3 at equal steps."}],
   "strength": "observed_in_reviews"}
]}
```

- `kind`: baseline, dataset, metric, ablation, theory, reproducibility, scale, other.
- `applies_when`: the kind of claim or setting the expectation is about. Audits use it to decide whether the expectation applies to a candidate, so write it narrowly: "an empirical return-improvement claim on DMC", not "any paper".
- `evidence.kind`: `paper_practice` (a read paper does it; `ref` is its arxiv_id or a sig_id), `paper_limitation` (the authors concede its absence weakens the paper), `review` (`ref` is a `review_id` in `reviews.jsonl`, and `quote` is the sentence from that review).
- `strength` (the validator checks it against the evidence): `observed_in_reviews` needs at least one resolvable review; `common_practice` needs evidence from ≥ 3 read papers; otherwise `single_source`. An expectation is a question audits ask of candidates it applies to, not a requirement for every idea; a candidate may challenge it with evidence.

## Output 2: `profile/lexicon.json`

```json
{"cards": {"K01-latent-rollout-pruning": {"signature_terms": ["value uncertainty rollout pruning"], "alias_terms": ["selective model-based planning"]}},
 "collision_windows": {"signature_months": 10, "alias_months": 48, "basis": "why these windows fit this field's pace"}}
```

- Every card gets `signature_terms` (this field's own 3–7-word names for the operation) and `alias_terms` (what **other communities** call the same mechanism — the renamed-ancestor channel from ResearchStudio's collision check).
- Windows: ResearchStudio fixed 10 and 48 months. Set them from `timeline.json`: a field where most member papers are recent moves fast (shorter signature window catches contemporaneous scoops); a slow field needs a longer one. State the basis.

## Output 3: `profile/crossmap.json`

```json
{"maps": [
  {"source_domain": "operations research", "source_refs": ["2303.07777#s1"],
   "mapping": {"object": "job queue → imagined rollout set", "operation": "priority pruning → value-uncertainty pruning", "condition": "rollouts are independent and value estimates are calibrated"},
   "breaks_if": "rollout values are correlated across branches", "status": "proposed"}
]}
```

- Only mappings backed by a read cross-domain signature (`source_refs` are `sig_id`s). The brief's mappings that found no support stay out, and are worth a note in `breaks_if` of a related map or in a lesson.
- `status`: `proposed` (plausible from reading), `checked` (you verified the condition holds in target-domain readings), `refuted` (readings show it breaks). Keep refuted maps; they stop later steps from re-proposing them.

## Never

- Invent expectations without evidence refs, or claim `observed_in_reviews` without a `reviews.jsonl` row and its quote.
- Copy generic advice ("compare with strong baselines") — name the baseline.
