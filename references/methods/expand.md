# Expanding a versioned research idea

> Adapted research asset. This file contains the working method, not an instruction to run the archived workflow. Read only the part required by the current task. The [shared research contract](../contracts/research-contract.md) and [record API](../../docs/record-api.md) define persistence and version semantics. Legacy field names below describe optional working documents; they are not accepted record payloads. Candidate, material, activity, and assessment records remain the source of truth. Do not create every document or invoke another skill merely because this reference mentions it.

## Provenance and adaptation

Source: [archived original](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/expand.txt).

Rendering rules are optional advice for the actual requested format, not inherited host requirements. Retained: motivation, why prior work stopped, step-level mechanisms, linked equations, feasibility dimensions, and review responses. Changed: mandatory Phase 4 artifacts become optional views; fixed counts, immutable early budget, and prospective results as facts are removed. Added: exact record versions, contrary evidence, claim-specific result boundaries, and targeted return to construction/testing.

## Working method

Expand an existing, versioned candidate into the requested research view.

The canonical candidate and its evidence precede the view. Expansion can reveal a missing design decision; record that issue and return it to research-construct instead of inventing a method in the card. This step communicates the current IDEA, its motivation, method flow, claims, falsifiability, and feasibility. Experimental plans belong to research-test, but an actionable handoff to that skill is allowed. No experiment matrix is required simply to present an idea.

### Assembly options

For a small card, author the requested view directly from exact records. For a large technical card, first prepare a skeleton containing referenced facts and unresolved prose slots, then fill only those slots, then check semantic equivalence. Mechanical fields should reference their source rather than acquire new truth through repetition. An optional local fill map may use the field vocabulary below; it is not a records_put payload. A skeleton, fill map, plain translation, or every language variant is never mandatory.

## Inputs you read

- Exact candidate H and project Q versions; any requested audience/view.
- Relevant claim findings, original materials, implementation pointers, and test versions/results.
- Unresolved specification questions and contrary evidence, including evidence from low-ranked or parked candidates.
- The original diagnosis and nearest-prior comparisons where motivation depends on them.
- Real resource constraints and the provenance of cost estimates; unknown remains unknown.

Read indexed source passages as needed. Do not load an entire search dump when a specific source or claim is sufficient.

## Optional presentation advice

Choose notation and formatting for the requested output and its actual renderer. These are readability suggestions, not a scientific gate or a requirement to use a particular engine.

- In Markdown, backticks usually keep code identifiers such as `torch.no_grad` distinct from mathematical variables. Preserve identifiers exactly.
- If the selected viewer supports math, LaTeX may be appropriate; otherwise use readable Unicode or plain-text notation. No Unicode-only or no-LaTeX rule applies to all fields.
- If a viewer interprets dollar delimiters as math, escape literal currency and check delimiter balance. A plain-text viewer may need no such escaping.
- Place a displayed equation close to its defining operation and explain its variables. Use the chosen format's ordinary line-breaking rules.
- Check the rendered output when rendering matters; do not assume the archived KaTeX/card implementation is active.
- Formatting must preserve quantities, conditions, uncertainty, and scientific meaning. An equation correction belongs to a separately recorded scientific change.

## Output (a flat fill_map JSON)

```json
{
  "<path matching a TODO[path] placeholder>": "<the prose to substitute>",
  "<path>": <value-of-the-right-type>,
  ...
}
```

Path syntax matches the TODO labels exactly:
- Top-level: `"method_name"`, `"abstract_draft"`, `"core_claim"`
- Nested: `"motivation.problem_framing"`, `"feasibility_validation.data.verdict"`
- List entry sub-field: `"motivation.why_prior_stopped[0].what_they_did"`, `"reviewer_concerns_and_responses[0].response"`
- Whole-list field: `"sub_claims"` (value is the full list), `"method_flow.steps"` (value is the full list), `"key_equations"` (value contains only the equations needed for this candidate)

Values:
- Strings for prose fields.
- Lists for the few list-typed TODOs: `sub_claims`, `method_flow.steps`, `key_equations`. Each list entry is a dict matching the schema documented in the TODO's hint.

**Optional derived-view fields:** `title_zh`,
`plain_motivation_en`, `plain_motivation_zh`, `plain_method_steps_en`, `plain_method_steps_zh`,
`plain_method_modules_en`, `plain_method_modules_zh`. When a plain view or translation is requested, use [derive_plain](derive_plain.md) on the finished technical content. Do not leave TODO placeholders in a delivered view; show unresolved scientific decisions explicitly.

Save the requested view at a user/project-selected output path. Record new materials or findings only if the work actually produced them. Persist research changes through the shared API, not the optional fill-map schema.

## Field schemas (what each TODO must contain)

The skeleton's hint is the abridged spec. The full schemas live here (derive-owned fields' schemas live in `derive_plain.txt`):

**`method_name`** — short handle for the proposed method, e.g. `'Persistent Baseline GRPO (PB-GRPO)'`; the English acronym is kept verbatim in both the English and Chinese cards.

**`abstract_draft`** — optional, normally 150–250 words. Order: problem → evidenced bottleneck → proposed contribution → distinguishing prediction → conditional consequence. Before experiments, label the outcome as prospective. After experiments, replace it with claim-specific supported findings and scope; never retain hoped-for outcomes as results.

**`motivation.problem_framing`** — 2–3 paragraphs framing the user's problem. Reference the bottleneck_statement from Phase 1 and the closest_adjacent papers. NOT a category label — concrete structural framing. When Phase 1 framed the bottleneck as a structural property of a problem class, open at the CLASS level and present the anchor setting as its primary instance; when Phase 1 declared a class-of-one, stay at the instance level — do not inflate.

