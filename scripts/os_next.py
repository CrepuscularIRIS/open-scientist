#!/usr/bin/env python3
"""Open Scientist 0.4 navigator: ResearchStudio idea_spark is the backbone; selection layers are inserted around it.

It runs the bundled RS navigator (`skills/idea-spark/scripts/run.py next`) and looks at the step RS wants next. When
RS is about to start a phase whose selection layer has not been completed for this run, it emits the layer step
instead; otherwise it passes the RS step through, adding the layer outputs as extra inputs where RS should read them.

  RS wants "Phase 1 — bottleneck identification"  and phase0/innovation_lens.json is missing -> innovation-lens
  RS wants "Phase 2.1 + 2.2"                     and phase1/.gap_filter_done is missing    -> gap-code-filter
  RS wants "Phase 4 skeleton"                    and selection.json is missing             -> problem-selection
  (state-free, idempotent: completion = the marker file; re-run any time)

Usage: python3 scripts/os_next.py --dir <run_dir> [--query "..."] [--project <project root>]
Exit 0 always for a valid emit; non-zero only when RS itself fails.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RS = ROOT / "skills" / "idea-spark" / "scripts" / "run.py"
BAR = "━" * 72

LAYERS = {
    "lens": {
        "trigger": "Phase 1 — bottleneck identification",
        "marker": lambda run: run / "phase0" / "innovation_lens.json",
        "skill": "innovation-lens",
        "title": "Open Scientist layer — innovation lens (15 innovation types A–O, ranked) BEFORE Phase 1",
        "inputs": lambda run, proj: [run / "phase0" / "user_query.txt", run / "phase0" / "lit_table.md",
                                      proj / ".open-scientist" / "mainline.md", proj / ".open-scientist" / "facts.md"],
        "outputs": lambda run: [run / "phase0" / "innovation_lens.zh.md", run / "phase0" / "innovation_lens.json"],
    },
    "filter": {
        "trigger": "Phase 2.1 + 2.2",
        "marker": lambda run: run / "phase1" / ".gap_filter_done",
        "skill": "gap-code-filter",
        "title": "Open Scientist layer — gap code filter + design layer BEFORE Phase 2",
        "inputs": lambda run, proj: [run / "phase1" / "phase1_output.json", run / "phase0" / "innovation_lens.json",
                                      proj / ".open-scientist" / "code_map.md", proj / ".open-scientist" / "facts.md"],
        "outputs": lambda run: [run / "phase1" / "phase1_output.json (gap list rewritten; original kept as *_unfiltered)",
                                run / "phase1" / "ASSUMPTIONS.zh.md", run / "phase1" / ".gap_filter_done"],
    },
    "select": {
        "trigger": "Phase 4 skeleton",
        "marker": lambda run: run / "selection.json",
        "skill": "problem-selection",
        "title": "Open Scientist layer — problem selection (risk table, likelihood × impact, go / no-go) BEFORE Phase 4",
        "inputs": lambda run, proj: [run / "phase3_revise" / "final_candidate.json", run / "phase2_coherence" / "refined_candidate.json",
                                      run / "phase2_generate" / "phase2_generate_output.json", run / "phase3_critique" / "phase3_critique_output.json",
                                      proj / ".open-scientist" / "mainline.md"],
        "outputs": lambda run: [run / "selection.zh.md", run / "selection.json"],
    },
}
EXTRA_INPUTS = {  # RS steps that must also read a layer output
    "Phase 1 — bottleneck identification": lambda run: [run / "phase0" / "innovation_lens.json"],
    "Phase 2.1 + 2.2": lambda run: [run / "phase0" / "innovation_lens.json", run / "phase1" / "ASSUMPTIONS.zh.md"],
}


def rs_next(run: Path, query: str | None) -> tuple[int, str]:
    cmd = [sys.executable, str(RS), "next", "--dir", str(run)] + (["--query", query] if query else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def rs_step(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("STEP"):
            return line.split(":", 1)[1].strip()
    return ""


def emit_layer(name: str, run: Path, proj: Path, rs_text: str) -> str:
    L = LAYERS[name]
    ins = [str(p) for p in L["inputs"](run, proj) if Path(str(p).split(" ")[0]).exists()]
    outs = [str(p) for p in L["outputs"](run)]
    return "\n".join([BAR, f"STATE  : RS is ready for '{L['trigger']}', but this run has not passed the {L['skill']} layer.",
                      f"STEP   : {L['title']}", "TYPE   : open_scientist_layer",
                      f"SKILL  : {L['skill']}  (read skills/{L['skill']}/SKILL.md and follow it)",
                      "INPUT  : " + ("\n         ".join(ins) if ins else "(none found — the skill says what to do without them)"),
                      "OUTPUT : " + "\n         ".join(outs),
                      f"DONE   : when {L['marker'](run)} exists",
                      f"THEN   : python3 \"{Path(__file__).resolve()}\" --dir \"{run}\" --project \"{proj}\"",
                      "RS NEXT (held until the layer is done):", rs_text.strip()[:1500], BAR])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--query", default=None)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--skip", nargs="*", default=[], choices=list(LAYERS), help="layers to skip for this call")
    a = ap.parse_args()
    run, proj = a.dir.resolve(), a.project.resolve()
    rc, text = rs_next(run, a.query)
    if rc != 0:
        print(text)
        return rc
    step = rs_step(text)
    for name, L in LAYERS.items():
        if name in a.skip or L["trigger"] not in step:
            continue
        if not L["marker"](run).exists():
            print(emit_layer(name, run, proj, text))
            return 0
    extra = next((f(run) for k, f in EXTRA_INPUTS.items() if k in step), [])
    extra = [str(p) for p in extra if p.exists()]
    print(text.rstrip())
    if extra:
        print("OPEN-SCIENTIST: also pass these layer outputs to the sub-agent (ranking / design priority, not a substitute for the RS prompt):")
        for p in extra:
            print(f"         {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
