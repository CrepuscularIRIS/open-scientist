# Slice 1: question-driven study loop, shared records, materials

Date 2026-10-19. Status: design for approval; no code written. Basis: Research Forge `5869d39`, Open Scientist working tree (read only), and the build proposal `analysis/Research-Forge-统一科研套件-构建建议-2026-10-19.md`.

## 1. What this slice is

The direction is settled: Forge becomes the single driver of one research suite and takes over Open Scientist's useful methods and record semantics; OS's duplicate control flow is retired later. This slice builds the first two steps of that plan:

1. **One contract**: a question-driven navigator, one record store, one materials interface.
2. **One vertical loop that runs**: local material / code → diagnosis → minimal discriminating test → executed raw result → revision or decision.

Success means the evidence from an executed test can change the next action (update the question, stop a line of construction, deliver a diagnosis), and the code refuses steps that lack their inputs, authorization or prior plan.

What I took from the proposal versus what I am assuming:

| Stated by the proposal | Assumed here (correct me) |
|---|---|
| Forge is the only driver; OS worktree stays untouched in this phase | Code lives in the `research-forge` repo; renaming the product is later |
| Agent proposes the next action; code checks materials, versions, authorization, contracts | The checks are deterministic and run in the `forge` CLI, as today |
| Reuse OS record semantics (project, candidate, material, activity, assessment) as the one fact source | Ported to the Python standard library (Forge has no dependencies; OS records use pydantic) |
| Execution channel and participation are separate settings | The four mode names stay as shorthand |
| No fixed stage order; deliver when the question is answered | The existing domain build and idea pipeline stay as they are, callable later as methods |

## 2. Shape

```text
.forge/
  records.sqlite3              one fact store: Q/H/T, materials, findings, decisions (append-only versions)
  studies/<slug>/
    study.json                 goal, goal type, policy, optional pinned domain version
    proposals/NNN.json         the agent's proposed action (immutable once checked)
    actions/NNN-<action>/      that action's files: prompts' outputs, raw stdout/stderr, scripts
  domains/<slug>/...           unchanged (frozen domain assets; optional for a study)
  runs/<slug>/...              unchanged (existing idea pipeline; becomes a construct method in slice 3)
```

Files hold content (code excerpts, raw outputs, frozen assets). Records hold identity, version, links and judgments. Cards, reports and the Mod pane are views of records.

## 3. The loop

`forge next --study <slug>` stays read-only and returns one step, as today. Its states:

1. **No study**: `study_init`. In `auto` the goal is the user's message, verbatim. In human-at-decisions participation it is a human gate: goal, deliverable type, budget cap, hard constraints.
2. **An accepted action with uncommitted outputs**: that action's step (resume). A `run_test` in progress is checked by process identity (section 6).
3. **Nothing pending**:
   - If a stop condition holds (section 7), the step is terminal (`report` or `stuck`).
   - Otherwise it is `propose`: an LLM step that reads `study.json` and a record summary and writes `proposals/NNN.json`. The summary covers open questions, latest Q/H/T, unresolved findings and recent actions.
4. **A proposal not yet checked**: deterministic `check`. It returns FIX lines, routes to a human gate when the proposal leaves the authorization, or accepts.

Proposal contract:

```json
{"action": "diagnose",
 "open_question": "Is the reported memory loss caused by the save path or by retrieval?",
 "why_now": "Every construction so far assumes the save path; nothing on disk tests that.",
 "based_on": [{"id": "q-main", "version": 1}],
 "inputs": ["material:repo-agent@3f2c1e", "material:failure-log-0412"],
 "may_change": ["Q"],
 "cost": {"class": "free", "estimate": "read 4 files, run 1 local script < 1 min", "network": false, "egress": false},
 "expected_outputs": ["finding on q-main premise P1"]}
```

`check` refuses a proposal when:
- the action is unknown;
- a `based_on` ref is not the latest version (re-plan on current Q/H/T);
- an input does not exist;
- the cost exceeds the study's policy;
- the action's precondition fails (section 4);
- it repeats an earlier action with the same `based_on` and inputs that produced nothing new.

## 4. Actions in this slice

Each action has a method prompt, an output contract, a precondition and a rule for which records it commits. Methods are carried over from OS in full (the reasoning text, not just the summaries):

| Action | Method source | Precondition | Commits |
|---|---|---|---|
| `diagnose` | OS research-diagnose + research-code | a project (Q) | findings on Q premises; code materials (repo path, commit, dirty flag, file hashes); a new Q version only if `may_change` has Q |
| `retrieve` | OS research-retrieve (local library first, then arXiv) | an open question naming what is missing | materials (identity only: found ≠ read) |
| `read` | Forge `read.md` (versioned full text) | a material to read | reading material; signatures if useful |
| `construct` | Forge `generate.md` + OS construct (cards optional) | a Q whose premises are not contradicted | candidate (H) with claims, assumptions, predictions |
| `plan_test` | OS research-test steps 1–3 | a claim (of H, or a Q premise) and a named rival | activity `plan`: command, input versions, predictions for H and rival, the outcome table, budget, stop rule |
| `run_test` | OS research-test step 4 | an activity in `plan`, within policy | activity `running` → `completed`/`failed`; raw outputs as materials |
| `interpret` | OS research-test steps 5–6 | a completed or failed activity | finding typed as execution failure / mechanism refuted / not discriminating / partial support / supported / unknown |
| `review` | Forge audit checks + OS research-review (narrow, fresh context) | a finding or candidate | finding |
| `decide` | OS research-decide | ≥ 1 finding on the subject | decision (pursue / refine / park / kill) |
| `report` | OS research-report | the goal type's completion rule holds (section 7) | rendered from records; prose limited to scoped conclusions |
| `ask_human` | — | a reason in the allowed set (section 5) | feedback record + disposition |

