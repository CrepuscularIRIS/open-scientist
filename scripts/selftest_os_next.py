#!/usr/bin/env python3
"""Self-test of os_next.py (Open Scientist 0.9). No arguments, no network.

1. Label guard: every RS label os_next keys on still exists in the bundled RS source (an upstream rename must
   fail here, not silently skip a layer).
2. Trigger logic on synthetic run dirs: mainline -> gap gate -> admission -> classical -> pass-through to Phase 2 ->
   mechanism gate (before collision) -> protocol audit -> card gate -> selection -> pass-through;
   a KILL at either verifier stop -> terminal; overlays + extra inputs attached.
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
        (run / "phase1" / "admission.json").write_text("{}")
        check("admission done -> classical", name(prep_step) == "classical")
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
        extra = next((f(run) for c, f in N.EXTRA if c(gen_step)), [])
        check("generation gets overlay + gate + anchors", N.OVER / "generation.md" in extra
              and run / "phase1" / "soundness_gaps.json" in extra and run / "phase1" / "classical_anchors.json" in extra)
        extra1 = next((f(run) for c, f in N.EXTRA if c(p1_step)), [])
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
        for L in N.LAYERS:
            check(f"layer {L['name']} has a kind", L.get("kind") in ("rank", "verify", "model"))

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
