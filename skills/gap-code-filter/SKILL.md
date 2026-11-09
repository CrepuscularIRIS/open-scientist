---
name: gap-code-filter
description: OPTIONAL in Open Scientist 0.7 (not emitted by os_next; the soundness-gate layer replaced it, and its code-mapping step is the verifier's S1 / S2). Manual host filter + design layer between IdeaSpark Phase 1 and Phase 2. After phase1_output.json exists, STOP before Phase 2. Map every gap to the exact code line in the user's project that silently assumes it. Ask whether the simulator, model, protocol or code already exposes what makes that assumption unnecessary. Measure the phenomenon on existing runs, then run an admission audit (CPU, or offline GPU oracle; queue training only if unavoidable). Rewrite the gap list so Phase 2 receives only gaps backed by literature, code and measurement, and cross every admitted assumption with all 15 ideation patterns against the code to list concrete design options. Use whenever an IdeaSpark run reaches the end of Phase 1, or when the user asks for "默认接受但不必要的假设", a gap audit against code, or the gap filter.
---

# Gap 代码过滤层（IdeaSpark Phase 1 → [本层] → Phase 2）

IdeaSpark 原本只靠文献诊断 gap。本层由主会话执行，**夹在 Phase 1 和 Phase 2 之间**。Phase 2 的流程（2.1 选择 → 2.2 生成 → 2.3 一致性门）不改，只把它的输入换成"文献 + 代码 + 实测"共同支撑的 gap。

叙事口径（用户）：gap 存在，但我们没法证明现有做法错；找一个"之前很多人默认接受、但在本设置里其实不必要"的假设，去掉它，得到一个**更正确**的方向。没有代码落点的泛 gap 不收。

## 触发
0.6 起 os_next 不再输出本层；需要时由主会话手动调用（例如想要"默认但不必要的假设"四元组与"15 种模式 × 代码"设计表）。k3.1 的辅助笔记先合并进 Phase 1，再进本层。

## 五步

| 步骤 | 做什么 | 产物 |
|---|---|---|
| 1. 对照代码 | 每条 gap（Phase 1 的和 k3.1 的）对到训练 / 评测代码里**哪一行**在默认这个假设。不只看 gap 列表，还要按下方代码地图系统地扫一遍 | 默认假设 + 来源 + `file:line` |
| 2. 问是否必要 | 仿真、WM 或代码已经暴露了什么信息，使这个假设不必要？（例：WM 根本看不到延迟；执行器定律是已知解析式；回放已经存了延迟，critic 却不读） | "为什么本设置不必要" |
| 3. 实测 | 用已有 run、dump、ckpt 统计这个现象，不新训练 | 现象的数字 |
| 4. 准入审计 | 能离线就直接做：CPU 统计，或 GPU 上的 oracle 审计（用仿真真值 / 全状态当参照）。必须训练的写 PREREG 排队，等训练 | 准入证据 + 判读 |
| 5. 改写 gap | 删掉泛 gap，把有代码落点、有数据的条目写进 `phase1_output.json` 的 `what_phase_0_did_not_address`（原列表另存为 `what_phase_0_did_not_address_unfiltered`），再进 Phase 2 | 正式 gap 列表 |

每条假设都写成四元组：
① 默认假设及其来源（哪篇论文 / 哪个惯例）；
② 代码位置 `file:line`；
③ 为什么本设置不必要；
④ 实测数字 + 去掉后的"更正确方向" + 一个准入测量。
没测的标"未测"；审计否掉的条目保留在文档里并标"已审计，排除"（例：A-38 的 U6）。

## 设计层：15 种 ideation 模式 × 代码（用户 2026-11-07）
本层同时也是设计与思路层。每条通过准入的假设，都把 IdeaSpark 的 15 种模式（`idea-spark/references/ideation-patterns/overview.md`）逐一过一遍，问：
"在这一行代码上，这个模式意味着什么具体改动？"把能落到代码上的写成候选方向，写进 `ASSUMPTIONS.zh.md` 的"模式 × 代码"表（假设 × 模式 → 一句话改法 + 涉及的 file:line），交给 Phase 2.1 作为输入。
Phase 2 默认只会挑 2 种模式；本层的目的就是在看过代码之后，把其余模式的可能性也摆出来。

| 模式 | 在代码上通常对应（例子取自 SuperMimic：WM 梯度训练的人形跟踪） |
|---|---|
| assumption_audit_and_pivot | 本层主线：默认但不必要的假设 |
| architectural_operator_substitution | 换算子或表示：WM 的输入/输出参数化、critic 输入、动作空间 |
| generative_process_redesign | 解放固定的生成过程：想象的上下文与起点分布、推扰或事件注入、终止方式 |
| relax_discrete_search_to_continuous | 离散改连续：硬切换 → 软混合 / 后验加权，整数延迟 → 分数延迟，硬终止 → 软存活 |
| adapt_via_conditioning | 靠条件化适配：把上下文 / 历史编码 / WM 残差作为输入，不重训 |
| structural_prior_encoding | 按构造编码结构：已知解析定律放到网络外（执行器、延迟、事件算子） |
| heterogeneous_decomposition | 异质分解：按扰动轴、按片段族、按接触相位分别处理 |
| decompose_and_delegate | 分解后交给求解器：辨识 / 补偿交给解析或优化求解器 |
| unify_into_shared_representation | 统一表示：多个专家或多个轴合成一个条件化策略 |
| reframe_as_solvable_object | 重述成可解对象：名义代价 → 约束、遗憾、凸包问题 |
| self_supervised_signal_engineering | 制造监督信号：WM 残差、配对 rollout 的差异作为训练信号 |
| targeted_self_supervised_objective | 面向性质的辅助目标：对动作雅可比、识别能力的辅助损失 |
| algebraic_equivalence_unification | 证明等价：例如 hinge 约束 ≡ 重加权（attempt 1 的教训） |
| characterize_limit_then_surpass | 先刻画上限再超越：混合零假设曲线、oracle 上界 |
| controlled_diagnostic_design | 隔离混杂的诊断：配对 twin、冻结组件、口径对照 |

顺序灵活：可以先看代码再配模式，也可以先挑模式再找代码落点。但每个候选都必须有代码落点和至少一条实测或准入。

## 规则
- 不从方法反推问题；准入审计要看行为，不只看分数；证据保守（混杂、评测伪影照实写）。项目宪法里的证据要求照常适用。
- 离线审计**不用等用户批准**，直接跑；单次训练超过 1 GPU-day 仍要问用户。
- 写盘：`<run>/phase1/ASSUMPTIONS.zh.md`（项目也可以另存一份）（四元组 + 审计表）；每个审计一个 `research/exp/<id>/RESULT.md`，脚本放 `research/diag/`。
- 向用户汇报：结论先行，[实测] / [猜测] 分开标，然后直接进 Phase 2。Phase 2.1 的 sub-agent 要拿到 `ASSUMPTIONS.zh.md` 作为输入，锚点优先选通过准入的假设。

## 代码地图
项目专属的代码地图放在 `<project>/.open-scientist/code_map.md`：按"环节 → 文件 → 常见的默认假设"列出，作为第 1 步的扫描清单。插件模板见 `templates/.open-scientist/code_map.md`。

## 完成
写出 `phase1/ASSUMPTIONS.zh.md` 并改写 `phase1/phase1_output.json` 后，`touch phase1/.gap_filter_done`，然后重新运行 `os_next`。
