# Study file contracts

A study lives in `<project>/.forge/studies/<slug>/`. Every write to the study's record store (`.forge/studies/<slug>/records.sqlite3`) goes through a commit that code validates first. Read it with `forge records context|get|list|history --project <project> --study <slug>`. Ids starting with `out-`, `collision-`, `idea-run-`, `domain-`, `auth-`, `answer-`, `absorbed-`, and the id `policy`, are reserved for the study's own commands. Refs are exact `{"id": "...", "version": N}`. Protocols: [references/protocols.md](../../references/protocols.md).

## proposal (`proposals/NNN.json`), written at the `propose` step

```json
{"action": "diagnose",
 "open_question": "the one question this action answers",
 "why_now": "why this is the cheapest action that can change the next decision",
 "based_on": [{"id": "q", "version": 2}],
 "inputs": [{"id": "code-memory", "version": 1}, "agent-repo/memory.py"],
 "may_change": ["Q"],
 "cost": {"class": "free", "estimate": "read 3 files, < 1 min", "network": false, "egress": false,
          "training": false, "paid": false, "gpu_hours": 0, "api_usd": 0},
 "subject": {"id": "...", "version": 1}}
```

- `action` is one of: `adapt`, `retrieve`, `read`, `diagnose`, `construct`, `evolve`, `coherence`, `collision`, `review`, `plan_test`, `run_test`, `interpret`, `decide`, `report`, `ask_human`, `build_domain`, `idea_run`.
- `based_on` must name the **current** versions of the Q/H/T it builds on.
- `inputs` are record refs or paths under the project.
- `may_change` ⊆ {Q, H, T, view, assets}.
- A cost outside the study's policy goes to a person.

Extra fields by action:

| Action | Extra fields |
|---|---|
| `adapt` | `asset_kind` (a kind in `forge/assets.py`, or `kit`) |
| `read` | `subject` (the paper or review material) |
| `evolve` | `subject` (the candidate); `operator` (repair, combine, simplify, feasibility, out_of_box, reframe); `defect` (a finding on that candidate naming what is wrong) |
| `collision` | `terms` {`signature_terms` (≥ 2), `alias_terms` (≥ 1), optional `windows` {`signature_months`, `alias_months`}} |
| `plan_test` | `subject` (the candidate or question tested) |
| `run_test` | `subject` (the activity in status plan); optional `declared_outputs` (paths under its cwd) |
| `interpret` | `subject` (the completed or failed activity) |
| `decide` | `subject` |
| `ask_human` | `reason` (goal_change, budget, egress, training_or_paid, preference, blocked) |
| `build_domain` | `domain` (slug), `topic`, optional `read_limit` |
| `idea_run` | `run` (slug), `domain` (a frozen domain slug), optional `question` |

## commit (`actions/NNN-<action>/commit.json`)

```json
{"records": [{"kind": "material", "id": "code-memory", "expected_version": 0, "payload": {...}},
             {"kind": "assessment", "id": "f-premise", "expected_version": 0, "payload": {...}}]}
```

- Records are written **in order, all or none**.
- `expected_version` is the record's current version: 0 for a new id.
- A later record may cite an earlier one in the same commit.
- Files go in the action folder. A material that points at a file carries `path` (relative to the project) and its `sha256`.

## payloads

| kind | fields |
|---|---|
| `project` (id `q`) | `question`, `constraints` [], `user_context`, `change_note` (required on a new version) |
| `candidate` | `problem` (the current `q` ref), `mechanism`, `claims` {claim_id: text}, `assumptions` [], `predictions` [], `rivals` [], `parents` [refs], `operator` (construct, or an evolve operator), `change_note` (required with parents) |
| `material` | `source`, `content`, `type` (paper, code, data, log, output, asset, review, note), `access` (identity, abstract, fulltext, inspected, executed), `locator`, `version`, `path`, `sha256`, `scope` |
| `activity` (plan) | `objective`, `status` "plan", `plan`, `subject`, `inputs` [refs], `claim`, `rival`, `predictions` {`H`, `rival`}, `command`, `cwd`, `budget`, `stop_rule` |
| `assessment` finding | `type` "finding", `subject`, `claim`, `judgment` (supported, partial, contradicted, contested, unknown, not_found, unreachable, uncited), `evidence` [material refs], `rationale`, `scope`, `result_type` (execution_failure, mechanism_refuted, not_discriminating, partial_support, supported, unknown) |
| `assessment` decision | `type` "decision", `subject`, `decision` (pursue, refine, park, kill), `rationale`, `evidence`, `revisit_when` (required for park), `decided_by` (model, human) |
| `assessment` feedback / disposition | as in 0.2: feedback {`source`, `text`}; disposition {`outcome` adopted, deferred, rejected, superseded; `rationale`; `outputs`} |

A finding about a candidate names one of that version's `claims` ids.

## what each action may commit

| Action | Kinds | Rules |
|---|---|---|
| intake (000) | project `q`; material `kit` (type asset, the kit file) | exactly one project record |
| `adapt` | material `asset-<kind>` (or `kit`), type asset | the asset file must validate ([design](../../docs/design.md) §2); `checked` only after a review finding on its previous version supports it |
| `retrieve` | materials | access identity or abstract only: finding is not reading |
| `read` | materials | `fulltext` needs `version` (arXiv vN) or `sha256` (local PDF) |
| `diagnose` | materials, findings, a new `q` version | `q` only if `may_change` has Q; never changes the user's constraints |
| `construct` | candidate (operator construct) | `problem` is the current `q` |
| `evolve` | a **new** candidate id | `parents[0]` = the subject; operator = the proposal's; combine has two parents |
| `coherence`, `review` | findings, agent feedback, materials (executed checks with sha256) | — |
| `plan_test` | one activity in status plan | passes the plan protocol (claim, rival, different predictions, command, budget, stop rule) |
| `interpret` | findings | `result_type` set; an assertive finding cites the activity's raw outputs |
| `decide` | decision | `decided_by` human when the study's participation is `human_decisions` |
| `report` | material (the report file) | only when the deliverable's completion rule holds |

`run_test`, `collision`, `build_domain`, `idea_run` and `ask_human` are committed by their own commands (`forge study exec|collide|absorb|answer`), never from an agent's commit.json.

**Every action:** an assertive finding's evidence must be material read in full, inspected or executed.
