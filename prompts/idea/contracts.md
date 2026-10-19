# Idea-run file contracts

Every idea run lives in `<project>/.forge/runs/<run>/` and is pinned to one frozen domain version (`run.json`: `{run, domain, version, question, created, mode, budget}`; `budget` is the cap the user authorized, verbatim, or `not specified`). `D` below is that frozen directory, `.forge/domains/<domain>/v<N>/`. Validators in `forge/ideas.py` enforce these shapes; a step's FIX lines quote their errors.

## Domain refs an idea may cite

- `arxiv:<id>` — a paper in `D/papers.jsonl` or in `collision/papers.jsonl`.
- `<id>#s<k>` — a signature in `D/readings/*.json`.
- `K..-slug` — a card id in `D/cards/index.json`.
- `E..` — an expectation id in `D/profile/expectations.json`.
- `crossmap[<i>]` — entry `i` of `D/profile/crossmap.json`.

**Cited is not read.** Any of these may be cited as context. A premise marked `grounded` may rest only on material read in full: a `verified: fulltext` signature, an `arxiv:` paper that has one, or a card with status `candidate_pattern`/`checked_for_scope`. An abstract-only reading, an unread corpus paper or a collision hit is a lead; a premise resting on it is `untested`.

**Acceptance.** After each step the host runs the step's `run_after` command, which records provenance and stamps the outputs with the content hashes of the step's `deps`. If a dep later changes, the output is stale and its step returns.

## phase1.json — bottleneck (role design)

```json
{"state": "proceed",
 "bottleneck_statement": "...", "refs": ["arxiv:2501.00001", "2502.00002#s1"],
 "closest_adjacent": [{"ref": "arxiv:2501.00001", "residue": "what it leaves unsolved"}],
 "gaps": [{"gap_id": "G1", "text": "...", "stakes": "who pays and how", "refs": ["2501.00001#s1"]}],
 "do_not_generate_reason": null}
```
`state` is `proceed` or `do_not_generate` (then `do_not_generate_reason` is a non-empty string and gaps may be empty). `refs` ≥ 2 distinct; gaps 1–4.

## candidate.json — generation (role design); also `refined_candidate.json`, `revised_candidate.json`

