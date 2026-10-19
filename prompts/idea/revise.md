# Revise — apply the audit's revision targets

Role: `design`. Runs only when `audit.json` has `verdict: "revise"`. You resolve the attacks the audit identified; you do not identify new ones. Keeping attack (audit) and resolution (revise) in separate calls is what removes self-answering bias, so: do not re-judge the verdict, do not question whether a target is "really" the right fix, do not re-search literature, do not polish anything no target asks for.

## Inputs

- The **canonical candidate**: `refined_candidate.json` when the coherence gate patched, else `candidate.json`. Always revise this file — starting from `candidate.json` when a refined one exists silently drops the coherence repairs.
- `audit.json` — `revision_targets[]` are your instructions, in order; `checks`, `blocking_dispositions` and `verdict_rationale` are context for what each target means. Consult them only to understand a target.
- `phase1.json` — the gaps; `gap_closure[].gap_id` must keep pointing at real gaps.
- The cited card files under `D/cards/` — for a `card` target, read the new card's operation, success conditions and failure modes before rebinding.

## Scopes and fields

Each target names its `scope` and the exact `fields` (field paths) you may change for it. Change nothing else. The validator compares the revised candidate with the canonical one field by field: a changed path no `applied[]` entry claims, a claimed path outside its target's `fields`, or a claimed path that did not change is refused.

| `scope` | field paths a target may name | never |
|---|---|---|
| `tactical` | `title`, `hook`, `core_mechanism`, `mechanism_steps`, `gap_closure.how_closed`, `premises`, `naive_baseline`, `differentiation`, `almost_prior`, `signature_terms`, `alias_terms`, `crossmap_used`, `alternatives_considered`, `resources.estimate` | card bindings; `falsification` |
| `card` | `gap_closure` (rebind one entry's `card_ids` to cards in `D/cards/index.json`, or to `[]`), `gap_closure.how_closed`, `core_mechanism`, `mechanism_steps`, `premises`, `signature_terms`, `alias_terms`, `crossmap_used` | which gaps are closed; `falsification` |
| `falsification` | the named `falsification.<key>` paths, `resources.estimate` | anything not named |
| `feasibility` | `falsification.experiment`, `resources.estimate`, `mechanism_steps` | the variable, control, metric and direction |

`resources.authorized_limit` is the user's cap and is in no scope. There is no gap-level scope: a target that needs different gaps cannot be fixed here; record it as skipped. If every target would be skipped, the revision is refused (the audit should have abandoned). An unchanged candidate is refused.

## Falsification and feasibility targets

- A `falsification` target repairs structure or strengthens: name the one `load_bearing_variable`; make `negative_control` intervene on it and predict that the **downstream metric** returns to baseline (never the variable's own value); name the minimal experiment or direction the text left implicit; strike an `invented` numeric bar; or add a baseline or control arm. When the target names `falsification.metric` or `.direction`, the audit judged the old one did not measure the claim; change exactly what it says.
- A `feasibility` target asks for a **cheaper test that still discriminates**: fewer tasks, seeds or scale, a smaller model, a proxy dataset, while the load-bearing variable, negative control, metric and direction stay as written. Update `resources.estimate` with real numbers. If no cheaper test can still separate the candidate from its naive alternative, skip it and say why.
- You do not judge your own rewrite: every valid revision is searched for collisions again and audited a second time (round 2, where revise is not available) against the same hard floor.

## Rules

1. **One target, one note.** Address every `revision_targets[]` entry one by one, in audit order, each with exactly one `applied[]` entry (`target_index` = its position) — including skipped ones. Do not merge two targets into one note or drop a target silently. Put a card rebinding before the re-alignment edits it causes.
2. **Minimal edit.** Change only what the target's `instruction` requires; leave every other field byte-identical to the canonical candidate.
3. **Skips** start `change` with `skipped:` and one of `already satisfied` (quote where), `out of scope` (gap-level change), or `no discriminating cheaper test` — and the reason; their `fields` is `[]`.
4. **Terms.** If a change alters what the mechanism is and the target allows the term fields, regenerate `signature_terms`/`alias_terms` and claim them (collision reruns on the revised mechanism). If it does not allow them, say so in `change`; the round-2 audit weighs it.
5. **Contract.** The output is a full candidate under the `candidate.json` contract: statuses and branches from their enums, `premises[].refs` non-empty for `grounded`, `alternatives_considered` ≥ 2, every cited ref resolvable in `D/` or `collision/papers.jsonl`. Cite only what exists; never invent a card id, paper or signature.

## Output 1: `revised_candidate.json`

The **full** candidate (not a patch), same contract as `candidate.json`, with every non-skipped target applied.

## Output 2: `revise_notes.json`

```json
{"applied": [
  {"target_index": 0, "change": "mechanism_steps[2]: added tie rule 'lowest index wins'.", "fields": ["mechanism_steps"]},
  {"target_index": 1, "change": "negative_control now ablates the load-bearing variable and predicts the outcome metric returns to the baseline arm.", "fields": ["falsification.negative_control"]},
  {"target_index": 2, "change": "skipped: out of scope — gap-level change; the round-2 audit weighs it.", "fields": []}
]}
```

`change` names what concretely changed in one or two sentences; `fields` lists the paths it changed. `applied` has one entry per revision target.

## Never

- Re-judge the audit's verdict, add attacks, or answer a target the audit did not raise.
- Change a field path no target names, or `resources.authorized_limit` at all.
- Change which gaps are closed, or `card_ids` outside a `card` target.
- Revise from `candidate.json` when `refined_candidate.json` exists.
