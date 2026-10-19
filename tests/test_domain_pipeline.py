"""Domain layer end to end: navigator routing, validation repair loops, derivations, freeze and revise."""
from __future__ import annotations

import json

from conftest import atom, run_cli, walk
from forge.vendor.corpus import Corpus
from forge import cluster, derive, schemas
from forge.navigator import next_domain
from forge.util import read_json, write_json


def test_empty_project_walks_to_a_frozen_domain_version(layout, agent):
    seen, last = walk(layout, agent)
    assert seen == ["init", "brief", "corpus", "triage", "read", "clusters", "cards", "profile_base",
                    "profile", "stats", "freeze", "domain_ready"]
    manifest = read_json(layout.version_dir(1) / "manifest.json")
    assert manifest["version"] == 1 and manifest["labels"] == "no_outcome_labels"
    assert manifest["counts"]["papers"] == 4 and manifest["counts"]["cards"] == 2
    assert "cards/index.json" in manifest["files"] and not any(f.startswith("corpus/") for f in manifest["files"])
    assert layout.current_version() == 1 and "v1 is frozen" in last["notes"][0]


def test_off_topic_paper_is_never_read(layout, agent):
    walk(layout, agent)
    assert not (layout.readings_dir / "2403.00004.json").exists()
    assert schemas.reading_targets(layout, 25) == ["2410.00003", "2501.00001", "2502.00002"]


def test_invalid_reading_is_sent_back_with_its_errors(layout, agent):
    walk(layout, agent, stop_at="read")
    agent.read(["2501.00001", "2502.00002", "2410.00003"])
    path = layout.readings_dir / "2501.00001.json"
    bad = read_json(path)
    bad["signatures"][0]["sig_id"] = "wrong"
    bad["access"]["source"] = "abstract_only"
    write_json(path, bad)
    s = next_domain(layout)
    assert s["step"] == "read" and s["batch"] == ["2501.00001"]
    assert any("sig_id must look like" in e for e in s["errors"])
    assert any("verified must be 'abstract_only'" in e for e in s["errors"])


def test_card_errors_route_back_to_cards(layout, agent):
    walk(layout, agent, stop_at="cards")
    agent.cards()
    index = read_json(layout.cards_dir / "index.json")
    index["cards"][1]["status"] = "candidate_pattern"  # one paper only
    index["cards"][0]["members"].append("2410.00003#s1")  # also in K02
    write_json(layout.cards_dir / "index.json", index)
    s = next_domain(layout)
    assert s["step"] == "cards"
    assert any("needs members from >= 2 papers" in e for e in s["errors"])
    assert any("already in" in e for e in s["errors"])


def test_profile_rejects_unbacked_maps_and_missing_lexicon(layout, agent):
    walk(layout, agent, stop_at="profile")
    agent.profile()
    cross = read_json(layout.profile_dir / "crossmap.json")
    cross["maps"][0]["source_refs"] = ["9999.99999#s1"]
    write_json(layout.profile_dir / "crossmap.json", cross)
    lex = read_json(layout.profile_dir / "lexicon.json")
    del lex["cards"]["K02-priority-scheduling"]
    write_json(layout.profile_dir / "lexicon.json", lex)
    s = next_domain(layout)
    assert s["step"] == "profile"
    assert any("crossmap[0]" in e for e in s["errors"]) and any("K02-priority-scheduling" in e for e in s["errors"])


def test_zero_papers_sends_the_query_plan_back(layout, agent):
    walk(layout, agent, stop_at="corpus")
    with Corpus(layout.file("corpus")) as c:
        c.harvest(json.loads(layout.file("queries.json").read_text()), fetcher=lambda url: atom([]))
        c.export(layout.file("papers.jsonl"))
    s = next_domain(layout)
    assert s["step"] == "brief" and "zero papers" in s["errors"][0]


def test_too_broad_brief_stops_instead_of_looping(layout, agent):
    walk(layout, agent, stop_at="brief")
    layout.file("brief.md").write_text("# Brief\n## Too broad\nNo object named.\n")
    assert next_domain(layout)["step"] == "too_broad"


