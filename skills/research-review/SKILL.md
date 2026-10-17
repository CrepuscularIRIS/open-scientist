---
name: research-review
description: Use when a research claim, mechanism, experiment, citation, or revision needs scrutiny; when reviewers disagree; or when favorable scores conflict with raw counterevidence.
---

# Research review

Review a named question against the exact proposal and available evidence.
A completed review records what was examined; it does not certify a research project.
Keep scientific findings separate from the decision to spend more effort.

## Start with the review question

Use this skill for a proposed mechanism, a source claim, a discriminating test,
a response to an earlier finding, or a dispute about a concrete counterexample.
Choose the smallest question whose answer changes the next action.
“Review everything again” is appropriate only when the dependencies changed broadly.
A formatting edit belongs in research-report; a new mechanism belongs in research-evolve.
Investment priority belongs in research-decide after the relevant findings are available.
For that strategic question, [Companion critic](../../references/methods/companion-critic.md)
provides value, timing and opportunity lenses; its signals do not replace source or mechanism checks.

Read [the shared contract](../../references/contracts/research-contract.md).
Use [review-context](../../references/contracts/review-context.md) to assemble the view.
Read [record-api](../../docs/record-api.md) before writing records.
The project root is the user's research workspace, never the plugin installation.

## Choose the question and reference

| Question | Method to load | Useful answer |
|---|---|---|
| Does the source say what this claim says? | [grounding](../../references/methods/grounding.md) | Source-scoped support or a precise mismatch |
| Can this mechanism work under its stated assumptions? | [critique](../../references/methods/critique.md), [rubric](../../references/methods/review-rubric.md) | Supported steps, weakest premise, concrete obstacles |
| Does the experiment distinguish competing explanations? | [falsification](../../references/methods/falsification_reaudit.md) | Prediction/control assessment and missing discriminator |
| Is the claimed refutation of executed evidence valid? | [refutation recheck](../../references/methods/refutation_recheck.md) | Formalization, arithmetic, or instance-validity decision |
| Which candidate should be investigated first? | [comparison](../../references/methods/ranking.md) | Criteria-specific differences and information needs |

Load only the relevant methods. A source correction need not load all five.
For novelty, obtain actual closest-work evidence through research-retrieve.
An older same-mechanism paper can subsume a new title or vocabulary.
An empty search, inaccessible paper, or exhausted budget leaves coverage uncertain.

## Inputs and their meaning

The minimal package contains the question, exact Q/H/T references, constraints,
the target claim, original sources, applicable counterevidence, and permitted scope.
Q is the project question; H is the candidate mechanism; T is the test activity.
References use `{id, version}` and must resolve in the selected project.
If a candidate claim is targeted, identify its key in that version's `claims`.
Read the claim itself; a title, short card, or positive overview is insufficient.

Material may be a paper passage, repository code, a dataset inspection, or a run output.
Preserve source location, code/configuration version, input conditions, and limitations.
A citation's identity, its text being read, and its support for this claim are distinct.
Results from a failed run cannot silently become measurements of the hypothesis.
Constructed examples and actual task measurements must remain labeled separately.
If a crucial source cannot be opened, record that limit and avoid a decisive finding from it.

## Three review modes

### Independent

Supply accurate Q/H/T, raw evidence, fair baseline conditions, and resource constraints.
Hide old total scores, author/model identities, recommendations, and persuasive summaries.
Include negative evidence even if its candidate was parked or ranked poorly.
Extract evidence from previous reviews without passing their verdict as an authority.
Review the actual handoff: removing a numeric score alone may leave an anchoring narrative.
State the achieved independence; if old judgments were already seen, disclose that fact.
Independent does not mean ignorant of known facts or allowed to rediscover only favorable ones.

### Revision

Read the original finding, the proposed delta, its rationale, and the original evidence.
Check whether the same claim survived and whether the change actually confronts the issue.
Identify newly affected claims and tests; do not call this a fresh blind review.
Carry forward unaffected findings with an explicit applicability reason.
A citation-only change normally needs source/support verification, not a new experiment.

