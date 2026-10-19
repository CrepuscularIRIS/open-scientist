"""`forge` command line: navigator, domain lifecycle, deterministic derivations, validation, corpus."""
from __future__ import annotations

import argparse
import json
import sys

from forge import cluster, derive, domain, schemas
from forge.navigator import next_domain
from forge import runs
from forge.run_nav import next_run
from forge import handoff, routing
from forge.util import Layout, stamp, write_json


def _layout(args):
    return Layout(args.project, args.domain)


def _ids(parser):
    parser.add_argument("--project", required=True, help="Project directory; state lives in <project>/.forge/")
    parser.add_argument("--domain", required=True, help="Domain slug, e.g. world-model-planning")


def render(step):
    lines = [f"STATE  {step['state']}", f"STEP   {step['step']}  ({step['type']}, role={step['role']}"
             + (f", seat={step['seat']}" if step["seat"] else "") + ")"]
    if step.get("executor"):
        lines.append(f"BY     {step['executor']}  (mode {step.get('mode')})")
    if step.get("confirm"):
        lines.append(f"ASK    {step['confirm']}  (ask the person before running)")
    if step["prompt"]:
        lines.append(f"PROMPT {step['prompt']}")
    for key, label in (("inputs", "INPUT "), ("outputs", "OUTPUT"), ("run", "RUN   "), ("errors", "FIX   "), ("notes", "NOTE  ")):
        lines += [f"{label} {v}" for v in step[key]]
    if step["batch"]:
        lines.append("BATCH  " + " ".join(step["batch"]))
    lines += [f"AFTER  {c}" for c in step.get("run_after", [])]
    lines.append(f"THEN   {step['then']}" if step["type"] != "terminal" else "THEN   (terminal)")
    return "\n".join(lines)


def _run_command(args):
    run = runs.RunLayout(args.project, args.run)
    if args.command == "next":
        mode = routing.resolve_mode(args.mode)
        result = routing.route(next_run(run, domain=args.domain, question=args.question, mode=mode, budget=args.budget),
                               mode, ("run", args.project, args.run))
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
        return 0
    action = {"init": lambda: runs.init(run, args.domain, args.question, routing.resolve_mode(args.mode), args.budget),
              "set-mode": lambda: runs.set_mode(run, args.mode, args.reason),
              "collide": lambda: runs.collide(run), "promote": lambda: runs.promote_revision(run),
              "retry": lambda: runs.retry(run, args.mode), "render": lambda: runs.render(run),
              "close": lambda: runs.close(run), "finish": lambda: runs.finish(run),
              "status": lambda: {"meta": run.meta(), "attempts": len(run.archived()), "next": next_run(run)["step"]}}
    print(json.dumps(action[args.action](), ensure_ascii=False, indent=2))
    return 0


def _handoff_command(args):
    if args.command == "provenance":
        if sum(map(bool, (args.run, args.domain, args.study))) != 1:
            raise ValueError("Give exactly one of --run, --domain or --study")
        scope = ("study", args.project, args.study) if args.study else \
            ("run", args.project, args.run) if args.run else ("domain", args.project, args.domain)
        current = provenance_step(args)
        failed = current["step"] == args.step and bool(current["errors"])
        result = handoff.record_provenance(scope, args.step, args.executor, args.mode, args.output, current["deps"], failed)
    else:
        if bool(args.run) == bool(args.study):
            raise ValueError("Give exactly one of --run or --study")
        scope = ("study", args.project, args.study) if args.study else ("run", args.project, args.run)
        if args.action == "prepare":
            if args.study:
                from forge.study import StudyLayout
                from forge.study_nav import next_study
                step = next_study(StudyLayout(args.project, args.study))
            else:
                step = next_run(runs.RunLayout(args.project, args.run))
            if step["step"] != args.step or step["type"] != "llm":
                raise ValueError(f"The next step is {step['step']}, not {args.step}")
            result = handoff.prepare(scope, step, args.web_action, args.tier, supersede=args.supersede)
        else:
            result = handoff.mark(scope, args.step, args.status, args.url, args.observed_route)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


RECORD_ONLY = {"brief", "read"}  # domain steps whose outputs the navigator re-validates instead of stamping


