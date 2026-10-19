# I2 — Select and generate one candidate

Role: `design`. In one step you choose which gaps to close, find a mechanism (using this domain's cards as material where they help), diverge before committing, and write **one** concrete, buildable, falsifiable candidate. The candidate must be substantively new relative to `phase1.json`'s closest adjacent work and must read as one coordinated paper.

`D/` is the frozen domain version, `.forge/domains/<domain>/v<N>/`.

## Inputs

- `phase1.json`: the bottleneck, `closest_adjacent` (the first entry is the anchor paper) and `gaps`.
- `D/cards/index.json` and only the card files relevant to the gaps. A card's `operation` is the move. Its `success_conditions` must hold in your setting, and its `failure_modes`/`counterexamples` are what the audit will check against you. A `case` card rests on one paper and a `needs_revision` card is undermined, so lean on them only with a stated premise.
- `D/profile/crossmap.json`: cross-domain maps (`mapping.object/operation/condition`, `breaks_if`, `status`).
- `D/profile/expectations.json`: what reviewers here demand (named baselines, datasets, metrics, ablations).
- `D/antipatterns.json`: card combinations flagged `anti_pattern_candidate` (labeled domains) or reading-derived `qualitative_candidates` (`no_outcome_labels`).
- `D/../lessons.jsonl` (optional): failure modes, subsumptions and dead ends from earlier runs. Treat them as constraints.
- `D/papers.jsonl` and `D/readings/*.json`: read **only** the closest-adjacent papers' rows and readings, to write differentiation from what their method actually does.
- Sibling runs' `candidate.json` files (optional): candidates other runs in this domain already produced.
- `attempts/` (optional, retry mode): archived attempts of this run, each with its `candidate.json` and `audit.json` (and `coherence.json` when it reached the gate).
- `run.json`: `question`, and `budget`, the cap the user authorized (verbatim, or `not specified`). If the question states data or an excluded solution shape, honor it.

## Procedure

### 1. Select gaps

- **Anchor gap**: the gap whose closure is most load-bearing for the bottleneck and whose demanded deliverable matches the contribution the question wants. Read the gap's verb: "keep / produce / make X survive" demands a construction; "test whether / isolate" demands an analysis or diagnostic. Additive and subtractive gaps compete equally.
- **Siblings (0–2) must earn a seat.** Every gap descends from the same bottleneck, so "attacks the same question" is never enough. A sibling joins only if it passes the **removal test**: without it, the anchor's falsification weakens or becomes unrunnable, an obvious reviewer objection opens, or the anchor's claim loses verifiability. If the paper is merely smaller but still sound without the sibling, leave it out. A sibling that needs its own new machinery is a second paper. Anchor-only is a normal outcome.

### 2. Find the mechanism (cards are material, not a template)

A gap may be closed by one deep change, by a composition of moves, by removing an unnecessary mechanism, or by a mechanism no card describes. None of these is better by count: judge the mechanism by what it changes, the conditions it needs, the most naive alternative it must beat, and the prediction that would tell it apart. Do not add a second card to look deeper, and do not attach a card a mechanism does not actually use.

Use the cards for what they know: a card's `operation` is a move the field already has, its `success_conditions` must hold in your setting if you use it, and its `failure_modes`/`counterexamples` are what the audit will check you against. When cards help, realize them one of these ways:

- **Chain**: card A's operation produces a named intermediate object O, and card B's operation consumes O to produce the anchor's deliverable. If you cannot name O, the chain is decorative; drop it.
- **Earned sibling**: a second gap, admitted by the removal test, closed by a different move.
- **Single move**: one card's operation, applied where it has not been, is the whole idea.
- **No card**: the mechanism is new to this domain (`card_ids: []`). Say in `how_closed` where it comes from (a crossmap entry, a subtractive gap, a construction) and why no card's move already does it.

Pick moves by whether they actually produce what closes the gap ("A's move on gap G closes G because Z"), not by shared words. Then check:

- **Card conditions**: every success condition you rely on is a premise (grounded, or untested and falsified). Every failure mode whose trigger is present in your setting is either mitigated by a mechanism step or makes you drop the card.
- **Anti-patterns**: do not compose a card pair `D/antipatterns.json` flags (within a venue-year stratum) unless the mechanism removes the cause; say how in `how_closed`.
- **No regression**: if the mechanism's load-bearing artifact reduces to an older, superseded method (a running-average baseline, a target network, a curriculum, ...), it is a regression even if it closes the gap. Redesign it, or narrow the claim to the genuinely new part. Name the older method you avoided in `alternatives_considered`. Parametric knowledge informs this check; it is never cited.

### 3. Diverge before committing

Before writing the candidate, generate at least three genuinely different directions, not parameter variants:

- **In-domain**: a move or composition from step 2.
- **Cross-field**: a `crossmap.json` map whose source field solved a structurally identical problem under another name. Prefer `checked` maps. A `proposed` map's `mapping.condition` becomes a premise, and its `breaks_if` must be shown not to hold or be made the falsification target. A `refuted` map is never re-proposed, not even reworded. Record used maps by index in `crossmap_used`.
- **Strategic ignorance**: challenge one assumption the field takes for granted. Often this is the subtractive gap. Ask what a smart outsider would find suspicious about how the closest papers set the problem up.
- **Alternative framing**: restate the problem so the solution becomes obvious, or so the "obvious" solution is shown wrong.

Choose the direction that closes the anchor gap, survives the naive-baseline audit, passes the conclusion-first test and fits the budget. Record at least two of the others in `alternatives_considered`, each with a concrete `why_not_chosen` (it regresses to a named method, a card failure mode fires, a refuted map, it needs a resource that does not exist, the naive version suffices).

### 4. Self-checks before writing

- **Conclusion first** (Carlini): write, for yourself, the conclusion sentence of the finished paper: "We showed that X, which means Y for Z." If you cannot write it, or Y is not something a reader of the closest papers would care about, the candidate is not ready; go back to step 3. The `hook` must follow from that sentence.
- **Naive-baseline audit**: write the most obvious version of the anchor mechanism as one runnable sentence in `naive_baseline.naive`, then pick exactly one honest `branch`:
  - `false_premise`: the naive version silently relies on a premise that is false here (name it; often the observation-model premise). The mechanism must confront that failure head-on, and that confrontation is the contribution. If the fix is a textbook tool from another field (off-policy evaluation, missing-data methods, survival analysis, experimental design, ...), name the domain-specific structure that keeps this instance from being solved by the textbook (a budget, a coupling, adaptivity, a scale regime) and make that structure part of the mechanism. Otherwise say plainly that the contribution is application-grade.
  - `naive_suffices`: the naive version works and the field knows it. That is an incremental signal: redesign toward a real obstacle, or state the increment honestly in `why_insufficient`. Never paper over it.
  - `disbelieved`: the naive version works but the field believes it does not. Name the evidence for that belief (a ref); this is a minimalism contribution.
- **Sibling dedup** (soft, when sibling candidates are passed): do not steer toward a mechanism family a sibling already produced unless the question demands it. If it does, state the delta from the sibling in one sentence of `core_mechanism`. Siblings are never cited as literature and never veto on their own.

## Output: `candidate.json`

Shape, field names and enums exactly as in `contracts.md` (candidate.json section). Abbreviated example:

```json
{
 "title": "Keeping Rare Branches Alive: Return-Tail Pruning for Sparse-Reward Latent Planning",
 "hook": "Pruning by value uncertainty discards the branches that matter most once reward is sparse; pruning by an estimate of the return's upper tail keeps them at the same rollout budget.",
 "gap_closure": [
   {"gap_id": "G1", "card_ids": ["K01-latent-rollout-pruning", "K04-quantile-return-heads"], "how_closed": "K04's quantile head yields a per-branch tail estimate (object O); K01's pruning consumes O instead of disagreement"}
 ],
 "core_mechanism": "...",
 "mechanism_steps": ["1. ...", "2. ..."],
 "premises": [
   {"text": "observation-model: rollouts are sampled on-policy from the latent model, so tail estimates see only branches the policy already visits", "status": "untested", "refs": []},
   {"text": "estimand: P(return >= R_tau | branch) under the latent model's rollout distribution", "status": "grounded", "refs": ["2501.01234#s1"]}
 ],
 "naive_baseline": {
   "naive": "prune by ensemble disagreement with a lower threshold",
   "why_insufficient": "disagreement collapses with value calibration under sparse reward (2501.01234#s1)",
   "branch": "false_premise"
 },
 "falsification": {
   "experiment": "...",
   "metric": "success rate on DMC sparse tasks at equal rollout budget",
   "direction": "increase",
   "load_bearing_variable": "per-branch tail estimate",
   "negative_control": "replace the tail estimate with a permuted one; success rate must fall to the disagreement baseline"
 },
 "resources": {"authorized_limit": "not specified", "estimate": "first decisive test: 2 DMC sparse tasks x 3 seeds, about 3 GPU-days; full campaign about 30 GPU-days (80GB-class), $0 API"},
 "differentiation": [
   {"ref": "arxiv:2501.01234", "delta": "they prune on disagreement; we derive a pruning signal from the return tail that stays informative where their Sec 4.3 shows disagreement fails"}
 ],
 "almost_prior": {
   "ref": "arxiv:2406.05555",
   "missed_step": "they had distributional returns but used them only to re-weight, never to decide which branches to expand"
 },
 "signature_terms": ["return tail rollout pruning", "sparse reward latent planning"],
 "alias_terms": ["optimistic tree search pruning", "upper confidence branch elimination"],
 "crossmap_used": [],
 "alternatives_considered": [
   {"title": "...", "why_not_chosen": "..."},
   {"title": "...", "why_not_chosen": "..."}
 ]
}
```

## Rules

- **Mechanism computable from the text.** `core_mechanism` walks the chain for each closed gap (the move, from a card or new → applied to this gap → concrete artifact → why it closes the gap) and defines every quantity: what it is and where it comes from (model readout, computed, external). It fixes or gives a selection rule for every free index, and names any weight that bridges quantities in different units. `mechanism_steps` (5–12) are code-pathway steps with inputs and outputs. For any step that intervenes on a model or its inference, state how the change reaches the downstream task output, not only the intermediate value.
- **Premises ledger.** Every load-bearing empirical or domain premise is one entry.
  - `grounded` needs refs to material read in full (a `verified: fulltext` signature, a paper that has one, a `candidate_pattern` card); the validator refuses an abstract-only, unread or collision-only ref. `untested` marks a bet and makes it a falsification target; the load-bearing variable should pivot on an untested premise.
  - **Observation model**: when the mechanism consumes sampled or observed data, at least one premise starts with `observation-model:` and says how inputs are sampled and whether that is unbiased and complete here. Censoring, selection bias, non-iid sampling, leakage and self-preference live here; it is where naive mechanisms hide their assumptions. With no sampled inputs, write `observation-model: n/a (no sampled inputs)`. Never invent one.
  - **Estimand**: when the mechanism estimates or measures any quantity, one premise starts with `estimand:` and gives the exact target quantity and the population or process it is defined over, so the coherence gate can check that the estimator in `mechanism_steps` targets it.
  - Card success conditions and the `mapping.condition` of any crossmap map used appear here.
- **Every artifact nameable and existing.** Every dataset, benchmark, model, tool and access level (weights, logits, gradients, API-only) is a named, currently existing artifact. Prefer the baselines and datasets in `expectations.json`. Modest self-built resources (a few hundred hand labels, a converter script) are allowed if named and costed in `resources.estimate`. Never assume a large resource into existence; redesign or narrow the claim now.
- **Claims at defensible strength.** Guarantee words (unbiased, provable, exact, optimal, lossless, or any paraphrase) appear only with their assumptions stated next to them; otherwise use consistent, asymptotic or empirical. Do not hedge away ambition: a strong claim with honest assumptions beats a weak hedged one.
- **Every number has provenance.** Any number that changes what the procedure does (a threshold, budget, window, count, weight) is a named parameter with a default and a one-clause selection rule (`tau = 0.9, swept 0.8–0.95`). No bare literals in prose. Artifact versions, structural constants, definitional settings and campaign scale are exempt. Numbers about prior work cite the paper they come from.
- **Falsification** (`experiment`, `metric`, `direction`, `load_bearing_variable`, `negative_control`).
  - `experiment` is a minimal procedure naming the model, dataset and measurement; `metric` and `direction` say what moves if the candidate works.
  - `load_bearing_variable` is the one named quantity carrying the mechanism claim.
  - `negative_control` intervenes on it (randomize, permute, oracle-replace, ablate its producer) and must predict a move in the **downstream task metric**, not in the variable itself or anything analytically derived from it. "Set X to 0, X becomes 0" tests a definition; "set X to 0, success rate falls to the baseline" is the Popper test.
  - A positive control (only the load-bearing variable recovers most of the effect) or a full-observation oracle is recommended where feasible.
  - A numeric bar is allowed only if it is derived (say from what) or measured (say which ref), tagged inline `derived:` or `measured in <ref>`. Never invent a bar: a made-up threshold can kill a good idea or bless a bad one. Seed counts and campaign scale are design, not bars.
  - Read each `common_practice` and `observed_in_reviews` expectation's `applies_when`. Cover the ones that are about this claim (named baselines, datasets, metrics) in the experiment. An expectation that is not about this claim (a benchmark norm for a mechanism diagnosis), or a convention the candidate deliberately challenges, is not forced into the plan: the audit records it as `not_applicable` or `challenged` with a reason, and a challenge needs evidence.
- **Resources.** `resources.authorized_limit` is `run.json`'s `budget`, copied verbatim; only the user raises it. `resources.estimate` is yours: real numbers (GPU-days, 80GB-class; API dollars; wall-clock) for the **first decisive test** and then for the full campaign. Design so the first decisive test is the cheapest experiment that still separates the candidate from its naive alternative; with `not specified`, keep it small enough that a person can approve it without a second thought, and say what the full campaign would need. The estimate may be revised later (a `feasibility` target); the falsification's variable, control, metric and direction may not be made weaker to fit.
- **Falsification is written last**, after everything else is settled, as if it cannot be revised: later steps change it only through an audit target that names the exact `falsification.<key>` paths.
- **Hook**: at most 2 sentences, exactly one shape, chosen by its admission test, not by ease. Don't stack shapes.
  - (a) Surprising reveal: a metric in `falsification` whose predicted direction or regime split is non-obvious to a reader of the closest papers.
  - (b) Structural reframe: a cited paper whose design operationalizes an assumption nobody has named in published practice (not a known property restated loudly). It is the cheapest shape to fake.
  - (c) Minimalism: the strongest baseline's load-bearing axis (parameters, data, new objects) on which you are strictly ≤.
- **Differentiation is substantive.** One entry per `closest_adjacent` paper at least. Each `delta` says what you derive, construct, claim or measure that the paper did not ("they derive A under B; we derive C under D, the user's regime"). "We use a different card or pattern" is a process error. Write deltas from the reading's method-level fields; if that reading is `abstract_only`, end the delta with `(abstract-only inference)`. `almost_prior` is the single structurally closest paper, and `missed_step` is the substantive step it would have needed (a derivation, construction, regime extension, measurement primitive), not a method label.
- **Collision terms.** `signature_terms` (2–8, 3–7 words each) are your own vocabulary for the mechanism, the claim and the setting, with no title strings and no generic words. `alias_terms` (1–8) name the **same mechanism in other communities' words**: take the source fields of related crossmap maps and older method families that attack the same residue, and ask what their titles would call it. Do not reuse signature vocabulary; a paraphrase catches nothing new. Err toward covering every distinct family.
- **Citations from the domain only.** Every `refs`, `differentiation.ref` and `almost_prior.ref` resolves to `D/papers.jsonl`, `D/readings/`, `D/cards/index.json`, `D/profile/expectations.json` or `crossmap[<i>]`. A paper you remember but the domain does not hold is not evidence; leave it out or make the premise `untested`.

## Retry mode (`attempts/` present)

The archived attempts died at audit. Read each `audit.json`'s `verdict_rationale`, the triggered checks, `revision_targets` and `lessons`, plus any `coherence.json` `blocking` entries.

- **Negative constraints**: do not reuse the same gap set with the same cards. The anchor gap may stay if it is genuinely the most load-bearing; vary the composition. Avoid any composition that walks back into a triggered card failure mode, a flagged anti-pattern or the threat paper's mechanism.
- **Blocking findings become positive directives**: an obstacle the earlier mechanism "did not confront" is now a requirement the new mechanism must solve head-on. A `structural_requirement` is the most load-bearing input you have. Sources it excludes are hard constraints; what it says to salvage you may keep; if it shows the anchor gap does not need the failed component, build around the surviving one.
- Anchor-only is a valid retry. Do not mention the failed attempt anywhere in the output's prose.

## Never

- Cite a paper, result or number not in `D/`, or a sibling candidate as literature.
- Re-propose a `refuted` crossmap map, or a mechanism a lesson records as subsumed or dead.
- Ship a first step that reads "first, build a dataset that does not exist".
- Change, soften or omit `falsification` to make the idea look safer, or write an `authorized_limit` other than `run.json`'s `budget`.
- Add a card to a gap only to make the composition look deeper.