**`motivation.why_now`** — one paragraph on what makes this gap timely. Cite the most recent Phase 0 papers (within last 4–12 months) that get close but stop short. Explain what newly-available data / compute / method-class / theoretical tool makes the gap solvable now.

**`motivation.why_prior_stopped[i].what_they_did`** — one sentence per closest_adjacent paper.
**`motivation.why_prior_stopped[i].what_they_did_not_do`** — one sentence — the specific limit being lifted by the candidate.
**`motivation.why_prior_stopped[i].structural_reason_they_stopped`** — one sentence — missing tool / missing assumption-relaxation / missing mechanism / missing measurement.
Use checked source identity and venue/year where available; do not infer missing bibliographic metadata.

**`motivation.what_changes_when_gap_closes`** — 2–3 sentences naming downstream consequences. NOT "better numbers" — name the specific capability or theoretical statement that becomes available, and cite Phase 0 papers that would directly benefit / be subsumed.

**`core_claim`** — one sentence; should mirror the candidate's hook stripped to its load-bearing assertion.

**`sub_claims`** — list of `{id: "c1", statement: "...", supports_which_aspect: "<conceptual reference to a specific aspect of the bottleneck this sub-claim closes>"}`. As many entries as the mechanism actually needs; no quota.

**`key_equations`** — list of `{id, linked_step_id, latex, description, description_zh}`. Use only load-bearing equations; emit `[]` for pure-prose candidates. `linked_step_id` MUST match an existing `method_flow.steps[].step_id`. For a math-capable output, `latex` may carry the raw formula body; for other outputs use an equivalent readable representation. Descriptions explain the equation in the requested language and preserve identifiers. The field name does not require a specific renderer.

**`method_flow.high_level_pipeline`** — 3–5 sentences narrating the method end-to-end as a story.

**`method_flow.steps`** — list derived from `candidate.core_mechanism_steps`. Each entry:
```
{
  "step_id": "S1",
  "title": "<short imperative>",
  "what_changes": "<concrete operation: which line of the loss / which estimator / which proof step>",
  "why_this_step": "<reference the gap this step closes OR the ideation pattern's success conditions>",
  "linked_component": "theory | engineering | both",
  "linked_falsification": "metric_specification | mechanism_distinguisher | both",
  "input": "<from previous step or external>",
  "output": "<used by next step or final>"
}
```
Step IDs should be stable across views and revisions; S1, S2, … is an optional initial convention. Explain each step's role rather than forcing its role into a fixed category.

**`method_flow.design_reasoning_echo`** — one paragraph echoing or condensing `candidate.core_mechanism_reasoning` — surfaces the design rationale for the paper's discussion section (why this design vs alternatives).

**`feasibility_validation.data.verdict`** — `feasible | tight | infeasible`. **`feasibility_validation.data.rationale`** — one sentence: required data sources accessible; if any closed/private, name a public substitute the user can use.

**`feasibility_validation.theoretical.verdict`** — `feasible | tight | infeasible | n/a` (n/a only when the candidate has no theoretical contribution). **`feasibility_validation.theoretical.rationale`** — one sentence; if tight, name the missing prerequisite.

**`feasibility_validation.engineering.verdict`** — same scale. **`feasibility_validation.engineering.rationale`** — one sentence; if tight, name the binding implementation cost.

**`feasibility_validation.falsification.verdict`** — `feasible | tight | infeasible`. **`feasibility_validation.falsification.rationale`** — one sentence: the experiment is concrete enough to run with available tooling; the mechanism distinguisher's intervention is implementable.

**`feasibility_validation.overall`** — `feasible | tight | infeasible`. Aggregate verdict across the five sub-blocks. Compute estimates must cite actual constraints or measurements; an estimate is not runtime verification.

**`reviewer_concerns_and_responses[i].response`** — 2–3 sentences: explain where in the candidate (which field) the defense is anchored. Reference the exact original finding and the candidate delta. Keep the original attack and its evidence intact; a response is not proof that the issue was solved.

**`domain_landscape.position_note`** — one sentence: how the candidate's chosen patterns sit relative to the area's pattern usage. Descriptive, not prescriptive.

## Current hard rules

1. A presentation change does not edit H or a frozen test T. A mechanism, load-bearing parameter, scope, or claim change requires the relevant new version and an impact review.
2. Prior-work comparisons must name the actual source and supported difference. There is no required minimum paper count; insufficient evidence is visible.
3. Give method steps stable local identifiers so equations, inputs/outputs, implementation pointers, and findings can be aligned. Existing steps retain identity across a prose rewrite.
4. Plain-language variants must preserve steps and meaning. If one variant needs a new fact to make sense, expose the gap instead.
5. Equations stay attached to the operation they define. No invented constants, measurements, or empirical effects.
6. Resource feasibility is judged against known environment facts. Do not assume the original factory budget or an unlimited laboratory.
7. A next test may be linked, but generating an experiment matrix or calendar is not necessary to produce a card. Any schedule estimate states its basis and uncertainty.
8. An unresolved issue, missing citation, failed run, or contrary result remains visible. Rendering a card does not close it.
9. Formatting-only changes stop after semantic and readability checks. Reopen only judgments affected by substantive changes.
10. Do not run archived phase commands. Use current research-report, research-construct, research-test, and research-decide handoffs where their observable triggers apply.
