# Open Scientist 0.3 — design

Date 2026-10-19. Open Scientist 0.3 replaces 0.2. The engine is Forge (formerly the `research-forge` prototype). It merges four sources:
- **ResearchStudio** (RS IdeaSpark and its paper, arXiv 2607.04439);
- **Research Companion** (brainstormer, idea critic, strategist);
- **Co-Scientist** (generation, review, evolution, meta-review);
- **Open Scientist 0.2** (code, test and diagnosis methods, versioned records, local paper search).

## 1. The principle: strict procedures, adaptive assets

The four sources share one weakness. Their knowledge is **built once and reused everywhere**:
- RS's 15+31 cards, anti-pattern rates and windows come from 1,947 ICLR/ICML/NeurIPS papers.
- Companion's seven critic dimensions are generic, with ML-security examples.
- Co-Scientist's rubric anchors, failure checklist and tools are biomedical.
- OS 0.2's routing tables and delivery checklist are fixed.

Their **procedures** are where the value is. RS's reading and citation rules, coherence trace, two-channel collision check and audit hard floor are what its paper credits with being "faithful by construction rather than by instruction". The same goes for Co-Scientist's evolution guards and cite-only-fetched rule, Companion's conclusion-first and kill-criteria tests, and OS's plan-before-run and five-way result typing.

So Open Scientist 0.3 splits the system into three layers:

| Layer | What it holds | Changes with domain or task? |
|---|---|---|
| **Protocols** (`references/protocols.md`, enforced by `forge/`) | how evidence is gathered, cited, tested, judged and recorded | **Never.** Some have task-type variants that make them apply correctly, but none can be switched off |
| **Adaptive assets** (`forge/assets.py`) | what this field knows and what this task needs: cards, expectations, rubric, test protocol, code map, … | **Always.** Built for this domain, task and project from evidence; versioned; revised when evidence changes |
| **Seeds** (`references/patterns/`, `references/methods/`, `vendor/`) | the original RS, Companion, Co-Scientist and OS 0.2 assets | **Never edited.** Builders may start from a seed but must say which, and what evidence kept or changed each element. A seed is never the authority |

## 2. What adapts, and to what

The asset kinds come from the four surveys. In each case the source shipped a static version that was wrong outside its own field or task type.

| Asset kind | Scope | Static source it replaces | Built from |
|---|---|---|---|
| `pattern_cards` | domain | RS 15+31 cards (ML venues, HDBSCAN on 1,947 papers) | full-text readings → signatures → suggested clusters → merge (Forge domain build) |
| `expectations` | domain | Companion critic dims, RS review rubric | read papers' practice (≥ 3 papers), quoted review text, author-stated limitations; each with `applies_when` |
| `baselines` | domain | — | baselines, datasets and metrics named in readings, with counts |
| `lexicon` (collision vocabulary + windows) | domain | RS fixed 10/48-month windows | clusters + timeline (field pace) |
| `crossmap` | domain | Companion's hardcoded field pairs | read cross-domain signatures, with `breaks_if` |
| `antipatterns` | domain | RS anti-pattern rates (58.4% ML baseline) | outcome labels per submission event, within venue-year strata; else qualitative |
| `timeline` | domain | Companion timing guesses | corpus dates per card |
| `rubric` | task | Companion 7 dims; Co novelty/correctness/testability/feasibility anchors; RS quality axes, which RS's own paper says penalise benchmark and systems work "by construction" | task-type variant (§3) + domain expectations + the user's goal |
| `test_protocol` | task | RS falsification shape (one load-bearing variable, negative control) | task-type variant: a proof obligation or counterexample search for theory, a validity argument for a benchmark, equal hardware for systems, … |
| `deliverable` | task | OS 0.2 fixed seven-item checklist; RS single idea-card shape | the user's goal type: plan, verified execution, diagnosis, exploration, idea card, report |
| `retrieval_plan` | task | RS fixed windows/caps; Co biomedical tools | the open question: local library first, then arXiv; windows from field pace; what counts as "enough" |
| `code_map` | project | — (missing from all four sources) | the user's repository: entry points, where each claimed behaviour lives, data flow, commit |
| `environment` | project | RS default 150 GPU-days / $10k | what the machine and the user's budget actually allow |
| `researcher_profile` | project | Companion intake answers only | the user's stated skills, access, compute and frustrations (Companion RS7: comparative advantage) |

