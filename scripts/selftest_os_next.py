#!/usr/bin/env python3
"""Self-test of os_next.py (Open Scientist 0.6). No arguments, no network.

1. Label guard: every RS label os_next keys on still exists in the bundled RS source (an upstream rename must
   fail here, not silently skip a layer).
2. Trigger logic on synthetic run dirs: mainline -> gap gate -> solution lens -> pass-through to Phase 2 ->
   card gate -> selection -> pass-through; a KILLed card -> terminal; overlays + extra inputs attached.
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
    name = lambda run, step: (N.decide(run, step) or {}).get("name")
    with tempfile.TemporaryDirectory() as td:
        run = Path(td) / "run"
        (run / "phase0").mkdir(parents=True)
        check("Phase 1 -> mainline layer", name(run, p1_step) == "mainline")
        (run / "phase0" / "mainline_first.json").write_text("{}")
        check("mainline done -> RS Phase 1", name(run, p1_step) is None)
        (run / "phase1").mkdir()
        (run / "phase1" / "phase1_output.json").write_text(json.dumps({"state": "proceed"}))
        check("Phase 1 proceed -> gap gate", name(run, prep_step) == "gaps")
        (run / "phase1" / ".gap_filter_done").write_text("")
        check("gap gate done -> solution lens", name(run, prep_step) == "lens")
        (run / "phase1" / "solution_lens.json").write_text("{}")
        check("lens done -> RS PREPARE", name(run, prep_step) is None)
        (run / "phase2_generate").mkdir()
        (run / "phase2_generate" / "closest_abstracts.json").write_text("{}")
        (run / "phase1" / "solution_lens.json").unlink()
        check("Phase 2 started -> lens no longer due", name(run, gen_step) is None)
        (run / "phase1" / "solution_lens.json").write_text("{}")
        extra = next((f(run) for c, f in N.EXTRA if c(gen_step)), [])
        check("generation gets overlay + gate + lens", N.OVER / "generation.md" in extra and run / "phase1" / "soundness_gaps.json" in extra)
        extra1 = next((f(run) for c, f in N.EXTRA if c(p1_step)), [])
        check("Phase 1 gets overlay + mainline", N.OVER / "phase1.md" in extra1)
        check("skeleton -> card gate", name(run, skel_step) == "cards")
        (run / "soundness_cards.json").write_text(json.dumps({"verdict": "CHECK"}))
        check("card gate done -> selection", name(run, skel_step) == "select")
        (run / "selection.json").write_text("{}")
        check("selection done -> RS skeleton", name(run, skel_step) is None)
        check("CHECK card not treated as killed", not N.killed(run))
        (run / "soundness_cards.json").write_text(json.dumps({"verdict": "KILL", "kill_reasons": ["x"]}))
        check("KILL card -> terminal", N.killed(run) and "CARD_KILLED" in N.emit_killed(run))
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
