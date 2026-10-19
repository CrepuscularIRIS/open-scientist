"""Idea layer end to end on a frozen fixture domain: gates, hard floor, revise, retry, lessons back to the domain."""
from __future__ import annotations

import copy
from datetime import date, timedelta
import shutil

import pytest

from conftest import atom, host_after, run_cli, run_step_command, walk
from forge import runs
from forge.run_nav import next_run
from forge.util import read_json, read_jsonl, write_json

QUESTION = "How can a planner spend fewer imagined rollouts without losing return?"

CANDIDATE = {
    "title": "Budgeted rollout pruning", "hook": "Spend imagination where values disagree.",
    "gap_closure": [{"gap_id": "G1", "card_ids": ["K01-rollout-uncertainty-pruning", "K02-priority-scheduling"],
                     "how_closed": "priority queue over value disagreement"}],
    "core_mechanism": "Schedule rollouts by ensemble disagreement under a fixed budget.",
    "mechanism_steps": ["estimate disagreement", "queue rollouts", "expand top-k"],
    "premises": [{"text": "values are calibrated", "status": "grounded", "refs": ["2501.00001#s1"]},
                 {"text": "disagreement tracks error", "status": "untested", "refs": []}],
    "naive_baseline": {"naive": "random pruning", "why_insufficient": "ignores value error", "branch": "false_premise"},
    "falsification": {"experiment": "DMC at fixed budget", "metric": "return", "direction": "increase",
                      "load_bearing_variable": "disagreement signal", "negative_control": "shuffled disagreement returns to baseline"},
    "resources": {"authorized_limit": "not specified", "estimate": "20 GPU-days for the full DMC campaign"},
    "differentiation": [{"ref": "arxiv:2501.00001", "delta": "budgeted queue instead of a threshold"}],
    "almost_prior": {"ref": "arxiv:2502.00002", "missed_step": "no budget-aware scheduling"},
    "signature_terms": ["budgeted rollout pruning", "disagreement rollout scheduling"], "alias_terms": ["selective planning"],
    "crossmap_used": [0],
    "alternatives_considered": [{"title": "learned pruning", "why_not_chosen": "needs labels"},
                                {"title": "fixed threshold", "why_not_chosen": "already done"}]}


def audit(verdict="advance", **over):
    a = {"checks": {"card_failure_modes": {"finding": "sparse rewards addressed", "triggered": False, "refs": []},
                    "operation_applied": {"finding": "applied", "status": "applied", "refs": []},
                    "anti_patterns": {"finding": "no labels", "triggered": False, "refs": []},
                    "paper_threat": {"finding": "partial", "threat_ref": "arxiv:2501.00001", "kind": "partial_overlap"},
                    "falsification_structure": {"finding": "ok", "ok": True, "numeric_bar_provenance": "none"},
                    "expectations": {"finding": "DreamerV3 compared", "unmet": []}},
         "blocking_dispositions": [],
         "critic": {k: 3 for k in ("novelty", "impact", "timing", "feasibility", "competition", "nugget", "narrative")} | {"nugget_sentence": "x"},
         "strategy": {"timing_basis": "recent_share 1.0", "scoop_risk": "medium", "note": ""},
         "verdict": verdict, "verdict_rationale": "per checks", "revision_targets": [], "lessons": []}
    for key, value in over.items():
        a[key] = value
    return a


def card(final):
    return {"title": final["title"], "hook": final["hook"], "abstract_draft": "abs",
            "motivation": {"why_prior_stopped": "thresholds", "stakes": "compute"}, "core_claim": "claim",
            "sub_claims": ["c1"], "method_flow": ["S1: estimate"], "key_equations": [],
            "falsification": final["falsification"], "resources": final["resources"],
            "almost_prior": final["almost_prior"], "differentiation": final["differentiation"],
            "expectation_coverage": [{"expectation_id": "E01", "status": "met", "how": "DreamerV3 on DMC"}],
            "reviewer_concerns": [{"concern": "overlap with 2501.00001", "response": "budgeted", "source": "collision"}],
            "feasibility": "standard", "kill_switch": {"condition": "no gain at 50% budget", "action": "stop"},
            "domain_landscape": {"cards": ["K01-rollout-uncertainty-pruning"], "timing": "active area"},
            "plain_summary": "plain"}


