#!/usr/bin/env python3
"""Run three synthetic code→record→revision→report fixtures, without model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from open_scientist.records import Store


def ref(record):
    return {"id": record["id"], "version": record["version"]}


def material(store, record_id, path):
    return store.put("material", record_id, {
        "source": str(path), "content": path.read_text(encoding="utf-8"),
        "scope": "Synthetic deterministic bridge fixture; no real research result",
    }, 0)


def execute(store, directory, record_id, script, inputs, objective, plan, arguments=()):
    """Record a plan before dispatch; preserve actual exit status and raw output."""
    payload = {"objective": objective, "status": "plan", "plan": plan, "inputs": inputs}
    planned = store.put("activity", record_id, payload, 0)
    running = store.put("activity", record_id, {**payload, "status": "running"}, 1)
    command = [sys.executable, str(script), *map(str, arguments)]
    call = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=10)
    stdout_path = directory / f"{record_id}.stdout.txt"
    stderr_path = directory / f"{record_id}.stderr.txt"
    execution_path = directory / f"{record_id}.execution.json"
    stdout_path.write_text(call.stdout, encoding="utf-8")
    stderr_path.write_text(call.stderr, encoding="utf-8")
    execution_path.write_text(json.dumps({
        "synthetic": True, "command": command,
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "activity_plan": ref(planned), "activity_dispatch": ref(running),
        "returncode": call.returncode, "stdout": call.stdout, "stderr": call.stderr,
    }, indent=2), encoding="utf-8")
    observation = material(store, f"{record_id}-observation", execution_path)
    final = {**payload, "outputs": [ref(observation)]}
    if call.returncode == 0:
        final.update(status="completed", result="The command returned zero; see recorded stdout. This alone makes no scientific finding.")
    else:
        final.update(status="failed", failure=f"Command exited {call.returncode}; see stderr. Execution failure is not a mechanism refutation.")
    activity = store.put("activity", record_id, final, 2)
    return {"activity": ref(activity), "plan": ref(planned), "material": ref(observation),
            "returncode": call.returncode, "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path), "execution_path": str(execution_path)}


def case_a(store, directory):
    question = store.put("project", "question-a", {
        "question": "Are frames dropped from memory in this synthetic system?",
        "constraints": ["Local fixture only; no network or GPU", "Separate storage from retrieval"],
    }, 0)
    data_path = directory / "frames.json"
    data_path.write_text(json.dumps({"frames": [{"id": "frame-1", "step": 7, "content": "red door"}], "query_step": 8}), encoding="utf-8")
    script = directory / "inspect_retrieval.py"
    script.write_text('''import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
frames, query = data["frames"], data["query_step"]
print(json.dumps({"stored_count": len(frames), "available_steps": [f["step"] for f in frames], "queried_step": query, "matched_ids": [f["id"] for f in frames if f["step"] == query]}))
''', encoding="utf-8")
    data = material(store, "frames-data", data_path)
    code = material(store, "retrieval-code", script)
    run = execute(store, directory, "inspect-a", script,
                  [ref(question), ref(data), ref(code)],
                  "Distinguish dropped storage from a query miss",
                  "Inspect stored frames and perform exact-step lookup. Do not infer absence from an empty query result.",
                  [data_path])
    observed = json.loads(Path(run["stdout_path"]).read_text())
    if run["returncode"] != 0 or observed["stored_count"] != 1 or observed["matched_ids"]:
        raise ValueError("Case A did not produce the expected storage/query distinction")
    store.put("assessment", "finding-a", {
        "type": "finding", "subject": ref(question), "claim": "frames-dropped",
        "judgment": "contradicted", "evidence": [run["material"]],
        "rationale": "The frame exists at step 7; querying step 8 returns no match.",
        "scope": "Only the one-frame synthetic fixture, not a real agent memory system",
    }, 0)
    revised = store.put("project", "question-a", {
        **question["payload"], "question": "Why does exact-step lookup miss a frame still present in storage?",
        "change_note": "Actual storage/query evidence changed the question; preserve the original materials.",
    }, 1)
    return {**run, "question_before": ref(question), "question_after": ref(revised), "data_path": str(data_path)}


def case_b(store, directory, a):
    question = store.put("project", "question-b", {
        "question": "Does exact-step retrieval satisfy a shifted-query universal guarantee?",
        "constraints": ["One finite synthetic counterexample; no average-performance inference"],
    }, 0)
    hypothesis = store.put("candidate", "candidate-b", {
        "problem": ref(question), "mechanism": "Look up the stored frame by exact query step",
        "claims": {"universal": "For every stored frame at step s, querying s+1 retrieves that frame"},
        "assumptions": ["A stored step is a unique integer"],
        "predictions": ["The frame at step 7 will be returned for query 8 if the universal claim holds"],
    }, 0)
    script = directory / "counterexample.py"
    script.write_text('''import json, sys
from pathlib import Path
frames = json.loads(Path(sys.argv[1]).read_text())["frames"]
frame = frames[0]
query = frame["step"] + 1
returned = next((f["id"] for f in frames if f["step"] == query), None)
print(json.dumps({"universal_claim_holds": returned == frame["id"], "witness": {"stored_step": frame["step"], "queried_step": query, "returned_id": returned}}))
''', encoding="utf-8")
    code = material(store, "counterexample-code", script)
    run = execute(store, directory, "test-b", script,
                  [ref(hypothesis), {"id": "frames-data", "version": 1}, ref(code)],
                  "Test the universal shifted-query guarantee on a legal witness",
                  "Before execution: for stored step 7 query 8. The claim predicts frame-1; None would be a counterexample.",
                  [a["data_path"]])
    observed = json.loads(Path(run["stdout_path"]).read_text())
    if run["returncode"] != 0 or observed["universal_claim_holds"] is not False:
        raise ValueError("Case B did not produce a valid counterexample")
    finding = store.put("assessment", "finding-b", {
        "type": "finding", "subject": ref(hypothesis), "claim": "universal",
        "judgment": "contradicted", "evidence": [run["material"]],
        "rationale": "A legal stored frame at step 7 is not returned for query 8. One counterexample suffices against this universal statement.",
        "scope": "Refutes the stated exact-lookup guarantee; says nothing about real-world average retrieval performance",
    }, 0)
    failure_script = directory / "unavailable_dataset.py"
    failure_script.write_text('import sys\nprint("Synthetic dataset is unavailable", file=sys.stderr)\nsys.exit(7)\n', encoding="utf-8")
    failure_code = material(store, "unavailable-code", failure_script)
    failed = execute(store, directory, "test-b-unavailable", failure_script,
                     [ref(hypothesis), ref(failure_code)], "Attempt a separate dataset check",
                     "Try to read an unavailable synthetic dataset. Nonzero exit is execution failure, not a claim verdict.")
    revised = store.put("candidate", "candidate-b", {
        **hypothesis["payload"], "claims": {"universal": "For each unique stored step s, exact lookup at s retrieves that frame"},
        "predictions": ["A same-step query should return the stored frame; a shifted-step query has no such guarantee"],
        "parents": [ref(hypothesis)],
        "change_note": "Narrow the guarantee to same-step lookup after finding-b@1. The new claim is not automatically verified.",
    }, 1)
    new_test = store.put("activity", "test-b-revised", {
        "objective": "Check the revised same-step claim", "status": "plan",
        "plan": "Use all unique steps in a new fixture and compare exact lookup with stored IDs. This test has not run.",
        "inputs": [ref(revised), {"id": "frames-data", "version": 1}, ref(finding)],
    }, 0)
    return {"candidate_before": ref(hypothesis), "candidate_after": ref(revised),
            "counterexample": run, "failed_run": failed, "new_test": ref(new_test)}


def case_c(store, directory):
    question = store.put("project", "question-c", {
        "question": "Is a proposed score-normalization method specified enough to implement?",
        "constraints": ["Do not claim research improvement from specification completion"],
    }, 0)
    hypothesis = store.put("candidate", "candidate-c", {
        "problem": ref(question), "mechanism": "Rank values after applying normalize_score; this operation is undefined",
        "claims": {"implementation_complete": "All operations necessary for score computation are specified"},
    }, 0)
    card_before = directory / "candidate-c-v1.md"
    card_before.write_text("# Synthetic card: candidate-c@1\n\nMechanism: normalize_score is undefined.\nResearch effect: unknown.\n", encoding="utf-8")
    before_hash = hashlib.sha256(card_before.read_bytes()).hexdigest()
    revisit = "A real dataset and comparison budget become available"
    park = store.put("assessment", "decision-c", {
        "type": "decision", "subject": ref(hypothesis), "decision": "park",
        "rationale": "No real dataset or comparison budget is available", "revisit_when": revisit,
    }, 0)
    feedback = store.put("assessment", "feedback-c", {
        "type": "feedback", "subject": ref(hypothesis), "source": "human",
        "text": "Synthetic user instruction: define normalize_score in a new method version before updating the card; retain the PARK condition.",
    }, 0)
    script = directory / "undefined_normalizer.py"
    script.write_text('def score(value):\n    return normalize_score(value)\nprint(score(4.0))\n', encoding="utf-8")
    code = material(store, "undefined-normalizer-code", script)
    run = execute(store, directory, "spec-c", script,
                  [ref(hypothesis), ref(code), ref(feedback)],
                  "Locate an implementation specification gap",
                  "Call score(4.0). A missing operation is a specification finding, not a result about normalization quality.")
    stderr = Path(run["stderr_path"]).read_text()
    if run["returncode"] == 0 or "NameError" not in stderr or "normalize_score" not in stderr:
        raise ValueError("Case C did not expose the intended missing operation")
    finding = store.put("assessment", "finding-c", {
        "type": "finding", "subject": ref(hypothesis), "claim": "implementation_complete",
        "judgment": "contradicted", "evidence": [run["material"], ref(code)],
        "rationale": "The specification and implementation omit normalize_score, and the actual invocation raises NameError.",
        "scope": "Only completeness of this toy implementation; no claim about method efficacy",
    }, 0)
    revised = store.put("candidate", "candidate-c", {
        **hypothesis["payload"], "mechanism": "Explicit fixture design choice: normalize_score(x) = x / (1 + abs(x)); rank normalized values",
        "parents": [ref(hypothesis)],
        "change_note": "Respond to finding-c@1 and feedback-c@1. This is an authored definition, not an inferred successful research result.",
    }, 1)
    revised_script = directory / "defined_normalizer.py"
    revised_script.write_text('def normalize_score(value):\n    return value / (1.0 + abs(value))\ndef score(value):\n    return normalize_score(value)\n', encoding="utf-8")
    revised_code = material(store, "defined-normalizer-code", revised_script)
    updated_park = store.put("assessment", "decision-c", {
        **park["payload"], "subject": ref(revised),
        "rationale": "Specification changed, but the dataset and comparison-budget condition is still unmet",
    }, 1)
    disposition = store.put("assessment", "feedback-c-response", {
        "type": "disposition", "subject": ref(feedback), "outcome": "adopted",
        "rationale": "A new candidate/code version defines the operation, and the updated decision explicitly retains PARK and its revisit condition.",
        "outputs": [ref(revised), ref(revised_code), ref(updated_park)],
    }, 0)
    card_after = directory / "candidate-c-v2.md"
    card_after.write_text("# Synthetic card: candidate-c@2\n\nSource: candidate-c@2; decision-c@2.\nDefinition: normalize_score(x) = x / (1 + abs(x)).\nExecution: revised code has not been run.\nResearch effect: unknown.\nDecision: PARK. Revisit when a real dataset and comparison budget become available.\n", encoding="utf-8")
    return {"candidate_before": ref(hypothesis), "candidate_after": ref(revised),
            "spec_probe": run, "finding": ref(finding), "feedback": ref(feedback),
            "disposition": ref(disposition), "decision": ref(updated_park),
            "card_before_path": str(card_before), "card_before_sha256": before_hash,
            "card_after_path": str(card_after)}


def run_replay(project_root: str) -> dict:
    """Write only in the requested existing root; refuse a populated research store."""
    store = Store(project_root)
    if store.list():
        raise ValueError("Refusing a nonempty existing record store; use a fresh temporary project")
    directory = store.root / "bridge-replay"
    if directory.exists() or directory.is_symlink():
        raise ValueError("Refusing to overwrite an existing bridge-replay artifact directory")
    directory.mkdir()
    a = case_a(store, directory)
    b = case_b(store, directory, a)
    c = case_c(store, directory)
    report = directory / "REPORT.md"
    report.write_text("""# Synthetic bridge replay

