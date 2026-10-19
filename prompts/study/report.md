# Report: deliver what the study found, within its scope

Role: `review`. Runs only when the kit's deliverable completion rule holds (code checks). Methods:
- [OS report](../../references/methods/actions/report.md): statement typing, evidence spine, tense rules;
- [expand](../../references/methods/expand.md) and [derive_plain](../../references/methods/derive_plain.md): plain language, no new facts;
- [implementability_audit](../../references/methods/implementability_audit.md), for plans;
- the views in [references/templates/](../../references/templates/).

## The report (`report.md` in the action folder)

Rendered from records, not memory:
- the question as it now stands (and how it changed, from `q`'s history);
- each finding with its judgment, evidence and scope;
- what was ruled out;
- the decision, if one was made;
- what is still unknown, and the next decisive test.

For an idea card from `idea_run`, link the card file. Every claim cites the record it rests on.

## Commit

The report as material type `note`, access `inspected`, `path`, `sha256`.

## Never

- Add facts, numbers or mechanisms the records lack.
- Turn an unknown into a result.
- Pad a diagnosis into an idea.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