### Adjudication

Read both precise positions and the evidence that could decide the dispute.
For executed counterevidence, use the refutation recheck method.
Do not decide a modeling or arithmetic dispute by votes, prestige, or fluency.
When the evidence does not decide it, return a bounded unresolved question and next check.
The adjudicator need not rescore novelty, impact, narrative, and feasibility together.

## Procedure

### 1. Pin the scope and retrieve the record closure

Read the focused object and referenced historical versions, not only the latest card.
Inspect the full context index for contrary findings and unresolved user feedback.
The context tool is not a scientific relevance filter or a blinding service.
Build the smallest evidence-preserving view needed for the chosen mode.
Write the question in one sentence and state which changes are outside this review.

### 2. Reconstruct the claim before attacking it

State the mechanism's input, operation, output, available information, and assumptions.
For each important statement, identify what would establish or refute it.
If a term has two plausible readings, quote both and test the actual intended definition.
Do not simplify away the part that could make the proposed method work.
Do not rescue a failing method by adding an unstated label, oracle, default, or parameter.
An unresolved specification is a finding, not permission for the reviewer to invent a method.

### 3. Inspect evidence and the closest alternatives

Read the relevant source passages and code paths, not just abstracts or comments.
Check the direction, system, scale, timing, and information conditions of each claim.
Compare against a simple alternative under the same resource and data-access constraints.
Check whether a proposed outcome is already known or also predicted by its rival.
If novelty is disputed, compare operations and premises across field-specific aliases.
Parametric recall may nominate a family to search; it is not a verified paper citation.

### 4. Examine the weakest links

Decompose the mechanism into individual testable assumptions using the rubric.
Separate missing specification, direct contradiction, and unmeasured empirical benefit.
For quantitative claims, recompute the relevant arithmetic when permitted and useful.
Mark an unexecuted calculation as unexecuted; do not imply a tool result was obtained.
A valid single counterexample can refute a universal claim within its stated domain.
A favorable toy instance cannot establish average effectiveness on the real distribution.
Use the shared falsification method for test design; do not invent another local definition.

### 5. Disposition existing contrary findings

For each relevant finding, say upheld, addressed, disputed, or outside the present scope.
These are review prose labels; record API dispositions have their own enumerated outcomes.
Cite the concrete reason and new evidence, not just “the revised mechanism should work.”
If an executed finding is disputed, name the alleged formalization, arithmetic, or instance flaw.
Invoke narrow adjudication when that dispute affects the next action.
An unresolved obstacle limits the affected claim; it is not automatically a global project gate.

### 6. Record findings and route the next question

Write source materials before findings that reference them.
Use an assessment of type `finding` for one claim-scoped judgment.
Put review mode, applicability, and independence limits in `rationale`/`scope` or a linked material.
Use only schema fields from record-api; an informal checklist is not a payload schema.
For a candidate subject, `claim` must be a key in that exact candidate version.
Use `unknown` for an unmeasured mechanism claim rather than calling plausibility support.
Use `contested` when admissible evidence conflicts or the modeling dispute remains unresolved.
Use supported/partial/contradicted only with actual material references and stated scope.
Record feedback consumption separately; storing a review does not consume a user's instruction.

## Minimal output

The user-facing output starts with the answer to the named question and its boundary.
Then list the deciding evidence, unresolved issue, and concrete next action.
The durable finding contains subject reference, claim, judgment, evidence, rationale, and scope.
A review note may additionally summarize mode, checked inputs, affected dependencies, and omissions.
Do not require a numerical score, fixed panel, tournament, or long card to finish a review.
If asked for scores, label the scale and do not let arithmetic erase a decisive contradiction.
The record backend checks structure and versions; it does not validate scientific truth.

## Branches and bridges

