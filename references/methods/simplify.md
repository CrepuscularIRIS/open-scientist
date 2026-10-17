# Operator: simplify

Strip a hypothesis to its load-bearing claim. This is the repair operator: when
a review kills one step, simplify is how you find out whether the rest stands
on its own.

## When it applies

- A review found a fatal flaw in one claim while praising another.
- The mechanism has steps that no prediction depends on.
- The hypothesis is hard to test because it asserts too much at once.

## Procedure

1. List every claim the hypothesis makes, one per line.
2. Mark each as load-bearing or ornamental. A claim is load-bearing only if
   removing it changes what the hypothesis predicts. Be strict: most
   hypotheses carry two or three load-bearing claims and a lot of scaffolding.
3. Propose removal of ornamental items. For a contradicted load-bearing claim,
   explicitly record its removal as a changed hypothesis and preserve the original finding.
4. State what is left as one sentence at the top of the full text.
5. Re-derive the mechanism and the anticipated outcomes from that sentence
   alone. They must still be specific. If they collapse into vagueness, the
   claim you deleted was doing the work and the hypothesis does not survive
   simplification. Say so rather than recording a hollow version.
6. Propose an experiment that is easier to run on the simplified version than
   on the original, and say why it is easier.

## Failure mode

Simplifying into a truism. "The microbiome affects inflammation" is simple,
testable in principle, and worthless. The test is whether the simplified claim
still discriminates against the obvious alternative.

The second failure mode is quiet deletion: dropping the claim a review attacked
without saying you dropped it. Always include a "Changes from parent" section
naming what was removed and why.

## Active bridge: expose losses before rewriting

Make a dependency list from each component or premise to its claimed consequence. “Ornamental” means no needed prediction or implementation behavior depends on it under the stated scope; it does not mean the prose is long or unfamiliar.

For each removal, state whether it eliminates an operation, a parameter, an assumption, a claim, or only wording. Removing a load-bearing part creates a changed H, and sometimes a changed Q. Removing an explanation from a card while leaving the algorithm unchanged is merely View work.

A repair may retain an instrument, control or measurement after its original explanation fails. Preserve why it remains useful and what it no longer establishes. This salvage is a legitimate outcome, but it is not evidence the parent mechanism survived.

Do not silently narrow a universal claim to exclude a counterexample and describe the parent as fixed. Record the old contradiction and the new scope. If the narrower claim no longer answers the original problem, return that choice to research-diagnose or research-decide.

## Minimal input and output

Inputs are the exact parent, claim dependencies, motivating evidence or constraint, and the allowed scope of simplification. Include the original adverse result, not only the author's preferred correction.

Output an explicit change list: retained operations/claims; removed items and reasons; lost capability or coverage; remaining discriminating prediction; and next check. Write an H revision or branch with parent references when mechanism or scientific scope changes. View-only shortening goes to research-report.

## Local recheck and stopping

Recheck the consequences that depended on removed items, the surviving test's discrimination, and the relevance of the narrowed benefit. Preserve unaffected raw observations and sources. The child does not automatically inherit either the parent's rejection or approval.

If removing a component exposes an undefined step, do not fill it with an invented default. Return to construction. If the result says only that a broad system affects another broad system with no distinct prediction, stop; the proposed simplification has become a truism.

## Provenance and replacements

Adapted closely from [Co-Scientist simplify operator](../../vendor/co-scientist/plugin/skills/evolving-hypotheses/reference/simplify.md). The original core procedure and failure-mode paragraphs are retained with the targeted substitutions above.

Replaced tournament/cluster/tool coupling with exact project and parent references, explicit Q/H/T classification, scoped evidence and local recheck. Added bridge inputs, expected outputs, structural requirements and stopping conditions. No fixed panel, score, agent count or automatic execution is required.
