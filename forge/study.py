"""A study: one research question driven by proposed actions, checked by code, committed as records.

Layout (`<project>/.forge/studies/<slug>/`):
    study.json            goal (the user's words), policy, created
    proposals/NNN.json    the agent's proposed next action
    proposals/NNN.auth.json   a person's answer when a proposal leaves the authorization
    actions/NNN-<action>/ the action's files and commit.json; COMMITTED once applied
    assets/<kind>/vN.json adaptive assets (registered as material records)
Intake is action 000. Every write to the record store goes through `commit`, which validates the action's
contract and the protocols (references/protocols.md) first.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

from forge import assets
from forge.kit import DELIVERABLES, policy_for, validate_kit, validate_policy
from forge.records import ASSERTIVE, RecordError, Store, validate_payload
from forge.util import SLUG, now, read_json, sha256_file, write_json

ACTIONS = ("adapt", "retrieve", "read", "diagnose", "construct", "evolve", "coherence", "collision", "review",
           "plan_test", "run_test", "interpret", "decide", "report", "ask_human", "build_domain", "idea_run")
DELEGATES = {"build_domain", "idea_run"}
DETERMINISTIC = {"collision", "run_test"}
EVOLVE_OPS = {"repair", "combine", "simplify", "feasibility", "out_of_box", "reframe"}
STRONG_ACCESS = {"fulltext", "inspected", "executed"}
COST_CLASSES = {"free", "cheap", "metered"}
ASK_REASONS = {"goal_change", "budget", "egress", "training_or_paid", "preference", "blocked"}
MAX_UNPRODUCTIVE = 3


class StudyLayout:
    def __init__(self, project, slug):
        if not SLUG.fullmatch(slug or ""):
            raise ValueError("Study slug must be lowercase letters, digits and hyphens (max 63)")
        self.project = Path(project).expanduser().resolve()
        self.slug = slug
        self.dir = self.project / ".forge" / "studies" / slug

    @property
    def store(self):
        """One record store per study: the study's single source of truth."""
        return Store(self.project, path=self.dir / "records.sqlite3")

    def file(self, name):
        return self.dir / name

    def meta(self):
        return read_json(self.file("study.json"))

    def resolve(self, path):
        path = Path(path)
        return path if path.is_absolute() else self.project / path

    def proposal_path(self, n):
        return self.dir / "proposals" / f"{n:03d}.json"

    def proposals(self):
        root = self.dir / "proposals"
        return sorted(int(p.stem) for p in root.glob("[0-9][0-9][0-9].json")) if root.exists() else []

    def action_dir(self, n, action):
        return self.dir / "actions" / f"{n:03d}-{action}"

    def committed(self, n, action):
        """The COMMITTED marker, only when every record it names is in the store (a hand-written marker is not)."""
        marker = read_json(self.action_dir(n, action) / "COMMITTED")
        if not isinstance(marker, dict) or not marker.get("records"):
            return None
        store = self.store
        ok = all(store.find(r["id"], r["version"]) is not None for r in marker["records"] if isinstance(r, dict))
        return marker if ok else None

    def commits(self):
        """Committed actions in order: [(n, action, COMMITTED record)]."""
        root = self.dir / "actions"
        out = []
        for d in sorted(root.glob("[0-9][0-9][0-9]-*")) if root.exists() else []:
            marker = self.committed(int(d.name[:3]), d.name[4:])
            if marker:
                out.append((int(d.name[:3]), d.name[4:], marker))
        return out

    def kit(self):
        """The committed kit, only while its file still has the recorded sha256."""
        record = self.store.find("kit")
        if not record or not record["payload"].get("path"):
            return None
        path = self.resolve(record["payload"]["path"])
        if not path.is_file() or sha256_file(path) != record["payload"].get("sha256"):
            raise ValueError(f"the kit file {path} no longer matches its record; revise the kit through adapt")
        return read_json(path)

    def policy_errors(self):
        """study.json's policy must be the one recorded at init or by a person since."""
        record = self.store.find("policy")
        meta = self.meta() or {}
        if record is None:
            return ["no recorded policy (study init writes it)"]
        if _canon(meta.get("policy")) != record["payload"]["content"]:
            return ["study.json's policy differs from the recorded one; a person changes it with `forge study policy`"]
        return []


