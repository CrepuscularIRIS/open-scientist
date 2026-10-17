#!/usr/bin/env python3
"""Start MCP from a checkout without installing or changing global configuration."""
from pathlib import Path
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "src"))

try:
    from open_scientist.server import main
except ModuleNotFoundError as error:
    # Hosts launch whichever python3 is first on PATH; name the missing package and the fix.
    sys.exit(
        f"open-scientist MCP: missing Python package '{error.name}' for {sys.executable}. "
        f"Install with: {sys.executable} -m pip install '{PLUGIN_ROOT}'"
    )

if __name__ == "__main__":
    main()
