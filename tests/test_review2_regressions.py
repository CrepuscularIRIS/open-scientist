"""One test per finding of the 2026-10-18 design-and-runtime review (R1-R5, D1, D4, D5, E1-E5).

Each test is the review's reproduction turned around: it asserts the fixed behavior.
"""
# ruff: noqa: F811  (pytest fixtures imported from test_idea_run)
from __future__ import annotations

import copy
import json

import pytest

from conftest import Agent, host_after, walk
from forge import cluster, derive, ideas, review_gates, runs, schemas
from forge.navigator import next_domain
from forge.run_nav import next_run
from forge.util import Layout, read_json, write_json
from test_idea_run import (CANDIDATE, IdeaAgent, advance_until, audit, built_domain, drive, frozen, notes,  # noqa: F401
                           run)


class AbstractOnlyAgent(Agent):
    """Reads only abstracts; the profile claims review evidence that does not exist."""

    def read(self, batch):
        super().read(batch)
        for aid in batch:
            path = self.layout.readings_dir / f"{aid}.json"
            reading = read_json(path)
            reading["access"] = {"source": "abstract_only", "locator": f"https://arxiv.org/abs/{aid}", "sections_read": []}
            for sig in reading["signatures"]:
                sig["verified"] = "abstract_only"
            write_json(path, reading)


# --- R1: commit commands re-check the gates; DONE must match what it recorded -------------------------------

def test_r1_finish_is_refused_before_the_gates_pass(run):
    runs.init(run, "world-model-planning", "q?")
    write_json(run.file("decision.json"), {"decision": "pursue", "rationale": "r", "decided_by": "model"})
    with pytest.raises(ValueError, match="refused: the run's next step is bottleneck"):
        runs.finish(run)
    run.file("DONE").write_text("2026-10-18T00:00:00Z")  # a hand-written DONE
    assert next_run(run)["step"] == "bottleneck"


def test_r1_promote_retry_render_and_close_are_gated_too(run):
    runs.init(run, "world-model-planning", "q?")
    for call in (runs.promote_revision, runs.render, lambda r: runs.retry(r, "candidate")):
        with pytest.raises(ValueError):
            call(run)
    write_json(run.file("phase1.json"), {"state": "do_not_generate", "do_not_generate_reason": "x"})
    with pytest.raises(ValueError, match="refused"):
        runs.close(run)  # valid content, but not accepted: the navigator wants an accept step first


def test_r1_done_stops_counting_when_the_card_or_decision_changes(run):
    drive(run, IdeaAgent(run))
    assert next_run(run)["step"] == "done"
    card = read_json(run.file("idea_card.json")) | {"core_claim": "a different claim"}
    write_json(run.file("idea_card.json"), card)
    assert next_run(run)["step"] != "done"


# --- R2 lives in test_modes (round-2 packet, superseded packet) ---------------------------------------------

# --- R3: semantic upstream changes invalidate downstream -------------------------------------------------------

def test_r3_rewriting_the_bottleneck_under_the_same_gap_ids_reopens_generation(run):
    agent = IdeaAgent(run)
    advance_until(run, agent, "card")
    problem = read_json(run.file("phase1.json"))
    problem["bottleneck_statement"] = "A different failure: labels leak into evaluation."
    problem["gaps"][0]["text"] = "Need a label leakage diagnostic, not rollout scheduling."
    write_json(run.file("phase1.json"), problem)
    s = next_run(run)
    assert s["step"] == "bottleneck" and any("edited after it was accepted" in n for n in s["notes"])
    host_after(s, ("run", run.project, run.run))  # the step is redone; its provenance accepts the new problem
    s = next_run(run)
    assert s["step"] == "generate" and any("phase1.json" in n for n in s["notes"])


def test_r3_new_review_evidence_reopens_the_profile_not_only_stats(layout, agent):
    walk(layout, agent, stop_at="stats")
    layout.file("reviews.jsonl").write_text(json.dumps(
        {"review_id": "R1", "paper_ref": "arxiv:2501.00001", "text": "Missing DreamerV3.", "source": "fixture"}) + "\n")
    s = next_domain(layout)
    assert s["step"] == "profile" and any("reviews.jsonl" in n for n in s["notes"])