def _canon(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def init(layout: StudyLayout, goal, mode="auto", budget=None, wall_clock_min=30, max_actions=40):
    if not goal or not goal.strip():
        raise ValueError("A non-empty goal (the user's question, verbatim) is required")
    if layout.file("study.json").exists():
        meta = layout.meta()
        if meta["goal"] != goal.strip():
            raise ValueError("This study exists with a different goal; choose a new slug")
        return {"created": False, **meta}
    layout.dir.mkdir(parents=True, exist_ok=True)
    policy = policy_for(mode, budget, wall_clock_min, max_actions)
    meta = {"study": layout.slug, "goal": goal.strip(), "created": now(), "policy": policy}
    write_json(layout.file("study.json"), meta)
    layout.store.put("material", "policy", {"source": "study init", "content": _canon(policy), "type": "note",
                                            "access": "inspected", "scope": f"mode {mode}; budget {policy['budget']['authorized']}"})
    return {"created": True, **meta}


def set_policy(layout: StudyLayout, policy, text):
    """A person changes the policy: the new policy and their words are recorded."""
    errors = validate_policy(policy)
    if errors:
        raise ValueError("; ".join(errors))
    if not text or not text.strip():
        raise ValueError("record the person's words (--text)")
    meta = layout.meta()
    current = layout.store.get("policy")
    layout.store.put_many([
        {"kind": "material", "id": "policy", "expected_version": current["version"], "payload": {
            "source": "a person", "content": _canon(policy), "type": "note", "access": "inspected", "scope": text.strip()}}])
    write_json(layout.file("study.json"), {**meta, "policy": policy})
    return {"policy": policy}


# ---------------------------------------------------------------- proposals

def _latest(store, ref):
    r = store.find(ref.get("id")) if isinstance(ref, dict) else None
    return r is not None and r["version"] == ref.get("version")


def _ref(v):
    return isinstance(v, dict) and set(v) == {"id", "version"} and isinstance(v.get("id"), str) and type(v.get("version")) is int


def latest_findings(store, subject):
    return [r for r in store.list("assessment") if r["payload"]["type"] == "finding" and r["payload"]["subject"] == subject]


def completion_errors(layout, deliverable):
    """Why the deliverable's completion rule does not hold yet (empty: it holds)."""
    store = layout.store
    if deliverable in {"exploration", "report"}:
        return []
    if deliverable == "idea_card":
        return [] if any(r["id"].startswith("idea-run-") and r["payload"].get("scope") == "outcome:done"
                         for r in store.list("material")) else ["no idea card absorbed from a finished idea_run yet"]
    if deliverable == "diagnosis":
        q = store.find("q")
        ok = q and any(f["payload"]["judgment"] in {"supported", "contradicted", "partial"}
                       for f in latest_findings(store, {"id": "q", "version": q["version"]}))
        return [] if ok else ["no finding with a judgment on the current question's premise (subject q, latest version)"]
    if deliverable == "verified_execution":
        done = [a for a in store.list("activity") if a["payload"]["status"] == "completed"]
        outputs = {(o["id"], o["version"]) for a in done for o in a["payload"].get("outputs", [])}
        ok = any((e["id"], e["version"]) in outputs for f in store.list("assessment") if f["payload"]["type"] == "finding"
                 for e in f["payload"].get("evidence", []))
        return [] if ok else ["no completed test activity whose outputs a finding interprets"]
    if deliverable == "plan":
        for c in store.list("candidate"):
            ref = {"id": c["id"], "version": c["version"]}
            planned = any(a["payload"].get("subject") == ref for a in store.list("activity"))
            reviewed = latest_findings(store, ref)
            contra = any(f["payload"]["judgment"] == "contradicted" for f in reviewed)
            if planned and reviewed and not contra:
                return []
        return ["no current candidate with a test plan and a review finding and no contradicting finding"]
    return [f"unknown deliverable {deliverable}"]


def check_proposal(layout: StudyLayout, n):
    """(errors, needs_human). Errors send the proposal back; needs_human routes it to a person first."""
    p = read_json(layout.proposal_path(n))
    store = layout.store
    if not isinstance(p, dict):
        return ["proposal must be an object"], []
    errors, ask = [], []
    action = p.get("action")
    if action not in ACTIONS:
        return [f"action must be one of {list(ACTIONS)}"], []
    for f in ("open_question", "why_now"):
        if not isinstance(p.get(f), str) or not p[f].strip():
            errors.append(f"proposal.{f} required")
    based = p.get("based_on", [])
    if not isinstance(based, list) or not all(_ref(r) for r in based):
        errors.append("proposal.based_on must be a list of {id, version} refs")
        based = []
    for r in based:
        if not _latest(store, r):
            current = store.find(r["id"])
            errors.append(f"based_on {r['id']}@{r['version']} is not current" +
                          (f" (latest is v{current['version']}); re-plan on the current version" if current else " (no such record)"))
    inputs = p.get("inputs", [])
    if not isinstance(inputs, list):
        errors.append("proposal.inputs must be a list")
        inputs = []
    for i in inputs:
        if _ref(i):
            if store.find(i["id"], i["version"]) is None:
                errors.append(f"input {i['id']}@{i['version']} does not exist")
        elif not (isinstance(i, str) and (layout.project / i).exists()):
            errors.append(f"input {i!r} is neither a record ref nor an existing path under the project")
    may = p.get("may_change", [])
    if not isinstance(may, list) or any(m not in {"Q", "H", "T", "view", "assets"} for m in may):
        errors.append("proposal.may_change must list from Q, H, T, view, assets")
    for field in ("subject", "defect"):
        if field in p and not _ref(p[field]):
            errors.append(f"proposal.{field} must be an {{id, version}} ref")
    if "subject" in p and _ref(p["subject"]) and not _latest(store, p["subject"]):
        errors.append(f"subject {p['subject']['id']}@{p['subject']['version']} is not the current version")
    for field in ("asset_kind", "operator", "reason", "domain", "topic", "run", "question"):
        if field in p and not isinstance(p[field], str):
            errors.append(f"proposal.{field} must be a string")
    if errors:
        return errors, []
    ask += _cost(layout, p, errors)
    errors += _precondition(layout, p)
    errors += _repeat(layout, n, p)
    return errors, ask


def proposal_sha(layout, n):
    return sha256_file(layout.proposal_path(n))


def authorized(layout, n):
    """True / False / None: a person's recorded answer to exactly this proposal's content."""
    auth = read_json(layout.dir / "proposals" / f"{n:03d}.auth.json")
    if not isinstance(auth, dict) or auth.get("proposal_sha256") != proposal_sha(layout, n):
        return None  # no answer, or an answer to a different version of the proposal
    record = layout.store.find(f"auth-{n:03d}")
    if not record or auth["proposal_sha256"] not in record["payload"].get("text", ""):
        return None  # an auth file the store does not back is ignored
    return bool(auth.get("approved"))


def _cost(layout, p, errors):
    cost = p.get("cost")
    if not isinstance(cost, dict) or cost.get("class") not in COST_CLASSES or not isinstance(cost.get("estimate"), str):
        errors.append(f"proposal.cost needs class {sorted(COST_CLASSES)} and estimate (text)")
        return []
    policy = layout.meta()["policy"]
    allow, budget = policy["allow"], policy["budget"]
    ask = []
    for flag, key in (("network", "network_search"), ("egress", "web_egress"), ("training", "training"), ("paid", "paid")):
        if cost.get(flag) and not allow.get(key):
            ask.append(f"{flag}: the policy does not allow {key}")
    for key in ("gpu_hours", "api_usd"):
        v = cost.get(key, 0)
        if type(v) not in (int, float) or v != v or v in (float("inf"), float("-inf")) or v < 0:
            errors.append(f"proposal.cost.{key} must be a non-negative number")
        elif v > budget.get(key, 0):
            ask.append(f"{key}: {v} exceeds the authorized {budget.get(key, 0)}")
    return ask


def _subject(store, p):
    s = p.get("subject")
    return store.find(s["id"], s["version"]) if _ref(s) else None


def _precondition(layout, p):
    store, action = layout.store, p["action"]
    q = store.find("q")
    subject = _subject(store, p)
    if action not in {"ask_human"} and q is None:
        return ["no question record yet (intake)"]
    if action == "adapt":
        kind = p.get("asset_kind")
        if not isinstance(kind, str) or (kind != "kit" and kind not in assets.KINDS):
            return [f"adapt needs asset_kind from {['kit', *sorted(assets.KINDS)]}"]
    if action == "read" and not (subject and subject["kind"] == "material" and subject["payload"].get("type") in {"paper", "review"}):
        return ["read needs subject = a paper (or review) material ref"]
    if action == "construct":
        qref = {"id": "q", "version": q["version"]}
        if any(f["payload"]["judgment"] == "contradicted" for f in latest_findings(store, qref)):
            return ["the current question has a contradicted premise: revise the question (diagnose, may_change Q) before constructing"]
    if action in {"evolve", "coherence", "review"} and not subject:
        return [f"{action} needs subject = an existing record ref"]
    if action == "evolve":
        if p.get("operator") not in EVOLVE_OPS:
            return [f"evolve needs operator from {sorted(EVOLVE_OPS)}"]
        if subject["kind"] != "candidate":
            return ["evolve needs subject = a candidate"]
        defect = store.find(p.get("defect", {}).get("id"), p.get("defect", {}).get("version")) if _ref(p.get("defect")) else None
        if not defect or defect["payload"].get("type") != "finding" or defect["payload"]["subject"] != p["subject"]:
            return ["evolve needs defect = a finding on that candidate that names what is wrong (protocol 10)"]
    if action == "collision":
        t = p.get("terms")
        if not isinstance(t, dict) or not (isinstance(t.get("signature_terms"), list) and len(t["signature_terms"]) >= 2
                                           and all(isinstance(x, str) and x.strip() for x in t["signature_terms"])
                                           and isinstance(t.get("alias_terms"), list) and t["alias_terms"]
                                           and all(isinstance(x, str) and x.strip() for x in t["alias_terms"])):
            return ["collision needs terms.signature_terms (>= 2 phrases) and terms.alias_terms (>= 1)"]
        w = t.get("windows")
        if w is not None and not (isinstance(w, dict) and all(type(w.get(k)) is int and 1 <= w[k] <= 120
                                                               for k in ("signature_months", "alias_months"))):
            return ["collision terms.windows needs signature_months and alias_months (1..120)"]
    if action == "plan_test" and not subject:
        return ["plan_test needs subject = the candidate or question whose claim is tested"]
    if action == "run_test":
        if not subject or subject["kind"] != "activity" or subject["payload"]["status"] != "plan":
            return ["run_test needs subject = an activity in status plan"]
        return plan_errors(subject["payload"])
    if action == "interpret":
        if not subject or subject["kind"] != "activity" or subject["payload"]["status"] not in {"completed", "failed"}:
            return ["interpret needs subject = a completed or failed activity"]
    if action == "decide" and not (subject and latest_findings(store, p["subject"])):
        return ["decide needs subject with at least one finding on it"]
    if action == "report":
        kit = layout.kit() or {}
        return completion_errors(layout, kit.get("deliverable", "report"))
    if action == "ask_human" and p.get("reason") not in ASK_REASONS:
        return [f"ask_human needs reason from {sorted(ASK_REASONS)}"]
    if action == "build_domain" and not (SLUG.fullmatch(str(p.get("domain", ""))) and str(p.get("topic", "")).strip()):
        return ["build_domain needs domain (slug) and topic"]
    if action == "idea_run" and not (SLUG.fullmatch(str(p.get("run", ""))) and SLUG.fullmatch(str(p.get("domain", "")))):
        return ["idea_run needs run (slug) and domain (a frozen domain slug)"]
    return []


def _norm(text):
    return " ".join(str(text).lower().split())


def plan_errors(plan):
    """Protocol 3: a plan states the claim, the strongest rival, different predictions, the command and the stop rule."""
    errors = []
    for f in ("claim", "rival", "command", "budget", "stop_rule"):
        if not isinstance(plan.get(f), str) or not plan[f].strip():
            errors.append(f"test plan needs {f}")
    preds = plan.get("predictions")
    if not isinstance(preds, dict) or not all(isinstance(preds.get(k), str) and preds[k].strip() for k in ("H", "rival")):
        errors.append("test plan needs predictions {H, rival}: what each explanation predicts you will observe")
    elif _norm(preds["H"]) == _norm(preds["rival"]):
        errors.append("H and the rival predict the same observation: this test cannot discriminate; change T")
    if not plan.get("subject"):
        errors.append("test plan needs subject (the candidate or question it tests)")
    return errors


def _repeat(layout, n, p):
    """An action repeated on the same versions and inputs that produced nothing new the first time is refused."""
    key = (p.get("action"), json.dumps(p.get("based_on"), sort_keys=True), json.dumps(p.get("inputs"), sort_keys=True),
           json.dumps(p.get("subject"), sort_keys=True))
    for m, action, marker in layout.commits():
        if m >= n or not marker.get("proposal"):
            continue
        old = marker["proposal"]
        if (old.get("action"), json.dumps(old.get("based_on"), sort_keys=True), json.dumps(old.get("inputs"), sort_keys=True),
                json.dumps(old.get("subject"), sort_keys=True)) == key and not marker.get("productive"):
            return [f"proposal repeats action {m:03d} ({action}) on the same versions and inputs, which produced nothing "
                    "new; change the inputs, the question or the action"]
    return []


# ---------------------------------------------------------------- commits

def _material_files(layout, payload, where):
    errors = []
    path = payload.get("path")
    if path:
        f = Path(path) if Path(path).is_absolute() else layout.project / path
        if not f.is_file():
            errors.append(f"{where}: path {path} does not exist")
        elif payload.get("sha256") and sha256_file(f) != payload["sha256"]:
            errors.append(f"{where}: sha256 does not match {path}")
        elif not payload.get("sha256"):
            errors.append(f"{where}: a material with a path records its sha256")
    return errors


def _evidence_errors(store, batch, payload, where):
    """Protocol 1: an assertive finding rests on material read in full, inspected or executed."""
    if payload.get("type") != "finding" or payload.get("judgment") not in ASSERTIVE:
        return []
    errors = []
    for ev in payload.get("evidence", []):
        record = batch.get((ev["id"], ev["version"])) or store.find(ev["id"], ev["version"])
        if record and record.get("kind") == "material" and record["payload"].get("access", "identity") not in STRONG_ACCESS:
            errors.append(f"{where}: evidence {ev['id']} is {record['payload'].get('access', 'identity')} only; a "
                          f"{payload['judgment']} judgment needs material read in full, inspected or executed")
    return errors


ALLOWED = {
    "intake": {"project", "material"}, "adapt": {"material"}, "retrieve": {"material"}, "read": {"material"},
    "diagnose": {"material", "assessment", "project"}, "construct": {"candidate", "material"},
    "evolve": {"candidate", "material"}, "coherence": {"assessment", "material"}, "review": {"assessment", "material"},
    "plan_test": {"activity"}, "interpret": {"assessment"}, "decide": {"assessment"}, "report": {"material"},
    # Written only by forge/execute.py, never from an agent's commit.json (the commit command refuses them):
    "run_test": {"material", "activity"}, "collision": {"material"}, "ask_human": {"assessment"},
    "build_domain": {"material"}, "idea_run": {"material", "candidate", "assessment"},
}
# Record ids only the deterministic commands write (execute.py); an agent's commit.json may not use them.
RESERVED = ("out-", "collision-", "idea-run-", "domain-", "auth-", "answer-", "absorbed-", "policy")
RESULT_JUDGMENTS = {"execution_failure": {"unknown"}, "mechanism_refuted": {"contradicted"},
                    "not_discriminating": {"unknown", "contested"}, "partial_support": {"partial"},
                    "supported": {"supported"}, "unknown": {"unknown", "contested", "not_found", "unreachable", "uncited"}}
AGENT_COMMITS = {"intake", "adapt", "retrieve", "read", "diagnose", "construct", "evolve", "coherence", "review",
                 "plan_test", "interpret", "decide", "report"}


def validate_commit(layout: StudyLayout, action, commit, proposal):
    """Errors for an action's commit.json before anything is written."""
    if not isinstance(commit, dict) or not isinstance(commit.get("records"), list) or not commit["records"]:
        return ["commit.json must be {\"records\": [{kind, id, expected_version, payload}, ...]} with at least one record"]
    store, errors, batch, pending = layout.store, [], {}, {}
    allowed = ALLOWED.get(action, set())
    for i, item in enumerate(commit["records"]):
        where = f"records[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{where}: must be an object")
            continue
        kind, rid = item.get("kind"), item.get("id")
        if kind not in allowed:
            errors.append(f"{where}: {action} may write {sorted(allowed)}, not {kind!r}")
            continue
        if action in AGENT_COMMITS and isinstance(rid, str) and rid.startswith(RESERVED):
            errors.append(f"{where}: id {rid!r} is reserved for records the study's own commands write")
            continue
        try:
            payload = validate_payload(kind, item.get("payload"))
        except RecordError as exc:
            errors.append(f"{where} ({rid}): {exc}")
            continue
        current = pending.get(rid) or (store.find(rid) if isinstance(rid, str) else None)
        version = (current["version"] if current else 0) + 1
        if item.get("expected_version", 0) != version - 1:
            errors.append(f"{where} ({rid}): expected_version must be {version - 1}")
        batch[(rid, version)] = {"kind": kind, "payload": payload}
        pending[rid] = {"version": version, "kind": kind, "payload": payload}
        errors += [f"{where} ({rid}): {e}" for e in _rules(layout, action, kind, rid, payload, current, proposal)]
        if kind == "material":
            errors += _material_files(layout, payload, f"{where} ({rid})")
        errors += _evidence_errors(store, batch, payload, f"{where} ({rid})")
    if action == "intake" and sum(1 for it in commit["records"] if it.get("kind") == "project") != 1:
        errors.append("intake writes exactly one project record, id q (the question)")
    return errors


