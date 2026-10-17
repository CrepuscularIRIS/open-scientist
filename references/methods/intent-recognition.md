# Query intent and cross-community vocabulary

Adapted from ResearchStudio's
[intent-recognition.md](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/intent-recognition.md)
and [Scoop Check, steps 1–2](../../vendor/research-studio/ResearchStudio-Idea/skills/scoop_check/SKILL.md).
Retained reasoning passages below are local source adaptations, not instructions
to invoke the archived workflow or its former providers.

## Input contract

Read the user's original question, the object the project manipulates, any exact
candidate/claim version, known baselines, and the question this retrieval must
settle. Distinguish an explicit hard constraint from the user's proposed answer.
No anchored question: return the concrete missing object or observation to intake;
do not manufacture broad-noise queries merely to produce a literature table.

## Retained query roles

- **BROAD-DOMAIN** — the high-level area, approximately 3–5 words.
  Example: `diffusion model sampling efficiency`.
- **METHOD-SIGNATURE** — the specific technical move, approximately 5–8 words.
  Example: `consistency model knowledge distillation`.
- **MOST-SIMILAR-PROBLEM** — the closest analogue problem, approximately 5–8 words.
  Example: `score based generative model fast inference`.
- **ESCAPE-MECHANISM** — the vocabulary a paper that *already fixed* this bottleneck
  would title itself with. A solver paper names itself by its solution, not by
  the problem, so queries all keyed on the problem can miss the closest prior work.
  Reason about plausible solution families and phrase the query in their vocabulary.
- **CROSS-COMMUNITY ALIAS** — another community's name for the same operation,
  object, objective or guarantee. Change the community, not merely the wording.

These roles are a question checklist, not a fixed four-query quota. Reuse prior
completed searches where their scope still applies. A targeted missing reference
may need only one title or ID lookup. A broad new problem may justify several
complementary keyword queries; each costs part of the bounded request budget.

## Vocabulary ownership: precision without losing cross-field mechanisms

RS asks whether a field is the dominant **owner** of a phrase, rather than merely
whether its researchers use it. This is useful for identifying noisy queries:
`memory augmented`, `world model` or `model predictive control` can retrieve a
much larger neighbouring literature than the target setting.

For the **target-field channel**, anchor generic regimes to a concrete object:
`keyframe`, `tutorial video`, `skill library`, `agent trajectory`, `workflow memory`
or `visuomotor policy`. A query made only of regimes and desirable properties does
not say which object is being changed. Adding more generic adjectives rarely helps.

For the **cross-field channel**, the neighbouring literature may be exactly what
we need. Do not reject its vocabulary for belonging to another field. Attach a
transfer warrant: source object/operation → target object/operation, shared
structure, conditions that must transfer, and one reason the analogy might fail.
A warrant is a hypothesis about usefulness, not verified applicability.

## Named references and remembered papers

Capture every paper, system or model the user names, including bare names without
URLs. Preserve the original wording; use a full title only when known. A nickname
shared by several papers remains ambiguous until the source identity is resolved.
Keep title/author/year/ID guesses separate from resolved metadata.

Model-recall augmentation can surface landmark or differently phrased work missed
by keyword search. Retain the original requirements: **No overlap. Mark provenance.
Stay relevant and modest in count. Flag uncertainty.** An empty nomination list is
honest. A remembered source must not flow downstream as a searched, read or verified
record merely because its title sounds plausible.

## Collision queries

The candidate's own vocabulary covers mechanism, claim and setting. Aliases name
the same mechanism in another vocabulary: a `goal image conditioned scorer for
task completion` might be discussed as a `goal conditioned success detector` or
`goal image reward model`. This is a search lead, not an assertion of equivalence.

Do not paraphrase signature terms and call them aliases. Include old foundations
when the operation depends on them; a fixed recent window is not a novelty test.
Expand only when a specific untested synonym, mechanism family or source gap can
change the comparison. Exhausted queries do not establish absence of prior work.

## Adapter contract and output

The active script accepts plain keywords, not Boolean API syntax. Words within a
query are ANDed; `|` separates queries. Keep the raw question alongside the
actual query strings, each query's purpose and dates, requested sources, outcomes,
limits, and unresolved nominations. Active default sources are local + arXiv.
The host may directly read a task-relevant original source using its available
tools; it must not silently enable a different aggregator.

## Changes from the archived source

- Removed fixed query counts, model-tier mandates and provider-specific dispatch.
- Kept solution vocabulary, concrete-object test, named-reference capture and aliases.
- Split target-field precision from cross-domain transfer instead of excluding the latter.
- Replaced fixed recency windows with the dates required by the actual comparison.
- Preserved nominations as unresolved until identity is checked; identity is separate
  from content support and target applicability.
