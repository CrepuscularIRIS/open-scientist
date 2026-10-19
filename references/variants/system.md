# Variant: system

A system: software or hardware that does a known job faster, cheaper, larger or more reliably.

This variant changes how the protocols in [protocols.md](../protocols.md) apply to this task type. It never switches one off. Seeds below are starting vocabulary; the study's `rubric` and `test_protocol` assets are rebuilt from this field's evidence (see [design](../../docs/design.md) §2–3).

| Protocol | How it applies |
|---|---|
| Falsification (3) | An **equal-hardware workload baseline**: the same machine, the same workload, the simplest competent alternative (a naive scheduler, an off-the-shelf cache); the prediction is a throughput, latency or cost direction under a stated workload. |
| Coherence (7) | T3 resource exhaustion and limits (queue full, cold start, worst-case input); T5 naive system under the same constraints. |
| Review | Deployment realism (is the workload representative), what is traded away (consistency, accuracy, memory), whether the gain survives at the next scale. |
| Environment | The `environment` asset (what the machine actually has) bounds the test; anything beyond it is a person's authorization. |
| Deliverable | A plan with a benchmarked baseline, or verified execution of a small run. |

Seeds: RS `architectural_operator_substitution`, `heterogeneous_decomposition`. Watch for: comparing against an unoptimized baseline; one hand-picked workload.
