"""Auto-mode workflow checkpoints and the evidence-based milestone check.

A workflow record is the loop state of one bounded research run: goal, acceptance
criteria, budget, stage, the last action and the next one. The store appends one
version per checkpoint. Only two transitions are gated mechanically: `done` needs
every declared criterion to hold on current record versions, and an
`evidence_based_stop` needs a kill/park decision backed by material. Everything
else stays a host-agent judgment.
"""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from .base import Ref, StrictModel, Text

Criterion = Literal["question", "literature", "code", "counterexamples", "test_plan", "card", "decision"]
CRITERIA: tuple[str, ...] = Criterion.__args__
Stage = Literal["frame", "ground", "abduce", "probe", "grill", "report"]
Status = Literal["active", "waiting_user", "paused", "done", "stopped"]
StopReason = Literal["evidence_based_stop", "no_progress", "budget", "blocked", "user_abort"]
TERMINAL = {"done", "stopped"}
CONTRACT = ("goal", "criteria", "max_actions", "authorized", "forbidden")
# Idempotency key, e.g. "retrieve:q@2:alias-search#2"; '@' and '#' tag versions and retries.
ACTION_KEY = r"^[A-Za-z0-9][A-Za-z0-9_.:@#/-]{0,199}$"
CONTRARY = {"contradicted", "contested"}
RESOLVED = {"adopted", "rejected", "superseded"}
ASSERTED = {"supported", "partial", "contradicted", "contested"}


class Action(StrictModel):
    key: Annotated[str, StringConstraints(pattern=ACTION_KEY)]
    skill: Text
    question: Text
    outcome: Literal["advanced", "no_change", "failed", "needs_user"]
    summary: Text
    outputs: list[Ref] = Field(default_factory=list)


class NextAction(StrictModel):
    skill: Text
    question: Text
    why: Text


class Workflow(StrictModel):
    goal: Text
    project: Ref
    criteria: list[Criterion] = Field(min_length=1)
    max_actions: int = Field(ge=1, le=500)
    actions_used: int = Field(ge=0)
    status: Status
    stage: Stage
    focus: Ref | None = None
    evidence: dict[Criterion, list[Ref]] = Field(default_factory=dict)
    authorized: list[Text] = Field(default_factory=list)
    forbidden: list[Text] = Field(default_factory=list)
    last_action: Action | None = None
    open_issues: list[Text] = Field(default_factory=list)
    next_action: NextAction | None = None
    question_for_user: Text | None = None
    stop_reason: StopReason | None = None
    summary: Text | None = None
    user_input: Ref | None = None  # human feedback that authorizes a contract change or a resume

    @model_validator(mode="after")
    def status_fields_are_consistent(self):
        if len(set(self.criteria)) != len(self.criteria):
            raise ValueError("criteria must not repeat")
        if not set(self.evidence) <= set(self.criteria):
            raise ValueError("evidence keys must be declared criteria")
        if self.actions_used > self.max_actions:
            raise ValueError("actions_used exceeds max_actions; stop with stop_reason=budget or raise the budget")
        if self.status == "active" and self.next_action is None:
            raise ValueError("an active workflow requires next_action")
        if self.status == "waiting_user" and not self.question_for_user:
            raise ValueError("waiting_user requires question_for_user")
        if self.status == "stopped" and not (self.stop_reason and self.summary):
            raise ValueError("stopped requires stop_reason and summary")
        if self.status != "stopped" and self.stop_reason:
            raise ValueError("stop_reason belongs to a stopped workflow")
        if self.status == "done" and not self.summary:
            raise ValueError("done requires summary")
        return self


def workflow_references(payload: dict):
    yield payload["project"]
    if "focus" in payload:
        yield payload["focus"]
    for refs in payload.get("evidence", {}).values():
        yield from refs
    yield from payload.get("last_action", {}).get("outputs", [])
    if "user_input" in payload:
        yield payload["user_input"]


class _Snapshot:
    """Read-only view of every record version in one project."""

    def __init__(self, records: list[dict]):
        self.exact = {(r["id"], r["version"]): r for r in records}
        self.latest: dict[str, dict] = {}
        for r in records:
            if r["id"] not in self.latest or r["version"] > self.latest[r["id"]]["version"]:
                self.latest[r["id"]] = r

    def get(self, ref: dict) -> dict | None:
        return self.exact.get((ref["id"], ref["version"]))

    def is_latest(self, ref: dict) -> bool:
        return ref["id"] in self.latest and self.latest[ref["id"]]["version"] == ref["version"]

    def latest_of(self, kind: str, assessment_type: str | None = None):
        for r in self.latest.values():
            if r["kind"] == kind and (assessment_type is None or r["payload"].get("type") == assessment_type):
                yield r


