"""A scripted host for study tests: it plays the agent (writes proposals and commits) and runs what a host runs."""
from __future__ import annotations

import json
import shlex
from pathlib import Path

from conftest import run_cli
from forge import routing
from forge.study import StudyLayout
from forge.study_nav import next_study
from forge.util import sha256_file, write_json

GOAL = "Why does the agent lose memories across sessions?"

PROBE = '''import json
memories = [f"m{i}" for i in range(40)]
saved = list(memories)                 # the save path keeps everything
WINDOW = 8
retrieved = saved[-WINDOW:]            # retrieval only sees the last WINDOW items
print(json.dumps({"saved": len(saved), "retrieved": len(retrieved), "window": WINDOW}))
'''


def fixture_repo(root: Path):
    repo = root / "agent-repo"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "memory.py").write_text("def save(m, store): store.append(m)\n\ndef retrieve(store, window=8):\n"
                                    "    return store[-window:]\n")
    (repo / "probe.py").write_text(PROBE)
    return repo


class Host:
    def __init__(self, project: Path, slug="memory-loss", mode="auto"):
        self.layout = StudyLayout(project, slug)
        self.mode = mode
        self.scope = ("study", str(self.layout.project), slug)

    def next(self, **kw):
        return next_study(self.layout, **kw)

    def routed(self, s=None):
        s = s or self.next()
        return routing.route(s, self.mode, tuple(s.get("scope") or self.scope))

    def after(self, s):
        for cmd in self.routed(s).get("run_after", []):
            run_cli(*shlex.split(cmd)[2:])

    def bash(self, s):
        for cmd in s["run"]:
            run_cli(*shlex.split(cmd)[2:])

    # ---- the agent's writing
    def rel(self, path):
        return str(Path(path).relative_to(self.layout.project))

    def material(self, rid, path, mtype, access, content, **extra):
        return {"kind": "material", "id": rid, "expected_version": 0, "payload": {
            "source": str(path), "content": content, "type": mtype, "access": access, "path": self.rel(path),
            "sha256": sha256_file(path), **extra}}

    def intake(self, deliverable="diagnosis", task_types=("diagnosis",), assets=()):
        adir = self.layout.action_dir(0, "intake")
        kit = {"task_types": list(task_types), "deliverable": deliverable,
               "variants": {t: f"references/variants/{t}.md" for t in task_types},
               "assets": [{"kind": k, "why": "the first decision needs it"} for k in assets],
               "rationale": "the user reports a failure and asks why"}
        write_json(adir / "kit.json", kit)
        write_json(adir / "commit.json", {"records": [
            {"kind": "project", "id": "q", "expected_version": 0,
             "payload": {"question": GOAL, "constraints": ["no training", "local machine only"],
                         "user_context": "premise under doubt: memories are lost when they are saved"}},
            self.material("kit", adir / "kit.json", "asset", "inspected", "the study's kit v1")]})

    def propose(self, n, action, **fields):
        q = self.layout.store.find("q")
        p = {"action": action, "open_question": fields.pop("open_question", f"what does {action} settle?"),
             "why_now": "it is the cheapest step that can change the next decision",
             "based_on": fields.pop("based_on", [{"id": "q", "version": q["version"]}] if q else []),
             "inputs": fields.pop("inputs", []), "may_change": fields.pop("may_change", []),
             "cost": fields.pop("cost", {"class": "free", "estimate": "seconds, local"}), **fields}
        write_json(self.layout.proposal_path(n), p)
        return p

    def commit(self, n, action, records, files=()):
        adir = self.layout.action_dir(n, action)
        adir.mkdir(parents=True, exist_ok=True)
        for name, text in files:
            (adir / name).write_text(text)
        write_json(adir / "commit.json", {"records": records})

    def drive_to(self, wanted, limit=12):
        """Run bash steps and record provenance until the navigator asks for `wanted` (an llm/gate step)."""
        for _ in range(limit):
            s = self.next()
            if s["step"] == wanted or s["type"] == "terminal":
                return s
            if s["type"] == "bash":
                self.bash(s)
            else:
                raise AssertionError(f"needs the agent: {s['step']} {s.get('errors')}")
        raise AssertionError(f"never reached {wanted}")

    def step_llm(self, s):
        """After the agent wrote the step's outputs: run its run_after, then any bash steps it unlocks."""
        self.after(s)

    def ref(self, rid):
        r = self.layout.store.get(rid)
        return {"id": r["id"], "version": r["version"]}


def show(s):
    return json.dumps({k: s.get(k) for k in ("step", "state", "type", "errors")}, ensure_ascii=False)