# --- R4 lives in test_modes (stored mode, intake gate, repair cap) -------------------------------------------

def test_r4_provenance_lists_missing_outputs_and_says_routes_are_requested(run):
    from forge.handoff import record_provenance
    runs.init(run, "world-model-planning", "q?")
    row = record_provenance(("run", run.project, run.run), "bottleneck", "local:forge-core", "auto", [run.file("phase1.json")])
    assert row["missing_outputs"] == [str(run.file("phase1.json"))] and row["observed_route"] == "unknown"


# --- R5: revisions and coherence patches change only what they are allowed to ---------------------------------

def _revise_with(run, targets, revised, applied, stop="revise"):
    agent = IdeaAgent(run, verdicts=("revise",))
    agent.audit = lambda: write_json(run.file("audit.json"), audit("revise", revision_targets=targets))
    agent.revise = lambda: (write_json(run.file("revised_candidate.json"), revised),
                            write_json(run.file("revise_notes.json"), {"applied": applied}))
    return advance_until(run, agent, stop, written="revised_candidate.json")


def test_r5_an_add_a_baseline_target_cannot_swap_the_metric_or_control(run):
    revised = copy.deepcopy(CANDIDATE)
    revised["differentiation"][0]["delta"] = "adds a DreamerV3 comparison"
    revised["falsification"]["metric"] = "wall-clock time"
    revised["falsification"]["negative_control"] = "none"
    s = _revise_with(run, [{"scope": "tactical", "target": "baseline", "instruction": "add DreamerV3",
                            "fields": ["differentiation"]}], revised,
                     [{"target_index": 0, "change": "added", "fields": ["differentiation", "falsification.metric"]}])
    assert s["step"] == "revise"
    assert any("['falsification.metric'], which target 0 does not name" in e for e in s["errors"])
    assert any("falsification.negative_control" in e and "without an applied entry" in e for e in s["errors"])


def test_r5_audit_targets_must_name_fields_inside_their_scope(run):
    refs = ideas.Refs(run.project / ".forge/domains/world-model-planning/v1")
    bad = audit("revise", revision_targets=[{"scope": "tactical", "target": "t", "instruction": "i",
                                             "fields": ["falsification.metric"]}])
    assert any("within scope tactical" in e for e in review_gates.validate_audit(bad, refs, {}, 1))


def test_r5_coherence_may_not_rewrite_premises_or_crossmap_use(run):
    agent = IdeaAgent(run)
    advance_until(run, agent, "coherence")
    refined = copy.deepcopy(CANDIDATE) | {"premises": [{"text": "x", "status": "untested", "refs": []}], "crossmap_used": []}
    write_json(run.file("refined_candidate.json"), refined)
    write_json(run.file("coherence.json"), {"verdict": "patched", "trace": "t", "claims": [], "naive_comparison": "n_a",
                                            "blocking": []})
    errors = next_run(run)["errors"]
    assert any("'crossmap_used'" in e and "'premises'" in e for e in errors)


# --- D1: cards are material, not a template --------------------------------------------------------------------

def test_d1_a_new_mechanism_with_no_card_passes_the_citation_gate(run):
    agent = IdeaAgent(run)
    advance_until(run, agent, "generate")
    novel = copy.deepcopy(CANDIDATE)
    novel["gap_closure"][0]["card_ids"] = []
    agent.generate = lambda: write_json(run.file("candidate.json"), novel)
    from test_idea_run import card
    agent.card = lambda: write_json(run.file("idea_card.json"), card(read_json(run.canonical())) | {
        "domain_landscape": {"cards": [], "timing": "no card covers this mechanism"}})
    seen, last = drive(run, agent)
    assert last["step"] == "done" and "none (new mechanism)" in run.file("idea_card.md").read_text()


# --- D4: expectations are answered per candidate, and can be not applicable or challenged ----------------------

def test_d4_a_required_expectation_can_be_answered_not_applicable_with_a_reason(run):
    advance_until(run, IdeaAgent(run), "audit")
    checks = audit()["checks"] | {"expectations": {"finding": "diagnostic claim, no benchmark", "unmet": [],
                                                   "not_applicable": [{"id": "E01", "reason": "the claim is a mechanism diagnosis"}]}}
    write_json(run.file("audit.json"), audit("advance", checks=checks))
    assert next_run(run)["step"] == "accept"  # valid: advance is allowed
    checks["expectations"]["challenged"] = [{"id": "E01", "reason": "x", "refs": []}]
    write_json(run.file("audit.json"), audit("advance", checks=checks))
    assert any("challenged convention needs evidence refs" in e for e in next_run(run)["errors"])


