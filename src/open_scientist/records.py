"""Project-local, append-only research records; no model calls or job execution."""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
from typing import Annotated, Any, Literal

from pydantic import Field, TypeAdapter, model_validator

from . import workflow
from .base import Ref, StrictModel, Text

Kind = Literal["project", "candidate", "material", "activity", "assessment", "workflow"]


class Project(StrictModel):
    question: Text
    constraints: list[Text] = Field(default_factory=list)
    user_context: Text | None = None
    change_note: Text | None = None


class Candidate(StrictModel):
    problem: Ref
    mechanism: Text
    claims: dict[Text, Text] = Field(min_length=1)
    assumptions: list[Text] = Field(default_factory=list)
    predictions: list[Text] = Field(default_factory=list)
    parents: list[Ref] = Field(default_factory=list)
    change_note: Text | None = None


class Material(StrictModel):
    source: Text
    content: Text
    locator: Text | None = None
    scope: Text | None = None


class Activity(StrictModel):
    objective: Text
    status: Literal["plan", "running", "completed", "failed"]
    plan: Text
    inputs: list[Ref]
    outputs: list[Ref] = Field(default_factory=list)
    result: Text | None = None
    failure: Text | None = None
    change_note: Text | None = None

    @model_validator(mode="after")
    def execution_is_explicit(self):
        if self.status == "plan" and (self.outputs or self.result or self.failure):
            raise ValueError("a plan cannot contain outputs, a result, or a failure")
        if self.status == "completed" and not self.result:
            raise ValueError("completed activity requires result")
        if self.status == "failed" and not self.failure:
            raise ValueError("failed activity requires failure")
        if self.status != "failed" and self.failure:
            raise ValueError("failure belongs to a failed activity")
        return self


class Finding(StrictModel):
    type: Literal["finding"]
    subject: Ref
    claim: Text
    judgment: Literal["supported", "partial", "contradicted", "contested", "unknown", "not_found", "unreachable", "uncited"]
    evidence: list[Ref]
    rationale: Text
    scope: Text

    @model_validator(mode="after")
    def evidence_required_for_assertion(self):
        if self.judgment in {"supported", "partial", "contradicted"} and not self.evidence:
            raise ValueError("this judgment requires material evidence")
        return self


class Decision(StrictModel):
    type: Literal["decision"]
    subject: Ref
    decision: Literal["pursue", "refine", "park", "kill"]
    rationale: Text
    evidence: list[Ref] = Field(default_factory=list)
    revisit_when: Text | None = None


class Feedback(StrictModel):
    type: Literal["feedback"]
    subject: Ref
    source: Literal["human", "agent"]
    text: Text


class Disposition(StrictModel):
    type: Literal["disposition"]
    subject: Ref
    outcome: Literal["adopted", "deferred", "rejected", "superseded"]
    rationale: Text
    outputs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def action_is_identified(self):
        if self.outcome in {"adopted", "superseded"} and not self.outputs:
            raise ValueError("adopted/superseded disposition requires output references")
        return self


Assessment = Annotated[Finding | Decision | Feedback | Disposition, Field(discriminator="type")]
PAYLOADS = {"project": TypeAdapter(Project), "candidate": TypeAdapter(Candidate),
            "material": TypeAdapter(Material), "activity": TypeAdapter(Activity),
            "assessment": TypeAdapter(Assessment), "workflow": TypeAdapter(workflow.Workflow)}

KINDS = set(PAYLOADS)


def references(payload: dict):
    """Read only typed reference fields, never infer references from claim text."""
    if "criteria" in payload:  # workflow checkpoint
        yield from workflow.workflow_references(payload)
        return
    for field in ("problem", "subject"):
        if field in payload:
            yield payload[field]
    for field in ("parents", "inputs", "outputs", "evidence"):
        yield from payload.get(field, [])


