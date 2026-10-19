# Construct: one buildable, falsifiable mechanism for the diagnosed problem

Role: `design`. Methods:
- [Forge generate](../idea/generate.md): divergence before committing; cards optional; the naive-baseline audit; premises ledger; falsification;
- [OS construct](../../references/methods/actions/construct.md) and [OS ideate](../../references/methods/actions/ideate.md);
- [companion-brainstormer](../../references/methods/companion-brainstormer.md): cross-field moves, strategic ignorance, the skeptical reader;
- [ideate_generate](../../references/methods/ideate_generate.md) and [ideate_select](../../references/methods/ideate_select.md).

For a full RS idea card with collision search and audit, propose `idea_run` instead.

## Procedure

1. Start from the current `q` and the findings on it. Construct only for a problem the evidence shows is real.
2. **Diverge before committing.** Consider at least three genuinely different directions:
   - in-domain moves (the `pattern_cards` asset if one exists; cards are material, not a template);
   - a cross-field map (`crossmap` asset), with its `breaks_if`;
   - challenging a shared assumption;
   - an alternative framing.
   
   Keep the best two others as `rivals` in the candidate.
3. **Conclusion first.** Can you write "we showed X, which means Y for Z"? If not, it is not ready.
4. **Naive-baseline audit.** State the simplest version of the mechanism, and why it fails here: a false premise, naive suffices (an honest increment), or disbelieved.

## Commit

One candidate:
- `problem` = the current `q` ref;
- `mechanism`, computable from the text;
- `claims` {id: claim}, each falsifiable;
- `assumptions`: load-bearing premises, each grounded (cite read material in `content` of a note material if needed) or marked untested;
- `predictions`: what will be observed if it works, and what the rival predicts;
- `rivals`: the strongest alternatives;
- `operator` construct.

## Never

- Build on a contradicted premise (code refuses it).
- Cite a paper the study has not read.
- Add a card or a component to look deeper.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
