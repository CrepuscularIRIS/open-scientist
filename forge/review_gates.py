"""Validators for idea-run artifacts, part 2: audit, revision, idea card, decision.

The audit's hard floor and the decision's hard limits are enforced here. A
domain expectation is a question the audit must answer for this candidate —
met, unmet, not applicable to this claim, or challenged with evidence — and
only an unmet required one blocks `advance`. A revision may change only the
field paths its audit targets name, each within what the target's scope
allows; the round-2 audit judges whether the change kept the science. These
checks police what changed, not whether the change is scientifically
equivalent.
"""
from __future__ import annotations

from forge.ideas import (FALSIFICATION_KEYS, REQUIRED_STRENGTH, THREATS, _dicts, _t, _ts, _unknown, bindings,
                         changed_fields, resources_errors, threat_kind, tolerant, validate_candidate)

CRITIC_DIMS = ("novelty", "impact", "timing", "feasibility", "competition", "nugget", "narrative")
_F = {f"falsification.{k}" for k in FALSIFICATION_KEYS}
SCOPE_FIELDS = {
    "tactical": {"title", "hook", "core_mechanism", "mechanism_steps", "gap_closure.how_closed", "premises",
                 "naive_baseline", "differentiation", "almost_prior", "signature_terms", "alias_terms", "crossmap_used",
                 "alternatives_considered", "resources.estimate"},
    "card": {"gap_closure", "gap_closure.how_closed", "core_mechanism", "mechanism_steps", "premises",
             "signature_terms", "alias_terms", "crossmap_used"},
    "falsification": _F | {"resources.estimate"},
    # A cheaper test that still discriminates: same variable, control, metric and direction.
    "feasibility": {"falsification.experiment", "resources.estimate", "mechanism_steps"},
}
CARD_COPIED = ("title", "hook", "almost_prior", "differentiation", "falsification", "resources")
COVERAGE = {"met", "partial", "gap", "not_applicable", "challenged"}


def _expectation_answers(block, refs, errors):
    """(unmet ids, n/a ids, challenged ids) from checks.expectations, validated."""
    unmet = block.get("unmet")
    if not isinstance(unmet, list) or any(u not in refs.expectations for u in unmet):
        errors.append("checks.expectations.unmet must list known expectation ids (may be empty)")
        unmet = []
    answered = {}
    for key, need_refs in (("not_applicable", False), ("challenged", True)):
        rows = _dicts(block.get(key) or [])
        if rows is None:
            errors.append(f"checks.expectations.{key} must be a list of objects")
            rows = []
        for i, r in enumerate(rows):
            if r.get("id") not in refs.expectations or not _t(r.get("reason")):
                errors.append(f"checks.expectations.{key}[{i}]: needs a known id and a reason tied to this candidate's claim")
            if need_refs:
                if not r.get("refs"):
                    errors.append(f"checks.expectations.challenged[{i}]: a challenged convention needs evidence refs")
                _unknown(refs, r.get("refs"), f"checks.expectations.challenged[{i}]", errors)
            answered.setdefault(r.get("id"), key)
    clash = sorted(i for i in answered if i in unmet)
    if clash:
        errors.append(f"checks.expectations: {clash} cannot be both unmet and not_applicable/challenged")
    return unmet


