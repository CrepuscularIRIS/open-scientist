# Evolve: a child candidate that answers a named defect

Role: `design`. Evolution never edits in place. The proposal names:
- the `subject` candidate;
- the `defect` finding (what is wrong);
- one `operator`.

Methods: [OS evolve](../../references/methods/actions/evolve.md), [revise](../../references/methods/revise.md), [combine](../../references/methods/combine.md), [simplify](../../references/methods/simplify.md), [feasibility](../../references/methods/feasibility.md), [out-of-box](../../references/methods/out-of-box.md).

## Operators and their guards

These are Co-Scientist's, kept strict:

| operator | does | guard |
|---|---|---|
| `repair` | fixes the defect the finding names | the fix addresses that finding, not a nicer one |
| `combine` | merges two candidates (two parents) | names a test that separates the child from **both** parents; otherwise it is stapling |
| `simplify` | removes what the claim does not need | must not collapse to a truism; says what claim survives |
| `feasibility` | a cheaper test or mechanism | the test still discriminates; a feasible non-test is a loss |
| `out_of_box` | changes a premise | predicts something no current candidate predicts |
| `reframe` | restates the problem so the answer changes | ties to evidence that the old framing was wrong |

## Commit

One **new** candidate id:
- `parents` [the subject (+ the second parent for combine)];
- `operator`;
- `change_note`: the defect in one sentence, what changed, and which part of the parent survives;
- full `claims` / `predictions` / `rivals` for the child.

The child does not inherit the parent's review: it is reviewed again.

## Never

- Evolve without a defect you can state in one sentence.
- Apply two operators at once.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
