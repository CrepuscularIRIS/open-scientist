---
name: research-test
description: Use when a research claim needs a discriminating experiment, a counterexample, a dry run, or interpretation of a finished or failed run. Open Scientist 0.3 entry kept for compatibility; it forwards to the open-scientist study loop.
---

# research-test (forwards to open-scientist)

Since Open Scientist 0.3 this skill is an entry point, not a separate workflow. Use the [open-scientist skill](../open-scientist/SKILL.md): start or resume a study (`forge next --project "$PWD" --study <slug>`). When the study reaches a `propose` step, the `plan_test / run_test / interpret` action is the one this request usually needs. The study proposes it only if the evidence says it is the next useful step.

The full method text of this skill is unchanged at [references/methods/actions/test.md](../../references/methods/actions/test.md). The study's `plan_test` prompt follows it.
