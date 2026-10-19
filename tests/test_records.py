"""Record kernel: the Open Scientist 0.2 behavioural tests, ported to the standard-library store."""
import importlib
import sqlite3

import pytest


def store(root):
    try:
        records = importlib.import_module("forge.records")
    except ModuleNotFoundError:
        pytest.fail("The shared-record runtime has not been implemented")
    return records.Store(str(root))


def project(s):
    return s.put("project", "project", {"question": "Why does retrieval fail?"}, 0)


def candidate(s, record_id="candidate"):
    return s.put("candidate", record_id, {
        "problem": {"id": "project", "version": 1},
        "mechanism": "Query misses the relevant frame",
        "claims": {"c1": "The frame still exists in storage"},
    }, 0)


def test_reading_empty_project_does_not_create_store(tmp_path):
    s = store(tmp_path)
    assert s.list() == []
    assert not (tmp_path / ".forge").exists()


def test_history_keeps_exact_prior_question_after_revision(tmp_path):
    s = store(tmp_path)
    project(s)
    updated = s.put("project", "project", {"question": "Why does the query miss?"}, 1)
    assert updated["version"] == 2
    assert s.get("project", 1)["payload"]["question"] == "Why does retrieval fail?"
    assert [r["version"] for r in s.history("project")] == [1, 2]


def test_stale_writer_cannot_overwrite_new_question(tmp_path):
    s = store(tmp_path)
    project(s)
    s.put("project", "project", {"question": "New question"}, 1)
    with pytest.raises(ValueError, match="revision conflict"):
        s.put("project", "project", {"question": "Stale write"}, 1)
    assert s.get("project")["payload"]["question"] == "New question"


def test_reference_to_prior_project_version_stays_exact(tmp_path):
    s = store(tmp_path)
    project(s)
    s.put("project", "project", {"question": "Changed question"}, 1)
    c = candidate(s)
    assert c["payload"]["problem"] == {"id": "project", "version": 1}