def _rules(layout, action, kind, rid, payload, current, proposal):
    """Per-action contract rules (references/protocols.md)."""
    may = set((proposal or {}).get("may_change", []))
    if kind == "project":
        if rid != "q":
            return ["the question record id is q"]
        if action == "diagnose":
            if "Q" not in may:
                return ["this proposal may not change Q (may_change lacks Q)"]
            if current and current["payload"].get("constraints", []) != payload.get("constraints", []):
                return ["changing the user's hard constraints needs ask_human, not a diagnosis"]
            if not payload.get("change_note"):
                return ["a new question version needs change_note: what the evidence changed"]
    if kind == "material":
        if action == "retrieve" and payload.get("access", "identity") not in {"identity", "abstract"}:
            return ["retrieve registers what was found (identity or abstract); reading is a separate action"]
        if payload.get("access") == "fulltext":
            if action != "read":
                return ["only a read action records a full-text reading (protocol 1)"]
            if not (payload.get("version") or payload.get("sha256")):
                return ["a full-text reading pins what was read: version (arXiv vN) or sha256 of the local file"]
        if action == "adapt":
            return _asset_rules(layout, rid, payload, current, proposal)
        if action in {"coherence", "review", "diagnose"} and payload.get("access") == "executed" and not payload.get("sha256"):
            return ["an executed output records its sha256"]
    if kind == "candidate":
        q = layout.store.find("q")
        if payload["problem"] != {"id": "q", "version": q["version"]}:
            return [f"candidate.problem must be the current question q@{q['version']}"]
        if action == "construct" and (payload.get("operator", "construct") != "construct" or current is not None):
            return ["construct writes a new candidate with operator construct; changing an existing one is evolve"]
        if action == "evolve":
            if current is not None:
                return ["evolve never edits in place: write a child candidate with a new id (protocol 10)"]
            if payload.get("operator") != proposal.get("operator") or payload.get("parents", [])[:1] != [proposal.get("subject")]:
                return ["the child names the proposal's operator, and its first parent is the proposal's subject"]
            if payload["operator"] == "combine" and len(payload.get("parents", [])) < 2:
                return ["combine has two parents and a prediction that separates it from both"]
    if kind == "activity":
        if action == "plan_test":
            if payload["status"] != "plan" or (current is not None and current["payload"]["status"] != "plan"):
                return ["plan_test writes a plan (status plan); only run_test starts, completes or fails it"]
            return plan_errors(payload)
    if kind == "assessment":
        t = payload["type"]
        if action == "interpret":
            rt = payload.get("result_type", "unknown")
            if t != "finding" or payload["judgment"] not in RESULT_JUDGMENTS[rt]:
                return [f"interpret: result_type {rt} goes with judgment {sorted(RESULT_JUDGMENTS[rt])}, not {payload.get('judgment')}"]
            activity = (proposal or {}).get("subject")
            run = layout.store.find(activity["id"], activity["version"]) if activity else None
            if run and run["payload"]["status"] == "failed" and rt != "execution_failure":
                return ["a failed run is an execution_failure: it limits what is known, it never supports or refutes a claim"]
            outputs = {(o["id"], o["version"]) for o in (run or {}).get("payload", {}).get("outputs", [])}
            if payload["judgment"] in ASSERTIVE and not ({(e["id"], e["version"]) for e in payload.get("evidence", [])} & outputs):
                return ["an assertive interpretation cites the activity's raw outputs as evidence (protocol 4)"]
        if action == "decide":
            if t != "decision":
                return ["decide writes a decision"]
            if layout.meta()["policy"]["participation"] == "human_decisions" and payload.get("decided_by") != "human":
                return ["this study's decisions are made by a person: decided_by human, with their words in rationale"]
        if action in {"coherence", "review", "diagnose"} and t not in {"finding", "feedback"}:
            return [f"{action} writes findings (and agent feedback), not {t}"]
    return []


