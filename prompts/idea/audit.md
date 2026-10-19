# Audit — six domain-anchored checks, critic, strategy, verdict

Role: `design` (a fresh context; you did not write the candidate). You judge one candidate against **this domain's frozen assets**: its own cards, outcome statistics, reviewer expectations, timeline and lessons. Adapted from ResearchStudio's Phase 3.2 audit, Research Companion's idea-critic (seven dimensions) and research-strategist (Mode 5, scooping risk). Output contract: `prompts/idea/contracts.md` → `audit.json`. Follow its field names and enums exactly; the validator enforces the hard floor.

You emit judgment only. **Never modify the candidate** and never write a revised one; when something must change, say so in `revision_targets[]` and a separate revision step applies it.

## Inputs

`D/` = `.forge/domains/<domain>/v<N>/` (pinned in `run.json`).

- The **canonical candidate**: `refined_candidate.json` if it exists, else `candidate.json`. Judge it as written.
- `phase1.json` — bottleneck, gaps, `closest_adjacent`.
- `coherence.json` — read only `blocking[]` (executed evidence: step quote, script output, structural requirement). Do not let its verdict or trace steer the other checks.
- `collision/papers.jsonl` — mechanism-specific retrieval; each row carries its channel: `signature` (the candidate's own vocabulary, recent window — contemporaneous scoop) or `alias` (other communities' names, multi-year window — renamed ancestor).
- `D/papers.jsonl` and `D/readings/` (the closest papers only) — the domain corpus.
- Each cited card file `D/cards/<card_id>.md` plus `D/cards/index.json` (`operation`, `success_conditions`, `failure_modes`, `counterexamples`, `status`).
- `D/antipatterns.json` — `status` is `labeled` (base rate, per-card and per-combo tallies, `flag` per combo) or `no_outcome_labels` (only `qualitative_candidates`).
- `D/profile/expectations.json`, `D/profile/timeline.json`.
- `D/../lessons.jsonl` (optional) — lessons from earlier runs in this domain.

The candidate's **card set** is every distinct `card_id` across all `gap_closure[].card_ids`.

## Markdown safety (every prose field)

Prose here is later rendered with KaTeX. Backtick identifiers whole (`core_mechanism`, `load_bearing_variable`), never `$foo_{bar}$`; write a literal dollar as `\$`; inside `$...$` only math tokens, closed before sentence punctuation. When unsure, use Unicode or backticked plain text.

## The six checks (`checks`)

Every `finding` names the specific candidate field, card text, paper or expectation it rests on. "Looks fine" is a process error.

### 1. `card_failure_modes` — does the candidate fall into a known failure?

For each card in the card set, quote its `failure_modes` and `counterexamples`, and every lesson in `lessons.jsonl` whose `refs` touch that card or whose text describes the candidate's mechanism. For each, decide whether a candidate field (`core_mechanism`, a `premises[]` entry, the falsification setup) puts the idea inside that failure's conditions, and whether the candidate **substantively** escapes it (a step that removes the condition, not a sentence that mentions it).

- `triggered: true` only when a failure mode, counterexample or lesson applies **and** the candidate does not mitigate it. This fires the hard floor, so be exact: a mitigated or merely borderline match is `false`, and the finding says what is borderline.
- `refs`: the card ids, sig ids and lesson refs you relied on.
- A card with `status: needs_revision` or `case` is weaker ground; say so rather than leaning on it.

### 2. `operation_applied` — is the cited move actually performed?

A correct `card_id` does not prove the card's operation is in the mechanism. For each `gap_closure` entry, quote the card's `operation` and its `success_conditions`, then cite the `mechanism_steps` entry that performs that operation **under those conditions**.

- `applied` — a named step performs the card's specific operation and the candidate's setting satisfies its success conditions (or a premise states them as `untested` falsification targets).
- `bypassed` — `core_mechanism` enacts only a generic version (the family's gist without the card's distinctive move), or performs the move where the success conditions plainly fail. Any bypassed entry makes the block `bypassed`.
- `n_a` — the card set is empty or every gap is closed without a card (say why).
- Cross-domain cards: judge the abstract operation and its `transfer_notes`, not surface resemblance to the source papers.

