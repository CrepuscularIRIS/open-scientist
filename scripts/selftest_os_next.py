#!/usr/bin/env python3
"""Self-test of os_next.py (Open Scientist 0.10). No arguments, no network.

1. Label guard: every RS label os_next keys on still exists in the bundled RS source (an upstream rename must
   fail here, not silently skip a layer).
2. Trigger logic on synthetic run dirs: mainline -> gap gate -> admission (measured only) -> prior sweep ->
   classical -> pass-through to Phase 2 ->
   mechanism gate (before collision) -> protocol audit -> card gate -> selection -> pass-through;
   a KILL at either verifier stop -> terminal; overlays + extra inputs attached; prior-sweep stops
   (SOLVED_BY_SWITCH / IMMOVABLE); failure attribution before the structural audit counts a trained FAIL.
3. classical_check.py on a synthetic report: complete -> modeled, abstract-only -> lead, missing field -> incomplete.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import os_next as N  # noqa: E402


def main() -> int:
    ok = True

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name)

    src = "".join(p.read_text() for p in (N.ROOT / "skills" / "idea-spark" / "scripts").glob("*.py"))
    for lbl in N.RS_LABELS:
        check(f"RS label present: {lbl!r}", lbl in src)
    check("overlays exist", (N.OVER / "phase1.md").exists() and (N.OVER / "generation.md").exists())

    p1_step = f"STEP   : {N.LBL_PHASE1}\nTYPE   : llm_subagent"
    prep_step = f"STATE  : PREPARE\nSTEP   : {N.LBL_PREPARE} (deterministic)\nTYPE   : bash"
    gen_step = f"STATE  : REVIEW_REQUIRED\nSTEP   : {N.LBL_GENERATION}\nTYPE   : llm_subagent"
    skel_step = f"STATE  : DERIVE\nSTEP   : {N.LBL_SKELETON} and source mechanism record\nTYPE   : bash"
    coll_step = f"STATE  : RETRIEVAL_REQUIRED\nSTEP   : {N.LBL_COLLISION}\nTYPE   : bash"
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "proj"
        (proj / ".open-scientist").mkdir(parents=True)
        run = Path(td) / "run"
        name = lambda step: (N.decide(run, step, proj) or {}).get("name")
        (run / "phase0").mkdir(parents=True)
        check("Phase 1 -> mainline layer", name(p1_step) == "mainline")
        (run / "phase0" / "mainline_first.json").write_text("{}")
        check("mainline done -> causal-order audit", name(p1_step) == "causal")
        (run / "phase0" / "causal_order.json").write_text("{}")
        check("causal-order done -> RS Phase 1", name(p1_step) is None)
        (run / "phase1").mkdir()
        (run / "phase1" / "phase1_output.json").write_text(json.dumps({"state": "proceed"}))
        check("Phase 1 proceed -> gap gate", name(prep_step) == "gaps")
        (run / "phase1" / ".gap_filter_done").write_text("")
        check("gap gate done -> admission", name(prep_step) == "admit")
        (run / "phase1" / "admission.json").write_text(json.dumps({"gaps": [{"id": "G1", "phenomenon": "pending"}]}))
        check("pending admission blocks design", N.admission_pending(run) == ["G1"]
              and "ADMISSION_PENDING" in N.emit_pending(run, ["G1"]))
        (run / "phase1" / "admission.json").write_text(json.dumps({"gaps": [
            {"id": "G1", "phenomenon": "measured"}, {"id": "G2", "phenomenon": "out_of_scope"}]}))
        check("measured admission does not block", N.admission_pending(run) == [])
        adm = run / "phase1" / "admission.json"
        good = adm.read_text()
        for bad in ('{"gaps": {"G1": {"phenomenon": "measured"}}}', '{"gaps": ["G1"]}', '{}', '{"gaps": []}',
                    '{"gaps": [{"id": "G2", "phenomenon": "out_of_scope"}]}'):
            adm.write_text(bad)
            check(f"malformed / empty admission blocks: {bad[:28]}", len(N.admission_pending(run)) == 1)
        adm.write_text(good)
        check("admission done -> prior sweep", name(prep_step) == "sweep")
        sweep = run / "phase1" / "prior_sweep.json"
        for dec in ("SOLVED_BY_SWITCH", "IMMOVABLE"):
            sweep.write_text(json.dumps({"decision": dec}))
            check(f"prior sweep {dec} -> terminal", N.sweep_stop(run) == dec and dec in N.emit_sweep_stop(run, dec))
        sweep.write_text(json.dumps({"decision": "solved_by_switch"}))
        check("prior sweep decision is case-insensitive", N.sweep_stop(run) == "SOLVED_BY_SWITCH")
        sweep.write_text(json.dumps({"decision": "looks fine"}))
        check("unknown sweep decision -> sweep still due", name(prep_step) == "sweep")
        sweep.write_text(json.dumps({"decision": "RESIDUAL"}))
        check("prior sweep RESIDUAL -> keep going", N.sweep_stop(run) is None)
        check("prior sweep done -> classical", name(prep_step) == "classical")
        (run / "phase1" / "classical_anchors.json").write_text("{}")
        check("classical done -> property test (ml)", name(prep_step) == "property")
        N.DOMAIN = "general"
        check("general domain skips property test", name(prep_step) is None)
        N.DOMAIN = "ml"
        (run / "phase1" / ".property_tests_done").write_text("")
        check("property test done -> RS PREPARE", name(prep_step) is None)
        (run / "phase2_generate").mkdir()
        (run / "phase2_generate" / "closest_abstracts.json").write_text("{}")
        (run / "phase1" / "classical_anchors.json").unlink()
        check("Phase 2 started -> classical no longer due", name(gen_step) is None)
        (run / "phase1" / "classical_anchors.json").write_text("{}")
        extra = next((f(run, proj) for c, f in N.EXTRA if c(gen_step)), [])
        check("generation gets overlay + gate + anchors", N.OVER / "generation.md" in extra
              and run / "phase1" / "soundness_gaps.json" in extra and run / "phase1" / "classical_anchors.json" in extra)
        check("generation gets prior sweep + deploy contract", run / "phase1" / "prior_sweep.json" in extra
              and proj / ".open-scientist" / "deploy_contract.md" in extra)
        extra1 = next((f(run, proj) for c, f in N.EXTRA if c(p1_step)), [])
        check("Phase 1 gets overlay + mainline", N.OVER / "phase1.md" in extra1)
        check("collision -> mechanism gate", name(coll_step) == "early")
        (run / "soundness_early.json").write_text(json.dumps({"verdict": "CHECK"}))
        check("mechanism gate done -> RS collision", name(coll_step) is None)
        check("skeleton -> protocol audit (project-level)", name(skel_step) == "protocol")
        tool = proj / "tool.py"
        tool.write_text("x = 1\n")
        audit = proj / ".open-scientist" / "protocol_audit.json"
        audit.write_text(json.dumps({"tools": [{"path": "tool.py", "verdict": "PASS"}]}))
        check("audit without sha256 -> protocol still due", name(skel_step) == "protocol")
        import hashlib  # noqa: E402
        audit.write_text(json.dumps({"tools": [{"path": "tool.py", "verdict": "PASS",
                                                "sha256": hashlib.sha256(tool.read_bytes()).hexdigest()}]}))
        check("protocol done -> card gate", name(skel_step) == "cards")
        tool.write_text("x = 2\n")
        check("edited tool -> protocol audit stale", name(skel_step) == "protocol")
        tool.write_text("x = 1\n")
        (run / "soundness_cards.json").write_text(json.dumps({"verdict": "CHECK"}))
        check("card gate done -> selection", name(skel_step) == "select")
        (run / "selection.json").write_text("{}")
        check("selection done -> RS skeleton", name(skel_step) is None)
        check("CHECK not treated as killed", not N.killed(run))
        (run / "soundness_early.json").write_text(json.dumps({"verdict": "KILL", "kill_reasons": ["early"]}))
        kf = N.killed(run)
        check("mechanism KILL -> terminal", kf is not None and "CARD_KILLED" in N.emit_killed(kf) and "early" in N.emit_killed(kf))
        (run / "soundness_early.json").write_text(json.dumps({"verdict": "CHECK"}))
        (run / "soundness_cards.json").write_text(json.dumps({"verdict": "KILL", "kill_reasons": ["x"]}))
        check("card KILL -> terminal", N.killed(run) == run / "soundness_cards.json")
        reg = proj / ".open-scientist" / "cards.json"
        reg.write_text(json.dumps({"cards": [{"id": "a", "run": f"ideaspark_run/{run.name}", "verdict": "KILL"}]}))
        check("1 failure -> no structural audit", N.structural_state(run, proj)[0] is None)
        reg.write_text(json.dumps({"cards": [
            {"id": "a", "run": f"ideaspark_run/{run.name}", "verdict": "KILL"},
            {"id": "b", "run": f"ideaspark_run/{run.name}", "verdict": "PASS 9/12", "outcome": "FAIL"},
            {"id": "c", "run": "ideaspark_run/other", "verdict": "KILL"}]}))
        check("trained FAIL without attribution -> attribution due first", N.attribution_due(run, proj) == ["b"]
              and "ATTRIBUTION_DUE" in N.emit_attribution(run, ["b"]))
        mk = lambda attr, role="method": reg.write_text(json.dumps({"cards": [
            {"id": "a", "run": f"ideaspark_run/{run.name}", "verdict": "KILL"},
            {"id": "b", "run": f"ideaspark_run/{run.name}", "verdict": "PASS 9/12", "outcome": "FAIL",
             "attribution": attr, "role": role},
            {"id": "c", "run": "ideaspark_run/other", "verdict": "KILL"}]}))
        mk("IMPLEMENTATION: wrong ckpt")
        check("FAIL attributed to implementation is not a failed card",
              N.attribution_due(run, proj) == [] and N.structural_state(run, proj) == (None, ["a"]))
        mk("METHOD: premise falsified", role="upper_bound")
        check("upper-bound / baseline arms never count as failed cards", N.structural_state(run, proj) == (None, ["a"]))
        mk("METHOD: premise falsified")
        check("KILL + trained FAIL (METHOD) on this run -> audit due",
              N.structural_state(run, proj) == ("due", ["a", "b"]))
        # main()-level ordering, with the RS navigator stubbed out
        import contextlib, io  # noqa: E401,E402

        def run_main(step: str, mode: str = "full") -> str:
            real, argv, N.MODE = N.rs_next, sys.argv, mode
            N.rs_next = lambda r, q: (0, step)
            sys.argv = ["os_next.py", "--dir", str(run), "--project", str(proj)]
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    N.main()
            finally:
                N.rs_next, sys.argv, N.MODE = real, argv, "full"
            return buf.getvalue()

        mk("")
        check("main: unattributed FAIL is asked for before the structural audit",
              "ATTRIBUTION_DUE" in run_main(skel_step) and "STRUCTURAL_AUDIT" not in run_main(skel_step))
        mk("METHOD: premise falsified")
        check("main: attributed failures -> structural audit", "STRUCTURAL_AUDIT" in run_main(skel_step))
        (run / "structural_audit.json").write_text(json.dumps({"decision": "NOT_STRUCTURAL", "failures_at_audit": 2}))
        reg.write_text(json.dumps({"cards": [
            {"id": "a", "run": f"ideaspark_run/{run.name}", "verdict": "KILL"},
            {"id": "b", "run": f"ideaspark_run/{run.name}", "outcome": "FAIL", "attribution": "METHOD: x"},
            {"id": "d", "run": f"ideaspark_run/{run.name}", "outcome": "FAIL", "attribution": "METHOD: y"}]}))
        check("NOT_STRUCTURAL then a third failure -> audit again", N.structural_state(run, proj)[0] == "due")
        (run / "structural_audit.json").unlink()
        (run / "soundness_cards.json").write_text(json.dumps({"verdict": "CHECK"}))
        reg.write_text(json.dumps({"cards": []}))
        sweep.write_text(json.dumps({"decision": "IMMOVABLE"}))
        check("main: sweep stop ends the run", "PRIOR_SWEEP_STOP (IMMOVABLE)" in run_main(prep_step))
        check("a line that ends never re-scopes the deliverable", "never re-scope the paper" in run_main(prep_step)
              and "never re-scope the paper" in N.emit_structural("closed", run, []))
        sweep.write_text(json.dumps({"decision": "RESIDUAL"}))
        for f in ("phase2_generate/closest_abstracts.json",):
            (run / f).unlink()
        adm.write_text(json.dumps({"gaps": [{"id": "G1", "phenomenon": "pending"}]}))
        check("main: pending admission stops before design", "ADMISSION_PENDING" in run_main(prep_step, "lite"))
        adm.write_text(good)
        (run / "phase2_generate" / "closest_abstracts.json").write_text("{}")
        audit.unlink()
        lite_out = run_main(coll_step, "lite")
        check("main: lite exit names the card gate and warns about a stale evaluator audit",
              "LITE_CANDIDATE_READY" in lite_out and "EVALUATOR" in lite_out and "UPPER_BOUND" in lite_out)
        check("main: lite exit asks for two different arms on the same line", "TWO ARMS, ONE LINE" in lite_out
              and "sibling_candidate.json" in lite_out and "Never a second seed" in lite_out)
        check("generation receives the sibling candidate", run / "phase0" / "sibling_candidate.json"
              in next((f(run, proj) for c, f in N.EXTRA if c(gen_step)), []))
        # per-TARGET counting and gate kills
        (run / "soundness_cards.json").write_text(json.dumps({"verdict": "KILL", "kill_reasons": ["x"]}))
        check("unregistered card-gate KILL counts once", N.run_failures(run, proj) == ["card-gate"])
        reg.write_text(json.dumps({"cards": [{"id": "k", "run": f"ideaspark_run/{run.name}", "verdict": "KILL"}]}))
        check("registered gate KILL is not counted twice", N.run_failures(run, proj) == ["k"])
        (run / "soundness_cards.json").write_text(json.dumps({"verdict": "CHECK"}))
        (run / "phase0" / "same_target_runs.txt").write_text("ideaspark_run/prev_run\n")
        reg.write_text(json.dumps({"cards": [{"id": "k", "run": f"ideaspark_run/{run.name}", "verdict": "KILL"},
                                             {"id": "p", "run": "ideaspark_run/prev_run", "verdict": "KILL"}]}))
        check("failures carry over from earlier runs on the same TARGET",
              N.structural_state(run, proj) == ("due", ["k", "p"]))
        (run / "phase0" / "same_target_runs.txt").unlink()
        reg.write_text(json.dumps({"cards": [{"id": "g", "run": f"ideaspark_run/{run.name}", "verdict": "CHECK",
                                              "outcome": "FAIL", "attribution": "GAP: criterion immovable"}]}))
        check("one FAIL attributed to the gap -> audit due at once", N.structural_state(run, proj) == ("due", ["g"]))
        mk("METHOD: premise falsified")
        (run / "structural_audit.json").write_text(json.dumps({"decision": "NOT_STRUCTURAL", "failures_at_audit": 2}))
        check("NOT_STRUCTURAL buys one more card", N.structural_state(run, proj)[0] is None)
        (run / "structural_audit.json").write_text(json.dumps({"decision": "STRUCTURAL", "failures_at_audit": 2}))
        check("STRUCTURAL closes the run", N.structural_state(run, proj)[0] == "closed"
              and "RUN_CLOSED" in N.emit_structural("closed", run, []))
        N.MODE = "lite"
        check("lite exits at first collision", N.lite_exit(f"STEP   : {N.LBL_COLLISION}"))
        check("lite does not exit at Phase 1", not N.lite_exit(f"STEP   : {N.LBL_PHASE1}"))
        N.MODE = "full"
        check("full mode never lite-exits", not N.lite_exit(f"STEP   : {N.LBL_COLLISION}"))
        reg.write_text(json.dumps({"cards": []}))
        (run / "structural_audit.json").unlink()
        for L in N.LAYERS:
            check(f"layer {L['name']} has a kind", L.get("kind") in ("rank", "verify", "model", "measure"))
        check("lite keeps the prior sweep", "sweep" not in N.LITE_SKIP)

        import property_check as P  # noqa: E402
        (run / "phase1" / "anchor_tests.json").write_text(json.dumps({"tests": [
            {"obj_id": "ok", "T2": {"pass": True}}, {"obj_id": "kill", "T2": {"pass": False}},
            {"obj_id": "unt", "T2": {"pass": None}}, {"obj_id": "none"}]}))
        v = P.check(run)
        check("property_check: verdicts", v == {"ok": "PASS", "kill": "KILL", "unt": "UNTESTABLE", "none": "UNTESTABLE"})
        (run / "phase1" / "classical_anchors.json").write_text(json.dumps(
            {"order": [{"obj_id": "ok"}, {"obj_id": "kill"}, {"obj_id": "unt"}]}))
        P.rewrite_anchors(run, v)
        an = json.loads((run / "phase1" / "classical_anchors.json").read_text())
        check("property_check: KILL pruned from order, kept in killed_by_test",
              [o["obj_id"] for o in an["order"]] == ["ok", "unt"] and an["killed_by_test"] == ["kill"])

        import classical_check as C  # noqa: E402
        cd = run / "phase1" / "classical"
        cd.mkdir()
        cd.joinpath("recall.json").write_text(json.dumps({"candidates": [
            {"obj_id": "a", "tier": "priority"}, {"obj_id": "b", "tier": "priority"},
            {"obj_id": "c", "tier": "priority"}, {"obj_id": "d", "tier": "not_fit"}]}))
        full = {"anchor": {"authors": "Ng, Harada, Russell", "year": 1999, "venue": "ICML", "url": "u", "read_location": "Thm 1"},
                "construction": "x", "property": "y", "conditions": ["z"], "mismatch": ["m"], "entry": "e",
                "cost": {"params": "0", "compute": "0", "data": "0", "storage": "0"}, "refuted_by": "r", "status": "modeled"}
        md = "[原理论] ... [迁移推导] ..."
        cd.joinpath("a.json").write_text(json.dumps(full)); cd.joinpath("a.md").write_text(md)
        cd.joinpath("b.json").write_text(json.dumps({**full, "status": "lead"})); cd.joinpath("b.md").write_text(md)
        cd.joinpath("c.json").write_text(json.dumps({**full, "mismatch": []})); cd.joinpath("c.md").write_text(md)
        r = C.check(run)
        check("classical_check: complete -> modeled", r["a"]["status"] == "modeled")
        check("classical_check: abstract-only -> lead", r["b"]["status"] == "lead")
        check("classical_check: no mismatch -> incomplete", r["c"]["status"] == "incomplete" and "mismatch" in r["c"]["missing"])
        check("classical_check: non-priority ignored", "d" not in r)
    import os, subprocess  # noqa: E401,E402
    probe = ("import sys; sys.path.insert(0, '.'); import scripts.run as r; "
             "print(sorted(c[0] for c in r.CONNECTORS), sorted(r._resolve_pool_caps()))")
    rsd = N.ROOT / "skills" / "idea-spark"
    for dom, want in (("ml", "['arxiv', 'local', 'openreview']"), ("general", "['arxiv', 'openreview']")):
        out = subprocess.run([sys.executable, "-c", probe], cwd=rsd, capture_output=True, text=True,
                             env={**os.environ, "OPEN_SCIENTIST_DOMAIN": dom}).stdout
        check(f"domain {dom}: connectors {want}", out.startswith(want))
    bad = subprocess.run([sys.executable, "-c", probe], cwd=rsd, capture_output=True, text=True,
                         env={**os.environ, "OPEN_SCIENTIST_DOMAIN": "bio"})
    check("domain switch rejects unknown value", bad.returncode != 0)
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
