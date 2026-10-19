"""`forge study ...` and `forge records ...`: the study loop's commands and read access to the record store."""
from __future__ import annotations

import json

from forge import execute, routing, study
from forge.records import Store
from forge.study_nav import next_study
from forge.util import read_json


def add_parsers(subs):
    st = subs.add_parser("study", help="Question-driven study: init, commit, exec, wait, collide, absorb, answer, status")
    ssubs = st.add_subparsers(dest="action", required=True)
    for name in ("init", "commit", "exec", "wait", "collide", "absorb", "answer", "policy", "status"):
        p = ssubs.add_parser(name)
        p.add_argument("--project", required=True)
        p.add_argument("--study", required=True)
        if name == "init":
            p.add_argument("--goal", required=True, help="The user's research question or goal, verbatim")
            p.add_argument("--mode", default=None, help="auto | web | hitl | web+hitl (default: $FORGE_MODE or auto)")
            p.add_argument("--budget", help="The budget cap the user authorizes, verbatim")
            p.add_argument("--wall-clock-min", type=float, default=30)
            p.add_argument("--max-actions", type=int, default=40)
        if name in {"commit", "exec", "wait", "collide", "absorb", "answer"}:
            p.add_argument("--proposal", type=int, required=True)
        if name == "policy":
            p.add_argument("--json", required=True, help="The full new policy object, as the person set it")
            p.add_argument("--text", required=True, help="The person's words")
        if name == "answer":
            p.add_argument("--text", required=True, help="The person's words")
            group = p.add_mutually_exclusive_group()
            group.add_argument("--approve", action="store_true")
            group.add_argument("--deny", action="store_true")
    rec = subs.add_parser("records", help="Read the record store (writes happen only through study commits)")
    rsubs = rec.add_subparsers(dest="action", required=True)
    for name in ("context", "get", "list", "history", "import"):
        p = rsubs.add_parser(name)
        p.add_argument("--project", required=True)
        if name != "import":
            where = p.add_mutually_exclusive_group(required=True)
            where.add_argument("--study", help="The study whose record store to read")
            where.add_argument("--archive", action="store_true", help="The read-only archive imported from 0.2")
        if name in {"get", "history"}:
            p.add_argument("--id", required=True)
        if name == "get":
            p.add_argument("--version", type=int)
        if name == "list":
            p.add_argument("--kind")
        if name == "import":
            p.add_argument("--from", dest="source", required=True, help="An Open Scientist 0.2 .open-scientist/records.sqlite3")


def _at(layout, args, steps, state=None):
    """Refuse unless the navigator's current step is one of `steps` for exactly this proposal."""
    s = next_study(layout)
    if s["step"] not in steps or s.get("proposal", 0 if s.get("state") == "intake" else None) != args.proposal \
            or (state and s.get("state") != state):
        raise ValueError(f"refused: the study is at {s['step']} ({s.get('state')}) of proposal {s.get('proposal')}, not "
                         f"{'/'.join(sorted(steps))} of proposal {args.proposal}"
                         + (f": {'; '.join(s['errors'][:3])}" if s.get("errors") else ""))
    return s


def run_study(args):
    layout = study.StudyLayout(args.project, args.study)
    a = args.action
    if a == "init":
        result = study.init(layout, args.goal, routing.resolve_mode(args.mode), args.budget, args.wall_clock_min, args.max_actions)
    elif a == "commit":
        proposal = {"action": "intake", "may_change": ["Q", "assets"]} if args.proposal == 0 else read_json(layout.proposal_path(args.proposal))
        action = proposal.get("action")
        if action not in study.AGENT_COMMITS:
            raise ValueError(f"{action} is committed by its own command (exec, collide, absorb, answer), not by commit")
        _at(layout, args, {"commit"}, state=action)
        result = study.apply_commit(layout, args.proposal, action, proposal)
    elif a in {"exec", "collide", "absorb"}:
        _at(layout, args, {"exec": {"run_test"}, "collide": {"collision"}, "absorb": {"absorb"}}[a])
        result = {"exec": execute.exec_activity, "collide": execute.collide, "absorb": execute.absorb}[a](layout, args.proposal)
    elif a == "wait":
        _at(layout, args, {"wait", "run_test"})
        result = execute.wait(layout, args.proposal)
    elif a == "policy":
        result = study.set_policy(layout, json.loads(args.json), args.text)
    elif a == "answer":
        s = _at(layout, args, {"authorize", "ask_human"})
        approve = True if args.approve else False if args.deny else None
        if (s["step"] == "authorize") != (approve is not None):
            raise ValueError("an authorization needs --approve or --deny; an ask_human answer takes neither")
        result = execute.answer(layout, args.proposal, args.text, approve)
    else:
        result = {"study": layout.meta(), "commits": [(n, act, m.get("productive")) for n, act, m in layout.commits()],
                  "next": next_study(layout)["step"]}
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


ARCHIVE = ".forge/archive/open-scientist-0.2.sqlite3"


def run_records(args):
    from pathlib import Path
    a = args.action
    if a == "import":
        print(json.dumps(import_v02(Path(args.project).expanduser().resolve(), args.source), ensure_ascii=False, indent=2))
        return 0
    root = Path(args.project).expanduser().resolve()
    store = Store(root, path=root / ARCHIVE) if args.archive else study.StudyLayout(root, args.study).store
    if a == "context":
        result = store.context()
    elif a == "get":
        result = store.get(args.id, args.version)
    elif a == "list":
        result = store.list(args.kind)
    else:
        result = store.history(args.id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def import_v02(project, source):
    """Copy an Open Scientist 0.2 record store's history, unchanged, into the project's read-only archive.

    The archive is history to read (`forge records context --archive`), never a study's evidence: no completion
    rule or citation resolves against it, so an imported record cannot satisfy a gate. Read-only on the source.
    """
    from pathlib import Path
    store = Store(project, path=Path(project) / ARCHIVE)
    if store.path.exists():
        raise ValueError(f"{store.path} already exists; the archive is written once")
    rows = sorted(Store(project, path=source).all(), key=lambda r: (r["created_at"], r["id"], r["version"]))  # write order
    skipped = [r["id"] for r in rows if r["kind"] not in {"project", "candidate", "material", "activity", "assessment"}]
    items = [{"kind": r["kind"], "id": r["id"], "payload": r["payload"], "expected_version": r["version"] - 1}
             for r in rows if r["id"] not in skipped]
    imported = store.put_many(items)
    return {"imported": len(imported), "skipped_workflow_records": sorted(set(skipped)), "source": str(source)}