| Finding | Receiver | Preserve | Return here when |
|---|---|---|---|
| Missing or ambiguous prior-work evidence | research-retrieve | Claim, mechanism aliases, existing passages, failed queries | The nominated sources are actually checked |
| Bottleneck depends on unavailable information | research-diagnose | Code trace, stated problem, oracle/label conditions | A revised problem is explicit |
| Mechanism has a repairable defect | research-evolve | Finding, parent version, raw counterexample | A specific delta changes the relevant dependency |
| Broad construct lacks an executable definition | research-construct or research-code | Exact gap and constraints | The missing operation is specified |
| Experiment cannot distinguish the rivals | research-test | Both predictions and existing controls | A discriminating plan is available |
| Multiple reasonable explanations remain | research-ideate or research-test | Shared facts and disagreement map | New information can separate them |
| Correct but low-value or infeasible now | research-decide | Scientific findings and real resource limits | A value/constraint change affects the choice |
| Claim wording exceeds evidence | research-report | Supported scope and exact unsupported sentence | Wording or intended claim changes |

research-workflow can organize these handoffs without imposing a global stage order.
The same review may generate two different questions for two receivers.
Keep each question scoped so one local fix does not restart an entire pipeline.

## Local invalidation after changes

| Change | Recheck | Usually reuse |
|---|---|---|
| Citation corrected, same supported claim | Identity, passage, support relation, dependent judgment | Code results and unrelated reviews |
| Mechanism or information source changed | Dataflow, counterexamples, fairness, affected novelty and predictions | Unchanged background sources |
| Control or measurement changed | Test discrimination, comparability, feasibility | Mechanism reasoning not dependent on that measurement |
| Budget changed | Feasibility and next investment | Historical observations and scientific definitions |
| Q changed | Problem relevance and applicable evidence | Individually applicable sources with justification |
| View changed only | Faithfulness to recorded claims | Q/H/T and existing evidence |

Review stale notices semantically: a changed version requests applicability analysis.
Old findings remain historical; they do not automatically certify or condemn the new version.

## Stopping conditions

Stop when the named question has a supported answer or a precise remaining uncertainty.
Stop a repetition when it adds no evidence, new prediction, or useful discriminating action.
Do not manufacture agreement by rewording the same arguments until a reviewer approves.
If source access or execution is unavailable, return the bounded finding and required next check.
Additional reviewers are useful for a consequential unresolved dispute or distinct expertise.
They are not required for every edit; delegation still follows the active user's authorization.
Do not start experiments, new monitoring, or a larger review campaign from a review conclusion alone.

## Worked example: positive review versus a valid counterexample

A candidate claims its pruning rule always preserves the only task-relevant visual token.
An earlier review rated it highly; a saved test shows that token was discarded on a valid input.
The independent package includes the candidate version, legal-input definition, script, and output.
It excludes the old score and recommendation, while retaining the raw adverse result.
The reviewer checks the real rule and records a contradiction to the universal preservation claim.
If the author says the input is illegal, adjudication checks the original written premise.
Adding a new exception creates a revised H; it does not erase the old contradiction.
research-evolve may repair the selector, and only affected claims/tests need another review.
research-decide may still find a useful restricted application; that is a separate judgment.

## Common mistakes

- Blind review that omits the negative result: restore the original material and disclose the gap.
- “Already reviewed” treated as scientific approval: inspect the actual findings and their scope.
- Pattern-library failure used as proof: identify the concrete mechanism defect it predicts.
- Source existence treated as support: inspect what the source says in the relevant setting.
- Full restart after citation repair: follow dependencies and explain what still applies.
- Reviewer silently invents a default: record a specification issue and route H revision.

## Provenance and adaptation

Adapted from ResearchStudio critique, falsification re-audit, refutation recheck and patch workflow;
Co-Scientist reviewing, grounding and comparison skills; and Companion's evidence-backed disagreement.
The method references retain detailed source procedures with explicit adaptation notes and source links.
Removed fixed seats, score-based gates, mandatory tournaments, and automatic whole-project approval.
Authoring evidence is in [authoring-review](../../evaluations/authoring-review.md); it is not an efficacy claim.
