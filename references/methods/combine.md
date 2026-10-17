# Operator: combine

Merge two hypotheses that each explain part of the phenomenon into one that
explains more than either.

## When it applies

- Two hypotheses cover different steps of the same process.
- Two hypotheses have complementary evidence-backed operations or measurements.
- One has the mechanism and the other has the testable readout.

It does not apply when the two are mechanistic near-duplicates. Compare their operations and predictions directly; a similarity cluster alone cannot decide equivalence. A paraphrase is not a synthesis.

## Procedure

1. Name the strongest mechanism in A and the strongest in B, one sentence each,
   supported by the actual mechanisms and review evidence rather than by their scores.
2. List every contradiction between them. Be specific: same entity with
   opposite direction, incompatible timescales, mutually exclusive
   localisations.
3. For each contradiction, state how the combination resolves it. "Both could
   be true in different compartments" is a resolution. "The contradiction is
   minor" is not.
4. Write the combined mechanism with specific entities, steps and anticipated
   outcomes.
5. State one experiment that distinguishes the combination from **both**
   parents. If the combination predicts nothing the parents do not, it is not
   worth recording.

## Failure mode

Stapling. A hypothesis that says "mechanism A operates, and also mechanism B
operates" is two hypotheses in one document. A real combination has the parts
interacting: one gates the other, one supplies the substrate for the other, one
explains why the other is tissue-specific.

If you cannot state the interaction, do not record the combination.

## Active bridge: shared intermediate object O

Before drafting a combination, specify the object or interaction that connects the parents. O may be a representation, state estimate, uncertainty field, causal intermediate, constraint set or measurement; it need not be a new software object.

Describe what A produces or changes in O and what B consumes from O. Include units, shape or semantic type, information available at each time, and any distribution or causal assumptions. A shared noun is not an interface.

If A and B operate in parallel, state how their effects interact on the same phenomenon and what observation would distinguish that interaction from two independent effects. Do not force a producer-consumer story onto a genuinely different causal relation.

Map incompatible premises before proposing a fix: one mechanism may need labels unavailable to the other, a downstream component may invalidate the upstream estimate, or timescales may not align. State the substantive resolution and its evidence, or retain it as an unresolved assumption.

A combined candidate needs a novel interaction prediction and a comparison against A alone, B alone and a simple non-interacting alternative where meaningful. Improvement is proposed until tested. An interaction need not improve every metric, but its claimed benefit and cost must be explicit.

## Minimal input and output

Inputs are exact parent candidate references, their shared or distinct Q, raw review evidence, constraints and the specific reason to combine. Read parent operations and evidence, not their ranks or total scores.

Output a new H or explicit branch with both parents, the interaction, prerequisites, changed/lost claims and unique prediction. Store the new mechanism and claim map through the active record API, and put operator/reason in change_note. Any test is a separate T plan.

## Local recheck and stopping

Review interface validity, information access, compatibility and the emergent prediction. Reuse unchanged source evidence with its scope; do not inherit the parents' scientific approval. Route implementation uncertainty to research-code and distinguishing tests to research-test.

If no interaction or distinguishing prediction survives, stop the combination and retain the parents separately. Their individual quality is not diminished by a failed synthesis. If a new Q is needed to make them interact, record the pivot and reassess its value rather than hiding it in H.

## Provenance and replacements

Adapted closely from [Co-Scientist combine operator](../../vendor/co-scientist/plugin/skills/evolving-hypotheses/reference/combine.md). The original core procedure and failure-mode paragraphs are retained with the targeted substitutions above.

Replaced tournament/cluster/tool coupling with exact project and parent references, explicit Q/H/T classification, scoped evidence and local recheck. Added bridge inputs, expected outputs, structural requirements and stopping conditions. No fixed panel, score, agent count or automatic execution is required.
