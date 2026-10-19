> Method text carried from Open Scientist 0.2 (`skills/research-report/SKILL.md`), kept whole. In 0.3 the study loop ([prompts/study/](../../../prompts/study/)) decides when this method runs, and records are written through a study commit ([contracts](../../../prompts/study/contracts.md)), not through the 0.2 MCP write tools or the auto-mode workflow record. Where this text names those, follow the commit contract instead; the method itself is unchanged.

# Research report

A report is a view of exact research records, with claims limited by available evidence.
It can discover new problems and return them to the right skill; rendering does not resolve them.
Use this skill for a short direction card as well as a detailed technical overview.
Produce the requested output, not a mandatory collection of five cards.

## Entry and scope

Use when the user wants an idea made understandable or an investigation summarized.
Use when translating a technical candidate without changing its mechanism.
Use when experimental results need a conclusion with appropriate scope.
Use when an overview must preserve competing explanations, objections, and next decisions.
Use when a card rewrite exposes an undefined quantity or a factual contradiction.
For generation of a new mechanism, use research-ideate or research-construct.
For execution of an experiment, use research-test after a specific plan exists.
For a choice about future effort, use research-decide; the report supplies its evidence.
A report request alone does not authorize new training, recurring monitoring, or publication.

## Read the governing contracts

Read [research-contract](../../contracts/research-contract.md) for Q/H/T/View semantics.
Read [record-api](../../../docs/record-api.md) before persisting any new record.
For independent-review output, use [review-context](../../contracts/review-context.md).
Use the current user/project root, never the installed plugin directory as research storage.
The record service stores evidence references; it does not verify facts or run experiments.

## Required input and missing context

Identify the requested audience, purpose, format, language, and output location from the task.
Identify the exact project Q, candidate H, and any test T versions discussed.
Retrieve existing records and unresolved feedback with the shared context operation.
Read source materials behind claims you will present as supported or contradicted.
Read the original plan and results before reporting an experiment's interpretation.
Read the full mechanism and relevant review rationale, not only its score or abstract.
Retrieve the strongest applicable counterevidence even from low-ranked or stopped candidates.
Read current user constraints and preserve which constraints are facts versus preferences.
If a source is inaccessible, say what remains unverified; do not substitute model memory.
If the material lacks a precise version, identify this limitation before drawing comparisons.
Do not create fictitious record IDs merely to make a card look complete.
A small supplied idea can be reported without importing an entire literature collection.

## Quick routing reference

| Finding during reporting | Action |
|---|---|
| Long or awkward wording, unchanged meaning | Rewrite the requested view; stop after equivalence check |
| Undefined object already present in method | Open a specification issue; research-construct |
| New method proposed by the writer | Remove it from the prose-only edit; propose separately if useful |
| Complete method cannot run in this environment | research-evolve feasibility or research-decide |
| Citation does not support a claim | research-retrieve or research-review for that claim |
| Valid contrary result | Record finding; preserve it; route affected claim for review |
| Results fit only a narrower condition | State actual scope; new broader/narrower hypothesis needs versioned decision |
| Best-case conclusion has little value | research-decide or research-diagnose, not stylistic inflation |
| Human feedback changes the research objective | New Q through research-diagnose/workflow |

## Procedure 1: establish what kind of statement this is

For each main sentence distinguish observation, inference, proposal, prediction, and decision.
An observation names its material or activity source and the conditions under which it arose.
An inference explains the reasoning from observations and which alternatives remain.
A proposal states what could be built; a design description is not a completed implementation.
A prediction is conditional and belongs to the relevant H/T version.
A decision allocates future effort and must not masquerade as scientific validation.
A high score, stable ranking, completed session, or rendered card is not a finding.
Do not turn the absence of retrieved literature into an established novelty statement.
Separate implementation checks, real-environment execution, and scientific effects.
This classification can remain internal when the prose already conveys it clearly.

## Procedure 2: select one useful view

