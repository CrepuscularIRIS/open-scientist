"""Deterministic study actions: execute a planned test, collision search, absorb a delegate, record a person.

Execution (protocol 4): the planned command runs as a child process; the wrapper records the command, cwd, git
commit and dirty flag, start and end, exit code, and stdout/stderr as files with hashes, then writes the raw
outputs as materials and moves the activity to completed or failed in one transaction. `attempt.json` makes an
interruption visible: on resume a live wrapper is waited for; a dead one without a recorded exit becomes
`failed (interrupted)`, and the command is never rerun under the same activity.
"""
from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

from forge.records import Store
from forge.study import StudyLayout, apply_commit
from forge.util import now, read_json, read_jsonl, sha256_file, write_json


def _proc_start(pid):
    """Process start time from /proc (Linux); without /proc, 'alive' or None from a signal-0 probe."""
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError, TypeError):
        if Path("/proc/self/stat").exists() or not isinstance(pid, int):
            return None
        try:
            os.kill(pid, 0)
            return "alive"
        except OSError:
            return None


def _git(cwd):
    def run(*args):
        try:
            return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    commit = run("rev-parse", "HEAD")
    return {"commit": commit or None, "dirty": bool(run("status", "--porcelain")) if commit else None}


def _activity(layout, proposal):
    return layout.store.find(proposal["subject"]["id"])


def attempt_state(layout, n):
    """'none' | 'running' | 'finished' | 'interrupted' | 'forged' for proposal n's run_test.

    An attempt counts only when the store holds the activity's `running` version with the same start and the
    planned command: that version is written before the command starts, so a hand-written attempt.json is 'forged'.
    """
    adir = layout.action_dir(n, "run_test")
    attempt = read_json(adir / "attempt.json")
    if not attempt:
        return "none", None
    proposal = read_json(layout.proposal_path(n)) or {}
    activity = _activity(layout, proposal) if isinstance(proposal.get("subject"), dict) else None
    execution = (activity or {}).get("payload", {}).get("execution") or {}
    if not activity or activity["payload"]["status"] != "running" or execution.get("started_at") != attempt.get("started_at") \
            or attempt.get("command") != activity["payload"].get("command"):
        return "forged", attempt
    if attempt.get("exit_code") is not None:
        return "finished", attempt
    alive = _proc_start(attempt.get("wrapper_pid")) == attempt.get("wrapper_start") and attempt.get("wrapper_start") is not None
    return ("running" if alive else "interrupted"), attempt


def _materials(layout, n, adir, attempt):
    out = []
    for name in ("stdout.txt", "stderr.txt"):
        f = adir / name
        if f.exists():
            out.append({"kind": "material", "id": f"out-{n:03d}-{name.split('.')[0]}", "expected_version": 0, "payload": {
                "source": f"run_test {n:03d}: {attempt['command']}", "content": f"{name} of the planned command (exit "
                f"{attempt.get('exit_code')})", "type": "output", "access": "executed", "path": str(f.relative_to(layout.project)),
                "sha256": sha256_file(f), "locator": f"git {attempt['git'].get('commit')} dirty={attempt['git'].get('dirty')}"}})
    cwd = Path(attempt["cwd"]).resolve()
    for i, rel in enumerate(attempt.get("declared_outputs", [])):
        f = (cwd / rel).resolve()
        # Only a file this run wrote: under its cwd and modified after it started.
        if f.is_file() and f.is_relative_to(cwd) and f.stat().st_mtime >= attempt.get("started_epoch", float("inf")):
            out.append({"kind": "material", "id": f"out-{n:03d}-file{i}", "expected_version": 0, "payload": {
                "source": f"run_test {n:03d} output {rel}", "content": f"declared output {rel}", "type": "output",
                "access": "executed", "path": str(f), "sha256": sha256_file(f)}})
    return out