class Store:
    def __init__(self, project_root: str):
        root = Path(project_root)
        if not root.is_absolute():
            raise ValueError("project_root must be an absolute path")
        if not root.is_dir():
            raise ValueError("project_root must be an existing directory")
        self.root = root.resolve()
        self.directory = self.root / ".open-scientist"
        self.path = self.directory / "records.sqlite3"

    def _connect(self, *, write=False):
        if self.directory.is_symlink() or self.path.is_symlink():
            raise ValueError("store directory/database cannot be a symlink")
        if write:
            self.directory.mkdir(exist_ok=True)
            conn = sqlite3.connect(self.path, timeout=10)
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS records (
                    id TEXT NOT NULL, version INTEGER NOT NULL,
                    kind TEXT NOT NULL, created_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY(id, version)
                );
                CREATE TRIGGER IF NOT EXISTS records_no_update
                    BEFORE UPDATE ON records BEGIN
                    SELECT RAISE(ABORT, 'record history is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS records_no_delete
                    BEFORE DELETE ON records BEGIN
                    SELECT RAISE(ABORT, 'record history is append-only'); END;
            """)
        else:
            conn = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _record(row):
        if row is None:
            return None
        return {**dict(row), "payload": json.loads(row["payload"])}

    @staticmethod
    def _fetch(conn, record_id, version=None):
        if version is None:
            row = conn.execute("SELECT * FROM records WHERE id=? ORDER BY version DESC LIMIT 1", (record_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM records WHERE id=? AND version=?", (record_id, version)).fetchone()
        return Store._record(row)

    def put(self, kind: str, record_id: str, payload: dict, expected_version: int = 0) -> dict:
        if kind not in KINDS:
            raise ValueError("unknown record kind")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", record_id):
            raise ValueError("invalid record id")
        if type(expected_version) is not int or expected_version < 0:
            raise ValueError("expected_version must be a non-negative integer")
        payload = PAYLOADS[kind].validate_python(payload).model_dump(exclude_none=True)
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        with closing(self._connect(write=True)) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            current = self._fetch(conn, record_id)
            actual = current["version"] if current else 0
            if actual != expected_version:
                raise ValueError(f"revision conflict: expected {expected_version}, current {actual}")
            if current and current["kind"] != kind:
                raise ValueError("record kind cannot change")
            if current and kind == "assessment" and current["payload"]["type"] != payload["type"]:
                raise ValueError("assessment type cannot change; use a new record ID")
            for ref in references(payload):
                if self._fetch(conn, ref["id"], ref["version"]) is None:
                    raise ValueError(f"reference not found in this project: {ref}")
            self._validate_links(conn, kind, payload)
            if current and kind == "activity":
                self._validate_activity_update(current["payload"], payload)
            if kind == "workflow":
                everything = [self._record(row) for row in conn.execute("SELECT * FROM records")]
                history = [r for r in everything if r["id"] == record_id]
                workflow.validate_transition(current["payload"] if current else None, payload, history, everything)
            result = {"id": record_id, "version": actual + 1, "kind": kind,
                      "created_at": datetime.now(timezone.utc).isoformat(), "payload": payload}
            conn.execute("INSERT INTO records VALUES (?,?,?,?,?)", (
                record_id, actual + 1, kind, result["created_at"], encoded,
            ))
        return result

    def _validate_links(self, conn, kind, payload):
        def linked(ref):
            return self._fetch(conn, ref["id"], ref["version"])

        if kind == "candidate":
            if linked(payload["problem"])["kind"] != "project":
                raise ValueError("candidate problem must reference a project")
            if any(linked(ref)["kind"] != "candidate" for ref in payload["parents"]):
                raise ValueError("candidate parents must reference candidates")
        if kind == "assessment":
            subject = linked(payload["subject"])
            if any(linked(ref)["kind"] != "material" for ref in payload.get("evidence", [])):
                raise ValueError("evidence must reference material records, not plans or judgments")
            if payload["type"] == "finding" and subject["kind"] == "candidate":
                if payload["claim"] not in subject["payload"]["claims"]:
                    raise ValueError("claim does not exist in the referenced candidate version")
            if payload["type"] == "disposition":
                if subject["kind"] != "assessment" or subject["payload"]["type"] not in {"feedback", "finding"}:
                    raise ValueError("disposition subject must be a feedback or finding assessment")

    @staticmethod
    def _validate_activity_update(old, new):
        allowed = {"plan": {"plan", "running", "failed"},
                   "running": {"running", "completed", "failed"},
                   "completed": {"completed"}, "failed": {"failed"}}
        if new["status"] not in allowed[old["status"]]:
            raise ValueError("invalid activity transition; use a new ID for a new run")
        # Freeze the submitted plan at dispatch, including the plan→running edge.
        if old["status"] != "plan" or new["status"] != "plan":
            if any(old[field] != new[field] for field in ("objective", "plan", "inputs")):
                raise ValueError("activity objective, plan, and inputs are frozen once started")

    def check_workflow(self, record_id: str, version: int | None = None) -> dict:
        """Evaluate a workflow's declared acceptance criteria against current records."""
        record = self.get(record_id, version)
        if record["kind"] != "workflow":
            raise ValueError(f"{record_id} is not a workflow record")
        with closing(self._connect()) as conn:
            everything = [self._record(row) for row in conn.execute("SELECT * FROM records")]
        return {"workflow": {"id": record["id"], "version": record["version"]},
                "status": record["payload"]["status"], **workflow.check(record["payload"], everything)}

    def get(self, record_id: str, version: int | None = None) -> dict:
        if version is not None and (type(version) is not int or version < 1):
            raise ValueError("version must be a positive integer")
        result = None
        if self.path.exists():
            with closing(self._connect()) as conn:
                result = self._fetch(conn, record_id, version)
        if result is None:
            raise ValueError(f"record not found: {record_id}@{version or 'latest'}")
        return result

    def list(self, kind: str | None = None) -> list[dict]:
        if kind is not None and kind not in KINDS:
            raise ValueError("unknown record kind")
        if not self.path.exists():
            return []
        with closing(self._connect()) as conn:
            rows = conn.execute("""SELECT r.* FROM records r JOIN
                (SELECT id, MAX(version) v FROM records GROUP BY id) latest
                ON r.id=latest.id AND r.version=latest.v
                WHERE (? IS NULL OR r.kind=?) ORDER BY r.id""", (kind, kind)).fetchall()
        return [self._record(row) for row in rows]

    def history(self, record_id: str) -> list[dict]:
        if not self.path.exists():
            return []
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM records WHERE id=? ORDER BY version", (record_id,)).fetchall()
        return [self._record(row) for row in rows]

    def context(self, subject: dict | None = None) -> dict:
        if subject is not None:
            subject = Ref.model_validate(subject).model_dump()
        # One read snapshot keeps latest pointers and their dependencies consistent.
        rows = []
        if self.path.exists():
            with closing(self._connect()) as conn:
                rows = conn.execute("SELECT * FROM records ORDER BY id, version").fetchall()
        all_records = [self._record(row) for row in rows]
        indexed = {(r["id"], r["version"]): r for r in all_records}
        latest = {r["id"]: r for r in all_records}
        if subject and (subject["id"], subject["version"]) not in indexed:
            raise ValueError("context subject reference not found in this project")
        contrary = [r for r in all_records if r["kind"] == "assessment"
                    and r["payload"]["type"] == "finding"
                    and r["payload"]["judgment"] in {"contradicted", "contested"}
                    and r["version"] != latest[r["id"]]["version"]]
        assessments = [r for r in latest.values() if r["kind"] == "assessment"]
        dispositions = {}
        for r in sorted(assessments, key=lambda r: r["created_at"]):
            p = r["payload"]
            if p["type"] == "disposition":
                dispositions[(p["subject"]["id"], p["subject"]["version"])] = p
        # A revision is not an implicit withdrawal of earlier instructions.
        # Consumption/supersession always names an exact feedback version.
        unresolved = [r for r in all_records if r["kind"] == "assessment"
                      and r["payload"]["type"] == "feedback"
                      and dispositions.get((r["id"], r["version"]), {}).get("outcome")
                      not in {"adopted", "rejected", "superseded"}]
        history, stale, visited = {}, [], set()
        queue = list(latest.values()) + contrary + unresolved
        if subject:
            queue.append(indexed[(subject["id"], subject["version"])])
        while queue:
            record = queue.pop()
            key = (record["id"], record["version"])
            if key in visited:
                continue
            visited.add(key)
            if latest[record["id"]]["version"] != record["version"]:
                history[key] = record
            for ref in references(record["payload"]):
                target = indexed[(ref["id"], ref["version"])]
                queue.append(target)
                current = latest[ref["id"]]["version"]
                if current != ref["version"]:
                    stale.append({"consumer": {"id": record["id"], "version": record["version"]},
                                  "used": ref, "latest_version": current,
                                  "action": "review applicability; do not silently rerun or replace"})
        return {"project_root": str(self.root), "subject": subject,
                "records": list(latest.values()), "historical_inputs": list(history.values()),
                "prior_contrary_findings": contrary, "stale_inputs": stale,
                "unresolved_feedback": unresolved, "truncated": False,
                "execution_notice": "Recorded running status is not proof a process is alive; context never starts work."}
