#!/usr/bin/env python3
"""Run the per-venue OpenReview outcome collector without installing the plugin."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from forge.vendor.openreview_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
