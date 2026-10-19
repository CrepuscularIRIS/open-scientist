# Decide: pursue, refine, park or kill

Role: `gate`. When the study's participation is `human_decisions`, a person decides: show them the evidence summary and write their words with `decided_by: human`. Methods: [OS decide](../../references/methods/actions/decide.md), [companion-strategy](../../references/methods/companion-strategy.md) (triage, opportunity cost, scoop risk, excitement bias), [ranking](../../references/methods/ranking.md), and the user's `researcher_profile` asset when it exists.

## How

1. **Hard limits first.** A contradicted core claim, or same-mechanism prior work, is never pursue.
2. **Then weigh** the evidence on disk against the cost of the next decisive test:
   - what it costs, from the user's authorization, not your preference;
   - what the user can do (comparative advantage);
   - timing and scoop risk.
3. Prefer `pursue` when the next test is cheap and decisive, even under uncertainty. Ignore sunk effort.

## Commit

One decision on the subject:
- `decision`;
- `rationale` naming the findings it rests on;
- `evidence`;
- `revisit_when`: checkable conditions, required for park;
- `decided_by`.

## Never

- Decide for the person in a human-decisions study.
- Pursue against a hard limit.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