```json
{"title": "...", "hook": "...",
 "gap_closure": [{"gap_id": "G1", "card_ids": ["K01-..."], "how_closed": "..."}],
 "core_mechanism": "...", "mechanism_steps": ["..."],
 "premises": [{"text": "...", "status": "grounded", "refs": ["2501.00001#s1"]}, {"text": "...", "status": "untested", "refs": []}],
 "naive_baseline": {"naive": "...", "why_insufficient": "...", "branch": "false_premise"},
 "falsification": {"experiment": "...", "metric": "...", "direction": "increase", "load_bearing_variable": "...", "negative_control": "..."},
 "resources": {"authorized_limit": "<run.json budget, verbatim>", "estimate": "your estimate: the first decisive test, then the full campaign"},
 "differentiation": [{"ref": "arxiv:2501.00001", "delta": "substantive difference"}],
 "almost_prior": {"ref": "arxiv:2501.00001", "missed_step": "..."},
 "signature_terms": ["3-7 word phrase"], "alias_terms": ["other communities' name"],
 "crossmap_used": [0],
 "alternatives_considered": [{"title": "...", "why_not_chosen": "..."}]}
```
- `gap_closure[].card_ids`: zero, one or several card ids. Cards are material, not a template: an empty list is a mechanism no card describes; say where it comes from in `how_closed`.
- `premises[].status`: `grounded` (refs non-empty, all read in full; see above) or `untested` (a falsification target).
- `naive_baseline.branch`: `false_premise` | `naive_suffices` | `disbelieved`.
- `falsification.direction`: `increase` | `decrease` | `no_change`.
- `signature_terms` 2–8, `alias_terms` 1–8; `alternatives_considered` ≥ 2 (Companion's diverge step, kept visible).
- `resources.authorized_limit` is copied from `run.json` and never changes: only the user raises a cap. `resources.estimate` is yours and may be revised (e.g. a cheaper test).
- `falsification` changes only through an audit revision target that names the exact `falsification.<key>` paths.

## coherence.json — coherence gate (role review, fresh context)

```json
{"verdict": "pass", "trace": "dataflow, dry-run script and output, degenerate probes",
 "claims": [{"claim": "...", "grade": "established"}],
 "naive_comparison": "confronts_obstacle",
 "blocking": [{"finding": "...", "evidence": "script output / step quote", "structural_requirement": "..."}]}
```
`verdict`: `pass` | `patched` (then `refined_candidate.json` exists and is a full candidate). `grade`: established | conditional | overclaim | empirical. `naive_comparison`: confronts_obstacle | equivalent_to_naive | n_a.

## collision/papers.jsonl — written by `forge run collide` (operator)

## audit.json — audit (role design)

```json
{"checks": {
   "card_failure_modes": {"finding": "...", "triggered": false, "refs": ["K01-..."]},
   "operation_applied": {"finding": "...", "status": "applied", "refs": ["K01-..."]},
   "anti_patterns": {"finding": "...", "triggered": false, "refs": []},
   "paper_threat": {"finding": "...", "threat_ref": "arxiv:2501.00001", "kind": "partial_overlap", "parametric_family_concern": "optional: an un-retrieved mechanism family to scoop-check"},
   "falsification_structure": {"finding": "...", "ok": true, "numeric_bar_provenance": "none"},
   "expectations": {"finding": "...", "unmet": ["E01"],
                    "not_applicable": [{"id": "E02", "reason": "why this expectation is not about this candidate's claim"}],
                    "challenged": [{"id": "E03", "reason": "why the convention is wrong for this claim", "refs": ["2501.00001#s1"]}]}},
 "blocking_dispositions": [{"index": 0, "disposition": "upheld", "reason": "..."}],
 "critic": {"novelty": 3, "impact": 4, "timing": 3, "feasibility": 4, "competition": 3, "nugget": 4, "narrative": 3, "nugget_sentence": "..."},
 "strategy": {"timing_basis": "timeline recent_share ...", "scoop_risk": "medium", "note": "..."},
 "verdict": "revise", "verdict_rationale": "cites the checks",
 "revision_targets": [{"scope": "tactical", "target": "...", "instruction": "...", "fields": ["differentiation"]}],
 "lessons": [{"kind": "failure_mode", "text": "...", "refs": ["K01-..."]}]}
```
- `operation_applied.status`: applied | bypassed | n_a. `paper_threat.kind`: none | partial_overlap | subsumes | same_mechanism (`threat_ref` null only for none).
- `numeric_bar_provenance`: none | derived | measured | asserted | invented.
- `critic` scores are integers 1–5 (Companion's seven dimensions). `strategy.scoop_risk`: low | medium | high.
- `verdict`: advance | revise | abandon. **Hard floor** (the validator enforces): `abandon` is required when a card failure mode is triggered and unmitigated, `paper_threat.kind` is `same_mechanism`, or a blocking finding is upheld; `advance` is forbidden while any blocking finding is upheld or `expectations.unmet` contains a `common_practice`/`observed_in_reviews` expectation.
- Expectations: every required expectation is met (listed nowhere), `unmet`, `not_applicable` (with a reason tied to this claim) or `challenged` (with a reason and evidence refs). An id appears in at most one list.
- `revision_targets[]` (≥1 when `revise`): `scope` and the exact `fields` (field paths) the revision may change, each allowed by the scope:

| scope | allowed field paths |
|---|---|
| `tactical` | `title`, `hook`, `core_mechanism`, `mechanism_steps`, `gap_closure.how_closed`, `premises`, `naive_baseline`, `differentiation`, `almost_prior`, `signature_terms`, `alias_terms`, `crossmap_used`, `alternatives_considered`, `resources.estimate` |
| `card` | `gap_closure` (rebinding cards, same gaps), `gap_closure.how_closed`, `core_mechanism`, `mechanism_steps`, `premises`, `signature_terms`, `alias_terms`, `crossmap_used` |
| `falsification` | `falsification.experiment`, `.metric`, `.direction`, `.load_bearing_variable`, `.negative_control`, `resources.estimate` |
| `feasibility` | `falsification.experiment`, `resources.estimate`, `mechanism_steps` (a cheaper test with the same variable, control, metric and direction) |

`resources.authorized_limit` is in no scope.
- `lessons` ≥ 1 when `abandon`; `kind`: failure_mode | subsumption | anti_pattern | blocking | expectation.

## revise_notes.json — written with revised_candidate.json

```json
{"applied": [{"target_index": 0, "change": "what changed, or 'skipped: why'", "fields": ["falsification.negative_control"]}]}
```
One entry per revision target (`target_index` 0..n-1). `fields` lists the field paths this entry changed (empty when skipped); each must be among its target's `fields`, every field that changed must be claimed by some entry, and no entry may claim a field that did not change. The set of closed gaps never changes in a revision.

## Revision flow

A valid `revised_candidate.json` is promoted (`audit.json` → `audit_round1.json`), searched for collisions again if its terms changed, and audited a second time; round 2 allows only `advance` or `abandon`. There is no separate falsification re-audit.

## idea_card.json — expansion (role review); rendered to `idea_card.md`

```json
{"title": "...", "hook": "...", "abstract_draft": "...",
 "motivation": {"why_prior_stopped": "...", "stakes": "..."},
 "core_claim": "...", "sub_claims": ["..."], "method_flow": ["..."], "key_equations": ["..."],
 "falsification": {...copied unchanged from the final candidate...}, "resources": {...copied...},
 "almost_prior": {...}, "differentiation": [...],
 "expectation_coverage": [{"expectation_id": "E01", "status": "met", "how": "..."}],
 "reviewer_concerns": [{"concern": "...", "response": "...", "source": "audit"}],
 "feasibility": "...", "kill_switch": {"condition": "...", "action": "..."},
 "domain_landscape": {"cards": ["K01-..."], "timing": "..."},
 "plain_summary": "..."}
```
- `expectation_coverage` lists **every** domain expectation with strength `common_practice` or `observed_in_reviews`; `status`: met | partial | gap | not_applicable | challenged (a `partial`, `gap` or `challenged` row needs a reviewer concern with source `expectation`).
- `domain_landscape.cards` may be empty (a mechanism no card describes).
- `reviewer_concerns[].source`: audit | coherence | expectation | collision.
- `title`, `hook`, `almost_prior` and `differentiation` are copied from the final candidate; `single_source` expectations may be listed but are optional.

## decision.json — gate (role gate: model in auto/web, human in hitl)

```json
{"decision": "pursue", "rationale": "...", "revisit_conditions": "...", "decided_by": "model"}
```
`decision`: pursue | park | kill. `decided_by`: model | human.