def _finish(layout, n, proposal, attempt, failure=None):
    adir = layout.action_dir(n, "run_test")
    running = _activity(layout, proposal)
    mats = _materials(layout, n, adir, attempt)
    ok = failure is None and attempt.get("exit_code") == 0
    outputs = [{"id": m["id"], "version": 1} for m in mats]
    final = {**running["payload"], "outputs": outputs,
             "execution": {**running["payload"]["execution"], "ended_at": attempt.get("ended_at"), "exit_code": attempt.get("exit_code")}}
    if ok:
        final.update(status="completed", result=f"exit 0; raw outputs {', '.join(o['id'] for o in outputs)}")
    else:
        final.update(status="failed", failure=failure or f"exit {attempt.get('exit_code')}; see the raw outputs")
    write_json(adir / "commit.json", {"records": mats + [
        {"kind": "activity", "id": running["id"], "expected_version": running["version"], "payload": final}]})
    return apply_commit(layout, n, "run_test", proposal)


def exec_activity(layout: StudyLayout, n):
    """Run the planned command of proposal n's activity (blocking), then commit its raw outputs."""
    proposal = read_json(layout.proposal_path(n))
    adir = layout.action_dir(n, "run_test")
    state, attempt = attempt_state(layout, n)
    if state == "forged":
        raise ValueError(f"run_test {n:03d}: attempt.json is not backed by a recorded start of the planned command")
    if state == "running":
        raise ValueError(f"run_test {n:03d} is still running (wrapper pid {attempt['wrapper_pid']}); wait for it")
    if state == "finished":
        return _finish(layout, n, proposal, attempt)
    if state == "interrupted":
        if attempt.get("child_pgid"):
            try:  # the command may outlive its wrapper; stop it so nothing writes after the run is recorded
                os.killpg(attempt["child_pgid"], signal.SIGKILL)
            except OSError:
                pass
        return _finish(layout, n, proposal, attempt, failure="interrupted: the wrapper stopped before the command "
                       "finished; the command is not rerun under this activity (plan a new activity to run again)")
    plan = layout.store.get(proposal["subject"]["id"], proposal["subject"]["version"])
    cwd = layout.resolve(plan["payload"].get("cwd") or layout.project)
    adir.mkdir(parents=True, exist_ok=True)
    started = now()
    attempt = {"command": plan["payload"]["command"], "cwd": str(cwd), "git": _git(cwd), "started_at": started,
               "started_epoch": time.time(), "wrapper_pid": os.getpid(), "wrapper_start": _proc_start(os.getpid()),
               "declared_outputs": proposal.get("declared_outputs", []), "exit_code": None}
    running = {**plan["payload"], "status": "running",
               "execution": {"command": attempt["command"], "cwd": attempt["cwd"], "git": attempt["git"], "started_at": started}}
    layout.store.put("activity", plan["id"], running, plan["version"])  # recorded before the command starts
    write_json(adir / "attempt.json", attempt)
    limit = 60 * float(layout.meta()["policy"]["budget"].get("wall_clock_min") or 30)
    failure = None
    with (adir / "stdout.txt").open("w") as out, (adir / "stderr.txt").open("w") as err:
        proc = subprocess.Popen(attempt["command"], shell=True, cwd=cwd, stdout=out, stderr=err, start_new_session=True)
        write_json(adir / "attempt.json", {**attempt, "child_pgid": proc.pid})
        attempt["child_pgid"] = proc.pid
        try:
            code = proc.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)  # the whole group: no child keeps writing after the run is recorded
            proc.wait()
            code, failure = -9, f"timeout after {limit:.0f} s (the study's wall_clock_min); the process group was killed"
    attempt.update(exit_code=code, ended_at=now())
    write_json(adir / "attempt.json", attempt)
    return _finish(layout, n, proposal, attempt, failure=failure)


def wait(layout, n, poll=2.0, limit=None):
    start = time.time()
    while attempt_state(layout, n)[0] == "running":
        if limit and time.time() - start > limit:
            return {"state": "running"}
        time.sleep(poll)
    return {"state": attempt_state(layout, n)[0]}


