"""Study navigator: one step at a time for a question-driven study (read-only; resuming is calling it again).

    no study            -> study_init (the user's goal, verbatim; a person sets goal and budget in hitl)
    no intake           -> intake (question record q, kit.json: task types, deliverable, assets, variants)
    current proposal:
      invalid           -> propose again with FIX lines
      outside policy    -> authorize (a person approves or denies)
      accepted          -> the action: an llm step that writes commit.json, then `commit`;
                           run_test / collision: a deterministic command; build_domain / idea_run: the delegate's
                           own steps (RS's strict domain build or idea chain), then `absorb`
    nothing pending     -> done (report committed) | stuck (no progress) | budget | propose the next action

The agent chooses what to do next; this code checks that the choice has its inputs, current versions,
authorization and contract.
"""
from __future__ import annotations

from forge import study
from forge.execute import attempt_state
from forge.handoff import step_runs
from forge.kit import validate_policy
from forge.navigator import accept_step, forge_cmd, review_state, stale_note, step
from forge.util import BadJSON, read_json

MAX_STEP_RUNS = 5
METHODS = {
    "intake": "study/intake.md", "propose": "study/propose.md", "adapt": "study/adapt.md", "retrieve": "study/retrieve.md",
    "read": "study/read.md", "diagnose": "study/diagnose.md", "construct": "study/construct.md", "evolve": "study/evolve.md",
    "coherence": "study/coherence.md", "review": "study/review.md", "plan_test": "study/plan_test.md",
    "interpret": "study/interpret.md", "decide": "study/decide.md", "report": "study/report.md",
}
ROLES = {"intake": "design", "propose": "design", "adapt": "design", "retrieve": "fast", "read": "read", "diagnose": "design",
         "construct": "design", "evolve": "design", "coherence": "review", "review": "audit", "plan_test": "design",
         "interpret": "review", "decide": "gate", "report": "review"}


def _ids(layout):
    return ("--project", str(layout.project), "--study", layout.slug)


def context_note(layout):
    return (f"Read the record context first: {forge_cmd('records', 'context', '--project', str(layout.project), '--study', layout.slug)} "
            "(latest records, stale inputs, earlier contrary findings, open feedback). Cite records as {id, version}.")


def _llm(layout, name, outputs, deps, errors, inputs, notes=(), prompt=None):
    scope = ("study", layout.project, layout.slug)
    state, changed = review_state(outputs, deps)
    if not outputs[0].exists() or errors or state in {"stale", "edited"}:
        if errors and step_runs(scope, name) >= MAX_STEP_RUNS:
            return step("stuck", "terminal", "gate", state=name, outputs=outputs, errors=errors, notes=[
                f"{name} was filled {MAX_STEP_RUNS} times and still fails validation; a person should look."])
        return step(name, "llm", ROLES.get(name, "design"), prompt=prompt or METHODS[name], inputs=inputs, outputs=outputs,
                    deps=deps, errors=errors, notes=[*notes, context_note(layout), *stale_note(changed, state)])
    if state == "unaccepted":
        return accept_step(name, outputs, deps, _ids(layout))
    return None


def next_study(layout: study.StudyLayout, goal=None, mode=None, budget=None):
    ids = _ids(layout)
    if not layout.file("study.json").exists():
        if not goal:
            return step("need_goal", "terminal", "gate", notes=["Pass --goal \"<the user's research question, verbatim>\"."])
        return step("study_init", "bash", "operator", run=[forge_cmd("study", "init", *ids, "--goal", goal,
                                                                   "--mode", mode or "auto", *(["--budget", budget] if budget else []))])
    meta = layout.meta()
    errors = validate_policy((meta or {}).get("policy")) or layout.policy_errors()
    if errors:
        return step("policy", "terminal", "gate", errors=errors, notes=[
            "The study's policy is invalid or was edited outside `forge study policy` (a person's command)."])
    try:
        result = _next(layout, ids, meta)
    except BadJSON as exc:
        return step("fix_json", "terminal", "gate", errors=[str(exc)], notes=["An agent-written file is not valid JSON."])
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        return step("malformed", "terminal", "gate", errors=[f"{type(exc).__name__}: {exc}"],
                    notes=["A study file is malformed or changed outside its command; restore it or fix it, then call next."])
    from forge.kit import mode_name
    return {**result, "mode": result.get("mode") or mode_name(meta["policy"])}


