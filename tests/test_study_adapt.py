"""Adaptive assets and the strict RS chains inside a study (build_domain, idea_run)."""
# ruff: noqa: F811  (pytest fixtures imported from test_idea_run)
from __future__ import annotations

import pytest

from conftest import Agent, run_cli, walk
from forge.util import Layout, write_json
from study_host import GOAL, Host, fixture_repo, show
from test_idea_run import IdeaAgent, built_domain, drive  # noqa: F401
from test_study import intake


@pytest.fixture
def host(tmp_path):
    h = Host(tmp_path / "project")
    h.repo = fixture_repo(h.layout.project)
    run_cli("study", "init", "--project", str(h.layout.project), "--study", h.layout.slug, "--goal", GOAL)
    intake(h, deliverable="exploration", task_types=("benchmark",))
    return h


def rubric(status="draft", evidence=("seed:references/methods/companion-critic.md",)):
    return {"kind": "rubric", "scope": "task", "applies_when": "a benchmark for agent memory retrieval", "status": status,
            "seeds": [{"ref": "seed:references/methods/companion-critic.md", "used": "dimension names",
                       "changed": "impact redefined as discriminative power between memory systems"}],
            "built_from": [], "items": [{"dimension": "construct validity", "meaning": "a high score requires recall across sessions",
                                         "signals": ["a lookup baseline scores low"], "evidence": list(evidence)}]}


def adapt(host, n, asset, rid="asset-rubric", kind="rubric"):
    host.propose(n, "adapt", asset_kind=kind, open_question="what does a fair review of this benchmark check?", may_change=["assets"])
    s = host.next()
    assert s["step"] == "adapt", show(s)
    path = host.layout.action_dir(n, "adapt") / f"{kind}.json"
    write_json(path, asset)
    rec = host.layout.store.find(rid)
    m = host.material(rid, path, "asset", "inspected", f"{kind} asset")
    m["expected_version"] = rec["version"] if rec else 0
    host.commit(n, "adapt", [m])
    return s


def test_a_seeded_rubric_stays_draft_and_a_lead_cannot_back_a_domain_asset(host):
    s = adapt(host, 1, rubric(status="candidate"))
    assert any("resting only on seeds stays draft" in e for e in host.next()["errors"])
    adapt(host, 1, rubric(status="draft"))
    host.step_llm(s)
    host.drive_to("propose")
    host.propose(2, "retrieve")
    s = host.next()
    host.commit(2, "retrieve", [{"kind": "material", "id": "lead", "expected_version": 0, "payload": {
        "source": "arxiv:2501.00001", "content": "abstract", "type": "paper", "access": "abstract"}}])
    host.step_llm(s)
    host.drive_to("propose")
    expectations = {"kind": "expectations", "scope": "domain", "applies_when": "memory benchmarks", "status": "candidate",
                    "built_from": [], "items": [{"id": "E01", "text": "compare with a lookup baseline", "kind": "baseline",
                                                 "applies_when": "any memory benchmark", "strength": "single_source",
                                                 "evidence": [{"id": "lead", "version": 1}]}]}
    adapt(host, 3, expectations, rid="asset-expectations", kind="expectations")
    assert any("must be material read in full" in e for e in host.next()["errors"])


def test_an_asset_is_checked_only_after_a_review_supports_its_previous_version(host):
    host.propose(1, "diagnose", open_question="does a lookup baseline score low on the pilot?")
    s = host.next()
    out = host.layout.action_dir(1, "diagnose") / "pilot.txt"
    host.commit(1, "diagnose", [], files=[("pilot.txt", "lookup baseline accuracy 0.02 on the 50-item pilot\n")])
    host.commit(1, "diagnose", [host.material("pilot", out, "output", "executed", "pilot run of the lookup baseline")])
    host.step_llm(s)
    host.drive_to("propose")
    evidence = ({"id": "pilot", "version": 1},)
    s = adapt(host, 2, rubric(status="candidate", evidence=evidence))
    host.step_llm(s)
    host.drive_to("propose")
    s = adapt(host, 3, rubric(status="checked", evidence=evidence))
    assert any("only after a review finding" in e for e in host.next()["errors"]), show(host.next())
    host.propose(3, "review", subject=host.ref("asset-rubric"), open_question="does the rubric hold on the pilot?")
    s = host.next()
    assert s["step"] == "review", show(s)
    host.commit(3, "review", [{"kind": "assessment", "id": "f-rubric", "expected_version": 0, "payload": {
        "type": "finding", "subject": host.ref("asset-rubric"), "claim": "construct validity dimension separates a lookup",
        "judgment": "supported", "evidence": [{"id": "pilot", "version": 1}], "scope": "50-item pilot",
        "rationale": "the lookup baseline scored 0.02"}}])
    host.step_llm(s)
    host.drive_to("propose")
    s = adapt(host, 4, rubric(status="checked", evidence=evidence))
    host.step_llm(s)
    assert host.drive_to("propose")["step"] == "propose"
    assert host.layout.store.get("asset-rubric")["version"] == 2


def test_build_domain_runs_rs_strict_chain_inside_the_study_and_is_absorbed(host):
    host.propose(1, "build_domain", domain="world-model-planning", topic="world models for planning",
                 cost={"class": "cheap", "estimate": "arXiv harvest, minutes", "network": True})
    s = host.next()
    assert s["step"] == "init" and s["scope"][0] == "domain", show(s)
    dom = Layout(host.layout.project, "world-model-planning")
    walk(dom, Agent(dom))  # the host follows the domain navigator's own steps
    s = host.next()
    assert s["step"] == "absorb", show(s)
    host.bash(s)
    bundle = host.layout.store.get("domain-world-model-planning")
    assert bundle["payload"]["type"] == "asset" and bundle["payload"]["path"].endswith("v1/manifest.json")


def test_idea_run_is_absorbed_as_candidate_and_decision(host, built_domain):
    import shutil
    shutil.copytree(built_domain.project / ".forge" / "domains", host.layout.project / ".forge" / "domains")
    host.propose(1, "idea_run", run="memory-idea", domain="world-model-planning")
    s = host.next()
    assert s["step"] == "run_init" and s["scope"][0] == "run", show(s)
    from forge.runs import RunLayout
    run = RunLayout(host.layout.project, "memory-idea")
    seen, last = drive(run, IdeaAgent(run))
    assert last["step"] == "done"
    s = host.next()
    assert s["step"] == "absorb", show(s)
    host.bash(s)
    cand = host.layout.store.get("absorbed-h-memory-idea")
    assert cand["payload"]["problem"] == {"id": "q", "version": 1} and "core" in cand["payload"]["claims"]
    assert host.layout.store.get("absorbed-decision-memory-idea")["payload"]["decision"] == "pursue"
