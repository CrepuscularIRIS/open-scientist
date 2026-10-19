# Variant: diagnosis

Why does an observed failure happen; is a reported problem real; is a measurement right.

This variant changes how the protocols in [protocols.md](../protocols.md) apply to this task type. It never switches one off. Seeds below are starting vocabulary; the study's `rubric` and `test_protocol` assets are rebuilt from this field's evidence (see [design](../../docs/design.md) §2–3).

| Protocol | How it applies |
|---|---|
| Falsification (3) | A counterfactual control: change only the suspected cause and predict whether the symptom moves; the rival is the next most likely cause (often in measurement, data or preprocessing). Retrodiction counts: does each explanation predict observations already on disk? |
| Coherence (7) | T1 dataflow over the **measurement** path as well as the system: where could the signal be produced or destroyed before it is measured? |
| Code (diagnose) | [research-code method](../methods/actions/code.md): turn the claim into a checkable statement, find the real entry points, audit what information is available when, and run the cheapest exclusion first. |
| Review | Anti-circularity: the system under test must not define its own ground truth; independence of the oracle. |
| Deliverable | `diagnosis`: done when a finding judges the premise in question. Revising the question is progress; so is stopping construction on a false premise. |

Rubric seeds: Co-Scientist observation review (already explained / other more likely / missing piece), OS diagnose. Watch for: building a fix for a premise nobody tested.
