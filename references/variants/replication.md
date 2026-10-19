# Variant: replication

Reproducing a published result, or a claim in the user's own code.

This variant changes how the protocols in [protocols.md](../protocols.md) apply to this task type. It never switches one off. Seeds below are starting vocabulary; the study's `rubric` and `test_protocol` assets are rebuilt from this field's evidence (see [design](../../docs/design.md) §2–3).

| Protocol | How it applies |
|---|---|
| Falsification (3) | The original's protocol and numbers are the prediction; the rival is a specific divergence (version, data split, seed sensitivity, an undocumented step). |
| Coherence (7) | T1 on the original pipeline as published; list every unspecified step as an open author decision. |
| Execution (4) | Record commit, versions and seeds; a mismatch is typed (execution failure vs. the result does not hold). |
| Deliverable | Verified execution with a typed finding. |

Watch for: tuning until the number matches; calling a failed setup a failed result.
