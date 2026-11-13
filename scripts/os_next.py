#!/usr/bin/env python3
"""Open Scientist 0.10 navigator: ResearchStudio idea_spark (upstream #63 quality flow) is the backbone;
layers of three kinds are inserted around it — constrain (fixes what RS works on), verify (kills / admits),
rank (orders what survived) — plus the classical-modeling layer, the solution-side core.

It runs the bundled RS navigator (`skills/idea-spark/scripts/run.py next`), reads the step RS wants next plus the
run's artifacts, and emits a layer step when one is due; otherwise it passes the RS step through, adding the
layer outputs (and the overlay prompts in `overlays/`) as extra inputs where RS should read them.

  RS step "Phase 1 — bottleneck identification",   no phase0/mainline_first.json        -> mainline        (rank)
  same,                                            no phase0/causal_order.json          -> causal-order    (verify; Sol, paper+code anchored)
  Phase 1 proceed, Phase 2 not materialised,       no phase1/.gap_filter_done           -> soundness-gate  (verify, gap)
  same,                                            no phase1/admission.json             -> admission       (verify, measured)
  admission.json lists a gap that is not "measured"                                     -> terminal: ADMISSION_PENDING
  same,                                            no phase1/prior_sweep.json           -> prior-sweep     (measure: run the
                                                   existing official / community switches + one upper-bound arm)
  prior_sweep.json decision SOLVED_BY_SWITCH / IMMOVABLE                                -> terminal: no method design
  same,                                            no phase1/classical_anchors.json     -> classical-recall (model)
  same, domain ml,                                 no phase1/.property_tests_done       -> property-test   (verify, quick script)
  RS step "Run existing dual-channel collision",   no soundness_early.json              -> soundness-gate  (verify, mechanism; before Phase 3)
  RS step "Build the technical skeleton ...",      protocol_audit.json missing or a tool's sha256 changed -> soundness-gate (verify, protocol)
  same,                                            no soundness_cards.json              -> soundness-gate  (verify, card)
  same,                                            no selection.json                    -> problem-selection (rank)
  soundness_early.json / soundness_cards.json says KILL                                 -> terminal: new run
  >= 2 cards of this run KILL/FAIL in <project>/.open-scientist/cards.json (any source: RS, mature-method slot,
  host-written; trained FAILs count), no structural_audit.json covering them            -> terminal: STRUCTURAL_AUDIT
  structural_audit.json decision GOAL_MISSET / STRUCTURAL                              -> terminal: run closed, back to mainline
  a trained FAIL of this run without an `attribution` in cards.json                     -> ATTRIBUTION_DUE (skills/attribution);
  only GAP / METHOD attributions count as failed cards, one GAP triggers the audit at once; cards with
  role baseline / upper_bound never count.
Order of work (0.10): measure -> existing switches -> upper bound -> design on the residual -> pre-review -> code
review -> run -> attribution.
Overlays (constrain): overlays/phase1.md on RS Phase 1, overlays/generation.md on RS 2.1+2.2.
State-free and idempotent: completion = the marker file. Every RS label used here is asserted to exist in the
RS source by scripts/selftest_os_next.py, so an upstream rename fails loudly instead of skipping a layer.

Usage: python3 scripts/os_next.py --dir <run_dir> [--query "..."] [--project <project root>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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


# Said at every stop where a line ends: the usual drift is to re-scope the paper around the failures.
FIXED = ("The deliverable type is fixed by the project (see its constitution): a line that ends is reported to the user "
         "and the next line is taken — never re-scope the paper into an analysis / audit of what failed. Move this "
         "line's failed-method files (run dir, PREREG / RESULT, drafts) out of the project into its archive directory; "
         "keep only the measured rows in facts.md and one line per falsified premise.")
SLATE = ("TWO ARMS, ONE LINE: both GPUs work on THIS target with arms that differ in kind — (1) a sibling candidate: "
         "copy this run's phase0/, phase1/, context/ and run_contract.json into a new run dir (RS continues from there at "
         "Phase 2), add this run's name to its phase0/same_target_runs.txt, "
         "put this candidate there as phase0/sibling_candidate.json and rerun generation (overlay rule 9: next anchor / "
         "different intervention object and premise); or, if no second mechanism of a different kind is defensible, "
         "(2) this candidate's decisive control arm from its falsification plan; or (3) a switch / upper-bound arm of the "
         "prior sweep that has not been run. Never a second seed of the same arm, never another topic, never an idle GPU.")


def phase1_proceed(run: Path) -> bool:
    return _read(run / "phase1" / "phase1_output.json").get("state") == "proceed"


def before_phase2(run: Path) -> bool:
    """Phase 1 done, nothing of Phase 2 materialised yet (the gap list may still be rewritten)."""
    return phase1_proceed(run) and not (run / "phase2_generate" / "closest_abstracts.json").exists() \
        and not (run / ".quality" / "generation").exists()


DOMAIN = os.environ.get("OPEN_SCIENTIST_DOMAIN", "ml").strip().lower() or "ml"
# lite: problem side (mainline + causal) → RS Phase 0/1 → admission (measured) → prior sweep → ONE classical anchor
# → RS 2.1–2.3 (generation + coherence) → exit with a candidate for the card gate. Skips the gap verifier, property
# test, mechanism gate, RS Phase 3 and selection — in practice they rarely changed a decision. The prior sweep and
# the evaluator hash check are never skipped.
MODE = os.environ.get("OPEN_SCIENTIST_MODE", "full").strip().lower() or "full"
LITE_SKIP = {"gaps", "property", "early", "protocol", "cards", "select"}


def lite_exit(step: str) -> bool:
    """In lite mode the run ends where RS would start Phase 3 (first collision, right after the coherence gate)."""
    return MODE == "lite" and LBL_COLLISION in step


def protocol_stale(proj: Path) -> bool:
    """No audit yet, or an audited tool's file no longer matches its recorded sha256 (0.9: tools are hash-pinned)."""
    audit = _read(proj / ".open-scientist" / "protocol_audit.json")
    if not audit:
        return True
    for t in audit.get("tools", []):
        f = proj / str(t.get("path", "")).split(" ")[0]
        if not t.get("sha256") or not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != t["sha256"]:
            return True
    return False


