"""Auto-mode checkpoints: progress, anti-repeat, budget and evidence-based completion."""
import pytest

from open_scientist.records import Store

REF = lambda record_id, version=1: {"id": record_id, "version": version}  # noqa: E731
FULL = ["question", "literature", "code", "counterexamples", "test_plan", "card", "decision"]


def base(s):
    s.put("project", "q", {"question": "Why do long-horizon agents miss frames?"}, 0)


def start(s, criteria=None, max_actions=10, record_id="run"):
    return s.put("workflow", record_id, {
        "goal": "Deliver a literature-, code- and counterexample-checked research plan",
        "project": REF("q"), "criteria": criteria or FULL, "max_actions": max_actions,
        "actions_used": 0, "status": "active", "stage": "frame",
        "authorized": ["search", "read code"], "forbidden": ["training", "paid API"],
        "next_action": {"skill": "research-diagnose", "question": "Is the miss real?", "why": "Q unverified"},
    }, 0)


def step(s, previous, key, **changes):
    payload = {**previous["payload"], **changes}
    payload["last_action"] = {"key": key, "skill": "research-retrieve", "question": "Find prior work",
                              "outcome": "advanced", "summary": "Found two baselines"}
    payload["actions_used"] = previous["payload"]["actions_used"] + 1
    return s.put("workflow", previous["id"], payload, previous["version"])


def research_plan_records(s):
    """Minimal records that satisfy every default criterion for candidate h@1."""
    s.put("candidate", "h", {"problem": REF("q"), "mechanism": "Re-rank stored frames by query",
                             "claims": {"c1": "Frames are stored", "c2": "Query misses them"}}, 0)
    s.put("material", "paper", {"source": "arXiv:2501.00001", "content": "Retrieval recall drops after 200 steps",
                                "locator": "Sec 4.2"}, 0)
    s.put("material", "code", {"source": "repo@abc123", "content": "store() keeps every frame",
                               "locator": "src/memory.py:42"}, 0)
    for claim, evidence in (("c1", "code"), ("c2", "paper")):
        s.put("assessment", f"f-{claim}", {"type": "finding", "subject": REF("h"), "claim": claim,
                                           "judgment": "supported", "evidence": [REF(evidence)],
                                           "rationale": "Read the source", "scope": "This codebase"}, 0)
    s.put("activity", "t1", {"objective": "Separate storage from retrieval failure", "status": "plan",
                             "plan": "Replay 50 episodes; oracle query vs learned query", "inputs": [REF("h")]}, 0)
    s.put("material", "card", {"source": "card:construction", "content": "Method card for h@1"}, 0)
    s.put("assessment", "d1", {"type": "decision", "subject": REF("h"), "decision": "pursue",
                               "rationale": "Cheap discriminating test available"}, 0)
    return {"question": [REF("q")], "literature": [REF("f-c2")], "code": [REF("code")],
            "test_plan": [REF("t1")], "card": [REF("card")], "decision": [REF("d1")]}