def test_revise_from_cards_keeps_readings_and_builds_v2(layout, agent):
    walk(layout, agent)
    run_cli("domain", "lesson", "--project", str(layout.project), "--domain", layout.domain,
            "--text", "uncertainty pruning fails with correlated rollouts", "--source", "run:demo/phase3")
    assert "1 lesson(s) arrived" in next_domain(layout)["notes"][1]
    run_cli("domain", "revise", "--project", str(layout.project), "--domain", layout.domain,
            "--from-stage", "cards", "--reason", "lessons")
    assert (layout.work / "previous" / "cards" / "index.json").exists()
    assert (layout.readings_dir / "2501.00001.json").exists()
    s = next_domain(layout)
    assert s["step"] == "clusters"
    seen, _ = walk(layout, agent)
    assert seen[0] == "clusters" and seen[-1] == "domain_ready"
    assert layout.current_version() == 2
    assert read_json(layout.version_dir(2) / "manifest.json")["revision"]["reason"] == "lessons"
    # A second revision: the cards step must see both the lessons and the previous cards.
    run_cli("domain", "revise", "--project", str(layout.project), "--domain", layout.domain,
            "--from-stage", "cards", "--reason", "again")
    run_cli("derive", "clusters", "--project", str(layout.project), "--domain", layout.domain)
    cards_step_inputs = next_domain(layout)["inputs"]
    assert any(i.endswith("lessons.jsonl") for i in cards_step_inputs)
    assert any(i.endswith("previous/cards") for i in cards_step_inputs)


def test_freeze_refuses_an_incomplete_domain(layout, agent):
    walk(layout, agent, stop_at="triage")
    from forge.cli import main
    assert main(["domain", "freeze", "--project", str(layout.project), "--domain", layout.domain]) == 2


def test_stats_without_labels_report_qualitative_candidates_only(layout, agent):
    walk(layout, agent)
    stats = read_json(layout.version_dir(1) / "antipatterns.json")
    assert stats["status"] == "no_outcome_labels"
    assert stats["qualitative_candidates"][0]["text"] == "sparse rewards"


def test_stats_with_labels_flag_only_combinations_with_enough_evidence(layout, agent):
    walk(layout, agent, stop_at="stats")
    rows = [{"paper_ref": "arxiv:2501.00001", "outcome": "rejected", "source": "fixture", "venue": "X", "year": 2025},
            {"paper_ref": "arxiv:2502.00002", "outcome": "accepted", "source": "fixture", "venue": "X", "year": 2025}]
    layout.file("labels.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    targets = schemas.reading_targets(layout, 25)
    stats = derive.outcome_stats(layout, targets, min_n=1, delta_pp=-10)
    assert stats["status"] == "labeled" and stats["base"]["decided"] == 2
    assert stats["cards"]["K01-rollout-uncertainty-pruning"]["positive_rate"] == 0.5
    strict = derive.outcome_stats(layout, targets)
    assert all(c["flag"] == "insufficient_n" for c in strict["combos"])


def test_bad_labels_stop_the_pipeline(layout, agent):
    walk(layout, agent, stop_at="stats")
    layout.file("labels.jsonl").write_text(json.dumps({"paper_ref": "2501.00001", "outcome": "maybe"}) + "\n")
    s = next_domain(layout)
    assert s["step"] == "labels" and s["type"] == "terminal"


def test_clusters_group_shared_operations_and_flag_near_duplicates():
    sigs = {
        "a#s1": {"arxiv_id": "a", "operation": "prune imagined rollouts by value uncertainty", "information": "value ensemble variance"},
        "b#s1": {"arxiv_id": "b", "operation": "prune imagined rollouts by value uncertainty", "information": "value ensemble variance"},
        "c#s1": {"arxiv_id": "c", "operation": "schedule jobs by priority", "information": "queue length"},
    }
    out = cluster.suggest(sigs)
    groups = {tuple(g["members"]) for g in out["groups"]}
    assert ("a#s1", "b#s1") in groups and ("c#s1",) in groups
    assert out["near_duplicates"] == [{"a": "a#s1", "b": "b#s1", "similarity": 1.0}]
    assert cluster.suggest(sigs) == out  # deterministic


def test_baselines_and_timeline_are_derived_from_readings(layout, agent):
    walk(layout, agent)
    base = read_json(layout.version_dir(1) / "profile" / "baselines.json")
    assert base["baselines"][0] == {"name": "DMC", "kind": "benchmark",
                                    "used_by": ["2410.00003", "2501.00001", "2502.00002"], "count": 3}
    timeline = read_json(layout.version_dir(1) / "profile" / "timeline.json")
    assert timeline["corpus_end"] == "2025-02"
    assert timeline["cards"]["K01-rollout-uncertainty-pruning"]["last_12_months"] == 2


def test_json_step_contract_is_stable(layout):
    s = next_domain(layout, topic="t")
    assert set(s) == {"state", "step", "type", "role", "seat", "prompt", "inputs", "outputs", "deps", "run", "notes",
                      "errors", "batch", "then"}
