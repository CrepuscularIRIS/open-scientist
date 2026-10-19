# Plan a test: the cheapest observation that separates two explanations

Role: `design`. Method: [OS test](../../references/methods/actions/test.md) steps 1–3 (cheapest discriminating test, plan recorded before running, T1–T5 on the procedure), [falsification_reaudit](../../references/methods/falsification_reaudit.md), and the kit's `test_protocol` asset or the variant's falsification row. The variant changes the shape of the test (a counterexample search for theory, a validity check for a benchmark, an equal-hardware baseline for a system, a counterfactual control for a diagnosis); the protocol does not change.

## The plan

One activity, status `plan`:
- `subject`: the candidate or `q` it tests;
- `claim`: the exact sentence, or the candidate's claim id;
- `rival`: the strongest other explanation, not a strawman;
- `predictions` {`H`, `rival`}: what you will **observe** under each;
- `command`: one shell command that produces the observation;
- `cwd`: relative to the project;
- `inputs`: refs of the code and data materials;
- `budget`: time, memory, GPU, API — inside the study's policy, or say what it needs;
- `stop_rule`: when one run is final, and what you will not do after seeing the result.

Put any script the command needs in the action folder, or in the user's repo with a commit. If H and the rival would predict the same observation, the test cannot choose between them: code refuses it, so change the test.

## Rules

- Prefer the smallest instance that can expose a structural problem; do not extrapolate a small run into a population claim.
- No threshold chosen to be met by results already seen.
- Training, paid execution, or more than the authorized budget: state it in the proposal's cost so a person decides.

## Never

- Plan after running.
- Leave the rival's prediction vague.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