def provenance_step(args):
    """The navigator's view of the step being recorded. Provenance stamps acceptance, so it is allowed only while the
    navigator is at that step (writing it, repairing it, or accepting it); the deps come from the navigator, never
    from the caller. Brief and reading steps only record provenance (the navigator has moved on by then)."""
    if getattr(args, "study", None):
        from forge.study import StudyLayout
        from forge.study_nav import next_study
        s = next_study(StudyLayout(args.project, args.study))
    elif args.run:
        s = next_run(runs.RunLayout(args.project, args.run))
    else:
        s = next_domain(Layout(args.project, args.domain))
    if args.step == "propose" and getattr(args, "study", None):
        from forge.study import StudyLayout, check_proposal
        layout = StudyLayout(args.project, args.study)
        numbers = layout.proposals()
        return {**s, "deps": [], "errors": check_proposal(layout, numbers[-1])[0] if numbers else []}
    if args.step in RECORD_ONLY and not getattr(args, "study", None):
        return {**s, "deps": [], "errors": []}  # validated on every pass, never accepted against deps
    if args.step in {s["step"], s.get("state")}:
        return s
    raise ValueError(f"refused: the navigator is at {s['step']} ({s.get('state')}), not {args.step}; "
                     "provenance is recorded right after the step it names")


