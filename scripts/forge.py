#!/usr/bin/env python3
"""Run Research Forge from a checkout or installed plugin; standard library only."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from forge.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