@tolerant
def validate_audit(data, refs, coherence, round_=1):
    if not isinstance(data, dict):
        return ["audit.json missing or not an object"]
    errors, checks = [], data.get("checks") if isinstance(data.get("checks"), dict) else {}
    for name in ("card_failure_modes", "operation_applied", "anti_patterns", "paper_threat", "falsification_structure", "expectations"):
        if not isinstance(checks.get(name), dict) or not _t(checks[name].get("finding")):
            errors.append(f"checks.{name}.finding required")
    checks = {k: (v if isinstance(v, dict) else {}) for k, v in checks.items()}
    if checks.get("operation_applied", {}).get("status") not in {"applied", "bypassed", "n_a"}:
        errors.append("checks.operation_applied.status must be applied|bypassed|n_a")
    threat = checks.get("paper_threat", {})
    if threat.get("kind") not in THREATS:
        errors.append("checks.paper_threat.kind must be none|partial_overlap|subsumes|same_mechanism")
    elif threat["kind"] != "none":
        _unknown(refs, [threat.get("threat_ref")], "paper_threat", errors)
    if checks.get("falsification_structure", {}).get("numeric_bar_provenance") not in {"none", "derived", "measured", "asserted", "invented"}:
        errors.append("falsification_structure.numeric_bar_provenance must be none|derived|measured|asserted|invented")
    unmet = _expectation_answers(checks.get("expectations", {}), refs, errors)
    blocking = _dicts((coherence or {}).get("blocking") or []) or []
    disp = _dicts(data.get("blocking_dispositions") or []) or []
    if sorted(map(str, (d.get("index") for d in disp))) != sorted(map(str, range(len(blocking)))) or \
            any(d.get("disposition") not in {"upheld", "refuted"} or not _t(d.get("reason")) for d in disp):
        errors.append(f"blocking_dispositions must give upheld|refuted with a reason for each of {len(blocking)} blocking findings")
    critic = data.get("critic") if isinstance(data.get("critic"), dict) else {}
    if any(type(critic.get(k)) is not int or not 1 <= critic[k] <= 5 for k in CRITIC_DIMS) or not _t(critic.get("nugget_sentence")):
        errors.append(f"critic needs integer 1..5 scores for {', '.join(CRITIC_DIMS)} and nugget_sentence")
    strategy = data.get("strategy") if isinstance(data.get("strategy"), dict) else {}
    if not _t(strategy.get("timing_basis")) or strategy.get("scoop_risk") not in {"low", "medium", "high"}:
        errors.append("strategy needs timing_basis and scoop_risk low|medium|high")
    verdict = data.get("verdict")
    if verdict not in {"advance", "revise", "abandon"} or not _t(data.get("verdict_rationale")):
        errors.append("verdict must be advance|revise|abandon with verdict_rationale")
    if round_ > 1 and verdict == "revise":
        errors.append("this is the post-revision audit: revise is not allowed again; advance or abandon")
    upheld = any(d.get("disposition") == "upheld" for d in disp)
    floor = bool(checks.get("card_failure_modes", {}).get("triggered")) or threat.get("kind") == "same_mechanism" or upheld
    if floor and verdict != "abandon":
        errors.append("hard floor: a triggered failure mode, a same_mechanism threat or an upheld blocking finding requires abandon")
    required_unmet = [u for u in unmet if refs.expectations.get(u) in REQUIRED_STRENGTH]
    if verdict == "advance" and required_unmet:
        errors.append(f"advance is forbidden with unmet required expectations {required_unmet}; "
                      + ("revise, or answer not_applicable/challenged with a reason" if round_ == 1 else "abandon instead"))
    targets = _dicts(data.get("revision_targets") or []) or []
    if verdict == "revise" and not targets:
        errors.append("revise needs >= 1 revision_targets entry")
    for i, t in enumerate(targets if verdict == "revise" else []):
        scope = t.get("scope")
        if scope not in SCOPE_FIELDS or not _t(t.get("instruction")):
            errors.append(f"revision_targets[{i}]: scope must be one of {sorted(SCOPE_FIELDS)} with an instruction")
        elif not _ts(t.get("fields"), 1) or any(f not in SCOPE_FIELDS[scope] for f in t["fields"]):
            errors.append(f"revision_targets[{i}]: fields must name the field paths to change, within scope {scope}: "
                          f"{sorted(SCOPE_FIELDS[scope])}")
    lessons = _dicts(data.get("lessons") or []) or []
    if verdict == "abandon" and not lessons:
        errors.append("abandon needs >= 1 lesson")
    for i, lesson in enumerate(lessons):
        if lesson.get("kind") not in {"failure_mode", "subsumption", "anti_pattern", "blocking", "expectation"} or not _t(lesson.get("text")):
            errors.append(f"lessons[{i}]: kind failure_mode|subsumption|anti_pattern|blocking|expectation and text required")
    return errors


