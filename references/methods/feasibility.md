# Operator: feasibility

Keep the scientific claim, change how it would be tested, so that it can
actually be done with what exists now.

## When it applies

- The mechanism is plausible and novel but the proposed experiment needs a
  method, model or reagent that does not exist or is out of reach.
- The proposed test is informative but cannot run under the actual constraints.
- The session's constraints (timescale, available assays, sample access) rule
  out the stated approach.

Read constraints in the exact project version and resource evidence. Feasibility is judged against those, not against an unlimited lab.

## Procedure

1. State what makes the original infeasible, precisely. Not "it is hard" but
   "it needs single-cell resolution in live tissue over 72 hours".
2. Survey what current methods can do for this specific measurement. Search;
   do not rely on memory of what was possible.
3. Propose the alternative route to the same discriminating result. It may be a
   different readout, a different model system, a proxy measurement with a
   stated validity argument, or a staged design where a cheap step gates an
   expensive one.
4. Confirm the new route still distinguishes this hypothesis from the leading
   alternative. A feasible experiment that no longer discriminates is a loss,
   not a gain.
5. State the resource envelope: rough time, rough cost, what has to be in the
   lab already.

## Failure mode

Weakening the test to fit the budget. If the cheaper experiment cannot separate
this hypothesis from its rival, you have made it easier to run and useless to
run. Say the hypothesis is not currently testable rather than recording a
feasible non-test.

The core claim must survive unchanged. If you find yourself editing the
mechanism to fit the method, classify that as H evolution, using scoped revision or simplification as appropriate; it is not
a fixed-H feasibility change.

## Active bridge: fixed H, changed T

Quote the exact H and the rival prediction that the expensive or unavailable test was intended to distinguish. State which elements must remain invariant for a cheaper route to answer the same question.

A different model system, subset or proxy changes the evidential scope. Explain the bridge from the proxy observation to the target claim, its assumptions, and a cheap check that could reveal bridge failure. If that bridge is unsupported, label the plan exploratory rather than equivalent validation.

Distinguish a resource cap chosen by the user, a measured resource cost, and an unverified estimate. Missing budgets remain unknown. A smaller sample or weaker model may reduce cost while losing the contrast; that is a tradeoff to evaluate, not automatic success.

An execution failure and a valid negative counterexample are different. Diagnose the failed run's cause before treating it as a test result. If the fixed H is already refuted in scope, a cheaper positive test cannot restore it; propose an explicit H revision or stop.

## Minimal input and output

Inputs are the exact H reference, old T, rival predictions, real resource constraints, existing code/data access, and any run failures or contrary findings. Read applicable materials rather than relying on a feasibility score.

Output a new T plan with the same H, changed measurement route, validity assumptions, matched controls, prospective costs and stopping rule. Keep the earlier plan and execution history. An unexecuted plan can be revised; a rerun or replacement for a started activity needs a new activity ID.

Do not create a new candidate merely because its experiment became cheaper. If mechanism, claim or problem assumptions changed, record H/Q evolution explicitly before claiming that the new test answers the same question.

## Local recheck and stopping

Apply [the shared falsification definition](falsification_reaudit.md) to check that competing predictions remain distinguishable. Check actual executability through research-code or research-test using the available authorized tools.

If no affordable informative route exists, return a park recommendation to research-decide with a concrete revisit condition, such as access to a named readout. Do not substitute a feasible non-test to keep the workflow moving.

## Provenance and replacements

Adapted closely from [Co-Scientist feasibility operator](../../vendor/co-scientist/plugin/skills/evolving-hypotheses/reference/feasibility.md). The original core procedure and failure-mode paragraphs are retained with the targeted substitutions above.

Replaced tournament/cluster/tool coupling with exact project and parent references, explicit Q/H/T classification, scoped evidence and local recheck. Added bridge inputs, expected outputs, structural requirements and stopping conditions. No fixed panel, score, agent count or automatic execution is required.
