# Open Scientist overlay for RS Phase 1 (bottleneck_identify)

Read this together with `bottleneck_identify.txt`. Where they conflict, THIS file wins.

1. **The bottleneck is given, not chosen.** `phase0/mainline_first.json` (`final`) holds the project's mainline and ≤2 branches, formulated by the mainline layer from measured facts. This run targets ONE of them: the one named on the `TARGET:` line of `phase0/user_query.txt` (default: the mainline).
   - Set `bottleneck_statement` to that target's claim, in its own words. Tighten the wording if needed, but do NOT replace it with a different bottleneck.
   - If the literature shows the target is already solved or mis-stated, keep it anyway and put that evidence in a top-level `target_dispute` field (one paragraph, with arXiv ids). The mainline changes only through the mainline layer, never inside Phase 1.
2. **Rule 12 (structural-property / class-over-instance framing) is optional.** Abstract to a class only when that does not change the next experiment. Default: the minimal sufficient statement of the target.
3. **Measured, setting-specific gaps are admissible.** A gap may come from a measured fact of this project (source = FACTS) even when no retrieved paper names it. For such gaps the `method_lineage` position is used for regression context only, never as an admission gate. Still cite the closest papers.
4. **Gap fields.** Every entry of `what_phase_0_did_not_address[]` adds `gap_id` (G1, G2, …), `mainline_relation` (`target` | `other_branch:<which>` | `unrelated`) and `source` (`literature` | `facts` | `k31`).
5. **One run = one bottleneck.** Gaps belonging to another branch are listed with `mainline_relation=other_branch` and left for that branch's own run; do not merge them into this run's anchor.
