---
name: research-retrieve
description: Use when research needs related work, a missing source, a cross-field mechanism, a baseline or evidence about a novelty claim. Open Scientist 0.3 entry kept for compatibility; it forwards to the open-scientist study loop.
---

# research-retrieve (forwards to open-scientist)

Since Open Scientist 0.3 this skill is an entry point, not a separate workflow. Use the [open-scientist skill](../open-scientist/SKILL.md): start or resume a study (`forge next --project "$PWD" --study <slug>`). When the study reaches a `propose` step, the `retrieve` action is the one this request usually needs. The study proposes it only if the evidence says it is the next useful step.

The full method text of this skill is unchanged at [references/methods/actions/retrieve.md](../../references/methods/actions/retrieve.md). The study's `retrieve` prompt follows it.
