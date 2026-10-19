"""The study loop end to end on a fixture repository: a wrong premise is corrected by a small executed test.

Acceptance (docs/specs/2026-10-19-study-loop-design.md §9 and docs/design.md §5): the agent proposes, code checks,
the planned command really runs, its raw output decides the finding, the question is revised, and building on the
old question is refused.
"""
from __future__ import annotations

from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from conftest import run_cli
from forge import study
from forge.execute import attempt_state
from forge.util import read_json, write_json
from study_host import GOAL, Host, fixture_repo, show


@pytest.fixture
def host(tmp_path):
    h = Host(tmp_path / "project")
    h.repo = fixture_repo(h.layout.project)
    run_cli("study", "init", "--project", str(h.layout.project), "--study", h.layout.slug, "--goal", GOAL)
    return h


def intake(host, **kw):
    s = host.next()
    assert s["step"] == "intake", show(s)
    host.intake(**kw)
    host.step_llm(s)
    s = host.next()
    assert s["step"] == "commit" and s["state"] == "intake", show(s)
    host.bash(s)


def diagnose_and_plan(host):
    """001 diagnose (inspect code), 002 plan the probe."""
    host.propose(1, "diagnose", open_question="Is memory lost at save time, or at retrieval?",
                 inputs=[host.rel(host.repo / "memory.py")], may_change=["Q"])
    s = host.next()
    assert s["step"] == "diagnose", show(s)
    code = host.material("code-memory", host.repo / "memory.py", "code", "inspected", "save appends; retrieve slices the last window")
    finding = {"kind": "assessment", "id": "f-premise", "expected_version": 0, "payload": {
        "type": "finding", "subject": host.ref("q"), "claim": "memories are lost when saved", "judgment": "contested",
        "evidence": [{"id": "code-memory", "version": 1}], "scope": "memory.py only",
        "rationale": "save keeps every item; retrieve returns only the last `window` items, so loss may be at retrieval"}}
    host.commit(1, "diagnose", [code, finding])
    host.step_llm(s)
    host.drive_to("propose")
    host.propose(2, "plan_test", subject=host.ref("q"), open_question="Does retrieval drop saved memories?")
    s = host.next()
    assert s["step"] == "plan_test", show(s)
    host.commit(2, "plan_test", [{"kind": "activity", "id": "t-probe", "expected_version": 0, "payload": {
        "objective": "separate save loss from retrieval truncation", "status": "plan",
        "plan": "save 40 memories, count what retrieval returns", "subject": host.ref("q"), "inputs": [{"id": "code-memory", "version": 1}],
        "claim": "memories are lost when saved", "rival": "retrieval truncates to a fixed window",
        "predictions": {"H": "saved < 40", "rival": "saved == 40 and retrieved == window"},
        "command": f"{sys.executable} probe.py", "cwd": host.rel(host.repo), "budget": "< 1 s, local",
        "stop_rule": "one run; any exit is final"}}])
    host.step_llm(s)
    host.drive_to("propose")


