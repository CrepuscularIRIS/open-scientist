#!/usr/bin/env python3
"""Open Scientist 0.7 navigator: ResearchStudio idea_spark (upstream #63 quality flow) is the backbone;
layers of three kinds are inserted around it — constrain (fixes what RS works on), verify (kills / admits),
rank (orders what survived) — plus the classical-modeling layer, the solution-side core.

It runs the bundled RS navigator (`skills/idea-spark/scripts/run.py next`), reads the step RS wants next plus the
run's artifacts, and emits a layer step when one is due; otherwise it passes the RS step through, adding the
layer outputs (and the overlay prompts in `overlays/`) as extra inputs where RS should read them.

  RS step "Phase 1 — bottleneck identification",   no phase0/mainline_first.json        -> mainline        (rank)
  Phase 1 proceed, Phase 2 not materialised,       no phase1/.gap_filter_done           -> soundness-gate  (verify, gap)
  same,                                            no phase1/admission.json             -> admission       (verify, measured)
  same,                                            no phase1/classical_anchors.json     -> classical-recall (model)
  RS step "Run existing dual-channel collision",   no soundness_early.json              -> soundness-gate  (verify, mechanism; before Phase 3)
  RS step "Build the technical skeleton ...",      no <project>/.open-scientist/protocol_audit.json -> soundness-gate (verify, protocol; once per project)
  same,                                            no soundness_cards.json              -> soundness-gate  (verify, card)
  same,                                            no selection.json                    -> problem-selection (rank)
  soundness_early.json / soundness_cards.json says KILL                                 -> terminal: new run
Overlays (constrain): overlays/phase1.md on RS Phase 1, overlays/generation.md on RS 2.1+2.2.
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
LBL_COLLISION = "Run existing dual-channel collision retrieval"  # first collision = right after the coherence gate
RS_LABELS = (LBL_PHASE1, LBL_PREPARE, LBL_SKELETON, LBL_COLLISION, "'generation'")


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


CANDIDATES = ("phase3_revise/final_candidate.json", "phase2_coherence/refined_candidate.json",
              "phase2_coherence/repaired_candidate.json", "phase2_generate/phase2_generate_output.json")

LAYERS = [  # checked in order; the first due layer is emitted. kind: rank | verify | model
    {"name": "mainline", "skill": "mainline", "kind": "rank",
     "due": lambda run, step, proj: LBL_PHASE1 in step and not (run / "phase0" / "mainline_first.json").exists(),
     "title": "Open Scientist layer — mainline-first formulation (blind first pass + crux validation) BEFORE Phase 1",
     "inputs": lambda run, proj: [run / "phase0" / "user_query.txt", run / "phase0" / "lit_table.md",
                                  *proj_files(proj, "mainline.md", "facts.md", "code_map.md")],
     "outputs": lambda run: [run / "phase0" / "mainline_first.json"],
     "marker": lambda run, proj: run / "phase0" / "mainline_first.json"},
    {"name": "gaps", "skill": "soundness-gate", "kind": "verify",
     "due": lambda run, step, proj: before_phase2(run) and not (run / "phase1" / ".gap_filter_done").exists(),
     "title": "Open Scientist layer — soundness gate, GAP level (verifier: code + literature only) BEFORE Phase 2",
     "inputs": lambda run, proj: [run / "phase1" / "phase1_output.json", run / "phase0" / "mainline_first.json",
                                  *proj_files(proj, "code_map.md")],
     "outputs": lambda run: [run / "phase1" / "phase1_output.json (kept gaps only, mainline first; original kept as *_unfiltered)",
                             run / "phase1" / "soundness_gaps.json", run / "phase1" / ".gap_filter_done"],
     "marker": lambda run, proj: run / "phase1" / ".gap_filter_done"},
    {"name": "admit", "skill": "soundness-gate", "kind": "verify",
     "due": lambda run, step, proj: before_phase2(run) and not (run / "phase1" / "admission.json").exists(),
     "title": "Open Scientist layer — phenomenon admission (host measures the phenomenon on this machine, or cites the facts.md row) BEFORE Phase 2",
     "inputs": lambda run, proj: [run / "phase1" / "soundness_gaps.json", *proj_files(proj, "facts.md")],
     "outputs": lambda run: [run / "phase1" / "admission.json"],
     "marker": lambda run, proj: run / "phase1" / "admission.json"},
    {"name": "classical", "skill": "classical-recall", "kind": "model",
     "due": lambda run, step, proj: before_phase2(run) and not (run / "phase1" / "classical_anchors.json").exists(),
     "title": "Open Scientist layer — classical recall + modeling (Q1–Q8: original problem → construction → property → mapping) BEFORE Phase 2",
     "inputs": lambda run, proj: [run / "phase1" / "soundness_gaps.json", run / "phase1" / "admission.json",
                                  run / "phase0" / "mainline_first.json", run / "phase0" / "user_query.txt",
                                  ROOT / "skills" / "classical-recall" / "references" / "modeling-standard.md",
                                  *proj_files(proj, "code_map.md")],
     "outputs": lambda run: [run / "phase1" / "classical" / "recall.json", run / "phase1" / "classical" / "<obj_id>.md + <obj_id>.json",
                             run / "phase1" / "classical_anchors.json"],
     "marker": lambda run, proj: run / "phase1" / "classical_anchors.json"},
    {"name": "early", "skill": "soundness-gate", "kind": "verify",
     "due": lambda run, step, proj: LBL_COLLISION in step and not (run / "soundness_early.json").exists(),
     "title": "Open Scientist layer — soundness gate, MECHANISM level (S1 / S2 / S7 only; a KILL here skips Phase 3) BEFORE collision",
     "inputs": lambda run, proj: [*(run / c for c in CANDIDATES), run / "phase1" / "classical_anchors.json",
                                  run / "phase0" / "mainline_first.json", *proj_files(proj, "code_map.md")],
     "outputs": lambda run: [run / "soundness_early.json"],
     "marker": lambda run, proj: run / "soundness_early.json"},
    {"name": "protocol", "skill": "soundness-gate", "kind": "verify",
     "due": lambda run, step, proj: LBL_SKELETON in step and not (proj / ".open-scientist" / "protocol_audit.json").exists(),
     "title": "Open Scientist layer — soundness gate, PROTOCOL level (the project's evaluation tools; once per project, redo when a tool changes) BEFORE Phase 4",
     "inputs": lambda run, proj: [*proj_files(proj, "code_map.md", "mainline.md")],
     "outputs": lambda run: [Path("<project>/.open-scientist/protocol_audit.json")],
     "marker": lambda run, proj: proj / ".open-scientist" / "protocol_audit.json"},
    {"name": "cards", "skill": "soundness-gate", "kind": "verify",
     "due": lambda run, step, proj: LBL_SKELETON in step and not (run / "soundness_cards.json").exists(),
     "title": "Open Scientist layer — soundness gate, CARD level S1–S7 (kill before training) BEFORE Phase 4",
     "inputs": lambda run, proj: [*(run / c for c in CANDIDATES), run / "phase3_collision" / "collision_hits.json",
                                  run / "phase1" / "classical_anchors.json", run / "phase0" / "mainline_first.json",
                                  *proj_files(proj, "code_map.md", "cards.json", "protocol_audit.json")],
     "outputs": lambda run: [run / "soundness_cards.json", Path("<project>/.open-scientist/cards.json (append)")],
     "marker": lambda run, proj: run / "soundness_cards.json"},
    {"name": "select", "skill": "problem-selection", "kind": "rank",
     "due": lambda run, step, proj: LBL_SKELETON in step and not (run / "selection.json").exists(),
     "title": "Open Scientist layer — problem selection over admitted cards (step-H axes, on the mainline) BEFORE Phase 4",
     "inputs": lambda run, proj: [run / "soundness_cards.json", run / "phase1" / "classical_anchors.json",
                                  *proj_files(proj, "cards.json", "mainline.md")],
     "outputs": lambda run: [run / "selection.zh.md", run / "selection.json"],
     "marker": lambda run, proj: run / "selection.json"},
]

EXTRA = [  # (condition on the RS step, extra inputs) — layer outputs + overlay prompts the RS sub-agent must also read
    (lambda step: LBL_PHASE1 in step,
     lambda run: [run / "phase0" / "mainline_first.json", OVER / "phase1.md"]),
    (lambda step: "llm_subagent" in step and f"STEP   : {LBL_GENERATION}" in step,
     lambda run: [run / "phase0" / "mainline_first.json", run / "phase1" / "soundness_gaps.json",
                  run / "phase1" / "classical_anchors.json", OVER / "generation.md"]),
]


def rs_next(run: Path, query: str | None) -> tuple[int, str]:
    cmd = [sys.executable, str(RS), "next", "--dir", str(run)] + (["--query", query] if query else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def rs_block(text: str) -> str:
    """The STEP/TYPE lines of the RS emit (for label matching)."""
    return "\n".join(l for l in text.splitlines() if l.startswith(("STATE", "STEP", "TYPE")))


KILL_FILES = ("soundness_early.json", "soundness_cards.json")


def killed(run: Path) -> Path | None:
    return next((run / f for f in KILL_FILES if _read(run / f).get("verdict") == "KILL"), None)


def decide(run: Path, step: str, proj: Path | None = None) -> dict | None:
    proj = proj or run.parent
    for L in LAYERS:
        if L["due"](run, step, proj):
            return L
    return None


def emit_layer(L: dict, run: Path, proj: Path, rs_text: str) -> str:
    ins = [str(p) for p in L["inputs"](run, proj) if Path(str(p).split(" ")[0]).exists()]
    return "\n".join([BAR, f"STATE  : RS is ready to continue, but this run has not passed the {L['skill']} layer.",
                      f"STEP   : {L['title']}", "TYPE   : open_scientist_layer", f"KIND   : {L['kind']}",
                      f"SKILL  : {L['skill']}  (read skills/{L['skill']}/SKILL.md and follow it)",
                      "INPUT  : " + ("\n         ".join(ins) if ins else "(none found — the skill says what to do without them)"),
                      "OUTPUT : " + "\n         ".join(str(p) for p in L["outputs"](run)),
                      f"DONE   : when {L['marker'](run, proj)} exists",
                      f"THEN   : python3 \"{Path(__file__).resolve()}\" --dir \"{run}\" --project \"{proj}\"",
                      "RS NEXT (held until the layer is done):", rs_text.strip()[:1500], BAR])


def emit_killed(kf: Path) -> str:
    sc = _read(kf)
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
    kf = killed(run)
    if kf:
        print(emit_killed(kf))
        return 0
    rc, text = rs_next(run, a.query)
    if rc != 0:
        print(text)
        return rc
    step = rs_block(text)
    for L in LAYERS:
        if L["name"] not in a.skip and L["due"](run, step, proj):
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