Use the [direction card](../../templates/direction-card.md) for choosing a direction.
Use the [construction card](../../templates/construction-card.md) for technical handoff.
Use the [challenge card](../../templates/challenge-card.md) for scientific objections.
Use the [execution card](../../templates/execution-card.md) for a bounded test handoff.
Use the [decision card](../../templates/decision-card.md) for investment and resumption.
A user may need two views; share the same exact records instead of independently authoring facts.
The five templates are optional audience projections, not five workflow gates.
Preserve stable claim/step IDs when using multiple views so disagreements can be traced.
Keep full equations, logs, and source excerpts in linked material when a short view is enough.
Do not hide an unresolved critical issue in an appendix merely to make the card attractive.

## Procedure 3: construct the evidence spine

Write the concrete question before architecture and tools.
For each main claim, identify its exact H claim ID and supporting finding/material references.
Check evidence direction, target system, measurement, and applicable scope.
List the strongest contrary finding beside the claim it limits.
Preserve distinctions among supported, partial, contradicted, contested, and unknown.
Use not_found, unreachable, and uncited only with their actual retrieval/source meanings.
A material can support one claim and contradict another; no global source truth label is enough.
A failed activity is not automatically a negative scientific result.
A valid counterexample within the stated scope can defeat a universal claim.
One successful demonstration does not prove average improvement or broad generality.
Avoid selecting only top-scored candidates for the evidence spine.
Relevant low-scored alternatives may carry the decisive mechanism objection.
When evidence is missing, report the gap rather than inventing a complete story.

## Procedure 4: expand only what the reader needs

For a technical idea use [expand](../../methods/expand.md).
Retain the problem, why prior methods stop, proposed mechanism, and distinguishing prediction.
Name the actual method objects: inputs, transformation, output, and source of parameters.
Link equations to the step they define instead of placing unconnected equations at the end.
Separate implemented components from proposed or unspecified ones.
Use [implementability audit](../../methods/implementability_audit.md) if the method is underspecified.
An existing definition can be explained; an absent load-bearing design cannot be invented.
If a parameter choice changes the mechanism or its predictions, it requires a candidate revision.
Present environmental feasibility separately from mathematical/specification completeness.
An honest open decision is more useful than a confident fabricated implementation detail.
Do not add a new estimator, normalizer, reward, or hidden oracle to improve the prose.
Do not repeat old factory defaults for GPU days, API cost, fixed paper counts, or model panels.

## Procedure 5: handle conclusion-first and result-first writing

Before experiments, a best-case conclusion is a conditional value test.
State what would matter if the mechanism and predictions were borne out.
Use prospective language such as “if this holds” or “the proposed test would distinguish”.
Do not write fabricated numerical gains or imply a completed experiment.
After experiments, return to the exact prior prediction and the actual result.
Replace hoped-for outcomes with claim-specific findings and the observed scope.
State what changed the next decision and what remained unresolved.
If evidence only supports a narrow subpopulation, identify that subpopulation.
If a new framing is proposed after results, label it as a new interpretation/version.
Preserve the original failed prediction rather than rewriting its history.
Use [companion strategy](../../methods/companion-strategy.md) for the value question.
Use research-decide when the resulting conclusion changes whether the project is worth pursuing.

## Procedure 6: translate and simplify without scientific mutation

Use [derive plain](../../methods/derive_plain.md) for requested register/language changes.
Every assertion in a plain view must derive from the technical source or its visible findings.
Preserve units, uncertainty, negation, comparison conditions, and causal versus correlational wording.
Spell out specialist terms only when they help this audience understand the method.
Do not turn an undefined quantity into an invented default to improve readability.
If translation reveals ambiguity, state it and open a targeted construction issue.
Check the revised view against the original H, not against a second independently generated summary.
Changing language or layout alone does not invalidate experiments or reopen all reviews.
Stop once the requested view is accurate and readable.

## Procedure 7: overview across candidates and feedback