def test_dangling_and_cross_project_references_are_rejected(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    project(store(a))
    with pytest.raises(ValueError, match="reference"):
        candidate(store(b))
    s = store(a)
    with pytest.raises(ValueError, match="reference"):
        s.put("candidate", "bad", {
            "problem": {"id": "project", "version": 99},
            "mechanism": "No valid input", "claims": {"c": "A claim"},
        }, 0)


def test_identity_cannot_change_record_kind(tmp_path):
    s = store(tmp_path)
    project(s)
    with pytest.raises(ValueError, match="kind"):
        s.put("material", "project", {"source": "paper:1", "content": "A quote"}, 1)


def test_relative_or_missing_root_is_not_silently_created(tmp_path):
    with pytest.raises(ValueError, match="absolute"):
        store(".")
    with pytest.raises(ValueError, match="existing"):
        store(tmp_path / "missing")
    assert not (tmp_path / "missing").exists()


def test_database_rejects_mutation_of_record_history(tmp_path):
    s = store(tmp_path)
    project(s)
    with sqlite3.connect(tmp_path / ".forge" / "records.sqlite3") as db:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            db.execute("DELETE FROM records")


def material(s, record_id="observation"):
    return s.put("material", record_id, {"source": "run:baseline", "content": "The stored frame is present"}, 0)


def finding(s, record_id="finding", judgment="contradicted"):
    return s.put("assessment", record_id, {
        "type": "finding", "subject": {"id": "candidate", "version": 1},
        "claim": "c1", "judgment": judgment,
        "evidence": [{"id": "observation", "version": 1}],
        "rationale": "Controlled observation challenges this claim", "scope": "This fixture only",
    }, 0)


def test_material_cannot_claim_global_support(tmp_path):
    s = store(tmp_path)
    with pytest.raises(ValueError):
        s.put("material", "paper", {"source": "doi:x", "content": "quote", "supports": True}, 0)


def test_finding_must_name_real_claim_in_exact_candidate_version(tmp_path):
    s = store(tmp_path)
    project(s)
    candidate(s)
    material(s)
    p = finding(s)["payload"]
    p["claim"] = "nonexistent"
    with pytest.raises(ValueError, match="claim"):
        s.put("assessment", "bad", p, 0)


def test_plan_cannot_be_used_as_evidence_or_claim_execution(tmp_path):
    s = store(tmp_path)
    project(s)
    candidate(s)
    plan = {"objective": "Check c1", "status": "plan", "plan": "Read stored frame", "inputs": [{"id": "candidate", "version": 1}]}
    s.put("activity", "probe", plan, 0)
    with pytest.raises(ValueError):
        s.put("activity", "false-result", {**plan, "result": "it worked"}, 0)
    with pytest.raises(ValueError, match="material"):
        s.put("assessment", "bad", {
            "type": "finding", "subject": {"id": "candidate", "version": 1},
            "claim": "c1", "judgment": "supported", "rationale": "Only a plan",
            "scope": "No run", "evidence": [{"id": "probe", "version": 1}],
        }, 0)


def test_started_activity_cannot_rewrite_prediction_or_reopen(tmp_path):
    s = store(tmp_path)
    project(s)
    plan = {"objective": "Compare explanations", "status": "plan", "plan": "Prediction: A increases, B decreases", "inputs": [{"id": "project", "version": 1}]}
    s.put("activity", "probe", plan, 0)
    running = {**plan, "status": "running"}
    s.put("activity", "probe", running, 1)
    with pytest.raises(ValueError, match="frozen"):
        s.put("activity", "probe", {**running, "plan": "Prediction rewritten after seeing results"}, 2)
    completed = {**running, "status": "completed", "result": "A increased"}
    s.put("activity", "probe", completed, 2)
    with pytest.raises(ValueError, match="transition"):
        s.put("activity", "probe", running, 3)


def test_failed_execution_does_not_create_scientific_rejection(tmp_path):
    s = store(tmp_path)
    project(s)
    s.put("activity", "probe", {"objective": "Read data", "status": "failed", "plan": "Open dataset", "inputs": [], "failure": "Dataset unreachable"}, 0)
    assert s.list("assessment") == []
    with pytest.raises(ValueError):
        s.put("activity", "false-completion", {"objective": "Read data", "status": "completed", "plan": "Open data", "inputs": []}, 0)


def test_context_preserves_old_inputs_and_more_than_ten_contrary_findings(tmp_path):
    s = store(tmp_path)
    project(s)
    candidate(s)
    material(s)
    for n in range(12):
        finding(s, f"finding-{n}")
    s.put("project", "project", {"question": "A changed question"}, 1)
    ctx = s.context({"id": "candidate", "version": 1})
    assert len([r for r in ctx["records"] if r["kind"] == "assessment"]) == 12
    assert any(r["id"] == "project" and r["version"] == 1 for r in ctx["historical_inputs"])
    assert any(n["used"] == {"id": "project", "version": 1} and n["latest_version"] == 2 for n in ctx["stale_inputs"])


def test_feedback_is_unresolved_until_disposition_and_deferred_stays_open(tmp_path):
    s = store(tmp_path)
    project(s)
    s.put("assessment", "feedback", {"type": "feedback", "subject": {"id": "project", "version": 1}, "source": "human", "text": "Check the evaluation code"}, 0)
    assert len(s.context()["unresolved_feedback"]) == 1
    p = {"type": "disposition", "subject": {"id": "feedback", "version": 1}, "outcome": "deferred", "rationale": "Need access to evaluation code"}
    s.put("assessment", "response", p, 0)
    assert len(s.context()["unresolved_feedback"]) == 1
    material(s)
    s.put("assessment", "response", {**p, "outcome": "adopted", "outputs": [{"id": "observation", "version": 1}]}, 1)
    assert s.context()["unresolved_feedback"] == []


def test_context_retains_prior_contradiction_after_finding_revision(tmp_path):
    s = store(tmp_path)
    project(s)
    candidate(s)
    material(s)
    old = finding(s)
    s.put("assessment", "finding", {**old["payload"], "judgment": "unknown", "rationale": "Counterexample may use an invalid setting"}, 1)
    assert any(r["id"] == "finding" and r["version"] == 1 for r in s.context()["prior_contrary_findings"])


def test_store_symlink_cannot_redirect_writes_outside_explicit_project(tmp_path):
    root = tmp_path / "project"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / ".forge").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        project(store(root))
    assert list(outside.iterdir()) == []