class IdeaAgent:
    def __init__(self, run, verdicts=("advance",), coherence_blocking=()):
        self.run, self.verdicts, self.blocking, self.audits = run, list(verdicts), list(coherence_blocking), 0
        self.decision = "pursue"

    def bottleneck(self):
        write_json(self.run.file("phase1.json"), {
            "state": "proceed", "bottleneck_statement": "pruning ignores budgets",
            "refs": ["arxiv:2501.00001", "2502.00002#s1"],
            "closest_adjacent": [{"ref": "arxiv:2501.00001", "residue": "no budget"}],
            "gaps": [{"gap_id": "G1", "text": "no budget-aware pruning", "stakes": "wasted compute", "refs": ["2501.00001#s1"]}],
            "do_not_generate_reason": None})

    def generate(self):
        write_json(self.run.file("candidate.json"), copy.deepcopy(CANDIDATE))

    def coherence(self):
        write_json(self.run.file("coherence.json"), {"verdict": "pass", "trace": "dry-run ok",
                                                     "claims": [{"claim": "c", "grade": "empirical"}],
                                                     "naive_comparison": "confronts_obstacle", "blocking": self.blocking})

    def audit(self):
        verdict = self.verdicts[min(self.audits, len(self.verdicts) - 1)]
        self.audits += 1
        extra = {}
        if verdict == "revise":
            extra["revision_targets"] = [{"scope": "falsification", "target": "control", "instruction": "tighten control",
                                          "fields": ["falsification.negative_control"]}]
        if verdict == "abandon":
            extra["lessons"] = [{"kind": "subsumption" if "subsume" in str(self.verdicts) else "failure_mode",
                                 "text": f"lesson {self.audits if 'new' in str(self.verdicts) else 1}", "refs": []}]
            extra["checks"] = audit()["checks"] | {"card_failure_modes": {"finding": "sparse", "triggered": True, "refs": []}}
        if self.blocking:
            extra["blocking_dispositions"] = [{"index": 0, "disposition": "refuted", "reason": "arithmetic slip"}]
        write_json(self.run.file("audit.json"), audit(verdict, **extra))

    def revise(self):
        revised = copy.deepcopy(read_json(self.run.canonical()))
        revised["falsification"]["negative_control"] = "permuted disagreement across states returns to baseline"
        write_json(self.run.file("revised_candidate.json"), revised)
        write_json(self.run.file("revise_notes.json"), notes())

    def card(self):
        write_json(self.run.file("idea_card.json"), card(read_json(self.run.canonical())))

    def decide(self):
        write_json(self.run.file("decision.json"), {"decision": self.decision, "rationale": "evidence on disk",
                                                    "revisit_conditions": "when labels exist", "decided_by": "model"})


def collision_fetch(url):
    """A recent paper inside both windows, which are anchored on the run's creation date (today in tests)."""
    recent = (date.today() - timedelta(days=20)).isoformat()
    return atom([("2507.00007", "Budgeted pruning of rollouts", recent, "budgeted rollout pruning")])


def notes(change="permuted", fields=("falsification.negative_control",)):
    return {"applied": [{"target_index": 0, "change": change, "fields": list(fields)}]}


def act(run, agent, s, domain="world-model-planning", fetcher=None, mode="auto"):
    """Do one step the way a host would: run bash steps, let the agent write LLM outputs, then record provenance."""
    if s["step"] == "run_init":
        runs.init(run, domain, QUESTION, mode)
    elif s["step"] == "collision":
        runs.collide(run, fetcher=fetcher or collision_fetch)
    elif s["step"] == "retry":
        runs.retry(run, s["run"][0].rsplit(" ", 1)[1])
    elif s["step"] in {"render", "finish", "close_dng", "promote", "accept"}:
        run_step_command(s)
    else:
        getattr(agent, s["step"])()
        host_after(s, ("run", run.project, run.run), mode)


