# Interpret: what the raw result says, typed

Role: `review`. The proposal's `subject` is the completed or failed activity. Read its raw outputs (the `out-NNN-*` materials) and the plan's predictions. Method: [OS test](../../references/methods/actions/test.md) steps 5–6.

## Type the result

Choose one `result_type`, with its judgment:

| result_type | when | judgment |
|---|---|---|
| `execution_failure` | OOM, missing input, wrong metric script, config not loaded | unknown for the claim; a finding on the measurement |
| `mechanism_refuted` | under legal conditions the output contradicts the claim | contradicted |
| `not_discriminating` | both explanations fit the output | unknown; change T next |
| `partial_support` | fits H and excludes the named rival, in a limited scope | partial |
| `supported` | fits H, excludes the rival, within the plan's scope | supported |
| `unknown` | outputs missing, provenance unclear, noise too large | unknown |

## Commit

Findings on the subject the plan tested (`q` or the candidate's claim id):
- `evidence`: the run's output materials (required for supported, partial and contradicted);
- `rationale`: the observed numbers against both predictions;
- `scope`: exactly what was run.

A failed run limits what is known. It never becomes a scientific rejection.

## Next

Say what the result changes, in `rationale`:
- a refuted premise of `q` → diagnose and revise `q`;
- a refuted claim → evolve or decide;
- not discriminating → a new plan.

## Never

- Average a legal counterexample with a failed run.
- Re-interpret predictions after seeing the output.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
