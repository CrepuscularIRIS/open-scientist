"""Run modes: decide who fills each step's role, without changing what the step produces.

auto      models fill every role (seat agents).
web       high-leverage idea steps go to a ChatGPT web handoff (serial): prepare a
          packet, send it, save the reply, ingest it locally into the same files.
hitl      a human sets the run's goal and budget cap at intake and makes the final decision.
web+hitl  both.

An idea run stores its mode in run.json at init; that mode wins over whatever a
later call passes, and changes only through `forge run set-mode` (recorded).
Every LLM step also records provenance after its outputs are written, which
stamps them as accepted, so runs in different modes compare on the same artifacts.
"""
from __future__ import annotations

import os

from forge.handoff import deps_fingerprint, handoff_dir, response_path
from forge.navigator import forge_cmd
from forge.util import read_json

MODES = {"auto", "web", "hitl", "web+hitl"}
# Idea-run steps worth a serial web call, with the web action and suggested model tier.
WEB_STEPS = {"bottleneck": ("design", "Pro"), "generate": ("design", "Pro"), "revise": ("design", "Pro"),
             "coherence": ("challenge", "Extra High"), "audit": ("challenge", "Extra High"),
             # study actions (forge/study_nav.py)
             "construct": ("design", "Pro"), "evolve": ("design", "Pro"), "plan_test": ("design", "Pro"),
             "review": ("challenge", "Extra High")}
INTAKE = ("Before the run starts, ask the person (one short message): the research question in their words, the "
          "budget cap they authorize (GPU-days, API dollars, wall-clock; or 'not specified'), and any solution "
          "shape they want or rule out. Pass their answers to the init command (--question/--goal, --budget); "
          "never fill them in yourself.")


def resolve_mode(mode=None):
    mode = mode or os.environ.get("FORGE_MODE") or "auto"
    if mode not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    return mode


def scope_args(scope):
    kind, project, name = scope
    return ["--project", str(project), f"--{kind}", name]


def route(step, mode, scope):
    """scope = ("run", project, run_slug) or ("domain", project, domain_slug). A run's stored mode wins."""
    mode = resolve_mode(step.get("mode") or mode)
    step = {**step, "mode": mode, "executor": None}
    kind = step["type"]
    if kind == "bash":
        step["executor"] = "local:operator"
        if "hitl" in mode and step["step"] in {"run_init", "study_init"}:
            return {**step, "type": "human_gate", "executor": "human", "notes": step["notes"] + [INTAKE]}
        return step
    if kind == "human_gate" and step.get("outputs"):  # a gate the navigator marked: the person writes the outputs
        return _with_provenance({**step, "executor": "human"}, scope, "human")
    if kind != "llm":
        return step
    if "hitl" in mode and step["role"] == "gate":
        step.update(type="human_gate", executor="human", notes=step["notes"] + [
            "Show the human a short evidence summary (verdict, scores, unmet expectations, scoop risk, kill switch) and "
            "the options from the prompt; write their choice with decided_by \"human\". Do not decide for them."])
        return _with_provenance(step, scope, "human")
    if "web" in mode and scope[0] in {"run", "study"} and step["step"] in WEB_STEPS:
        return _web(step, scope)
    return _with_provenance({**step, "executor": f"local:{step['seat']}"}, scope, f"local:{step['seat']}")


def _web(step, scope):
    action, tier = WEB_STEPS[step["step"]]
    hdir = handoff_dir(scope, step["step"])
    receipt = read_json(hdir / "receipt.json")
    prepare = forge_cmd("handoff", "prepare", *scope_args(scope), "--step", step["step"], "--action", action, "--tier", tier)
    if receipt is None:
        return {**step, "type": "bash", "executor": "local:operator", "run": [prepare],
                "notes": [f"Prepare a self-contained web packet ({action}, {tier}) for {hdir.name}; local files are "
                          "inlined because the web cannot read them."]}
    if receipt.get("deps_fingerprint") != deps_fingerprint(scope, step.get("deps", [])):
        return {**step, "type": "bash", "executor": "local:operator", "run": [prepare + " --supersede"],
                "notes": [f"The files {hdir.name} was built from changed since it was prepared; a reply to the old "
                          "packet must not be ingested. Supersede it (kept as history) and prepare a new one."]}
    if not response_path(hdir).exists():
        return {**step, "type": "web_handoff", "executor": f"web:{tier}", "inputs": [str(hdir / "packet.md")],
                "outputs": [str(response_path(hdir))], "run": [], "notes": [
                    f"Send packet.md to ChatGPT ({tier}) in a NEW conversation; the web is serial, one handoff at a time.",
                    f"Record it: {forge_cmd('handoff', 'mark', *scope_args(scope), '--step', step['step'], '--status', 'sent', '--url', '<conversation url>')}",
                    "Save the full reply verbatim to response.md, then run `forge next` again.",
                    "If the web route is unavailable, say so; switch with `forge run set-mode --mode auto` to fill the role locally."]}
    return _with_provenance({**step, "executor": f"web:{tier}", "seat": "forge-critic",
                             "inputs": [str(response_path(hdir)), *step["inputs"]],
                             "notes": step["notes"] + [
                                 f"INGEST: the first input is the web reply for {hdir.name}. Transcribe it into the "
                                 "output files per the prompt's contract. Add no content of your own; where the reply "
                                 "lacks a required field, write what the reply implies and flag it in the most relevant "
                                 "free-text field."]},
                            scope, f"web:{tier}")


def _with_provenance(step, scope, executor):
    record = forge_cmd("provenance", *scope_args(scope), "--step", step["step"], "--executor", executor, "--mode", step["mode"],
                       *[a for path in step["outputs"] for a in ("--output", path)])
    return {**step, "run_after": [record]}