def _asset_rules(layout, rid, payload, current, proposal):
    kind = (proposal or {}).get("asset_kind")
    if rid != ("kit" if kind == "kit" else f"asset-{kind}") or payload.get("type") != "asset":
        return [f"adapt writes one material of type asset with id {'kit' if kind == 'kit' else 'asset-' + str(kind)}"]
    if not payload.get("path"):
        return ["an asset material points at its file (path, sha256)"]
    data = read_json(layout.resolve(payload["path"]))
    if kind == "kit":
        return validate_kit(data, assets.KINDS)
    errors = assets.validate_asset(data, layout.store, kind)
    if not errors and data.get("status") == "checked":
        prev = {"id": rid, "version": current["version"]} if current else None
        if not prev or not any(f["payload"]["judgment"] in {"supported", "partial"} for f in latest_findings(layout.store, prev)):
            errors.append("an asset becomes checked only after a review finding on its previous version supports it")
    return errors


def _content_key(r):
    p = r["payload"]
    if r["kind"] == "material":
        return ("material", p.get("sha256") or " ".join(f"{p.get('source')} {p.get('content')}".lower().split()))
    if r["kind"] == "assessment" and p["type"] == "finding":
        return ("finding", json.dumps(p["subject"], sort_keys=True), " ".join(p["claim"].lower().split()), p["judgment"])
    return None


