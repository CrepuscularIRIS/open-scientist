"""One test per finding of the adversarial review of the study loop (2026-10-19), so each stays fixed."""
from __future__ import annotations

import json
import shlex
import sys

import pytest

from conftest import run_cli
from forge import execute, study
from forge.cli import main
from forge.util import read_json, write_json
from study_host import GOAL, Host, fixture_repo, show
from test_study import diagnose_and_plan, intake


@pytest.fixture
def host(tmp_path):
    h = Host(tmp_path / "project")
    h.repo = fixture_repo(h.layout.project)
    run_cli("study", "init", "--project", str(h.layout.project), "--study", h.layout.slug, "--goal", GOAL)
    return h


def cli(host, *args):
    return main(["study", *args, "--project", str(host.layout.project), "--study", host.layout.slug])


def test_1_the_kit_is_read_from_the_project_and_checked_by_hash(host, tmp_path, monkeypatch):
    intake(host)
    monkeypatch.chdir(tmp_path)  # the MCP server runs from the plugin root, not the project
    assert host.layout.kit()["deliverable"] == "diagnosis"
    kit_file = host.layout.resolve(host.layout.store.get("kit")["payload"]["path"])
    kit_file.write_text(kit_file.read_text().replace('"diagnosis",', '"report",', 1))
    assert host.next()["step"] == "malformed"


def test_1_an_idea_card_needs_a_finished_idea_run_not_a_material_named_like_one(host):
    intake(host, deliverable="idea_card", task_types=("mechanism",))
    host.propose(1, "retrieve")
    host.next()
    host.commit(1, "retrieve", [{"kind": "material", "id": "idea-run-fake", "expected_version": 0, "payload": {
        "source": "idea_run", "content": "x", "type": "note", "access": "identity", "scope": "outcome:done"}}])
    assert any("reserved" in e for e in host.next()["errors"])


def test_2_commands_act_only_on_the_navigators_current_proposal(host):
    intake(host)
    diagnose_and_plan(host)
    host.propose(3, "run_test", subject=host.ref("t-probe"))
    assert cli(host, "exec", "--proposal", "2") == 2
    assert cli(host, "exec", "--proposal", "3") == 0


def test_3_plan_test_cannot_write_a_completed_run(host):
    intake(host)
    host.propose(1, "plan_test", subject=host.ref("q"))
    host.next()
    host.commit(1, "plan_test", [{"kind": "activity", "id": "t-x", "expected_version": 0, "payload": {
        "objective": "o", "status": "completed", "result": "it worked", "plan": "p", "subject": host.ref("q"), "inputs": [],
        "claim": "c", "rival": "r", "predictions": {"H": "a", "rival": "b"}, "command": "true", "budget": "b", "stop_rule": "s"}}])
    assert any("only run_test starts, completes or fails" in e for e in host.next()["errors"])


def test_3_declared_outputs_must_be_new_files_under_the_runs_cwd(host):
    intake(host)
    diagnose_and_plan(host)
    (host.repo / "planted.json").write_text("{}")
    host.propose(3, "run_test", subject=host.ref("t-probe"), declared_outputs=["planted.json", "../../outside.txt"])
    host.bash(host.next())
    assert host.layout.store.find("out-003-file0") is None and host.layout.store.find("out-003-file1") is None


def test_3_a_timeout_kills_the_whole_process_group(host):
    intake(host)
    host.propose(1, "plan_test", subject=host.ref("q"))
    s = host.next()
    host.commit(1, "plan_test", [{"kind": "activity", "id": "t-long", "expected_version": 0, "payload": {
        "objective": "o", "status": "plan", "plan": "p", "subject": host.ref("q"), "inputs": [], "claim": "c", "rival": "r",
        "predictions": {"H": "a", "rival": "b"}, "command": "(sleep 2; echo late >> late.txt) & sleep 30",
        "cwd": host.rel(host.repo), "budget": "b", "stop_rule": "s"}}])
    host.step_llm(s)
    host.drive_to("propose")
    meta = host.layout.meta()
    meta["policy"]["budget"]["wall_clock_min"] = 0.01
    study.set_policy(host.layout, meta["policy"], "a person shortened runs for this test")
    host.propose(2, "run_test", subject=host.ref("t-long"))
    host.bash(host.next())
    import time
    time.sleep(2.5)
    assert host.layout.store.get("t-long")["payload"]["status"] == "failed" and not (host.repo / "late.txt").exists()


def test_4_an_approval_binds_to_the_exact_proposal_and_a_forged_one_is_ignored(host):
    intake(host)
    host.propose(1, "plan_test", subject=host.ref("q"), cost={"class": "metered", "estimate": "1 GPU-hour", "gpu_hours": 1})
    assert host.next()["step"] == "authorize"
    assert cli(host, "answer", "--proposal", "1", "--approve", "--text", "one GPU-hour is fine") == 0
    assert host.next()["step"] == "plan_test"
    host.propose(1, "plan_test", subject=host.ref("q"), cost={"class": "metered", "estimate": "fine-tune", "gpu_hours": 500,
                                                                  "training": True})
    assert host.next()["step"] == "authorize"  # the approval was for the earlier content
    write_json(host.layout.dir / "proposals" / "001.auth.json",
               {"approved": True, "proposal_sha256": study.proposal_sha(host.layout, 1)})
    assert host.next()["step"] == "authorize"  # no recorded human answer backs this file