def test_a_wrong_premise_is_corrected_by_an_executed_probe(host):
    intake(host)
    diagnose_and_plan(host)
    host.propose(3, "run_test", subject=host.ref("t-probe"))
    s = host.next()
    assert s["step"] == "run_test" and s["type"] == "bash", show(s)
    host.bash(s)
    activity = host.layout.store.get("t-probe")
    assert activity["payload"]["status"] == "completed" and activity["payload"]["execution"]["exit_code"] == 0
    stdout = host.layout.store.get("out-003-stdout")
    assert stdout["payload"]["access"] == "executed" and '"retrieved": 8' in (host.layout.project / stdout["payload"]["path"]).read_text()

    host.drive_to("propose")
    host.propose(4, "interpret", subject=host.ref("t-probe"))
    s = host.next()
    assert s["step"] == "interpret", show(s)
    host.commit(4, "interpret", [{"kind": "assessment", "id": "f-premise", "expected_version": 1, "payload": {
        "type": "finding", "subject": {"id": "q", "version": 1}, "claim": "memories are lost when saved",
        "judgment": "contradicted", "result_type": "mechanism_refuted", "evidence": [{"id": "out-003-stdout", "version": 1}],
        "scope": "the fixture's save and retrieve paths", "rationale": "all 40 were saved; retrieval returned the last 8"}}])
    host.step_llm(s)
    host.drive_to("propose")

    # Building on the refuted premise is refused; so is planning on the old question once it is revised.
    host.propose(5, "construct", open_question="design a better save module")
    s = host.next()
    assert s["step"] == "propose" and any("contradicted premise" in e for e in s["errors"]), show(s)
    host.propose(5, "diagnose", open_question="restate the question on the evidence", may_change=["Q"])
    s = host.next()
    assert s["step"] == "diagnose", show(s)
    host.commit(5, "diagnose", [
        {"kind": "project", "id": "q", "expected_version": 1, "payload": {
            "question": "Why does retrieval return only the last 8 memories, and is that the reported loss?",
            "constraints": ["no training", "local machine only"], "change_note": "the probe shows saving keeps all 40"}},
        {"kind": "assessment", "id": "f-window", "expected_version": 0, "payload": {
            "type": "finding", "subject": {"id": "q", "version": 2}, "claim": "the reported loss is retrieval truncation",
            "judgment": "supported", "result_type": "supported", "evidence": [{"id": "out-003-stdout", "version": 1}],
            "scope": "the fixture repo", "rationale": "retrieve() slices store[-window:] with window 8"}}])
    host.step_llm(s)
    host.drive_to("propose")
    host.propose(6, "plan_test", based_on=[{"id": "q", "version": 1}], subject={"id": "q", "version": 1})
    s = host.next()
    assert any("q@1 is not current" in e for e in s["errors"]), show(s)

    host.propose(6, "report", open_question="deliver the diagnosis")
    s = host.next()
    assert s["step"] == "report", show(s)
    report = host.layout.action_dir(6, "report") / "report.md"
    host.commit(6, "report", [], files=[("report.md", "# Diagnosis\nRetrieval truncates to the last 8 memories.\n")])
    host.commit(6, "report", [host.material("report", report, "note", "inspected", "the diagnosis report")])
    host.step_llm(s)
    assert host.drive_to("done")["step"] == "done"
    marks = [m["productive"] for _, _, m in host.layout.commits()]
    assert all(marks[1:]), marks


def test_an_interrupted_test_is_recorded_as_interrupted_and_not_rerun(host):
    intake(host)
    host.propose(1, "plan_test", subject=host.ref("q"))
    s = host.next()
    host.commit(1, "plan_test", [{"kind": "activity", "id": "t-slow", "expected_version": 0, "payload": {
        "objective": "o", "status": "plan", "plan": "p", "subject": host.ref("q"), "inputs": [], "claim": "c",
        "rival": "r", "predictions": {"H": "prints done", "rival": "prints nothing"},
        "command": "echo started >> runs.log; sleep 30; echo done", "cwd": host.rel(host.repo), "budget": "b", "stop_rule": "s"}}])
    host.step_llm(s)
    host.drive_to("propose")
    host.propose(2, "run_test", subject=host.ref("t-slow"))
    assert host.next()["step"] == "run_test"
    wrapper = subprocess.Popen([sys.executable, "scripts/forge.py", "study", "exec", "--project", str(host.layout.project),
                                "--study", host.layout.slug, "--proposal", "2"], cwd=str(Path(__file__).parents[1]))
    adir = host.layout.action_dir(2, "run_test")
    for _ in range(100):
        if (read_json(adir / "attempt.json") or {}).get("child_pgid"):
            break
        time.sleep(0.05)
    assert host.next()["step"] == "wait"
    wrapper.send_signal(signal.SIGKILL)
    wrapper.wait()
    assert attempt_state(host.layout, 2)[0] == "interrupted"
    s = host.next()
    assert s["step"] == "run_test" and "interrupted" in s["notes"][0], show(s)
    host.bash(s)
    activity = host.layout.store.get("t-slow")
    assert activity["payload"]["status"] == "failed" and "interrupted" in activity["payload"]["failure"]
    assert (host.repo / "runs.log").read_text().count("started") == 1  # the command was not rerun
    attempt = read_json(adir / "attempt.json")
    forged = {**attempt, "started_at": "2020-01-01T00:00:00+00:00", "exit_code": 0}
    write_json(host.layout.action_dir(2, "run_test") / "attempt.json", forged)  # after commit this changes nothing
    assert host.next()["step"] == "propose"


