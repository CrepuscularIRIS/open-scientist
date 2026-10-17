"""Exercise CLI subprocess and real SDK stdio transport, not mocked tool calls."""
import asyncio
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_cli_records_and_reads_in_explicit_project_from_other_cwd(tmp_path):
    script = ROOT / "scripts" / "records.py"
    if not script.exists():
        pytest.fail("CLI fallback is not implemented")
    project = tmp_path / "project"
    project.mkdir()
    args = [sys.executable, str(script), "--project-root", str(project)]
    put = subprocess.run(args + ["put", "--kind", "project", "--record-id", "project", "--expected-version", "0", "--payload-file", "-"], input='{"question":"Why does retrieval fail?"}', text=True, capture_output=True, cwd=tmp_path, timeout=20)
    assert put.returncode == 0, put.stderr
    get = subprocess.run(args + ["get", "project", "--version", "1"], text=True, capture_output=True, cwd=tmp_path, timeout=20)
    assert get.returncode == 0, get.stderr
    assert json.loads(get.stdout)["payload"]["question"] == "Why does retrieval fail?"
    assert not (tmp_path / ".open-scientist").exists()
    stale = subprocess.run(args + ["put", "--kind", "project", "--record-id", "project", "--expected-version", "0", "--payload-file", "-"], input='{"question":"Stale write"}', text=True, capture_output=True, cwd=tmp_path, timeout=20)
    assert stale.returncode != 0
    assert "revision conflict" in stale.stderr


def test_real_stdio_tools_write_read_context_and_reject_unscoped_request(tmp_path):
    script = ROOT / "scripts" / "mcp_server.py"
    if not script.exists():
        pytest.fail("MCP stdio entrypoint is not implemented")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def exercise():
        parameters = StdioServerParameters(command=sys.executable, args=[str(script)], cwd=str(tmp_path))
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                info = await session.initialize()
                assert info.serverInfo.name == "open-scientist-records"
                tools = (await session.list_tools()).tools
                names = {tool.name for tool in tools}
                assert names == {"records_put", "records_get", "records_list", "records_context", "records_history"}
                assert all("project_root" in t.inputSchema["required"] for t in tools)
                assert not (tmp_path / ".open-scientist").exists()
                invalid = await session.call_tool("records_list", {})
                assert invalid.isError
                put = await session.call_tool("records_put", {
                    "project_root": str(tmp_path), "kind": "project", "record_id": "project",
                    "payload": {"question": "Can this be recovered?"}, "expected_version": 0,
                })
                assert not put.isError, put.content
                read = await session.call_tool("records_get", {"project_root": str(tmp_path), "record_id": "project", "version": 1})
                assert not read.isError
                assert read.structuredContent["payload"]["question"] == "Can this be recovered?"
                context = await session.call_tool("records_context", {"project_root": str(tmp_path)})
                assert not context.isError
                assert context.structuredContent["truncated"] is False
                assert context.structuredContent["records"][0]["id"] == "project"
                invalid = await session.call_tool("records_put", {
                    "project_root": str(tmp_path), "kind": "material", "record_id": "bad",
                    "payload": {"source": "paper", "content": "quote", "supports": True}, "expected_version": 0,
                })
                assert invalid.isError

    asyncio.run(asyncio.wait_for(exercise(), timeout=30))