def test_4_an_edited_policy_stops_the_study_and_a_person_changes_it_on_the_record(host):
    intake(host)
    meta = host.layout.meta()
    meta["policy"]["allow"]["training"] = True
    write_json(host.layout.file("study.json"), meta)
    assert host.next()["step"] == "policy"
    assert cli(host, "policy", "--json", json.dumps(meta["policy"]), "--text", "training allowed for this study") == 0
    assert host.next()["step"] == "propose" and host.layout.store.get("policy")["version"] == 2


def test_4_a_hand_written_committed_marker_does_not_count(host):
    intake(host)
    host.propose(1, "report")
    write_json(host.layout.action_dir(1, "report") / "COMMITTED",
               {"action": "report", "productive": True, "records": [{"id": "report", "version": 1, "kind": "material"}]})
    assert host.next()["step"] != "done"


def test_4_non_finite_costs_are_refused(host):
    intake(host)
    host.propose(1, "plan_test", subject=host.ref("q"), cost={"class": "metered", "estimate": "x", "gpu_hours": float("nan")})
    assert any("non-negative number" in e for e in host.next()["errors"])


def test_5_imported_records_go_to_a_read_only_archive(host, tmp_path):
    from forge.cli_study import ARCHIVE, import_v02
    from forge.records import Store
    old_root = tmp_path / "old"
    old_root.mkdir()
    old = Store(old_root, path=old_root / "old.sqlite3")
    old.put("project", "q", {"question": "Why?"})
    old.put("material", "m", {"source": "s", "content": "c", "type": "output", "access": "executed"})
    old.put("assessment", "f", {"type": "finding", "subject": {"id": "q", "version": 1}, "claim": "c", "judgment": "supported",
                                "evidence": [{"id": "m", "version": 1}], "rationale": "r", "scope": "s"})
    import_v02(host.layout.project, old.path)
    assert (host.layout.project / ARCHIVE).exists() and host.layout.store.find("f") is None


def test_6_only_read_records_a_full_text_reading(host):
    intake(host)
    host.propose(1, "diagnose")
    host.next()
    host.commit(1, "diagnose", [{"kind": "material", "id": "p-mem", "expected_version": 0, "payload": {
        "source": "arxiv:2501.00001", "content": "c", "type": "paper", "access": "fulltext"}}])
    assert any("only a read action records a full-text reading" in e for e in host.next()["errors"])


def test_7_a_failed_run_is_an_execution_failure_and_result_types_match_judgments(host):
    intake(host)
    host.propose(1, "plan_test", subject=host.ref("q"))
    s = host.next()
    host.commit(1, "plan_test", [{"kind": "activity", "id": "t-fail", "expected_version": 0, "payload": {
        "objective": "o", "status": "plan", "plan": "p", "subject": host.ref("q"), "inputs": [], "claim": "c", "rival": "r",
        "predictions": {"H": "a", "rival": "b"}, "command": "echo partial; exit 3", "cwd": host.rel(host.repo), "budget": "b",
        "stop_rule": "s"}}])
    host.step_llm(s)
    host.drive_to("propose")
    host.propose(2, "run_test", subject=host.ref("t-fail"))
    host.bash(host.next())
    host.drive_to("propose")
    host.propose(3, "interpret", subject=host.ref("t-fail"))
    host.next()
    finding = {"type": "finding", "subject": host.ref("q"), "claim": "c", "judgment": "supported", "result_type": "supported",
               "evidence": [{"id": "out-002-stdout", "version": 1}], "rationale": "r", "scope": "s"}
    host.commit(3, "interpret", [{"kind": "assessment", "id": "f1", "expected_version": 0, "payload": finding}])
    assert any("failed run is an execution_failure" in e for e in host.next()["errors"])
    host.commit(3, "interpret", [{"kind": "assessment", "id": "f1", "expected_version": 0,
                                  "payload": {**finding, "judgment": "contradicted", "result_type": "supported"}}])
    assert any("goes with judgment" in e for e in host.next()["errors"])


def test_8_construct_never_edits_an_existing_candidate(host):
    intake(host)
    cand = {"problem": host.ref("q"), "mechanism": "m", "claims": {"c": "x"}}
    for n, mech in ((1, "windowed retrieval drops items"), (2, "an entirely different mechanism")):
        host.propose(n, "construct", open_question=f"mechanism {n}")
        s = host.next()
        rec = host.layout.store.find("h1")
        host.commit(n, "construct", [{"kind": "candidate", "id": "h1", "expected_version": rec["version"] if rec else 0,
                                      "payload": {**cand, "mechanism": mech}}])
        if n == 1:
            host.step_llm(s)
            host.drive_to("propose")
    assert any("changing an existing one is evolve" in e for e in host.next()["errors"])


