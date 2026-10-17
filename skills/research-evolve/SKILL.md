---
name: research-evolve
description: Use when an existing research mechanism needs repair, simplification, combination, or reframing; when a useful test is infeasible; or when repeated findings expose a shared faulty assumption.
---

# Research evolve

Change a named research object to address a named obstacle or opportunity.
Preserve the parent, the evidence that motivated the change, and what the change loses.
A better-written card is a view change; it is not a new scientific mechanism.

## When this skill fits

Use it after a concrete finding, a new source or code observation, a changed constraint,
or a plausible interaction between existing candidates creates a reason to revise.
Do not generate another variant merely because the previous variant scored poorly.
If the defect is unclear, use research-review or research-diagnose to locate it first.
For a wholly new problem, research-ideate may be the better entry point.
For prose-only editing, use research-report and keep the underlying mechanism fixed.

Read [research-contract](../../references/contracts/research-contract.md).
Read [record-api](../../docs/record-api.md) before creating or updating records.
Read [review-context](../../references/contracts/review-context.md) when handing a child to review.
Use the current research project root; do not write its records into the plugin installation.

## Classify the intended change first

| Object | What changes | Durable representation | Example |
|---|---|---|---|
| Q | Research target, setting, measurement goal, or question premise | New project version | Study partial-observation behavior instead of oracle access |
| H | Mechanism, load-bearing premise, key parameter, or scientific claim | Candidate revision or explicit child | Replace the selector with a different observable |
| T | Testing route while H remains fixed | Activity plan revision, or new activity for a rerun | Use a validated cheaper readout |
| View | Wording, explanation, ordering, presentation | Revised report/card linked to the same objects | Clarify a sentence without adding a rule |

Classify by scientific meaning, not by how few words changed.
Adding a reward normalizer is H even if it fits in one short clause.
Changing which inputs count as legal changes the claim or Q, not just its description.
A budget revision can change T or an investment decision without changing H.
Once an activity runs, its plan and input versions cannot be rewritten retrospectively.

## Minimal input package

Read the exact project and candidate versions, relevant test plans and raw results,
the motivating finding or feedback, user constraints, and the allowable edit scope.
Include negative evidence and failed attempts, distinguishing what each actually established.
Read the parents in full enough to understand their operations and assumptions.
Read the relevant review evidence; evolution is a response, not an independent blind review.
Do not inherit a parent's score or verdict as evidence that its premises are sound.
If a parent's key source is unavailable, preserve that uncertainty in the child.

Write the reason for changing it in one sentence.
Examples: the stated input is unavailable; the control is tautological; the prior method
already performs this operation; the proposed readout exceeds available resources.
If the only reason is “make it stronger,” identify what actual weakness that means.

## Select the operator by the obstacle

| Operator | Use when | Reference |
|---|---|---|
| Scoped revision | A specific definitional, evidential, or local mechanism repair is available | [revise](../../references/methods/revise.md) |
| Combine | Two mechanisms have a real interacting object or process | [combine](../../references/methods/combine.md) |
| Simplify | A claim is broken or a component adds no needed prediction | [simplify](../../references/methods/simplify.md) |
| Feasibility | A fixed H has an informative but unavailable or unaffordable T | [feasibility](../../references/methods/feasibility.md) |
| Out of box | Several candidates share the same unsupported framing assumption | [out-of-box](../../references/methods/out-of-box.md) |

Load the chosen operator in full. These are reasoning techniques, not compulsory stages.
A cohesive repair may involve more than one operation; name each dependency it changes.
Do not split one necessary repair into artificial rounds just to obey an operator quota.
Do not bundle unrelated improvements into a patch that obscures which issue was addressed.

## Procedure

### 1. Reconstruct the parent and the live obstacle

State what the parent consumes, does, produces, and predicts.
Identify the claim and original evidence behind the motivating finding.
Check whether it is a failed execution, a valid negative result, or an interpretation dispute.
A failed job alone may say nothing about H; a legal counterexample may refute a universal H.
If the finding is contested, use research-review adjudication before silently dismissing it.
Preserve the obstacle in terms the next candidate must actually confront.

### 2. State the structural requirement

