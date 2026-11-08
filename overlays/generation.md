# Open Scientist overlay for RS Phase 2.1 + 2.2 (ideate_select + ideate_generate)

Read this together with the RS prompts. Where they conflict, THIS file wins.

1. **Anchor order is fixed.** `phase1/soundness_gaps.json` → `order` lists the gaps that passed the independent soundness verifier, mainline first. Choose the anchor gap from the FIRST entry whose `mainline_relation` is `target`; pick a later one only if the first is structurally unusable, and say why in `selection_rationale`. Gaps that were killed are not in the list, so never revive them.
2. **Solution angles.** `phase1/solution_lens.json` ranks solution angles (innovation types A–O) for each admitted gap. Use it as an extra preference when you choose the RS pattern / sub_pattern: prefer a pattern that realises a top-ranked angle. If an angle has no matching RS pattern (types B, F, H, K, M, N, O), use the closest parent pattern with `sub_pattern: null` (parent-only fit) and name the angle in `selection_rationale`. The RS pattern rules (sibling/companion contracts, no quota) still apply.
3. **Intervention object.** `intervention_object` must name the concrete code object the method changes (module / function / input / loss term). The card-level soundness verifier reads it against the code.
4. **Keep the claim minimal.** State the mechanism on the target bottleneck itself. Do not widen it to a class of problems unless that changes the experiment.