def test_9_a_study_read_commits_and_web_mode_prepares_a_study_packet(tmp_path):
    h = Host(tmp_path / "p", mode="web")
    h.repo = fixture_repo(h.layout.project)
    study.init(h.layout, GOAL, "web")
    intake(h)
    h.propose(1, "retrieve")
    s = h.next()
    h.commit(1, "retrieve", [{"kind": "material", "id": "lead", "expected_version": 0, "payload": {
        "source": "arxiv:2501.00001", "content": "abstract", "type": "paper", "access": "abstract"}}])
    h.step_llm(s)
    h.drive_to("propose")
    h.propose(2, "read", subject=h.ref("lead"))
    s = h.next()
    reading = h.layout.action_dir(2, "read") / "reading.json"
    h.commit(2, "read", [], files=[("reading.json", "{}")])
    h.commit(2, "read", [h.material("read-lead", reading, "paper", "fulltext", "summary", version="v1")])
    h.step_llm(s)
    h.drive_to("propose")  # the read committed: record-only provenance no longer leaves it stale
    h.propose(3, "construct", open_question="a mechanism")
    s = h.routed()
    assert s["type"] == "bash" and "handoff prepare" in s["run"][0] and "--study" in s["run"][0], show(s)
    run_cli(*shlex.split(s["run"][0])[2:])
    assert h.routed()["type"] == "web_handoff"


def test_10_run_test_needs_the_current_plan_version(host):
    intake(host)
    diagnose_and_plan(host)
    plan = host.layout.store.get("t-probe")
    host.propose(3, "plan_test", subject=host.ref("q"), open_question="sharpen the plan")
    s = host.next()
    host.commit(3, "plan_test", [{"kind": "activity", "id": "t-probe", "expected_version": 1,
                                  "payload": {**plan["payload"], "stop_rule": "one run, final"}}])
    host.step_llm(s)
    host.drive_to("propose")
    host.propose(4, "run_test", subject={"id": "t-probe", "version": 1})
    assert any("not the current version" in e for e in host.next()["errors"])


def test_11_the_same_lead_under_new_ids_is_not_progress_and_a_persons_answer_is(host):
    intake(host)
    for n in (1, 2):
        host.propose(n, "retrieve", inputs=[host.rel(host.repo / ("memory.py" if n == 1 else "probe.py"))])
        s = host.next()
        host.commit(n, "retrieve", [{"kind": "material", "id": f"lead-{n}", "expected_version": 0, "payload": {
            "source": "arxiv:1", "content": "the same lead", "type": "paper", "access": "identity"}}])
        host.step_llm(s)
        host.drive_to("propose")
    assert [m["productive"] for _, _, m in host.layout.commits()][1:] == [True, False]
    host.propose(3, "ask_human", reason="preference", open_question="which venue do you target?")
    assert cli(host, "answer", "--proposal", "3", "--text", "NeurIPS") == 0
    assert host.layout.commits()[-1][2]["productive"] is True


def test_12_malformed_proposals_are_fix_lines_not_crashes(host):
    intake(host)
    host.layout.proposal_path(1).parent.mkdir(parents=True, exist_ok=True)
    host.layout.proposal_path(1).write_text("[1, 2]")
    assert host.next()["step"] == "propose"
    for bad in ({"terms": "x"}, {"asset_kind": ["rubric"]}):
        action = "collision" if "terms" in bad else "adapt"
        host.propose(1, action, **bad)
        assert host.next()["step"] == "propose"


def test_12_a_seed_plus_a_non_material_ref_is_not_evidence(host):
    from forge.assets import validate_asset
    intake(host)
    asset = {"kind": "rubric", "scope": "task", "applies_when": "x", "status": "candidate", "built_from": [],
             "items": [{"dimension": "d", "meaning": "m", "signals": ["s"],
                        "evidence": ["seed:references/methods/companion-critic.md", host.ref("q")]}]}
    assert any("must be material read in full" in e for e in validate_asset(asset, host.layout.store, "rubric"))


def test_exec_refuses_a_forged_attempt(host):
    intake(host)
    diagnose_and_plan(host)
    host.propose(3, "run_test", subject=host.ref("t-probe"))
    adir = host.layout.action_dir(3, "run_test")
    adir.mkdir(parents=True)
    write_json(adir / "attempt.json", {"command": f"{sys.executable} probe.py", "started_at": "t", "exit_code": 0})
    with pytest.raises(ValueError, match="not backed"):
        execute.exec_activity(host.layout, 3)
    assert read_json(adir / "attempt.json")["exit_code"] == 0 and host.layout.store.get("t-probe")["payload"]["status"] == "plan"
