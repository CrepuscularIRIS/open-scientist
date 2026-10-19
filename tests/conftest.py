"""Fixtures that play the agent's part: they write the files each LLM step asks for.

The navigator, validators, collector and derivations are the real code; only the
network (arXiv Atom bytes) and the model's writing are stood in for.
"""
from __future__ import annotations

import json
from pathlib import Path
import shlex
import sys
from xml.sax.saxutils import escape

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge.cli import main as forge  # noqa: E402
from forge.navigator import next_domain  # noqa: E402
from forge.util import Layout, write_json  # noqa: E402
from forge.vendor.corpus import Corpus  # noqa: E402

PAPERS = [
    ("2501.00001", "Pruning imagined rollouts by value uncertainty", "2025-01-10", "planning world model rollout pruning"),
    ("2502.00002", "Uncertainty-aware rollout selection for latent planning", "2025-02-11", "latent planning rollout selection"),
    ("2410.00003", "Priority scheduling of job queues", "2024-10-01", "operations research job queue priority"),
    ("2403.00004", "A survey of everything", "2024-03-03", "survey"),
]


def atom(rows, start=0):
    entries = "".join(f"""<entry><id>http://arxiv.org/abs/{aid}v1</id><title>{escape(t)}</title>
      <summary>{escape(abstract)}</summary><published>{day}T00:00:00Z</published><updated>{day}T00:00:00Z</updated>
      <author><name>A. Author</name></author><category term="cs.LG"/>
      <link href="https://arxiv.org/pdf/{aid}v1" title="pdf" type="application/pdf"/></entry>"""
                      for aid, t, day, abstract in rows)
    return f"""<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
      <opensearch:totalResults>{len(rows)}</opensearch:totalResults><opensearch:startIndex>{start}</opensearch:startIndex>
      {entries}</feed>""".encode()


QUERIES = {"name": "world-model planning", "start_date": "2024-01-01", "end_date": "2025-12-31", "page_size": 25,
           "queries": [{"id": "in-core", "lane": "in_domain", "domain": "model-based RL",
                        "search_query": "abs:\"rollout pruning\"", "max_results": 10},
                       {"id": "x-or", "lane": "cross_domain", "domain": "operations research",
                        "search_query": "abs:\"job queue\"", "max_results": 10}]}


def fake_fetch(url):
    if "job" in url:
        return atom([PAPERS[2]])
    return atom([PAPERS[0], PAPERS[1], PAPERS[3]])


SIGS = {
    "2501.00001": [("prune imagined rollouts by value uncertainty", "value ensemble variance per rollout")],
    "2502.00002": [("select imagined rollouts by value uncertainty", "value ensemble variance over latent rollouts")],
    "2410.00003": [("schedule jobs by priority under capacity", "estimated job priority and queue length")],
}


