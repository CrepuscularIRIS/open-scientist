> Method text carried from Open Scientist 0.2 (`skills/research-decide/SKILL.md`), kept whole. In 0.3 the study loop ([prompts/study/](../../../prompts/study/)) decides when this method runs, and records are written through a study commit ([contracts](../../../prompts/study/contracts.md)), not through the 0.2 MCP write tools or the auto-mode workflow record. Where this text names those, follow the commit contract instead; the method itself is unchanged.

# Research decide

Choose the next justified investment from current evidence, constraints, and alternatives.
A decision about effort is different from a finding about what is scientifically true.
Keep both visible: a promising idea may be parked, and a cheap test may target an uncertain idea.
The output is a concrete decision and its reason, not a score that pretends to settle the science.

## Entry and scope

Use for initial commitment, mid-project triage, a pivot, or a proposal to stop.
Use after a meaningful new finding changes the case for continuing.
Use when data access, compute, collaboration, timing, or the user's priorities change.
Use when two explanations remain plausible but only one can be tested first.
Use when a parked project has a potentially satisfied revisit condition.
Do not run this skill after every minor edit or automatically after every report.
Do not turn an idea-score threshold into a mandatory continue/kill gate.
Do not initiate a watch process because a strategy document contains a watch list.
The skill can recommend execution; execution still follows the task's existing authorization.

## Governing contracts and references

Read [research-contract](../../contracts/research-contract.md) for exact Q/H/T semantics.
Read [record-api](../../../docs/record-api.md) for real payload names and version checks.
Read relevant parts of [companion strategy](../../methods/companion-strategy.md).
Use [idea quality](../../methods/idea_quality.md) only for diagnostic uncertainty.
Use [Companion critic](../../methods/companion-critic.md) when impact, timing, advantage, nugget, or narrative needs a diagnostic assessment; keep investment and truth separate.
Use [decision card](../../templates/decision-card.md) if a reusable handoff helps.
The source strategy heuristics inform judgment; they are not calibrated laws of research impact.

## Inputs: read before deciding

Retrieve current project records and the exact candidate/test versions under discussion.
Read the original user objective and distinguish hard requirements from preferences.
Read the latest decision, its rationale, and any explicit revisit condition.
Read unresolved human feedback and any later changes to constraints.
Read current results, their raw source references, and their actual execution status.
Read the strongest relevant adverse finding, including from stopped or low-ranked candidates.
Read the remaining work, environment facts, and resource estimates with their uncertainty.
Identify realistic alternatives, including a smaller question or doing no more work now.
If a decision hinges on novelty or competition, check the actual available evidence.
If material is missing, list the missing fact rather than inventing a numerical utility estimate.
A previous score, PID, ACTIVE label, or summary cannot substitute for these inputs.

## Decision meanings

| Decision | Meaning | Required practical content |
|---|---|---|
| pursue | Allocate the next bounded action to this line | Exact action, purpose, inputs, authorized resource boundary |
| refine | Repair a named problem before further commitment | Deficiency, what may change, responsible skill, completion condition |
| park | Stop active investment under current conditions | Reason and a checkable condition for reconsideration |
| kill | End this line under the current question/version | Decisive reasons, retained evidence/assets, no implied deletion |

These meanings apply to exact subjects and versions, not to a whole scientific field.
A failed universal claim can be killed while a narrower child hypothesis is considered.
Parking a test for budget does not label its scientific hypothesis false.
Pursuing a test does not label its hypothesis supported.
Refine is not a euphemism for repeated polishing without a specific defect.
Kill preserves history, negative results, and useful code/data; it does not authorize deletion.
A later revision may reopen a line when new evidence or conditions warrant it.

## Procedure 1: identify the decision and its trigger

State what changed since the previous decision, or why this is the first commitment.
Name the question: choose a first test, continue a mechanism, pivot framing, or resume a project.
Keep scientific adjudication separate from resource prioritization.
If the user asks for a scientific winner without distinguishing evidence, say it remains unknown.
You can still recommend which test or investigation to fund first.
If the request is only a status read, report the status; do not manufacture a new phase transition.
If a result is merely an execution failure, diagnose execution before interpreting the hypothesis.
If no material fact or goal changed, reuse the prior decision with an applicability explanation.