This is a deterministic local integration fixture. No model, GPU, network, or autonomous research agent was used.
No research gain is established.

- A: actual code/data show one stored frame and an empty shifted-step lookup. question-a@2 changes the question; question-a@1 and its materials remain.
- B: test-b@3 records an executed counterexample to candidate-b@1's universal statement. finding-b@1 remains attached to that old version. candidate-b@2 is a narrower, unverified claim.
- test-b-revised@1: plan — not executed. A revised test is a new object, not a rewritten historical prediction.
- test-b-unavailable@3: failed — exit 7 is an execution failure, with no automatic scientific rejection.
- C: actual NameError reveals an undefined normalizer. candidate-c@2 records the design choice before the v2 card is written. The v1 card is retained. Revised code has not run and efficacy remains unknown.
- feedback-c@1 is consumed by feedback-c-response@1. decision-c@2 remains PARK with its original dataset/budget revisit condition.

The records demonstrate provenance and handoff invariants. They do not demonstrate that the plugin improves scientific ideation, discovery, or agent decisions.
""", encoding="utf-8")
    result = {"synthetic": True, "project_root": str(store.root), "cases": {"A": a, "B": b, "C": c}, "report_path": str(report)}
    (directory / "RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", help="Existing fresh absolute directory; omitted means create a fresh temporary directory")
    args = parser.parse_args(argv)
    try:
        root = args.project_root or tempfile.mkdtemp(prefix="open-scientist-bridge-")
        result = run_replay(root)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