Describe the capability, signal, contrast, or information access needed to get past the obstacle.
Name which sources are available and which are excluded by the setting or resources.
Separate an unsupported desired capability from one that code or evidence already provides.
Identify salvage: useful instruments, controls, measurements, representations, or subclaims.
Identify what must be discarded and which claimed benefit is lost.
The requirement guides redesign; it does not itself constitute a replacement mechanism.

### 3. Apply the selected operation

For scoped revision, produce a minimal semantic delta against the canonical parent.
For combination, require a shared intermediate object O or a concrete causal interaction.
Show what A writes or changes in O, what B reads, and the conditions under which that is valid.
State a prediction made by the combination that neither parent makes alone.
If no such interaction exists, preserve separate candidates rather than stapling their prose.

For simplification, list claims/components and the predictions that depend on each.
Remove ornament, but state when removing a broken load-bearing claim changes H or Q.
Re-derive the remaining predictions; an empty truism is not a successful simplification.
Retain the old failure in history even if the new restricted claim avoids its scope.

For feasibility, quote the fixed H and the distinction the original test was meant to reveal.
Change the measurement route only with an argument that the new T preserves that distinction.
Name proxy validity assumptions and the rival's prediction, not just a smaller budget.
If making it feasible requires changing the mechanism, classify that separately as H evolution.

For out-of-box work, name the shared assumption and what observations would look like without it.
Map an external mechanism's operations, state variables, information and invariants to this setting.
Use an analogy as a source of structure, not as a replacement for the mechanism.
Meet the structural requirement and state an independently distinguishable prediction.

### 4. Check the resulting object

Read the delta against the exact parent, not a regenerated memory of it.
Every new operation must have defined inputs, outputs and information access.
Every new scientific claim must be identified as proposed, supported, conditional, or unresolved.
Preserve source support and contrary evidence with their applicable scopes.
Use the shared [falsification definition](../../references/methods/falsification_reaudit.md)
for the resulting test rather than writing a new local notion of “good experiment.”
Do not insert unexplained constants, default normalizers, or private labels to make the child work.
If a new parameter is required, expose its meaning, selection rule and dependence explicitly.

### 5. Check that the change is substantive and useful

Compare operations and predictions with the parent and verified nearest prior work.
New words, a nicer title, or a changed pattern citation are not H novelty.
For a T-only change, improvement means a more feasible informative test, not a new hypothesis.
For simplification, improvement can be interpretability or testability despite a lost claim.
For a Q pivot, explain why the new question remains worth answering.
If the child only evades the declared bottleneck, name that loss rather than claiming it solved it.

### 6. Persist the change with ancestry and reasons

Store any newly inspected source or execution material before referring to it.
For H, write a candidate with its exact problem reference, mechanism and nonempty claim map.
Add assumptions, predictions, parent candidate references and change_note where applicable.
A local revision can append a version of the same record; a distinct competing branch can use a new ID.
Both retain exact parent versions and rationale; neither deletes or overwrites history.
For T-only work, retain the same candidate reference and write the changed activity plan.
A new run uses a new activity ID; no old completed/failed activity is reopened.
For Q, append the project version and explicitly connect any revised H to that question.
For View, keep Q/H/T unchanged and route the prose work to research-report.

Use `expected_version` when writing; reread on conflict instead of overwriting another writer.
Record disposition of the motivating feedback/finding with its output reference when adopted.
If a suggestion is deferred or rejected, give the evidence-based reason; omission is not consumption.
Use only the five record kinds and active fields; operator names belong in change_note or plan.
If the record service is unavailable, retain a versioned Markdown handoff and mark it unrecorded.

### 7. Recheck the affected dependencies

Use research-review in revision mode with the parent finding, delta, raw evidence and child version.
The child does not automatically inherit an approval, nor require a complete new review of everything.
For a new independent opinion, build a fresh evidence-preserving view and disclose actual independence.
If a code path changed, research-code checks implementation correspondence and the affected examples.
If novelty vocabulary or operations changed, research-retrieve checks the relevant closest mechanisms.
If prediction/measurement changed, research-test rechecks discrimination and feasibility.
Stop the loop once the motivating issue is answered or the remaining obstacle is explicit.

## Minimal output and handoff

