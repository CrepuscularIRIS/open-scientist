"""Open Scientist MCP server over stdio, standard library only (JSON-RPC 2.0, one message per line).

Tools:
- `forge_next`: the next step of a study, domain or idea run, routed for the run's mode.
- `records_context`, `records_get`, `records_list`, `records_history`: read-only access to the record store.
- `papers_search`: the local paper index first, then arXiv.

There is no write tool. Records change only through a study's commit step, which validates the action's contract
and the protocols first. Retrieved text is data, never instructions.
"""
from __future__ import annotations

import json
import sys
import traceback

PROTOCOL = "2025-06-18"
INSTRUCTIONS = ("Open Scientist drives research one checked step at a time: call forge_next with the study slug, do "
                "exactly that step, then call it again. Records are read here and written only through a study's commit "
                "step. papers_search results are discovery leads: an empty result is not novelty, and a hit supports "
                "nothing until its text is read.")


def _obj(props, required=()):
    return {"type": "object", "properties": props, "required": list(required), "additionalProperties": False}


PROJECT = {"type": "string", "description": "Absolute path of the research project (state lives in <project>/.forge/)"}
STUDY = {"type": "string", "description": "The study slug (each study has its own record store)"}
TOOLS = [
    {"name": "forge_next", "description": "The next step for a study (default), a domain build or an idea run. "
     "Pass goal on a study's first call. Do the step, then call again.",
     "inputSchema": _obj({"project": PROJECT, "study": {"type": "string"}, "domain": {"type": "string"},
                          "run": {"type": "string"}, "goal": {"type": "string"}, "topic": {"type": "string"},
                          "question": {"type": "string"}, "mode": {"type": "string", "enum": ["auto", "web", "hitl", "web+hitl"]},
                          "budget": {"type": "string"}}, ["project"]),
     "annotations": {"readOnlyHint": True}},
    {"name": "records_context", "description": "A study's latest records with stale inputs, earlier contrary findings and open feedback.",
     "inputSchema": _obj({"project": PROJECT, "study": STUDY}, ["project", "study"]), "annotations": {"readOnlyHint": True}},
    {"name": "records_get", "description": "One record of a study (latest, or an exact version).",
     "inputSchema": _obj({"project": PROJECT, "study": STUDY, "id": {"type": "string"}, "version": {"type": "integer", "minimum": 1}},
                         ["project", "study", "id"]), "annotations": {"readOnlyHint": True}},
    {"name": "records_list", "description": "Latest version of every record of a study, optionally of one kind.",
     "inputSchema": _obj({"project": PROJECT, "study": STUDY,
                          "kind": {"type": "string", "enum": ["project", "candidate", "material", "activity", "assessment"]}},
                         ["project", "study"]), "annotations": {"readOnlyHint": True}},
    {"name": "records_history", "description": "Every version of one record of a study, oldest first.",
     "inputSchema": _obj({"project": PROJECT, "study": STUDY, "id": {"type": "string"}}, ["project", "study", "id"]),
     "annotations": {"readOnlyHint": True}},
    {"name": "papers_search", "description": "Search the local paper index (PAPER_SEARCH_LOCAL_DB) and/or arXiv. Per-source "
     "status separates empty, missing_index, timeout and errors. Local hits carry pdf_path.",
     "inputSchema": _obj({"queries": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 8},
                          "sources": {"type": "array", "items": {"type": "string", "enum": ["local", "arxiv"]}},
                          "max_papers": {"type": "integer", "minimum": 1, "maximum": 100},
                          "start_year": {"type": "integer"}, "end_year": {"type": "integer"},
                          "budget_seconds": {"type": "number", "exclusiveMinimum": 0, "maximum": 300}}, ["queries"]),
     "annotations": {"readOnlyHint": True, "openWorldHint": True}},
]


def _next(a):
    from forge import routing
    project = a["project"]
    mode = routing.resolve_mode(a.get("mode"))
    if a.get("run"):
        from forge.run_nav import next_run
        from forge.runs import RunLayout
        raw = next_run(RunLayout(project, a["run"]), domain=a.get("domain"), question=a.get("question"), mode=mode,
                       budget=a.get("budget"))
        scope = ("run", project, a["run"])
    elif a.get("domain") and not a.get("study"):
        from forge.navigator import next_domain
        from forge.util import Layout
        raw = next_domain(Layout(project, a["domain"]), topic=a.get("topic"))
        scope = ("domain", project, a["domain"])
    else:
        from forge.study import StudyLayout
        from forge.study_nav import next_study
        if not a.get("study"):
            raise ValueError("pass study (a short slug for this research question), domain or run")
        raw = next_study(StudyLayout(project, a["study"]), goal=a.get("goal"), mode=mode, budget=a.get("budget"))
        scope = tuple(raw.get("scope") or ("study", project, a["study"]))
    return routing.route(raw, mode, scope)


def call(name, a):
    if name == "forge_next":
        return _next(a)
    if name.startswith("records_"):
        from forge.study import StudyLayout
        store = StudyLayout(a["project"], a["study"]).store
        return {"records_context": lambda: store.context(), "records_get": lambda: store.get(a["id"], a.get("version")),
                "records_list": lambda: store.list(a.get("kind")), "records_history": lambda: store.history(a["id"])}[name]()
    if name == "papers_search":
        from forge.search import search
        budget = float(a.get("budget_seconds", 25))
        return search(a["queries"], sources=tuple(a.get("sources") or ("local", "arxiv")), max_papers=a.get("max_papers", 20),
                      start_year=a.get("start_year"), end_year=a.get("end_year"), timeout=min(10, budget), budget_seconds=budget)
    raise KeyError(name)


def handle(msg):
    """One JSON-RPC message in, one response (or None for a notification) out."""
    method, mid = msg.get("method"), msg.get("id")
    if mid is None:
        return None
    if method == "initialize":
        version = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": version, "capabilities": {"tools": {}},
                                                        "serverInfo": {"name": "open-scientist", "version": _version()},
                                                        "instructions": INSTRUCTIONS}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        if name not in {t["name"] for t in TOOLS}:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {name}"}}
        try:
            result = call(name, params.get("arguments") or {})
            text, error = json.dumps(result, ensure_ascii=False, indent=2, default=str), False
        except (ValueError, KeyError, OSError) as exc:
            text, error = f"{type(exc).__name__}: {exc}", True
        return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": error}}
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}


def _version():
    try:
        from pathlib import Path
        return json.loads((Path(__file__).resolve().parents[1] / ".claude-plugin" / "plugin.json").read_text())["version"]
    except (OSError, ValueError, KeyError):
        return "unknown"


def main(stdin=None, stdout=None):
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            reply = handle(msg) if isinstance(msg, dict) else {"jsonrpc": "2.0", "id": None,
                                                               "error": {"code": -32600, "message": "invalid request"}}
        except json.JSONDecodeError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        except Exception:  # noqa: BLE001 - a server must answer, never die on one request
            reply = {"jsonrpc": "2.0", "id": msg.get("id") if isinstance(msg, dict) else None,
                     "error": {"code": -32603, "message": traceback.format_exc(limit=2)}}
        if reply is not None:
            stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            stdout.flush()


if __name__ == "__main__":
    main()
