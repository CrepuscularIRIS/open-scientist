"""Codex and Claude Code manifests must describe the same plugin and a startable MCP server."""
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
CLAUDE_ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def test_claude_manifest_matches_codex_identity():
    claude = load(".claude-plugin/plugin.json")
    codex = load(".codex-plugin/plugin.json")
    assert claude["name"] == codex["name"] == "open-scientist"
    assert claude["version"] == codex["version"] == load("plugin.json")["version"]


def test_claude_mcp_uses_claude_variable_and_existing_launcher():
    servers = load(".claude-plugin/plugin.json")["mcpServers"]
    server = servers["research-records"]
    assert server["command"] == "python3"
    launcher = server["args"][0]
    assert launcher.startswith(CLAUDE_ROOT_VAR + "/")
    assert (ROOT / launcher.removeprefix(CLAUDE_ROOT_VAR + "/")).is_file()
    # Claude Code expands only CLAUDE_* plugin variables; Codex's would fail to start.
    assert "${PLUGIN_ROOT}" not in json.dumps(server)


def test_claude_server_name_shadows_codex_root_mcp_file():
    # Claude Code also reads the root .mcp.json written for Codex (${PLUGIN_ROOT}).
    # Using the same server name lets the manifest entry replace that unstartable one.
    codex_root = load(".mcp.json")["mcpServers"]
    assert set(codex_root) == set(load(".claude-plugin/plugin.json")["mcpServers"])
    assert "${PLUGIN_ROOT}" in json.dumps(codex_root), "Codex entry must stay unchanged"


def test_claude_local_marketplace_points_to_this_directory():
    market = load(".claude-plugin/marketplace.json")
    entries = {p["name"]: p for p in market["plugins"]}
    assert entries["open-scientist"]["source"] == "./"
    assert market["owner"]["name"]


def test_mcp_sdk_is_a_required_dependency():
    text = (ROOT / "pyproject.toml").read_text()
    dependencies = text.split("dependencies = [", 1)[1].split("]", 1)[0]
    assert "mcp" in dependencies