## Procedure 2: establish the scientific position

For each load-bearing claim, read its findings, evidence, and scope.
Distinguish contradicted, unsupported, contested, and not yet tested.
A valid counterexample to a universal statement is not canceled by several positive reviews.
A source that could not be read is not evidence that a claim is false.
A negative experiment only applies to the tested conditions and valid measurement assumptions.
A high idea-quality score cannot repair a missing causal comparison.
An Elo preference is not the probability that a mechanism is correct.
If a conclusion changed after observing results, preserve the earlier prediction and H version.
State what scientific uncertainty would remain even if the next action succeeds.
Do not reopen every past review when only one evidence relationship changed.

## Procedure 3: apply the relevant strategy mode

For project triage, compare current results, remaining work, motivation, and recent changes.
For comparative advantage, inspect actual skills, access, domain knowledge, and available collaborators.
For impact, explain whose scientific or practical decision the result would change.
For opportunity cost, compare credible alternatives and their switching costs.
For competition, distinguish verified overlap from forecasts about what another group may do.
The researcher's interest affects capacity and preference; it is not evidence of scientific truth.
Do not equate community popularity with an important unsolved problem.
Do not discard useful reusable assets when excluding sunk effort from the decision.
Do not prefer a new idea merely because it feels fresher than the current project.
Use source-backed arguments rather than unsupported months-until-scooped predictions.
A strong local contribution may be worth doing even if it is not a large paper.
The user's objective may be understanding, reproduction, infrastructure, or a measured improvement.
Do not silently substitute publication prestige as the goal.

## Procedure 4: test the value proposition with appropriate tense

Before testing, ask what the best-case conclusion would mean if it held.
This is a conditional value probe, not permission to invent results.
State the nugget clearly without forcing unrelated mechanisms into one slogan.
After results, assess value using the supported conclusion and its actual limits.
A weak conclusion can mean the problem is poorly chosen or the mechanism misses it.
It can also mean the evidence is incomplete; do not confuse that with an unimportant question.
If the issue is only wording, use research-report and retain the investment decision.
If the target is wrong, route to research-diagnose with the precise mismatch.
If the mechanism is weak, route to research-construct or research-evolve with a named defect.

## Procedure 5: choose the next information-bearing action

Identify the most consequential uncertain assumption that can presently be investigated.
Compare what each possible action would distinguish, not only how easy it is to run.
Prefer a cheap discriminating check before a large campaign when the check is informative.
Name the observation, intervention or comparison, expected divergence, and stopping condition.
Use research-test for a concrete test plan and research-code for required implementation.
A test plan must cite its H and the real constraints; unknown budget remains unknown.
A cheap proxy states the assumptions under which it informs the original question.
If reducing cost erases discrimination, report the test as uninformative and consider park.
If the claim must change to become testable, create a candidate revision rather than hiding the change.
An inability to run a test here does not establish that the mechanism is impossible in principle.
Do not promise a universal one-to-two-week timeline; estimate from actual dependencies.
Do not start an expensive action merely because the recommendation is pursue.

## Procedure 6: handle alternatives without a forced winner

List competing explanations against the same observations and information conditions.
State which predictions differ and which observations both can explain.
Account for cost, availability, and information gained by the next action.
If a cheap test only addresses one explanation, state what it says about the other.
Tie or unresolved is an acceptable scientific result.
A selected next test is an investment preference, not a discovery of which theory is true.
Keep plausible nonselected hypotheses available unless evidence defeats them.
When selecting a candidate pair for a review, preserve known adverse facts and hide old scores if appropriate.
Use research-review for a specific scientific dispute, not another broad attractiveness vote.
A pairwise ranking cannot replace a missing observation.

## Procedure 7: resume only from current evidence and authorization

