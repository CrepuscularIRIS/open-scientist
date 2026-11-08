---
name: open-scientist
description: Orchestrator for research idea generation and selection (Open Scientist 0.6). ResearchStudio idea_spark (synced to upstream #63) is the generator. Problem side — a mainline-first formulation (blind first pass + crux validation; one mainline, at most two causally linked branches; one RS run per bottleneck). Gate — an independent soundness verifier (code + literature only, never the project's own scores) kills every idea before training, at gap level after Phase 1 and card level before Phase 4. Solution side — research taste (15 innovation types) ranks solution angles only; problem-selection ranks admitted cards in a cross-run registry. Use when the user wants to pick a research direction, draw an idea card, rank candidate methods or cards, or continue an IdeaSpark run.
---

# Open Scientist 0.6：RS 生成 + 主线优先 + soundness 门

**一句话**：ResearchStudio（RS，已同步上游 #63）负责生成：检索、诊断、生成、一致性检查、审查、写卡。Open Scientist 只做三件事：
1. **问题侧：主线优先。** 先独立找出限制目标的**一条主线**，再找与它因果相连的支线（≤2 条）。每个 bottleneck 开一个 RS run。挑问题**不用** research taste。
2. **soundness 门。** 一个独立验证器只看代码和文献，**不看我们的跑分**。任何 idea 训练前都要过它：KILL 不训；PASS / CHECK 只给一次单跑。
3. **解法侧：research taste。** 15 种创新类型只给已准入的 bottleneck 排**解决角度**；problem-selection 只给没被杀的卡排序。

## 驱动
```bash
python3 "<plugin>/scripts/os_next.py" --dir "$PWD/ideaspark_run/<slug>" --project "$PWD" [--query "<研究问题>"]
```
- **每一步都调用 os_next**，不要直接调用 RS 的 `next`。os_next 负责插入各层，并附上 `overlays/`。overlay 与 RS prompt 冲突时，以 overlay 为准。
- 按输出类型处理：
  - `bash`：照跑。
  - `llm_subagent`：派隔离 sub-agent，只传文件路径，输出写盘；用哪个模型见下面的分工表。
  - `open_scientist_layer`：按对应 skill 执行，写出完成标记。
  - `CARD_KILLED`：不写卡，在同一个 target 上开新 run。
- RS 自身的规则不变（见 `skills/idea-spark/SKILL.md` 和 `references/host-runbook.md`）。每个 run 有 run contract，旧版 run 目录不能续跑。

## 阶段地图
| 位置 | 层 | 产物 / 完成标记 |
|---|---|---|
| 开 run 之前 | 主线已写在 `mainline.md`。每个 bottleneck 一个 run，query 第一行写 `TARGET:`，正文带上 `facts.md` 的实测事实 | `phase0/user_query.txt` |
| RS Phase 0 | 检索（arXiv + 本地库 + OpenReview）、0.4 分区、0.5 补漏、全文 | `phase0/` |
| **Phase 0 → 1** | `mainline`：盲测首轮 → Crux 校验。项目第一次跑或有新证据时才做，否则复制已有的 `mainline_first.json` | `phase0/mainline_first.json` |
| RS Phase 1 | 在 target 内诊断 gap（overlay：主线是硬输入） | `phase1/phase1_output.json` |
| **Phase 1 → 2** | `soundness-gate`（gap 级）+ 现象准入 → `innovation-lens`（解法侧） | `soundness_gaps.json`、`.gap_filter_done`、`solution_lens.json` |
| RS Phase 2–3 | 选择 + 生成（overlay：anchor 按 gate 的顺序）→ 一致性 / formula repair → 碰撞 → 审查 → 修订 → post-revision 审查 | `phase2_*`、`phase3_*` |
| **Phase 3 → 4** | `soundness-gate`（卡级，写进 `cards.json`）→ `problem-selection` | `soundness_cards.json`、`selection.json` |
| RS Phase 4 | 写卡（可以先做实验、后写卡） | `phase4/` |
| 成熟方法槽 | 不走 RS 生成：把"用方法 X 解 bottleneck Y"写成一张卡，直接送卡级 gate | `cards.json` |

## 模型分工（默认值；项目可以在 `.open-scientist/model_routing.md` 里覆盖）
| 任务 | 档位 |
|---|---|
| **设计方法**：RS 2.1+2.2 选择与生成、formula repair、3.3 修订；主线 Crux 校验 | 设计档（最强推理模型，只在这里花最贵的额度） |
| **科研推理**：Phase 0 写 query、0.4 分区、0.5 补漏；Phase 1 诊断；2.3 一致性检查；3.2 审查；post-revision 审查；Phase 4 填写；主线盲测首轮；**soundness 验证器**；代码审查 | 推理档 |
| **执行**：主会话编排、写实验代码、跑实验、确定性步骤、Phase 0 pattern tagging、4.x 的 plain derive | 执行档（便宜，靠审查兜底） |

**独立性规则：生成者不能同时是验证者。**
- 设计档生成的卡，由推理档验证。
- 执行档（主会话）写的成熟方法卡，也由推理档验证。
- 推理档自己诊断出的 gap，再由推理档验证，这是已知的弱点。目前的缓解办法有两条：验证器在隔离 context 里只拿代码和文献，看不到诊断过程；PASS / CHECK 都只给一次单跑。

## 规则
- **RS 是生成核心。** 每个实验都要能追溯到以下之一：某个 RS run 的卡、经过 gate 的 gap、`cards.json` 里的成熟方法卡。各层只删除和排序，不自己立项。
- **任何 idea 训练前都要过验证器。** 包括 RS 的卡、主会话自己想的、用户提的，以及执行中临时冒出的改法。
- **问题侧和解法侧分开。** 挑 bottleneck 只按主线 / 支线；research taste 只用来挑解法。
- **主线只在新证据推翻时才改**，改动写进 `mainline.md` 的变更记录。撞车、RS 退役某个框架，都不算推翻主线的证据。
- **回测。** 每个实验结束后，更新 `cards.json` 里的 `outcome`，并在 `verifier_log.md` 记一行。
- 0.4 / 0.5 的 host 步骤放进隔离 sub-agent，只给 query 文件，不给我们的 claim。
- 离线检查不用等用户批准。超出训练预算、真机实验、commit / PR / 发布，要先问用户。
- 项目文件放在 `<project>/.open-scientist/`（模板见 `templates/`）：`mainline.md`、`facts.md`、`code_map.md`（交给验证器前删掉带结果的行）、`cards.json`、`verifier_log.md`、`model_routing.md`。

## 可选工具（不由 os_next 发出）
`gap-code-filter`：手动整理"默认但不必要的假设"四元组，以及"15 种模式 × 代码"设计表。

## 自检
`python3 scripts/selftest_os_next.py`（无参数）检查两件事：
- RS 的标签是否还在，防止上游改名后某一层静默失效；
- 各层的触发顺序，以及 KILL 停点。
