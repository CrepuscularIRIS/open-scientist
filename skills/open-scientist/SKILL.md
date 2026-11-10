---
name: open-scientist
description: Orchestrator for research idea generation and selection (Open Scientist 0.9). ResearchStudio idea_spark (synced to upstream #63) is the generator; Open Scientist inserts layers of three kinds at phase boundaries — RANK (mainline-first problem formulation; problem-selection over a cross-run card registry), VERIFY (an independent soundness verifier on code + literature only, never the project's own scores, at gap / mechanism / card level, plus phenomenon admission and a once-per-project protocol audit), and the solution-side core MODEL layer (classical-theory recall and modeling: original problem → construction → preserved property → mapping, to the user's Q1–Q8 standard), whose construction RS Phase 2 must transport. Use when the user wants to pick a research direction, draw an idea card, rank candidate methods or cards, or continue an IdeaSpark run.
---

# Open Scientist 0.9：RS 生成 + 三类插入层（排序 / 验证 / 经典建模）

**通用**：插件对任意领域都适用；领域内容只放在 `<project>/.open-scientist/`。非 ML 领域设 `OPEN_SCIENTIST_DOMAIN=general`（检索 = arXiv + OpenReview），验证器的证据可以是协议 / 配置 / 方程等系统事实（见 README「用于任意领域」）。

**一句话**：ResearchStudio（RS，已同步上游 #63）负责生成：检索、诊断、生成、一致性检查、审查、写卡。Open Scientist 在 phase 边界插入三类层，再加两份覆盖 RS prompt 的 overlay（约束）：
1. **排序（rank）**：问题侧用 `mainline`（一条主线、≤2 条因果相连的支线；每个 bottleneck 一个 RS run），卡侧用 `problem-selection`（只排没被杀的卡，按步骤 H 六项）。挑问题**不用** research taste。
2. **验证（verify）**：独立验证器只看代码和文献，**不看我们的跑分**；只杀不排。gap 级、机制级（2.3 之后，KILL 省掉 Phase 3）、卡级；另有主会话的现象准入和项目一次的协议审计。KILL 不训；PASS / CHECK 只给一次单跑。
3. **经典建模（model，解法侧的核心）**：`classical-recall` 先 Recall 2010 年以前的经典原问题，再一对象一隔离 context 按 Q1–Q8 推出"朴素失败 → 对象 → 构造 → 保持性质及条件 → 映射与失配"。RS 2.2 必须把锚点的构造搬到代码上，而不是从近年模式里拼机制。标准原文：`skills/classical-recall/references/modeling-standard.md`。
4. **约束（overlay）**：`overlays/phase1.md`（瓶颈是给定的）、`overlays/generation.md`（gap 顺序、经典构造、`intervention_object`）。

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

## 阶段地图（类型：约束 / 排序 / 验证 / 建模）
| 位置 | 层 | 类型 | 产物 / 完成标记 |
|---|---|---|---|
| 开 run 之前 | 每个 bottleneck 一个 run；query 第一行 `TARGET:`，接**问题卡**（现象来源、一句话困难、两个竞争解释、切分 / 参照 / 货币，见 `mainline`），正文带 `facts.md` 的实测事实 | 约束 | `phase0/user_query.txt` |
| RS Phase 0 | 检索（arXiv + 本地库 + OpenReview）、0.4 分区、0.5 补漏、全文 | — | `phase0/` |
| **Phase 0 → 1** | `mainline`：盲测首轮 → Crux 校验 → 因果排序检验（隔离 Sol，每个候选锚到基线论文章节 + 代码 `file:line`，可改主线）。项目第一次跑或有新证据时才做，否则复制已有的两个产物 | 排序 + 验证 | `phase0/mainline_first.json`、`phase0/causal_order.json` |
| RS Phase 1 | 在 target 内诊断 gap（`overlays/phase1.md`：主线是硬输入） | 约束 | `phase1/phase1_output.json` |
| **Phase 1 → 2** | `soundness-gate`（gap 级） | 验证 | `soundness_gaps.json`、`.gap_filter_done` |
| **Phase 1 → 2** | 现象准入（主会话实测或引 facts 行） | 验证 | `phase1/admission.json` |
| **Phase 1 → 2** | `classical-recall`：宽 Recall → 每对象隔离建模（Q1–Q8）→ `classical_check.py` → 步骤 H 排序（自动，事后汇报） | 建模 | `phase1/classical/`、`classical_anchors.json` |
| **Phase 1 → 2**（仅 ml 域） | `property-test`：每个锚点一个短脚本，在本项目代码 + 冻结 ckpt 上量一次声称的性质（不训练，分钟级）；明显失败的锚点剔除，量不出来的放行 | 验证（快检） | `anchor_tests.json`、`.property_tests_done` |
| RS 2.1–2.3 | 选择 + 生成（`overlays/generation.md`：gap 顺序、搬经典构造）→ 一致性 / formula repair | 约束 | `phase2_*` |
| **2.3 → 碰撞** | `soundness-gate`（机制级：S1 / S2 / S7） | 验证 | `soundness_early.json`（KILL → 停） |
| RS Phase 3 | 碰撞 → 审查 → 修订 → post-revision 审查 | — | `phase3_*` |
| **Phase 3 → 4** | `soundness-gate`（协议级，项目一次）→（卡级 S1–S7，写进 `cards.json`）→ `problem-selection` | 验证 → 排序 | `protocol_audit.json`、`soundness_cards.json`、`selection.json` |
| RS Phase 4 | 写卡（可以先做实验、后写卡） | — | `phase4/` |
| 成熟方法槽 | 不走 RS 生成：把"用方法 X 解 bottleneck Y"写成一张卡，直接送卡级 gate | 验证 | `cards.json` |

## 模型分工（默认值；项目可以在 `.open-scientist/model_routing.md` 里覆盖）
| 任务 | 档位 |
|---|---|
| **设计方法**：经典建模的深入报告（每对象一个）；RS 2.1+2.2 选择与生成、formula repair、3.3 修订；主线 Crux 校验 | 设计档（最强推理模型，只在这里花最贵的额度） |
| **科研推理**：Phase 0 写 query、0.4 分区、0.5 补漏；Phase 1 诊断；经典宽 Recall；2.3 一致性检查；3.2 审查；post-revision 审查；Phase 4 填写；主线盲测首轮；**soundness 验证器**；代码审查 | 推理档 |
| **执行**：主会话编排、写实验代码、跑实验、确定性步骤、Phase 0 pattern tagging、4.x 的 plain derive | 执行档（便宜，靠审查兜底） |

**独立性规则：生成者不能同时是验证者。**
- 设计档生成的卡，由推理档验证。
- 执行档（主会话）写的成熟方法卡，也由推理档验证。
- 推理档自己诊断出的 gap，再由推理档验证，这是已知的弱点。目前的缓解办法有两条：验证器在隔离 context 里只拿代码和文献，看不到诊断过程；PASS / CHECK 都只给一次单跑。

## 规则
- **RS 是生成核心，经典建模是解法侧的灵魂。** 每个实验都要能追溯到以下之一：某个 RS run 的卡（其机制来自一个经典锚点）、经过 gate 的 gap、`cards.json` 里的成熟方法卡。排序层和验证层只删除和排序，不自己立项；经典建模层只给构造，不选 bottleneck。
- **任何 idea 训练前都要过验证器。** 包括 RS 的卡、主会话自己想的、用户提的，以及执行中临时冒出的改法。
- **问题侧和解法侧分开。** 挑 bottleneck 只按主线 / 支线；解法从经典原问题推导，不按“哪类贡献好看”挑。
- **主线只在新证据推翻时才改**，改动写进 `mainline.md` 的变更记录。撞车、RS 退役某个框架，都不算推翻主线的证据。
- **回测。** 每个实验结束后，更新 `cards.json` 里的 `outcome`，并在 `verifier_log.md` 记一行。只有 KILL 与已知赢家校准可检验；CHECK / single_run 记 `n/a`。
- 0.4 / 0.5 的 host 步骤放进隔离 sub-agent，只给 query 文件，不给我们的 claim。
- 离线检查不用等用户批准。超出训练预算、真机实验、commit / PR / 发布，要先问用户。
- 项目文件放在 `<project>/.open-scientist/`（模板见 `templates/`）：`mainline.md`、`facts.md`、`code_map.md`（交给验证器前删掉带结果的行）、`cards.json`、`verifier_log.md`、`model_routing.md`。

## 可选工具（不由 os_next 发出）
`gap-code-filter`：手动整理"默认但不必要的假设"四元组，以及"15 种模式 × 代码"设计表。

## 自检
`python3 scripts/selftest_os_next.py`（无参数）检查两件事：
- RS 的标签是否还在，防止上游改名后某一层静默失效；
- 各层的触发顺序（每层都声明了类型），以及两个 KILL 停点；
- `classical_check.py` 对合成报告的判定（完整 / 只读摘要 / 缺失配）。