def _label(ref: dict) -> str:
    return f"{ref['id']}@{ref['version']}"


def _refs(payload: dict, criterion: str, snap: _Snapshot) -> list[dict]:
    """Cited records that are still their latest version; a superseded citation no longer counts."""
    return [snap.get(ref) for ref in payload.get("evidence", {}).get(criterion, [])
            if snap.get(ref) and snap.is_latest(ref)]


def _focus(payload: dict, snap: _Snapshot) -> tuple[dict | None, str]:
    focus = payload.get("focus")
    if not focus:
        return None, "no focus candidate set"
    if not snap.is_latest(focus):
        newest = {"id": focus["id"], "version": snap.latest[focus["id"]]["version"]}
        return None, f"focus {_label(focus)} is stale; latest is {_label(newest)}"
    return snap.get(focus), ""


def _question(payload, snap, focus):
    project = payload["project"]
    if not snap.is_latest(project):
        return False, f"project {_label(project)} changed; re-point the workflow to the latest question"
    ok = any(r["kind"] == "project" and r["id"] == project["id"] and r["version"] == project["version"]
             for r in _refs(payload, "question", snap))
    return ok, "question pinned" if ok else "cite the current project record"


def _literature(payload, snap, focus):
    ok = any(r["kind"] == "assessment" and r["payload"]["type"] == "finding" and r["payload"]["evidence"]
             and r["payload"]["judgment"] in ASSERTED for r in _refs(payload, "literature", snap))
    return ok, "source-backed finding cited" if ok else "cite a finding whose judgment rests on material evidence"


def _code(payload, snap, focus):
    ok = any(r["kind"] == "material" and r["payload"].get("locator") for r in _refs(payload, "code", snap))
    return ok, "located code/data material cited" if ok else "cite material with a file/line locator"


def _counterexamples(payload, snap, focus):
    if focus is None:
        return False, _focus(payload, snap)[1]
    ref = {"id": focus["id"], "version": focus["version"]}
    findings = [r for r in snap.latest_of("assessment", "finding") if r["payload"]["subject"] == ref]
    missing = sorted(set(focus["payload"]["claims"]) - {r["payload"]["claim"] for r in findings})
    if missing:
        return False, f"claims without a finding on {_label(ref)}: {', '.join(missing)}"
    # Every contrary finding ever recorded on any version of this candidate stays open until its most
    # recent disposition resolves it; softening the finding or revising H does not erase it.
    newest = {}
    for d in sorted(snap.latest_of("assessment", "disposition"), key=lambda d: d["created_at"]):
        newest[(d["payload"]["subject"]["id"], d["payload"]["subject"]["version"])] = d["payload"]
    def resolved(key):
        d = newest.get(key)
        return bool(d) and (d["outcome"] in {"adopted", "superseded"}
                            or (d["outcome"] == "rejected" and d.get("outputs")))
    contrary = {(r["id"], r["version"]) for r in snap.exact.values()
                if r["kind"] == "assessment" and r["payload"]["type"] == "finding"
                and r["payload"]["subject"]["id"] == focus["id"] and r["payload"]["judgment"] in CONTRARY}
    open_contrary = sorted(f"{i}@{v}" for i, v in contrary if not resolved((i, v)))
    if open_contrary:
        return False, f"contrary findings without a resolving disposition (a rejection needs output evidence): {', '.join(open_contrary)}"
    return True, f"every claim of {_label(ref)} assessed; contrary findings disposed"


def _test_plan(payload, snap, focus):
    if focus is None:
        return False, _focus(payload, snap)[1]
    ref = {"id": focus["id"], "version": focus["version"]}
    ok = any(r["kind"] == "activity" and r["payload"]["status"] != "failed" and ref in r["payload"]["inputs"]
             for r in _refs(payload, "test_plan", snap))
    return ok, "test plan bound to focus" if ok else f"cite an activity whose inputs include {_label(ref)}"


