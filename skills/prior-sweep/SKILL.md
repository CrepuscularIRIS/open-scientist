---
name: prior-sweep
description: Measure before designing (Open Scientist 0.10). After phenomenon admission and BEFORE classical recall or RS generation, list every existing switch in the official implementation and the community repositories that touches this run's TARGET, run the deployable ones in the regime where the criterion will be judged, and run one upper-bound arm to show the criterion can move at all. The result decides whether a method is designed at all — SOLVED_BY_SWITCH (an existing switch already reaches the criterion), IMMOVABLE (nothing moves it, so the gap or the criterion is mis-set), or RESIDUAL (design only on what the best switch leaves open, with that switch as the baseline). Use when os_next emits the prior-sweep layer, or before proposing any method on a problem that a community has already worked on.
---

# 先验扫描（先量、先跑现成的，再设计）

**为什么有这一层**：一次真实复盘。某个 TARGET 的社区解法（一个采集开关）在项目的生态图里记了 37 小时才被跑，期间流水线生成并训练了 11 张新方法卡，全部失败；那个开关零代码改动、3 GPU-h 一次跑通。另一次，一个"新观测通道"训了 4 次、过了 3 轮审查，之后才发现是两个社区仓的现成开关。流水线会生成新构造，但没有任何一步问"现成的开关跑过没有"。本层补这一步。

**位置**：现象准入之后，`classical-recall` 和 RS 2.1 之前。lite 模式**不跳过**。完成标记 `phase1/prior_sweep.json`。
**谁做**：清单由一个隔离的推理档 sub-agent 列（只读代码与社区仓）；跑实验和读结果由主会话做；判决是机械规则。

## 输入
- `phase1/admission.json`：已实测的现象和它的**制度**（regime：训练长度 / checkpoint / 评测条件）。
- `<project>/.open-scientist/ecosystem_map.md`（没有就先建：官方实现 + 社区仓各自的开关、报告的数字、失败记录，带 `file:line`）。
- `<project>/.open-scientist/deploy_contract.md`：部署时允许读什么。
- 官方实现与社区仓的源码、README、实验笔记（`REF_ROOTS`）。

## 四步

### 1. 定制度
从 `admission.json` 抄下现象出现的制度。**所有臂都在这个制度下跑和评**。现象只在长训练后出现，就不能在短训练的 checkpoint 上判方法（否则判据在那里本来就不会动）。

### 2. 列清单：碰到 TARGET 的现成开关
对 TARGET 涉及的量（例如"确定性部署下的状态覆盖""执行延迟"），在官方实现和每个社区仓里找：命令行开关、配置字段、README / 笔记里写明的配方。每条记：
- 仓、开关、`file:line`；作者报告了什么（数字 + 出处）；作者自己写的代价或失败。
- 在我们要跑的栈上怎么得到等价配置（原生开关 / 一个配置值 / 需要移植，移植的写一行实现对表）。
- `deploy`：对照 `deploy_contract.md`，标 `deployable` 或 `upper_bound`（部署时要读合同外的量）。
- 估计成本（GPU-h）。

**按"碰不碰判据"收，不按主线关系收**：Phase 1 标成 unrelated 的 gap、有人论证"不该有用"的开关，只要碰到判据就列进来。便宜的实验由运行结果裁决，不由论证裁决。

### 3. 跑
- 所有 `deployable` 且成本不超过项目便宜线的开关：现在就跑，空闲的卡并行。这些不是新 idea，**不过验证器**；移植的开关开跑前照常做一次代码审查。
- **至少一个上界臂**：把 gap 声称缺的那个量直接给系统（oracle，允许合同外的量，标 `upper_bound`）。它回答"在这个制度下判据到底能不能动"。上界臂要给的是**墙对应的量**——例如缺的是累计位移，就给位置，不是给速度。造不出上界臂就写明原因，`movable` 记 `unknown`。
- 超过便宜线的开关：列出、标 `ran: false`，问用户。

每个臂在 `<project>/.open-scientist/cards.json` 登记一行：`role` = `baseline` 或 `upper_bound`。这些行不算方法卡，失败不计入止损。

### 4. 判（机械）
与未改动的基线逐样本配对，读行为（时间过程、存活、配对差的区间），然后：

| 判决 | 条件 | 之后 |
|---|---|---|
| `IMMOVABLE` | 上界臂和所有开关都没让判据显著移动 | gap 或判据设错了，不是方法不行。不出方法卡，带着本结果回 `mainline` 层 |
| `SOLVED_BY_SWITCH` | 某个 `deployable` 开关达到项目的验收判据 | 不在这个 TARGET 上设计方法。结果按集成记录；把这个开关**没被测过的代价**（更长训练、扰动、其他制度）写进 `residual_gap`，要不要为它开新 TARGET 由用户或主线层定 |
| `RESIDUAL` | 判据能动，最好的 `deployable` 开关仍留下可测的差距（对验收线或对上界） | 继续到设计。之后每张卡的基线是 `best_deployable`，要补的是 `residual_gap` |

`os_next` 读 `decision`：前两种直接停在 `PRIOR_SWEEP_STOP`。

## `phase1/prior_sweep.json`
```json
{"target": "<TARGET 行>",
 "regime": {"train": "...", "checkpoint": "...", "eval": "..."},
 "criterion": {"metric": "...", "baseline_value": 0.0, "acceptance": "..."},
 "switches": [{"id": "sw1", "repo": "...", "flag": "...", "source": "file:line",
               "community_report": "数字 + 出处", "ours": "native flag | config value | port",
               "deploy": "deployable | upper_bound", "est_gpu_h": 0.0, "ran": true,
               "result": {"criterion": 0.0, "paired_delta": "...", "other_axes": "...", "survival": "..."},
               "not_run_reason": null}],
 "upper_bound": {"id": "...", "quantity_given": "...", "result": {"criterion": 0.0, "paired_delta": "..."}},
 "movable": true,
 "best_deployable": "sw1",
 "residual_gap": "最好的可部署开关之后还剩什么（一句话 + 数字）；没测过的代价",
 "decision": "SOLVED_BY_SWITCH | IMMOVABLE | RESIDUAL",
 "summary": "一段话"}
```

## 规则
- **已有做法不是扣分项，是基线，也可能就是结果。** 不因为"别人做过"绕开它，也不为了和它不同而设计方法。
- **上界臂永远不是贡献。** 它只证明判据能动、量出墙有多厚。
- 清单为空（确实没有任何现成开关）也要写文件，`switches: []`，上界臂照跑。
- 结果写进 `facts.md`（[实测] 行）。之后出现新现象时，回来重查这张清单和被弃的 gap，不沿用旧判断。