@tolerant
def validate_revision(revised, notes, base, audit, refs, phase1):
    errors = validate_candidate(revised, refs, phase1, "revised_candidate")
    if not isinstance(revised, dict):
        return errors
    targets = _dicts((audit or {}).get("revision_targets") or []) or []
    applied = _dicts((notes or {}).get("applied"))
    indices = [a.get("target_index") for a in applied or []]
    if applied is None or not all(type(i) is int for i in indices) or sorted(indices) != list(range(len(targets))):
        return errors + [f"revise_notes.json needs one applied entry per revision target, each with target_index "
                         f"0..{len(targets) - 1}, change and fields"]
    changed = changed_fields(base, revised)
    if not changed:
        errors.append("revised_candidate.json is identical to the audited candidate; apply the revision targets")
    claimed = set()
    for a in applied:
        t = targets[a["target_index"]]
        if not _t(a.get("change")) or not isinstance(a.get("fields"), list):
            errors.append(f"applied[{a['target_index']}]: change (text) and fields (list) required")
            continue
        if str(a["change"]).startswith("skipped"):
            continue
        outside = [f for f in a["fields"] if f not in (t.get("fields") or [])]
        if outside:
            errors.append(f"applied[{a['target_index']}]: changed {outside}, which target {a['target_index']} does not name")
        unchanged = [f for f in a["fields"] if f not in changed]
        if unchanged:
            errors.append(f"applied[{a['target_index']}]: says it changed {unchanged}, but they are unchanged")
        claimed |= set(a["fields"])
    silent = sorted(changed - claimed)
    if silent:
        errors.append(f"revised_candidate changed {silent} without an applied entry that names them")
    if set(bindings(revised)) != set(bindings(base)):
        errors.append("the set of closed gaps changed; choosing different gaps is a new attempt, not a revision")
    if applied and all(str(a.get("change", "")).startswith("skipped") for a in applied):
        errors.append("every revision target was skipped; apply them, or the audit should have abandoned")
    return errors


@tolerant
def validate_card(card, final, refs):
    if not isinstance(card, dict):
        return ["idea_card.json missing or not an object"]
    errors = []
    for f in ("abstract_draft", "core_claim", "feasibility", "plain_summary"):
        if not _t(card.get(f)):
            errors.append(f"idea_card.{f} required")
    errors += [f"idea_card.{f} must be copied unchanged from the final candidate" for f in CARD_COPIED if card.get(f) != (final or {}).get(f)]
    errors += [e for e in resources_errors(card, refs, "idea_card") if "copied verbatim" in e]
    motivation = card.get("motivation") if isinstance(card.get("motivation"), dict) else {}
    if not all(_t(motivation.get(k)) for k in ("why_prior_stopped", "stakes")):
        errors.append("idea_card.motivation needs why_prior_stopped and stakes")
    for f in ("sub_claims", "method_flow"):
        if not _ts(card.get(f), 1):
            errors.append(f"idea_card.{f} must be a non-empty list of strings")
    covered = {}
    for i, e in enumerate(_dicts(card.get("expectation_coverage") or []) or []):
        if e.get("expectation_id") not in refs.expectations or e.get("status") not in COVERAGE or not _t(e.get("how")):
            errors.append(f"expectation_coverage[{i}]: known expectation_id, status {'|'.join(sorted(COVERAGE))}, how")
        covered[e.get("expectation_id")] = e.get("status")
    missing = [e for e in refs.required_expectations() if e not in covered]
    if missing:
        errors.append(f"expectation_coverage omits required expectations {missing}")
    concerns = _dicts(card.get("reviewer_concerns") or []) or []
    for i, c in enumerate(concerns):
        if not _t(c.get("concern")) or not _t(c.get("response")) or c.get("source") not in {"audit", "coherence", "expectation", "collision"}:
            errors.append(f"reviewer_concerns[{i}]: concern, response, source audit|coherence|expectation|collision")
    open_rows = [e for e, s in covered.items() if s in {"gap", "partial", "challenged"}]
    if open_rows and not any(c.get("source") == "expectation" for c in concerns):
        errors.append(f"expectations {open_rows} are partial/gap/challenged but no reviewer concern with source expectation names them")
    ks = card.get("kill_switch") if isinstance(card.get("kill_switch"), dict) else {}
    if not all(_t(ks.get(k)) for k in ("condition", "action")):
        errors.append("kill_switch needs condition and action")
    land = card.get("domain_landscape") if isinstance(card.get("domain_landscape"), dict) else {}
    if not isinstance(land.get("cards"), list) or any(c not in refs.cards for c in land["cards"]) or not _t(land.get("timing")):
        errors.append("domain_landscape needs a list of known cards (may be empty) and timing")
    return errors


@tolerant
def validate_decision(data, audit=None):
    if not isinstance(data, dict) or data.get("decision") not in {"pursue", "park", "kill"} or not _t(data.get("rationale")) \
            or data.get("decided_by") not in {"model", "human"}:
        return ["decision.json needs decision pursue|park|kill, rationale, decided_by model|human"]
    if data["decision"] == "park" and not _t(data.get("revisit_conditions")):
        return ["park needs revisit_conditions"]
    if data["decision"] == "pursue" and threat_kind(audit) in {"subsumes", "same_mechanism"}:
        return [f"pursue is forbidden: the audit found prior work that {threat_kind(audit).replace('_', ' ')}s this idea; park or kill"]
    return []
