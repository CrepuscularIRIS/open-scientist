"""Run modes: the same steps and files, filled by local seats, a serial web handoff, or a human gate."""
# ruff: noqa: F811  (pytest fixtures imported from test_idea_run)
from __future__ import annotations

import json
import shlex

import pytest

from conftest import run_cli
from forge import handoff, routing, runs
from forge.run_nav import MAX_STEP_RUNS, next_run
from forge.util import read_json, read_jsonl, write_json
from test_idea_run import QUESTION, IdeaAgent, advance_until, built_domain, frozen, run  # noqa: F401


def routed(r, mode=None):
    return routing.route(next_run(r, domain="world-model-planning", question=QUESTION, mode=mode), mode, ("run", r.project, r.run))


def run_after(step):
    for cmd in step["run_after"]:
        run_cli(*shlex.split(cmd)[2:])


def sh(cmd):
    run_cli(*shlex.split(cmd)[2:])


def web_run(run, until):
    runs.init(run, "world-model-planning", QUESTION, "web")
    agent = IdeaAgent(run)
    return agent, advance_until(run, agent, until)


def test_auto_mode_fills_roles_locally_and_records_provenance(run):
    agent = IdeaAgent(run)
    advance_until(run, agent, "generate")
    s = routed(run, "auto")
    assert s["executor"] == "local:forge-core" and s["mode"] == "auto"
    agent.generate()
    run_after(s)
    row = read_jsonl(run.project / ".forge" / "provenance.jsonl")[-1]
    assert row["step"] == "generate" and row["requested_executor"] == "local:forge-core" and row["handoff"] is None
    assert row["observed_route"] == "unknown" and row["attempt"] == 1 and row["round"] == 1
    assert row["outputs"][0]["path"].endswith("candidate.json")


def test_web_mode_prepares_a_self_contained_packet_then_waits_then_ingests(run):
    agent, _ = web_run(run, "generate")
    s = routed(run)
    assert s["type"] == "bash" and "handoff prepare" in s["run"][0]
    sh(s["run"][0])
    hdir = run.dir / "handoff" / "generate-a1-r1"
    packet = (hdir / "packet.md").read_text()
    assert "# Research Forge handoff: generate (design, suggested Pro)" in packet
    assert "## Output contract" in packet and "no budget-aware pruning" in packet  # phase1 inlined
    assert "## Step notes" in packet and "Citation gate" in packet  # notes reach the web, not only the host
    assert "K01-rollout-uncertainty-pruning" in packet  # cards inlined
    assert read_json(hdir / "receipt.json")["status"] == "prepared"

    s = routed(run)
    assert s["type"] == "web_handoff" and s["executor"] == "web:Pro" and s["outputs"] == [str(hdir / "response.md")]
    run_cli("handoff", "mark", "--project", str(run.project), "--run", run.run, "--step", "generate",
            "--status", "sent", "--url", "https://chatgpt.com/c/abc")
    assert routed(run)["type"] == "web_handoff"  # still waiting: no reply saved

    (hdir / "response.md").write_text("```candidate.json\n{...}\n```")
    s = routed(run)
    assert s["type"] == "llm" and s["step"] == "generate" and s["seat"] == "forge-critic"
    assert s["inputs"][0] == str(hdir / "response.md") and any("INGEST" in n for n in s["notes"])
    agent.generate()
    run_after(s)
    receipt = read_json(hdir / "receipt.json")
    assert receipt["status"] == "returned" and receipt["conversation_url"] == "https://chatgpt.com/c/abc"
    assert read_jsonl(run.project / ".forge" / "provenance.jsonl")[-1]["handoff"] == receipt["request_id"]
    assert routed(run)["step"] == "coherence"


def test_a_handoff_is_never_prepared_twice(run):
    web_run(run, "generate")
    s = routed(run)
    sh(s["run"][0])
    from forge.cli import main
    assert main(shlex.split(s["run"][0])[2:]) == 2


def test_round_two_audit_gets_its_own_packet_not_the_round_one_reply(run):
    """Review R2: the revised candidate must be sent for audit again, not judged by the old reply."""
    agent = IdeaAgent(run, verdicts=("revise", "advance"))
    runs.init(run, "world-model-planning", QUESTION, "web")
    advance_until(run, agent, "audit")
    s = routed(run)
    sh(s["run"][0])  # prepare round-1 audit packet
    first = run.dir / "handoff" / "audit-a1-r1"
    (first / "response.md").write_text("Round 1: revise the control.\n")
    s = routed(run)
    agent.audit()
    run_after(s)
    s = advance_until(run, agent, "promote")
    sh(s["run"][0])
    s = routed(run)
    while s["step"] != "audit":  # collision on the revised terms, if any
        sh(s["run"][0])
        s = routed(run)
    assert s["type"] == "bash" and "handoff prepare" in s["run"][0] and "audit-a1-r2" in s["notes"][0]
    sh(s["run"][0])
    s = routed(run)
    assert s["type"] == "web_handoff" and str(first) not in s["inputs"][0]
    assert "revised" in (run.dir / "handoff" / "audit-a1-r2" / "packet.md").read_text()