def proj_files(proj: Path, *names: str) -> list[Path]:
    return [proj / ".open-scientist" / n for n in names]


def admission_pending(run: Path) -> list[str]:
    """Gaps this run wants to design for whose phenomenon is not measured yet (0.10: no design on a pending gap).
    `out_of_scope` = another branch's gap, listed for the record only; no card of this run may cite it."""
    f = run / "phase1" / "admission.json"
    if not f.exists():
        return []                      # the admission layer itself is still due; nothing to block yet
    gaps = _read(f).get("gaps")
    if not isinstance(gaps, list) or not gaps or not all(isinstance(g, dict) for g in gaps):
        return ["<admission.json malformed or empty: need {\"gaps\": [{\"id\", \"phenomenon\", \"evidence\", \"regime\"}]}>"]
    pend = [str(g.get("id", "?")) for g in gaps if g.get("phenomenon") not in ("measured", "out_of_scope")]
    if not pend and not any(g.get("phenomenon") == "measured" for g in gaps):
        return ["<no measured gap in admission.json>"]
    return pend


SWEEP_STOPS = ("SOLVED_BY_SWITCH", "IMMOVABLE")
SWEEP_DECISIONS = (*SWEEP_STOPS, "RESIDUAL")


def sweep_decision(run: Path) -> str | None:
    """Normalised decision of the prior sweep; None = not done (file missing, or a decision the navigator does not know)."""
    d = str(_read(run / "phase1" / "prior_sweep.json").get("decision") or "").strip().upper()
    return d if d in SWEEP_DECISIONS else None


