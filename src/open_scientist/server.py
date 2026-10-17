"""Thin MCP stdio adapter over the same project-local Store used by the CLI."""
from __future__ import annotations

from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .records import Kind, Ref, Store

Root = Annotated[str, Field(description="Explicit absolute path to an existing research project; no default is inferred.")]
Revision = Annotated[int, Field(strict=True, ge=0)]
Version = Annotated[int, Field(strict=True, ge=1)]

mcp = FastMCP(
    "open-scientist-records",
    instructions="Versioned research records only. Every call needs an explicit project_root. "
    "No command execution, model calls, network fetching, or background research. "
    "References are exact {id, version} in that project. Findings and investment decisions are separate. "
    "Auto mode keeps one workflow record per run; workflow_check reports which acceptance criteria still fail. "
    "Consult docs/record-api.md in the plugin for payload contracts.",
)

READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)


@mcp.tool(annotations=WRITE)
def records_put(project_root: Root, kind: Kind, record_id: str,
                payload: dict[str, Any], expected_version: Revision) -> dict[str, Any]:
    """Append one validated record. New ID: expected_version=0; update: exact current revision.

    Kinds: project(question), candidate(problem Ref/mechanism/claims), material(source/content),
    activity(objective/status/plan/inputs), assessment(type finding/decision/feedback/disposition),
    workflow(auto-mode checkpoint: goal/project/criteria/max_actions/actions_used/status/stage/next_action).
    Unknown payload fields and dangling references are rejected. There is no overwrite/delete.
    """
    return Store(project_root).put(kind, record_id, payload, expected_version)


@mcp.tool(annotations=READ)
def records_get(project_root: Root, record_id: str, version: Version | None = None) -> dict[str, Any]:
    """Read an exact revision, or latest when version is omitted. Does not create a store."""
    return Store(project_root).get(record_id, version)


@mcp.tool(annotations=READ)
def records_list(project_root: Root, kind: Kind | None = None) -> list[dict[str, Any]]:
    """List every latest record, optionally by kind. No hidden limit or scientific ranking."""
    return Store(project_root).list(kind)


@mcp.tool(annotations=READ)
def records_context(project_root: Root, subject: Ref | None = None) -> dict[str, Any]:
    """Return complete project context, exact old inputs, prior contrary findings and unresolved feedback.

    Subject identifies focus; it does not filter evidence. Stale input notices require applicability
    review, not automatic reruns. Recorded running status does not prove a process is alive.
    """
    return Store(project_root).context(subject.model_dump() if subject else None)


@mcp.tool(annotations=READ)
def workflow_check(project_root: Root, workflow_id: str, version: Version | None = None) -> dict[str, Any]:
    """Check an auto-mode workflow's declared acceptance criteria against current record versions.

    Returns pass/detail per criterion (question, literature, code, counterexamples, test_plan, card,
    decision) and `ready`. Writing status=done is refused unless ready. Structural check only: cited
    records must exist, be current and be linked to the focus candidate; it does not judge the science.
    """
    return Store(project_root).check_workflow(workflow_id, version)


@mcp.tool(annotations=READ)
def records_history(project_root: Root, record_id: str) -> list[dict[str, Any]]:
    """Return all revisions of one record, oldest first, without modifying them."""
    return Store(project_root).history(record_id)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
