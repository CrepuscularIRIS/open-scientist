# Grounding claims in sources and observations

Machine-generated hypotheses cite real-looking sources that sometimes do not say what the text claims. Check one factual claim at a time before relying on it for a consequential research decision or sharing it as established.

## What gets checked

For each claim:

1. Does the source exist and resolve to the intended work, file or run?
2. Does the quoted passage or observed output actually occur there?
3. Does it support the claim, or merely mention the topic?
4. Does it support the direction and scope: activation is not inhibition, correlation is not causation, mouse is not human?
5. Is the evidence available under the candidate's actual information, timing and measurement conditions?

The direction check catches a frequent failure: a source discussing the right entities in the wrong relation can look supportive when skimmed.

## Sources and provenance

Use exact material references plus source location. For papers record the passage and section/page or stable URL; for code record repository version and the relevant path/lines; for runs record command/configuration, input version, status and raw output location.

An agent having seen a URL in a search result does not mean it fetched the body. A tool returning a file path does not mean its content was inspected. A log reporting completion does not independently verify scientific success.

Review evidence already cited by the candidate, then locate uncited load-bearing assertions. Prioritize unsupported claims and contradictions that could change the next decision, rather than spending equal effort on every background sentence.

## 1. Extract before checking

List claims with source and claimed excerpt before judging them. Checking claims opportunistically while reading prose risks missing assertions without citations, which are often the most consequential.

Use one testable assertion per row. If a sentence asserts identity, causal direction and performance, separate them. Preserve the candidate's exact wording and version so a later correction can be traced.

Claims without a source remain in the list as uncited. For original observations, the source can be an execution material rather than a paper; do not invent a literature citation for a new result.

## 2. Open the source

Fetch each needed source and locate the passage. If a paper is paywalled, try an accessible preprint, abstract or landing page and say which was checked. An abstract may settle identity or a broad result while leaving a detailed mechanism uncertain.

For local evidence, inspect the actual file and its relevant dependencies. Match the run to the claimed code/configuration and distinguish a completed result from a failed attempt. Do not execute costly or external work just because a citation is missing.

If only a summarized excerpt is available, state that limit. The primary source and an agent's summary of it are different evidence levels.

## 3. Judge support

| Judgment | Meaning |
|---|---|
| supported | The inspected source supports this claim in this direction and scope. |
| partial | The source supports a specified weaker or narrower version. |
| contradicted | The source supports an incompatible assertion or the opposite direction. |
| not_found | The inspected source does not contain the claimed passage or support. |
| unreachable | The relevant source could not be accessed well enough to check. |
| uncited | The claim has no identified evidentiary source. |
| unknown | Available material is insufficient to decide the target claim. |
| contested | Relevant evidence or its mapping to the claim remains in conflict. |

Not-found and unreachable are different. A fabricated excerpt on an accessible real page differs from a dead link. Neither by itself proves the scientific claim false.

When the original wording overstates the source, write the actual supported statement. When the source contradicts a load-bearing claim, record that contradiction with its scope; do not automatically mark the entire project rejected.

## 4. Record the finding

Store inspected source content/locator as a material, then an assessment of type finding tied to the exact subject and claim. The material itself has no global support flag: one source may support one claim and contradict another.

Candidate finding claims use the claim key in the referenced candidate version. Put the source's actual excerpt in material content and the support reasoning in the finding rationale. A supported/partial/contradicted finding requires evidence references.

A finding is not an investment decision. If the project should be paused or retired, research-decide records that choice separately with its reason. If a correction responds to feedback or an old finding, record the disposition explicitly.

## 5. Report coverage and next action

Lead with failures that change the conclusion. State the inspected claims and omissions; do not report “sources check out” unless the stated coverage was actually checked. Say which statements are supported and which remain claims or plans.

If the scope was one contested citation, report that scope rather than implying all citations were audited. Stop when the target support relation is resolved, or a precise missing source is identified.

## Rules that preserve evidential meaning

Never mark a claim supported solely from memory. Open the source.
Quote the excerpt found, not the excerpt the candidate asserted, when they differ.
A numerical value needs its units, comparison and conditions, not only matching digits.
A changed citation should reopen its dependent judgment, not automatically every experiment.
An inaccessible source remains a gap even if several agents repeat the same claim.
Use known uncertainty rather than polishing a gap out of the report.

## Provenance and replacements

Adapted from [Co-Scientist grounding-claims](../../vendor/co-scientist/plugin/skills/grounding-claims/SKILL.md), especially original checks, extraction, verdicts and direction rules.

Preserved the detailed claim/source/excerpt procedure and distinction between not-found and unreachable. Extended URL-based grounding to code and execution materials, added scope/identity checks, and used shared findings rather than a Co review/tournament rejection command. Removed fixed database/tool names and automatic whole-hypothesis verdicts.