def test_a_hand_written_attempt_is_not_an_execution(host):
    intake(host)
    diagnose_and_plan(host)
    host.propose(3, "run_test", subject=host.ref("t-probe"))
    adir = host.layout.action_dir(3, "run_test")
    adir.mkdir(parents=True)
    (adir / "stdout.txt").write_text("fabricated\n")
    write_json(adir / "attempt.json", {"command": "x", "cwd": str(host.repo), "git": {}, "started_at": "t",
                                       "wrapper_pid": 1, "wrapper_start": "0", "exit_code": 0})
    s = host.next()
    assert s["step"] == "attempt_mismatch" and s["type"] == "terminal", show(s)


def test_a_plan_whose_rival_predicts_the_same_is_refused(host):
    intake(host)
    host.propose(1, "plan_test", subject=host.ref("q"))
    s = host.next()
    host.commit(1, "plan_test", [{"kind": "activity", "id": "t-weak", "expected_version": 0, "payload": {
        "objective": "o", "status": "plan", "plan": "p", "subject": host.ref("q"), "inputs": [], "claim": "c",
        "rival": "r", "predictions": {"H": "Retrieved == 8", "rival": "retrieved  == 8"}, "command": "true",
        "budget": "b", "stop_rule": "s"}}])
    s = host.next()
    assert s["step"] == "plan_test" and any("cannot discriminate" in e for e in s["errors"]), show(s)


def test_training_or_a_raised_budget_asks_a_person_but_a_search_does_not(host):
    intake(host)
    host.propose(1, "retrieve", cost={"class": "free", "estimate": "2 queries", "network": True})
    assert host.next()["step"] == "retrieve"
    host.propose(1, "plan_test", subject=host.ref("q"), cost={"class": "metered", "estimate": "fine-tune", "training": True,
                                                                  "gpu_hours": 4})
    s = host.next()
    assert s["step"] == "authorize" and s["type"] == "human_gate" and "training" in s["notes"][0], show(s)
    with pytest.raises(AssertionError):  # an ask_human answer is not an authorization
        run_cli("study", "answer", "--project", str(host.layout.project), "--study", host.layout.slug, "--proposal", "1",
                "--text", "ok")
    run_cli("study", "answer", "--project", str(host.layout.project), "--study", host.layout.slug, "--proposal", "1",
            "--deny", "--text", "no training on this machine")
    s = host.next()
    assert s["step"] == "propose" and "denied" in s["errors"][0]
    assert host.layout.store.get("auth-001")["payload"]["source"] == "human"


def test_three_unproductive_actions_stop_the_study(host):
    intake(host)
    inputs = [[], [host.rel(host.repo / "memory.py")], [host.rel(host.repo / "probe.py")], [host.ref("kit")]]
    for n in (1, 2, 3, 4):
        host.propose(n, "retrieve", open_question=f"lead {n}", inputs=inputs[n - 1])
        s = host.next()
        assert s["step"] == "retrieve", show(s)
        rec = host.layout.store.find("lead")
        host.commit(n, "retrieve", [{"kind": "material", "id": "lead", "expected_version": rec["version"] if rec else 0,
                                     "payload": {"source": "s", "content": "the same lead again", "type": "paper", "access": "identity"}}])
        host.step_llm(s)
        s = host.drive_to("propose")
    marks = [m["productive"] for _, _, m in host.layout.commits()]
    assert marks == [True, True, False, False, False], marks
    assert s["step"] == "stuck" and "produced nothing new" in s["notes"][0], show(s)


