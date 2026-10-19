# Variant: analysis

A measurement or analysis study: what is true of existing systems, data or practice.

This variant changes how the protocols in [protocols.md](../protocols.md) apply to this task type. It never switches one off. Seeds below are starting vocabulary; the study's `rubric` and `test_protocol` assets are rebuilt from this field's evidence (see [design](../../docs/design.md) §2–3).

| Protocol | How it applies |
|---|---|
| Falsification (3) | A pre-stated analysis plan with the comparison that could come out the other way; the rival is a confound (selection, leakage, a shortcut feature) that produces the same pattern. |
| Coherence (7) | T1 on the measurement; T3 degenerate inputs on the metric (empty groups, ties, a constant predictor). |
| Review | Controlled-diagnostic design (RS `controlled_diagnostic_design`): one confound manipulated at a time, an independent oracle, limits of extrapolation from synthetic settings. |
| Deliverable | A report with scoped findings, or a plan for the measurement. |

Seeds: [patterns INDEX](../patterns/INDEX.md) `controlled_diagnostic_design`, C02. Watch for: the evaluated model grading itself; a correlation reported as a mechanism.
