"""Validators for idea-run artifacts, part 1: what an idea may cite and how a candidate is shaped.

Contracts: prompts/idea/contracts.md. The citation gate is `validate_candidate`:
every card, gap, paper, signature, expectation and cross-domain map an idea
cites must exist in the pinned domain version or the run's collision pool, and
a premise marked `grounded` must rest on material that was actually read in
full. Cards are material, not a template: a gap may be closed with zero, one or
several cards. The user's budget cap is copied from run.json and never changes;
the model's cost estimate may. Audit, revision, card and decision gates live in
forge/review_gates.py. Every validator tolerates malformed input and reports it.
"""
from __future__ import annotations

import re
from pathlib import Path

from forge.util import read_json, read_jsonl, tolerant  # noqa: F401 (re-exported)

NO_BUDGET = "not specified"
REQUIRED_STRENGTH = {"common_practice", "observed_in_reviews"}
PATTERN_STATUS = {"candidate_pattern", "checked_for_scope"}
NESTED = ("falsification", "resources")
FALSIFICATION_KEYS = ("experiment", "metric", "direction", "load_bearing_variable", "negative_control")
# What a coherence patch may touch: the written procedure, never the idea's claim, novelty surface or tests.
COHERENCE_ALLOWED = {"core_mechanism", "mechanism_steps", "gap_closure.how_closed", "signature_terms", "alias_terms"}
CROSSMAP = re.compile(r"^crossmap\[(\d+)\]$")
THREATS = {"none", "partial_overlap", "subsumes", "same_mechanism"}


def _t(v):
    return isinstance(v, str) and v.strip() != ""


def _ts(v, lo=0, hi=None):
    return isinstance(v, list) and all(_t(x) for x in v) and len(v) >= lo and (hi is None or len(v) <= hi)


def _dicts(v):
    return v if isinstance(v, list) and all(isinstance(x, dict) for x in v) else None


class Refs:
    """Everything an idea may cite: the frozen domain plus the run's collision pool, and what counts as read."""

    def __init__(self, domain_dir, collision_papers=None, budget=None):
        d = Path(domain_dir)
        self.papers = {f"arxiv:{p['arxiv_id']}" for p in read_jsonl(d / "papers.jsonl")}
        self.collision = ({f"arxiv:{p['arxiv_id']}" for p in read_jsonl(collision_papers)}
                          if collision_papers and Path(collision_papers).exists() else set())
        self.sigs, self.read_sigs, self.read_papers = set(), set(), set()
        for path in (d / "readings").glob("*.json"):
            for s in (read_json(path) or {}).get("signatures", []):
                self.sigs.add(s.get("sig_id"))
                if s.get("verified") == "fulltext":
                    self.read_sigs.add(s.get("sig_id"))
                    self.read_papers.add(f"arxiv:{str(s.get('sig_id')).split('#')[0]}")
        cards = (read_json(d / "cards" / "index.json") or {"cards": []})["cards"]
        self.cards = {c["card_id"] for c in cards}
        self.pattern_cards = {c["card_id"] for c in cards if c.get("status") in PATTERN_STATUS}
        exp = (read_json(d / "profile" / "expectations.json") or {"expectations": []})["expectations"]
        self.expectations = {e["id"]: e.get("strength") for e in exp}
        self.crossmap = len((read_json(d / "profile" / "crossmap.json") or {"maps": []})["maps"])
        self.budget = budget  # the user's authorized cap (run.json), None when unknown to the caller

    def known(self, ref):
        if not isinstance(ref, str):
            return False
        m = CROSSMAP.fullmatch(ref)
        if m:
            return int(m[1]) < self.crossmap
        return (ref in self.papers or ref in self.collision or ref in self.sigs or ref in self.cards
                or ref in self.expectations)

    def read_evidence(self, ref):
        """Material read in full: a full-text signature, a paper with one, or a pattern card built from them."""
        return ref in self.read_sigs or ref in self.read_papers or ref in self.pattern_cards

    def required_expectations(self):
        return sorted(e for e, s in self.expectations.items() if s in REQUIRED_STRENGTH)


def _unknown(refs, items, where, errors):
    if items is not None and not isinstance(items, list):
        errors.append(f"{where}: refs must be a list")
        return
    for ref in items or []:
        if not refs.known(ref):
            errors.append(f"{where}: unknown ref {ref!r} (not in the domain version or collision pool)")


def threat_kind(audit):
    return (((audit or {}).get("checks") or {}).get("paper_threat") or {}).get("kind")


def bindings(candidate):
    """{gap_id: frozenset(card_ids)}: which gaps are closed, by which cards; order is not meaning."""
    return {g.get("gap_id"): frozenset(g.get("card_ids") or [])
            for g in _dicts((candidate or {}).get("gap_closure") or []) or []}


