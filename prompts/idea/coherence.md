# Coherence gate — execute the candidate on paper

Role: `review`. **Fresh context, never the generator**: the context that wrote a logic bug is the one guaranteed to rubber-stamp it. Your single question: does this procedure, executed exactly as written, survive? Logic bugs read fluently ("resample R=16 times until the 24-bit parity matches" sounds fine until the acceptance probability, about 4^-24, shows the loop is vacuous); they surface only under execution, so this gate executes, it does not review.

In scope: internal procedural validity, plus one depth question — does the mechanism confront the obstacle the candidate itself declares (`naive_baseline`)? Out of scope: novelty and threats (audit), falsification structure (audit), whether it works on real data (the falsification experiment). A candidate can pass here and be empirically wrong; it cannot pass here and be incoherent.

## Inputs

- `candidate.json` — under test: `core_mechanism`, `mechanism_steps`, `gap_closure[].how_closed`, `premises`, `naive_baseline`. Treat the candidate's account of itself as a claim, not a guide.
- `phase1.json` — context only: what each gap demands.
- `D/cards/index.json` and the cited card files — the operation each `card_ids` binding promises, and its failure modes (a step that triggers a card's stated failure mode is a finding).
- `D/profile/expectations.json` — context only; do not grade expectations here.

## Depth floor

The same candidate through the same gate has produced 0 findings and 4 findings depending only on how hard the gate pushed. So:

1. **Pick the likely-fatal step yourself, first.** Before anything else, write in `trace` which step or claim you judge most likely structurally broken and why, then attack it first with executed code. (A measured fatal step was a preprocessing stage the candidate never flagged: it made, at observation time, exactly the lossy commitment the mechanism claimed to relocate.)
2. **Try to break every guarantee.** For each "exactly zero", "cannot happen", "by construction", "strictly dominates", "recoverable", "no free parameter": build an instance that would violate it and run it.

## The five trace actions (all, in order)

**T1 — Formalize.** (a) *Dataflow*: rewrite `mechanism_steps` as inputs → numbered steps (each: what it consumes, what it produces, types/dimensions) → outputs. A step consuming something no earlier step produces, a symbol or threshold used before it is defined, a circular dependency, or one term with two meanings is a finding. (b) *Unbound parameters*: a number the procedure acts on (threshold, budget, window, count, interval) must carry a name with a default and a selection rule; `k = 5` or `eps in [0.02, 0.05]` pass, a bare "top 5", ">= 95% agreement", "every 2e3 tokens" are findings. The test is behavioural: if changing the number changes what the algorithm does, it is a parameter; if it only sizes the evaluation campaign (corpus size, seeds), it is scale and exempt. A name bound anywhere in `core_mechanism`/`mechanism_steps` counts. Numbers inside `falsification` are never raised here. (c) *Dual reading*: quote each step verbatim before formalizing it. When an operative term admits more than one defensible reading ("unchanged", "similar", "stable", "near"), formalize every reading and run T2/T3/T5 under each; tag each finding `reading_robust` or `reading_dependent: <reading>`. An ambiguous operative term is always itself a wording finding — patch the text to the reading under which the step is sound, and say so. (d) *Estimand match*: when a premise declares what quantity is estimated, check the steps' estimator targets that quantity over the same population and conditioning.

**T2 — Numeric dry-run.** Build one minimal concrete instance with real small numbers and compute every intermediate quantity. **When Bash is available, write a stdlib-only Python script, run it, and paste script and output into `trace`**; hand arithmetic only when no execution tool exists, each such number marked `unexecuted`. An anomaly asserted without its computed number is not a finding. Tag each anomaly:
- `structural` — follows from the procedure's algebra or shape, so any instance exposes it (vacuous loop, two cases collapsing to one value, a correction constant across items it must separate, dimension mismatch).
- `instance_contingent` — a property of the instance you invented (a gap vs baseline, a win rate). It may motivate a finding but never alone supports a `blocking` one.
Forced results are not evidence: a value fixed by construction (an identity restated as a check, a control compared with itself) confirms nothing; say so and, where cheap, rerun under a perturbation that would move a genuinely contingent quantity.

**T3 — Degenerate probes.** Empty set, k=0, all-identical elements, ties at every threshold, single element, the spec's maximum. Does the procedure halt, divide by zero, emit a meaningless output, or silently skip a branch later steps rely on?

**T4 — Claim → step, graded.** For each property the candidate asserts of its mechanism (in `core_mechanism`, `how_closed`): name the T1 step that establishes it (none → finding), then grade it `established` (constructed, no unstated assumptions), `conditional` (holds only under assumptions not stated where the claim appears — patch: state them next to the claim), `overclaim` (wrong strength, e.g. "unbiased" for a merely consistent estimator — patch: downgrade the wording), or `empirical` (a prediction, fine unless phrased as a guarantee). Statistical claims are settled by an executed Monte Carlo only when the result is structural; if it would depend on the distribution you chose, grade `empirical`. Theorem-shaped claims ("provably", "converges") are at best `conditional` — list the proof obligations. Never push claims vaguer: strong claims with honest assumptions beat hedges, and if every claim is already unfalsifiably soft, that is itself a finding.

**T5 — Independent naive baseline.** Build the most naive version of the mechanism yourself, from the gap and the mechanism's inputs — not the candidate's `naive_baseline.naive`, which may be a strawman. It must be **simpler, not different** (fewer components, no learned part, a rule instead of an optimisation) and run under the **same constraints** (budget, information available at the same moment, deployment limits); state both in one clause. A naive that wins only by relaxing a constraint is a note that the constraint may be unnecessary, not `equivalent_to_naive`. Run it on the T2 instance beside the mechanism and compare numbers. Judge against `naive_baseline.branch`:
- `false_premise` → `confronts_obstacle` if the naive fails for the stated reason and the extra machinery fixes it (show the number); `equivalent_to_naive` if the mechanism behaves as the naive plus cosmetics — an obstacle hole.
- `naive_suffices` → equivalence is expected; check the increment is surfaced, not hidden.
- `disbelieved` → check the naive really works on the instance (that is the claim).
- `n_a` only when no naive execution is expressible (e.g. a pure equivalence result); say why, never fabricate.

## Repair contract (single pass)

Patches make the **written procedure sound**; they never redesign the idea and never "improve" anything no T1–T5 finding requires. Allowed fields: `core_mechanism`, `mechanism_steps`, `gap_closure[].how_closed` (narrative alignment only), and `signature_terms`/`alias_terms` only when a repair changed what the mechanism is (collision must query the repaired mechanism). The validator refuses a refined candidate that changes any other field. **Never touch** `falsification`, `resources` (the tests and the user's cap), `gap_closure[].gap_id`/`card_ids` (card bindings), `differentiation`, `almost_prior`, `hook`, `title` (novelty surface), `premises`, `naive_baseline`, `crossmap_used`, `alternatives_considered`. One pass; no iterate-until-clean.

**Obstacle holes are never patched around.** A finding is an obstacle hole when its honest fix would change what the mechanism is, or when it coincides with the obstacle the candidate's premises or `naive_baseline` say it exists to solve (including `equivalent_to_naive`). Avoidance patches — abstain on the affected cells, clamp the range, skip the regime — are forbidden when they sidestep that obstacle (they stay legitimate for engineering edges unrelated to it). Obstacle holes, and any other finding unfixable without redesign, go to `blocking[]` **verbatim and unsoftened**, and the candidate stays unchanged on that point; the audit owns the decision.

Each `blocking[]` entry is self-contained — a reader holding only that entry can check the modeling and the arithmetic:
- `finding` — the defect, unsoftened.
- `evidence` — the verbatim step quote, the script excerpt and measured numbers (or `unexecuted` arithmetic), the `structural` tag, and `reading_robust` or `reading_dependent: <reading>`.
- `structural_requirement` — written for the next generation on this bottleneck: (a) the identifying condition any mechanism here must possess (a capability, signal or contrast — never a restatement of the defect); (b) sources of it available vs excluded in this setting, pricing excluded ones honestly rather than inheriting the candidate's cost claims; (c) salvage — which instrument, control or measurement carries forward. Only as far as the executed evidence supports; say plainly when it supports nothing concrete. Never cite a ratio whose normalizer is one of its own arms. Diagnosis, not a replacement mechanism.

## Output

`coherence.json`:

```json
{"verdict": "patched",
 "trace": "Likely-fatal step: S3 because ... | T1 dataflow: S1 consumes x[n] -> ... | T2 script:\n```python\n...\n```\noutput: accept_prob=5.96e-08 (structural) | T3: k=0 -> division by zero in S4 | T5 naive: ...; respects the same budget, simpler (no learned scorer); naive 0.41 vs mechanism 0.73 | Patches: mechanism_steps[3] bound 'top 5' to k_top=5 with rule ... (T1b)",
 "claims": [{"claim": "the estimator is unbiased", "grade": "overclaim"}],
 "naive_comparison": "confronts_obstacle",
 "blocking": [{"finding": "...", "evidence": "S2 quote: \"...\"; script excerpt ...; output ...; structural; reading_robust", "structural_requirement": "(a) ... (b) ... (c) ..."}]}
```

- `verdict`: `pass` (no patch applied — `blocking` may still be non-empty) or `patched` (≥ 1 patch applied).
- `trace` holds, in order: the likely-fatal pick, T1 dataflow, T2 script and output (or `unexecuted` arithmetic), T3 probes, T4 arbitration notes, T5 naive and its fairness clause, non-blocking notes, and a **Patches** list — each patch names the field and the T1–T5 finding it repairs (a patch without a finding is scope creep).
- `claims` lists every graded T4 claim; `naive_comparison` is the T5 verdict.

When `verdict` is `patched`, also write `refined_candidate.json`: the **full** candidate (same contract as `candidate.json`), byte-for-byte equal outside the allowed fields, with the patches applied. It becomes the canonical candidate for collision, audit and revision.

## Never

- Run inside the generating context, or adopt the candidate's own view of where the hard part lies.
- Report an anomaly without its computed number, or call hand arithmetic executed.
- Rest a blocking finding solely on an `instance_contingent` result.
- Patch around an obstacle hole, soften a blocking finding, or write the replacement mechanism.
- Touch kill-switch fields, card bindings or the novelty surface; judge novelty or the falsification plan.
