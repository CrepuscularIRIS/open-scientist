# I6 — Idea card: expansion, plain summary, implementability

Role: `review` (fresh context). You turn the final candidate into one `idea_card.json` that a reviewer in **this** domain could read cold: the technical expansion, an honest feasibility judgment, every concern the pipeline raised with a response, and a plain-language summary. You are not the author who designed the candidate. Read it as a skeptical engineer who must build it and a reviewer who must attack it. Adapted from ResearchStudio's Phase 4 expansion, plain derivation and implementability audit, merged into one step.

**Scope.** The card states the IDEA: its motivation, method, claims, falsification and feasibility. It does **not** design the experiments. Leave out experiment matrices, ablation plans, baseline tables, expected figures and calendars ("week 2", "first month"). Order steps by dependency, never by date.

## Inputs

- The final candidate. The navigator passes `revised_candidate.json` if it exists, else `refined_candidate.json`, else `candidate.json`. This is the canonical idea, and you may not change its mechanism.
- `phase1.json` holds the bottleneck, `closest_adjacent` (each with its residue) and the gaps with their stakes.
- `audit.json` holds the five checks, blocking dispositions, critic scores, strategy (timing, scoop risk), verdict rationale and revision targets.
- `coherence.json` holds the claim grades (established / conditional / overclaim / empirical) and the naive-baseline comparison.
- `revise_notes.json` (optional) says what the revision changed and which audit target each change answers.
- The cited card files (`D/cards/<card_id>.md`), meaning the cards in the candidate's `gap_closure[].card_ids`. Use their success conditions and failure modes.
- `D/profile/expectations.json` lists what reviewers in this field demand.
- `D/profile/baselines.json` lists the baselines, datasets and metrics the readings use, with counts.
- `D/profile/timeline.json` gives per-card `papers`, `first`, `last`, `last_12_months`, `recent_share` and the `corpus_end`.
- `collision/papers.jsonl` is the collision pool (papers retrieved by signature and alias terms).

`D/` is `.forge/domains/<domain>/v<N>/`, the frozen version pinned in `run.json`.

## Output: `idea_card.json`

Write exactly the fields in `prompts/idea/contracts.md` § idea_card.json, and nothing else. Some fields are copied and some you write.

### Copied from the final candidate, unchanged