def drive(run, agent, domain="world-model-planning", limit=40, mode="auto"):
    seen = []
    for _ in range(limit):
        s = next_run(run, domain=domain, question=QUESTION, mode=mode)
        seen.append(s["step"])
        if s["type"] == "terminal":
            return seen, s
        act(run, agent, s, domain, mode=mode)
    raise AssertionError(seen)


def advance_until(run, agent, stop, written=None, limit=14):
    """Drive the run until the navigator asks for `stop` (after `written` exists, if given)."""
    for _ in range(limit):
        s = next_run(run, domain="world-model-planning", question=QUESTION)
        if s["step"] == stop and (written is None or run.file(written).exists()):
            return s
        act(run, agent, s)
    raise AssertionError(f"never reached {stop}")


@pytest.fixture(scope="session")
def built_domain(tmp_path_factory):
    """Build and freeze the fixture domain once; each test gets its own copy."""
    from conftest import Agent
    from forge.util import Layout
    base = Layout(tmp_path_factory.mktemp("domain") / "project", "world-model-planning")
    walk(base, Agent(base, strength="common_practice"))  # E01 is a required expectation
    return base


@pytest.fixture
def frozen(built_domain, layout):
    shutil.copytree(built_domain.project, layout.project)
    return layout


@pytest.fixture
def run(frozen):
    return runs.RunLayout(frozen.project, "budgeted-pruning")


def test_advance_path_reaches_a_rendered_card_and_decision(run):
    seen, last = drive(run, IdeaAgent(run))
    assert seen == ["run_init", "bottleneck", "generate", "coherence", "collision", "audit", "card", "render",
                    "decide", "finish", "done"]
    text = run.file("idea_card.md").read_text()
    assert "Budgeted rollout pruning" in text and "E01 — **met**" in text and "domain `world-model-planning` v1" in text
    hits = read_jsonl(run.file("collision") / "papers.jsonl")
    assert hits[0]["arxiv_id"] == "2507.00007" and hits[0]["channels"] == ["signature", "alias"]
    terms = read_json(run.file("collision") / "terms.json")
    assert terms["windows"] == {"signature_months": 10, "alias_months": 48}
    assert "value uncertainty rollout pruning" in terms["signature_terms"]  # cited card's lexicon terms join the channel


def test_run_requires_a_frozen_domain(layout):
    r = runs.RunLayout(layout.project, "early")
    with pytest.raises(ValueError, match="no frozen version"):
        runs.init(r, "world-model-planning", QUESTION)


def test_citation_gate_rejects_unknown_cards_and_papers(run):
    advance_until(run, IdeaAgent(run), "generate")
    bad = copy.deepcopy(CANDIDATE)
    bad["gap_closure"][0]["card_ids"] = ["K99-invented"]
    bad["differentiation"][0]["ref"] = "arxiv:9999.99999"
    write_json(run.file("candidate.json"), bad)
    s = next_run(run)
    assert s["step"] == "generate"
    assert any("card_ids" in e for e in s["errors"]) and any("9999.99999" in e for e in s["errors"])


def test_hard_floor_forbids_advance_over_an_upheld_blocking_finding(run):
    agent = IdeaAgent(run, coherence_blocking=[{"finding": "estimator diverges", "evidence": "script", "structural_requirement": "bounded"}])
    advance_until(run, agent, "audit")
    write_json(run.file("audit.json"), audit("advance", blocking_dispositions=[{"index": 0, "disposition": "upheld", "reason": "real"}]))
    s = next_run(run)
    assert s["step"] == "audit" and any("hard floor" in e for e in s["errors"])


def test_advance_with_unmet_required_expectation_is_refused(run):
    advance_until(run, IdeaAgent(run), "audit")
    checks = audit()["checks"] | {"expectations": {"finding": "no DreamerV3", "unmet": ["E01"]}}
    write_json(run.file("audit.json"), audit("advance", checks=checks))
    s = next_run(run)
    assert s["step"] == "audit" and any("unmet required expectations" in e for e in s["errors"])


def test_revision_is_promoted_and_audited_again(run):
    seen, _ = drive(run, IdeaAgent(run, verdicts=("revise", "advance")))
    assert seen[seen.index("audit"):seen.index("card")] == ["audit", "revise", "promote", "audit"]
    assert read_json(run.file("audit_round1.json"))["verdict"] == "revise"
    assert read_json(run.file("idea_card.json"))["falsification"]["negative_control"].startswith("permuted")


