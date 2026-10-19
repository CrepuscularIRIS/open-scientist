> **0.2 reference.** In 0.3 the eleven skills are entries that forward to `open-scientist`; their methods are in [references/methods/actions/](../references/methods/actions/).

# 技能、核心资产与桥接覆盖

每项skill都是详细操作指南；方法参考保留更长的原始推理。只在相关问题出现时加载对应文件。下表说明实际适配位置，不是要求按表顺序执行。

| 入口 | 活动方法参考 | 原资产与本次改动 |
|---|---|---|
| workflow | [共同合同](../references/contracts/research-contract.md)、[32桥接](../references/contracts/bridges.md)、[自动模式](../references/contracts/auto-loop.md) | Companion模式/Seed/Decide＋Co目标解析；用触发替代固定六阶段/常驻session |
| retrieve | [intent](../references/methods/intent-recognition.md)、[reading](../references/methods/relevance-and-reading.md)、[collision](../references/methods/collision-check.md) | RS查询、相关性、深读与Scoop；改默认local+arXiv、主题/用途双轴、任何阶段增量覆盖 |
| diagnose | [bottleneck](../references/methods/bottleneck_identify.md) | RS谱系/残差/规则/价值；纳入代码，解除近期叶子/篇数/默认预算限制 |
| ideate | [brainstormer](../references/methods/companion-brainstormer.md)、[select](../references/methods/ideate_select.md) | Companion跨域/前提挑战＋RS选择；需要对象/操作/条件/断点，模式是可选词汇 |
| construct | [generate](../references/methods/ideate_generate.md)、[select](../references/methods/ideate_select.md) | RS观测模型、naive、机制步骤；保留公平基线与必要性，不强迫两个模式 |
| code | [coherence](../references/methods/coherence_trace.md)、[implementability](../references/methods/implementability_audit.md) | 新增代码调查桥：实际入口、信息时序、数据/评测/日志；区分静态与执行事实 |
| test | [coherence](../references/methods/coherence_trace.md)、[falsification](../references/methods/falsification_reaudit.md) | RS T1–T5＋Co testability/feasibility；接宿主执行，分运行失败与机制反证 |
| review | [critique](../references/methods/critique.md)、[grounding](../references/methods/grounding.md)、[rubric](../references/methods/review-rubric.md)、[refutation](../references/methods/refutation_recheck.md) | RS审计＋Co前提/来源；分独立首评、修订复核、窄争议；保留原始反证 |
| evolve | [revise](../references/methods/revise.md)、[combine](../references/methods/combine.md)、[simplify](../references/methods/simplify.md)、[feasibility](../references/methods/feasibility.md)、[out-of-box](../references/methods/out-of-box.md) | RS局部修订＋Co四算子；明确Q/H/T，旧测试不回写，不按高分/远嵌入自动组合 |
| report | [expand](../references/methods/expand.md)、[derive](../references/methods/derive_plain.md)、[implementability](../references/methods/implementability_audit.md)、[quality](../references/methods/idea_quality.md) | RS Phase4与IdeaQuality＋Co overview；单源多视图、反证不按排名过滤、缺口回流 |
| decide | [critic](../references/methods/companion-critic.md)、[strategy](../references/methods/companion-strategy.md)、[ranking](../references/methods/ranking.md) | Companion七维/策略与Co比较；投入选择≠科学真伪，PARK有重访条件 |

## 所有桥接的落点

| 组 | 主要入口 | 检查重点 |
|---|---|---|
| P0-1…6 | workflow/retrieve/ideate/code/review | 缺锚点、跨域映射、用途分流、两层来源核验、争议导读、增量检索 |
| P1-1…6 | diagnose/code/decide/ideate | 约束分类、条件价值、谱系旁支、问题前提核验、缺口分流、退役与挽救 |
| P2-1…6 | construct/ideate/evolve/test/decide | naive障碍、实质互补、必要删减、结构需求、固定H改T、贡献价值 |
| R-1…8 | retrieve/review/test/evolve/decide | 机制碰撞、来源矛盾、区分实验、反例核查、局部重查、不同预测、投入选择、结果分类 |
| O-1…6 | report/code/review/diagnose/decide | 表达缺口、规格缺口、A/B/C诊断、结论边界、可撤回教训、反馈消费 |

这些桥接由Agent依据技能合同选择。自动模式下，宿主 Agent 按 [auto-loop](../references/contracts/auto-loop.md) 循环推进，后端用 `workflow` 记录保存检查点，并用 `workflow_check` 机械核对验收项；后端本身不调度。实现的是统一记录、明确输入输出与版本检查，未实现自动科学判断、自动依赖推理或全局规则自改写。

## 保真与适配边界

原文完整保存与活动说明原样执行不是一回事。归档保持110个文件的字节不变；活动方法有标明的修改，保留有价值的研究段落，移除旧引擎控制内容。段落/token保留比例只帮助审阅迁移范围，不证明研究方法正确或skill更有效。作者的逐项说明见 evaluations 下的 authoring 记录。

保留15+31资产为 [按需索引](../references/patterns/INDEX.md)，并完整链接原卡。没有逐篇复核其中引用论文或历史“oral/reject”结论；它们是可质疑的启发式，不是证据捷径。Theorem偏好的子卡也不对所有领域施加定理要求。

## 未迁入的控制引擎

RS next_step、固定sentinel、固定重试配额、预算字节锁；Companion固定两轮三席；Co常驻supervisor、Elo、向量聚类与自动演化门槛均未作为运行依赖。Reel海报/视频与对外发布不在这11个科研入口的默认流程里。保留资产和分工思想的同时，默认执行可由单Agent完成。
