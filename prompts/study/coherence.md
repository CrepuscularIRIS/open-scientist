# Coherence: execute the candidate on paper (fresh context)

Role: `review`. Never run this in the context that wrote the candidate. The proposal's `subject` is the candidate. Method: [coherence_trace](../../references/methods/coherence_trace.md) (RS T1–T5: formalize the dataflow; numeric dry run with an executed stdlib script; degenerate probes; claim grading; an independent naive baseline under the same constraints). [Forge coherence](../idea/coherence.md) has the depth floor and repair rules.

## Commit

- **A material for each executed script and its output:** type `output`, access `executed`, `path` the script output file, `sha256`. These are evidence; hand arithmetic is `unexecuted` and is not.
- **Findings on the candidate's claims** (the candidate's claim ids):
  - judgment supported, partial or contradicted from executed evidence; else unknown;
  - `rationale` with the computed numbers;
  - `scope` naming the instance.
  
  A blocking structural defect is a contradicted finding with the evidence and the structural requirement in `rationale`.

Do not patch the candidate here. A defect becomes a finding, and `evolve` answers it.

## Never

- Report an anomaly without its computed number.
- Rest a contradicted finding on an instance-contingent result alone.
- Soften a blocking finding.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