def _intake(layout, ids, meta):
    adir = layout.action_dir(0, "intake")
    commit, kit = adir / "commit.json", adir / "kit.json"
    errors = []
    if commit.exists():
        data = read_json(commit)
        proposal = {"action": "intake", "may_change": ["Q", "assets"]}
        errors = study.validate_commit(layout, "intake", data, proposal)
        kit_items = [it for it in (data or {}).get("records", []) if isinstance(it, dict) and it.get("id") == "kit"]
        if not kit_items:
            errors.append("intake also registers kit.json as material id kit (type asset, path, sha256)")
        else:
            from forge import assets
            from forge.kit import validate_kit
            errors += validate_kit(read_json(kit), assets.KINDS)
    s = _llm(layout, "intake", [commit, kit], [layout.file("study.json")], errors,
             inputs=[layout.file("study.json")],
             notes=["Write kit.json and commit.json in the action folder. The question record q holds the user's goal "
                    "(verbatim) and their hard constraints; the kit chooses task types, deliverable, the asset kinds the "
                    "first decisions need and one variant per task type (references/variants/)."])
    if s:
        return s
    return step("commit", "bash", "operator", state="intake", run=[forge_cmd("study", "commit", *ids, "--proposal", "0")])


def _next(layout, ids, meta):
    if not layout.committed(0, "intake"):
        return _intake(layout, ids, meta)
    numbers = layout.proposals()
    if numbers:
        n = numbers[-1]
        proposal = read_json(layout.proposal_path(n))
        action = proposal.get("action") if isinstance(proposal, dict) else None
        marker = layout.committed(n, action) if isinstance(action, str) and action in study.ACTIONS else None
        if not marker:
            return {**_current(layout, ids, meta, n, proposal if isinstance(proposal, dict) else {}), "proposal": n}
    return {**_between(layout, ids, meta, (numbers[-1] if numbers else 0) + 1), "proposal": (numbers[-1] if numbers else 0) + 1}


def _between(layout, ids, meta, n):
    commits = layout.commits()
    if any(a == "report" for _, a, _ in commits):
        return step("done", "terminal", "operator", notes=[f"Study {layout.slug} delivered its report."],
                    outputs=[layout.dir / "actions"])
    tail = [m for _, a, m in commits if a != "intake"][-study.MAX_UNPRODUCTIVE:]
    if len(tail) == study.MAX_UNPRODUCTIVE and not any(m.get("productive") for m in tail):
        return step("stuck", "terminal", "gate", notes=[
            f"The last {study.MAX_UNPRODUCTIVE} actions produced nothing new (no new material, no changed Q/H/T, no "
            "changed finding, no decision). A person should choose: narrow the question, add material, or stop."])
    if len(commits) - 1 >= meta["policy"]["max_actions"]:
        return step("budget", "terminal", "gate", notes=[f"{meta['policy']['max_actions']} actions used (policy.max_actions)."])
    out = layout.proposal_path(n)
    kit = layout.kit() or {}
    open_rule = study.completion_errors(layout, kit.get("deliverable", "report"))
    return step("propose", "llm", "design", prompt=METHODS["propose"], outputs=[out],
                inputs=[layout.file("study.json"), *([layout.resolve(layout.store.get("kit")["payload"]["path"])] if layout.store.find("kit") else []),
                        layout.dir / "actions"],
                notes=[context_note(layout),
                       f"Deliverable {kit.get('deliverable')}: " + ("its completion rule holds; you may propose report."
                                                                    if not open_rule else "not yet complete: " + "; ".join(open_rule)),
                       "Propose ONE action that answers the open question most likely to change the next decision."])