def test_start_requires_project_reference_and_next_action(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = start(s)
    assert run["payload"]["status"] == "active"
    with pytest.raises(ValueError, match="next_action"):
        s.put("workflow", "run2", {**run["payload"], "next_action": None}, 0)
    s.put("material", "m", {"source": "x", "content": "y"}, 0)
    with pytest.raises(ValueError, match="project"):
        s.put("workflow", "run3", {**run["payload"], "project": REF("m")}, 0)


def test_each_recorded_action_counts_once_and_cannot_repeat(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = step(s, start(s), "retrieve:q@1:baselines")
    assert run["payload"]["actions_used"] == 1
    with pytest.raises(ValueError, match="already recorded"):
        step(s, run, "retrieve:q@1:baselines")
    skipped = {**run["payload"], "actions_used": 3,
               "last_action": {**run["payload"]["last_action"], "key": "other"}}
    with pytest.raises(ValueError, match="one action"):
        s.put("workflow", "run", skipped, run["version"])


def test_budget_cannot_be_exceeded(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = step(s, start(s, max_actions=1), "a1")
    with pytest.raises(ValueError, match="max_actions"):
        step(s, run, "a2")
    stopped = s.put("workflow", "run", {**run["payload"], "status": "stopped", "stop_reason": "budget",
                                        "summary": "Budget reached; next would be a code probe",
                                        "next_action": None}, run["version"])
    assert stopped["payload"]["status"] == "stopped"


def test_status_specific_fields_are_required(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = start(s)
    with pytest.raises(ValueError, match="question_for_user"):
        s.put("workflow", "run", {**run["payload"], "status": "waiting_user"}, 1)
    with pytest.raises(ValueError, match="stop_reason"):
        s.put("workflow", "run", {**run["payload"], "status": "stopped", "summary": "x"}, 1)
    waiting = s.put("workflow", "run", {**run["payload"], "status": "waiting_user",
                                        "question_for_user": "Change the target metric?"}, 1)
    s.put("assessment", "answer", {"type": "feedback", "subject": REF("run", 2), "source": "human",
                                   "text": "Keep the target metric"}, 0)
    resumed = s.put("workflow", "run", {**waiting["payload"], "status": "active",
                                        "question_for_user": None, "user_input": REF("answer")}, 2)
    assert resumed["version"] == 3


def test_done_is_rejected_until_every_criterion_has_current_evidence(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = start(s)
    report = s.check_workflow("run")
    assert report["ready"] is False
    assert report["criteria"]["literature"]["pass"] is False
    with pytest.raises(ValueError, match="not ready"):
        s.put("workflow", "run", {**run["payload"], "status": "done", "summary": "x", "next_action": None}, 1)

    evidence = research_plan_records(s)
    run = s.put("workflow", "run", {**run["payload"], "focus": REF("h"), "evidence": evidence}, 1)
    report = s.check_workflow("run")
    assert report["ready"] is True, report
    done = s.put("workflow", "run", {**run["payload"], "status": "done", "next_action": None,
                                     "summary": "Plan for h@1 with test t1"}, run["version"])
    assert done["payload"]["status"] == "done"
    with pytest.raises(ValueError, match="terminal"):
        s.put("workflow", "run", {**done["payload"], "status": "active",
                                  "next_action": {"skill": "x", "question": "y", "why": "z"}}, done["version"])


def test_revised_mechanism_invalidates_focus_dependent_evidence(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    start(s)
    evidence = research_plan_records(s)
    run = s.put("workflow", "run", {**s.get("run")["payload"], "focus": REF("h"), "evidence": evidence}, 1)
    s.put("candidate", "h", {"problem": REF("q"), "mechanism": "Learned frame index",
                             "claims": {"c1": "Frames are stored", "c2": "Query misses them"},
                             "parents": []}, 1)
    report = s.check_workflow("run")
    assert report["ready"] is False
    assert "h@2" in report["criteria"]["counterexamples"]["detail"]
    run = s.put("workflow", "run", {**run["payload"], "focus": REF("h", 2)}, run["version"])
    report = s.check_workflow("run")
    for name in ("counterexamples", "test_plan", "card", "decision"):
        assert report["criteria"][name]["pass"] is False, name


def test_unresolved_contrary_finding_blocks_until_dispositioned(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    start(s)
    evidence = research_plan_records(s)
    s.put("workflow", "run", {**s.get("run")["payload"], "focus": REF("h"), "evidence": evidence}, 1)
    s.put("material", "cx", {"source": "probe output", "content": "Frame 17 absent from store",
                             "locator": "runs/probe/out.json"}, 0)
    s.put("assessment", "f-cx", {"type": "finding", "subject": REF("h"), "claim": "c1",
                                 "judgment": "contradicted", "evidence": [REF("cx")],
                                 "rationale": "Legal episode loses a frame", "scope": "Episodes > 500 steps"}, 0)
    assert s.check_workflow("run")["criteria"]["counterexamples"]["pass"] is False
    s.put("material", "rerun", {"source": "probe rerun", "content": "Frame 17 present with full buffer",
                                "locator": "runs/probe/out2.json"}, 0)
    s.put("assessment", "disp", {"type": "disposition", "subject": REF("f-cx"), "outcome": "rejected",
                                 "rationale": "Probe used a truncated buffer config; rerun shows frame present",
                                 "outputs": [REF("rerun")]}, 0)
    assert s.check_workflow("run")["criteria"]["counterexamples"]["pass"] is True


def test_evidence_based_stop_needs_kill_or_park_with_material(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = start(s)
    stop = {**run["payload"], "status": "stopped", "stop_reason": "evidence_based_stop",
            "summary": "The gap is already solved", "next_action": None}
    with pytest.raises(ValueError, match="kill or park"):
        s.put("workflow", "run", stop, 1)
    s.put("material", "prior", {"source": "doi:10.1/x", "content": "Same mechanism, same setting"}, 0)
    s.put("assessment", "d", {"type": "decision", "subject": REF("q"), "decision": "kill",
                              "rationale": "Subsumed by prior work", "evidence": [REF("prior")]}, 0)
    assert s.put("workflow", "run", stop, 1)["payload"]["status"] == "stopped"


def test_evidence_keys_must_be_declared_criteria(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = start(s, criteria=["question", "literature"])
    with pytest.raises(ValueError, match="criteria"):
        s.put("workflow", "run", {**run["payload"], "evidence": {"card": [REF("q")]}}, 1)


# --- 0.2.1 fixes for the audit's reproduced bypasses -------------------------

def human(s, record_id, subject, text):
    return s.put("assessment", record_id, {"type": "feedback", "subject": subject,
                                           "source": "human", "text": text}, 0)


def ready_run(s):
    base(s)
    start(s)
    evidence = research_plan_records(s)
    return s.put("workflow", "run", {**s.get("run")["payload"], "focus": REF("h"), "evidence": evidence}, 1)


def test_contract_cannot_be_weakened_without_human_input(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = start(s)
    for change in ({"criteria": ["question"]}, {"max_actions": 500}, {"forbidden": []},
                   {"authorized": ["paid API"]}):
        with pytest.raises(ValueError, match="contract"):
            s.put("workflow", "run", {**run["payload"], **change}, 1)
    fb = human(s, "fb-budget", REF("run"), "Raise the budget to 30 actions")
    raised = s.put("workflow", "run", {**run["payload"], "max_actions": 30,
                                       "user_input": REF(fb["id"])}, 1)
    assert raised["payload"]["max_actions"] == 30


def test_stale_or_withdrawn_evidence_does_not_pass(tmp_path):
    s = Store(str(tmp_path))
    run = ready_run(s)
    assert s.check_workflow("run")["ready"] is True
    s.put("project", "q", {"question": "Revised question"}, 1)
    s.put("workflow", "run", {**run["payload"], "project": REF("q", 2)}, run["version"])
    assert s.check_workflow("run")["criteria"]["question"]["pass"] is False  # evidence still cites q@1


def test_withdrawn_literature_finding_and_failed_test_fail(tmp_path):
    s = Store(str(tmp_path))
    ready_run(s)
    s.put("assessment", "f-c2", {"type": "finding", "subject": REF("h"), "claim": "c2", "judgment": "unknown",
                                 "evidence": [], "rationale": "Source misread", "scope": "Withdrawn"}, 1)
    s.put("activity", "t1", {"objective": "Separate storage from retrieval failure", "status": "failed",
                             "plan": "Replay 50 episodes; oracle query vs learned query", "inputs": [REF("h")],
                             "failure": "Replay harness crashed"}, 1)
    report = s.check_workflow("run")
    assert report["criteria"]["literature"]["pass"] is False
    assert report["criteria"]["test_plan"]["pass"] is False


def test_contrary_history_cannot_be_erased_by_revision(tmp_path):
    s = Store(str(tmp_path))
    ready_run(s)
    s.put("material", "cx", {"source": "probe", "content": "Frame lost", "locator": "out.json"}, 0)
    s.put("assessment", "f-cx", {"type": "finding", "subject": REF("h"), "claim": "c1", "judgment": "contradicted",
                                 "evidence": [REF("cx")], "rationale": "Legal case", "scope": "L>500"}, 0)
    s.put("assessment", "f-cx", {"type": "finding", "subject": REF("h"), "claim": "c1", "judgment": "unknown",
                                 "evidence": [], "rationale": "Softened", "scope": "L>500"}, 1)
    assert s.check_workflow("run")["criteria"]["counterexamples"]["pass"] is False
    # A bare rejection without supporting output does not clear it either.
    s.put("assessment", "d-bare", {"type": "disposition", "subject": REF("f-cx"), "outcome": "rejected",
                                   "rationale": "We think it is fine"}, 0)
    assert s.check_workflow("run")["criteria"]["counterexamples"]["pass"] is False
    s.put("material", "rerun", {"source": "probe rerun", "content": "Frame present with full buffer",
                                "locator": "out2.json"}, 0)
    s.put("assessment", "d-ok", {"type": "disposition", "subject": REF("f-cx"), "outcome": "rejected",
                                 "rationale": "Truncated buffer config", "outputs": [REF("rerun")]}, 0)
    assert s.check_workflow("run")["criteria"]["counterexamples"]["pass"] is True
    s.put("assessment", "d-later", {"type": "disposition", "subject": REF("f-cx"), "outcome": "deferred",
                                    "rationale": "Reopened after review"}, 0)
    assert s.check_workflow("run")["criteria"]["counterexamples"]["pass"] is False


def test_stop_decision_must_match_current_version(tmp_path):
    s = Store(str(tmp_path))
    run = ready_run(s)
    s.put("assessment", "kill-h1", {"type": "decision", "subject": REF("h"), "decision": "kill",
                                    "rationale": "Old mechanism subsumed", "evidence": [REF("paper")]}, 0)
    s.put("candidate", "h", {"problem": REF("q"), "mechanism": "Different mechanism",
                             "claims": {"c1": "x"}}, 1)
    run = s.put("workflow", "run", {**run["payload"], "focus": REF("h", 2)}, run["version"])
    with pytest.raises(ValueError, match="kill or park"):
        s.put("workflow", "run", {**run["payload"], "status": "stopped", "stop_reason": "evidence_based_stop",
                                  "summary": "stop", "next_action": None}, run["version"])


def test_waiting_user_resumes_only_with_a_new_human_answer(tmp_path):
    s = Store(str(tmp_path))
    base(s)
    run = start(s)
    waiting = s.put("workflow", "run", {**run["payload"], "status": "waiting_user",
                                        "question_for_user": "Optimize latency or success rate?"}, 1)
    resume = {**waiting["payload"], "status": "active"}
    resume.pop("question_for_user")
    with pytest.raises(ValueError, match="human"):
        s.put("workflow", "run", resume, 2)
    fb = human(s, "fb-answer", REF("run", 2), "Success rate")
    assert s.put("workflow", "run", {**resume, "user_input": REF(fb["id"])}, 2)["version"] == 3
