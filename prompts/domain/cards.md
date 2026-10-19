# D6 — Merge signatures into domain pattern cards

Role: `design`. You turn read signatures into this domain's own pattern cards: reusable operations with the conditions under which they work and fail. These replace ResearchStudio's static 15+31 cards for this domain. A card is knowledge about existing work, **not** a research proposal.

## Inputs

- `brief.md`.
- `clusters.suggested.json` — groups suggested by word overlap (TF-IDF, average linkage) and near-duplicate pairs. **A suggestion only**: shared words are not a shared mechanism.
- `readings/*.json` — every signature with its information access, conditions, evidence and failure boundary.
- `lessons.jsonl` (optional) — lessons from idea runs (dead ends, counterexamples, subsumed mechanisms), each with a `key`. A lesson that contradicts a card must show up in that card's `counterexamples` or `failure_modes`, cited as `lesson:<key>`: an observation from a run is cited as what it is, never as a paper.
- `previous/cards/` (optional) — the version being revised. Keep `card_id`s stable for cards that still describe the same operation; record what changed in `merge_notes`.

## How to merge

1. Start from the suggested groups, then **split or join by mechanism**: two signatures belong together only if they share the operation *and* the information it uses *and* the conditions it needs. Different preconditions that predict different outcomes → separate cards, or one card with explicit sub-conditions.
2. A signature goes into at most one card. Anything that fits nowhere goes into `unassigned` — that is fine and informative.
3. `status`: `case` (members from one paper, or from papers read only as abstracts), `candidate_pattern` (members from ≥ 2 papers read in full text; abstract-only members may be listed but do not count), `needs_revision` (a lesson or counterexample undermines it). Never mark `checked_for_scope` here; review does that.
4. Every success condition, failure mode and counterexample cites the `sig_id`s (or `lesson:<key>`) it comes from. Failure modes come from stated failure boundaries, limitations, negative results and lessons — never from imagination.
5. Cross-domain signatures may form cards of their own; note in `transfer_notes` what would have to hold in the target domain.

## Output 1: `cards/index.json`

```json
{
  "cards": [
    {
      "card_id": "K01-latent-rollout-pruning",
      "title": "Prune imagined rollouts by value uncertainty",
      "status": "candidate_pattern",
      "operation": "verb phrase of the shared move",
      "members": ["2501.01234#s1", "2406.05555#s2"],
      "success_conditions": [{"text": "...", "refs": ["2501.01234#s1"]}],
      "failure_modes": [{"text": "...", "refs": ["2406.05555#s2"]}],
      "counterexamples": [],
      "transfer_notes": "What must hold for this move to transfer; 'n/a' if none.",
      "file": "cards/K01-latent-rollout-pruning.md"
    }
  ],
  "unassigned": ["2502.09999#s1"],
  "merge_notes": "Which suggested groups were split or joined and why."
}
```

`card_id` format: `K` + two or three digits + `-` + short lowercase slug.

## Output 2: one Markdown file per card

`cards/<card_id>.md` with exactly these sections (add sub-bullets freely):

```markdown
# <title>
## Operation
## When it works
## When it fails
## Counterexamples
## Sources
```

`## Sources` lists each member `sig_id` with the paper title and the reading locator.

## Never

- Force every signature into a card, or force cards into ResearchStudio's old 15-pattern vocabulary.
- Report how often a card succeeds; outcome statistics come later, from labels, deterministically.
