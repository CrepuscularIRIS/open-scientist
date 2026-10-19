# Diagnose: is the problem real, where does it come from, what does the code actually do

Role: `design`. The method is in three texts, kept whole:
- [OS diagnose](../../references/methods/actions/diagnose.md): bottleneck as a failure ("under C, S cannot Y, shown as O"), nearest-neighbour residue, premise split into checkable parts;
- [OS code](../../references/methods/actions/code.md): claim to checkable statement, real entry points, information-availability and timing table, measurement audit, cheapest exclusion;
- [bottleneck_identify](../../references/methods/bottleneck_identify.md): RS phase-1 rules (failure, not missing cure; stakes; class over instance, honestly).

## Procedure

1. State the premise under doubt as checkable parts. For example, "memories are lost" splits into: lost at save; lost in storage; not retrieved; retrieved but not used; mis-measured.
2. **Read the actual code and data.** Look at entry points, configuration and logs, at a named commit. For each part, write what the code does and what would be observed if that part were the cause.
3. Run the cheapest exclusions first: a static fact, a log line, a one-line count. Anything that needs a real test run goes to `plan_test`. Do not run ad-hoc experiments here and present them as findings.

## Commit

- **Materials** for what you inspected: type `code` / `data` / `log`, access `inspected`, `path`, `sha256`, `locator` (file:line, commit).
- **Findings** on `q`, one per premise part:
  - `judgment` contested or unknown when it is not yet decided;
  - `supported` or `contradicted` only with inspected or executed evidence;
  - `scope` says exactly where it holds.
- **A new `q` version**, if the evidence changes the question and the proposal has `may_change: ["Q"]`. Keep the user's constraints, and write `change_note` (what the evidence changed). Stopping work on a false premise is progress.

## Never

- Treat a stack trace or a "running" status as proof of a cause.
- Change the user's hard constraints (that is `ask_human`).
- Propose a fix inside a diagnosis.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