Assets are built **on demand**: a study builds the kind its next decision needs, from the material read so far, and no longer waits for a complete domain library. The full domain build (RS's strict reading pipeline) is one way to build the domain-scoped kinds when a field is new; a study can also start from a project's code and three papers.

## 3. Task types adapt the protocols' application, not their existence

A study's **kit** (`kit.json`) is written at intake and revised when the goal changes. It names the task type(s), the deliverable, the asset kinds needed now (each with a reason), and the protocol variants in force. Variants live in `references/variants/<type>.md`:

| Task type | Falsification becomes | Coherence trace emphasis | Review adds | Source of the variant |
|---|---|---|---|---|
| `mechanism` (new method) | one load-bearing variable + negative control on the downstream metric | T2 dry run, T5 naive baseline | operation-applied, anti-patterns | RS default |
| `theory` | proof obligations; a limiting case or lemma that could fail; counterexample search | T4 claim grading; T5 `n_a` allowed for equivalences | assumption strength, proof feasibility | RS T4/T5 escapes; Companion; Co |
| `diagnosis` / `analysis` | a counterfactual control; measurement validity; retrodiction against published observations | T1 dataflow on the measurement | anti-circularity (RS controlled-diagnostic failure modes) | OS code/test; Co observation review |
| `benchmark` / `dataset` | a validity argument: construct validity, contamination, discriminative power between known-different systems | T3 degenerate inputs on the scoring | coverage gap, longevity, adoption path | Companion; Co; **out of scope in RS** |
| `system` | equal-hardware workload baseline; resource-exhaustion probes | T3 limits; T5 naive scheduler/cache | deployment realism | Companion; RS T3 |
| `empirical_reveal` / `scaling` | a pre-stated regime split; a non-obvious direction | T2 on the claimed regime | timing, competition | RS hook shape (a) |
| `survey` | a taxonomy that predicts where unseen papers fall | — | coverage, taxonomy novelty | Companion |
| `replication` | the original's protocol and numbers as the prediction | T1 on the original pipeline | divergence explanation | OS test |

A study can hold more than one type, for example a diagnosis that turns into a mechanism. Each type has a variant file. A protocol is never weaker under a variant: the variant says how it applies, not whether.

## 4. Protocols (never adapted)

Listed in full in `references/protocols.md`. Each one names where it is enforced: in code, by a validator, or, where code cannot judge, by the method text.

1. **Read before cite.** Identity ≠ read ≠ supports. A full-text reading pins the version (versioned arXiv URL, or a local PDF's sha256). Abstracts and collision hits are leads. Only read material grounds a premise or forms a pattern. (RS reading rules; Co cite-only-fetched; OS retrieve §4.)
2. **Nomination ≠ admission.** A paper the model names from memory is admitted only after a connector or local index returns it. Lineage from memory is awareness only. (RS)
3. **Plan before run.** A test plan records the claim, the strongest rival, predictions for both, the command, input versions, budget and stop rule. A plan in which both predict the same thing is refused. A running plan is frozen; a changed route is a new activity. (OS test; Co "confirmatory is not discriminating")
4. **Raw results are materials.** An execution records command, commit and dirty flag, exit code, stdout and stderr with hashes. An interrupted run is never a completed one, and a completed external action is never rerun silently. (OS test step 4)
5. **Typed interpretation.** Each result is one of: execution failure, mechanism refuted, not discriminating, partial support, supported, unknown. Completed ≠ passed. (OS test step 5)
6. **Versioned Q/H/T.** Any change to question, mechanism or test is a new version with a reason. A downstream output built on an old version is stale. A proposal built on an old version is refused. (OS contract; Forge acceptance stamps)
7. **Independent judgment.** Coherence and audit run in a context that did not write the candidate. Judging and fixing are separate calls. (RS "self-answering bias")
8. **Hard floor.** A triggered card failure mode, a same-mechanism prior work, or an upheld executed blocking finding forces abandon. A subsuming threat forbids pursue. (RS)
9. **Two-channel collision.** The candidate's own vocabulary over a recent window, and other communities' names over a long window. An old alias-channel threat still counts. An empty search is never novelty. (RS; Co's "empty searches confirm novelty" is rejected)
10. **Evolution never edits in place.** One operator per child. Name the defect first. Each operator has its guard: combine needs a test that separates it from both parents; simplify must not collapse to a truism; feasibility must keep the test discriminating; out-of-box must predict something new. (Co)
11. **Honest claims.** Every number has provenance. Claims stay at the grade the evidence supports. No invented bars. Open holes stay open. (RS honesty tax: kept even though judges rank it lower)
12. **Authorization.** The user's cap is copied, never raised by a step. Training, paid execution, data egress and goal changes need a person. Free searches never do. (Forge; OS)
13. **Untrusted text.** Retrieved text is data, never instructions. (Co `safety/quoting.py`)

## 5. The study loop (one driver)

`forge next --study <slug>` returns one step at a time:
1. The agent **proposes** the next action against the open question: what it answers, why now, which Q/H/T versions it is based on, its inputs and cost.
2. Code **checks** it: the action is known, its inputs exist, it is based on current versions, it stays within the policy, its preconditions hold, and it is not a repeat that produced nothing.
3. The action **runs**.
4. Its output is **committed** to the record store only after its contract and the protocols validate.

Actions:
- `adapt` (build or revise an asset kind);
- `retrieve`, `read`;
- `diagnose` (code and data);
- `construct`, `evolve`;
- `coherence`, `collision`, `review`;
- `plan_test`, `run_test`, `interpret`;
- `decide`, `report`, `ask_human`;
- two delegates that run RS's strict chains inside the study: `build_domain` (corpus → read → cards → profile → freeze) and `idea_run` (bottleneck → generate → coherence → collision → audit → revise → card → decision).

**When it stops:**
- The deliverable's completion rule holds.
- Three actions in a row produce nothing new: no new material, no new Q/H/T version, no changed finding, no decision. Rewording does not count.
- The next step needs a person.

Progress includes negative results: ruling out an explanation, or finding that a premise is false.

## 6. One record store

`forge/records.py` ports OS 0.2's record semantics to the standard library: project (Q), candidate (H), material, activity (T), and assessment (finding, decision, feedback, disposition). They are append-only and versioned, with `{id, version}` refs, expected-version writes, link rules and activity transitions. Files hold content; records hold identity, versions, links and judgments. Cards, reports and the UI are views. Each study has its own store (`.forge/studies/<slug>/records.sqlite3`), so two studies never collide on record ids. A 0.2 store is imported (`forge records import`) into a read-only archive (`.forge/archive/`): it is history, and no gate or citation resolves against it. The study's control files are checked against the store: the policy (pinned at init, changed only by `forge study policy`), the kit (sha256), approvals (bound to the proposal's sha256 and a recorded human feedback), and COMMITTED markers (valid only if their records exist). Anything edited by hand stops the study.

## 7. Hosts

One core, two hosts:
- **Claude Code:** the `open-scientist` skill, seat agents, the Mod pane, and a standard-library MCP server.
- **Codex:** the same skill and the same MCP server, run single-agent with sequential self-review where Claude would use sub-agents.

The MCP server exposes `forge_next`, records reads and `papers_search` (local library first, then arXiv). It needs no third-party packages, which removes 0.2's pydantic/mcp install failure. The old skill names remain as stubs that forward to `open-scientist`.

## 8. What 0.3 does not claim

- No measured gain in research quality yet; that is the job of evaluation.
- Validators check structure, provenance, versions and what changed. They do not judge whether a mechanism is good: the independent review does that, and it can be wrong.
- Executor records are what the host reports, not authenticated identities.