For a parked project, read its reason and check its specific revisit condition.
Read the latest user constraints before considering any historical plan.
If a historical process is relevant, verify its present identity with a read-only check.
A PID may have been reused; match process start time, command, work directory, and job record.
A remote log or old ACTIVE flag is not current runtime evidence.
If the environment is unreachable, say unverified and preserve the pause/park state.
Do not restart, kill, or duplicate a job merely to reconcile stale metadata.
Identify which artifacts remain reusable and which dependencies changed.
Resume only the work within the user's currently authorized scope.
If new resource commitment is outside that scope, prepare the concrete action and required decision.
A revisit condition is not a recurring automation; create monitoring only when explicitly authorized.

## Procedure 8: persist decision and actual feedback consumption

Record an assessment decision for the exact subject with pursue/refine/park/kill and rationale.
Add material evidence references when they support the decision's factual basis.
For park include a checkable revisit_when condition; avoid “when things improve”.
Record any scientific finding separately with claim, evidence, judgment, and scope.
Do not put unsupported scientific assertions into a decision as a substitute for findings.
When user feedback changes Q, H, T, or the decision, create the appropriate output first.
Then record its adopted/superseded disposition with exact output references.
Deferred feedback remains unresolved and names what is needed to address it.
A rejected agent suggestion has a reason; user requirements are not optional preferences to dismiss.
Reading feedback alone does not establish that it was implemented.
Use expected_version and re-read after conflicts to preserve another agent's work.
If storage is unavailable, leave a versioned handoff and disclose that it is not persisted.

## Outputs

Lead with the concrete investment decision and the subject version.
Give the strongest reason for it and the strongest reason against it.
Summarize scientific status separately from feasibility and strategic value.
Give one bounded next action, named refinement, revisit condition, or salvage plan.
Link the evidence needed to understand what changed since the last decision.
State uncertainty that could reverse the decision and how it would be resolved.
Provide the relevant feedback dispositions when this was a response to new input.
Use a compact decision card; no compulsory score table or generated abstract is required.

## Bridges and termination

| Trigger | Next skill or stop |
|---|---|
| Missing prior work or uncertain overlap | research-retrieve with the specific claim |
| Misidentified target or unobservable outcome | research-diagnose |
| New cross-field approach worth checking | research-ideate with the mapping question |
| Undefined method or revised mechanism | research-construct |
| Need a code-level fact or repair | research-code |
| Discriminating observation available | research-test within authorization |
| Contested evidence or counterexample validity | research-review |
| Plausible mechanism with infeasible test route | research-evolve feasibility |
| Pure presentation problem | research-report; no scientific restart |
| No new information or useful action | Preserve uncertainty and park/stop the current loop |

## Worked example

Two explanations A and B fit the current observations; A's proposed test is cheaper.
Select A's test first only if its outcomes provide useful discrimination or eliminate a major uncertainty.
Record pursue for that bounded investigation, not “A is scientifically correct”.
If the test cannot separate A from B, keep both explanations unresolved and redesign or park.
A later user constraint removes the necessary data access while an old PID says running.
Read the existing park decision and verify current process identity before proposing any resumption.
The new constraint may justify continued park; it does not authorize a replacement training job.
Retain both candidates, adverse evidence, and the exact condition required to revisit.

## Common mistakes and provenance

Do not confuse optimism with support, a budget with truth, a score with a finding, or a PID with a job.
Do not use sunk effort, a polished abstract, or review majority to erase valid counterevidence.
Do not promise automatic follow-up merely because a watch list or revisit condition was written.
Do not turn refine into a loop that changes only the prose while the core issue remains.
This skill adapts Companion strategy, Frame/Decide, and explicit risk-first action selection.
It incorporates Co-Scientist's separation of ranking preference from correctness and feasibility operators.
It uses RS's idea-quality decomposition diagnostically instead of as a mandatory score gate.
Source paragraphs, adaptation notes, and archive links are in the linked method references.
See [authoring replay](../../../evaluations/authoring-reporting.md) for bounded synthetic checks and limits.
