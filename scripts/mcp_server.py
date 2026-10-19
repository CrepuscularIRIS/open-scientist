#!/usr/bin/env python3
"""Start the Open Scientist MCP server from a checkout (standard library only; no install step)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge.mcp_server import main  # noqa: E402

if __name__ == "__main__":
    main()
