# Review: an independent judgment of a claim, a candidate or an asset

Role: `audit`, in a fresh context. Methods:
- [OS review](../../references/methods/actions/review.md) (independent first review, revision re-check, adjudication);
- [critique](../../references/methods/critique.md) (RS audit: card failure modes, operation applied, anti-patterns, paper threat, falsification structure, expectations; the hard floor);
- [grounding](../../references/methods/grounding.md) (does each source support each claim, and in which direction);
- [refutation_recheck](../../references/methods/refutation_recheck.md);
- [companion-critic](../../references/methods/companion-critic.md) and [companion-strategy](../../references/methods/companion-strategy.md).

**Judge with this task's rubric.** If the kit's `rubric` asset exists, its dimensions and meanings replace the generic ones. Otherwise apply the variant's "Review adds" row and say that the rubric is not yet adapted.

## What to check

Check what the subject's next decision depends on, not everything:
- the sources: read material only, and in the right direction;
- the claims, against the executed evidence and the collision pool (both channels; an old alias-channel threat still counts);
- whether the falsification can kill the idea;
- the domain expectations, answered as met, unmet, not applicable or challenged, each with a reason.

**Hard floor:** a same-mechanism prior work, a triggered failure mode, or an upheld executed blocking finding means the candidate is contradicted. Say so plainly.

## Commit

- Findings on the subject (its claim ids for a candidate; a stated claim for an asset or `q`), with evidence (read, inspected or executed material) and scope.
- Feedback (source agent) for concerns that are not judgments.

A review of an asset that supports it is what lets a later `adapt` mark it `checked`.

## Never

- Re-argue an executed result without a concrete flaw in it.
- Fabricate a threat, or cite from memory.
- Score from taste.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