def test_revision_may_not_raise_the_users_budget_cap(run):
    agent = IdeaAgent(run, verdicts=("revise",))
    raised = copy.deepcopy(CANDIDATE)
    raised["resources"]["authorized_limit"] = "200 GPU-days"
    raised["falsification"]["negative_control"] = "permuted"
    agent.revise = lambda: (write_json(run.file("revised_candidate.json"), raised),
                            write_json(run.file("revise_notes.json"), notes()))
    s = advance_until(run, agent, "revise", written="revised_candidate.json")
    assert s["step"] == "revise" and any("authorized_limit must be copied verbatim" in e for e in s["errors"])
    assert any("resources.authorized_limit" in e and "without an applied entry" in e for e in s["errors"])


def test_abandon_retries_with_new_lessons_then_fails_without_them(run, frozen):
    seen, last = drive(run, IdeaAgent(run, verdicts=("abandon",)))
    assert seen.count("retry") == 2 and seen[-1] == "failed"
    assert [p.name for p in run.archived()] == ["attempt_1"]
    lessons = read_jsonl(frozen.lessons)
    assert any("[failure_mode] lesson 1" in row["text"] for row in lessons)
    assert "## Attempt 2" in run.file("failed.md").read_text()


def test_repeated_subsumption_rediagnoses_the_bottleneck_once(run):
    agent = IdeaAgent(run)
    agent.audit = lambda: write_json(run.file("audit.json"), audit(
        "abandon", lessons=[{"kind": "subsumption", "text": f"subsumed {len(run.archived())}", "refs": []}],
        checks=audit()["checks"] | {"paper_threat": {"finding": "same", "threat_ref": "arxiv:2501.00001", "kind": "same_mechanism"}}))
    seen, _ = drive(run, agent)
    assert "bottleneck" in seen[seen.index("retry") + 1:]
    assert run.file(".bottleneck_retry_used").exists()
    assert any((a / "phase1.json").exists() for a in run.archived())


def test_card_must_copy_kill_switch_and_cover_required_expectations(run):
    agent = IdeaAgent(run)

    def bad_card():
        c = card(read_json(run.canonical()))
        c["resources"] = {"authorized_limit": "not specified", "estimate": "1 GPU-day"}
        c["expectation_coverage"] = []
        write_json(run.file("idea_card.json"), c)
    agent.card = bad_card
    s = advance_until(run, agent, "card", written="idea_card.json")
    assert s["step"] == "card"
    assert any("idea_card.resources must be copied" in e for e in s["errors"])
    assert any("omits required expectations ['E01']" in e for e in s["errors"])


def test_kill_decision_feeds_a_lesson_back_to_the_domain(run, frozen):
    agent = IdeaAgent(run)
    agent.decision = "kill"
    drive(run, agent)
    assert any(row["text"].startswith("[decision:kill]") for row in read_jsonl(frozen.lessons))


def test_do_not_generate_closes_the_run_with_a_lesson(run, frozen):
    agent = IdeaAgent(run)
    agent.bottleneck = lambda: write_json(run.file("phase1.json"), {"state": "do_not_generate",
                                                                    "do_not_generate_reason": "fewer than 5 relevant readings"})
    seen, last = drive(run, agent)
    assert seen[-2:] == ["close_dng", "do_not_generate"]
    assert any("[do_not_generate]" in row["text"] for row in read_jsonl(frozen.lessons))


def test_second_run_sees_the_first_runs_candidate_for_dedup(run, frozen):
    drive(run, IdeaAgent(run))
    other = runs.RunLayout(frozen.project, "second-run")
    runs.init(other, "world-model-planning", "another question")
    s = advance_until(other, IdeaAgent(other), "generate")
    assert s["step"] == "generate" and str(run.file("candidate.json")) in s["inputs"]


def test_run_cli_status(run):
    drive(run, IdeaAgent(run))
    run_cli("run", "status", "--project", str(run.project), "--run", run.run)
