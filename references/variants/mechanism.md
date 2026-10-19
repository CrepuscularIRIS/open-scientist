# Variant: mechanism

A new method or mechanism: an operation that changes what a system computes or how it behaves.

This variant changes how the protocols in [protocols.md](../protocols.md) apply to this task type. It never switches one off. Seeds below are starting vocabulary; the study's `rubric` and `test_protocol` assets are rebuilt from this field's evidence (see [design](../../docs/design.md) §2–3).

| Protocol | How it applies |
|---|---|
| Falsification (3) | One `load_bearing_variable`; a negative control that intervenes on it (randomize, permute, ablate its producer) and predicts the **downstream metric** returns to the baseline arm. "Set X to 0, X becomes 0" tests a definition. A positive control is recommended. |
| Coherence (7) | All of T1–T5 ([coherence_trace](../methods/coherence_trace.md)); T2 runs a stdlib script; T5 builds the naive version independently, simpler and under the same constraints. |
| Review | Operation-applied (does a named step perform the cited move under its conditions), card failure modes, anti-patterns within a venue-year stratum, two-channel collision, the naive-baseline branch (false premise / naive suffices / disbelieved). |
| Retrieval | Closest prior mechanisms read in full; older method families that attacked the same residue (lineage, awareness only). |
| Deliverable | A plan (H + test + review) or an idea card through `idea_run`. |

Rubric seeds: [companion-critic](../methods/companion-critic.md) seven dimensions; [review-rubric](../methods/review-rubric.md). Watch for: regression to a superseded method; stapled compositions with no intermediate object; numbers without provenance.
