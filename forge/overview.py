"""One read-only summary of a project's Forge state, for the Mod's pane and status line."""
from __future__ import annotations

from pathlib import Path

from forge import routing
from forge.domain import lessons_since_freeze
from forge.navigator import next_domain
from forge.run_nav import next_run
from forge.runs import RunLayout
from forge.util import Layout, read_json

ATTENTION = {"web_handoff", "human_gate"}


def _brief(step):
    return {"step": step["step"], "type": step["type"], "executor": step.get("executor"),
            "needs_attention": step["type"] in ATTENTION or bool(step.get("confirm"))
            or step["step"] in {"too_broad", "labels", "stuck", "domain_changed", "revision_changed", "budget", "policy"}}


def overview(project, mode=None):
    mode = routing.resolve_mode(mode)
    root = Path(project).expanduser().resolve() / ".forge"
    domains, run_rows = [], []
    for d in sorted((root / "domains").glob("*/")) if (root / "domains").exists() else []:
        try:
            layout = Layout(project, d.name)
        except ValueError:
            continue
        step = routing.route(next_domain(layout), mode, ("domain", project, d.name))
        domains.append({"domain": d.name, "current": layout.current_version(), "versions": layout.versions(),
                        "lessons_since_freeze": len(lessons_since_freeze(layout)), **_brief(step)})
    for r in sorted((root / "runs").glob("*/run.json")) if (root / "runs").exists() else []:
        meta = read_json(r)
        run = RunLayout(project, meta["run"])
        step = routing.route(next_run(run, mode=mode), mode, ("run", project, meta["run"]))
        decision = read_json(run.file("decision.json"))
        card = read_json(run.file("idea_card.json"))
        run_rows.append({"run": meta["run"], "domain": meta["domain"], "version": meta["version"], "run_mode": step["mode"],
                         "question": meta["question"], "attempts": len(run.archived()) + 1,
                         "title": (card or {}).get("title"), "decision": (decision or {}).get("decision"),
                         "card": str(run.file("idea_card.md")) if run.file("idea_card.md").exists() else None, **_brief(step)})
    study_rows = []
    for st in sorted((root / "studies").glob("*/study.json")) if (root / "studies").exists() else []:
        from forge.study import StudyLayout
        from forge.study_nav import next_study
        layout = StudyLayout(project, st.parent.name)
        step = routing.route(next_study(layout), mode, ("study", project, layout.slug))
        kit = layout.kit() or {}
        study_rows.append({"study": layout.slug, "goal": layout.meta()["goal"], "deliverable": kit.get("deliverable"),
                           "actions": len(layout.commits()), "run_mode": step.get("mode"), **_brief(step)})
    attention = [x for x in domains + run_rows + study_rows if x["needs_attention"]]
    return {"project": str(Path(project).expanduser().resolve()), "mode": mode, "exists": root.exists(),
            "studies": study_rows, "domains": domains, "runs": run_rows, "attention": len(attention)}
