---
name: mainline
description: Keep a journal method paper's spine — three bottlenecks actually hit in the project, each solved by a simple method (one or two of our own, the rest mature methods applied well) — and decide whether a problem deserves to be a topic by re-measuring it on the paper's own ablation baselines or on others' released weights. Use before an IdeaSpark run (to write the query and the project mainline file), when choosing or re-checking paper topics, or when deciding what to run next.
---

# 主线（三瓶颈）

## 原则
- 一篇期刊方法论文由三个瓶颈组成。
  - 每个瓶颈都用简单、有效、不容易翻车的方法解决；
  - 其中 1–2 个可以是自己的切入（innovation-lens 的 A、B、E、F、H、L 等类型），其余集成别人已经成熟的方法，用过来效果好就行。
- 瓶颈必须是项目里**实际撞到**的。只在自选设置下才出现的现象要照实标注，只能作佐证。
- 领域里一直存在的问题可以做，前提是在本设置里测到了、能量化、有简单的解法。

## 选题判据：在自己的系统上测到，再到对照上复测
1. 在自己的系统上测到现象，有数字。
2. 到**基线论文自己的消融对照**上复测，或者用**别人发布的权重**做复测（只评测，不训练）：
   - 对照上也存在：领域问题，适合作为期刊主题；
   - 只在自己的范式里存在：本设置特有，适合作为"自己的"那 1–2 个；
   - 在对照上消失：说明是某个具体设计造成的，回到代码找原因（gap-code-filter）。
3. 用 innovation-lens 给每个瓶颈的候选方法排序，再用 problem-selection 定 go / no-go。

## 项目文件 `<project>/.open-scientist/mainline.md`
模板见插件 `templates/.open-scientist/mainline.md`。至少包括：
- **目标函数**：验收判据（problem-selection 的目标函数模块）；
- **固定的那一个约束**；
- **候选瓶颈表**：瓶颈、实测、对照上的复测、对应的领域老问题、状态；
- **已有结果**：一行一个数字和出处。

## 输出给 RS
RS 的 query 应当包含：
- 主线里的实测事实（来自 `facts.md`）；
- 本轮针对的瓶颈；
- 要求区分领域通用问题和本设置特有问题。