def test_claim_names_id_and_version_are_not_interpreted_as_record_reference(tmp_path):
    s = store(tmp_path)
    project(s)
    c = s.put("candidate", "candidate", {
        "problem": {"id": "project", "version": 1}, "mechanism": "A mechanism",
        "claims": {"id": "ID changes correlate with retrieval", "version": "Version drift is measurable"},
    }, 0)
    assert c["payload"]["claims"]["version"] == "Version drift is measurable"
    assert len(s.context()["records"]) == 2


def test_prior_contrary_finding_keeps_its_exact_old_material(tmp_path):
    s = store(tmp_path)
    project(s)
    candidate(s)
    material(s)
    old = finding(s)
    s.put("material", "observation", {"source": "run:recheck", "content": "Different conditions"}, 1)
    s.put("assessment", "finding", {**old["payload"], "judgment": "unknown", "evidence": [{"id": "observation", "version": 2}]}, 1)
    ctx = s.context()
    assert any(r["id"] == "observation" and r["version"] == 1 for r in ctx["historical_inputs"])


def test_scientific_finding_cannot_be_retyped_as_investment_decision(tmp_path):
    s = store(tmp_path)
    project(s)
    candidate(s)
    material(s)
    finding(s)
    with pytest.raises(ValueError, match="assessment type"):
        s.put("assessment", "finding", {"type": "decision", "subject": {"id": "candidate", "version": 1}, "decision": "kill", "rationale": "No budget"}, 1)


def test_read_version_rejects_boolean_instead_of_treating_it_as_one(tmp_path):
    s = store(tmp_path)
    project(s)
    with pytest.raises(ValueError, match="version"):
        s.get("project", True)


def test_feedback_revision_does_not_erase_unconsumed_prior_instruction(tmp_path):
    s = store(tmp_path)
    project(s)
    feedback = {"type": "feedback", "subject": {"id": "project", "version": 1}, "source": "human", "text": "Use no external API"}
    s.put("assessment", "feedback", feedback, 0)
    s.put("assessment", "feedback", {**feedback, "text": "Read local code first"}, 1)
    ctx = s.context()
    assert [(r["id"], r["version"]) for r in ctx["unresolved_feedback"]] == [("feedback", 1), ("feedback", 2)]
    assert any(r["id"] == "feedback" and r["version"] == 1 for r in ctx["historical_inputs"])
    s.put("assessment", "supersession", {
        "type": "disposition", "subject": {"id": "feedback", "version": 1},
        "outcome": "superseded", "rationale": "Explicitly superseded for this fixture",
        "outputs": [{"id": "feedback", "version": 2}],
    }, 0)
    assert [(r["id"], r["version"]) for r in s.context()["unresolved_feedback"]] == [("feedback", 2)]


def test_a_v02_store_is_imported_unchanged_and_workflow_records_are_skipped(tmp_path):
    """0.2 wrote <project>/.open-scientist/records.sqlite3 with the same table; 0.3 copies its history verbatim."""
    old_root = tmp_path / "old"
    old_root.mkdir()
    old = importlib.import_module("forge.records").Store(str(old_root), path=old_root / ".open-scientist" / "records.sqlite3")
    old.put("project", "project", {"question": "Why does retrieval fail?"}, 0)
    old.put("project", "project", {"question": "Why does retrieval truncate?", "change_note": "probe"}, 1)
    with sqlite3.connect(old.path) as conn:  # a 0.2 workflow checkpoint, which 0.3 does not port
        conn.execute("INSERT INTO records VALUES ('wf', 1, 'workflow', 't', '{\"criteria\": {}}')")
    new_root = tmp_path / "new"
    new_root.mkdir()
    from forge.cli_study import ARCHIVE, import_v02
    result = import_v02(new_root, old.path)
    assert result["imported"] == 2 and result["skipped_workflow_records"] == ["wf"]
    archive = store(new_root).__class__(str(new_root), path=new_root / ARCHIVE)
    assert [r["payload"]["question"] for r in archive.history("project")] == ["Why does retrieval fail?", "Why does retrieval truncate?"]
    with pytest.raises(ValueError, match="written once"):
        import_v02(new_root, old.path)