def _closure_changes(base, new):
    """Field paths changed inside gap_closure, compared per gap_id (a pure reorder is no change)."""
    def by_gap(c):
        return {g.get("gap_id"): g for g in _dicts((c or {}).get("gap_closure") or []) or []}
    if bindings(base) != bindings(new):
        return {"gap_closure"}
    old, cur = by_gap(base), by_gap(new)
    out = set()
    for gid, entry in cur.items():
        for k in set(entry) | set(old.get(gid, {})):
            if k != "card_ids" and entry.get(k) != old.get(gid, {}).get(k):
                out.add(f"gap_closure.{k}")
    return out


def changed_fields(base, new):
    """Field paths that differ: top-level keys, `falsification.<k>` / `resources.<k>`, and `gap_closure.<k>` per
    gap when every (gap, cards) binding is the same (`gap_closure` itself when a binding changed)."""
    base, new = base or {}, new or {}
    out = set()
    for k in set(base) | set(new):
        if base.get(k) == new.get(k):
            continue
        if k in NESTED and isinstance(base.get(k), dict) and isinstance(new.get(k), dict):
            out |= {f"{k}.{s}" for s in set(base[k]) | set(new[k]) if base[k].get(s) != new[k].get(s)}
        elif k == "gap_closure":
            out |= _closure_changes(base, new)
        else:
            out.add(k)
    return out


@tolerant
def validate_phase1(data, refs):
    if not isinstance(data, dict):
        return ["phase1.json missing or not an object"]
    errors = []
    if data.get("state") not in {"proceed", "do_not_generate"}:
        return ["phase1.state must be proceed or do_not_generate"]
    if data["state"] == "do_not_generate":
        return [] if _t(data.get("do_not_generate_reason")) else ["do_not_generate needs do_not_generate_reason"]
    if not _t(data.get("bottleneck_statement")):
        errors.append("bottleneck_statement required")
    if not isinstance(data.get("refs"), list) or len(set(map(str, data["refs"]))) < 2:
        errors.append("refs needs >= 2 distinct refs")
    _unknown(refs, data.get("refs"), "phase1.refs", errors)
    adjacent = _dicts(data.get("closest_adjacent") or [])
    if adjacent is None:
        errors.append("closest_adjacent must be a list of {ref, residue} objects")
        adjacent = []
    for i, a in enumerate(adjacent):
        if not _t(a.get("residue")):
            errors.append(f"closest_adjacent[{i}]: residue required")
        _unknown(refs, [a.get("ref")], f"closest_adjacent[{i}]", errors)
    gaps = _dicts(data.get("gaps"))
    if gaps is None or not 1 <= len(gaps) <= 4:
        errors.append("gaps must be 1..4 objects")
        gaps = gaps or []
    ids = [g.get("gap_id") for g in gaps]
    if len(set(map(str, ids))) != len(ids) or not all(isinstance(i, str) and re.fullmatch(r"G\d+", i) for i in ids):
        errors.append("gap_id values must be unique like G1, G2")
    for g in gaps:
        if not _t(g.get("text")) or not _t(g.get("stakes")):
            errors.append(f"{g.get('gap_id')}: text and stakes required")
        _unknown(refs, g.get("refs"), f"{g.get('gap_id')}.refs", errors)
    return errors


def resources_errors(data, refs, name):
    res = data.get("resources") if isinstance(data.get("resources"), dict) else {}
    errors = []
    if not _t(res.get("authorized_limit")) or not _t(res.get("estimate")):
        errors.append(f"{name}.resources needs authorized_limit (the user's cap from run.json) and estimate (yours)")
    elif refs.budget is not None and res["authorized_limit"] != refs.budget:
        errors.append(f"{name}.resources.authorized_limit must be copied verbatim from run.json budget "
                      f"({refs.budget!r}); only the user raises a cap")
    return errors