# ---------------------------------------------------------------- collision

def collide(layout: StudyLayout, n, fetcher=None):
    """RS's two channels over arXiv for the proposal's terms, anchored on the study's creation date."""
    from forge.runs import _expression, _months_before
    from forge.vendor.corpus import Corpus
    proposal = read_json(layout.proposal_path(n))
    terms = proposal["terms"]
    windows = terms.get("windows") or {"signature_months": 10, "alias_months": 48}  # validated in check_proposal
    anchor = date.fromisoformat(layout.meta()["created"][:10])
    adir = layout.action_dir(n, "collision")
    rows = {}
    for channel, months in (("signature", windows["signature_months"]), ("alias", windows["alias_months"])):
        root = adir / channel
        config = {"name": f"{layout.slug}-{n:03d}-{channel}", "start_date": _months_before(anchor, months).isoformat(),
                  "end_date": anchor.isoformat(), "page_size": 50,
                  "queries": [{"id": channel, "lane": "in_domain", "domain": "collision",
                               "search_query": _expression(terms[f"{channel}_terms"][:8]), "max_results": 100}]}
        with Corpus(root) as corpus:
            report = corpus.harvest(config, fetcher=fetcher)
            if not report["collection_ok"]:
                raise ValueError(f"collision {channel} channel incomplete; rerun to resume")
            corpus.export(root / "papers.jsonl")
        for paper in read_jsonl(root / "papers.jsonl"):
            rows.setdefault(paper["arxiv_id"], {**{k: paper.get(k) for k in ("arxiv_id", "title", "published", "abs_url")},
                                                "channels": []})["channels"].append(channel)
    pool = adir / "papers.jsonl"
    pool.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows.values()), encoding="utf-8")
    records = [{"kind": "material", "id": f"collision-{n:03d}", "expected_version": 0, "payload": {
        "source": f"collision {n:03d}: two arXiv channels", "content": f"{len(rows)} papers ({sum('alias' in r['channels'] for r in rows.values())} "
        "alias-channel); an empty pool is not novelty", "type": "paper", "access": "identity",
        "path": str(pool.relative_to(layout.project)), "sha256": sha256_file(pool), "scope": json.dumps(windows)}}]
    write_json(adir / "commit.json", {"records": records})
    return apply_commit(layout, n, "collision", proposal)


# ---------------------------------------------------------------- delegates

def _file_material(layout, rid, path, source, content, mtype="note", access="inspected"):
    path = Path(path)
    return {"kind": "material", "id": rid, "expected_version": (layout.store.find(rid) or {"version": 0})["version"],
            "payload": {"source": source, "content": content, "type": mtype, "access": access,
                        "path": str(path), "sha256": sha256_file(path)}}


