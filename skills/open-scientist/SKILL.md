---
name: open-scientist
description: Orchestrator for research idea generation and selection (Open Scientist 0.5). ResearchStudio idea_spark is the backbone (retrieval, bottleneck diagnosis, generation, gauntlet, card). Around it — a mainline-first formulation after Phase 0 (blind first pass + crux validation, one mainline plus at most two causally linked branches), and an independent soundness gate (verifier agent, KILL / CHECK / PASS) after Phase 1 for gaps and after Phase 3 for cards, so ideas die before training; methodology (problem-selection) only ranks what passed. Use when the user wants to pick a research direction, draw an idea card, rank candidate methods or cards, or continue an IdeaSpark run.
---

# Open Scientist 0.5：RS 出卡 + 主线优先 + soundness 门

**一句话**：ResearchStudio（RS）的 idea_spark 负责生成（检索、诊断、生成、审查、写卡）。Open Scientist 只做两件事：
1. **主线优先**：在诊断之前，先独立找出限制目标的**一条主线**，其余问题作为与它因果相连的支线（≤2）；
2. **soundness 门**：一个独立的验证器 agent 对每条 gap、每张卡打分并判决 KILL / CHECK / PASS，**在训练之前杀 idea**。

方法论（problem-selection 的风险表、innovation-lens 的 15 种类型）退为**筛选和排序**，只作用于通过 soundness 门的条目。

## 驱动
```bash
python3 "<plugin>/scripts/os_next.py" --dir "$PWD/ideaspark_run/<slug>" --project "$PWD" [--query "<研究问题>"]
```
照输出逐步执行：`bash` 照跑；`llm_subagent` 派隔离 sub-agent，只传文件路径；`open_scientist_layer` 按对应 skill 执行，写出完成标记后再跑 `os_next`。RS 自身的规则不变（`skills/idea-spark/SKILL.md`，尤其 Context discipline）。

## 阶段地图
| 位置 | 层 | 谁执行 | 产物 / 完成标记 |
|---|---|---|---|
| Phase 0 之前 | 写 query：包含 `facts.md` 的实测事实 | 主会话 | `phase0/user_query.txt` |
| RS Phase 0 | 检索、分区、补漏、全文 | RS | `phase0/` |
| **Phase 0 → 1** | `mainline`：盲测首轮（不看我们的 claim）→ Crux 校验（对照我们的 claim） | 两个隔离 Opus sub-agent | `phase0/mainline_first.json` |
| RS Phase 1 | 瓶颈诊断；gap 标主线 / 支线 | RS | `phase1/phase1_output.json` |
| **Phase 1 → 2** | `soundness-gate`（gap 级） | 验证器 agent（Sol），每条 gap 一次 | `phase1/soundness_gaps.json`、`phase1/.gap_filter_done` |
| RS Phase 2 / 3 | 选择 → 生成 → 一致性 → 碰撞 → 审查 → 修订 | RS | `phase2_*`、`phase3_*` |
| **Phase 3 → 4** | `soundness-gate`（卡级），再 `problem-selection` 只给 PASS 的卡排序 | 验证器 agent；主会话 | `soundness_cards.json`、`selection.json` |
| RS Phase 4 | 写卡（可以先做实验后写卡） | RS | `phase4/` |

## 分工
| 角色 | 只做 | 不做 |
|---|---|---|
| RS（Opus 隔离 sub-agent） | 生成 claim / 卡 | 判断 soundness |
| 主线表述（两个 Opus 隔离 sub-agent） | 一条主线 + ≤2 支线、反事实检验 | 无证据时改主线；追问"更本质" |
| **soundness-verifier**（`agents/soundness-verifier.md`，Sol） | 读代码 + 事实 + artifact，打分，判决 | 提新点子、改写 claim |
| 主会话 | 写代码、跑离线检查和实验、维护 facts、机械聚合判决 | 推翻验证器的判决（只有新证据能） |
| 用户 | 定目标，批准训练预算、真机、发布 | — |

## 规则
- **RS 是核心**：每个实验都追溯到某个 RS run 的卡或经过 soundness 门的 gap 列表。各层不自己立项，只删除和排序。
- **KILL 的不训**：PASS 直接开跑；CHECK 先做验证器指定的那一个离线检查（≤ 1 h）再重判，仍无 0 分 → 允许一次单跑定对错。
- **主线只在新证据推翻时改**，改动写进 `mainline.md` 的变更记录。
- **回测验证器**：每个实验结束，把结果与当时的判决对比，记进 `<project>/.open-scientist/verifier_log.md`。
- 问题必须真实存在、有实测；不从方法反推问题；证据保守，混杂和评测伪影照实写。
- 离线检查不用等用户；超过项目训练预算、真机、commit / PR / 发布要先问用户。
- 项目专属内容放在 `<project>/.open-scientist/`（模板见 `templates/.open-scientist/`）：`mainline.md`、`facts.md`、`code_map.md`、`verifier_log.md`。

## 可选工具（0.5 起不由 os_next 发出）
- `innovation-lens`：15 种创新类型，给已通过的方向打标签、做次级排序；
- `gap-code-filter`：手动做"默认但不必要的假设"四元组和"15 种模式 × 代码"设计表。其代码对照部分已并入验证器的 S3。

## 自检
`python3 scripts/selftest_os_next.py <一个已完成的 RS run 目录>`：检查 6 个阶段转换（mainline → Phase 1 → gap 门 → Phase 2 → 卡门 → selection）。
