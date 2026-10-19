"""One test per finding of the M1+M2 code review, so each stays fixed."""
# ruff: noqa: F811  (pytest fixtures imported from test_idea_run)
from __future__ import annotations

import copy
import io
import json
from email.message import Message
from urllib.error import HTTPError

from conftest import Agent, fake_fetch, run_cli, run_step_command, walk
from forge import runs
from forge.navigator import next_domain
from forge.run_nav import next_run
from forge.util import Layout, read_json, read_jsonl, write_json
from forge.vendor.corpus import Corpus
from test_idea_run import (CANDIDATE, QUESTION, IdeaAgent, act, advance_until, audit, built_domain, frozen,  # noqa: F401
                           notes, run)


class TwoPaperAgent(Agent):
    """With --read-limit 2 only the two in-domain papers are read; cards and maps cite only them."""

    def triage(self):
        super().triage()
        tri = read_json(self.layout.file("triage.json"))
        for row in tri["papers"]:
            if row["arxiv_id"] == "2410.00003":
                row["read_priority"] = 1
        write_json(self.layout.file("triage.json"), tri)

    def cards(self):
        super().cards()
        index = read_json(self.layout.cards_dir / "index.json")
        index["cards"] = index["cards"][:1]
        write_json(self.layout.cards_dir / "index.json", index)

    def profile(self):
        super().profile()
        lex = read_json(self.layout.profile_dir / "lexicon.json")
        lex["cards"].pop("K02-priority-scheduling")
        write_json(self.layout.profile_dir / "lexicon.json", lex)
        write_json(self.layout.profile_dir / "crossmap.json", {"maps": []})


def test_h1_non_default_read_limit_persists_and_freeze_completes(tmp_path):
    layout = Layout(tmp_path / "p", "small-domain")
    run_cli("domain", "init", "--project", str(layout.project), "--domain", layout.domain, "--topic", "t", "--read-limit", "2")
    seen, last = walk(layout, TwoPaperAgent(layout), topic="t")
    assert last["step"] == "domain_ready" and seen.count("freeze") == 1
    frozen_readings = sorted(p.name for p in (layout.version_dir(1) / "readings").glob("*.json"))
    assert frozen_readings == ["2501.00001.json", "2502.00002.json"]  # only validated targets become citable


def test_h2_failed_harvest_is_never_exported(layout, agent):
    walk(layout, agent, stop_at="corpus")

    def flaky(url):
        if "job" in url:
            headers = Message()
            raise HTTPError(url, 503, "busy", headers, io.BytesIO(b""))
        return fake_fetch(url)
    with Corpus(layout.file("corpus")) as c:
        c.harvest(json.loads(layout.file("queries.json").read_text()), fetcher=flaky)
    assert next_domain(layout)["step"] == "corpus"  # resume the harvest, not export
    agent.corpus()
    assert next_domain(layout)["step"] == "triage"


def test_h3_revision_may_not_rebind_cards_or_skip_everything(run):
    agent = IdeaAgent(run, verdicts=("revise",))
    advance_until(run, agent, "revise")
    rebound = copy.deepcopy(read_json(run.file("candidate.json")))
    rebound["gap_closure"][0]["card_ids"] = ["K02-priority-scheduling"]
    rebound["falsification"]["negative_control"] = "changed"
    write_json(run.file("revised_candidate.json"), rebound)
    write_json(run.file("revise_notes.json"), notes("skipped: out of scope", ()))
    s = next_run(run)
    assert s["step"] == "revise"
    assert any("'gap_closure'" in e and "without an applied entry" in e for e in s["errors"])
    assert any("every revision target was skipped" in e for e in s["errors"])
    write_json(run.file("revised_candidate.json"), read_json(run.file("candidate.json")))
    assert any("identical" in e for e in next_run(run)["errors"])


def test_h3_round_two_cannot_revise_again(run):
    agent = IdeaAgent(run, verdicts=("revise", "revise"))
    for _ in range(20):
        s = next_run(run, domain="world-model-planning", question=QUESTION)
        if s["step"] == "audit" and run.audit_round() == 2 and run.file("audit.json").exists():
            break
        act(run, agent, s)
    assert s["step"] == "audit" and any("revise is not allowed again" in e for e in s["errors"])


def test_h4_changed_terms_after_revision_rerun_collision(run):
    agent = IdeaAgent(run, verdicts=("revise", "advance"))
    targets = [{"scope": "falsification", "target": "control", "instruction": "permute", "fields": ["falsification.negative_control"]},
               {"scope": "tactical", "target": "terms", "instruction": "name the queue", "fields": ["signature_terms"]}]
    agent.audit = lambda: write_json(run.file("audit.json"), audit("revise", revision_targets=targets))

    def revise():
        revised = copy.deepcopy(read_json(run.file("candidate.json")))
        revised["falsification"]["negative_control"] = "permuted control"
        revised["signature_terms"] = ["disagreement budgeted planning", "queue of imagined rollouts"]
        write_json(run.file("revised_candidate.json"), revised)
        write_json(run.file("revise_notes.json"), {"applied": [
            {"target_index": 0, "change": "permuted", "fields": ["falsification.negative_control"]},
            {"target_index": 1, "change": "renamed", "fields": ["signature_terms"]}]})
    agent.revise = revise
    s = advance_until(run, agent, "promote")
    run_step_command(s)
    assert next_run(run)["step"] == "collision"


