"""Run-state navigator: inspect a project's files and emit exactly ONE next step.

Read-only and idempotent (borrowed from ResearchStudio's `next`): resuming is
calling it again. A step declares a role; the run mode decides who fills it
(forge/routing.py). Deterministic outputs are kept fresh by content
fingerprints. Agent-written outputs are accepted by the provenance command that
follows each LLM step, which stamps them with the content hashes of their
`deps`; when a dep changes the output is stale and its step comes back, and an
output nobody accepted gets an `accept` step. The commands that change run
state re-check the navigator before acting, so the navigator is not the only
gate a host could bypass.
"""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

from forge import schemas
from forge.domain import lessons_since_freeze
from forge.util import BadJSON, acceptance, encoded, fresh, read_json, read_jsonl
from forge.vendor.corpus import Corpus, digest, normalize_config

PLUGIN = Path(__file__).resolve().parents[1]
PROMPTS = PLUGIN / "prompts"
READ_BATCH = 5

SEATS = {"design": "forge-core", "audit": "forge-core", "read": "forge-critic", "review": "forge-critic",
         "fast": "forge-fast", "operator": None, "gate": "forge-core"}


def forge_cmd(*args):
    return " ".join(shlex.quote(a) for a in [sys.executable or "python3", str(PLUGIN / "scripts" / "forge.py"), *args])


def step(name, kind, role, *, prompt=None, inputs=(), outputs=(), run=(), notes=(), errors=(), batch=None, state=None,
         deps=()):
    """`deps` are the files whose content the outputs are built from; acceptance stamps hash them."""
    return {"state": state or name, "step": name, "type": kind, "role": role, "seat": SEATS.get(role),
            "prompt": str(PROMPTS / prompt) if prompt else None,
            "inputs": [str(p) for p in inputs], "outputs": [str(p) for p in outputs], "deps": [str(p) for p in deps],
            "run": list(run), "notes": list(notes), "errors": list(errors)[:40], "batch": batch,
            "then": "Run `forge next` again with the same arguments."}


def review_state(outputs, deps):
    """('ok'|'stale'|'edited'|'unaccepted', changed deps) over the outputs that exist; the worst state wins."""
    states = [acceptance(o, deps) for o in outputs if Path(o).is_file()]
    changed = sorted({c for _, ch in states for c in ch})
    for worst in ("stale", "edited", "unaccepted"):
        if any(state == worst for state, _ in states):
            return worst, changed
    return "ok", []


def accept_step(name, outputs, deps, scope_ids):
    """An output that validates but was never stamped (the host skipped run_after): record it as unknown-origin."""
    return step("accept", "bash", "operator", state=name, outputs=outputs, deps=deps, run=[forge_cmd(
        "provenance", *scope_ids, "--step", name, "--executor", "unknown", "--mode", "unknown",
        *[a for o in outputs if Path(o).is_file() for a in ("--output", str(o))])],
        notes=[f"{name}: the outputs validate but no provenance was recorded after they were written. This records "
               "them with executor 'unknown'. Next time run the step's run_after commands."])


def stale_note(changed, state="stale"):
    if state == "edited":
        return ["This output was edited after it was accepted. Rerun the step (the validators check the new content "
                "and run_after records who wrote it)."]
    return [f"Upstream changed since this output was accepted: {', '.join(Path(c).name for c in changed)}. "
            "Rewrite it against the current inputs."] if changed else []


def checked(fn, *args):
    """Run a validator; malformed JSON becomes a FIX line for the step that wrote it."""
    try:
        return fn(*args)
    except BadJSON as exc:
        return [str(exc)]


def corpus_status(layout):
    """('harvest', refresh) while the current query plan's collection is incomplete; ('export', run_id) once done."""
    config = normalize_config(read_json(layout.file("queries.json")))
    key = digest(encoded(config).encode())
    revision = read_json(layout.file("REVISION.json")) or {}
    with Corpus(layout.file("corpus")) as corpus:
        row = corpus.db.execute("SELECT run_id, created_at FROM runs WHERE config_hash=? ORDER BY created_at DESC LIMIT 1",
                                (key,)).fetchone()
        if row is None:
            return "harvest", False
        if revision.get("refresh_corpus") and row["created_at"] < revision.get("at", ""):
            return "harvest", True
        report = corpus.report(row["run_id"])
    return ("export", row["run_id"]) if report["collection_ok"] else ("harvest", False)


