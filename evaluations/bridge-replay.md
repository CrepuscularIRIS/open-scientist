# Synthetic bridge replay: verification scope

Date: 2026-10-17. This is a deterministic local integration test of record/code/
test/report handoffs. It is **not** an autonomous research evaluation, a model
benchmark, or a comparison against the three source plugins.

## What is exercised

The executable [fixture](../examples/bridge_replay.py) creates small Python
programs and data inside an explicitly selected fresh project, runs them with
the current Python interpreter, records their actual stdout/stderr/exit codes,
and links observations and assessments to exact question/candidate/activity
versions. It writes a report from the exercised fixture, preserving the
distinction between executed work and proposed next work.

| Invariant | Observable check |
|---|---|
| A code fact can change a research question | Stored frame exists at step 7 while lookup at step 8 misses; old question remains readable after Q revision |
| A valid counterexample remains available after H revision | The universal shifted-query claim has an actual finite witness; its contradiction targets the old candidate version |
| Execution failure is not scientific failure | Separate process exits 7; its activity is failed, with no automatically generated contradiction |
| T revision does not rewrite a historical prediction | Old activity's plan remains byte-for-byte equal between planned and completed versions; revised test has its own ID and stays planned |
| Specification repair changes the method before the view | Actual NameError leads to a finding and candidate v2; card v1 remains unchanged, and card v2 identifies candidate v2 |
| Feedback consumption and resource decisions are explicit | Exact feedback gets a disposition with output references; PARK and its revisit condition survive a specification repair |
| The fixture cannot quietly overwrite a research store | A populated store is rejected before fixture artifacts are created |

## TDD evidence

Three tests were written before the executable fixture. All three initially
failed because the replay did not exist. The implementation was then exercised
against the same tests, including real subprocess output and SQLite reads.
Run `python -m pytest tests/test_bridge_replay.py -q` for the current result.

Observed locally on 2026-10-17: the three replay tests passed. The combined
records, real MCP/CLI, and replay suite passed **27 tests**. A separate default
CLI run created a fresh temporary project and returned actual exit codes 0 for
the counterexample, 7 for the unavailable dataset, and 1 for the undefined
normalizer. These failures are expected fixture observations, not test failures.

An integration review separately found that revising a feedback ID could hide
an unconsumed earlier instruction from context. A regression test demonstrated
the loss, then the runtime was corrected to retain every unconsumed exact
feedback version and its dependencies. Only a disposition targeting that exact
version consumes or explicitly supersedes it.

## What remains unverified

- The bridge choices are authored by the fixture, not chosen by a model. This
  does not show that an Agent will recognize the same trigger or choose the
  correct bridge without guidance.
- The data are synthetic, the scripts are tiny, and the counterexample concerns
  a deliberately overbroad finite retrieval claim. No real scientific result,
  average-performance effect, cross-domain transfer, or research gain is shown.
- Revised candidate B has a new **unexecuted** test. Revised candidate C has a
  new definition and code that have **not been executed**. Neither is declared
  scientifically supported by the fixture.
- There is no GPU, network retrieval, background supervisor, host installation,
  or multi-process research orchestration in this demonstration.
- Future behavioral evaluation needs actual host-Agent runs and matched inputs,
  tools and budgets. It must measure evidence-grounded decisions, not record
  count, card length, or whether this fixture completed.