Read the full relevant candidates and review rationales before synthesizing shared weaknesses.
Name shared assumptions and genuinely different explanations rather than forcing a winner.
If rankings are shown, explain their within-comparison preference meaning and observation count.
A strong objection outranks a pleasing ranking when discussing scientific support.
For a recurring issue, retain its evidence, affected subjects, scope, and counterexamples.
Do not promote reviewer agreement into a universal generation rule.
Route a missing method family to research-retrieve and a measurement blind spot to research-diagnose.
Route a failed mechanism to research-construct/research-evolve with the actual defect.
A disagreement that needs a new observation goes to research-test, not another summary vote.
Read human feedback as well as agent summaries; saving it is not consumption.
For adopted feedback create a disposition referencing the exact resulting output records.
For deferred feedback state the missing evidence and leave it unresolved.
A rejected suggestion needs an evidence-based reason; it cannot override a valid user instruction.

## Outputs and persistence

Deliver the requested report/card in a readable project file or directly in the conversation.
Its minimum content is question, current view, decisive evidence, limits, and next decision/action.
Do not force every internal field into the human-facing report.
New source observations become material records with actual source/locator/content.
New scientific findings are assessment findings tied to an exact subject and claim.
Do not record a rhetorical assertion as supported without the required material evidence.
Substantive H changes are handed to research-construct with their delta and affected dependencies.
Use expected_version on updates; after conflicts re-read instead of overwriting another writer.
Feedback dispositions reference actual created outputs; do not invent output records for closure.
If persistence is unavailable, preserve an explicit versioned handoff and say it is not in the store.
Report completion means the requested communication is complete, not that research is validated.

## Branches and stopping

For prose-only requests stop after checking semantic equivalence and presentation.
For a new factual inconsistency, resolve only the source/claim affected or mark it unresolved.
For an undefined mechanism, return a concrete issue; do not begin unrequested implementation.
For an infeasible test, propose the named feasibility handoff and retain the scientific uncertainty.
For a narrow or negative result, state it without forcing a positive contribution narrative.
When new research is required, give the question and minimal evidence needed rather than endlessly rewriting.
When the report is adequate and no new evidence exists, do not rerun an attractiveness panel.
Use [idea quality](../../methods/idea_quality.md) only when the user needs idea diagnosis.
Use [Companion critic](../../methods/companion-critic.md) when impact, timing, advantage, nugget, or narrative needs a diagnostic assessment; keep investment and truth separate.
A low score routes a specific weakness; it does not create a polishing loop.

## Worked example

Input: H1 proposes “aggregate reward across samples”; code contains only an arithmetic mean.
The user asks for clearer wording; a draft adds “normalize by reward uncertainty”.
That normalizer is absent from H1 and code, so remove it from this prose-only revision.
Explain the arithmetic mean faithfully; if the original text needed another definition, mark it open.
A separate low-ranked H0 contains a valid counterexample to H1's universal robustness claim.
Keep that counterexample in the report and limit the claim even if H1 has the highest score.
Write “the present construction does not establish universal robustness”, with the evidence link.
If a new normalizer is worth investigating, propose it separately as H2 through research-construct.
Do not create H2, rerun experiments, or rewrite H1's prior predictions merely to finish the card.

## Common traps

| Trap | Correct response |
|---|---|
| “A polished card needs all details filled” | Surface missing design decisions instead of inventing them |
| “Overview only needs top candidates” | Include decisive contrary evidence regardless of rank |
| “Expected results can stand in for results” | Keep prospective and observed claims distinct |
| “Three independent rewrites improve quality” | Generate requested views from one exact record basis |
| “A source link proves the claim” | Check support direction, scope, and actual content |
| “Feedback was saved, so it was handled” | Record actual disposition and its output references |
| “A low score means rewrite again” | Route the named deficiency or stop without new information |

## Provenance and validation scope

Adapted from ResearchStudio expansion, plain derivation, implementability audit, and IdeaQuality.
The working methods above retain source paragraphs with explicit adaptation notes and archive links.
Companion contributes conditional conclusion-first framing and project strategy.
Co-Scientist contributes full-review reading, contrary-evidence priority, and feedback from overview.
The runtime record contract replaces historical phase artifacts and host-specific commands.
See [authoring replay](../../../evaluations/authoring-reporting.md) for the limited synthetic checks.
These checks do not establish improved scientific outcomes or reliability across real projects.