def test_d4_expectations_say_when_they_apply(layout, agent):
    walk(layout, agent, stop_at="profile")
    agent.profile()
    exp = read_json(layout.profile_dir / "expectations.json")
    del exp["expectations"][0]["applies_when"]
    write_json(layout.profile_dir / "expectations.json", exp)
    assert any("applies_when required" in e for e in next_domain(layout)["errors"])


# --- D5: the user's cap is locked; the model's estimate is not ------------------------------------------------

def test_d5_a_cheaper_discriminating_test_is_a_valid_revision(run):
    cheaper = copy.deepcopy(CANDIDATE)
    cheaper["falsification"]["experiment"] = "two DMC tasks, 3 seeds, same negative control"
    cheaper["resources"]["estimate"] = "2 GPU-days"
    s = _revise_with(run, [{"scope": "feasibility", "target": "cost", "instruction": "cheapest decisive test",
                            "fields": ["falsification.experiment", "resources.estimate"]}], cheaper,
                     [{"target_index": 0, "change": "fewer tasks and seeds",
                       "fields": ["falsification.experiment", "resources.estimate"]}], stop="promote")
    assert s["step"] == "promote" and not s["errors"]


def test_d5_the_budget_cap_comes_from_the_user(run):
    runs.init(run, "world-model-planning", "q?", "auto", budget="1 GPU-day")
    refs = ideas.Refs(run.domain_dir(), budget=run.meta()["budget"])
    assert any("copied verbatim" in e for e in ideas.validate_candidate(CANDIDATE, refs, {"gaps": [{"gap_id": "G1"}]}))


# --- E1: review evidence must resolve to review text -----------------------------------------------------------

def test_e1_review_strength_needs_resolvable_review_text(layout, agent):
    walk(layout, agent, stop_at="profile")
    agent.profile()
    exp = read_json(layout.profile_dir / "expectations.json")
    exp["expectations"][0].update(evidence=[{"kind": "review"}], strength="observed_in_reviews")
    write_json(layout.profile_dir / "expectations.json", exp)
    assert any("review evidence needs ref = a review_id" in e for e in next_domain(layout)["errors"])
    layout.file("reviews.jsonl").write_text(json.dumps(
        {"review_id": "R1", "paper_ref": "arxiv:2501.00001", "text": "No DreamerV3 comparison.", "source": "fixture"}) + "\n")
    exp["expectations"][0]["evidence"] = [{"kind": "review", "ref": "R1", "quote": "No DreamerV3 comparison."}]
    write_json(layout.profile_dir / "expectations.json", exp)
    targets = schemas.reading_targets(layout)
    assert schemas.validate_profile(layout, ["K01-rollout-uncertainty-pruning", "K02-priority-scheduling"], targets) == []


def test_e1_common_practice_needs_three_read_papers(layout, agent):
    walk(layout, agent, stop_at="profile")
    agent.profile()
    exp = read_json(layout.profile_dir / "expectations.json")
    exp["expectations"][0]["strength"] = "common_practice"  # evidence: one paper
    write_json(layout.profile_dir / "expectations.json", exp)
    assert any("exceeds what the evidence supports" in e for e in next_domain(layout)["errors"])


# --- E2: discovery, abstract reading and full-text reading are not the same evidence ---------------------------

def test_e2_abstract_only_readings_cannot_form_a_pattern(tmp_path):
    weak = Layout(tmp_path / "weak", "world-model-planning")
    agent = AbstractOnlyAgent(weak)
    walk(weak, agent, stop_at="cards")
    agent.cards()  # the fixture's K01 is a candidate_pattern over two abstract-only papers
    s = next_domain(weak)
    assert s["step"] == "cards" and any("read in full text (has 0)" in e for e in s["errors"])


