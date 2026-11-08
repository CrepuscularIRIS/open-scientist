#!/usr/bin/env python3
"""Self-test of os_next.py on synthetic run directories built from a real finished RS run.

Usage: python3 scripts/selftest_os_next.py <a finished RS run dir (has phase0, phase1, phase2_*, phase3_*)>
Checks: Phase 0 only -> mainline layer; + marker -> RS Phase 1 with the extra input line; phase1 present -> gap soundness
layer; + marker -> RS Phase 2; Phase 3 passed -> card soundness layer; + marker -> problem-selection layer.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NAV = Path(__file__).resolve().parent / "os_next.py"


def nav(run: Path) -> str:
    return subprocess.run([sys.executable, str(NAV), "--dir", str(run), "--project", str(run)], capture_output=True, text=True).stdout


def main() -> int:
    src = Path(sys.argv[1]).resolve()
    ok = True
    with tempfile.TemporaryDirectory() as td:
        run = Path(td) / "run"
        run.mkdir()
        shutil.copytree(src / "phase0", run / "phase0")
        out = nav(run)
        ok &= "mainline-first" in out and "open_scientist_layer" in out
        print("phase0 only -> mainline layer:", "mainline-first" in out)
        (run / "phase0" / "mainline_first.json").write_text("{}")
        out = nav(run)
        ok &= "Phase 1" in out and "mainline_first.json" in out and "open_scientist_layer" not in out
        print("mainline done -> RS Phase 1 + extra input:", "Phase 1" in out and "OPEN-SCIENTIST" in out)
        shutil.copytree(src / "phase1", run / "phase1")
        (run / "phase1" / ".gap_filter_done").unlink(missing_ok=True)
        out = nav(run)
        ok &= "soundness-gate" in out and "GAP level" in out
        print("phase1 -> gap soundness layer:", "GAP level" in out)
        (run / "phase1" / ".gap_filter_done").write_text("")
        out = nav(run)
        ok &= ("Phase 2" in out) and "open_scientist_layer" not in out
        print("filter done -> RS Phase 2:", "Phase 2" in out)
        for d in src.iterdir():
            if d.is_dir() and d.name.startswith(("phase2", "phase3", "attempt_")) and not (run / d.name).exists():
                shutil.copytree(d, run / d.name)
        for f in src.glob(".*"):
            if f.is_file():
                shutil.copy(f, run / f.name)
        out = nav(run)
        hit = "CARD level" in out
        print("phase3 passed -> card soundness layer:", hit, "" if hit else out[:400])
        ok &= hit
        (run / "soundness_cards.json").write_text("{}")
        out = nav(run)
        hit = "problem-selection" in out
        print("cards done -> selection layer:", hit)
        ok &= hit
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
