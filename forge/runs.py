"""Idea-run lifecycle: init (pin a domain version, mode and budget cap), collision search, revision
promotion, information-gain retry, render, close, finish.

Every command that changes run state first asks the navigator whether that is
the next step, so a host (or a person) cannot finish, promote or retry a run
whose earlier gates have not passed. DONE records the content hashes of what
the decision rests on; if any of them changes, the run is no longer done.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re

from forge.domain import add_lesson, verify_version
from forge.ideas import NO_BUDGET, threat_kind
from forge.util import (SLUG, Layout, move_with_sidecars, now, read_json, read_jsonl, sha256_file, stamp, write_json)
from forge.vendor.corpus import Corpus

ATTEMPT_FILES = ("candidate.json", "refined_candidate.json", "coherence.json", "collision", "audit_round1.json",
                 "audit.json", "revised_candidate.json", "revise_notes.json", "promotion.json", "handoff")
DONE_INPUTS = ("question.txt", "run.json", "phase1.json", "candidate.json", "refined_candidate.json",
               "revised_candidate.json", "revise_notes.json", "coherence.json", "collision/terms.json",
               "collision/papers.jsonl", "audit_round1.json", "audit.json", "idea_card.json", "idea_card.md",
               "decision.json")
MAX_ATTEMPTS = 3
SUBSUMED = {"subsumes", "same_mechanism"}


class RunLayout:
    def __init__(self, project, run):
        if not SLUG.fullmatch(run or ""):
            raise ValueError("Run slug must be lowercase letters, digits and hyphens (max 63)")
        self.project = Path(project).expanduser().resolve()
        self.run = run
        self.dir = self.project / ".forge" / "runs" / run
        self.attempts = self.dir / "attempts"

    def file(self, name):
        return self.dir / name

    def meta(self):
        return read_json(self.file("run.json"))

    def domain(self):
        meta = self.meta()
        return Layout(self.project, meta["domain"]), meta["version"]

    def domain_dir(self):
        layout, version = self.domain()
        return layout.version_dir(version)

    def audit_round(self):
        return 2 if self.file("audit_round1.json").exists() else 1

    def audited(self):
        """The candidate the current round judges and later steps build on: the promoted revision in round 2,
        else the coherence-refined or generated candidate. A round-1 revision not yet promoted is never canonical."""
        if self.audit_round() == 2 and self.file("revised_candidate.json").exists():
            return self.file("revised_candidate.json")
        refined = self.file("refined_candidate.json")
        return refined if refined.exists() else self.file("candidate.json")

    canonical = audited

    def archived(self):
        if not self.attempts.exists():
            return []
        return sorted((p for p in self.attempts.glob("attempt_*") if p.is_dir() and (p / "audit.json").exists()),
                      key=lambda p: int(p.name.split("_")[1]))


def require_step(run: RunLayout, expected, detail=None):
    """Refuse a state change the navigator would not make now."""
    from forge.run_nav import next_run  # the navigator imports this module
    s = next_run(run)
    if s["step"] != expected or (detail and detail not in " ".join(s.get("run", []))):
        raise ValueError(f"refused: the run's next step is {s['step']}, not {expected}"
                         + (f" ({'; '.join(s['errors'][:3])})" if s.get("errors") else ""))
    return s


def init(run: RunLayout, domain, question, mode="auto", budget=None):
    if not question or not question.strip():
        raise ValueError("A non-empty --question is required")
    layout = Layout(run.project, domain)
    version = layout.current_version()
    if version is None:
        raise ValueError(f"Domain {domain} has no frozen version; build it first with `forge next --domain {domain}`")
    if run.file("run.json").exists():
        meta = run.meta()
        if meta["question"] != question.strip() or meta["domain"] != domain:
            raise ValueError("This run already exists with a different question or domain; choose a new run slug")
        return {"created": False, **meta}
    broken = verify_version(layout, version)
    if broken:
        raise ValueError(f"Domain {domain} v{version} does not match its manifest: {broken[:3]}")
    meta = {"run": run.run, "domain": domain, "version": version, "question": question.strip(), "created": now(),
            "manifest_sha256": sha256_file(layout.version_dir(version) / "manifest.json"),
            "mode": mode, "mode_history": [{"mode": mode, "at": now(), "reason": "init"}],
            "budget": (budget or "").strip() or NO_BUDGET}
    write_json(run.file("run.json"), meta)
    run.file("question.txt").write_text(question.strip() + "\n", encoding="utf-8")
    return {**meta, "created": True}


def set_mode(run: RunLayout, mode, reason):
    """Change the run's mode on the record; the navigator never switches it silently."""
    from forge.routing import resolve_mode
    if not reason or not reason.strip():
        raise ValueError("A --reason is required to change a run's mode")
    meta = run.meta()
    mode = resolve_mode(mode)
    meta["mode_history"] = [*meta.get("mode_history", []), {"mode": mode, "at": now(), "reason": reason.strip(),
                                                             "from": meta.get("mode")}]
    meta["mode"] = mode
    write_json(run.file("run.json"), meta)
    return {"run": run.run, "mode": mode}