def test_e2_an_unread_paper_cannot_ground_a_premise(run):
    advance_until(run, IdeaAgent(run), "generate")
    refs = ideas.Refs(run.domain_dir(), budget="not specified")
    candidate = copy.deepcopy(CANDIDATE)
    candidate["premises"][0]["refs"] = ["arxiv:2403.00004"]  # off-topic, never read
    errors = ideas.validate_candidate(candidate, refs, read_json(run.file("phase1.json")))
    assert any("grounded needs material read in full" in e for e in errors)


def test_e2_an_unversioned_full_text_locator_is_refused(layout, agent):
    walk(layout, agent, stop_at="read")
    agent.read(["2501.00001"])
    path = layout.readings_dir / "2501.00001.json"
    reading = read_json(path)
    reading["access"] = {"source": "arxiv_html", "locator": "https://arxiv.org/html/2501.00001", "sections_read": ["3"]}
    write_json(path, reading)
    assert any("access.version must name the arXiv version" in e for e in schemas.validate_reading(layout, "2501.00001"))


# --- E3: submission events, flagged only within a venue-year stratum -------------------------------------------

def _labels(layout, rows):
    layout.file("labels.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_e3_a_reject_then_accept_counts_as_two_submission_events(layout, agent):
    walk(layout, agent, stop_at="stats")
    _labels(layout, [{"paper_ref": "arxiv:2501.00001", "outcome": o, "venue": v, "year": y, "source": "fixture"}
                     for o, v, y in [("rejected", "A", 2024), ("accepted", "B", 2025)]])
    base = derive.outcome_stats(layout, schemas.reading_targets(layout))["base"]
    assert base["counts"] == {"rejected": 1, "accepted": 1} and base["decided"] == 2 and base["papers"] == 1


def test_e3_a_pooled_gap_alone_never_flags_an_anti_pattern(layout, agent):
    walk(layout, agent, stop_at="stats")
    rows = [{"paper_ref": "arxiv:2410.00003", "outcome": "accepted", "venue": "B", "year": 2025, "source": "f"},
            {"paper_ref": "arxiv:2501.00001", "outcome": "rejected", "venue": "A", "year": 2025, "source": "f"},
            {"paper_ref": "arxiv:2502.00002", "outcome": "rejected", "venue": "A", "year": 2025, "source": "f"}]
    _labels(layout, rows)
    index = read_json(layout.cards_dir / "index.json")
    index["cards"][0]["members"].append("2410.00003#s1")
    index["cards"][1]["members"] = []
    stats = derive.outcome_stats(layout, schemas.reading_targets(layout), min_n=1, delta_pp=-10)
    assert all(c["flag"] != "anti_pattern_candidate" for c in stats["combos"])
    assert stats["unit"] == "submission_event"


def test_e3_label_rows_must_name_the_submission(layout, agent):
    walk(layout, agent, stop_at="stats")
    _labels(layout, [{"paper_ref": "arxiv:2501.00001", "outcome": "accepted", "source": "fixture"}])
    s = next_domain(layout)
    assert s["step"] == "labels" and "venue, year" in s["errors"][0]


# --- E4: run observations are citable as lessons, not disguised as papers --------------------------------------

def test_e4_a_counterexample_may_cite_a_lesson(layout, agent):
    walk(layout, agent, stop_at="cards")
    from forge.domain import add_lesson
    row = add_lesson(layout, "pruning collapses with correlated rollouts", "run:demo/probe", [])
    agent.cards()
    index = read_json(layout.cards_dir / "index.json")
    index["cards"][0]["counterexamples"] = [{"text": "probe showed collapse", "refs": [f"lesson:{row['key']}"]}]
    write_json(layout.cards_dir / "index.json", index)
    assert schemas.validate_cards(layout, schemas.reading_targets(layout)) == []


# --- E5: clustering on tiny or non-Latin samples -------------------------------------------------------------

def test_e5_two_identical_signatures_are_near_duplicates_and_cjk_tokenizes():
    sigs = {"a#s1": {"arxiv_id": "a", "operation": "剪枝 想象 轨迹", "information": "价值 不确定性"},
            "b#s1": {"arxiv_id": "b", "operation": "剪枝 想象 轨迹", "information": "价值 不确定性"}}
    out = cluster.suggest(sigs)
    assert out["near_duplicates"] and len(out["groups"]) == 1