def test_changed_inputs_supersede_a_pending_packet(run):
    agent, _ = web_run(run, "coherence")
    s = routed(run)
    sh(s["run"][0])
    hdir = run.dir / "handoff" / "coherence-a1-r1"
    (hdir / "response.md").write_text("old reply")
    changed = read_json(run.file("candidate.json")) | {"hook": "A different hook."}
    write_json(run.file("candidate.json"), changed)  # generation redone after the coherence packet was built
    handoff.record_provenance(("run", run.project, run.run), "generate", "local:forge-core", "web",
                              [run.file("candidate.json")], [run.file("phase1.json")])
    s = routed(run)
    assert s["type"] == "bash" and s["run"][0].endswith("--supersede")
    sh(s["run"][0])
    assert (run.dir / "handoff" / "coherence-a1-r1.superseded-1" / "response.md").exists()
    assert routed(run)["type"] == "web_handoff"


def test_web_mode_keeps_domain_and_card_steps_local(run, layout):
    agent = IdeaAgent(run)
    advance_until(run, agent, "card")
    runs.set_mode(run, "web", "test the card route")
    assert routed(run)["executor"] == "local:forge-critic"
    from forge.navigator import next_domain
    assert routing.route(next_domain(layout), "web", ("domain", layout.project, layout.domain))["type"] == "terminal"


def test_a_run_keeps_its_stored_mode_until_changed_on_the_record(run):
    """Review R4: a model decision in a hitl run is refused even when a later call says auto."""
    runs.init(run, "world-model-planning", QUESTION, "hitl")
    agent = IdeaAgent(run)
    s = advance_until(run, agent, "decide")
    g = routing.route(s, "auto", ("run", run.project, run.run))
    assert g["type"] == "human_gate" and g["executor"] == "human"
    agent.decide()  # writes decided_by "model"
    s = next_run(run, mode="auto")
    assert s["step"] == "decide" and "must come from the human" in s["errors"][0]
    assert "stored in run.json" in s["notes"][0]
    with pytest.raises(ValueError, match="refused"):
        runs.finish(run)
    d = read_json(run.file("decision.json")) | {"decided_by": "human"}
    run.file("decision.json").write_text(json.dumps(d))
    s = next_run(run)
    assert s["step"] == "accept"  # the person's file was written outside a routed step: record it, origin unknown
    sh(s["run"][0])
    assert next_run(run)["step"] == "finish"
    runs.set_mode(run, "auto", "the person handed the decision to the model")
    history = run.meta()["mode_history"]
    assert [h["mode"] for h in history] == ["hitl", "auto"] and history[1]["reason"].startswith("the person")


def test_hitl_asks_for_goal_and_budget_at_intake_not_before_free_searches(run, layout):
    s = routing.route(next_run(run, domain="world-model-planning", question=QUESTION, mode="hitl"), "hitl",
                      ("run", run.project, run.run))
    assert s["step"] == "run_init" and s["type"] == "human_gate" and "budget cap" in s["notes"][-1]
    runs.init(run, "world-model-planning", QUESTION, "hitl", budget="4 GPU-days, $50 API")
    assert run.meta()["budget"] == "4 GPU-days, $50 API"
    walked = routing.route(next_run(run), None, ("run", run.project, run.run))
    assert walked["type"] == "llm"  # bottleneck, local; no confirm on any search step
    assert "confirm" not in walked


def test_retry_archives_the_attempts_handoffs(run):
    agent = IdeaAgent(run, verdicts=("abandon",))
    runs.init(run, "world-model-planning", QUESTION, "web")
    s = advance_until(run, agent, "audit")
    s = routed(run)
    sh(s["run"][0])
    agent.audit()  # written locally while the web packet waits
    sh(next_run(run)["run"][0])  # accept
    s = next_run(run)
    assert s["step"] == "retry"
    runs.retry(run, "candidate")
    assert (run.archived()[0] / "handoff" / "audit-a1-r1" / "receipt.json").exists()
    assert not (run.dir / "handoff").exists()


def test_a_step_that_keeps_failing_stops_for_a_person(run):
    agent = IdeaAgent(run)
    s = advance_until(run, agent, "generate")
    for _ in range(MAX_STEP_RUNS):
        write_json(run.file("candidate.json"), {"title": f"broken {_}"})
        run_cli("provenance", "--project", str(run.project), "--run", run.run, "--step", "generate",
                "--executor", "local:forge-core", "--mode", "auto", "--output", str(run.file("candidate.json")))
    assert read_jsonl(run.project / ".forge" / "provenance.jsonl")[-1]["failed_validation"]
    s = next_run(run)
    assert s["step"] == "stuck" and s["type"] == "terminal" and s["state"] == "generate"


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        routing.resolve_mode("turbo")


def test_overview_lists_domains_and_runs_and_counts_what_waits(run):
    from forge.overview import overview
    runs.init(run, "world-model-planning", QUESTION, "hitl")
    advance_until(run, IdeaAgent(run), "decide")
    view = overview(run.project, "auto")
    assert view["exists"] and view["mode"] == "auto"
    assert view["domains"][0]["domain"] == "world-model-planning" and view["domains"][0]["current"] == 1
    assert view["runs"][0]["step"] == "decide" and view["runs"][0]["type"] == "human_gate"
    assert view["runs"][0]["run_mode"] == "hitl" and view["attention"] == 1
