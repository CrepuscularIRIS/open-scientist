---
name: research-construct
description: Use when a diagnosed research problem needs a concrete, falsifiable mechanism. Open Scientist 0.3 entry kept for compatibility; it forwards to the open-scientist study loop.
---

# research-construct (forwards to open-scientist)

Since Open Scientist 0.3 this skill is an entry point, not a separate workflow. Use the [open-scientist skill](../open-scientist/SKILL.md): start or resume a study (`forge next --project "$PWD" --study <slug>`). When the study reaches a `propose` step, the `construct` action is the one this request usually needs. The study proposes it only if the evidence says it is the next useful step.

The full method text of this skill is unchanged at [references/methods/actions/construct.md](../../references/methods/actions/construct.md). The study's `construct` prompt follows it.
