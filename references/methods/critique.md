# Mechanism critique and corpus-anchored audit

## Purpose and exact inputs

This method produces an evidence-anchored audit on the current candidate. It emits findings and concrete revision directions; it does not silently revise the candidate while judging it. Separate attack identification from attack resolution so the reviewer cannot answer its own objection by changing the method under review.

Read the exact candidate version, its problem version and constraints, original code or equations when relevant, closest prior-work passages, applicable failure lessons, and all material counterevidence. A repaired candidate is canonical only when its change is recorded; reading an older raw candidate can silently drop the repair.

For independent review, do not read a previous trace narrative, total score, or recommendation. Self-contained executed findings still reach the reviewer: quoted step, script or code location, inputs, output, modeling assumptions, reading dependence, and scope. These are evidence, not a prior vote. Each relevant finding requires an explicit response.

A pattern or subpattern is optional diagnostic vocabulary. If a candidate names a pattern, read the actual tactical move and failure mode before evaluating it. If it does not name a pattern, inspect its mechanism directly; there is no obligation to classify the candidate before review.

## 1. Failure-lesson check

Read the relevant tactical failure mode and the paper-agnostic reject lessons. Quote the particular lesson being used, then state which concrete candidate step would trigger it and why. A generic resemblance to an unsuccessful paper is insufficient.

For each lesson, distinguish:

- Not applicable: its premises are absent in this setting.
- Relevant warning: the same risk could occur, but it has not been established here.
- Instantiated defect: the actual candidate satisfies the conditions of the failure, with evidence.
- Addressed: the candidate's operation or test delivers the mitigation substantively.

The legacy audit treated any matched reject lesson as a hard abandon rule. Here it is a hypothesis about a failure mode. A direct contradiction may refute an affected claim; a corpus tendency does not prove this candidate fails.

A lesson's source, the observed defect, and the research decision remain separate records or clearly separated reasoning. Do not turn “a reviewer dislikes this pattern” into a scientific finding.

## 2. Tactical application check

If a method deliberately uses a tactical pattern, identify the specific verb or operation that defines it, not the parent pattern's generic gist. Cite the specific mechanism step that performs that operation.

A clean pattern citation does not prove its card was read, and reading the card does not prove the mechanism performs the move. Judge the mechanism against the tactic, not the citation string.

When examples come from another domain, evaluate the abstract operation and its prerequisites rather than surface resemblance. An operation may transfer while the original entities do not. Conversely, matching words can conceal incompatible information access or a different causal role.

If the mechanism works but the pattern label is wrong, repair or remove the label. Do not distort a sound method merely to fit a taxonomy. If the missing tactic was the only stated reason the method solves the bottleneck, record that missing link and route to research-construct or research-evolve.

## 3. Composition and anti-pattern check

List the actual components and their interactions, including a component hidden inside another step. Evaluate substantive delivery, not keyword presence: does the candidate produce the artifact or contrast the mitigation requires?

For a proposed combination, name what one component supplies to another, what conditions make that transfer valid, and what new prediction depends on the interaction. Components that each sound useful can still be unrelated.

A mitigation is not delivered by naming it in the card. Locate the artifact, dataflow, experiment, or argument that implements it. If the mitigation is only planned, label it planned.

A single complete mechanism needs no ornamental second pattern. A multi-component mechanism needs an account of why the interaction matters, but not a quota of patterns or cards.

## 4. Paper-pointed threat

Name the closest verified prior work and state what specific result makes the candidate's contribution stand or fall. Compare task assumptions, available information, operations, guarantees, measurement, and scope.

Use both the candidate's own terminology and other communities' names for the same mechanism. Alias-channel hits may be older by design: do not discount a same-mechanism ancestor for being several years old.

A threat can be:

- Equivalent mechanism under the same relevant assumptions.
- A stronger known construction that subsumes the proposed contribution.
- A related operation whose assumptions or information differ materially.
- A possible overlap that needs body-level or code-level inspection.
- No threat found within the stated search coverage.

Write the concrete difference and evidence, not only an overlap score. The count of matching dimensions is not a scientific novelty level. Zero retrieved papers does not establish novelty.

If a mechanism resembles a named family from memory that retrieval missed, name the family and useful vocabulary as a search lead. Do not cite remembered titles, authors or dates as verified facts. That concern routes to research-retrieve; it does not become a hard verdict before verification.

Exact prior coverage limits the claimed novelty, but it need not kill the entire project. Reproduction, empirical boundary discovery, or a meaningful constraint change may still be worth considering through research-decide.

## 5. Discriminating-test check

Use the single definition in [falsification_reaudit](falsification_reaudit.md). Do not copy a reduced version of it here or introduce a second testability rule.

Record which part of that definition is answered, which remains unclear, and what minimal change would make the test informative. A test-plan deficiency and a refuted mechanism are different findings.

## 6. Executed findings and rebuttal

For every relevant contrary finding, identify the precise claim and decide whether the evidence remains applicable. A reviewer may challenge executed evidence, but the challenge must name a checkable flaw: formalization contradicts the quoted step, arithmetic is wrong, or the instance violates an originally stated premise.

Re-reasoning about what the mechanism “should” do does not refute its observed behavior. A charitable reading only resolves a reading-dependent finding if it is supported by the actual specification. A finding robust to both readings cannot be dismissed by choosing one.

A single valid instance refutes a universal statement covering that instance. It does not establish prevalence in the real population. A synthetic positive result is similarly not a performance estimate.

If a counterexample is contested, use [refutation_recheck](refutation_recheck.md). Preserve the evidence while it is unresolved. If it stands, constrain the affected claim and name what would be required to repair it; do not declare every other project claim false.

## 7. Output and routing

For each consequential issue, produce:

- Exact Q/H/T reference and target claim.
- The source or execution evidence actually inspected.
- The finding, its scope and uncertainty.
- Whether the issue is specification, mechanism, evidence, novelty, test design, or investment.
- What change could address it and which dependencies that would affect.
- What should be preserved from the candidate or its experiment.

Persist claim-scoped findings through the shared record API; use the active assessment schema, not the legacy audit JSON. An untested but plausible step is unknown, not automatically supported.

Route a field-level correction to a scoped revision. Route a changed mechanism to research-evolve, a changed problem to research-diagnose, missing prior work to research-retrieve, and a non-discriminating experiment to research-test. Return investment questions to research-decide.

A finding only opens the smallest necessary loop. Repeat when new evidence or a genuinely different operation makes another attempt informative. Stop when the question is answered, the scope limit is explicit, or no new information can be obtained within the authorized work.

## Provenance and replacements

Adapted from [ResearchStudio critique.txt](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/critique.txt), especially inputs and checks at source lines 3–12, 55–114 and evidence disposition at 117–184.

Preserved near-original reasoning: canonical candidate, executed evidence outranks unsupported reassurance, tactical application versus correct citation, substantive mitigation, older alias mechanisms, and independent audit versus revision.

Replaced mandatory five-check gate and hard-floor abandonment with question-scoped findings. Removed rendering rules, fixed Phase directories, mandatory taxonomy, permanent compute-budget locking, and one-shot global verdicts. Falsification now has one shared definition; counterexample logic explicitly distinguishes universal and empirical claims.
