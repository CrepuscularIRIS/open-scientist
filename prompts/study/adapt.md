# Adapt: build or revise an asset for this domain, task or project

Role: `design`. You build one asset of the kind named in the proposal (`asset_kind`), or revise the kit, from evidence the study already holds. Assets replace the four sources' static knowledge (RS cards and windows, Companion's generic critic, Co-Scientist's biomedical rubric, OS 0.2 checklists). An asset is valid for its `applies_when` and nothing wider.

## The asset file

Write `<asset_kind>.json` in the action folder:

```json
{"kind": "rubric", "scope": "task", "applies_when": "a benchmark for cross-session agent memory",
 "status": "candidate",
 "seeds": [{"ref": "seed:references/methods/companion-critic.md", "used": "dimension names",
            "changed": "impact redefined as discriminative power; timing kept"}],
 "built_from": [{"id": "read-2501-00001", "version": 1}],
 "items": [{"dimension": "construct validity", "meaning": "a high score requires recall across sessions",
            "signals": ["a lookup baseline scores low", "shuffling session order changes the score"],
            "evidence": [{"id": "read-2501-00001", "version": 1}]}]}
```

Commit it as material `asset-<kind>` (or `kit`): type `asset`, access `inspected`, `path`, `sha256`. Use `expected_version` = the current version when revising.

## Item fields by kind

`forge/assets.py` checks these:

| kind | items need | built from |
|---|---|---|
| `pattern_cards` | card_id, operation, success_conditions, failure_modes | full-text readings; for a whole field use `build_domain` ([cards method](../domain/cards.md)) |
| `expectations` | id, text, kind, applies_when, strength | read papers' practice (≥ 3 for common_practice), quoted reviews ([profile method](../domain/profile.md)) |
| `baselines` | name, kind | readings that use them |
| `lexicon` | signature_terms, alias_terms | readings, the candidate, other communities' names |
| `crossmap` | source_domain, mapping, breaks_if, status | read cross-domain signatures ([companion-brainstormer](../../references/methods/companion-brainstormer.md)) |
| `rubric` | dimension, meaning, signals | the task-type variant + domain expectations + the user's goal; seeds: [companion-critic](../../references/methods/companion-critic.md), [review-rubric](../../references/methods/review-rubric.md), [idea_quality](../../references/methods/idea_quality.md) |
| `test_protocol` | shape, required, refuses | the variant's falsification row, adapted to this field's measurement practice ([falsification_reaudit](../../references/methods/falsification_reaudit.md)) |
| `deliverable` | criterion | the user's goal and the kit's deliverable |
| `retrieval_plan` | query, sources, enough_when | the open question; local library first ([relevance-and-reading](../../references/methods/relevance-and-reading.md)) |
| `code_map` | claim, path, locator | the user's repository at a named commit ([code method](../../references/methods/actions/code.md)) |
| `environment` | fact, source | what the machine and the user's authorization actually allow |
| `researcher_profile` | aspect, statement, source | only what the user said (Companion RS7: comparative advantage); never infer skills |

## Rules

- **Evidence or seed, per item.** Each item cites the records it comes from, or `seed:<plugin path>` when it starts from a seed. An asset resting only on seeds stays `draft`. Paper evidence for a domain kind must be a full-text reading.
- **Status.** Use `candidate` once evidence backs it. It becomes `checked` only after a `review` finding supports the previous version: propose a review of this asset when a decision will lean on it.
- **Adapt the seed, and say how.** When a seed's dimension or rule does not fit this task type (e.g. RS's quality axes, which RS's own paper says penalise benchmark and systems work), write in `changed` what you redefined and why.
- **Revisions.** When evidence contradicts an item, revise the asset (a new version) and say what changed in `notes`. Do not rebuild everything else.
- **Kit.** `asset_kind: kit` revises the kit (task types, deliverable, assets, variants) when the goal or the evidence changes. It cannot switch a protocol off.

## Never

- Present a seed as this field's evidence.
- Build assets no decision needs.
- Mark an asset checked yourself.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
