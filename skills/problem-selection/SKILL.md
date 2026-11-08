---
name: problem-selection
description: Rank research cards and candidate methods, decide go / no-go and the first falsifying experiment, and get unstuck — the problem-choice layer of Open Scientist 0.5 — applied only to cards that PASSED the soundness gate, distilled from Anthropic's scientific-problem-selection skill (Fischbach & Walsh, Cell 2024). Use after IdeaSpark Phase 3 (os_next emits it before Phase 4), when several cards or methods compete, when defining what a project optimises before Phase 0, or when an experiment line is stuck.
---

# 选题与选法（problem-selection）

精简自 Anthropic life-sciences 的 `scientific-problem-selection`（Apache-2.0；Fischbach & Walsh, *Problem choice and decision trees in science and engineering*, Cell 187:1828, 2024）。原文的详细做法保留在 `references/`。
本层只保留与"挑方法、给卡排序、卡住时转向"有关的 5 个模块。去掉了面向生物实验的例子、职业规划和写作模块。

## 用在哪里
| 时机 | 模块 | 作用 |
|---|---|---|
| Phase 0 之前（定主线） | **目标函数**（`references/03-optimization-function.md`） | 先写清楚要优化什么："成功"的定义、谁在乎、用什么指标判定。方法论文就是项目的验收判据（例如 Pareto 判据），把任务表述成一个优化问题 |
| Phase 0 之前 | **参数策略**（`04-parameter-strategy.md`） | 只固定一个有意义的约束（例如平台 + 范式 + 论文类型），其余放开。固定太多会变脆，太少会无从下手 |
| **Phase 3 之后（os_next 在 Phase 4 前插入）** | **风险评估**（`02-risk-assessment.md`） | 见下面的流程 |
| 执行中 | **决策树**（`05-decision-tree.md`） | 每个实验结束都要回答："学到了什么？下一个分支是什么？"做到执行与策略交替（altitude dance） |
| 卡住时 | **问题反转**（`07-problem-inversion.md`） | 三种转法：① 放开一个原本被固定的参数；② 原目标做不到时，换成同等价值的目标；③ 拿到的答案回答的不是原问题时，反问"数据回答了哪个问题" |

## Phase 3 之后的流程（产物 `selection.zh.md` + `selection.json`）
0. **只排 PASS 的卡**：输入是 `soundness_cards.json` 的 `kept`；KILL / unresolved 的卡不进排序。风险表的"现象假设"直接引用验证器的 S1–S4 证据，不重新打分。"影响"按是否作用在 `mainline.md` 的主线上判断：主线 > 支线 > 其他。
1. **列出所有候选**：本轮的卡（`final_candidate.json` 或 `refined_candidate.json`），以及项目里其他在册的卡和候选方法（`<project>/.open-scientist/mainline.md`）。
2. **每张卡的假设表**：对每个关键假设打 1–5 分（1 是 >90% 把握，5 是 <10%），分清"现象假设"和"技术可行性假设"，注明是否已有实测或离线准入。
   - 两个以上 4–5 分的假设属于"多个奇迹"，要么回避，要么先做细化。
3. **两轴打分**：
   - 成功概率：由风险表推出；
   - 成功后的影响：对项目目标函数的贡献，例如能否越过 Pareto 判据、能否成为三瓶颈之一。
   各给一句理由。
4. **go / no-go 与第一个实验**：为风险最高的那个假设设计最便宜的检验，离线优先。写清通过和否决的条件。
5. **排序**：先按"影响 × 成功概率"，再按第一个实验的成本。输出排序表和推荐的下一步。

`selection.json` 的格式：`{"cards": [{"id", "title", "assumptions": [{"text", "kind": "phenomenon|technical", "risk": 1-5, "evidence"}], "p_success", "impact", "first_test": {"what", "admit", "reject", "cost"}, "rank"}], "recommendation"}`。

## 规则
- 打分要有依据。没有实测就写"未测"，不凭印象打低风险。
- 不做"零风险 = 好"的判断。零风险往往只是增量工作，目标是风险被理解、被量化、可控。
- 只给用户排序和建议；涉及训练预算、真机实验、对外发布时，由用户拍板。