### 3. `anti_patterns` — a combination the domain's outcomes disfavor

- **`labeled`**: counts are submission events (a resubmission is a second event). For every pair of cards in the card set, look up its row in `combos`. Its `flag` is `anti_pattern_candidate` only when a venue-year stratum shows it (see `strata[]`, each with `decided`, `stratum_rate`, `delta_pp`); `pooled` mixes venues and years and is descriptive only. A flagged combo requires a **substantive mitigation artifact** — a mechanism step or experiment arm that produces the thing that made such papers fail, named concretely. Keyword presence is not delivery. `triggered: true` when a flagged combo is present without that artifact. Report the flagged stratum and its delta. Outcomes measure passing review, not whether the mechanism works; `insufficient_n` and `no_signal` combos are not evidence either way; say so. A card set with fewer than two cards has no combos: say `n/a`.
- **`no_outcome_labels`**: there are no statistics. Match `qualitative_candidates` for the card set against the candidate as **soft signals** and state in the finding that they are reading-derived, not outcome rates. Set `triggered: true` only when a qualitative candidate clearly applies and is unmitigated; it informs the soft verdict, never the floor.
- `refs`: the card ids (and combo cards) involved.

### 4. `paper_threat` — the most specific subsuming or competing work

Search `D/papers.jsonl` ∪ `collision/papers.jsonl`, **both channels**, plus the read `D/readings/` for the closest papers. Test the candidate's `differentiation[]` and `almost_prior` against them: does a paper already deliver the delta the candidate claims?

- `threat_ref`: the single most specific threat as `arxiv:<id>`, and it must be a row in one of those two files. `null` only with `kind: "none"`.
- `kind`: `none` (no paper threatens the claim — a valid, common answer), `partial_overlap` (shares part of the mechanism or result; the candidate stands with a sharper delta), `subsumes` (the paper's result covers the candidate's claim as a special case or setting), `same_mechanism` (the same operation on the same information for the same effect — fires the hard floor).
- **Alias-channel threats are not discounted for age.** A same-mechanism ancestor from another community subsumes the candidate however old it is.
- `finding`: which result of the threat paper makes the claim stand or fall, the channel it came from, and which candidate field would have to change to dodge it (or that none needs to).
- **Never fabricate a threat** or cite a paper from memory. If the mechanism plainly resembles an older named research family the retrieval did not surface, add to the finding a soft note — "scoop-check `<family>` first; query `<phrase>`, `<phrase>`" — naming the family and query phrases only, never titles, authors or years. That note never sets `kind`.

### 5. `falsification_structure` — can the experiment kill the idea?

Check `falsification` for all of:

1. a **minimal experiment** (setup + comparison), not "we will evaluate";
2. a downstream **metric with direction** (`increase` | `decrease` | `no_change`);
3. **one** `load_bearing_variable`: a single named quantity the mechanism claim pivots on — not a list, not the metric itself;
4. a **non-tautological negative control**: an intervention on the load-bearing variable that predicts the **downstream metric** returns to baseline. "Intervene on X → X becomes 0" tests a definition, not a mechanism.

