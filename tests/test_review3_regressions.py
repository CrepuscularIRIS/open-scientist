"""One test per finding of the third (adversarial) review of the gate fixes, F1-F10."""
# ruff: noqa: F811  (pytest fixtures imported from test_idea_run)
from __future__ import annotations

import copy
import json
import shutil

from conftest import host_after, walk
from forge import ideas, runs, schemas
from forge.cli import main
from forge.navigator import next_domain
from forge.run_nav import next_run
from forge.util import read_json, write_json
from test_idea_run import (CANDIDATE, QUESTION, IdeaAgent, act, advance_until, built_domain, drive, frozen,  # noqa: F401
                           run)


def provenance(run, step, output):
    return main(["provenance", "--project", str(run.project), "--run", run.run, "--step", step,
                 "--executor", "local:x", "--mode", "auto", "--output", str(run.file(output))])


def test_f1_provenance_cannot_restamp_stale_outputs_or_skip_ahead(run):
    advance_until(run, IdeaAgent(run), "finish")
    problem = read_json(run.file("phase1.json")) | {"bottleneck_statement": "A different problem."}
    write_json(run.file("phase1.json"), problem)
    assert provenance(run, "card", "idea_card.json") == 2  # not the step the navigator is at
    assert provenance(run, "bottleneck", "phase1.json") == 0  # the edited step itself may be recorded
    assert provenance(run, "generate", "candidate.json") == 2  # unchanged candidate, changed problem: refused
    assert next_run(run)["step"] == "generate"


def test_f2_touching_a_stale_output_keeps_it_stale(run):
    agent = IdeaAgent(run)
    advance_until(run, agent, "card")
    problem = read_json(run.file("phase1.json")) | {"bottleneck_statement": "A different problem."}
    write_json(run.file("phase1.json"), problem)
    host_after(next_run(run), ("run", run.project, run.run))
    run.file("candidate.json").write_text(run.file("candidate.json").read_text() + "\n")  # touch
    s = next_run(run)
    assert s["step"] == "generate" and any("phase1.json" in n for n in s["notes"])


def test_f3_an_unpromoted_round_one_revision_is_never_canonical(run):
    agent = IdeaAgent(run, verdicts=("revise",))
    advance_until(run, agent, "promote")  # a valid revision exists
    s = next_run(run)
    write_json(run.file("audit.json"), read_json(run.file("audit.json")) | {"verdict": "advance", "revision_targets": []})
    s = next_run(run)
    assert s["step"] == "audit"  # an edited audit goes back through its step
    host_after(s, ("run", run.project, run.run))
    s = next_run(run)
    assert s["step"] == "card" and run.canonical() == run.file("candidate.json") and s["inputs"][0] == str(run.file("candidate.json"))


def test_f4_changing_the_promoted_revision_stops_round_two(run):
    agent = IdeaAgent(run, verdicts=("revise", "advance"))
    advance_until(run, agent, "promote")
    act(run, agent, next_run(run))
    revised = read_json(run.file("revised_candidate.json"))
    revised["falsification"]["metric"] = "wall-clock time"
    write_json(run.file("revised_candidate.json"), revised)
    s = next_run(run)
    assert s["step"] == "revision_changed" and "revised_candidate.json changed" in s["errors"][0]


def test_f5_f6_malformed_files_become_fix_lines_not_crashes(run, layout):
    agent = IdeaAgent(run, verdicts=("revise", "advance"))
    advance_until(run, agent, "promote")
    act(run, agent, next_run(run))
    for name in ("revised_candidate.json", "audit_round1.json"):
        saved = run.file(name).read_text()
        run.file(name).write_text("not json{")
        assert next_run(run)["step"] == "revision_changed"
        run.file(name).write_text(saved)
    from conftest import Agent
    domain = layout.__class__(layout.project.parent / "fuzz", "world-model-planning")
    a = Agent(domain)
    walk(domain, a, stop_at="triage")
    a.triage()
    tri = read_json(domain.file("triage.json"))
    tri["papers"][0]["arxiv_id"] = ["not", "a", "string"]
    write_json(domain.file("triage.json"), tri)
    s = next_domain(domain)
    assert s["step"] == "triage" and "malformed structure" in s["errors"][0]


def test_f7_moving_the_project_keeps_acceptance(run):
    advance_until(run, IdeaAgent(run), "decide")
    moved = run.project.parent / "moved"
    shutil.move(str(run.project), str(moved))
    assert next_run(runs.RunLayout(moved, run.run))["step"] == "decide"


def test_f8_a_changed_reading_reopens_the_cards(layout, agent):
    walk(layout, agent, stop_at="stats")
    path = layout.readings_dir / "2502.00002.json"
    reading = read_json(path)
    reading["signatures"][0]["failure_boundary"] = "works with sparse rewards"
    write_json(path, reading)
    seen, _ = walk(layout, agent, stop_at="cards")
    assert seen[-1] == "cards"


def test_f9_a_review_quote_must_be_in_the_review_and_about_a_domain_paper(layout, agent):
    walk(layout, agent, stop_at="profile")
    agent.profile()
    rows = [{"review_id": "R1", "paper_ref": "arxiv:2501.00001", "text": "Nice writing.", "source": "f"},
            {"review_id": "R2", "paper_ref": "arxiv:1111.11111", "text": "Needs MuZero.", "source": "f"}]
    layout.file("reviews.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    exp = read_json(layout.profile_dir / "expectations.json")
    targets = schemas.reading_targets(layout)
    cards = ["K01-rollout-uncertainty-pruning", "K02-priority-scheduling"]
    for ref, quote, message in (("R1", "Reviewers demand a MuZero baseline.", "quote is not in review"),
                                ("R2", "Needs MuZero.", "review_id in reviews.jsonl")):
        exp["expectations"][0].update(evidence=[{"kind": "review", "ref": ref, "quote": quote}], strength="observed_in_reviews")
        write_json(layout.profile_dir / "expectations.json", exp)
        assert any(message in e for e in schemas.validate_profile(layout, cards, targets))


def test_f10_done_covers_the_question_and_collision_and_checks_integrity_first(run, frozen):
    drive(run, IdeaAgent(run))
    run.file("question.txt").write_text("another question\n")
    assert next_run(run)["step"] != "done"
    run.file("question.txt").write_text(QUESTION + "\n")
    assert next_run(run)["step"] == "done"
    brief = frozen.version_dir(1) / "brief.md"
    brief.write_text(brief.read_text() + "tampered\n")
    assert next_run(run)["step"] == "domain_changed"


def test_f10_reordering_gaps_or_cards_is_not_a_change():
    base = copy.deepcopy(CANDIDATE)
    base["gap_closure"] = [{"gap_id": "G1", "card_ids": ["A", "B"], "how_closed": "x"},
                           {"gap_id": "G2", "card_ids": [], "how_closed": "y"}]
    reordered = copy.deepcopy(base)
    reordered["gap_closure"] = [base["gap_closure"][1], {**base["gap_closure"][0], "card_ids": ["B", "A"]}]
    assert ideas.changed_fields(base, reordered) == set()
    extra = copy.deepcopy(base)
    extra["gap_closure"][0]["claim"] = "new"
    assert ideas.changed_fields(base, extra) == {"gap_closure.claim"}