def integrity_errors(run: RunLayout):
    layout, version = run.domain()
    meta = run.meta()
    manifest = layout.version_dir(version) / "manifest.json"
    if not manifest.exists() or sha256_file(manifest) != meta.get("manifest_sha256"):
        return [f"the pinned domain manifest v{version} changed or is missing"]
    return [f"pinned domain file changed: {f}" for f in verify_version(layout, version)]


def _months_before(day, months):
    y, m = day.year, day.month - months
    while m <= 0:
        y, m = y - 1, m + 12
    return date(y, m, 1)


def _expression(terms):
    phrases = [" ".join(re.sub(r"[\"()]", " ", t).split()) for t in terms]
    return " OR ".join(f'abs:"{p}"' for p in phrases if p)


def collision_terms(run: RunLayout):
    """Candidate terms first, then the domain lexicon's terms for the cards it cites (cap 8 per channel)."""
    candidate = read_json(run.audited())
    lexicon = read_json(run.domain_dir() / "profile" / "lexicon.json") or {}
    cited = [c for g in candidate.get("gap_closure", []) for c in g.get("card_ids", [])]
    channels = {}
    for channel, own, key in (("signature", candidate["signature_terms"], "signature_terms"),
                              ("alias", candidate["alias_terms"], "alias_terms")):
        terms = list(own) + [t for c in cited for t in (lexicon.get("cards", {}).get(c, {}).get(key) or [])]
        seen, out = set(), []
        for t in terms:
            if t.lower() not in seen:
                seen.add(t.lower())
                out.append(t)
        channels[channel] = out[:8]
    windows = lexicon.get("collision_windows") or {"signature_months": 10, "alias_months": 48}
    return {"signature_terms": channels["signature"], "alias_terms": channels["alias"],
            "windows": {k: windows[k] for k in ("signature_months", "alias_months")}}


def promotion_errors(run: RunLayout):
    """In round 2 the audited revision must be byte-for-byte the one that was validated and promoted."""
    record = read_json(run.file("promotion.json")) or {}
    errors = []
    for name, key in (("revised_candidate.json", "revised_sha256"), ("revise_notes.json", "notes_sha256"),
                      ("audit_round1.json", "audit_sha256")):
        if not run.file(name).is_file() or sha256_file(run.file(name)) != record.get(key):
            errors.append(f"{name} changed (or vanished) after it was validated and promoted")
    return errors


def collision_current(run: RunLayout):
    try:
        recorded = read_json(run.file("collision") / "terms.json")
        return bool(recorded) and (run.file("collision") / "papers.jsonl").exists() and \
            {k: recorded.get(k) for k in ("signature_terms", "alias_terms", "windows")} == collision_terms(run)
    except (ValueError, KeyError, TypeError, AttributeError):  # a malformed candidate is reported by its validator
        return False


def collide(run: RunLayout, fetcher=None):
    """Two channels over arXiv, as in ResearchStudio 3.1, anchored on the run's creation date (reproducible)."""
    require_step(run, "collision")
    terms = collision_terms(run)
    anchor = date.fromisoformat(run.meta()["created"][:10])
    rows = {}
    for channel, months in (("signature", terms["windows"]["signature_months"]), ("alias", terms["windows"]["alias_months"])):
        root = run.file("collision") / channel
        config = {"name": f"{run.run}-{channel}", "start_date": _months_before(anchor, months).isoformat(),
                  "end_date": anchor.isoformat(), "page_size": 50,
                  "queries": [{"id": channel, "lane": "in_domain", "domain": "collision",
                               "search_query": _expression(terms[f"{channel}_terms"]), "max_results": 100}]}
        with Corpus(root) as corpus:
            report = corpus.harvest(config, fetcher=fetcher)
            if not report["collection_ok"]:
                raise ValueError(f"collision {channel} channel incomplete: {[t['error'] for t in report['tasks']]}; rerun to resume")
            out = root / "papers.jsonl"
            corpus.export(out)
        for paper in read_jsonl(out):
            row = rows.setdefault(paper["arxiv_id"], {**{k: paper.get(k) for k in ("arxiv_id", "title", "abstract", "published", "abs_url")},
                                                      "channels": []})
            row["channels"].append(channel)
    path = run.file("collision") / "papers.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows.values()), encoding="utf-8")
    write_json(run.file("collision") / "terms.json", terms)
    return {"collision_papers": len(rows), "path": str(path)}