def _current(layout, ids, meta, n, proposal):
    path = layout.proposal_path(n)
    if proposal.get("action") == "run_test" and attempt_state(layout, n)[0] != "none":
        return _run_test(layout, ids, n)  # started: resume from the recorded attempt, never re-plan it
    errors, ask = study.check_proposal(layout, n)
    if errors:
        scope = ("study", layout.project, layout.slug)
        if step_runs(scope, "propose") >= MAX_STEP_RUNS:
            return step("stuck", "terminal", "gate", state="propose", errors=errors, notes=["Proposals keep failing the check."])
        return step("propose", "llm", "design", prompt=METHODS["propose"], inputs=[layout.file("study.json")], outputs=[path],
                    errors=errors, notes=[context_note(layout), f"Rewrite proposal {n:03d}; the check refused it."])
    answer = study.authorized(layout, n)
    if ask and answer is not True:
        if answer is False:
            text = read_json(layout.dir / "proposals" / f"{n:03d}.auth.json").get("text")
            return step("propose", "llm", "design", prompt=METHODS["propose"], inputs=[layout.file("study.json")], outputs=[path],
                        errors=[f"a person denied proposal {n:03d}: {text}"],
                        notes=[context_note(layout), "Propose a different action within the authorization."])
        return step("authorize", "human_gate", "gate", inputs=[path], notes=[
            f"Proposal {n:03d} ({proposal['action']}) needs a person: " + "; ".join(ask),
            "Show them the proposal's open question, why now and cost; record exactly their answer: "
            + forge_cmd("study", "answer", *ids, "--proposal", str(n), "--approve|--deny", "--text", "<their words>")])
    action = proposal["action"]
    adir = layout.action_dir(n, action)
    if action == "ask_human":
        return step("ask_human", "human_gate", "gate", inputs=[path], notes=[
            f"Ask the person: {proposal['open_question']} ({proposal.get('reason')}). Record their words: "
            + forge_cmd("study", "answer", *ids, "--proposal", str(n), "--text", "<their words>")])
    if action == "run_test":
        return _run_test(layout, ids, n)
    if action == "collision":
        return step("collision", "bash", "operator", run=[forge_cmd("study", "collide", *ids, "--proposal", str(n))],
                    notes=["Two arXiv channels: own terms, recent window; other communities' names, long window."])
    if action in study.DELEGATES:
        return _delegate(layout, ids, meta, n, proposal)
    commit = adir / "commit.json"
    errors = study.validate_commit(layout, action, read_json(commit), proposal) if commit.exists() else []
    s = _llm(layout, action, [commit], [path], errors, inputs=[path, layout.file("study.json")],
             notes=[f"Action {n:03d}: write files under {adir} and the records to commit in commit.json "
                    "(contract: prompts/study/contracts.md)."])
    if s:
        if action == "decide" and meta["policy"]["participation"] == "human_decisions" and s["type"] == "llm":
            s = {**s, "type": "human_gate", "notes": s["notes"] + [
                "This study's decisions are a person's: show the evidence summary and write their choice, decided_by human."]}
        return s
    return step("commit", "bash", "operator", state=action, run=[forge_cmd("study", "commit", *ids, "--proposal", str(n))])


def _run_test(layout, ids, n):
    state, attempt = attempt_state(layout, n)
    if state == "forged":
        return step("attempt_mismatch", "terminal", "gate", state="run_test", errors=[
            f"actions/{n:03d}-run_test/attempt.json is not backed by the recorded start of the planned command"],
            notes=["Restore or remove the attempt file; a run counts only when `forge study exec` started it."])
    if state == "running":
        return step("wait", "bash", "operator", state="run_test", run=[forge_cmd("study", "wait", *ids, "--proposal", str(n))],
                    notes=[f"run_test {n:03d} is running (wrapper pid {attempt['wrapper_pid']}); wait, do not start it again."])
    return step("run_test", "bash", "operator", run=[forge_cmd("study", "exec", *ids, "--proposal", str(n))],
                notes=["Runs the planned command and records its raw outputs; long commands may run in the background."
                       if state == "none" else f"The previous attempt is {state}; this records it without rerunning."])


def _delegate(layout, ids, meta, n, proposal):
    """Run RS's strict chains inside the study: the inner navigator's own steps, then absorb its results."""
    from forge.kit import mode_name
    if proposal["action"] == "build_domain":
        from forge.navigator import next_domain
        from forge.util import Layout
        dom = Layout(layout.project, proposal["domain"])
        inner = next_domain(dom, topic=proposal.get("topic"), read_limit=proposal.get("read_limit"))
        scope = ["domain", str(layout.project), dom.domain]
        done = inner["step"] == "domain_ready"
    else:
        from forge.run_nav import next_run
        from forge.runs import RunLayout
        run = RunLayout(layout.project, proposal["run"])
        q = layout.store.get("q")
        inner = next_run(run, domain=proposal["domain"], question=proposal.get("question") or q["payload"]["question"],
                         mode=mode_name(meta["policy"]), budget=meta["policy"]["budget"]["authorized"])
        scope = ["run", str(layout.project), run.run]
        done = inner["step"] in {"done", "failed", "do_not_generate"}
    if done:
        return step("absorb", "bash", "operator", state=proposal["action"],
                    run=[forge_cmd("study", "absorb", *ids, "--proposal", str(n))],
                    notes=[f"The {proposal['action']} delegate ended at {inner['step']}; bring its results into the records."])
    return {**inner, "scope": scope, "notes": [f"Study {layout.slug} action {n:03d} ({proposal['action']}) runs RS's strict "
                                                "chain; follow its steps as given.", *inner["notes"]]}