class Agent:
    """Writes what each LLM step's prompt asks for, minimally but validly."""

    def __init__(self, layout, strength="single_source"):
        self.layout = layout
        self.strength = strength  # expectation strength written by the profile step

    def brief(self):
        self.layout.file("brief.md").write_text("# Brief\n## Topic\n\"world models for planning\"\n")
        write_json(self.layout.file("queries.json"), QUERIES)

    def corpus(self):
        root = self.layout.file("corpus")
        with Corpus(root) as c:
            c.harvest(json.loads(self.layout.file("queries.json").read_text()), fetcher=fake_fetch)
            c.export(self.layout.file("papers.jsonl"))

    def triage(self):
        rows = []
        for aid, *_ in PAPERS:
            off = aid == "2403.00004"
            rows.append({"arxiv_id": aid, "relevance": "off_topic" if off else "core",
                         "lane": "cross_domain" if aid == "2410.00003" else "in_domain",
                         "read_priority": 0 if off else 3, "reason": "fixture"})
        write_json(self.layout.file("triage.json"), {"papers": rows})

    def read(self, batch):
        papers = {json.loads(line)["arxiv_id"]: json.loads(line)
                  for line in self.layout.file("papers.jsonl").read_text().splitlines()}
        for aid in batch:
            sigs = [{"sig_id": f"{aid}#s{i}", "object": "imagined rollouts" if "25" in aid[:2] else "job queue",
                     "information": info, "operation": op, "output": "kept subset", "claimed_effect": "fewer rollouts, same return",
                     "conditions": ["calibrated value estimates"], "evidence": {"kind": "reported_experiment", "locator": "Table 2"},
                     "failure_boundary": "sparse rewards", "verified": "fulltext"}
                    for i, (op, info) in enumerate(SIGS[aid], 1)]
            write_json(self.layout.readings_dir / f"{aid}.json", {
                "arxiv_id": aid, "snapshot_id": papers[aid]["snapshot_id"], "title": papers[aid]["title"],
                "access": {"source": "arxiv_html", "locator": f"https://arxiv.org/html/{aid}v1", "version": "v1",
                           "sections_read": ["3 Method"]},
                "summary": "fixture summary", "signatures": sigs,
                "baselines": [{"name": "DreamerV3", "kind": "method"}, {"name": "DMC", "kind": "benchmark"}],
                "limitations": ["only continuous control"]})

    def cards(self):
        cards = [{"card_id": "K01-rollout-uncertainty-pruning", "title": "Prune rollouts by value uncertainty",
                  "status": "candidate_pattern", "operation": "prune imagined rollouts by value uncertainty",
                  "members": ["2501.00001#s1", "2502.00002#s1"],
                  "success_conditions": [{"text": "calibrated values", "refs": ["2501.00001#s1"]}],
                  "failure_modes": [{"text": "sparse rewards", "refs": ["2502.00002#s1"]}], "counterexamples": [],
                  "transfer_notes": "n/a", "file": "cards/K01-rollout-uncertainty-pruning.md"},
                 {"card_id": "K02-priority-scheduling", "title": "Priority scheduling", "status": "case",
                  "operation": "schedule by priority", "members": ["2410.00003#s1"], "success_conditions": [],
                  "failure_modes": [], "counterexamples": [], "transfer_notes": "jobs map to rollouts",
                  "file": "cards/K02-priority-scheduling.md"}]
        for card in cards:
            path = self.layout.work / card["file"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {card['title']}\n## Operation\n## When it works\n## When it fails\n## Counterexamples\n## Sources\n")
        write_json(self.layout.cards_dir / "index.json", {"cards": cards, "unassigned": [], "merge_notes": "fixture"})

    def profile(self):
        p = self.layout.profile_dir
        read = ["2501.00001", "2502.00002", "2410.00003"] if self.strength != "single_source" else ["2501.00001"]
        write_json(p / "expectations.json", {"expectations": [
            {"id": "E01", "text": "Compare with DreamerV3 on DMC", "kind": "baseline",
             "applies_when": "an empirical planning-method claim on continuous control",
             "evidence": [{"kind": "paper_practice", "ref": aid} for aid in read], "strength": self.strength}]})
        write_json(p / "lexicon.json", {"cards": {
            "K01-rollout-uncertainty-pruning": {"signature_terms": ["value uncertainty rollout pruning"], "alias_terms": ["selective planning"]},
            "K02-priority-scheduling": {"signature_terms": ["priority job scheduling"], "alias_terms": []}},
            "collision_windows": {"signature_months": 10, "alias_months": 48, "basis": "fixture"}})
        write_json(p / "crossmap.json", {"maps": [
            {"source_domain": "operations research", "source_refs": ["2410.00003#s1"],
             "mapping": {"object": "jobs -> rollouts", "operation": "priority -> uncertainty", "condition": "independent rollouts"},
             "breaks_if": "correlated rollouts", "status": "proposed"}]})


def run_cli(*args):
    code = forge(list(args))
    assert code == 0, f"forge {' '.join(args)} exited {code}"


def host_after(s, scope, mode="auto"):
    """What a host does after an LLM step's agent wrote its outputs: run the routed step's run_after (provenance)."""
    from forge import routing
    for cmd in routing.route(s, mode, scope).get("run_after", []):
        run_cli(*shlex.split(cmd)[2:])


def run_step_command(s):
    for cmd in s["run"]:
        run_cli(*shlex.split(cmd)[2:])


def walk(layout, agent, topic="world models for planning", stop_at=None, limit=40):
    """Drive the navigator like a host would; return the step names seen."""
    seen = []
    for _ in range(limit):
        s = next_domain(layout, topic=topic)
        seen.append(s["step"])
        if s["type"] == "terminal" or s["step"] == stop_at:
            return seen, s
        ids = ["--project", str(layout.project), "--domain", layout.domain]
        if s["type"] == "llm":
            (agent.read(s["batch"]) if s["step"] == "read" else getattr(agent, s["step"])())
            host_after(s, ("domain", layout.project, layout.domain))
        elif s["step"] == "accept":
            run_step_command(s)
        elif s["step"] == "init":
            run_cli("domain", "init", *ids, "--topic", topic)
        elif s["step"] in {"corpus", "export"}:
            agent.corpus()
        elif s["step"] == "clusters":
            run_cli("derive", "clusters", *ids)
        elif s["step"] == "profile_base":
            run_cli("derive", "profile-base", *ids)
        elif s["step"] == "stats":
            run_cli("derive", "stats", *ids)
        elif s["step"] == "freeze":
            run_cli("domain", "freeze", *ids)
        else:
            getattr(agent, s["step"])()
    raise AssertionError(f"navigator did not settle: {seen}")


@pytest.fixture
def layout(tmp_path):
    return Layout(tmp_path / "project", "world-model-planning")


@pytest.fixture
def agent(layout):
    return Agent(layout)
