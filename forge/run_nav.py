"""Idea-run navigator: ResearchStudio phases 1-4 against a frozen domain version, one step at a time.

Round 1 audit may advance, revise or abandon. A valid revision is promoted and
audited again (round 2) against a fresh collision search, where revise is no
longer offered: every revised candidate passes the same hard floor as the first.

Each agent-written output is accepted against the content of its `deps`
(see forge/navigator.py). Changing an upstream file, for example rewriting the
bottleneck under the same gap ids, makes everything built on it stale. The
run's mode is the one stored in run.json. A step whose output keeps failing
validation stops the run for a person after MAX_STEP_RUNS attempts in one
attempt and round.
"""
from __future__ import annotations

from forge import ideas, review_gates
from forge.handoff import step_runs
from forge.navigator import accept_step, forge_cmd, review_state, stale_note, step
from forge.routing import resolve_mode
from forge.runs import RunLayout, collision_current, done_valid, integrity_errors, promotion_errors, retry_mode
from forge.util import BadJSON, fresh, read_json

MAX_STEP_RUNS = 5


def _siblings(run):
    meta = run.meta()
    found = []
    for other in sorted(run.dir.parent.glob("*/run.json")):
        try:
            o = read_json(other)
        except BadJSON:
            continue
        cand = other.parent / "candidate.json"
        if o and o.get("run") != run.run and o.get("domain") == meta["domain"] and cand.exists():
            found.append((cand.stat().st_mtime, cand))
    return [p for _, p in sorted(found, reverse=True)[:5]]


def _load(path):
    """(data, errors): malformed JSON becomes a FIX line instead of a crash."""
    try:
        return read_json(path), []
    except BadJSON as exc:
        return None, [str(exc)]


def checked_list(fn, *args):
    try:
        return fn(*args)
    except BadJSON as exc:
        return [str(exc)]


def _retry(run, ids, note):
    mode = retry_mode(run)
    return step("retry", "bash", "operator", run=[forge_cmd("run", "retry", *ids, "--mode", mode)],
                notes=[note, {"candidate": "New lessons: archive this attempt and regenerate with them as constraints.",
                              "bottleneck": "Repeated subsumption: archive and re-diagnose the bottleneck once.",
                              "fail": "No new information or attempt cap reached: write failed.md."}[mode],
                       "Audit lessons are appended to the domain's lessons.jsonl."])


class Flow:
    """One navigator pass over a run: each `llm` call returns a step, or None when that output is accepted."""

    def __init__(self, run: RunLayout):
        self.run = run
        self.ids = ("--project", str(run.project), "--run", run.run)
        self.scope = ("run", run.project, run.run)

    def llm(self, name, role, prompt, outputs, deps, errors, inputs, notes=()):
        primary = outputs[0]
        state, changed = review_state(outputs, deps)
        if not primary.exists() or errors or state in {"stale", "edited"}:
            if errors and step_runs(self.scope, name) >= MAX_STEP_RUNS:
                return step("stuck", "terminal", "gate", state=name, outputs=outputs, errors=errors, notes=[
                    f"{name} was filled {MAX_STEP_RUNS} times in this attempt and its output still fails validation. "
                    "A person should look: fix the file by hand, change the mode, or start a new run."])
            return step(name, "llm", role, prompt=prompt, inputs=inputs, outputs=outputs, deps=deps, errors=errors,
                        notes=[*notes, *stale_note(changed, state)])
        if state == "unaccepted":
            return accept_step(name, outputs, deps, self.ids)
        return None