def build_parser():
    parser = argparse.ArgumentParser(prog="forge", description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)

    nxt = subs.add_parser("next", help="Print exactly one next step for a domain (--domain) or an idea run (--run)")
    nxt.add_argument("--project", required=True)
    nxt.add_argument("--domain")
    nxt.add_argument("--run", help="Idea-run slug; with --domain and --question on the first call")
    nxt.add_argument("--study", help="Study slug (the default entry); with --goal on the first call")
    nxt.add_argument("--goal", help="New study only: the user's research question or goal, verbatim")
    nxt.add_argument("--question")
    nxt.add_argument("--topic")
    nxt.add_argument("--read-limit", type=int, help="Papers to read for a new domain (stored at init; default 25)")
    nxt.add_argument("--json", action="store_true")
    nxt.add_argument("--mode", help="auto | web | hitl | web+hitl (default: $FORGE_MODE or auto); a run keeps the mode it started with")
    nxt.add_argument("--budget", help="New run only: the budget cap the user authorizes (default: not specified)")

    dom = subs.add_parser("domain", help="Domain lifecycle")
    dsubs = dom.add_subparsers(dest="action", required=True)
    for name in ("init", "freeze", "revise", "status", "lesson"):
        p = dsubs.add_parser(name)
        _ids(p)
        if name == "init":
            p.add_argument("--topic", required=True)
            p.add_argument("--read-limit", type=int, default=domain.DEFAULT_READ_LIMIT)
        if name == "revise":
            p.add_argument("--from-stage", required=True, choices=list(domain.STAGES))
            p.add_argument("--reason", required=True)
        if name == "lesson":
            p.add_argument("--text", required=True)
            p.add_argument("--source", required=True, help="e.g. run:<slug>/phase3 or user")
            p.add_argument("--ref", action="append", default=[])

    der = subs.add_parser("derive", help="Deterministic assets (no model calls)")
    der.add_argument("what", choices=["clusters", "profile-base", "stats"])
    _ids(der)
    der.add_argument("--min-similarity", type=float, default=0.2)
    der.add_argument("--min-n", type=int, default=30)

    val = subs.add_parser("validate", help="Validate one asset kind")
    val.add_argument("kind", choices=["queries", "triage", "readings", "cards", "profile", "labels", "reviews"])
    _ids(val)

    run = subs.add_parser("run", help="Idea-run lifecycle")
    rsubs = run.add_subparsers(dest="action", required=True)
    for name in ("init", "set-mode", "collide", "promote", "retry", "render", "close", "finish", "status"):
        p = rsubs.add_parser(name)
        p.add_argument("--project", required=True)
        p.add_argument("--run", required=True)
        if name == "init":
            p.add_argument("--domain", required=True)
            p.add_argument("--question", required=True)
            p.add_argument("--mode", help="auto | web | hitl | web+hitl (default: $FORGE_MODE or auto)")
            p.add_argument("--budget", help="The budget cap the user authorizes, verbatim (default: not specified)")
        if name == "set-mode":
            p.add_argument("--mode", required=True)
            p.add_argument("--reason", required=True)
        if name == "retry":
            p.add_argument("--mode", required=True, choices=["candidate", "bottleneck", "fail"])

    ov = subs.add_parser("overview", help="Read-only summary of every domain and run in a project")
    ov.add_argument("--project", required=True)
    ov.add_argument("--mode")

    hand = subs.add_parser("handoff", help="Web handoff packets and receipts")
    hsubs = hand.add_subparsers(dest="action", required=True)
    for name in ("prepare", "mark"):
        p = hsubs.add_parser(name)
        p.add_argument("--project", required=True)
        p.add_argument("--run")
        p.add_argument("--study")
        p.add_argument("--step", required=True)
        if name == "prepare":
            p.add_argument("--action", dest="web_action", required=True, choices=["design", "challenge", "scoop"])
            p.add_argument("--tier", required=True)
            p.add_argument("--supersede", action="store_true", help="Replace a packet whose source files changed (kept as history)")
        else:
            p.add_argument("--status", required=True, choices=sorted(handoff.RECEIPT_STATUS))
            p.add_argument("--url")
            p.add_argument("--observed-route")

    prov = subs.add_parser("provenance", help="Record who produced a step's outputs")
    prov.add_argument("--project", required=True)
    prov.add_argument("--run")
    prov.add_argument("--domain")
    prov.add_argument("--study")
    prov.add_argument("--step", required=True)
    prov.add_argument("--executor", required=True)
    prov.add_argument("--mode", required=True)
    prov.add_argument("--output", action="append", default=[])


    from forge.cli_study import add_parsers
    add_parsers(subs)

    cor = subs.add_parser("corpus", help="Vendored Open Scientist arXiv collector (pass its own arguments)")
    cor.add_argument("rest", nargs=argparse.REMAINDER)
    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["corpus"]:
        from forge.vendor.corpus import main as corpus_main
        return corpus_main(argv[1:])
    args = build_parser().parse_args(argv)
    try:
        if args.command == "overview":
            from forge.overview import overview
            print(json.dumps(overview(args.project, args.mode), ensure_ascii=False, indent=2))
            return 0
        if args.command in {"handoff", "provenance"}:
            return _handoff_command(args)
        if args.command in {"study", "records"}:
            from forge import cli_study
            return cli_study.run_study(args) if args.command == "study" else cli_study.run_records(args)
        if args.command == "next" and args.study:
            from forge.study import StudyLayout
            from forge.study_nav import next_study
            mode = routing.resolve_mode(args.mode)
            raw = next_study(StudyLayout(args.project, args.study), goal=args.goal, mode=mode, budget=args.budget)
            scope = tuple(raw.get("scope") or ("study", args.project, args.study))
            result = routing.route(raw, mode, scope)
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
            return 0
        if args.command == "run" or (args.command == "next" and args.run):
            return _run_command(args)
        layout = _layout(args)
        if args.command == "next":
            mode = routing.resolve_mode(args.mode)
            result = routing.route(next_domain(layout, topic=args.topic, read_limit=args.read_limit), mode,
                                   ("domain", args.project, args.domain))
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
            return 0
        if args.command == "domain":
            if args.action == "init":
                result = domain.init(layout, args.topic, args.read_limit)
            elif args.action == "freeze":
                result = domain.freeze(layout)
            elif args.action == "revise":
                result = domain.revise(layout, args.from_stage, args.reason)
            elif args.action == "lesson":
                result = domain.add_lesson(layout, args.text, args.source, args.ref)
            else:
                result = {"current": layout.current_version(), "versions": layout.versions(),
                          "work": domain.counts(layout),
                          "lessons_since_freeze": len(domain.lessons_since_freeze(layout)),
                          "next": next_domain(layout)["step"]}
        elif args.command == "derive":
            targets = schemas.reading_targets(layout)
            readings = [layout.readings_dir / f"{schemas.safe_id(a)}.json" for a in targets]
            index = layout.cards_dir / "index.json"
            if args.what == "clusters":
                result = cluster.suggest(schemas.signatures(layout, targets), min_similarity=args.min_similarity)
                write_json(layout.file("clusters.suggested.json"), result)
                stamp(layout.file("clusters.suggested.json"), readings)
            elif args.what == "profile-base":
                for name, data in (("baselines.json", derive.baselines(layout, targets)), ("timeline.json", derive.timeline(layout, targets))):
                    write_json(layout.profile_dir / name, data)
                    stamp(layout.profile_dir / name, [layout.cards_dir, layout.file("papers.jsonl"), *readings])
                result = {"written": ["profile/baselines.json", "profile/timeline.json"]}
            else:
                result = derive.outcome_stats(layout, targets, min_n=args.min_n)
                write_json(layout.file("antipatterns.json"), result)
                stamp(layout.file("antipatterns.json"), [index, layout.file("labels.jsonl"), *readings])
            result = {"derived": args.what, **({"groups": len(result["groups"])} if "groups" in result else {}),
                      **({"status": result["status"]} if "status" in result else {})}
        else:
            targets = schemas.reading_targets(layout)
            check = {"queries": lambda: schemas.validate_queries(layout),
                     "triage": lambda: schemas.validate_triage(layout),
                     "readings": lambda: [e for a in targets for e in schemas.validate_reading(layout, a)],
                     "cards": lambda: schemas.validate_cards(layout, targets),
                     "profile": lambda: schemas.validate_profile(
                         layout, [c["card_id"] for c in (schemas.read_json(layout.cards_dir / "index.json") or {"cards": []})["cards"]], targets),
                     "labels": lambda: schemas.validate_labels(layout),
                     "reviews": lambda: schemas.validate_reviews(layout)}[args.kind]
            errors = check()
            result = {"kind": args.kind, "ok": not errors, "errors": errors}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if not errors else 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"forge: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
