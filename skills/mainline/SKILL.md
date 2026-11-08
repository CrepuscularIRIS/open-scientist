---
name: mainline
description: Mainline-first problem formulation (Open Scientist 0.6). Before RS Phase 1, find the ONE constraint that most limits the project goal and organise every other problem as a branch causally tied to it — via a blind first pass (an isolated agent that does not see our own hypotheses) followed by a crux validation against our claims, with a counterfactual bottleneck test and a rule that the mainline changes only on new evidence. Use at the Phase 0 → 1 boundary (os_next emits it), when writing the RS query, or when choosing or re-checking the paper's bottlenecks.
---

# 主线优先（Problem formulation → bottleneck → causal structure）

**要的能力**：在既定目标下，找出**哪个约束决定了整个系统的上限**，并把其他问题组织成围绕它的因果结构；不是平铺"有哪些挑战"，也不是一路追问"更本质"。

**问题侧只用主线 / 支线挑 bottleneck，不用 research taste**（用户 2026-11-08）。按"哪类贡献好看"去挑问题，就是从方法反推问题；15 种创新类型只在解法侧用（`innovation-lens`，soundness 门之后）。

**"最接近本质"的判据**（用来停止抽象，而不是无限往上抽）：主线是能满足下面四条的**最小充分**表述，
① 能把最多条 FACTS 解释为它的后果（其余问题是它的下游或并列支线）；
② 反事实检验下，修好它对目标的改善最大；
③ 能被一个具体实验或代码事实证伪；
④ 再往上抽象一层时，下一步该做什么不再改变——那一层就是停止点（例："WM 在名义分布外失真" vs "模型误差"：后者不改变我们该做的实验，就停在前者）。

一篇期刊方法论文 = 一条主线 + 最多两条支线（合计三个瓶颈），每个都用简单的方法解决：1–2 个自己的切入，其余集成成熟方法。瓶颈必须是项目里实际撞到、测到的。

## 两轮（位置：RS Phase 0 结束、Phase 1 开始之前；产物 `phase0/mainline_first.json`）

### 第 1 轮：盲测首轮（Blind First Pass）
一个隔离 sub-agent（`model=fable`），**只给**：
- GOAL（`mainline.md` 的"目标函数"一节，原文）；
- FACTS（`facts.md`，只保留带出处的 [实测] 行）；
- 文献池（`phase0/lit_table.md`）和 `code_map.md`。

**不给**：`mainline.md` 的候选瓶颈表、我们的 claim、以前的 RS 卡。（陈述式的用户判断会诱导模型迎合；先独立判断，再对照。）

prompt 要点（照抄）：
> 目标与衡量标准如上。不参考任何人对本项目的既有判断，独立识别**当前限制目标实现的主要约束**。区分现象、根因、当前约束、工程障碍、技术切入点。最终收敛到**一条**有证据的主线。
> 主线的选择标准：因果解释力（能解释多少条 FACTS）、对目标的约束作用、反事实检验、证据强度。
> 输出：① 一句话主线；② 为什么它是主要约束而不是表面症状；③ 最多两个从属问题，各写清与主线的因果关系；④ 最有力的反例、适用边界、不确定性；⑤ 能改变这个判断的关键证据；⑥ 反事实瓶颈检验：假设主线被改善 10 倍，目标能改善多少、接着被什么卡住；⑦ 最后一句可行切入点。
> 不要用"本质上是 X"不断替换抽象；不要以模型架构或工程实现作为默认视角；证据不足就标"待验证假设"。

### 第 2 轮：Crux 校验
**另一个**隔离 sub-agent（`model=fable`），这时才给 `mainline.md` 的候选瓶颈表（我们的 claim）和第 1 轮的输出：
> 对两份主线做反事实检验。各自的瓶颈如果被解决，目标能改善多少、还受什么限制？哪一份对 FACTS 的解释力更强？**只有证据充分时才改主线**；不要为了综合而综合。
> 输出：最终主线 + ≤2 支线（每条：一句 claim、与主线的因果关系、支撑的 FACTS 行、反事实检验结果）；被降为"其他"的条目及理由；双方分歧点，以及能裁决分歧的最小实验（离线优先）。

### 写盘
`phase0/mainline_first.json`：
```json
{"goal": "...",
 "blind": {"mainline": "...", "branches": [...], "counterfactual": "...", "would_change_if": [...]},
 "final": {"mainline": {"claim": "...", "facts": [...], "counterfactual": "..."},
           "branches": [{"claim": "...", "causal_link": "...", "facts": [...]}],
           "others": [{"claim": "...", "why_not": "..."}],
           "disputes": [{"point": "...", "decisive_test": "..."}]}}
```
同时把 `final` 写回项目的 `mainline.md`（主线 / 支线 / 其他三段），改动处注明日期和依据。

## 主线本身也要过验证器
Crux 校验给出的主线和每条支线，各作为一条 gap 级 claim 送 `soundness-gate`（验证器只看代码 + 文献）。主线被 KILL → 主线改为次优候选，并在变更记录里写明。

## 一个 bottleneck 一个 RS run
RS 一次只出一个 anchor 的卡。主线和每条支线各开一个 RS run（`ideaspark_run/<slug>-main`、`-b1`、`-b2`），`phase0/user_query.txt` 第一行写 `TARGET: mainline | branch:1 | branch:2`；同一份 `mainline_first.json` 复制进每个 run 的 `phase0/`。用成熟方法解的那条不开 RS run（见 `soundness-gate`）。

## 下游怎么用
- RS Phase 1 拿到 `mainline_first.json` 作为附加输入：gap 要标出属于主线、哪条支线，或与主线无关。
- `soundness-gate` 用它给每条 gap / 卡定主线位置；排序时主线优先，支线其次。
- `innovation-lens`（解法侧）只给已准入的主线 / 支线排解决角度，主线先排。
- `problem-selection` 的"影响"一项，按"是否作用在主线上"打分。

## 主线什么时候能改
- 只在**新证据**（新实验结果、离线检查、验证器 KILL 了主线本身）推翻时改；
- 不因为一轮讨论"听起来更深刻"而改；
- 改的时候在 `mainline.md` 记一行：旧主线 → 新主线、推翻它的证据。

## 选题判据（保留）
1. 在自己的系统上测到现象，有数字。
2. 到基线论文自己的消融对照上复测，或用别人发布的权重复测（只评测）：对照上也存在 → 领域问题；只在自己的范式里存在 → 本设置特有，适合作"自己的"切入；对照上消失 → 回代码找原因。

## 项目文件 `<project>/.open-scientist/mainline.md`
模板见插件 `templates/.open-scientist/mainline.md`：目标函数、固定的那一个约束、主线、支线、其他候选、已有结果、主线变更记录。
