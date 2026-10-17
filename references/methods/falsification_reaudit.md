# Discriminating tests and falsification review

This is the single active definition of the testability/falsification check used by review, revision and evolution. A revision reuses this definition rather than maintaining a second abbreviated copy.

## Inputs

Read the exact claim, mechanism and premises, the proposed test activity, competing explanation or baseline, available observations, resource constraints, and any prior test critique. For a changed plan, include the previous plan and the explicit delta.

A claim about a mechanism, a practical performance claim, and a universal mathematical claim need different kinds of evidence. Identify which is being tested before checking the plan. A convenient outcome measure cannot silently substitute for the intended claim.

## The check

### Concrete experiment

Name the minimal experiment: setup, inputs or units, comparison, readout, and the result that would change the next decision. “We will evaluate” is not an experiment. State what is already executable and what still needs implementation or access.

### Competing predictions

Specify the prediction of the candidate and at least the leading plausible alternative when the task is to distinguish explanations. A confirmatory result is not discriminating if both predict it. For performance comparisons, state the same-information, same-budget or otherwise justified baseline conditions.

If an alternative is not yet identified, write that gap and search for the obvious null or simpler mechanism. Do not fabricate an implausible rival merely to make the candidate easy to distinguish.

### Load-bearing variable or contrast

For an intervention claim, identify the quantity, operation or condition that carries the claimed mechanism: a gradient norm, information-gain term, representational direction, learned threshold, data-access condition, or other specified object. Quote its definition and explain why changing it tests the claim.

The legacy format required exactly one scalar. Here one primary contrast is preferable, but a joint mechanism may require a stated set of interventions. Do not force an identification problem or observational comparison into a meaningless single variable.

### Negative control and downstream consequence

A negative-control intervention on the load-bearing variable should predict a consequence in the downstream outcome relevant to the claim. A control of the form “intervene on X, therefore X becomes zero” tests a definition, not a mechanism.

Explain what should remain matched across the intervention and control, including rate, compute, input information, selection bias and measurement. If the intervention also changes an obvious confounder, its result may not identify the proposed mechanism.

For a theorem or deterministic property, a proof obligation or legal counterexample may replace an empirical negative control. The question remains whether the evidence decides the actual claim under its premises.

### Numerical thresholds and their provenance

Classify any claimed numerical outcome threshold:

- `none`: no numerical outcome threshold is asserted.
- `derived`: the derivation and its inputs are given so a reader can recompute it.
- `measured`: the value is taken from an identified source or run whose scope applies.
- `asserted`: a derivation or source is claimed but remains uncheckable.
- `invented`: an outcome magnitude is presented as known without provenance.

Cost and resource performance predictions can be invented as easily as accuracy improvements. Replication counts, sample sizes and user resource caps are design constraints, not predictions of success. Thresholds that define a subgroup are setup conditions and must be labeled as such.

A prospective decision threshold can also be a justified design choice: label its rationale and uncertainty rather than pretending it was measured. Do not turn the absence of empirical evidence into an obligation to use arbitrary numeric precision.

If a numerical prediction was invented, remove the unsupported assertion or make its prospective status explicit. Preserve the scientific question, metric and controls. If a new magnitude changes the intended claim, record a new H or T version instead of quietly weakening the old claim.

### Scope, feasibility and evidence level

State which conditions a negative result would refute and which a positive result could support. One valid counterexample can refute a universal claim in its stated domain. One successful example cannot establish average improvement or a general causal mechanism.

Check the actual ability to collect the readout under project constraints. A cheaper proxy requires a validity argument linking it to the original claim and the rival's prediction. Smaller, faster and easier does not automatically mean equally informative.

## Review result

Use a prose assessment such as `discriminating`, `deficient`, or `unresolved`, with the deciding sub-question and scope. These are method descriptions, not additional record API judgment enums.

A useful result names the minimal missing piece: unclear outcome, indistinguishable predictions, confounded intervention, unavailable readout, unsupported magnitude, or ambiguous applicability. Record the affected claim/test using the active finding schema.

Do not declare an H disproved merely because its proposed test is deficient. Do not declare it supported merely because its test design is discriminating.

## Reviewing a revision

Read the changed plan and its parent plan. Check the parts affected by the delta against the same definition above. Preserve unaffected checks with an explicit applicability reason.

When the authorized change is strengthen-only, verify that every previous experiment element, claim, metric direction and control survives in substance, with only the intended addition new. If something was removed or changed, surface it and classify the real Q/H/T change.

The original source allowed exactly one rewrite and permanently locked the experiment/claim. This adaptation preserves an executed activity's history while allowing prospective new plans. A new experiment needs a new activity ID; an executed plan is never rewritten to match its result.

## Stop and handoff

Return to research-test when only the design lacks a discriminator. Return to research-construct or research-evolve when the missing observable exposes an undefined mechanism. Return to research-decide when the necessary test is outside present resources.

Stop this check when the remaining uncertainty and next admissible action are explicit. Do not repeatedly rewrite the same prediction to obtain a favorable label.

## Provenance and replacements

Adapted from [ResearchStudio falsification_reaudit.txt](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/falsification_reaudit.txt) lines 3–38 and 90–103, and the fuller numeric provenance check in [critique.txt](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/critique.txt) lines 107–114.

Retained the concrete minimal experiment, downstream metric, non-tautological control, strengthen-only comparison and narrow re-audit. Added explicit rival predictions, truthful prospective thresholds, scope/feasibility, valid universal counterexamples, and reuse across all consumers. Removed duplicated specs, rendering boilerplate and automatic abandon after one rewrite.