`plan_test` is checked before `run_test` is allowed: the predictions must differ for H and the rival, or the plan is refused as not discriminating. Once running, the plan is frozen. A changed route is a new activity, never an edit of predictions already made.

## 5. Authorization and participation

`study.json` holds two independent settings and a budget:

```json
{"policy": {"channel": "local", "participation": "auto",
            "budget": {"authorized": "not specified", "gpu_hours": 0, "api_usd": 0, "wall_clock_min": 30},
            "allow": {"network_search": true, "web_egress": false, "training": false, "paid": false}}}
```

- **Shorthand.** `auto` = local + auto; `web` = web + auto; `hitl` = local + human at decisions; `web+hitl` = both.
- **Web egress.** The web channel sends packets that may contain code, so `web_egress` must be true to use it.
- **Done automatically within policy.** Searches, reading, code inspection, cheap local tests, revising H/T after counter-evidence, and Q updates that keep the user's hard constraints.
- **Needs a human.** Changing the goal or the deliverable; raising any budget field; data egress; training or paid execution; a choice the evidence cannot settle. Free searches never ask.

## 6. Execution and recovery

`run_test` is a bash step: `forge study exec --study <slug> --activity <id>`. It runs the planned command and records:
- the command and cwd;
- the git commit and dirty flag;
- the declared environment variables;
- start and end time and the exit code;
- stdout and stderr, as files with hashes;
- the declared output paths, with hashes.

Before starting, it writes `attempt.json` with the command hash, the PID and the process start time. On resume:
- The process is alive with the same start time: wait.
- The process is gone and outputs are complete: commit `completed` or `failed` from the exit code.
- The process is gone and outputs are incomplete: commit `failed (interrupted)`. A rerun needs a new activity, so a completed external action is never rerun silently.

Commands longer than the step limit run in the background through the same wrapper.

## 7. Progress and stopping

An action is **productive** when it commits at least one of:
- a new material;
- a new Q/H/T version;
- a finding whose judgment differs from the previous one on that claim;
- a decision.

Rewording with no new evidence or prediction is not progress. Three unproductive actions in a row stop the study as `stuck` for a person.

**Completion depends on the goal type** in `study.json`:
- `plan`: a candidate, a test plan and a review finding, with no unresolved contradicting finding.
- `verified_execution`: a completed activity and its interpret finding.
- `diagnosis`: a finding with a judgment on the Q premise in question.
- `exploration`: a report of what was learned, whenever the agent proposes it.

Reaching the completion rule allows `report`; it does not force it if the goal asks for more.

## 8. Records kernel

`forge/records.py` is a standard-library port of OS `records.py` semantics:
- the same kinds and `{id, version}` refs;
- append-only versions with `expected_version`;
- the same link rules (a candidate's problem is a project; finding evidence must be materials; a disposition answers a feedback or a finding);
- the same activity rules (a plan has no outputs; completed needs a result; failed needs a failure).

OS's `workflow` record kind is not ported: `study.json` and the proposals replace it. Domain versions enter as materials (manifest hash). Legacy `.forge/runs` stay readable. Read-only compatibility with `.open-scientist` records waits for slice 4.

## 9. Acceptance for this slice

All on fixtures with a scripted agent, as in the current tests, plus one real case:

1. **Wrong premise corrected.** In a fixture repo, a "memory loss" report is actually caused by a truncated retrieval window. The loop runs diagnose, plan_test (a probe), run_test (a real subprocess), interpret (premise contradicted), a new Q version, then report. A construct proposal still based on the old Q is refused.
2. **Interrupted test.** Killing `run_test` mid-run gives `failed (interrupted)` on resume. The test is not rerun until a new activity is planned.
3. **Non-discriminating plan.** A plan whose H and rival predictions are identical is refused.
4. **Authorization.** A plan declaring training or a raised budget in `auto` routes to `ask_human`; a free search does not.
5. **No progress.** Three unproductive actions in a row give `stuck`.
6. **Real case.** One real repository with a doubted premise, run with real model steps, with the transcript and records kept. The outcome does not have to be positive.

## 10. Not in this slice

- Collision-triggered reading and local domain updates.
- Adopting a v2 domain mid-study (slice 3).
- Wiring the existing idea pipeline in as `construct --deep` (slice 3).
- Codex adapter, OS entry retirement, `.open-scientist` read compatibility (slice 4).
- M5 and same-model, same-budget comparisons (slice 5).
