"""Claude Code and Codex manifests describe one plugin, and its MCP server starts with the standard library alone."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).parents[1]
CLAUDE_ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def test_every_manifest_names_the_same_plugin_and_version():
    claude, codex, root = load(".claude-plugin/plugin.json"), load(".codex-plugin/plugin.json"), load("plugin.json")
    assert claude["name"] == codex["name"] == root["name"] == "open-scientist"
    assert claude["version"] == codex["version"] == root["version"]
    import forge
    assert forge.__version__ == claude["version"]
    assert f'version = "{claude["version"]}"' in (ROOT / "pyproject.toml").read_text()


def test_claude_mcp_uses_claude_variable_and_an_existing_launcher():
    server = load(".claude-plugin/plugin.json")["mcpServers"]["open-scientist"]
    launcher = server["args"][0]
    assert server["command"] == "python3" and launcher.startswith(CLAUDE_ROOT_VAR + "/")
    assert (ROOT / launcher.removeprefix(CLAUDE_ROOT_VAR + "/")).is_file()
    assert "${PLUGIN_ROOT}" not in json.dumps(server)  # Claude Code expands only CLAUDE_* variables


def test_claude_server_name_shadows_the_codex_root_mcp_file():
    codex_root = load(".mcp.json")["mcpServers"]
    assert set(codex_root) == set(load(".claude-plugin/plugin.json")["mcpServers"]) == set(load("mcp.json")["mcpServers"])
    assert "${PLUGIN_ROOT}" in json.dumps(codex_root)


def test_marketplaces_point_to_this_directory():
    market = load(".claude-plugin/marketplace.json")
    assert {p["name"]: p for p in market["plugins"]}["open-scientist"]["source"] == "./" and market["owner"]["name"]
    codex = load(".agents/plugins/marketplace.json")
    assert codex["plugins"][0]["source"]["path"] == "./"


def test_no_third_party_runtime_dependencies():
    text = (ROOT / "pyproject.toml").read_text()
    assert text.split("dependencies = [", 1)[1].split("]", 1)[0].strip() == ""


def test_skills_exist_and_the_old_names_forward_to_the_study_loop():
    main = ROOT / "skills/open-scientist/SKILL.md"
    assert main.is_file() and "name: open-scientist" in main.read_text()
    for stub in (ROOT / "skills").glob("research-*/SKILL.md"):
        text = stub.read_text()
        assert "forwards to the open-scientist" in text
        method = text.split("references/methods/actions/", 1)[1].split(".md", 1)[0]
        assert (ROOT / "references/methods/actions" / f"{method}.md").is_file()


def rpc(*messages, cwd=None):
    lines = "".join(json.dumps(m) + "\n" for m in messages)
    out = subprocess.run([sys.executable, str(ROOT / "scripts/mcp_server.py")], input=lines, capture_output=True,
                         text=True, timeout=30, cwd=cwd)
    assert out.returncode == 0, out.stderr
    return [json.loads(line) for line in out.stdout.splitlines()]


def test_mcp_server_speaks_json_rpc_over_stdio_with_the_standard_library(tmp_path):
    init, tools, call = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                            {"jsonrpc": "2.0", "method": "notifications/initialized"},
                            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                                "name": "forge_next", "arguments": {"project": str(tmp_path), "study": "s1",
                                                                    "goal": "Why does retrieval fail?"}}}, cwd=tmp_path)
    assert init["result"]["serverInfo"]["name"] == "open-scientist"
    names = {t["name"] for t in tools["result"]["tools"]}
    assert names == {"forge_next", "records_context", "records_get", "records_list", "records_history", "papers_search"}
    assert not any("put" in n for n in names)  # writes go through study commits only
    step = json.loads(call["result"]["content"][0]["text"])
    assert step["step"] == "study_init" and not call["result"]["isError"]


def test_mcp_tool_errors_are_results_not_crashes(tmp_path):
    (bad,) = rpc({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                  "params": {"name": "records_get", "arguments": {"project": str(tmp_path), "study": "s1", "id": "nope"}}})
    assert bad["result"]["isError"] and "not found" in bad["result"]["content"][0]["text"]