def productive(store, applied):
    """New information: material or a finding not already in the store under any id, a changed Q/H/T, a decision,
    or a person's words. Rewording, and the same lead under a new id, are not progress."""
    applied_keys = {(r["id"], r["version"]) for r in applied}
    seen = {_content_key(r) for r in store.all() if (r["id"], r["version"]) not in applied_keys} - {None}
    for r in applied:
        kind, p = r["kind"], r["payload"]
        prev = store.find(r["id"], r["version"] - 1) if r["version"] > 1 else None
        key = _content_key(r)
        if key is not None:
            if key not in seen:
                return True
            continue
        if kind == "assessment" and (p["type"] in {"decision", "disposition"} or p.get("source") == "human"):
            return True
        if kind in {"project", "candidate"}:
            keys = ("question", "constraints") if kind == "project" else ("mechanism", "claims", "predictions", "assumptions")
            if prev is None or any(prev["payload"].get(k) != p.get(k) for k in keys):
                return True
        if kind == "activity" and (prev is None or prev["payload"]["status"] != p["status"]):
            return True
    return False


def apply_commit(layout: StudyLayout, n, action, proposal):
    """Validate and write an action's commit.json, then mark the action committed."""
    adir = layout.action_dir(n, action)
    commit = read_json(adir / "commit.json")
    errors = validate_commit(layout, action, commit, proposal)
    if errors:
        raise ValueError("commit refused: " + "; ".join(errors[:6]))
    applied = layout.store.put_many(commit["records"])
    marker = {"at": now(), "action": action, "proposal": proposal, "productive": productive(layout.store, applied),
              "records": [{"id": r["id"], "version": r["version"], "kind": r["kind"]} for r in applied],
              "commit_sha256": sha256_file(adir / "commit.json")}
    write_json(adir / "COMMITTED", marker)
    return marker


def record_files_under(layout, n, action):
    return layout.action_dir(n, action)


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text)[:80].strip("-") or "x"


ALL_DELIVERABLES = DELIVERABLES
__all__ = ["StudyLayout", "init", "check_proposal", "apply_commit", "validate_commit", "completion_errors",
           "plan_errors", "validate_policy", "ACTIONS", "DELEGATES", "DETERMINISTIC", "MAX_UNPRODUCTIVE"]
