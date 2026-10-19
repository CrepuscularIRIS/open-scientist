"""A study's kit: the task-specific adaptation plan, and its policy (who decides, what may be spent).

The kit is written at intake by the agent and revised by `adapt` when the goal or the evidence changes. It
chooses task types, the deliverable, the asset kinds the next decisions need, and the protocol variant in force
for each task type. It cannot switch a protocol off: the contract has no field for that, and unknown fields are
refused. Variants (references/variants/<type>.md) say how a protocol applies to a task type, never whether.
"""
from __future__ import annotations

from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
VARIANTS = PLUGIN / "references" / "variants"
TASK_TYPES = ("mechanism", "theory", "diagnosis", "analysis", "benchmark", "system", "empirical_reveal", "scaling",
              "survey", "replication")
DELIVERABLES = {
    "plan": "a candidate (H), a test plan for it and a review finding, with no unresolved contradicting finding",
    "verified_execution": "a completed test activity and an interpret finding on its result",
    "diagnosis": "a finding with a judgment on the question's premise under doubt",
    "idea_card": "an idea card from the strict RS chain (idea_run), absorbed into the records",
    "exploration": "a report of what was learned, whenever it answers the question",
    "report": "a report rendered from the records",
}
SHORTHAND = {"auto": ("local", "auto"), "web": ("web", "auto"), "hitl": ("local", "human_decisions"),
             "web+hitl": ("web", "human_decisions")}
ALLOW_KEYS = ("network_search", "web_egress", "training", "paid")
DEFAULT_ALLOW = {"network_search": True, "web_egress": False, "training": False, "paid": False}


def policy_for(mode="auto", budget=None, wall_clock_min=30, max_actions=40):
    """The two independent settings behind a mode name, plus the user's authorization."""
    if mode not in SHORTHAND:
        raise ValueError(f"mode must be one of {sorted(SHORTHAND)}")
    channel, participation = SHORTHAND[mode]
    return {"channel": channel, "participation": participation,
            "budget": {"authorized": (budget or "").strip() or "not specified", "gpu_hours": 0, "api_usd": 0,
                       "wall_clock_min": wall_clock_min},
            "allow": {**DEFAULT_ALLOW, "web_egress": channel == "web"}, "max_actions": max_actions}


def mode_name(policy):
    for name, pair in SHORTHAND.items():
        if pair == (policy.get("channel"), policy.get("participation")):
            return name
    return "auto"


def validate_policy(policy):
    errors = []
    if not isinstance(policy, dict):
        return ["policy must be an object"]
    if policy.get("channel") not in {"local", "web"} or policy.get("participation") not in {"auto", "human_decisions"}:
        errors.append("policy needs channel local|web and participation auto|human_decisions")
    budget = policy.get("budget") or {}
    if not isinstance(budget.get("authorized"), str) or any(
            not isinstance(budget.get(k), (int, float)) or budget[k] < 0 for k in ("gpu_hours", "api_usd", "wall_clock_min")):
        errors.append("policy.budget needs authorized (text) and non-negative gpu_hours, api_usd, wall_clock_min")
    allow = policy.get("allow") or {}
    if set(allow) != set(ALLOW_KEYS) or not all(isinstance(allow[k], bool) for k in ALLOW_KEYS):
        errors.append(f"policy.allow needs booleans {list(ALLOW_KEYS)}")
    if policy.get("channel") == "web" and not allow.get("web_egress"):
        errors.append("the web channel sends packets off this machine: it needs allow.web_egress true (a person's choice)")
    if type(policy.get("max_actions")) is not int or policy["max_actions"] < 1:
        errors.append("policy.max_actions must be a positive integer")
    return errors


def variant_path(task_type):
    return VARIANTS / f"{task_type}.md"


def validate_kit(kit, asset_kinds):
    """Structure of kit.json. Only the kit's own fields exist; there is none for disabling a protocol."""
    if not isinstance(kit, dict):
        return ["kit.json must be an object"]
    errors = []
    extra = set(kit) - {"task_types", "deliverable", "assets", "variants", "notes", "rationale"}
    if extra:
        errors.append(f"kit.json: unknown fields {sorted(extra)} (protocols cannot be switched off or renamed)")
    types = kit.get("task_types")
    if not isinstance(types, list) or not types or any(t not in TASK_TYPES for t in types):
        errors.append(f"kit.task_types must be a non-empty list from {list(TASK_TYPES)}")
        types = []
    if kit.get("deliverable") not in DELIVERABLES:
        errors.append(f"kit.deliverable must be one of {sorted(DELIVERABLES)}")
    if not isinstance(kit.get("rationale"), str) or not kit["rationale"].strip():
        errors.append("kit.rationale required: why these task types and this deliverable, from the user's words")
    variants = kit.get("variants")
    if not isinstance(variants, dict) or set(variants) != set(types):
        errors.append("kit.variants must name one variant file per task type: {task_type: 'references/variants/<type>.md'}")
    else:
        for t, path in variants.items():
            if path != f"references/variants/{t}.md" or not variant_path(t).is_file():
                errors.append(f"kit.variants.{t} must be references/variants/{t}.md")
    assets = kit.get("assets")
    if not isinstance(assets, list) or not all(isinstance(a, dict) for a in assets):
        errors.append("kit.assets must be a list of {kind, why} (may be empty)")
    else:
        for i, a in enumerate(assets):
            if a.get("kind") not in asset_kinds or not isinstance(a.get("why"), str) or not a["why"].strip():
                errors.append(f"kit.assets[{i}]: kind from {sorted(asset_kinds)} and why (which decision needs it)")
    return errors
