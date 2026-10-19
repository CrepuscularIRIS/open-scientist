# Propose the next action

Role: `design`. You choose **one** next action for this study and write it as `proposals/NNN.json` ([contracts.md](contracts.md)). Code then checks it: inputs exist, versions are current, the cost is inside the policy, the action's precondition holds, and it is not an unproductive repeat. The action you choose is the study's only control flow: there is no fixed stage order.

## Read first

- The record context (the step's notes give the command): latest Q/H/T, materials, findings and decisions, **stale inputs**, **earlier contrary findings**, **open feedback**.
- `study.json`: goal, policy (budget, what is allowed).
- The kit (`kit` material's file): task types, deliverable, variants, the assets planned.
- The variant file of each task type, and `actions/` (what earlier actions committed, and whether they were productive).
- The method index: [references/methods/actions/orient.md](../../references/methods/actions/orient.md) (OS 0.2 workflow: locate current facts; old "running" proves nothing) and [references/protocols.md](../../references/protocols.md).

## Choose by the open question, not by habit

Name the open question whose answer is most likely to change what happens next, then the cheapest action that can answer it:

| Open question | Action |
|---|---|
| Is the problem real? Is the measurement right? | `diagnose` (code, data, logs, failure cases); a cheap probe through `plan_test` → `run_test` |
| What is the closest prior work? Where does a mechanism or its conditions come from? | `retrieve` (local library first), then `read` the ones that matter |
| What does this field or this task need that the study lacks (a rubric, a test protocol, a code map, cards)? | `adapt` that asset kind, from evidence already read |
| No mechanism yet for a real, diagnosed problem | `construct` (or `idea_run` for the strict RS chain when the deliverable is an idea card) |
| A candidate has a named defect | `evolve` with the operator that answers that defect |
| Does the procedure as written work? | `coherence` (fresh context; executes on paper) |
| Is it already done, under this name or another? | `collision` (two channels), then `review` |
| Two explanations remain, and the evidence cannot separate them | `plan_test`: the cheapest test where they predict different observations |
| A plan is ready and authorized | `run_test` |
| A run finished or failed | `interpret` |
| Is this claim, asset or candidate sound? | `review` (independent) |
| Enough evidence to choose pursue, refine, park or kill | `decide` |
| The deliverable's completion rule holds (the notes say so) | `report` |
| Only the person can answer (a hard goal, more budget, sending data out, a preference evidence cannot settle) | `ask_human` |
| A new field and the decision needs its cards, expectations and vocabulary | `build_domain` (RS's strict reading pipeline) |

## Rules

- **Progress is information, not activity.** These count:
  - a new material;
  - a changed question, mechanism, prediction or test;
  - a finding whose judgment changed;
  - a decision.
  
  Ruling out an explanation counts. Rewording does not. Three unproductive actions in a row stop the study.
- **Go back when the evidence says so.** A contradicted premise of `q` means diagnose and revise `q` (`may_change: ["Q"]`) before constructing. A refuted claim means evolve or abandon the candidate, never re-run the same test hoping for another answer.
- **Do not build what nobody needs.** A diagnosis study is done when the premise is judged. Do not propose ideas, cards or reports to fill time.
- **Stay inside the policy.** Free searches and local cheap runs need no permission. Training, paid runs, sending data off the machine, or more budget than authorized go to a person (code routes them). Never hide a cost.
- `based_on` lists the current versions you build on. `cost.estimate` is honest. `why_now` says why this beats the alternatives.

## Never

- Propose two actions in one file, or an action whose output you already know.
- Repeat an unproductive action on the same inputs.
- Treat a search hit as read, or an empty search as novelty.
