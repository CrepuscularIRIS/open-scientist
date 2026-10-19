# Intake: the question record and the study's kit

Role: `design`. You turn the user's goal (in `study.json`, verbatim) into two things:
- the question record `q`;
- the **kit**, which says how this study adapts to its task.

You do not research yet. Contracts: [contracts.md](contracts.md). The design behind the kit: [docs/design.md](../../docs/design.md) §2–3.

## 1. The question (`q`)

- `question`: the user's question in their words. Do not improve it. If it carries a premise ("the agent loses memories when saving"), keep that wording and record the premise as doubtful in `user_context`.
- `constraints`: the user's **hard** constraints only: what they said must or must not happen (no training, local only, a deadline, a solution shape they rule out). Never add your own.
- `user_context`: everything else the user said that later steps need: what is bugging them (Companion's richest source), what they have tried, what they believe and how sure they are, their skills and access if stated.

If the goal names a project path, repository or paper, note it in `user_context`. The first proposals will register it as material.

## 2. The kit (`kit.json` in the action folder)

```json
{"task_types": ["diagnosis"],
 "deliverable": "diagnosis",
 "variants": {"diagnosis": "references/variants/diagnosis.md"},
 "assets": [{"kind": "code_map", "why": "the premise is about code paths; diagnose needs to know where save and retrieve live"},
            {"kind": "researcher_profile", "why": "decide weighs what this user can run"}],
 "rationale": "The user reports a failure and asks why; nothing yet says the save path is the cause."}
```

- **task_types**: read the goal's verb and deliverable, then choose one or more of the types in [references/variants/](../../references/variants/):
  - "why does X fail / is X real" → `diagnosis`;
  - "a method that" → `mechanism`;
  - "prove / bound" → `theory`;
  - "an evaluation / benchmark / dataset" → `benchmark`;
  - "make X faster or cheaper" → `system`;
  - "what is true of" → `analysis`;
  - "what exists" → `survey`;
  - "reproduce" → `replication`;
  - a surprising empirical claim → `empirical_reveal`;
  - behaviour with scale → `scaling`.
  
  Read the variant file for each type you choose.
- **deliverable**: what finishes this study for this user:
  - `diagnosis`: a judged premise;
  - `plan`: a candidate, a test plan and a review;
  - `verified_execution`: a run and its interpretation;
  - `idea_card`: the strict RS chain through `idea_run`;
  - `exploration` or `report`.
  
  Choose the smallest that answers what they asked. A diagnosis request is finished by a diagnosis, not by an idea.
- **variants**: one entry per task type, exactly `references/variants/<type>.md`.
- **assets**: only the kinds the **first** decisions need, each with the decision that needs it. Kinds are listed in `forge/assets.py` and docs/design.md §2. Assets are built later by `adapt`, from evidence. Listing a kind here does not build it. Do not list the whole catalogue.
- **rationale**: one or two sentences tying the choices to the user's words.

## 3. Commit

`commit.json` writes, in this order:
1. the `q` project record;
2. the kit as material id `kit`: type `asset`, access `inspected`, `path` the kit file relative to the project, `sha256`.

## Never

- Change or "clarify" the user's question, or add constraints they did not state.
- Choose a task type the goal does not support, to make the study look bigger.
- List assets that no early decision needs.
