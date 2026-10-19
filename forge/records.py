"""The one research fact store: append-only, versioned records (standard-library port of Open Scientist 0.2).

Kinds: project (Q), candidate (H), material (papers, code, data, raw outputs, assets), activity (T: a test plan and
its execution), assessment (finding, decision, feedback, disposition). Every reference is an exact
`{"id", "version"}` that must already exist; every write names the version it expects to replace. History is
never updated or deleted (SQLite triggers). The store checks structure, references and transitions; it never
judges a scientific claim. Writes come only from the study loop's commit step (forge/study_nav.py).
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3

ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
KINDS = ("project", "candidate", "material", "activity", "assessment")
JUDGMENTS = {"supported", "partial", "contradicted", "contested", "unknown", "not_found", "unreachable", "uncited"}
ASSERTIVE = {"supported", "partial", "contradicted"}
RESULT_TYPES = {"execution_failure", "mechanism_refuted", "not_discriminating", "partial_support", "supported", "unknown"}
MATERIAL_TYPES = {"paper", "code", "data", "log", "output", "asset", "review", "note"}
ACCESS = {"identity", "abstract", "fulltext", "inspected", "executed"}
DECISIONS = {"pursue", "refine", "park", "kill"}
OPERATORS = {"construct", "repair", "combine", "simplify", "feasibility", "out_of_box", "reframe"}
TRANSITIONS = {"plan": {"plan", "running", "failed"}, "running": {"running", "completed", "failed"},
               "completed": {"completed"}, "failed": {"failed"}}


class RecordError(ValueError):
    pass


def _text(v):
    return isinstance(v, str) and v.strip() != ""


def _ref(v):
    return isinstance(v, dict) and set(v) == {"id", "version"} and isinstance(v["id"], str) and ID.fullmatch(v["id"]) \
        and type(v["version"]) is int and v["version"] >= 1


def _need(cond, message):
    if not cond:
        raise RecordError(message)


def _texts(payload, field, required=False):
    v = payload.get(field, [] if not required else None)
    _need(isinstance(v, list) and all(_text(x) for x in v) and (v or not required), f"{field} must be a list of non-empty strings")


def _refs(payload, field, required=False):
    v = payload.get(field, [])
    _need(isinstance(v, list) and all(_ref(x) for x in v) and (v or not required), f"{field} must be a list of {{id, version}} refs")


def _only(payload, allowed):
    extra = set(payload) - set(allowed)
    _need(not extra, f"unknown fields {sorted(extra)}")


def validate_payload(kind, p):
    """Structural validation per kind; returns the payload with blank optionals removed."""
    _need(isinstance(p, dict), "payload must be an object")
    p = {k: v for k, v in p.items() if v is not None}
    if kind == "project":
        _only(p, {"question", "constraints", "user_context", "change_note"})
        _need(_text(p.get("question")), "project.question required")
        _texts(p, "constraints")
    elif kind == "candidate":
        _only(p, {"problem", "mechanism", "claims", "assumptions", "predictions", "rivals", "parents", "operator",
                  "change_note"})
        _need(_ref(p.get("problem")), "candidate.problem must be a project ref")
        _need(_text(p.get("mechanism")), "candidate.mechanism required")
        claims = p.get("claims")
        _need(isinstance(claims, dict) and claims and all(_text(k) and _text(v) for k, v in claims.items()),
              "candidate.claims must be a non-empty {claim_id: text} object")
        for f in ("assumptions", "predictions", "rivals"):
            _texts(p, f)
        _refs(p, "parents")
        _need(p.get("operator", "construct") in OPERATORS, f"candidate.operator must be one of {sorted(OPERATORS)}")
        _need(not p.get("parents") or _text(p.get("change_note")), "a candidate with parents needs change_note (what changed and why)")
    elif kind == "material":
        _only(p, {"source", "content", "locator", "scope", "type", "access", "sha256", "version", "path"})
        _need(_text(p.get("source")) and _text(p.get("content")), "material needs source and content")
        _need(p.get("type", "note") in MATERIAL_TYPES, f"material.type must be one of {sorted(MATERIAL_TYPES)}")
        _need(p.get("access", "identity") in ACCESS, f"material.access must be one of {sorted(ACCESS)}")
        _need("sha256" not in p or (isinstance(p["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", p["sha256"])),
              "material.sha256 must be a hex sha256")
    elif kind == "activity":
        _only(p, {"objective", "status", "plan", "inputs", "outputs", "result", "failure", "change_note", "claim",
                  "subject", "rival", "predictions", "command", "cwd", "budget", "stop_rule", "execution"})
        _need(_text(p.get("objective")) and _text(p.get("plan")), "activity needs objective and plan")
        _need(p.get("status") in TRANSITIONS, "activity.status must be plan|running|completed|failed")
        _refs(p, "inputs")
        _refs(p, "outputs")
        _need("subject" not in p or _ref(p["subject"]), "activity.subject must be a ref")
        if p["status"] == "plan":
            _need(not (p.get("outputs") or p.get("result") or p.get("failure")), "a plan cannot contain outputs, a result, or a failure")
        if p["status"] == "completed":
            _need(_text(p.get("result")), "completed activity requires result")
        if p["status"] == "failed":
            _need(_text(p.get("failure")), "failed activity requires failure")
        else:
            _need(not p.get("failure"), "failure belongs to a failed activity")
    elif kind == "assessment":
        t = p.get("type")
        _need(_ref(p.get("subject")), "assessment.subject must be a ref")
        if t == "finding":
            _only(p, {"type", "subject", "claim", "judgment", "evidence", "rationale", "scope", "result_type"})
            _need(_text(p.get("claim")) and _text(p.get("rationale")) and _text(p.get("scope")),
                  "finding needs claim, rationale and scope")
            _need(p.get("judgment") in JUDGMENTS, f"finding.judgment must be one of {sorted(JUDGMENTS)}")
            _refs(p, "evidence", required=p["judgment"] in ASSERTIVE)
            _need(p.get("result_type", "unknown") in RESULT_TYPES, f"finding.result_type must be one of {sorted(RESULT_TYPES)}")
        elif t == "decision":
            _only(p, {"type", "subject", "decision", "rationale", "evidence", "revisit_when", "decided_by"})
            _need(p.get("decision") in DECISIONS and _text(p.get("rationale")), "decision needs decision pursue|refine|park|kill and rationale")
            _need(p["decision"] != "park" or _text(p.get("revisit_when")), "park needs revisit_when")
            _need(p.get("decided_by", "model") in {"model", "human"}, "decided_by must be model|human")
            _refs(p, "evidence")
        elif t == "feedback":
            _only(p, {"type", "subject", "source", "text"})
            _need(p.get("source") in {"human", "agent"} and _text(p.get("text")), "feedback needs source human|agent and text")
        elif t == "disposition":
            _only(p, {"type", "subject", "outcome", "rationale", "outputs"})
            _need(p.get("outcome") in {"adopted", "deferred", "rejected", "superseded"} and _text(p.get("rationale")),
                  "disposition needs outcome adopted|deferred|rejected|superseded and rationale")
            _refs(p, "outputs", required=p["outcome"] in {"adopted", "superseded"})
        else:
            raise RecordError("assessment.type must be finding|decision|feedback|disposition")
    else:
        raise RecordError(f"unknown record kind {kind!r}")
    return p


def references(payload):
    """Typed reference fields only; references are never inferred from text."""
    for field in ("problem", "subject"):
        if field in payload:
            yield payload[field]
    for field in ("parents", "inputs", "outputs", "evidence"):
        yield from payload.get(field, [])


class Store:
    """`<project>/.forge/records.sqlite3`. Pass `path` to open another store (e.g. a 0.2 `.open-scientist` one)."""

    def __init__(self, project_root, path=None):
        root = Path(project_root).expanduser()
        if not root.is_absolute():
            raise RecordError("project_root must be an absolute path")
        if not root.is_dir():
            raise RecordError("project_root must be an existing directory")
        self.root = root.resolve()
        self.path = Path(path) if path else self.root / ".forge" / "records.sqlite3"

    def _connect(self, write=False):
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise RecordError("the record store cannot be a symlink")
        if write:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.path, timeout=10)
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS records (id TEXT NOT NULL, version INTEGER NOT NULL, kind TEXT NOT NULL,
                    created_at TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(id, version));
                CREATE TRIGGER IF NOT EXISTS records_no_update BEFORE UPDATE ON records
                    BEGIN SELECT RAISE(ABORT, 'record history is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS records_no_delete BEFORE DELETE ON records
                    BEGIN SELECT RAISE(ABORT, 'record history is append-only'); END;""")
        else:
            conn = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _record(row):
        return None if row is None else {**dict(row), "payload": json.loads(row["payload"])}

    @staticmethod
    def _fetch(conn, record_id, version=None):
        if version is None:
            row = conn.execute("SELECT * FROM records WHERE id=? ORDER BY version DESC LIMIT 1", (record_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM records WHERE id=? AND version=?", (record_id, version)).fetchone()
        return Store._record(row)

    def put(self, kind, record_id, payload, expected_version=0):
        return self.put_many([{"kind": kind, "id": record_id, "payload": payload, "expected_version": expected_version}])[0]

    def put_many(self, items):
        """Write several records in one transaction: all of them, in order, or none."""
        prepared = []
        for item in items:
            kind, record_id, expected = item.get("kind"), item.get("id"), item.get("expected_version", 0)
            if kind not in KINDS:
                raise RecordError(f"unknown record kind {kind!r}")
            if not isinstance(record_id, str) or not ID.fullmatch(record_id):
                raise RecordError(f"invalid record id {record_id!r}")
            if type(expected) is not int or expected < 0:
                raise RecordError("expected_version must be a non-negative integer")
            prepared.append((kind, record_id, validate_payload(kind, item.get("payload")), expected))
        results = []
        with closing(self._connect(write=True)) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            for kind, record_id, payload, expected in prepared:
                current = self._fetch(conn, record_id)
                actual = current["version"] if current else 0
                if actual != expected:
                    raise RecordError(f"revision conflict on {record_id}: expected {expected}, current {actual}")
                if current and current["kind"] != kind:
                    raise RecordError(f"{record_id}: record kind cannot change")
                if current and kind == "assessment" and current["payload"]["type"] != payload["type"]:
                    raise RecordError(f"{record_id}: assessment type cannot change; use a new record id")
                for ref in references(payload):
                    if self._fetch(conn, ref["id"], ref["version"]) is None:
                        raise RecordError(f"{record_id}: reference not found: {ref['id']}@{ref['version']}")
                self._links(conn, kind, payload)
                if current and kind == "activity":
                    self._activity_update(current["payload"], payload)
                created = datetime.now(timezone.utc).isoformat()
                encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True)
                conn.execute("INSERT INTO records VALUES (?,?,?,?,?)", (record_id, actual + 1, kind, created, encoded))
                results.append({"id": record_id, "version": actual + 1, "kind": kind, "created_at": created, "payload": payload})
        return results

    def _links(self, conn, kind, payload):
        def linked(ref):
            return self._fetch(conn, ref["id"], ref["version"])
        if kind == "candidate":
            _need(linked(payload["problem"])["kind"] == "project", "candidate.problem must reference a project")
            _need(all(linked(r)["kind"] == "candidate" for r in payload.get("parents", [])), "candidate parents must be candidates")
        if kind == "activity":
            _need(all(linked(r)["kind"] == "material" for r in payload.get("outputs", [])), "activity outputs must be materials")
        if kind == "assessment":
            subject = linked(payload["subject"])
            _need(all(linked(r)["kind"] == "material" for r in payload.get("evidence", [])),
                  "evidence must reference material records, not plans or judgments")
            if payload["type"] == "finding" and subject["kind"] == "candidate":
                _need(payload["claim"] in subject["payload"]["claims"], "claim does not exist in the referenced candidate version")
            if payload["type"] == "disposition":
                _need(subject["kind"] == "assessment" and subject["payload"]["type"] in {"feedback", "finding"},
                      "a disposition answers a feedback or finding")

    @staticmethod
    def _activity_update(old, new):
        _need(new["status"] in TRANSITIONS[old["status"]], f"invalid activity transition {old['status']} → {new['status']}; a new run is a new activity id")
        if old["status"] != "plan" or new["status"] != "plan":  # frozen at dispatch, including plan → running
            frozen = ("objective", "plan", "inputs", "claim", "rival", "predictions", "command", "budget", "stop_rule")
            _need(all(old.get(f) == new.get(f) for f in frozen), "a started activity's plan, predictions and inputs are frozen")

    def get(self, record_id, version=None):
        if version is not None and (type(version) is not int or version < 1):
            raise RecordError("version must be a positive integer")
        result = None
        if self.path.exists():
            with closing(self._connect()) as conn:
                result = self._fetch(conn, record_id, version)
        if result is None:
            raise RecordError(f"record not found: {record_id}@{version or 'latest'}")
        return result

    def find(self, record_id, version=None):
        try:
            return self.get(record_id, version)
        except RecordError:
            return None

    def all(self):
        if not self.path.exists():
            return []
        with closing(self._connect()) as conn:
            return [self._record(r) for r in conn.execute("SELECT * FROM records ORDER BY id, version")]

    def list(self, kind=None):
        if kind is not None and kind not in KINDS:
            raise RecordError(f"unknown record kind {kind!r}")
        latest = {}
        for r in self.all():
            latest[r["id"]] = r
        return [r for r in latest.values() if kind is None or r["kind"] == kind]

    def history(self, record_id):
        return [r for r in self.all() if r["id"] == record_id]

    def context(self, subject=None):
        """Latest records plus what a careful reader needs: stale inputs, earlier contrary findings, open feedback."""
        everything = self.all()
        indexed = {(r["id"], r["version"]): r for r in everything}
        latest = {}
        for r in everything:
            latest[r["id"]] = r
        if subject is not None and (subject.get("id"), subject.get("version")) not in indexed:
            raise RecordError("context subject not found")
        contrary = [r for r in everything if r["kind"] == "assessment" and r["payload"]["type"] == "finding"
                    and r["payload"]["judgment"] in {"contradicted", "contested"} and r["version"] != latest[r["id"]]["version"]]
        dispositions = {}
        for r in sorted((r for r in latest.values() if r["kind"] == "assessment"), key=lambda r: r["created_at"]):
            if r["payload"]["type"] == "disposition":
                s = r["payload"]["subject"]
                dispositions[(s["id"], s["version"])] = r["payload"]["outcome"]
        unresolved = [r for r in everything if r["kind"] == "assessment" and r["payload"]["type"] == "feedback"
                      and dispositions.get((r["id"], r["version"])) not in {"adopted", "rejected", "superseded"}]
        stale, seen = [], set()
        queue = list(latest.values()) + contrary + unresolved + ([indexed[(subject["id"], subject["version"])]] if subject else [])
        while queue:
            record = queue.pop()
            key = (record["id"], record["version"])
            if key in seen:
                continue
            seen.add(key)
            for ref in references(record["payload"]):
                queue.append(indexed[(ref["id"], ref["version"])])
                if latest[ref["id"]]["version"] != ref["version"]:
                    stale.append({"consumer": {"id": record["id"], "version": record["version"]}, "used": ref,
                                  "latest_version": latest[ref["id"]]["version"],
                                  "action": "review applicability; do not silently rerun or replace"})
        historical = [r for key, r in indexed.items() if key in seen and latest[r["id"]]["version"] != r["version"]]
        return {"records": list(latest.values()), "historical_inputs": historical, "prior_contrary_findings": contrary,
                "stale_inputs": stale,
                "unresolved_feedback": unresolved,
                "execution_notice": "A recorded running status is not proof that a process is alive."}

    def ref(self, record_id):
        r = self.get(record_id)
        return {"id": r["id"], "version": r["version"]}