def test_h5_expectation_and_crossmap_refs_are_citable(run):
    advance_until(run, IdeaAgent(run), "generate")
    phase1 = read_json(run.file("phase1.json"))
    phase1["gaps"][0]["refs"] = ["E01", "crossmap[0]"]
    write_json(run.file("phase1.json"), phase1)
    s = next_run(run)
    assert s["step"] == "bottleneck" and not s["errors"]  # valid; a hand edit goes back through its step
    phase1["gaps"][0]["refs"] = ["crossmap[7]"]
    write_json(run.file("phase1.json"), phase1)
    assert any("crossmap[7]" in e for e in next_run(run)["errors"])


def test_h7_bottleneck_rediagnosis_respects_the_attempt_cap(run):
    agent = IdeaAgent(run)
    kinds = iter(["same_mechanism", "partial_overlap", "same_mechanism"])

    def abandon():
        kind = next(kinds)
        write_json(run.file("audit.json"), audit(
            "abandon", lessons=[{"kind": "failure_mode", "text": f"lesson {len(run.archived())}", "refs": []}],
            checks=audit()["checks"] | {"card_failure_modes": {"finding": "x", "triggered": True, "refs": []},
                                        "paper_threat": {"finding": "t", "threat_ref": "arxiv:2501.00001", "kind": kind}}))
    agent.audit = abandon
    from test_idea_run import drive
    seen, last = drive(run, agent)
    assert last["step"] == "failed" and seen.count("generate") == 3 and seen.count("bottleneck") == 1


def test_m8_card_must_copy_title_and_prior_work(run):
    agent = IdeaAgent(run)

    def card():
        from test_idea_run import card as make
        c = make(read_json(run.canonical()))
        c["differentiation"] = [{"ref": "arxiv:1234.56789", "delta": "invented"}]
        write_json(run.file("idea_card.json"), c)
    agent.card = card
    s = advance_until(run, agent, "card", written="idea_card.json")
    assert any("differentiation must be copied" in e for e in s["errors"])


def test_m9_pursue_is_forbidden_when_prior_work_subsumes_the_idea(run):
    agent = IdeaAgent(run)
    agent.audit = lambda: write_json(run.file("audit.json"), audit(
        "advance", checks=audit()["checks"] | {"paper_threat": {"finding": "s", "threat_ref": "arxiv:2501.00001", "kind": "subsumes"}}))
    advance_until(run, agent, "decide")
    agent.decide()
    s = next_run(run)
    assert s["step"] == "decide" and "pursue is forbidden" in s["errors"][0]


def test_m10_malformed_agent_output_becomes_fix_lines(run, layout):
    runs.init(run, "world-model-planning", QUESTION)
    run.file("phase1.json").write_text('{"state": "proceed", "closest_adjacent": ["arxiv:x"]')  # truncated
    s = next_run(run)
    assert s["step"] == "bottleneck" and "invalid JSON" in s["errors"][0]
    write_json(run.file("phase1.json"), {"state": "proceed", "closest_adjacent": ["arxiv:2501.00001"], "gaps": "G1"})
    s = next_run(run)
    assert s["step"] == "bottleneck" and any("closest_adjacent must be a list" in e for e in s["errors"])


def test_m11_tampering_with_the_pinned_version_stops_the_run(run, frozen):
    runs.init(run, "world-model-planning", QUESTION)
    path = frozen.version_dir(1) / "profile" / "expectations.json"
    path.write_text(path.read_text().replace("common_practice", "single_source"))
    s = next_run(run)
    assert s["step"] == "domain_changed" and "expectations.json" in s["errors"][0]


def test_m11_lessons_carry_the_runs_version_and_are_not_duplicated(run, frozen):
    agent = IdeaAgent(run)
    agent.decision = "kill"
    from test_idea_run import drive
    drive(run, agent)
    assert runs.finish(run)["already_done"]  # a rerun of finish must not add the lesson twice
    rows = [r for r in read_jsonl(frozen.lessons) if r["source"].endswith("/decision")]
    assert len(rows) == 1 and rows[0]["domain_version"] == 1


def test_m12_lesson_during_the_build_forces_a_card_update(layout, agent):
    walk(layout, agent, stop_at="profile_base")
    run_cli("domain", "lesson", "--project", str(layout.project), "--domain", layout.domain, "--text", "late", "--source", "user")
    assert next_domain(layout)["step"] == "cards"


def test_m13_revising_from_corpus_refreshes_the_harvest(layout, agent):
    walk(layout, agent)
    run_cli("domain", "revise", "--project", str(layout.project), "--domain", layout.domain, "--from-stage", "corpus", "--reason", "new papers")
    s = next_domain(layout)
    assert s["step"] == "corpus" and s["run"][0].endswith("--refresh")


def test_m14_collision_window_is_anchored_on_the_run(run):
    agent = IdeaAgent(run)
    advance_until(run, agent, "collision")
    urls = []
    from conftest import atom
    runs.collide(run, fetcher=lambda url: urls.append(url) or atom([]))
    created = run.meta()["created"][:10].replace("-", "")
    assert all(f"{created}2359" in u for u in urls)