def promote_revision(run: RunLayout):
    """A valid revision is audited again (round 2) against a fresh collision search; revise is not offered twice."""
    if not run.file("revised_candidate.json").exists() or run.audit_round() != 1:
        raise ValueError("promote needs a revised candidate and a round-1 audit")
    require_step(run, "promote")
    write_json(run.file("promotion.json"), {"at": now(), "revised_sha256": sha256_file(run.file("revised_candidate.json")),
                                            "notes_sha256": sha256_file(run.file("revise_notes.json")),
                                            "audit_sha256": sha256_file(run.file("audit.json"))})
    move_with_sidecars(run.file("audit.json"), run.file("audit_round1.json"))
    return {"run": run.run, "audit_round": 2}


def lesson_keys(audit):
    return {(lesson["kind"], " ".join(lesson["text"].lower().split())) for lesson in (audit or {}).get("lessons") or []}


def retry_mode(run: RunLayout):
    """ResearchStudio's information-gain rule over archived audits, with the attempt cap applied to every branch."""
    audit = read_json(run.file("audit.json"))
    archived = [read_json(a / "audit.json") for a in run.archived()]
    attempts_after = len(archived) + 1  # attempts used once this one is archived
    seen = set().union(*(lesson_keys(a) for a in archived)) if archived else set()
    fresh = lesson_keys(audit) - seen
    repeated_subsumption = threat_kind(audit) in SUBSUMED and any(threat_kind(a) in SUBSUMED for a in archived)
    if attempts_after >= MAX_ATTEMPTS:
        return "fail"
    if repeated_subsumption:
        return "fail" if run.file(".bottleneck_retry_used").exists() else "bottleneck"
    if not archived or fresh:
        return "candidate"
    return "fail"


def record_audit_lessons(run: RunLayout, audit, attempt):
    layout, version = run.domain()
    for i, lesson in enumerate((audit or {}).get("lessons") or []):
        add_lesson(layout, f"[{lesson['kind']}] {lesson['text']}", f"run:{run.run}/audit", lesson.get("refs") or [],
                   version=version, key=f"{run.run}:attempt{attempt}:lesson{i}")


def retry(run: RunLayout, mode):
    require_step(run, "retry")
    expected = retry_mode(run)
    if mode != expected:
        raise ValueError(f"retry mode must be {expected} for the current archive")
    audit = read_json(run.file("audit.json"))
    attempt = len(run.archived()) + 1
    record_audit_lessons(run, audit, attempt)  # Idempotent (keyed), so an interrupted retry can rerun.
    if mode == "fail":
        attempts = [*(read_json(a / "audit.json") for a in run.archived()), audit]
        lines = ["# Idea run failed", "", f"Question: {run.meta()['question']}", ""]
        for i, a in enumerate(attempts, 1):
            lines += [f"## Attempt {i}", a.get("verdict_rationale", ""), ""]
        run.file("failed.md").write_text("\n".join(lines), encoding="utf-8")
        return {"mode": mode, "attempts": len(attempts)}
    target = run.attempts / f"attempt_{attempt}"
    target.mkdir(parents=True, exist_ok=True)
    names = [n for n in ATTEMPT_FILES if n != "audit.json"] + (["phase1.json"] if mode == "bottleneck" else [])
    for name in names:
        if run.file(name).exists():
            move_with_sidecars(run.file(name), target / name)
    move_with_sidecars(run.file("audit.json"), target / "audit.json")  # last: marks the attempt complete
    if mode == "bottleneck":
        run.file(".bottleneck_retry_used").write_text(now())
    return {"mode": mode, "archived_to": str(target)}


