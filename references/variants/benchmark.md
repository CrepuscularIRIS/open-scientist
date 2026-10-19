# Variant: benchmark

A benchmark, dataset or evaluation protocol. ResearchStudio routes this out of scope; here it is a first-class task type.

This variant changes how the protocols in [protocols.md](../protocols.md) apply to this task type. It never switches one off. Seeds below are starting vocabulary; the study's `rubric` and `test_protocol` assets are rebuilt from this field's evidence (see [design](../../docs/design.md) §2–3).

| Protocol | How it applies |
|---|---|
| Falsification (3) | A **validity argument**: (a) construct validity: what capability a high score must require, and a shortcut that would score high without it; (b) contamination: how items could already be in training data, and the check; (c) discriminative power: two systems known to differ must separate, and the rival "it measures something else" must predict a different ordering. |
| Coherence (7) | T3 on the scoring: empty answers, constant answers, answers copied from the prompt must not score well. |
| Review | Coverage gap against existing benchmarks (collision with alias terms: "evaluation suite", "test set", "leaderboard"), longevity (saturation risk), adoption path, licensing of sources. |
| Expectations | Domain expectations about baselines become: which reference systems must be run on it. |
| Deliverable | A plan with the validity checks as tests, or verified execution of a pilot. |

Seeds: Companion survey/benchmark notes; Co-Scientist correctness reinterpreted as label validity. Watch for: a benchmark whose top system is a lookup; items scraped from the evaluated systems' training sources.