def next_run(run: RunLayout, domain=None, question=None, mode=None, budget=None):
    ids = ("--project", str(run.project), "--run", run.run)
    if not run.file("run.json").exists():
        if not (domain and question):
            return step("need_question", "terminal", "gate",
                        notes=["Pass --domain <frozen domain slug> and --question \"<research question>\" to start this run."])
        return step("run_init", "bash", "operator", run=[forge_cmd(
            "run", "init", *ids, "--domain", domain, "--question", question, "--mode", resolve_mode(mode),
            *(["--budget", budget] if budget else []))])
    policy = run.meta().get("mode") or resolve_mode(mode)
    result = _next(run, ids, policy)
    if mode and mode != policy:
        result["notes"] = [f"This run's mode is {policy} (stored in run.json); `forge run set-mode` changes it.", *result["notes"]]
    return {**result, "mode": policy}


def _next(run, ids, policy):
    broken = integrity_errors(run)
    if broken:
        return step("domain_changed", "terminal", "gate", errors=broken,
                    notes=["The frozen domain version this run is pinned to was modified. Restore it, or start a new run on the current version."])
    if run.file("DONE").exists() and done_valid(run):
        return step("done", "terminal", "operator", outputs=[run.file("idea_card.md"), run.file("decision.json")],
                    notes=[f"Run {run.run} ended: done."])
    for name, label in (("failed.md", "failed"), ("do_not_generate.md", "do_not_generate")):
        if run.file(name).exists():
            return step(label, "terminal", "operator", outputs=[run.file(name)], notes=[f"Run {run.run} ended: {label}."])

    f = Flow(run)
    D = run.domain_dir()
    layout, _ = run.domain()
    lessons = [layout.lessons] if layout.lessons.exists() else []
    attempts = [run.attempts] if run.attempts.exists() else []
    cards = [D / "cards"]
    refs = ideas.Refs(D, run.file("collision") / "papers.jsonl", budget=run.meta().get("budget") or ideas.NO_BUDGET)
    question, P1 = run.file("question.txt"), run.file("phase1.json")

    # Phase 1 — bottleneck.
    phase1, errors = _load(P1)
    errors = errors or (ideas.validate_phase1(phase1, refs) if phase1 is not None else [])
    s = f.llm("bottleneck", "design", "idea/bottleneck.md", [P1], [question], errors,
              inputs=[question, run.file("run.json"), D / "brief.md", *cards, D / "readings", D / "papers.jsonl",
                      D / "profile" / "timeline.json", D / "profile" / "expectations.json", *lessons, *attempts])
    if s:
        return s
    if phase1["state"] == "do_not_generate":
        return step("close_dng", "bash", "operator", run=[forge_cmd("run", "close", *ids)])

    # Phase 2 — select + generate (citation gate = validation), then the coherence gate.
    C = run.file("candidate.json")
    candidate, errors = _load(C)
    errors = errors or (ideas.validate_candidate(candidate, refs, phase1) if candidate is not None else [])
    s = f.llm("generate", "design", "idea/generate.md", [C], [P1], errors,
              inputs=[question, run.file("run.json"), P1, *cards, D / "profile" / "crossmap.json",
                      D / "profile" / "expectations.json", D / "antipatterns.json", D / "papers.jsonl", D / "readings",
                      *lessons, *_siblings(run), *attempts],
              notes=["Citation gate: every card, gap, paper, signature, expectation and crossmap entry cited must "
                     "exist in the pinned domain; a grounded premise must rest on material read in full."])
    if s:
        return s
    CO, R = run.file("coherence.json"), run.file("refined_candidate.json")
    coherence, errors = _load(CO)
    if not errors and coherence is not None:
        errors = checked_list(ideas.validate_coherence, coherence, run.dir, refs, phase1, candidate)
    s = f.llm("coherence", "review", "idea/coherence.md", [CO, R], [C, P1], errors,
              inputs=[C, P1, *cards, D / "profile" / "expectations.json"],
              notes=["Fresh context: never the agent that generated the candidate. "
                     "Write refined_candidate.json only when verdict is patched."])
    if s:
        return s

    # Phase 3 — collision on the current candidate, audit (round 1 or 2), revise / retry.
    if run.audit_round() == 2:
        changed = promotion_errors(run) or review_gates.validate_revision(
            read_json(run.file("revised_candidate.json")), read_json(run.file("revise_notes.json")),
            read_json(R if R.exists() else C), read_json(run.file("audit_round1.json")), refs, phase1)
        if changed:
            return step("revision_changed", "terminal", "gate", state="audit", errors=changed, notes=[
                "The promoted revision no longer matches what was validated. Restore revised_candidate.json and "
                "revise_notes.json from promotion.json's hashes, or start a new run."])
    if not collision_current(run):
        return step("collision", "bash", "operator", run=[forge_cmd("run", "collide", *ids)],
                    notes=["Two arXiv channels (own + lexicon terms, recent window; aliases, long window); a few requests at ~3 s each."])
    current, round_, audited = run.canonical(), run.audit_round(), run.audited()
    base = R if R.exists() else C
    A, PAPERS = run.file("audit.json"), run.file("collision") / "papers.jsonl"
    round2 = [run.file("audit_round1.json"), run.file("revise_notes.json")] if round_ == 2 else []
    audit, errors = _load(A)
    if not errors and audit is not None:
        errors = review_gates.validate_audit(audit, refs, coherence, round_)
    s = f.llm("audit", "audit", "idea/audit.md", [A], [audited, P1, CO, PAPERS, *round2], errors,
              inputs=[audited, P1, CO, PAPERS, D / "papers.jsonl", D / "readings", *cards, D / "antipatterns.json",
                      D / "profile" / "expectations.json", D / "profile" / "timeline.json", *lessons, *round2],
              notes=["Round 2: this audits the revised candidate; revise is not available, advance or abandon."] if round_ == 2 else [])
    if s:
        return s
    if audit["verdict"] == "abandon":
        return _retry(run, ids, f"Round-{round_} audit abandoned the candidate.")
    if audit["verdict"] == "revise":
        RV, RN = run.file("revised_candidate.json"), run.file("revise_notes.json")
        revised, errors = _load(RV)
        notes, more = _load(RN)
        errors = errors + more
        if not errors and revised is not None:
            errors = review_gates.validate_revision(revised, notes, read_json(base), audit, refs, phase1)
        s = f.llm("revise", "design", "idea/revise.md", [RV, RN], [base, A, P1], errors,
                  inputs=[base, A, P1, *cards])
        if s:
            return s
        return step("promote", "bash", "operator", run=[forge_cmd("run", "promote", *ids)],
                    notes=["The revision is valid; it will be searched for collisions and audited again (round 2)."])

    # Phase 4 — idea card, render, decision gate, finish.
    IC, RN = run.file("idea_card.json"), run.file("revise_notes.json")
    card, errors = _load(IC)
    if not errors and card is not None:
        errors = review_gates.validate_card(card, read_json(current), refs)
    s = f.llm("card", "review", "idea/card.md", [IC], [current, A, P1, CO, RN], errors,
              inputs=[current, P1, A, CO, *([RN] if RN.exists() else []), *cards, D / "profile" / "expectations.json",
                      D / "profile" / "timeline.json", D / "profile" / "baselines.json", PAPERS])
    if s:
        return s
    if not fresh(run.file("idea_card.md"), [IC]):
        return step("render", "bash", "operator", run=[forge_cmd("run", "render", *ids)])
    DE = run.file("decision.json")
    decision, errors = _load(DE)
    if not errors and decision is not None:
        errors = review_gates.validate_decision(decision, audit)
    if decision is not None and not errors and "hitl" in policy and decision["decided_by"] != "human":
        errors = ["hitl mode: the decision must come from the human (decided_by \"human\")"]
    s = f.llm("decide", "gate", "idea/decide.md", [DE], [IC, A], errors,
              inputs=[run.file("idea_card.md"), IC, A, run.file("run.json")])
    if s:
        return s
    return step("finish", "bash", "operator", run=[forge_cmd("run", "finish", *ids)],
                notes=([f"{run.run}: DONE no longer matches the files it recorded; finishing again."]
                       if run.file("DONE").exists() else []))
