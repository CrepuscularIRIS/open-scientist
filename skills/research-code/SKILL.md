---
name: research-code
description: Use when a research premise depends on implementation, data, evaluation logic, logs or environment facts. Open Scientist 0.3 entry kept for compatibility; it forwards to the open-scientist study loop.
---

# research-code (forwards to open-scientist)

Since Open Scientist 0.3 this skill is an entry point, not a separate workflow. Use the [open-scientist skill](../open-scientist/SKILL.md): start or resume a study (`forge next --project "$PWD" --study <slug>`). When the study reaches a `propose` step, the `diagnose` action is the one this request usually needs. The study proposes it only if the evidence says it is the next useful step.

The full method text of this skill is unchanged at [references/methods/actions/code.md](../../references/methods/actions/code.md). The study's `diagnose` prompt follows it.