Lead with what changed, why, and whether the change is Q, H, T or View.
Provide the parent and new references, motivating evidence, changed operations, and lost claims.
State the surviving uncertainty, affected checks, and the next useful action.
Do not require a full three-language card, a score, or a tournament match to record evolution.
A compact change note can link a detailed mechanism and evidence without copying them repeatedly.

## Bridges to the rest of the suite

| Trigger | Receiver | What must travel |
|---|---|---|
| Same hidden assumption breaks multiple candidates | research-diagnose, research-ideate | Structural requirement, observed failures, excluded information sources |
| Cross-domain analogy suggests a new operation | research-retrieve, research-construct | Source mechanism, mapping, prerequisite mismatch and unique prediction |
| Candidate already subsumed by prior work | research-decide or research-diagnose | Verified overlap, still-useful artifacts, possible distinct question |
| Mechanism repair requires executable detail | research-code | Exact new H, input/output changes, original counterexample |
| H is fixed but its test is too costly | research-test | Original distinguishing prediction, proxy validity and real constraints |
| Repair changes project value or remaining work | research-decide | New scope, lost benefit, next cost and unresolved risk |
| Only clearer communication is needed | research-report | Same Q/H/T and permitted View change |
| More than one loop is active | research-workflow | Scoped questions, dependencies, and explicit stopping conditions |

## Local invalidation guide

| Delta | Reopen | Preserve as historical/applicable |
|---|---|---|
| Citation or label only | Relevant support/identity check | Mechanism and unrelated executions |
| Selector, normalizer or information source | Dataflow, counterexamples, fairness, affected novelty and predictions | Unchanged sources with scope noted |
| Combined mechanism | Interface, compatibility, emergent prediction, parent ablations | Both parents and their adverse evidence |
| Removed claim or component | Dependents of the removed item, narrowed value and test | Original claim's failure and unaffected subclaims |
| Cheaper fixed-H test | Proxy validity, discriminatory contrast and cost | H and prior scientific observations |
| New Q | Relevance of candidate, evidence and evaluation conditions | Individually applicable materials, not blanket prior approval |

A stale-input notice requests applicability review, not an automatic full rerun.
The record backend cannot decide whether the scientific meaning of a delta is local.

## Stopping and escalation

Stop when the next candidate/test is concrete enough for its targeted check.
Stop if another attempt adds no new evidence, operation, contrast or justified assumption.
If an obstacle requires unavailable information, say that rather than substituting an oracle.
If no feasible discriminating T exists, park the test with a specific revisit condition.
If a valid counterexample refutes the unchanged H, do not seek cheap positive tests to erase it.
An explicit H revision or different question can continue, with the old result preserved.
Additional agents are optional and depend on active authorization, expertise need and useful separation.
Evolution does not itself authorize experiments, new monitoring, compute purchases or publication.

## Worked example: cheaper testing after a failed run

A selector's expensive benchmark failed to launch; a separate legal-input test disproved
its universal claim that the critical visual token is always retained.
First classify the failed launch as an execution failure and retain the valid counterexample.
A request to make the same test cheaper cannot turn that original H into an intact hypothesis.
The author proposes a fallback rule, creating H version 2 and citing the exact parent finding.
The change note states the new operation, its information access and the benefit still unmeasured.
The original example is rechecked against H2; a smaller diagnostic T also compares the naive rival.
If that T preserves the relevant prediction difference, it is a useful next test plan.
Neither the plan nor a passed example establishes benchmark improvement.
If the fallback merely excludes the hard case, disclose the narrower H and return its value to research-decide.

## Common mistakes and provenance

- Combining two high scores: require an interacting object and a new prediction first.
- Dropping an attacked claim quietly: record the loss and the resulting Q/H scope.
- Cheapening T by weakening H: classify both changes and preserve the original result.
- Creative nouns without operational mapping: return to the structural requirement.
- Card prose adding a method decision: route H revision instead of hiding it in a View edit.

Adapted from Co-Scientist's four evolution operators and ResearchStudio's patch-only revision,
canonical candidate, executed-obstacle handoff and information-gain retry principle.
Detailed source links and replacements appear in each active method reference.
Fixed tournament entry, one-operator quotas, field locks and automatic full review were removed.
Authoring checks are recorded in [authoring-review](../../evaluations/authoring-review.md).
