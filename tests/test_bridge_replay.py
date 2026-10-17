"""Deterministic integration fixture, not an autonomous-agent quality benchmark."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from open_scientist.records import Store

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "bridge_replay.py"


def replay_module():
    if not SCRIPT.exists():
        pytest.fail("The executable bridge replay has not been implemented")
    spec = importlib.util.spec_from_file_location("bridge_replay", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_actual_code_observations_survive_question_hypothesis_and_test_revisions(tmp_path):
    module = replay_module()
    result = module.run_replay(str(tmp_path))
    assert result["synthetic"] is True
    store = Store(str(tmp_path))

    # A: a real script establishes storage exists but query lookup misses.
    a = result["cases"]["A"]
    observation = json.loads(Path(a["stdout_path"]).read_text())
    assert observation == {"stored_count": 1, "available_steps": [7], "queried_step": 8, "matched_ids": []}
    assert a["question_before"] == {"id": "question-a", "version": 1}
    assert a["question_after"] == {"id": "question-a", "version": 2}
    assert "dropped" in store.get("question-a", 1)["payload"]["question"]
    assert "lookup" in store.get("question-a", 2)["payload"]["question"]
    assert store.get(a["material"]["id"], 1)["payload"]["source"] == a["execution_path"]

    # B: the valid witness refutes the universal claim; failure is a separate event.
    b = result["cases"]["B"]
    counterexample = json.loads(Path(b["counterexample"]["stdout_path"]).read_text())
    assert counterexample["universal_claim_holds"] is False
    assert counterexample["witness"] == {"stored_step": 7, "queried_step": 8, "returned_id": None}
    old_test = store.get("test-b", 1)
    completed_test = store.get("test-b", 3)
    assert completed_test["payload"]["plan"] == old_test["payload"]["plan"]
    assert completed_test["payload"]["status"] == "completed"
    assert store.get("candidate-b", 1)["payload"]["claims"]["universal"] != store.get("candidate-b", 2)["payload"]["claims"]["universal"]
    assert store.get("test-b-revised", 1)["payload"]["status"] == "plan"
    assert store.get("test-b-revised", 1)["payload"]["inputs"][0] == {"id": "candidate-b", "version": 2}
    assert b["failed_run"]["returncode"] == 7
    assert store.get("test-b-unavailable", 3)["payload"]["status"] == "failed"
    assert not any(r["payload"].get("judgment") == "contradicted" and {"id": b["failed_run"]["material"]["id"], "version": 1} in r["payload"].get("evidence", []) for r in store.list("assessment"))

    # C: fixing the undefined operation creates a hypothesis revision, not a quiet card edit.
    c = result["cases"]["C"]
    assert "normalize_score" in Path(c["spec_probe"]["stderr_path"]).read_text()
    assert c["spec_probe"]["returncode"] != 0
    before = Path(c["card_before_path"]).read_bytes()
    assert hashlib.sha256(before).hexdigest() == c["card_before_sha256"]
    assert "undefined" in before.decode()
    assert "candidate-c@2" in Path(c["card_after_path"]).read_text()
    assert store.get("candidate-c", 1)["payload"]["mechanism"] != store.get("candidate-c", 2)["payload"]["mechanism"]
    assert store.get("decision-c", 1)["payload"]["decision"] == "park"
    assert store.get("decision-c", 1)["payload"]["revisit_when"] == "A real dataset and comparison budget become available"
    ctx = store.context()
    assert ctx["unresolved_feedback"] == []
    assert any(r["id"] == "finding-b" and r["payload"]["judgment"] == "contradicted" for r in ctx["records"])
    assert any(r["id"] == "candidate-b" and r["version"] == 1 for r in ctx["historical_inputs"])
    report = Path(result["report_path"]).read_text()
    assert "No research gain is established" in report
    assert "test-b-revised@1: plan" in report


def test_replay_refuses_nonempty_record_store_without_writing_fixture_files(tmp_path):
    module = replay_module()
    store = Store(str(tmp_path))
    store.put("project", "existing-work", {"question": "Preserve my research"}, 0)
    before = store.list()
    with pytest.raises(ValueError, match="nonempty"):
        module.run_replay(str(tmp_path))
    assert store.list() == before
    assert not (tmp_path / "bridge-replay").exists()


def test_cli_requires_existing_explicit_root_and_does_not_create_it(tmp_path):
    replay_module()
    missing = tmp_path / "missing"
    call = subprocess.run([sys.executable, str(SCRIPT), "--project-root", str(missing)], text=True, capture_output=True, timeout=20)
    assert call.returncode != 0
    assert not missing.exists()