def sweep_stop(run: Path) -> str | None:
    """The prior sweep ended the run: an existing switch already solves the TARGET, or nothing moves the criterion."""
    d = sweep_decision(run)
    return d if d in SWEEP_STOPS else None


CANDIDATES = ("phase3_revise/final_candidate.json", "phase2_coherence/refined_candidate.json",
              "phase2_coherence/repaired_candidate.json", "phase2_generate/phase2_generate_output.json")

LAYERS = [  # checked in order; the first due layer is emitted. kind: rank | verify | model
    {"name": "mainline", "skill": "mainline", "kind": "rank",
     "due": lambda run, step, proj: LBL_PHASE1 in step and not (run / "phase0" / "mainline_first.json").exists(),
     "title": "Open Scientist layer — mainline-first formulation (blind first pass + crux validation) BEFORE Phase 1",
     "inputs": lambda run, proj: [run / "phase0" / "user_query.txt", run / "phase0" / "lit_table.md",
                                  proj / ".open-scientist" / "paper_fulltext",
                                  *proj_files(proj, "mainline.md", "facts.md", "code_map.md")],
     "outputs": lambda run: [run / "phase0" / "mainline_first.json"],
     "marker": lambda run, proj: run / "phase0" / "mainline_first.json"},
    {"name": "causal", "skill": "mainline", "kind": "verify",
     "due": lambda run, step, proj: LBL_PHASE1 in step and not (run / "phase0" / "causal_order.json").exists(),
     "title": "Open Scientist layer — causal-ordering audit (round 3: isolated Sol, every candidate anchored to the "
              "baseline paper section AND code file:line) BEFORE Phase 1",
     "inputs": lambda run, proj: [run / "phase0" / "mainline_first.json", proj / ".open-scientist" / "paper_fulltext",
                                  *proj_files(proj, "facts.md", "code_map.md")],
     "outputs": lambda run: [run / "phase0" / "causal_order.json",
                             run / "phase0" / "mainline_first.json (final rewritten if REORDER / REJECT_MAINLINE)"],
     "marker": lambda run, proj: run / "phase0" / "causal_order.json"},
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
    {"name": "sweep", "skill": "prior-sweep", "kind": "measure",
     "due": lambda run, step, proj: before_phase2(run) and sweep_decision(run) is None,
     "title": "Open Scientist layer — prior sweep (run the existing official / community switches that touch this "
              "TARGET plus one upper-bound arm, in the regime where the criterion is judged) BEFORE any method design",
     "inputs": lambda run, proj: [run / "phase1" / "phase1_output.json", run / "phase1" / "admission.json",
                                  *proj_files(proj, "ecosystem_map.md", "deploy_contract.md", "facts.md", "code_map.md")],
     "outputs": lambda run: [run / "phase1" / "prior_sweep.json",
                             Path("<project>/.open-scientist/cards.json (one row per arm, role=baseline|upper_bound)")],
     "marker": lambda run, proj: Path(f"{run / 'phase1' / 'prior_sweep.json'} with decision "
                                      "SOLVED_BY_SWITCH | IMMOVABLE | RESIDUAL")},
    {"name": "classical", "skill": "classical-recall", "kind": "model",
     "due": lambda run, step, proj: before_phase2(run) and not (run / "phase1" / "classical_anchors.json").exists(),
     "title": "Open Scientist layer — classical recall + modeling (Q1–Q8: original problem → construction → property → mapping) BEFORE Phase 2",
     "inputs": lambda run, proj: [run / "phase1" / "soundness_gaps.json", run / "phase1" / "admission.json",
                                  run / "phase1" / "prior_sweep.json", proj / ".open-scientist" / "deploy_contract.md",
                                  run / "phase0" / "mainline_first.json", run / "phase0" / "user_query.txt",
                                  ROOT / "skills" / "classical-recall" / "references" / "modeling-standard.md",
                                  *proj_files(proj, "code_map.md")],
     "outputs": lambda run: [run / "phase1" / "classical" / "recall.json", run / "phase1" / "classical" / "<obj_id>.md + <obj_id>.json",
                             run / "phase1" / "classical_anchors.json"],
     "marker": lambda run, proj: run / "phase1" / "classical_anchors.json"},
    {"name": "property", "skill": "property-test", "kind": "verify",
     "due": lambda run, step, proj: DOMAIN == "ml" and before_phase2(run)
            and not (run / "phase1" / ".property_tests_done").exists(),
     "title": "Open Scientist layer — quick property check of classical anchors (one script per anchor on this "
              "project's code, frozen ckpt, no training; clear failure drops the anchor) BEFORE Phase 2",
     "inputs": lambda run, proj: [run / "phase1" / "classical_anchors.json", run / "phase1" / "classical",
                                  *proj_files(proj, "code_map.md")],
     "outputs": lambda run: [run / "phase1" / "property_tests" / "<obj_id>.py", run / "phase1" / "anchor_tests.json",
                             run / "phase1" / ".property_tests_done (written by scripts/property_check.py --write)"],
     "marker": lambda run, proj: run / "phase1" / ".property_tests_done"},
    {"name": "early", "skill": "soundness-gate", "kind": "verify",
     "due": lambda run, step, proj: LBL_COLLISION in step and not (run / "soundness_early.json").exists(),
     "title": "Open Scientist layer — soundness gate, MECHANISM level (S1 / S2 / S7 only; a KILL here skips Phase 3) BEFORE collision",
     "inputs": lambda run, proj: [*(run / c for c in CANDIDATES), run / "phase1" / "classical_anchors.json",
                                  run / "phase0" / "mainline_first.json", *proj_files(proj, "code_map.md")],
     "outputs": lambda run: [run / "soundness_early.json"],
     "marker": lambda run, proj: run / "soundness_early.json"},
    {"name": "protocol", "skill": "soundness-gate", "kind": "verify",
     "due": lambda run, step, proj: LBL_SKELETON in step and protocol_stale(proj),
     "title": "Open Scientist layer — soundness gate, PROTOCOL level (the project's evaluation tools; once per project, redo when a tool changes) BEFORE Phase 4",
     "inputs": lambda run, proj: [*proj_files(proj, "code_map.md", "mainline.md")],
     "outputs": lambda run: [Path("<project>/.open-scientist/protocol_audit.json")],
     "marker": lambda run, proj: proj / ".open-scientist" / "protocol_audit.json"},
    {"name": "cards", "skill": "soundness-gate", "kind": "verify",
     "due": lambda run, step, proj: LBL_SKELETON in step and not (run / "soundness_cards.json").exists(),
     "title": "Open Scientist layer — soundness gate, CARD level (deployment contract S0 + S1–S8; kill before training) BEFORE Phase 4",
     "inputs": lambda run, proj: [*(run / c for c in CANDIDATES), run / "phase3_collision" / "collision_hits.json",
                                  run / "phase1" / "classical_anchors.json", run / "phase0" / "mainline_first.json",
                                  run / "phase1" / "prior_sweep.json",
                                  *proj_files(proj, "code_map.md", "cards.json", "protocol_audit.json", "deploy_contract.md")],
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
     lambda run, proj: [run / "phase0" / "mainline_first.json", run / "phase0" / "causal_order.json", OVER / "phase1.md"]),
    (lambda step: "llm_subagent" in step and f"STEP   : {LBL_GENERATION}" in step,
     lambda run, proj: [run / "phase0" / "mainline_first.json", run / "phase1" / "soundness_gaps.json",
                        run / "phase1" / "prior_sweep.json", proj / ".open-scientist" / "deploy_contract.md",
                        run / "phase1" / "classical_anchors.json", run / "phase1" / "anchor_tests.json",
                        run / "phase0" / "sibling_candidate.json", OVER / "generation.md"]),
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


STRUCT_LIMIT = 2          # failures on one run before ideation stops and the structural audit runs
CLOSING = ("GOAL_MISSET", "STRUCTURAL")


COUNTED = ("GAP", "METHOD")                 # attributions that make a trained FAIL a failed card
NOT_METHOD_ROLES = ("baseline", "upper_bound")  # arms of the prior sweep / controls: never a failed card


def _up(card: dict, key: str) -> str:
    return str(card.get(key) or "").strip().upper()


def target_runs(run: Path) -> list[str]:
    """This run plus the earlier runs on the SAME TARGET (one name per line in phase0/same_target_runs.txt).
    The stop-loss counts per TARGET: a new run directory after a KILL must not reset the count."""
    try:
        prev = [l.strip().rstrip("/").split("/")[-1] for l in (run / "phase0" / "same_target_runs.txt").read_text().splitlines()]
    except OSError:
        prev = []
    return [run.name, *[n for n in prev if n and n != run.name]]


def own_cards(run: Path, proj: Path, only_this_run: bool = False) -> list[dict]:
    """Method cards of the project registry on this run's TARGET (baseline / upper-bound arms excluded)."""
    reg = _read(proj / ".open-scientist" / "cards.json")
    cards = reg.get("cards", []) if isinstance(reg, dict) else reg
    names = [run.name] if only_this_run else target_runs(run)
    own = re.compile(rf"(^|/)({'|'.join(re.escape(n) for n in names)})($|[/\s（(])")
    return [c for c in cards if isinstance(c, dict) and own.search(str(c.get("run", "")))
            and str(c.get("role") or "method").strip().lower() not in NOT_METHOD_ROLES] if isinstance(cards, list) else []


def attribution_due(run: Path, proj: Path) -> list[str]:
    """Trained FAILs of this run that nobody has attributed yet (gap vs method vs implementation vs evaluator)."""
    return [str(c.get("id", "?")) for c in own_cards(run, proj)
            if _up(c, "outcome").startswith("FAIL") and not _up(c, "attribution")]


def run_failures(run: Path, proj: Path) -> list[str]:
    """Ids of this run's failed cards: a verifier KILL, or a trained FAIL attributed to the gap or the method.
    A FAIL attributed to the evaluator, the implementation or a mechanism that never engaged is not a failed card."""
    def untrained_kill(c: dict) -> bool:
        return not _up(c, "outcome").startswith("FAIL") and (_up(c, "verdict").startswith("KILL")
                                                             or _up(c, "outcome").startswith("KILL"))
    out = []
    for c in own_cards(run, proj):
        if untrained_kill(c) or (_up(c, "outcome").startswith("FAIL") and _up(c, "attribution").startswith(COUNTED)):
            out.append(str(c.get("id", "?")))
    # A gate KILL of THIS run that nobody registered still counts once; a registered one is not counted twice.
    registered = sum(untrained_kill(c) for c in own_cards(run, proj, only_this_run=True))
    gate_kills = [lbl for f, lbl in (("soundness_early.json", "mechanism-gate"), ("soundness_cards.json", "card-gate"))
                  if _read(run / f).get("verdict") == "KILL"]
    return out + gate_kills[registered:]


def gap_attributed(run: Path, proj: Path) -> bool:
    return any(_up(c, "attribution").startswith("GAP") for c in own_cards(run, proj))


def structural_state(run: Path, proj: Path) -> tuple[str | None, list[str]]:
    """None = keep going; 'due' = audit needed; 'closed' = audit closed the run."""
    fails = run_failures(run, proj)
    audit = _read(run / "structural_audit.json")
    if audit.get("decision") in CLOSING:
        return "closed", fails
    enough = len(fails) >= STRUCT_LIMIT or (fails and gap_attributed(run, proj))  # one GAP attribution is enough
    if enough and len(fails) > int(audit.get("failures_at_audit", 0) or 0):
        return "due", fails   # NOT_STRUCTURAL buys exactly one more card, then re-audit
    return None, fails


def emit_structural(state: str, run: Path, fails: list[str]) -> str:
    if state == "closed":
        a = _read(run / "structural_audit.json")
        return "\n".join([BAR, f"STATE  : RUN_CLOSED ({a.get('decision')})", "TYPE   : terminal",
                          "NOTES  : " + str(a.get("summary", ""))[:800],
                          "THEN   : no more cards on this TARGET. Go back to the mainline layer (skills/mainline/SKILL.md "
                          "§结构审计) with the audit as NEW evidence; if the fix needs a fixed constraint released "
                          "(goal / observation contract / platform), ask the user first. " + FIXED, BAR])
    return "\n".join([BAR, "STATE  : STRUCTURAL_AUDIT", f"STEP   : {len(fails)} cards of this run failed ({', '.join(fails)}) — "
                      "stop ideation; do NOT draft, verify or train another card on this TARGET",
                      "TYPE   : open_scientist_layer", "KIND   : verify", "SKILL  : mainline  (section 结构审计)",
                      f"OUTPUT : {run / 'structural_audit.json'}  (decision GOAL_MISSET | STRUCTURAL | NOT_STRUCTURAL, "
                      f"failures_at_audit={len(fails)})",
                      f"THEN   : python3 \"{Path(__file__).resolve()}\" --dir \"{run}\" --project <project>", BAR])


def _then(run: Path) -> str:
    return f"python3 \"{Path(__file__).resolve()}\" --dir \"{run}\" --project <project>"


def emit_pending(run: Path, pend: list[str]) -> str:
    return "\n".join([BAR, "STATE  : ADMISSION_PENDING", f"STEP   : measure the phenomenon of {', '.join(pend)} on this "
                      "machine, in the regime where the criterion will be judged (same training length / checkpoint / "
                      "eval condition), BEFORE any method design", "TYPE   : open_scientist_layer", "KIND   : measure",
                      f"SKILL  : soundness-gate  (step 5b; read {ROOT / 'skills' / 'soundness-gate' / 'SKILL.md'})",
                      f"OUTPUT : {run / 'phase1' / 'admission.json'}  (phenomenon=measured + evidence + regime; a gap "
                      "whose phenomenon does not show up is removed from the file and recorded in facts.md)",
                      f"THEN   : {_then(run)}", BAR])


def emit_sweep_stop(run: Path, decision: str) -> str:
    sw = _read(run / "phase1" / "prior_sweep.json")
    note = {"SOLVED_BY_SWITCH": "an existing switch already reaches the criterion — do NOT generate a method on this "
                                "TARGET. Register the switch as the result (cards.json role=baseline, outcome filled; "
                                "facts.md). The next TARGET, if any, is what the switch still costs or leaves open "
                                "(`residual_gap`), as a new run.",
            "IMMOVABLE": "no arm, not even the upper-bound arm, moves the criterion in this regime — the gap or the "
                         "criterion is mis-set, not the methods. No method cards. Go back to the mainline layer with "
                         "this sweep as NEW evidence (skills/mainline/SKILL.md §结构审计: GOAL_MISSET)."}[decision]
    return "\n".join([BAR, f"STATE  : PRIOR_SWEEP_STOP ({decision})", "TYPE   : terminal",
                      "NOTES  : " + str(sw.get("summary") or sw.get("residual_gap") or "")[:800],
                      f"THEN   : {note} " + FIXED, BAR])


def emit_attribution(run: Path, ids: list[str]) -> str:
    return "\n".join([BAR, "STATE  : ATTRIBUTION_DUE", f"STEP   : {', '.join(ids)} failed after training and has no "
                      "attribution — decide whether the evaluator, the implementation, the gap or the method failed "
                      "BEFORE drafting, verifying or training another card", "TYPE   : open_scientist_layer",
                      "KIND   : verify", f"SKILL  : attribution  (read {ROOT / 'skills' / 'attribution' / 'SKILL.md'})",
                      f"OUTPUT : {run / 'attribution'}/<card id>.json + the `attribution` field of each card in "
                      "<project>/.open-scientist/cards.json  (EVALUATOR | IMPLEMENTATION | NOT_ENGAGED | GAP | METHOD)",
                      f"THEN   : {_then(run)}", BAR])


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
                      f"SKILL  : {L['skill']}  (read {ROOT / 'skills' / L['skill'] / 'SKILL.md'} and follow it)",
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
                      "THEN   : record the killed card in <project>/.open-scientist/cards.json (verdict KILL). Start a NEW run "
                      "directory on the same target bottleneck and write this run's name (plus the names already in this "
                      "run's phase0/same_target_runs.txt) into the new run's phase0/same_target_runs.txt — failures are "
                      "counted per TARGET, not per directory. Put the kill reasons in the query as "
                      "negative constraints (RS's cross-run dedup also treats this run's candidate as a soft negative anchor). "
                      "Before drafting the next card, check the kill reasons against phase0/causal_order.json: if they "
                      "point at a constraint upstream of the TARGET, run the structural audit now (skills/mainline/SKILL.md "
                      "§结构审计) instead of a new run. After 2 failed cards on one TARGET (KILL or trained FAIL, any "
                      "source) the audit is mandatory.", BAR])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--query", default=None)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--skip", nargs="*", default=[], choices=[L["name"] for L in LAYERS], help="layers to skip for this call")
    a = ap.parse_args()
    run, proj = a.dir.resolve(), a.project.resolve()
    st, fails = structural_state(run, proj)
    if st == "closed":
        print(emit_structural(st, run, fails))
        return 0
    unattributed = attribution_due(run, proj)
    if unattributed:
        print(emit_attribution(run, unattributed))
        return 0
    if st:
        print(emit_structural(st, run, fails))
        return 0
    stop = sweep_stop(run)
    if stop:
        print(emit_sweep_stop(run, stop))
        return 0
    kf = killed(run)
    if kf:
        print(emit_killed(kf))
        return 0
    rc, text = rs_next(run, a.query)
    if rc != 0:
        print(text)
        return rc
    step = rs_block(text)
    pend = admission_pending(run)
    if pend and before_phase2(run):
        print(emit_pending(run, pend))
        return 0
    if lite_exit(step):
        cand = next((run / c for c in CANDIDATES if (run / c).exists()), None)
        stale = ("EVALUATOR: protocol_audit.json is missing or an audited tool changed — re-audit the evaluation "
                 "tools (skills/soundness-gate, protocol level) before any run is judged with them.\n"
                 if protocol_stale(proj) else "")
        print("\n".join([BAR, "STATE  : LITE_CANDIDATE_READY", "TYPE   : terminal",
                         f"INPUT  : {cand}",
                         "THEN   : " + stale + "write it as ONE card in <project>/.open-scientist/cards.json (run = this "
                         "dir; fields role, deploy_inputs, baseline_switch, est_gpu_h) and send it to the card-level "
                         "soundness gate (skills/soundness-gate: deployment contract S0, S1–S8; ONE round for a cheap "
                         "run, at most one material round otherwise). KILL → no training; UPPER_BOUND → may run as a "
                         "control arm only, never the method; PASS / CHECK without 0 → reasoning-tier code review of "
                         "the diff → one single run against the best switch of phase1/prior_sweep.json → attribution "
                         "if it fails. RS Phase 3/4 (collision / scoop check) are skipped and are never a gate; write the "
                         "full card after the experiment if it is kept.\n         " + SLATE, BAR]))
        return 0
    skip = set(a.skip) | (LITE_SKIP if MODE == "lite" else set())
    for L in LAYERS:
        if L["name"] not in skip and L["due"](run, step, proj):
            print(emit_layer(L, run, proj, text))
            return 0
    print(text.rstrip())
    extra = next((f(run, proj) for cond, f in EXTRA if cond(step)), [])
    extra = [str(p) for p in extra if p.exists()]
    if extra:
        print("OPEN-SCIENTIST: also pass these to the sub-agent (layer outputs + overlay instructions; the overlay overrides the RS prompt where they conflict):")
        for p in extra:
            print(f"         {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