def render(run: RunLayout):
    require_step(run, "render")
    card = read_json(run.file("idea_card.json"))
    f, res = card["falsification"], card["resources"]
    out = [f"# {card['title']}", "", f"> {card['hook']}", "", "## Abstract", card["abstract_draft"], "",
           "## In plain words", card["plain_summary"], "", "## Motivation",
           f"**Why prior work stopped:** {card['motivation']['why_prior_stopped']}", "",
           f"**Stakes:** {card['motivation']['stakes']}", "", "## Core claim", card["core_claim"], "",
           *[f"- {c}" for c in card["sub_claims"]], "", "## Method", *[f"{i}. {s}" for i, s in enumerate(card["method_flow"], 1)], ""]
    if card.get("key_equations"):
        out += ["## Key equations", *[f"- `{e}`" for e in card["key_equations"]], ""]
    out += ["## Falsification", f"- Experiment: {f['experiment']}", f"- Metric: {f['metric']} ({f['direction']})",
            f"- Load-bearing variable: {f['load_bearing_variable']}", f"- Negative control: {f['negative_control']}", "",
            "## Resources", f"- Authorized by the user: {res['authorized_limit']}", f"- Estimated: {res['estimate']}", "",
            "## Closest prior work",
            f"- {card['almost_prior'].get('ref')}: {card['almost_prior'].get('missed_step')}",
            *[f"- {d.get('ref')}: {d.get('delta')}" for d in card.get("differentiation", [])], "",
            "## Field expectations", *[f"- {e['expectation_id']} — **{e['status']}**: {e['how']}" for e in card["expectation_coverage"]], "",
            "## Reviewer concerns", *[f"- ({c['source']}) {c['concern']} — {c['response']}" for c in card.get("reviewer_concerns", [])], "",
            "## Feasibility", card["feasibility"], "",
            "## Kill switch", f"If {card['kill_switch']['condition']}, then {card['kill_switch']['action']}.", "",
            "## Domain landscape", f"Cards: {', '.join(card['domain_landscape']['cards']) or 'none (new mechanism)'}. "
            f"{card['domain_landscape']['timing']}", ""]
    meta = run.meta()
    out += ["---", f"Run `{meta['run']}` · domain `{meta['domain']}` v{meta['version']} · attempt {len(run.archived()) + 1}"]
    run.file("idea_card.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    stamp(run.file("idea_card.md"), [run.file("idea_card.json")])
    return {"path": str(run.file("idea_card.md"))}


def close(run: RunLayout):
    phase1 = read_json(run.file("phase1.json"))
    if (phase1 or {}).get("state") != "do_not_generate":
        raise ValueError("close is only for a phase1 do_not_generate verdict")
    require_step(run, "close_dng")
    run.file("do_not_generate.md").write_text(
        f"# Not generated\n\nQuestion: {run.meta()['question']}\n\n{phase1['do_not_generate_reason']}\n", encoding="utf-8")
    layout, version = run.domain()
    add_lesson(layout, f"[do_not_generate] {phase1['do_not_generate_reason']}", f"run:{run.run}/phase1", [],
               version=version, key=f"{run.run}:do_not_generate")
    return {"run": run.run, "state": "do_not_generate"}


def _done_hashes(run: RunLayout):
    return {n: sha256_file(run.file(n)) for n in DONE_INPUTS if run.file(n).is_file()}


def done_valid(run: RunLayout):
    """DONE counts only while every file it recorded is unchanged (a hand-written DONE never counts)."""
    try:
        record = json.loads(run.file("DONE").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(record, dict) and bool(record.get("hashes")) and record["hashes"] == _done_hashes(run)


def finish(run: RunLayout):
    if run.file("DONE").exists() and done_valid(run):
        return {"run": run.run, "already_done": True}
    require_step(run, "finish")
    decision = read_json(run.file("decision.json"))
    if decision["decision"] in {"park", "kill"}:
        layout, version = run.domain()
        add_lesson(layout, f"[decision:{decision['decision']}] {decision['rationale']}", f"run:{run.run}/decision", [],
                   version=version, key=f"{run.run}:decision")
    executors = {}
    for row in read_jsonl(run.project / ".forge" / "provenance.jsonl"):
        if row.get("scope") == "run" and row.get("name") == run.run:
            executors[row["step"]] = row.get("requested_executor") or row.get("executor")
    meta = run.meta()
    write_json(run.file("DONE"), {"at": now(), "decision": decision["decision"], "decided_by": decision["decided_by"],
                                  "mode": meta.get("mode"), "budget": meta.get("budget"), "attempt": len(run.archived()) + 1,
                                  "hashes": _done_hashes(run), "executors": executors,
                                  "executor_note": "requested routes as recorded by the host; not authenticated"})
    return {"run": run.run, "decision": decision["decision"]}
