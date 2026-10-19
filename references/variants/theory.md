# Variant: theory

A theorem, bound, equivalence or impossibility result.

This variant changes how the protocols in [protocols.md](../protocols.md) apply to this task type. It never switches one off. Seeds below are starting vocabulary; the study's `rubric` and `test_protocol` assets are rebuilt from this field's evidence (see [design](../../docs/design.md) §2–3).

| Protocol | How it applies |
|---|---|
| Falsification (3) | Proof obligations listed as lemmas, each with the case that would break it; a **counterexample search** (small instances, degenerate cases, a constructed adversary) is the discriminating test. A rival is the strongest weaker statement that would explain the same evidence. |
| Coherence (7) | T1 formalization and T4 claim grading carry the weight; theorem-shaped claims are at best `conditional` until proved; T5 may be `n_a` for a pure equivalence (say why). T2 executes numeric checks of the statement on small instances. |
| Review | Assumption strength (are they ever true in the target setting), proof feasibility (what prerequisite is missing), whether the result is already a special case of a known one (collision on alias terms with long windows). |
| Test execution | A script that searches for a counterexample or checks the bound numerically is a run_test; a found counterexample refutes a universal claim, a passing search supports nothing beyond its instances. |
| Deliverable | A plan whose test is the counterexample search and the proof outline, or a report of a refutation. |

Rubric seeds: Companion feasibility (proof-feasibility), RS T4 grading. Watch for: guarantee words without their assumptions; a favourable instance presented as a proof.
