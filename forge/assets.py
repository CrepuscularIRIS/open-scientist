"""Adaptive assets: what this domain knows and what this task needs, rebuilt per study from evidence.

An asset file (`.forge/studies/<s>/assets/<kind>/v<N>.json`) has one envelope:

    {"kind", "scope": "domain|task|project", "applies_when", "status": "draft|candidate|checked|needs_revision",
     "seeds": [{"ref": "seed:<path in the plugin>", "used": ..., "changed": ...}],
     "built_from": [{"id", "version"}],            # record refs: the materials it was derived from
     "items": [{..., "evidence": [refs]}]}

and is registered as a material record of type "asset" (path + sha256), so the study's records say which
version of which asset a decision used. A seed (RS cards, Companion dimensions, Co-Scientist rubric, OS methods)
may start an asset but is never its authority: an item backed only by seeds keeps the asset at draft, and an
asset becomes `checked` only through a review finding on it. Paper evidence for a domain asset must have been
read in full (protocol 1). The full domain bundle from `build_domain` is the deep form of the domain-scope kinds.
"""
from __future__ import annotations

from pathlib import Path

from forge.kit import PLUGIN

STATUS = ("draft", "candidate", "checked", "needs_revision")
# kind -> scope, the item fields each item must carry (besides evidence), the method that builds it, its use.
KINDS = {
    "pattern_cards": ("domain", ("card_id", "operation", "success_conditions", "failure_modes"),
                      "prompts/domain/cards.md", "construct, review: moves this field already has, with where they fail"),
    "expectations": ("domain", ("id", "text", "kind", "applies_when", "strength"),
                     "prompts/domain/profile.md", "review: what a reviewer of this claim will ask"),
    "baselines": ("domain", ("name", "kind"), "prompts/study/adapt.md", "plan_test: what a fair comparison includes"),
    "lexicon": ("domain", ("signature_terms", "alias_terms"), "prompts/domain/profile.md", "collision vocabulary"),
    "crossmap": ("domain", ("source_domain", "mapping", "breaks_if", "status"), "prompts/domain/profile.md",
                 "construct: other fields' solved versions, with what must hold to transfer"),
    "rubric": ("task", ("dimension", "meaning", "signals"), "prompts/study/adapt.md",
               "review: the dimensions this task type is judged on, with their meaning here"),
    "test_protocol": ("task", ("shape", "required", "refuses"), "prompts/study/adapt.md",
                      "plan_test: what counts as a discriminating test for this task type"),
    "deliverable": ("task", ("criterion",), "prompts/study/adapt.md", "report: when this study is done"),
    "retrieval_plan": ("task", ("query", "sources", "enough_when"), "prompts/study/adapt.md",
                       "retrieve: where to look first and when to stop looking"),
    "code_map": ("project", ("claim", "path", "locator"), "prompts/study/adapt.md",
                 "diagnose, plan_test: where each claimed behaviour lives in the code"),
    "environment": ("project", ("fact", "source"), "prompts/study/adapt.md", "plan_test: what the machine can run"),
    "researcher_profile": ("project", ("aspect", "statement", "source"), "prompts/study/adapt.md",
                           "decide: comparative advantage and constraints (Companion RS7)"),
}
STRICT_PAPER_KINDS = {"pattern_cards", "expectations", "crossmap", "baselines"}


def seed_ok(ref):
    return isinstance(ref, str) and ref.startswith("seed:") and (PLUGIN / ref[5:]).is_file()


def _is_ref(v):
    return isinstance(v, dict) and set(v) == {"id", "version"}


def validate_asset(data, store, expected_kind=None):
    """Errors for an asset file against its kind and the record store (refs must exist)."""
    if not isinstance(data, dict):
        return ["asset must be an object"]
    errors = []
    kind = data.get("kind")
    if kind not in KINDS or (expected_kind and kind != expected_kind):
        return [f"asset.kind must be {expected_kind or 'one of ' + str(sorted(KINDS))}"]
    scope, fields, _, _ = KINDS[kind]
    extra = set(data) - {"kind", "scope", "applies_when", "status", "seeds", "built_from", "items", "notes"}
    if extra:
        errors.append(f"asset: unknown fields {sorted(extra)}")
    if data.get("scope") != scope:
        errors.append(f"asset.scope must be {scope} for {kind}")
    if not isinstance(data.get("applies_when"), str) or not data["applies_when"].strip():
        errors.append("asset.applies_when required: the domain, task or project this asset is valid for")
    if data.get("status") not in STATUS:
        errors.append(f"asset.status must be one of {list(STATUS)}")
    seeds = data.get("seeds", [])
    if not isinstance(seeds, list) or any(not isinstance(s, dict) or not seed_ok(s.get("ref")) or not s.get("used")
                                          for s in seeds):
        errors.append("asset.seeds: each {ref: 'seed:<existing plugin path>', used, changed}")
    built_from = data.get("built_from", [])
    if not isinstance(built_from, list) or not all(_is_ref(r) for r in built_from):
        errors.append("asset.built_from must be a list of {id, version} record refs")
        built_from = []
    for r in built_from:
        if store.find(r["id"], r["version"]) is None:
            errors.append(f"asset.built_from: no record {r['id']}@{r['version']}")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return errors + ["asset.items must be a non-empty list"]
    seed_only = True
    for i, item in enumerate(items):
        at = f"items[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{at}: must be an object")
            continue
        missing = [f for f in fields if item.get(f) in (None, "", [])]
        if missing:
            errors.append(f"{at}: {kind} items need {list(fields)}; missing {missing}")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{at}: evidence required (record refs, or seed:<path> for a seeded starting point)")
            continue
        for ev in evidence:
            if isinstance(ev, str):
                if not seed_ok(ev):
                    errors.append(f"{at}: {ev!r} is not an existing seed:<path>")
                continue
            if not _is_ref(ev):
                errors.append(f"{at}: evidence entries are {{id, version}} refs or seed:<path>")
                continue
            seed_only = False
            record = store.find(ev["id"], ev["version"])
            if record is None:
                errors.append(f"{at}: no record {ev['id']}@{ev['version']}")
            elif record["kind"] != "material" or record["payload"].get("access") not in {"fulltext", "inspected", "executed"}:
                errors.append(f"{at}: evidence {ev['id']} must be material read in full, inspected or executed "
                              f"(it is a {record['kind']} with access {record['payload'].get('access', 'n/a')})")
            elif kind in STRICT_PAPER_KINDS and record["payload"].get("type") == "paper" \
                    and record["payload"].get("access") != "fulltext":
                errors.append(f"{at}: {ev['id']} was not read in full ({record['payload'].get('access')}); a lead cannot "
                              "support a domain asset (protocol 1)")
    if seed_only and data.get("status") in {"candidate", "checked"}:
        errors.append("an asset resting only on seeds stays draft: seeds are starting points, not evidence")
    return errors


def asset_path(study_dir, kind, version):
    return Path(study_dir) / "assets" / kind / f"v{version}.json"
