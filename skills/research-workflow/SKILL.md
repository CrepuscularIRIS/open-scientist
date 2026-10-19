---
name: research-workflow
description: Use when start or resume a research project, choose the next research action, or run research autonomously (auto, 自动研究, 持续推进). Open Scientist 0.3 entry kept for compatibility; it forwards to the open-scientist study loop.
---

# research-workflow (forwards to open-scientist)

Since Open Scientist 0.3 this skill is an entry point, not a separate workflow. Use the [open-scientist skill](../open-scientist/SKILL.md): start or resume a study (`forge next --project "$PWD" --study <slug>`). When the study reaches a `propose` step, the `propose` action is the one this request usually needs. The study proposes it only if the evidence says it is the next useful step.

The full method text of this skill is unchanged at [references/methods/actions/orient.md](../../references/methods/actions/orient.md). The study's `propose` prompt follows it.
