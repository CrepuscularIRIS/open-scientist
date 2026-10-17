# Executable bridge replay

This is a **synthetic deterministic integration fixture**, not an autonomous-agent
evaluation, a model benchmark, or evidence of research improvement. It exercises
actual small Python programs, actual files/stdout/stderr, and the shared record
store. The fixture authors the handoff decisions; no model is asked to discover
them. It requires the plugin's Python dependencies, but no network, GPU, or API
credentials.

From the plugin checkout:

```bash
python examples/bridge_replay.py
```

This creates a fresh temporary project and prints JSON containing its path,
record references, raw-output paths, and `report_path`. Files remain there for
inspection. To choose a destination, first create an empty directory and pass
its **absolute** path:

```bash
python examples/bridge_replay.py --project-root /absolute/fresh-project
python scripts/records.py --project-root /absolute/fresh-project context
python scripts/records.py --project-root /absolute/fresh-project history candidate-b
```

The script refuses a nonempty record store or an existing `bridge-replay/`
artifact directory. It does not erase or reset a project. An explicit destination
must already exist; omitting it is the only mode that creates a temporary root.
If a run is interrupted, use a fresh directory and retain the old one for
diagnosis rather than overwriting its history.

| Case | Actual execution | Recorded handoff |
|---|---|---|
| A — storage versus lookup | Read one stored frame at step 7; query step 8; observe no match | Change `question-a@1` into `question-a@2`; retain original code, data, and observation materials |
| B — valid counterexample versus failed run | Execute shifted-step lookup and capture a counterexample; separately run an unavailable-dataset script with exit 7 | Bind the contradiction to `candidate-b@1`; create `candidate-b@2` and a **new planned** `test-b-revised@1`; failed execution creates no scientific rejection |
| C — missing specification versus card editing | Call a function whose `normalize_score` is undefined; capture actual NameError | Record `finding-c@1`, create a method/code revision before writing a new card, consume exact feedback, retain PARK and its dataset/budget revisit condition |

The revised B test is **not executed**. The revised C code is **not executed**.
Neither a narrower claim, a complete definition, a rendered card, nor a recorded
PARK decision establishes method efficacy. The final report says this explicitly.

Artifacts live in `bridge-replay/`: input data, the tiny Python programs, raw
stdout/stderr, command/exit-code JSON, two separate card versions, `RESULT.json`,
and `REPORT.md`. SQLite history is in `.open-scientist/records.sqlite3`.

To verify the handoff invariants and refusal behavior:

```bash
python -m pytest tests/test_bridge_replay.py -q
```

The test reads real output files and exact record versions. It checks that old
references and counterevidence survive revision, execution failure is separate,
card v1 was not overwritten, feedback was consumed, and PARK's condition remains.

See [record API](../docs/record-api.md) for payload contracts and
[evaluation scope](../evaluations/bridge-replay.md) for what this demonstration
does and does not establish.