@tolerant
def validate_candidate(data, refs, phase1, name="candidate"):
    if not isinstance(data, dict):
        return [f"{name}.json missing or not an object"]
    errors = []
    for f in ("title", "hook", "core_mechanism"):
        if not _t(data.get(f)):
            errors.append(f"{name}.{f} required")
    errors += resources_errors(data, refs, name)
    gap_ids = {g.get("gap_id") for g in _dicts((phase1 or {}).get("gaps") or []) or []}
    closure = _dicts(data.get("gap_closure"))
    if not closure:
        errors.append(f"{name}.gap_closure must be a non-empty list of objects")
        closure = []
    for i, g in enumerate(closure):
        if g.get("gap_id") not in gap_ids:
            errors.append(f"gap_closure[{i}]: gap_id {g.get('gap_id')!r} not in phase1 gaps")
        if not isinstance(g.get("card_ids"), list) or any(c not in refs.cards for c in g["card_ids"]):
            errors.append(f"gap_closure[{i}]: card_ids must be a list (empty for a new mechanism) of domain card ids")
        if not _t(g.get("how_closed")):
            errors.append(f"gap_closure[{i}]: how_closed required")
    if not _ts(data.get("mechanism_steps"), 1):
        errors.append(f"{name}.mechanism_steps must be a non-empty list of strings")
    premises = _dicts(data.get("premises"))
    if not premises:
        errors.append(f"{name}.premises must be a non-empty list of objects")
    for i, p in enumerate(premises or []):
        if not _t(p.get("text")) or p.get("status") not in {"grounded", "untested"}:
            errors.append(f"premises[{i}]: needs text and status grounded|untested")
        elif p["status"] == "grounded":
            if not p.get("refs"):
                errors.append(f"premises[{i}]: grounded premise needs refs")
            unread = [r for r in p.get("refs") or [] if refs.known(r) and not refs.read_evidence(r)]
            if unread:
                errors.append(f"premises[{i}]: grounded needs material read in full; {unread} were not (an unread, "
                              "abstract-only or collision paper is a lead: mark the premise untested)")
        _unknown(refs, p.get("refs"), f"premises[{i}]", errors)
    nb = data.get("naive_baseline") if isinstance(data.get("naive_baseline"), dict) else {}
    if not _t(nb.get("naive")) or not _t(nb.get("why_insufficient")) or nb.get("branch") not in {"false_premise", "naive_suffices", "disbelieved"}:
        errors.append("naive_baseline needs naive, why_insufficient, branch false_premise|naive_suffices|disbelieved")
    fz = data.get("falsification") if isinstance(data.get("falsification"), dict) else {}
    if not all(_t(fz.get(k)) for k in FALSIFICATION_KEYS if k != "direction") \
            or fz.get("direction") not in {"increase", "decrease", "no_change"}:
        errors.append("falsification needs experiment, metric, direction, load_bearing_variable, negative_control")
    diff = _dicts(data.get("differentiation"))
    if not diff:
        errors.append("differentiation needs at least one {ref, delta} object")
    for i, d in enumerate(diff or []):
        if not _t(d.get("delta")):
            errors.append(f"differentiation[{i}]: delta required")
        _unknown(refs, [d.get("ref")], f"differentiation[{i}]", errors)
    ap = data.get("almost_prior") if isinstance(data.get("almost_prior"), dict) else {}
    if not _t(ap.get("missed_step")):
        errors.append("almost_prior.missed_step required")
    _unknown(refs, [ap.get("ref")], "almost_prior", errors)
    if not _ts(data.get("signature_terms"), 2, 8) or not _ts(data.get("alias_terms"), 1, 8):
        errors.append("signature_terms needs 2..8 and alias_terms 1..8 phrases")
    for i in data.get("crossmap_used") or []:
        if type(i) is not int or not 0 <= i < refs.crossmap:
            errors.append(f"crossmap_used: index {i!r} out of range")
    alts = _dicts(data.get("alternatives_considered"))
    if not alts or len(alts) < 2 or any(not _t(a.get("title")) or not _t(a.get("why_not_chosen")) for a in alts):
        errors.append("alternatives_considered needs >= 2 entries with title and why_not_chosen")
    return errors


@tolerant
def validate_coherence(data, run_dir, refs, phase1, candidate):
    if not isinstance(data, dict):
        return ["coherence.json missing or not an object"]
    errors = []
    if data.get("verdict") not in {"pass", "patched"} or not _t(data.get("trace")):
        errors.append("coherence needs verdict pass|patched and a trace")
    if data.get("naive_comparison") not in {"confronts_obstacle", "equivalent_to_naive", "n_a"}:
        errors.append("naive_comparison must be confronts_obstacle|equivalent_to_naive|n_a")
    for i, c in enumerate(_dicts(data.get("claims") or []) or [{}]):
        if c and c.get("grade") not in {"established", "conditional", "overclaim", "empirical"}:
            errors.append(f"claims[{i}]: grade must be established|conditional|overclaim|empirical")
    blocking = _dicts(data.get("blocking") or [])
    if blocking is None:
        errors.append("blocking must be a list of objects")
    for i, b in enumerate(blocking or []):
        if not all(_t(b.get(k)) for k in ("finding", "evidence", "structural_requirement")):
            errors.append(f"blocking[{i}]: finding, evidence, structural_requirement required")
    refined = Path(run_dir) / "refined_candidate.json"
    if data.get("verdict") == "patched":
        r = read_json(refined)
        errors += validate_candidate(r, refs, phase1, "refined_candidate")
        if isinstance(r, dict):
            outside = sorted(changed_fields(candidate, r) - COHERENCE_ALLOWED)
            if outside:
                errors.append(f"refined_candidate changed {outside}; a coherence patch may only change "
                              f"{sorted(COHERENCE_ALLOWED)} (the procedure), never the claim, bindings, tests or novelty surface")
    elif refined.exists():
        errors.append("refined_candidate.json exists but verdict is pass; remove it or mark patched")
    return errors