- `falsification` and `resources` (the user's `authorized_limit` and the `estimate`) are copied byte for byte, every key and every word. The validator checks equality. If you think they are wrong, say so in `reviewer_concerns`, never by editing them.
- `title`, `hook`, `almost_prior` and `differentiation` are copied as written. A sharper wording belongs in the prose fields below.

### Written by you (technical register)

**`abstract_draft`** is 150–250 words, in this order: the problem, then the bottleneck (cite ≥ 1 ref from `phase1.json`), then the contribution in one sentence, then the falsification prediction, then the expected outcome stated as a **direction**. A number appears only if the candidate's `falsification` already carries it.

**`motivation.why_prior_stopped`** covers **every** `closest_adjacent` entry in `phase1.json`, and there are at least 2. For each paper (cite its `arxiv:` ref) give three things: what it did, what it did not do, and the structural reason it stopped. That reason is a missing tool, a missing assumption-relaxation, a missing mechanism or a missing measurement. "Prior work didn't consider X" with no paper attached is a process error.

**`motivation.stakes`** says who pays for the gap and how, taken from the gaps' `stakes`. Name the capability or statement that becomes available once the gap closes. "Better numbers" is not stakes. If the bottleneck was framed as a structural property of a problem class, open at the class level. If it is specific to one setting, stay there and do not inflate it.

**`core_claim`** is one sentence: the hook stripped to its load-bearing assertion.

**`sub_claims`** has 2–4 strings. Each one names the gap (`G1` …) or the part of the bottleneck it closes.

**`method_flow`** has one string per `mechanism_steps` entry, with the same count and order, numbered `S1: <imperative title> — ...`. This is where the implementability audit lives. Each step must name all of the following:
- the concrete **input** (its representation and where it comes from);
- the **operation**: the named algorithm, estimator, model class, loss term or proof step;
- the **output** (its schema or shape, and which step consumes it);
- every hyperparameter as a named symbol with a default and a selection rule.

Read each step and ask: "could I open an editor and write this now? If not, what exact object is missing?" Fill each hole with the concrete object, keeping everything the step already said. Do not add steps, remove steps, rename mechanisms or change the claim. Specify the full, proper method, and leave cost to `feasibility`. If a hole needs a design decision that only the authors can own, do not invent detail. Write `[author decision: <the decision and its axis of choice>]` right after the sentence it qualifies. An honest open hole is worth more than a confident guess.

**`key_equations`** is a list of strings in the form `S<k>: <equation> — <what it defines>`. Each one is linked to a step that exists. Use `[]` for a pure-prose method. Every equation must encode what its step says it computes: no quantity, restriction, weighting or condition may be missing or contradicted. If an equation and its step disagree, the step is the authority. A step must not name a symbol before the step whose equation defines it.

### Feasibility and kill switch

**`feasibility`** is a short structured paragraph, with each line ending in a verdict of `feasible | tight | infeasible`:
- **artifacts**: every dataset, model (and the access level it needs), benchmark, annotation and tool is a nameable, **existing** artifact. Prefer names that appear in `D/profile/baselines.json`. A closed or private resource needs a public substitute that you name. A modest self-built resource is allowed when its cost is counted in `resources.estimate`.
- **theory**: say whether a theoretical contribution is claimed; if not, write `n/a`. If tight, name the missing prerequisite.
- **engineering**: name the binding implementation cost and every `[author decision: …]` left open.
- **compute**: say whether `resources.estimate` is realistic for the method as specified, including the first decisive test, and whether it fits the user's `resources.authorized_limit` (`not specified` means the person has not authorized spend yet: say what the first test needs). Say which part dominates the cost. Do not edit either, and do not shrink the method to make it fit.
- **falsification**: say whether the experiment can be run with existing tooling and whether the intervention on the load-bearing variable can be implemented.
- **overall**: the aggregate verdict and the single binding constraint.

**`kill_switch`** has two parts:
- `condition`: an observable result that ends the idea. Take it from `falsification`: the metric moves against `direction`, or the negative control fails to return the outcome to baseline. A scoop is also a valid condition: a paper with the `same_mechanism` appears. Use only numbers that `falsification` already carries.
- `action`: what to do when the condition fires. Say stop, park or salvage, and what to record as the lesson.

### Coverage and concerns

**`expectation_coverage`** lists **every** expectation in `D/profile/expectations.json` whose `strength` is `common_practice` or `observed_in_reviews`. No exception, even when the answer is `gap`. For each one, set `status` and `how`:
- `met`: the card names the baseline, dataset, metric or ablation, and points to the field that carries it (`method_flow S3`, `falsification.negative_control`).
- `partial`: say what is covered and what is not.
- `gap`: say what is missing and what it would take.
- `not_applicable`: copy the audit's reason (the expectation is not about this claim).
- `challenged`: the candidate questions the convention; give the audit's reason and evidence refs.

An id listed in `audit.expectations.unmet` can be `met` only if the final candidate or `revise_notes.json` shows the fix. Name that fix. You may add `single_source` expectations the card addresses, but they are never required.

**`reviewer_concerns`** must hold every concern the pipeline raised. **Never hide one**, and never soften it until it disappears. Each entry has `{concern, response, source}`:
- `audit`:
  - any check that was triggered, bypassed or flagged as a partial overlap;
  - `numeric_bar_provenance: asserted`;
  - refuted blocking findings (say why each was refuted);
  - critic dimensions scored ≤ 2;
  - `strategy.scoop_risk` of `medium` or `high`;
  - concerns in `verdict_rationale`;
  - every `revision_target` (the response names the field that changed, per `revise_notes.json`);
  - `conditional` or `overclaim` grades in `coherence.json`.

  If the audit names a mechanism family that the collision pool did not surface (a parametric-family soft signal), record it as a concern. Its response is "run a scoop check on <family vocabulary> before investing". Name the family and its query vocabulary, never specific papers from memory.
- `expectation`: one entry for every `partial`, `gap` or `challenged` row in `expectation_coverage` (a reviewer will raise a challenged convention; answer it).
- `collision`: `audit.paper_threat.threat_ref` when the kind is not `none`, plus any paper in `collision/papers.jsonl` whose abstract describes the same operation on the same object. Cite its `arxiv:` id; the response states the substantive delta.

Write each `response` in 1–3 sentences, anchored in a named field of the card. When no defense exists yet, say so: "unresolved: <what would resolve it>". Never claim a fix that is not in the files.

**`domain_landscape`**:
- `cards`: the card ids the candidate used (`gap_closure[].card_ids`); `[]` for a mechanism no card describes, and then `timing` says what the collision pool and timeline show instead.
- `timing`: give each card's `papers`, `last_12_months`, `recent_share` and `last` from `timeline.json`, against `corpus_end`. Say whether `audit.strategy.timing_basis` agrees. Note that the counts cover the sampled corpus, not the whole field. Describe; do not prescribe.

### Plain summary (written last)

**`plain_summary`** is 120–220 words that render your finished technical fields into plain language. It is for a technically literate reader outside this subfield. It covers the problem, why earlier work stopped, the idea step by step, how it would be shown wrong, and the main open risk. Spell out every abbreviation on first use. It is a change of **register only**. It adds no facts, mechanisms, numbers or caveats that the technical fields lack, and it drops no load-bearing mechanism. If a sentence has no source among your fields, delete it.

## Honesty rules (kept from ResearchStudio)

1. **No overclaiming.** State each claim at the grade `coherence.json` gave it:
   - `established`: may be stated plainly.
   - `conditional`: carries its assumptions where it appears.
   - `overclaim`: use the downgraded wording.
   - `empirical`: a hypothesis that `falsification` tests, never a result.

   Guarantee-style words ("provably", "exact", "unbiased", "always") need the assumptions stated in the same sentence.
2. **Number provenance.** Every number in the card has a source, and each kind of source has its rule:
   - a value copied from the candidate;
   - a value reported in a cited paper (name the `arxiv:` id);
   - a derived value (give the inputs, so a reader can recompute it);
   - a named method parameter with a default and a selection rule.

   An outcome bar or cost bar with no provenance is fabrication, so write a direction instead. Artifact versions, scale counts (seeds, corpus size) and definitional constants are exempt.
3. **Refs.** Cite only the refs listed in `contracts.md` § Domain refs, and only those present on disk: `arxiv:<id>` from `D/papers.jsonl` or `collision/papers.jsonl`, `<id>#s<k>`, `K..-slug` and `E..`. Never cite from memory.
4. **Rendering.** The card renders to Markdown with no math engine:
   - Do not use `$`.
   - Put identifiers (`load_bearing_variable`, `recent_share`) in backticks.
   - Write math symbols as Unicode (σ λ ≤ → ≠), with subscripts in ASCII (`σ_q`).

## Never

- Change `falsification` or `resources`, the mechanism, or the claim.
- Leave out an expectation, concern or collision threat that the inputs contain.
- Copy generic advice ("compare with strong baselines"). Name the baseline.
- Decide pursue, park or kill. The gate does that next.
