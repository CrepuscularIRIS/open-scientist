# Changelog

## 0.3.0 — 2026-10-19

A redesign. The Forge engine (developed as `research-forge`) replaces 0.2's skill-by-skill workflow and auto mode.

### Added
- **Study loop** (`forge next --study`):
  - The agent proposes one action against the open question.
  - Code checks its inputs, current versions, authorization, preconditions and repeats before running it.
  - Commits are validated against the action's contract and the protocols.
- **Adaptive assets** (`forge/assets.py`): domain kinds (cards, expectations, baselines, lexicon, crossmap), task kinds (rubric, test protocol, deliverable, retrieval plan) and project kinds (code map, environment, researcher profile).
  - Built from evidence, versioned, and marked `checked` only after a review.
  - The original RS, Companion, Co-Scientist and OS assets are seeds.
- **Kit and task-type variants** (`references/variants/`): mechanism, theory, diagnosis, analysis, benchmark, system, empirical reveal, scaling, survey, replication.
- **Executed tests** (`run_test`): the planned command runs with recorded commit, exit code and hashed outputs; interruptions are recorded and never silently rerun.
- **Protocols** (`references/protocols.md`): 13 fixed rules, each naming where it is enforced.
- **Strict RS chains inside a study**: `build_domain` (domain build to a frozen version) and `idea_run` (bottleneck → generate → coherence → collision → audit → revise → card → decision), absorbed into the records.
- **Standard-library record store and MCP server**: no pydantic/mcp install, with read-only MCP tools (`forge_next`, `records_*`, `papers_search`). `forge records import` reads 0.2 stores.
- **OpenReview connector** (optional outcome labels and review text) and the arXiv corpus collector.

### Changed
- The 11 skills of 0.2 are now entries that forward to `open-scientist`. Their method texts are kept whole in `references/methods/actions/`.
- The MCP server is renamed `research-records` → `open-scientist`. Writes go only through study commits.

### Removed
- `workflow.py` / auto-loop and the fixed seven-item acceptance list (replaced by the study loop's completion rules and no-progress stop).
- The pydantic/mcp runtime dependencies.