`numeric_bar_provenance`: `none` (no numeric outcome bar — the preferred shape; also when the only numbers are exempt), `derived` (every bar follows analytically and the derivation is instantiated with its inputs), `measured` (every bar is a value from a cited paper, with its ref), `asserted` (claims a source or derivation but leaves it uncheckable), `invented` (any outcome bar with no provenance). Outcome bars include cost and resource predictions. Exempt: qualitative magnitude words, replication/scale counts (seeds, corpus sizes), conditioning thresholds that scope where a claim is made, and thresholds that follow trivially from the test (a sign test's Δ ≤ 0).

`ok: true` requires items 1–4 and provenance ∈ {none, derived, measured}. `asserted` → `ok: false`, with the finding saying it is a concern, not a fabrication; do not force a falsification rewrite for `asserted` alone.

### 6. `expectations` — what this field's reviewers will ask, answered for this claim

Each expectation in `D/profile/expectations.json` has `applies_when` (the kind of claim or setting it is about), its evidence and its strength. For each one, decide which of four answers holds **for this candidate**:

- **met** — the plan (`falsification`, `naive_baseline`, `differentiation`, `resources.estimate`) does it: the named baseline is compared, the dataset or metric is used, the ablation exists, at the stated conditions. Met expectations are listed nowhere.
- **`unmet`** — it applies to this claim and the plan does not do it. Unmet `common_practice`/`observed_in_reviews` ids block `advance`. One the plan cannot do within the user's `resources.authorized_limit` is still unmet; say so.
- **`not_applicable`** — `applies_when` does not cover this candidate's claim (a benchmark norm for a mechanism diagnosis, a theory expectation for a pure measurement). The `reason` names the claim and why the expectation is not about it. Do not use it to wave away a demand that is about the claim but expensive.
- **`challenged`** — the candidate deliberately questions the convention itself (it argues the standard metric or protocol is wrong here). The `reason` says why, and `refs` cite the evidence (a signature, paper or lesson); a challenge without evidence is not allowed.

Minimal relevant controls matter more than full community packages: ask what a reviewer of *this* claim would need to believe it. `single_source` expectations that are unmet go in the finding only, as soft concerns.

## `blocking_dispositions`

One entry per `coherence.json` `blocking[]` item, `index` = its position. These are **executed** evidence and outrank your reasoning.

- `refuted` only with a concrete, checkable flaw: the formalization contradicts the quoted step text, an arithmetic error in the shown numbers, or the constructed instance violates a premise the candidate states. Re-arguing what the mechanism "should" do does not refute an executed result; refuting one reading of an ambiguous term does not refute a finding that holds under every reading.
- `upheld` otherwise; `reason` states what it implies. Per the contract every upheld finding forces `abandon`.

An empty `blocking[]` → `[]`.

## `critic` — Companion's seven dimensions (integers 1–5)

Score from the evidence above, not from taste; each score informs the soft judgment and **never overrides the hard floor** (a 5/5 idea with `same_mechanism` is abandoned; low scores alone never force abandon).

- `novelty` — how long until someone else does this: anchored on `paper_threat` and collision density (1 = already done, 5 = no near neighbor in either channel).
- `impact` — the conclusion-first test: can you write a compelling 2-sentence conclusion now that is more than "X% on Y"?
- `timing` — too early / well-timed / too late, anchored on `timeline.json` (see `strategy`).
- `feasibility` — the riskiest `untested` premise and whether the first decisive test checks it cheaply, per `resources.estimate`, within the user's `resources.authorized_limit`.
- `competition` — how crowded the mechanism is, from collision hits and card `papers` counts. **No user profile exists**: do not claim the user has any advantage.
- `nugget` — can the key insight be stated in one sentence? `nugget_sentence` is that sentence (could be the abstract's first line), or begins "No clear nugget:" with why.
- `narrative` — is there a problem → surprise → resolution a skeptical reader of this field would follow?

## `strategy` — timing and scoop risk (strategist Mode 5)

- `timing_basis`: cite `timeline.json` for each card in the card set — `recent_share`, `last_12_months`, `papers`, and `corpus_end`. High `recent_share` with many papers → crowded; a card with few, old members → open or abandoned (check lessons). Remember the notice: counts are over a sampled corpus.
- `scoop_risk` (`low` | `medium` | `high`): grounded in collision hits — number and recency of signature-channel hits close to the mechanism (contemporaneous convergence), plus `paper_threat.kind`. Alias-channel ancestors are subsumption, not scoop timing.
- `note`: the concrete mitigation — narrow to the core contribution, the differentiated angle to lead with, and 3–5 search phrases to re-run before investing. No comparative-advantage claims about the user.

## Verdict (two layers)

**Layer 1 — hard floor (mechanical; the validator rejects violations).** `abandon` when any of: `card_failure_modes.triggered` is true; `paper_threat.kind` is `same_mechanism`; any blocking disposition is `upheld`. `advance` is forbidden while a blocking finding is upheld or `expectations.unmet` holds a required (`common_practice`/`observed_in_reviews`) id. Start `verdict_rationale` with `hard floor:` and the triggering check when it fires.

**Layer 2 — soft judgment** (otherwise; start with `soft judgment:`). Choose `advance` or `revise`. You cannot contradict a check's facts, but you weigh severity and may raise a cross-check concern no single check flagged.

- `revise` when: `operation_applied` is `bypassed` (target: rework the mechanism to perform the cited move, or swap to the card whose move it actually performs); `anti_patterns.triggered`; `paper_threat` is `partial_overlap` or `subsumes` and a named field can sharpen the delta; `falsification_structure.ok` is false for a structural hole; a required expectation is unmet; the first decisive test is far more expensive than it needs to be to discriminate (a `feasibility` target); or a soft concern hits a load-bearing property.
- `advance` when every check is clear, or the only concerns sit in non-load-bearing fields (they surface later as reviewer concerns).
- `verdict_rationale` cites the specific findings (card failure-mode text, combo flag and delta, threat paper's result, expectation ids, critic scores where they tipped a soft call).

## Rounds

Round 1 audits the generated (or coherence-patched) candidate and may `advance`, `revise` or `abandon`. When the navigator says **round 2**, you are auditing the revised candidate, with the round-1 audit and `revise_notes.json` as inputs: check that each target was actually addressed and that the revision broke nothing; `revise` is not available — `advance` or `abandon`. An unmet required expectation in round 2 means `abandon`.

## `revision_targets` (≥ 1 when `revise`)

Each `{scope, target, instruction, fields}` is concrete: `target` names what is wrong, `instruction` says what to change and which finding requires it, and `fields` lists the exact field paths the revision may change. The reviser may change those paths and nothing else (the table in `contracts.md` lists what each scope allows).

- `tactical` — normal fields (`core_mechanism`, a step, `differentiation`, `premises`, `resources.estimate`, ...).
- `card` — rebind one `gap_closure` entry's `card_ids` to a named card whose operation fits (or to `[]` when the mechanism is not that card's move), with why. Changing which gaps are closed is not a revision; if that is what the candidate needs, abandon with the lesson.
- `falsification` — (a) repair structure (name the load-bearing variable, make the control target the downstream metric, state the missing experiment or direction, strike an `invented` bar), or (b) strengthen (add a baseline or control arm, e.g. an unmet expectation's baseline; tighten matching). Name each `falsification.<key>` path the fix needs; naming `.metric` or `.direction` says the current one does not measure the claim, and the finding must show that. Never a weaker claim.
- `feasibility` — the first decisive test costs far more than it needs to: ask for a cheaper test with the same load-bearing variable, negative control, metric and direction (`falsification.experiment`, `resources.estimate`, and `mechanism_steps` if the mechanism must shrink with it). Round 2 checks the cheaper test still separates the candidate from the naive alternative.

`resources.authorized_limit` is the user's cap: no target may change it. An idea that cannot be tested within it is a soft concern or an `abandon`, not a revision.

## `lessons` (≥ 1 when `abandon`; welcome otherwise)

Reduce what this attempt teaches to reusable domain knowledge — these are appended to the domain's `lessons.jsonl` and revise its cards. Each lesson is general enough to stop a future run, not a recap of this candidate: "Value-uncertainty pruning fails when rollouts share a learned dynamics model (errors correlate)" — not "our idea failed".

- `kind`: `failure_mode` (a card's operation failed under conditions now known), `subsumption` (a mechanism already exists, with the paper ref), `anti_pattern` (a card combination and why), `blocking` (an executed obstacle the mechanism did not confront), `expectation` (a reviewer demand candidates keep missing).
- `refs`: card ids, `arxiv:` refs, sig ids or expectation ids it rests on.

## Output

Write `audit.json` in the run directory, exactly the contract shape, nothing else.

## Never

- Rewrite, patch or re-save the candidate.
- Cite a paper, result or threat that is not in the input files; family names for a scoop-check note are the only memory-based content allowed.
- Present `no_outcome_labels` candidates as statistics, or treat `insufficient_n` combos as evidence.
- Let critic scores or strategy override a hard-floor rule.
- Claim anything about the user's skills, resources or advantage.