def test_repeating_an_unproductive_action_on_the_same_inputs_is_refused(host):
    intake(host)
    for n in (1, 2, 3):
        host.propose(n, "retrieve", open_question="lead", inputs=[host.rel(host.repo / "memory.py")])
        s = host.next()
        if n == 3:
            assert any("repeats action 002" in e for e in s["errors"]), show(s)
            return
        rec = host.layout.store.find("lead")
        host.commit(n, "retrieve", [{"kind": "material", "id": "lead", "expected_version": rec["version"] if rec else 0,
                                     "payload": {"source": "s", "content": "x", "type": "paper", "access": "identity"}}])
        host.step_llm(s)
        host.drive_to("propose")


def test_retrieve_cannot_claim_a_full_text_reading_and_a_lead_cannot_support_a_finding(host):
    intake(host)
    host.propose(1, "retrieve")
    s = host.next()
    host.commit(1, "retrieve", [{"kind": "material", "id": "p1", "expected_version": 0, "payload": {
        "source": "arxiv:2501.00001", "content": "abstract", "type": "paper", "access": "fulltext"}}])
    assert any("reading is a separate action" in e for e in host.next()["errors"])
    host.commit(1, "retrieve", [{"kind": "material", "id": "p1", "expected_version": 0, "payload": {
        "source": "arxiv:2501.00001", "content": "abstract", "type": "paper", "access": "abstract"}}])
    host.step_llm(s)
    host.drive_to("propose")
    host.propose(2, "diagnose")
    s = host.next()
    host.commit(2, "diagnose", [{"kind": "assessment", "id": "f1", "expected_version": 0, "payload": {
        "type": "finding", "subject": host.ref("q"), "claim": "c", "judgment": "supported",
        "evidence": [{"id": "p1", "version": 1}], "rationale": "the abstract says so", "scope": "s"}}])
    assert any("abstract only" in e for e in host.next()["errors"])


def test_commit_and_exec_refuse_out_of_order(host):
    intake(host)
    host.propose(1, "diagnose")
    from forge.cli import main
    assert main(["study", "commit", "--project", str(host.layout.project), "--study", host.layout.slug, "--proposal", "1"]) == 2
    assert main(["study", "exec", "--project", str(host.layout.project), "--study", host.layout.slug, "--proposal", "1"]) == 2


def test_hitl_decisions_are_the_persons(tmp_path):
    h = Host(tmp_path / "p", mode="hitl")
    h.repo = fixture_repo(h.layout.project)
    s = h.routed(h.next(goal=GOAL, mode="hitl"))
    assert s["step"] == "study_init" and s["type"] == "human_gate"
    study.init(h.layout, GOAL, "hitl", budget="1 GPU-hour")
    intake(h)
    diagnose_and_plan(h)
    h.propose(3, "decide", subject=h.ref("q"))
    s = h.next()
    assert s["step"] == "decide" and s["type"] == "human_gate", show(s)
    h.commit(3, "decide", [{"kind": "assessment", "id": "d1", "expected_version": 0, "payload": {
        "type": "decision", "subject": h.ref("q"), "decision": "refine", "rationale": "model's view", "decided_by": "model"}}])
    assert any("decided_by human" in e for e in h.next()["errors"])


def test_the_kit_cannot_switch_a_protocol_off_and_needs_a_variant_per_task_type(host):
    host.next()
    host.intake(task_types=("benchmark", "theory"))
    kit = read_json(host.layout.action_dir(0, "intake") / "kit.json")
    kit["skip_protocols"] = ["plan_before_run"]
    del kit["variants"]["theory"]
    write_json(host.layout.action_dir(0, "intake") / "kit.json", kit)
    errors = host.next()["errors"]
    assert any("unknown fields ['skip_protocols']" in e for e in errors) and any("one variant file per task type" in e for e in errors)