def absorb(layout: StudyLayout, n):
    """Bring a finished delegate's results into the records (domain bundle, or idea-run card, audit and decision)."""
    proposal = read_json(layout.proposal_path(n))
    action = proposal["action"]
    adir = layout.action_dir(n, action)
    adir.mkdir(parents=True, exist_ok=True)
    records = []
    if action == "build_domain":
        from forge.util import Layout
        dom = Layout(layout.project, proposal["domain"])
        version = dom.current_version()
        if version is None:
            raise ValueError("the domain build did not freeze a version; resume it or ask the person")
        records.append(_file_material(layout, f"domain-{dom.domain}", dom.version_dir(version) / "manifest.json",
                                      f"build_domain {dom.domain} v{version}",
                                      f"frozen domain bundle v{version}: cards, expectations, lexicon, crossmap, stats",
                                      mtype="asset"))
    else:
        from forge.runs import RunLayout
        run = RunLayout(layout.project, proposal["run"])
        outcome = next((label for name, label in (("DONE", "done"), ("failed.md", "failed"),
                                                   ("do_not_generate.md", "do_not_generate")) if run.file(name).exists()), "stopped")
        main = run.file("idea_card.md") if outcome == "done" else run.file("failed.md" if outcome == "failed" else "do_not_generate.md")
        if not main.exists():
            main = run.file("run.json")
        records.append(_file_material(layout, f"idea-run-{run.run}", main, "idea_run", f"idea_run {run.run} ended {outcome}"))
        records[-1]["payload"]["scope"] = f"outcome:{outcome}"
        if outcome == "done":
            card, decision = read_json(run.file("idea_card.json")), read_json(run.file("decision.json"))
            q = layout.store.get("q")
            cid = f"absorbed-h-{run.run}"
            current = layout.store.find(cid)
            records.append({"kind": "candidate", "id": cid, "expected_version": current["version"] if current else 0, "payload": {
                "problem": {"id": "q", "version": q["version"]}, "mechanism": card["core_claim"],
                "claims": {"core": card["core_claim"], **{f"sub{i + 1}": c for i, c in enumerate(card["sub_claims"])}},
                "predictions": [f"{card['falsification']['metric']} {card['falsification']['direction']}",
                                card["falsification"]["negative_control"]],
                "rivals": [read_json(run.canonical())["naive_baseline"]["naive"]], "operator": "construct",
                "change_note": f"absorbed from idea_run {run.run}" if current else None}})
            ver = (current["version"] if current else 0) + 1
            records.append({"kind": "assessment", "id": f"absorbed-decision-{run.run}", "expected_version":
                            (layout.store.find(f"absorbed-decision-{run.run}") or {"version": 0})["version"], "payload": {
                                "type": "decision", "subject": {"id": cid, "version": ver},
                                "decision": {"pursue": "pursue", "park": "park", "kill": "kill"}[decision["decision"]],
                                "rationale": decision["rationale"], "decided_by": decision["decided_by"],
                                "revisit_when": decision.get("revisit_conditions") or None}})
    write_json(adir / "commit.json", {"records": records})
    return apply_commit(layout, n, action, proposal)


# ---------------------------------------------------------------- people

def answer(layout: StudyLayout, n, text, approve=None):
    """Record a person's answer: to an ask_human proposal, or to an authorization request (approve True/False)."""
    if not text or not text.strip():
        raise ValueError("record the person's words (--text)")
    proposal = read_json(layout.proposal_path(n))
    q = layout.store.find("q")
    subject = {"id": q["id"], "version": q["version"]} if q else None
    if approve is not None:
        from forge.study import proposal_sha
        sha = proposal_sha(layout, n)
        rec = layout.store.find(f"auth-{n:03d}")
        layout.store.put("assessment", f"auth-{n:03d}", {"type": "feedback", "subject": subject, "source": "human",
                                                          "text": f"[{'approved' if approve else 'denied'} proposal {n:03d} "
                                                                  f"sha256 {sha}] {text.strip()}"}, rec["version"] if rec else 0)
        write_json(layout.dir / "proposals" / f"{n:03d}.auth.json",
                   {"approved": bool(approve), "by": "human", "text": text.strip(), "at": now(), "proposal_sha256": sha})
        return {"proposal": n, "approved": bool(approve), "proposal_sha256": sha}
    adir = layout.action_dir(n, "ask_human")
    adir.mkdir(parents=True, exist_ok=True)
    write_json(adir / "commit.json", {"records": [{"kind": "assessment", "id": f"answer-{n:03d}", "expected_version": 0,
                                                   "payload": {"type": "feedback", "subject": subject, "source": "human",
                                                               "text": text.strip()}}]})
    return apply_commit(layout, n, "ask_human", proposal)


def shlex_join(cmd):
    return " ".join(shlex.quote(c) for c in cmd)


__all__ = ["exec_activity", "wait", "collide", "absorb", "answer", "attempt_state", "Store"]
