# Retrieval authoring and B02 replay

Date: 2026-10-17. Scope: `research-retrieve`, its three adapted method references,
the stdlib search adapter and its CLI. This record separates source adaptation,
model response behavior, deterministic tests and live-service observations.

## Baseline and reason for authoring

Read [baseline.md](baseline.md) before drafting the skill. B02's contextual baseline
already said “arXiv 429 表示这条检索没有完成” and “新颖性仍未确定”; it was **PASS**.
The evaluator inherited the earlier design discussion. It was not a fresh blind
baseline, and no failure is inferred from it.

The author read the installed Superpowers `writing-skills/SKILL.md` and its
`test-driven-development` / `writing-good-tests` references. The baseline did not
justify a claim that new prohibitions improve reasoning. The user nevertheless
explicitly requested a detailed, usable migration of the research assets and an
executable local+arXiv interface. This skill therefore packages a reference and
execution contract, rather than claiming to repair an observed B02 reasoning
failure. No nonexistent RED response or improvement percentage is reported.

## Source adaptation

The author inspected current RS intent/relevance/pattern-summary prompts, phase-0
navigator and full-text selection, Paper Search relevance/model-recall sections,
and Scoop Check's complete method. Adapted references preserve useful passages:

| Reference | Retained content | Explicit changes |
|---|---|---|
| `intent-recognition` | Broad/method/problem/solution views, concrete object, named papers, alias reasoning | Optional query roles, separate cross-field channel, plain keywords, local+arXiv |
| `relevance-and-reading` | Original-question alignment, conservative triage, abstract uncertainty, deciding passages | Topic/use separated; no taxonomy/full-text gate or universal method-first ranking |
| `collision-check` | Four comparison dimensions, assumptions, body-level mechanism comparison, one-sentence delta | No overlap-count novelty score, no empty→novel inference, future benefits remain predictions |

The original files are retained in `vendor/research-studio/` and linked from the
adapted references. They are archive material, not instructions to activate old
models, connectors, fixed panels, run directories or seven-stage dispatch.

## B02 skill-enabled text replay

Scenario: arXiv returned HTTP 429, the local query completed empty, a cross-domain
paper was nominated, and the user needs a novelty judgment before a deadline.

After reading the new skill, the author produced this response:

> 当前查新仍未确定。本地这条关键词查询完成但无命中；arXiv 被限流，因此它的覆盖没有完成。我会保留这两个不同状态，不即时重试，也不把合并后的零命中写成“没有先行工作”。
>
> 跨领域论文先保留为机制线索：核对它的原始身份和版本，再阅读决定对应关系的方法/假设段落；异领域不构成剔除理由。来源支持的源领域结论，与当前目标代码能否满足其前提分开记录。
>
> 在剩余预算内，用已知原始论文页、已有本地文件或明确的引用链核对这个承重点；不自动启用其他聚合服务。若候选机制/适用条件仍不清楚，就交付最近邻的已核差异、未核部分、查询范围及来源失败。到截止时间停止，下一轮只补缺口，不重跑全部文献流程。
>
> 记录实际检索报告为 material，把候选 novelty 主张的 finding 记为 unknown；如果没有读到论文正文，material 不能伪称包含正文证据。回流到方法构造的是具体操作对应、适用条件和未决问题，而不是新颖性分数。

Self-assessment: the response uses the specified default sources, preserves source
failure versus empty, keeps cross-domain leads, separates identity/support/transfer,
specifies bounded return and uses actual record kinds. This is **one author replay**,
not an independent subagent evaluation or matched baseline-versus-skill trial.
The baseline already expressed the central safeguards. The observed addition is
interface specificity, not demonstrated scientific-quality improvement.

## Executed checks

The adapter's first twelve behavior tests were written before implementation;
all twelve failed with the explicit “search adapter has not been implemented”
assertion. After implementation they passed. Additional defect-focused tests were
run red before fixes for incomplete HTTP bodies, output overwriting the configured
index, incomplete Atom entries and null local metadata.

Final command at authoring completion:

```bash
python -m unittest discover -s open-scientist/tests -p test_search.py -v
```

Result: **18 tests passed**. Fixtures use real temporary SQLite FTS5 databases.
Only the external HTTP boundary is replaced by Atom/error fixtures. The B02 test
executes actual orchestration and returns:

```json
{
  "local_status": "empty",
  "arxiv_status": "rate_limited",
  "papers": [],
  "evidence_status": "retrieval_only",
  "coverage_partial": true
}
```

A separate temporary-store check using `open_scientist.records.Store` accepted
these exact kinds and references: project `b02-project@1`, candidate
`b02-candidate@1`, material `b02-search@1`, assessment `b02-finding@1` with
`judgment: unknown` on the candidate's `novelty` claim. Its material explicitly
described an offline fixture, not real literature. Temporary records were removed
with the temporary directory. This checks schema compatibility, not scientific
source verification or MCP-host installation.

Live observations:

- Actual local index: `memory selection|vision language action`, years 2024–2026,
  max-papers 3, returned metadata/PDF references in approximately 0.013 seconds.
  Query/display truncation was exposed in coverage. No PDF was copied or opened.
- Actual arXiv endpoint: `diffusion watermark`, years 2024–2026, max-papers 2,
  timeout 8, scheduling budget 10, returned `timeout` in approximately 9.8 seconds.
  The adapter reported partial coverage. Live retrieval success is **unverified**;
  only parsing and transport failure behavior are validated by fixtures.

## Limits and next evaluation

The skill is 208 lines, with detailed adapted references loaded on demand.
Line count, link checks and source preservation establish packaging, not research
quality. A future fresh-context evaluation should use real source fixtures and
matched budgets, checking which decisive passages are actually read, whether
cross-domain conditions are traced to target code, and whether only affected
records are revisited. This authoring pass does not establish those outcomes.