def _card(payload, snap, focus):
    if focus is None:
        return False, _focus(payload, snap)[1]
    ok = any(r["kind"] == "material" and r["created_at"] > focus["created_at"] for r in _refs(payload, "card", snap))
    return ok, "card rendered after current focus" if ok else "render the card from the current focus version"


def _decision(payload, snap, focus):
    targets = [payload["project"]] + ([{"id": focus["id"], "version": focus["version"]}] if focus else [])
    ok = any(r["kind"] == "assessment" and r["payload"]["type"] == "decision" and r["payload"]["subject"] in targets
             for r in _refs(payload, "decision", snap))
    return ok, "decision on current focus/project" if ok else "cite a decision on the current focus or project version"


CHECKS = {"question": _question, "literature": _literature, "code": _code, "counterexamples": _counterexamples,
          "test_plan": _test_plan, "card": _card, "decision": _decision}


def check(payload: dict, records: list[dict]) -> dict:
    """Mechanical milestone check; it verifies record links and currency, not scientific truth."""
    snap = _Snapshot(records)
    focus, focus_note = _focus(payload, snap)
    results = {}
    for name in payload["criteria"]:
        passed, detail = CHECKS[name](payload, snap, focus)
        results[name] = {"pass": passed, "detail": detail}
    return {"ready": all(r["pass"] for r in results.values()), "criteria": results,
            "focus": payload.get("focus"), "focus_note": focus_note or "current",
            "notice": "Structural acceptance only: it checks that cited records exist, are current and are linked; "
                      "it does not judge whether the science is right."}


def validate_transition(old_record: dict | None, new: dict, history: list[dict], records: list[dict]) -> None:
    snap = _Snapshot(records)
    old = old_record["payload"] if old_record else None
    if snap.get(new["project"])["kind"] != "project":
        raise ValueError("workflow project must reference a project record")
    if "focus" in new and snap.get(new["focus"])["kind"] != "candidate":
        raise ValueError("workflow focus must reference a candidate record")
    if old and old["status"] in TERMINAL:
        raise ValueError("workflow is terminal; start a new workflow ID to continue")
    _validate_action_count(old, new, history)
    if old and any(old.get(k) != new.get(k) for k in CONTRACT):
        _require_human_input(old_record, new, snap, "changing the run contract (goal/criteria/budget/authorization)")
    if old and old["status"] == "waiting_user" and new["status"] != "waiting_user":
        _require_human_input(old_record, new, snap, "leaving waiting_user")
    if new["status"] == "done":
        report = check(new, records)
        if not report["ready"]:
            failed = [f"{k}: {v['detail']}" for k, v in report["criteria"].items() if not v["pass"]]
            raise ValueError("workflow not ready for done; " + "; ".join(failed))
    if new.get("stop_reason") == "evidence_based_stop":
        anchors = [ref for ref in (new["project"], new.get("focus")) if ref and snap.is_latest(ref)]
        if not any(r["payload"]["decision"] in {"kill", "park"} and r["payload"].get("evidence")
                   and r["payload"]["subject"] in anchors for r in snap.latest_of("assessment", "decision")):
            raise ValueError("evidence_based_stop requires a kill or park decision with material evidence")


def _require_human_input(old_record: dict, new: dict, snap: _Snapshot, why: str) -> None:
    ref = new.get("user_input")
    fb = snap.get(ref) if ref else None
    if not (fb and fb["kind"] == "assessment" and fb["payload"]["type"] == "feedback"
            and fb["payload"]["source"] == "human" and fb["created_at"] > old_record["created_at"]):
        raise ValueError(f"{why} requires user_input citing a human feedback record written after the previous checkpoint")


def _validate_action_count(old: dict | None, new: dict, history: list[dict]) -> None:
    previous = old["actions_used"] if old else 0
    action = new.get("last_action")
    if new["actions_used"] == previous:
        if action != (old or {}).get("last_action"):
            raise ValueError("a new last_action must increment actions_used by one")
        return
    if new["actions_used"] != previous + 1 or action is None:
        raise ValueError("each checkpoint records at most one action (actions_used +1 with a last_action)")
    seen = {h["payload"]["last_action"]["key"] for h in history if "last_action" in h["payload"]}
    if action["key"] in seen:
        raise ValueError(f"action key '{action['key']}' already recorded; do not repeat it, or use a new key for a deliberate retry")