def papers_current(layout, run_id):
    manifest = read_json(layout.file("papers.jsonl.manifest.json")) or {}
    return layout.file("papers.jsonl").exists() and manifest.get("run_id") == run_id


def next_domain(layout, topic=None, read_limit=None):
    w, ids = layout.work, ("--project", str(layout.project), "--domain", layout.domain)
    lessons = [layout.lessons] if layout.lessons.exists() else []
    if not layout.file("topic.txt").exists():
        if layout.current_version() is not None and not topic:
            return terminal_ready(layout)
        if not topic:
            return step("need_topic", "terminal", "gate", notes=["Pass --topic \"<research topic>\" to start this domain."])
        extra = ["--read-limit", str(read_limit)] if read_limit else []
        return step("init", "bash", "operator", run=[forge_cmd("domain", "init", *ids, "--topic", topic, *extra)])
    if layout.file("FROZEN_AS").exists():
        return terminal_ready(layout)
    previous = w / "previous"

    # D1 brief + queries: Companion-style framing turned into a two-lane query plan.
    brief = layout.file("brief.md")
    if brief.exists() and not layout.file("queries.json").exists() and "## Too broad" in brief.read_text(encoding="utf-8"):
        return step("too_broad", "terminal", "gate", inputs=[brief],
                    notes=["The brief says the topic is too broad to name a concrete object or obstacle. Narrow the topic "
                           "(new domain slug) or delete brief.md after editing topic.txt."])
    errors = checked(schemas.validate_queries, layout) if layout.file("queries.json").exists() else []
    if not brief.exists() or not layout.file("queries.json").exists() or errors:
        return step("brief", "llm", "design", prompt="domain/brief.md",
                    inputs=[layout.file("topic.txt"), *lessons, *([previous] if previous.exists() else [])],
                    outputs=[brief, layout.file("queries.json")], errors=errors,
                    notes=["Repair the listed errors in queries.json." if errors else "Write both files."])

    # D2 corpus: harvest until the plan's collection is complete, then export that run.
    state, detail = corpus_status(layout)
    corpus_root = str(layout.file("corpus"))
    if state == "harvest":
        return step("corpus", "bash", "operator", run=[
            forge_cmd("corpus", "--root", corpus_root, "harvest", "--config", str(layout.file("queries.json")),
                      *(["--refresh"] if detail else []))],
            notes=["arXiv allows one request per ~3 s; a large plan takes minutes. Run in the background if needed.",
                   "Exit code 2 means some queries errored or were rate-limited; run this step again later to resume."])
    if not papers_current(layout, detail):
        return step("export", "bash", "operator", run=[
            forge_cmd("corpus", "--root", corpus_root, "export", "--run-id", detail, "--output", str(layout.file("papers.jsonl")))])
    if not read_jsonl(layout.file("papers.jsonl")):
        return step("brief", "llm", "design", prompt="domain/brief.md", inputs=[layout.file("topic.txt"), brief],
                    outputs=[layout.file("queries.json")], errors=["The query plan returned zero papers."],
                    notes=["Rewrite queries.json with broader or differently worded queries; keep both lanes."])

    # D3 triage: relevance, lane and reading priority for every paper.
    errors = checked(schemas.validate_triage, layout) if layout.file("triage.json").exists() else []
    deps = [layout.file("papers.jsonl")]
    state, changed = review_state([layout.file("triage.json")], deps)
    if not layout.file("triage.json").exists() or errors or state in {"stale", "edited"}:
        return step("triage", "llm", "review", prompt="domain/triage.md",
                    inputs=[brief, layout.file("papers.jsonl"),
                            *([previous / "triage.json"] if (previous / "triage.json").exists() else [])],
                    outputs=[layout.file("triage.json")], errors=errors, deps=deps, notes=stale_note(changed, state))
    if state == "unaccepted":
        return accept_step("triage", [layout.file("triage.json")], deps, ids)

    # D4 readings + signatures, in batches; each paper is one file.
    targets = schemas.reading_targets(layout)
    if not targets:
        return step("triage", "llm", "review", prompt="domain/triage.md", inputs=[brief, layout.file("papers.jsonl")],
                    outputs=[layout.file("triage.json")], errors=["No paper has read_priority > 0; nothing would be read."])
    pending = [(aid, checked(schemas.validate_reading, layout, aid)) for aid in targets]
    pending = [(aid, errs) for aid, errs in pending if errs]
    if pending:
        batch = [aid for aid, _ in pending[:READ_BATCH]]
        errs = [e for aid, es in pending[:READ_BATCH] for e in es
                if (layout.readings_dir / f"{schemas.safe_id(aid)}.json").exists()]
        return step("read", "llm", "read", prompt="domain/read.md", inputs=[brief, layout.file("papers.jsonl")],
                    outputs=[layout.readings_dir / f"{schemas.safe_id(a)}.json" for a in batch], errors=errs, batch=batch,
                    notes=[f"{len(targets) - len(pending)}/{len(targets)} target papers read. Each paper may be its own "
                           "isolated sub-agent; write one file per paper."])
    readings = [layout.readings_dir / f"{schemas.safe_id(a)}.json" for a in targets]

    # D5 suggested clusters (deterministic), then D6 cards (merge with judgement; new lessons force an update).
    if not fresh(layout.file("clusters.suggested.json"), readings):
        return step("clusters", "bash", "operator", run=[forge_cmd("derive", "clusters", *ids)])
    index = layout.cards_dir / "index.json"
    errors = checked(schemas.validate_cards, layout, targets) if index.exists() else []
    # Cards cite signatures' conditions and failure boundaries, which clustering ignores: readings are deps too.
    deps = [layout.file("clusters.suggested.json"), layout.lessons, *readings]
    state, changed = review_state([index], deps)
    if not index.exists() or errors or state in {"stale", "edited"}:
        return step("cards", "llm", "design", prompt="domain/cards.md",
                    inputs=[brief, layout.file("clusters.suggested.json"), layout.readings_dir, *lessons,
                            *([previous / "cards"] if (previous / "cards").exists() else [])],
                    outputs=[index, layout.cards_dir], errors=errors, deps=deps, notes=stale_note(changed, state))
    if state == "unaccepted":
        return accept_step("cards", [index], deps, ids)

    # D7 deterministic profile parts, then the judged profile.
    base = [layout.profile_dir / "baselines.json", layout.profile_dir / "timeline.json"]
    base_inputs = [layout.cards_dir, layout.file("papers.jsonl"), *readings]
    if any(not fresh(p, base_inputs) for p in base):
        return step("profile_base", "bash", "operator", run=[forge_cmd("derive", "profile-base", *ids)])
    errors = checked(schemas.validate_labels, layout) + checked(schemas.validate_reviews, layout)
    if errors:  # optional inputs the profile and statistics rest on; a person supplies them, so a person fixes them
        return step("labels", "terminal", "gate", errors=errors,
                    notes=["Fix or remove labels.jsonl (one row per submission event: paper, venue, year, outcome) "
                           "or reviews.jsonl (one row per review: review_id, paper_ref, text, source)."])
    card_ids = [c.get("card_id") for c in (read_json(index) or {"cards": []})["cards"]]
    judged = [layout.profile_dir / n for n in ("expectations.json", "lexicon.json", "crossmap.json")]
    errors = checked(schemas.validate_profile, layout, card_ids, targets) if all(p.exists() for p in judged) else []
    sources = [layout.file("labels.jsonl"), layout.file("reviews.jsonl")]
    deps = [layout.cards_dir, *readings, *base, *sources]  # every input the expectations can rest on
    state, changed = review_state(judged, deps)
    if not all(p.exists() for p in judged) or errors or state in {"stale", "edited"}:
        return step("profile", "llm", "review", prompt="domain/profile.md",
                    inputs=[brief, layout.cards_dir, layout.readings_dir, *base, *[p for p in sources if p.exists()],
                            *([previous / "profile"] if (previous / "profile").exists() else [])],
                    outputs=judged, errors=errors, deps=deps, notes=stale_note(changed, state))
    if state == "unaccepted":
        return accept_step("profile", judged, deps, ids)

    # D8 outcome statistics (labels optional), D9 freeze.
    if not fresh(layout.file("antipatterns.json"), [index, layout.file("labels.jsonl"), *readings]):
        return step("stats", "bash", "operator", run=[forge_cmd("derive", "stats", *ids)])
    return step("freeze", "bash", "operator", run=[forge_cmd("domain", "freeze", *ids)])


def terminal_ready(layout):
    version = layout.current_version()
    pending = lessons_since_freeze(layout)
    notes = [f"Domain {layout.domain} v{version} is frozen at {layout.version_dir(version)}."]
    if pending:
        notes.append(f"{len(pending)} lesson(s) arrived after v{version}; fold them in with "
                     f"`forge domain revise --from-stage cards --reason \"lessons\"`.")
    return step("domain_ready", "terminal", "operator", notes=notes, outputs=[layout.version_dir(version)])
