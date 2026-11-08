#!/usr/bin/env python3
"""Open Scientist 0.6 navigator: ResearchStudio idea_spark (upstream #63 quality flow) is the backbone;
mainline-first + soundness layers are inserted around it.

It runs the bundled RS navigator (`skills/idea-spark/scripts/run.py next`), reads the step RS wants next plus the
run's artifacts, and emits a layer step when one is due; otherwise it passes the RS step through, adding the
layer outputs (and the overlay prompts in `overlays/`) as extra inputs where RS should read them.

  RS step "Phase 1 — bottleneck identification"           and phase0/mainline_first.json missing  -> mainline
  Phase 1 state=proceed, Phase 2 slice not materialised   and phase1/.gap_filter_done missing     -> soundness-gate (gap)
  same                                                     and phase1/solution_lens.json missing   -> innovation-lens (solution side)
  RS step "Build the technical skeleton ..."              and soundness_cards.json missing        -> soundness-gate (card)
  same                                                     and selection.json missing              -> problem-selection
  soundness_cards.json says the card was KILLed                                                    -> terminal: new run
State-free and idempotent: completion = the marker file. Every RS label used here is asserted to exist in the
RS source by scripts/selftest_os_next.py, so an upstream rename fails loudly instead of skipping a layer.

Usage: python3 scripts/os_next.py --dir <run_dir> [--query "..."] [--project <project root>]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RS = ROOT / "skills" / "idea-spark" / "scripts" / "run.py"
OVER = ROOT / "overlays"
BAR = "━" * 72

# RS labels this navigator depends on (checked against the RS source by the selftest).
LBL_PHASE1 = "Phase 1 — bottleneck identification"
LBL_PREPARE = "Materialise the slim Phase 2 input slice"
LBL_GENERATION = "generation"          # stage name of the selection + generation sub-agent
LBL_SKELETON = "Build the technical skeleton"
RS_LABELS = (LBL_PHASE1, LBL_PREPARE, LBL_SKELETON, "'generation'")


def _read(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def phase1_proceed(run: Path) -> bool:
    return _read(run / "phase1" / "phase1_output.json").get("state") == "proceed"


def before_phase2(run: Path) -> bool:
    """Phase 1 done, nothing of Phase 2 materialised yet (the gap list may still be rewritten)."""
    return phase1_proceed(run) and not (run / "phase2_generate" / "closest_abstracts.json").exists() \
        and not (run / ".quality" / "generation").exists()


def proj_files(proj: Path, *names: str) -> list[Path]:
    return [proj / ".open-scientist" / n for n in names]


LAYERS = [  # checked in order; the first due layer is emitted
    {"name": "mainline", "skill": "mainline",
     "due": lambda run, step: LBL_PHASE1 in step and not (run / "phase0" / "mainline_first.json").exists(),
     "title": "Open Scientist layer — mainline-first formulation (blind first pass + crux validation) BEFORE Phase 1",
     "inputs": lambda run, proj: [run / "phase0" / "user_query.txt", run / "phase0" / "lit_table.md",
                                  *proj_files(proj, "mainline.md", "facts.md", "code_map.md")],
     "outputs": lambda run: [run / "phase0" / "mainline_first.json"],
     "marker": lambda run: run / "phase0" / "mainline_first.json"},
    {"name": "gaps", "skill": "soundness-gate",
     "due": lambda run, step: before_phase2(run) and not (run / "phase1" / ".gap_filter_done").exists(),
     "title": "Open Scientist layer — soundness gate, GAP level (verifier: code + literature only) + phenomenon admission BEFORE Phase 2",
     "inputs": lambda run, proj: [run / "phase1" / "phase1_output.json", run / "phase0" / "mainline_first.json",
                                  *proj_files(proj, "code_map.md", "facts.md")],
     "outputs": lambda run: [run / "phase1" / "phase1_output.json (kept gaps only, mainline first; original kept as *_unfiltered)",
                             run / "phase1" / "soundness_gaps.json", run / "phase1" / ".gap_filter_done"],
     "marker": lambda run: run / "phase1" / ".gap_filter_done"},
    {"name": "lens", "skill": "innovation-lens",
     "due": lambda run, step: before_phase2(run) and not (run / "phase1" / "solution_lens.json").exists(),
     "title": "Open Scientist layer — solution lens (15 innovation types rank SOLUTION angles per admitted bottleneck) BEFORE Phase 2",
     "inputs": lambda run, proj: [run / "phase1" / "soundness_gaps.json", run / "phase0" / "mainline_first.json",
                                  run / "phase0" / "lit_table.md", *proj_files(proj, "code_map.md")],
     "outputs": lambda run: [run / "phase1" / "solution_lens.zh.md", run / "phase1" / "solution_lens.json"],
     "marker": lambda run: run / "phase1" / "solution_lens.json"},
    {"name": "cards", "skill": "soundness-gate",
     "due": lambda run, step: LBL_SKELETON in step and not (run / "soundness_cards.json").exists(),
     "title": "Open Scientist layer — soundness gate, CARD level (kill before training) BEFORE Phase 4",
     "inputs": lambda run, proj: [run / "phase3_revise" / "final_candidate.json", run / "phase2_coherence" / "refined_candidate.json",
                                  run / "phase2_coherence" / "repaired_candidate.json", run / "phase2_generate" / "phase2_generate_output.json",
                                  run / "phase3_collision" / "collision_hits.json", run / "phase0" / "mainline_first.json",
                                  *proj_files(proj, "code_map.md", "cards.json")],
     "outputs": lambda run: [run / "soundness_cards.json", Path("<project>/.open-scientist/cards.json (append)")],
     "marker": lambda run: run / "soundness_cards.json"},
    {"name": "select", "skill": "problem-selection",
     "due": lambda run, step: LBL_SKELETON in step and not (run / "selection.json").exists(),
     "title": "Open Scientist layer — problem selection over admitted cards (likelihood × impact on the mainline) BEFORE Phase 4",
     "inputs": lambda run, proj: [run / "soundness_cards.json", *proj_files(proj, "cards.json", "mainline.md")],
     "outputs": lambda run: [run / "selection.zh.md", run / "selection.json"],
     "marker": lambda run: run / "selection.json"},
]

EXTRA = [  # (condition on the RS step, extra inputs) — layer outputs + overlay prompts the RS sub-agent must also read
    (lambda step: LBL_PHASE1 in step,
     lambda run: [run / "phase0" / "mainline_first.json", OVER / "phase1.md"]),
    (lambda step: "llm_subagent" in step and f"STEP   : {LBL_GENERATION}" in step,
     lambda run: [run / "phase0" / "mainline_first.json", run / "phase1" / "soundness_gaps.json",
                  run / "phase1" / "solution_lens.json", OVER / "generation.md"]),
]


def rs_next(run: Path, query: str | None) -> tuple[int, str]:
    cmd = [sys.executable, str(RS), "next", "--dir", str(run)] + (["--query", query] if query else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def rs_block(text: str) -> str:
    """The STEP/TYPE lines of the RS emit (for label matching)."""
    return "\n".join(l for l in text.splitlines() if l.startswith(("STATE", "STEP", "TYPE")))


def killed(run: Path) -> bool:
    return _read(run / "soundness_cards.json").get("verdict") == "KILL"


def decide(run: Path, step: str) -> dict | None:
    for L in LAYERS:
        if L["due"](run, step):
            return L
    return None


def emit_layer(L: dict, run: Path, proj: Path, rs_text: str) -> str:
    ins = [str(p) for p in L["inputs"](run, proj) if Path(str(p).split(" ")[0]).exists()]
    return "\n".join([BAR, f"STATE  : RS is ready to continue, but this run has not passed the {L['skill']} layer.",
                      f"STEP   : {L['title']}", "TYPE   : open_scientist_layer",
                      f"SKILL  : {L['skill']}  (read skills/{L['skill']}/SKILL.md and follow it)",
                      "INPUT  : " + ("\n         ".join(ins) if ins else "(none found — the skill says what to do without them)"),
                      "OUTPUT : " + "\n         ".join(str(p) for p in L["outputs"](run)),
                      f"DONE   : when {L['marker'](run)} exists",
                      f"THEN   : python3 \"{Path(__file__).resolve()}\" --dir \"{run}\" --project \"{proj}\"",
                      "RS NEXT (held until the layer is done):", rs_text.strip()[:1500], BAR])


def emit_killed(run: Path) -> str:
    sc = _read(run / "soundness_cards.json")
    return "\n".join([BAR, "STATE  : CARD_KILLED", "STEP   : The soundness verifier killed this run's card — do not write the card, do not train",
                      "TYPE   : terminal",
                      "NOTES  : " + "; ".join(sc.get("kill_reasons", []))[:800],
                      "THEN   : start a NEW run directory on the same target bottleneck; put the kill reasons in the query as "
                      "negative constraints (RS's cross-run dedup also treats this run's candidate as a soft negative anchor). "
                      "After 2 killed runs on one bottleneck, return to the mainline layer.", BAR])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--query", default=None)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--skip", nargs="*", default=[], choices=[L["name"] for L in LAYERS], help="layers to skip for this call")
    a = ap.parse_args()
    run, proj = a.dir.resolve(), a.project.resolve()
    if killed(run):
        print(emit_killed(run))
        return 0
    rc, text = rs_next(run, a.query)
    if rc != 0:
        print(text)
        return rc
    step = rs_block(text)
    for L in LAYERS:
        if L["name"] not in a.skip and L["due"](run, step):
            print(emit_layer(L, run, proj, text))
            return 0
    print(text.rstrip())
    extra = next((f(run) for cond, f in EXTRA if cond(step)), [])
    extra = [str(p) for p in extra if p.exists()]
    if extra:
        print("OPEN-SCIENTIST: also pass these to the sub-agent (layer outputs + overlay instructions; the overlay overrides the RS prompt where they conflict):")
        for p in extra:
            print(f"         {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
