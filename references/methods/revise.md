# Scoped revision against a canonical research object

Apply an explicit revision direction as a delta against the current canonical object. This action does not quietly re-judge the review, propose unrelated attacks, search a new literature corpus, or rewrite the entire candidate to sound stronger.

Separate identifying a problem from resolving it. The review names a claim, evidence and defect; the revision states what actually changes to address it. If the proposed fix is mistaken or outside the user's scope, surface that issue and return it for review rather than blindly implementing it or silently ignoring it.

## Why a delta matters

The original ResearchStudio workflow asked the model to reproduce a large candidate with a few fields changed. Most of that payload was unchanged text, which wasted context and risked dropping prior repairs. Its later patch-only contract preserved untouched content and delegated merging to deterministic code.

Retain that principle: show the smallest semantic change and its dependencies, and apply it to the exact canonical parent. The shared record service is not a field patch merger. The host must read the current record, apply the intended changes, then submit a valid complete payload with expected_version; history preserves the old version.

Do not submit a legacy `applied_revisions` object to the current API or assume the backend knows which scientific fields may change. A compact human-readable delta can accompany the schema-valid record as rationale/change_note or a material.

## Inputs

- Exact project, candidate and applicable test references.
- The motivating finding or feedback, with original evidence.
- A proposed change direction and permitted Q/H/T/View scope.
- Current code/specification and previously applied repairs that must survive.
- User constraints, relevant source uncertainty, and any unchanged scientific commitments.

The canonical parent is the actual latest applicable object, not whichever file has the most familiar phase name. Check concurrent changes and exact references before writing. Re-read after a version conflict and merge facts deliberately; never force overwrite another writer.

## Classify the scope

| Scope | Example change | What to preserve or disclose |
|---|---|---|
| Specification repair | Define an already intended input shape consistently with code | Cite the basis; if the operation was not defined, expose the new design choice |
| Mechanism revision H | Replace an invalid selection rule or add a required normalizer | Parent claim, original evidence, changed operations, affected predictions |
| Source/support correction | Correct a citation or weaken an unsupported attribution | Actual source passage and dependent conclusion changes |
| Test revision T | Add a control or change an unexecuted measurement plan | Fixed H, comparison purpose and existing controls |
| Problem revision Q | Change setting, question or measurement target | Old problem and why the new one is different |
| View edit | Clarify wording without changing Q/H/T | Same operations, assumptions, claims and evidence scope |

A one-word edit can change H; a long explanation can remain View. Classify by meaning. Do not add a new mechanism inside a prose-only task.

## Procedure

### 1. Read the motivating issue

State which finding the revision addresses and what success would look like. If the finding cites a failure lesson, inspect the relevant passage rather than copying every pattern card into context. If it cites an execution, retain the original instance, script/configuration and output.

An upheld obstacle should become a positive requirement on the next mechanism: what capability, signal or contrast must it supply? Name available and excluded sources of that capability. Rewording a failed explanation does not supply the missing resource.

### 2. Propose the smallest coherent change

Prefer an explicit changed operation, corrected claim, added control, or removed unsupported assertion. Preserve unaffected fields and existing repairs. If several fields express the same scientific change, update them coherently and list them together.

The legacy contract required exactly one patch per target. Here each motivating issue must have an accounted-for disposition, but one scientific repair may need several related edits, or several issues may share one justified repair. The requirement is coverage and clarity, not an arbitrary patch count.

If the fix requires a different mechanism, gap or problem, say so. Route to research-evolve or research-diagnose rather than disguising redesign as a tactical wording change.

### 3. Preserve commitments honestly

For an authorized strengthen-only test change, preserve existing experiment elements, claim, metric direction and controls in substance, adding only the specified baseline/control or matching condition. If any item changes, expose it as a different T or H change.

Prospective test plans can change with a reason. Once a test has started, its original plan, input versions and predictions remain historical. A new or rerun test gets a new activity ID. Never rewrite an executed plan to match observed results.

The legacy source permanently locked `compute_budget` and allowed only one falsification rewrite. Those global locks do not apply here. Resource changes are legitimate facts; distinguish them from post hoc weakening of a scientific claim and record their effects on feasibility and investment.

Use [the shared falsification definition](falsification_reaudit.md) whenever a test or prediction changes. It includes numerical provenance; do not maintain a shorter revision-only checklist.

### 4. Check the delta against the parent

Verify that every intended change addresses its named issue, unchanged content is preserved, and no new default, oracle, parameter or scope restriction appeared without explanation. Check the full semantic difference, not only a successful merge or schema validation.

If a change is already satisfied, say why no edit is needed. If a target is impossible or outside scope, record that explicitly and route the unresolved issue. Do not hide a skipped target inside a harmless-looking no-op field.

If mechanism terms or aliases changed, flag the relevant novelty check as needing applicability review. A title typo alone does not invalidate all retrieval; a new operation may invalidate prior comparisons even if the title did not change.

### 5. Record and recheck locally

Write the schema-valid object and exact ancestry, with the change reason. Respond to motivating feedback/findings using a disposition and output reference where adopted or superseded. Deferred issues remain unresolved.

Route only changed dependencies back to review: source/support correction to grounding; a changed operation to coherence and affected novelty; test-control changes to the shared falsification review; Q changes to problem relevance. Preserve unaffected material and explain why prior findings still apply.

Do not assume a child inherits the parent's approval. Do not automatically reopen unrelated experiments. A review in revision mode sees the parent issue, delta and original evidence; it is not labeled independent.

## Minimal output

Produce parent/new references, Q/H/T/View classification, motivating issue, semantic changes, unchanged commitments, lost claims or scope, affected checks and next action. This is a content contract; the durable API schema remains the source of truth.

Stop when the issue has been addressed concretely or its unresolved requirement is clear. Without new evidence or a genuinely different operation, another revision round is likely to rewrite prose rather than improve research.

## Provenance and replacements

Adapted from [ResearchStudio revise.txt](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/revise.txt), particularly audit/revision separation, canonical-parent patching, patch-only rationale, scoped changes and accountable skipped targets.

Retained the detailed reasoning for preserving prior repairs and minimizing unchanged retyping. Replaced Phase paths, legacy patch commands, exact patch-count rules and permanently frozen budget with active record versions, semantic scope and executed-plan immutability. Removed automatic forced retries and whole-pipeline gates. The single active falsification definition is linked rather than duplicated.
