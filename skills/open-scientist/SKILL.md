---
name: open-scientist
description: Orchestrator for research idea generation and selection (Open Scientist 0.4). ResearchStudio idea_spark is the backbone (retrieval, bottleneck diagnosis, generation, gauntlet, card); research-taste selection layers are inserted around it — innovation-lens after Phase 0, gap-code-filter after Phase 1, problem-selection after Phase 3 — plus a three-bottleneck mainline for journal method papers. Use when the user wants to pick a research direction, draw an idea card, rank candidate methods or cards, or continue an IdeaSpark run with the selection layers.
---

# Open Scientist 0.4：RS 出卡 + 方法论选择

**一句话**：ResearchStudio（RS）的 idea_spark 负责工程推导：检索、诊断、生成、审查、写卡。Open Scientist 在 RS 的阶段之间插入**选择层**，把 research taste 显式化，避免每轮由 AI 随意挑选方向。
- **来源**：ResearchStudio（MIT）、Anthropic life-sciences 的 scientific-problem-selection（Apache-2.0，基于 Fischbach & Walsh, Cell 2024），以及我们自己的方法论。
- **不再包含**：0.3 的 Forge 引擎、Research Companion、Co-Scientist、类比推理。

## 驱动方式
```bash
python3 "<plugin>/scripts/os_next.py" --dir "$PWD/ideaspark_run/<slug>" --project "$PWD" [--query "<研究问题>"]
```
- `os_next` 会先调用 RS 的 `run.py next`。
  - 如果 RS 要进入下一阶段，而这一轮还没过对应的选择层，就先输出选择层这一步，`TYPE: open_scientist_layer`；
  - 否则原样输出 RS 的步骤。需要额外读选择层产物时，在后面附一行 `OPEN-SCIENTIST:`。
- 照输出逐步执行：
  - `bash`：照跑；
  - `llm_subagent`：派隔离的 sub-agent，只传文件路径，输出写盘；
  - `open_scientist_layer`：按对应 skill 执行，写出标记文件后再运行 `os_next`。
- RS 自身的规则不变（见 `skills/idea-spark/SKILL.md`，尤其是 Context discipline），例如每个 LLM 阶段一个隔离 context、不在父上下文粘贴大文件。

## 阶段地图
| 位置 | 层 | 产物 / 完成标记 |
|---|---|---|
| Phase 0 之前 | `mainline`（三瓶颈主线）+ `problem-selection` 的目标函数与参数策略 | `<project>/.open-scientist/mainline.md`；RS 的 query 必须包含 `facts.md` 里的实测事实 |
| RS Phase 0 | 检索：arXiv + OpenReview + 本地库，Phase 0.4 分区，0.5 补漏，全文抓取 | `phase0/` |
| **Phase 0 → 1** | `innovation-lens`：15 种创新类型 A–O（5 族），按瓶颈排序 | `phase0/innovation_lens.json` |
| RS Phase 1 | 瓶颈诊断，读 lens 的排序 | `phase1/phase1_output.json` |
| **Phase 1 → 2** | `gap-code-filter`：gap 对到代码行，判断哪些是"默认但不必要的假设"；实测 + 离线 oracle 准入；设计层"15 种 ideation 模式 × 代码"，按 lens 的顺序展开；改写 gap 列表 | `phase1/ASSUMPTIONS.zh.md`、`phase1/.gap_filter_done` |
| RS Phase 2 / 3 | 2.1 选择（以 lens 和设计表为优先级）→ 2.2 生成 → 2.3 一致性 → 3.1 碰撞 → 3.2 审查 → 3.3 修订 / 重试 | `phase2_*`、`phase3_*` |
| **Phase 3 → 4** | `problem-selection`：假设风险表（1–5，go / no-go），成功概率 × 影响；在本轮的卡和同一项目的其他卡之间排序，定下第一个证伪实验 | `selection.json` |
| RS Phase 4 | 写卡（用户可以选择先做实验、后写卡） | `phase4/` |
| 执行中卡住 | `problem-selection` 的决策树和问题反转（放开一个固定参数，或换成同等价值的目标） | 写进项目记录 |

## 规则
- **选择层只排序、筛选、准入**，不替代 RS 的生成和审查，也不替代实验。
- **RS 是核心**：每个实验都必须追溯到某个 RS run 的卡，或该 run 经过过滤的 gap 列表，实验记录里写明 run 目录和卡号。选择层不自己立项（离线准入审计属于过滤，可以直接做）。RS 之外得到的结果只作为实测事实写进 `facts.md`，供下一轮 RS 的 query 使用。
- gap-code-filter 只删和留 RS 提出的 gap，不新增；Phase 2.1 的 gap × 模式组合仍由 RS 挑，lens 只给优先级。
- 问题必须真实存在，有实测或最小实验支撑；不从方法反推问题；不为凑一个"高级"类型去编问题；证据保守，混杂和评测伪影照实写。
- 只在本项目自选设置下才出现的现象（例如只在某个剂量或协议下）要照实标注，只能作佐证。
- 离线审计不用等用户批准；训练超过项目规定的预算、真机实验、commit / PR，要先问用户。
- 项目专属的内容放在 `<project>/.open-scientist/`（模板见插件的 `templates/.open-scientist/`），不写进插件：
  - `mainline.md`：主线与候选瓶颈；
  - `facts.md`：实测事实；
  - `code_map.md`：代码地图与常见的默认假设。

## 自检
`python3 scripts/selftest_os_next.py <一个已完成的 RS run 目录>`：检查 5 个阶段转换，即 lens → Phase 1 → filter → Phase 2 → selection。
