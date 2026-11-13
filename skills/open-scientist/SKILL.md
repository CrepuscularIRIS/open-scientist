---
name: open-scientist
description: Orchestrator for research idea generation and selection (Open Scientist 0.10: measure first, run the existing switches, then design on the residual; pre-review against a deployment contract; failure attribution before backtracking). ResearchStudio idea_spark (synced to upstream #63) is the generator; Open Scientist inserts layers of three kinds at phase boundaries — RANK (mainline-first problem formulation; problem-selection over a cross-run card registry), VERIFY (an independent soundness verifier on code + literature only, never the project's own scores, at gap / mechanism / card level, plus phenomenon admission and a once-per-project protocol audit), and the solution-side core MODEL layer (classical-theory recall and modeling: original problem → construction → preserved property → mapping, to the user's Q1–Q8 standard), whose construction RS Phase 2 must transport. Use when the user wants to pick a research direction, draw an idea card, rank candidate methods or cards, or continue an IdeaSpark run.
---

# Open Scientist 0.10：先量 → 先跑现成的 → 在残余缺口上设计 → 预审 → 实验 → 归因

**顺序（0.10 的核心改动）**：
```
问题（社区 / 用户给，或主线层定）→ 现象准入：本机测到，记下制度（measured 才往下）
→ 先验扫描：官方 + 社区现成开关全跑一遍 + 一个上界臂
     IMMOVABLE（判据不可动）      → 回问题侧，不出方法卡
     SOLVED_BY_SWITCH（开关已解决）→ 记为集成结果，不在此 TARGET 设计方法
     RESIDUAL（还剩差距）          → 往下
→ 设计（设计档）：经典建模 + RS 生成，只针对残余缺口，基线 = 最好的可部署开关
→ 预审（推理档验证器）：部署合同 S0 + S1–S8；便宜的卡只审一轮
→ 执行档写代码 → 推理档代码审查 → 单跑
→ 失败归因：评测器 / 实现 / 机制没起作用 / gap / 方法 → 决定回溯到哪一层
```
什么时候量：设计之前（准入、先验扫描）和每次失败之后（归因）。什么时候设计：只有扫描判 `RESIDUAL` 之后。

## 原则（用户 2026-11-13；与 RS prompt 冲突时以此为准，已写进两份 overlay）
1. **不回避重叠，不强制查重。** 已有研究做过的问题照样可以做；RS 的"不得回退到已占据节点""占据源约束""相对最近邻实质新颖"在这里不生效；碰撞 / scoop check 只作引用线索，不是门，不改机制、不丢候选。
2. **不预先绑定技术方案。** 推理顺序固定：真实现象 + 文献 → 因果链里**最限制学习的环节** → 已有机制（含社区开关）**为什么不够**（缺哪条信息 / 梯度路径 / 状态覆盖，引先验扫描的结果）→ 最后才是方法：在基线框架内**补上那条关键信息的最简单的训练侧改动**。不从一个现成技术出发找用处。
3. **交付物类型由项目固定。** 项目宪法写的是方法论文，就不能在连续失败后改成分析 / 审计 / 负结果综述。一条线走不通：关闭、清理、汇报、换下一条线。
4. **RS 是骨架，实验串在它的边界上。** 检索、诊断、选择、生成、一致性检查都用 RS 自己的步骤；现象准入和先验扫描插在 Phase 1 与 2 之间，预审、实验、归因接在 2.3 之后，保留下来的结果再回到 RS Phase 4 写卡。

## 一条线、两臂（一次会话只推进一个 TARGET）
- **一次会话 = 一条线。** 一篇方法论文通常要 2–3 条线（各解决一个问题）；它们**依次**做，每条线走到终态（开关已解决 / 方法过线 / 审计关闭）就汇报并停下，由用户给下一条线。会话中途不换线，不同时开两条线的流水线。
- **两张卡都用在这条线上，跑两个不同的臂**（`os_next` 在 `LITE_CANDIDATE_READY` 时给出）：
  1. 先验扫描阶段：两个不同的现成开关，或一个开关 + 上界臂；
  2. 设计阶段：两个**不同类**的候选——把本 run 的 `phase0/`、`phase1/`、`context/`、`run_contract.json` 复制成兄弟 run，写 `phase0/same_target_runs.txt` 和 `phase0/sibling_candidate.json`，RS 从 Phase 2 接着生成第二个候选（overlay 第 9 条：换锚点或换干预对象，因果前提不同）；
  3. 没有站得住的第二个候选时：第一个候选的决定性对照臂（它的证伪计划里的负对照 / 消融）；
  4. 还空着：先验扫描里没跑的开关或上界臂。
  不跑同一臂的多个 seed，不为占卡重训，不拿第二张卡去跑别的课题，不让卡空着等文本审查。
- 两个候选都算这条线的方法卡：都失败且都归因到方法 → 正好触发结构审计（失败按 TARGET 累计）。

## RS 生成 + 插入层（排序 / 验证 / 测量 / 经典建模）

**通用**：插件对任意领域都适用；领域内容只放在 `<project>/.open-scientist/`。非 ML 领域设 `OPEN_SCIENTIST_DOMAIN=general`（检索 = arXiv + OpenReview），验证器的证据可以是协议 / 配置 / 方程等系统事实（见 README「用于任意领域」）。

**一句话**：ResearchStudio（RS，已同步上游 #63）负责生成：检索、诊断、生成、一致性检查、审查、写卡。Open Scientist 在 phase 边界插入三类层，再加两份覆盖 RS prompt 的 overlay（约束）：
1. **排序（rank）**：问题侧用 `mainline`（一条主线、≤2 条因果相连的支线；每个 bottleneck 一个 RS run），卡侧用 `problem-selection`（只排没被杀的卡，按步骤 H 六项）。挑问题**不用** research taste。
2. **验证（verify）**：独立验证器只看代码和文献，**不看我们的跑分**；只杀不排。gap 级、机制级（2.3 之后，KILL 省掉 Phase 3）、卡级（先判部署合同：部署路径读合同外的量 → `UPPER_BOUND`，只能当对照）；另有主会话的现象准入和项目一次的协议审计。KILL 不训；PASS / CHECK 只给一次单跑；训练后 FAIL 走 `attribution`。
2b. **测量（measure）**：`prior-sweep`——设计之前把现成开关和一个上界臂跑掉（见上）。lite 不跳过。
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

## Lite 模式（0.9.1；`OPEN_SCIENTIST_MODE=lite`）
完整流程有 RS 自身 5 个 phase + 11 个插入层。实际起决定作用的只有：因果排序（定 TARGET、判上下游）、Phase 1 诊断、现象准入、先验扫描、一个经典锚点、RS 生成 + 一致性检查、卡级验证器、失败归因、结构止损。lite 只跑这些：
```
mainline（盲测 → 因果排序；无新证据时复制）→ RS Phase 0/1 → 现象准入（measured）→ 先验扫描（RESIDUAL 才往下）
→ classical-recall（1 个锚点，针对残余缺口）→ RS 2.1–2.3（生成 + 一致性）→ os_next 输出 LITE_CANDIDATE_READY
→ 写进 cards.json → 卡级验证器（便宜的卡 1 轮；贵的卡至多再 1 轮补材料）
→ UPPER_BOUND：只当对照；KILL：不训；PASS / 无 0 的 CHECK：推理档代码审查 → 一次单跑（对最好的可部署开关）
→ 训练后 FAIL：失败归因 → GAP 一张、或 KILL / METHOD 累计 2 张 → 结构审计
```
跳过：gap 级验证器、property-test、机制级门、协议审计（工具没改时）、RS Phase 3、problem-selection（只有一张卡时无需排序）；RS Phase 4 写卡放到实验之后、且只为保留的卡写。需要更严的审查时把 `OPEN_SCIENTIST_MODE` 设回 `full`。

## 阶段地图（类型：约束 / 排序 / 验证 / 建模）
| 位置 | 层 | 类型 | 产物 / 完成标记 |
|---|---|---|---|
| 开 run 之前 | 每个 bottleneck 一个 run；query 第一行 `TARGET:`，接**问题卡**（现象来源、一句话困难、两个竞争解释、切分 / 参照 / 货币，见 `mainline`），正文带 `facts.md` 的实测事实 | 约束 | `phase0/user_query.txt` |
| RS Phase 0 | 检索（arXiv + 本地库 + OpenReview）、0.4 分区、0.5 补漏、全文 | — | `phase0/` |
| **Phase 0 → 1** | `mainline`：盲测首轮 → Crux 校验 → 因果排序检验（隔离 Sol，每个候选锚到基线论文章节 + 代码 `file:line`，可改主线）。项目第一次跑或有新证据时才做，否则复制已有的两个产物 | 排序 + 验证 | `phase0/mainline_first.json`、`phase0/causal_order.json` |
| RS Phase 1 | 在 target 内诊断 gap（`overlays/phase1.md`：主线是硬输入） | 约束 | `phase1/phase1_output.json` |
| **Phase 1 → 2** | `soundness-gate`（gap 级） | 验证 | `soundness_gaps.json`、`.gap_filter_done` |
| **Phase 1 → 2** | 现象准入（主会话实测或引 facts 行；只认 `measured`，带制度；`pending` 停在 ADMISSION_PENDING） | 验证 | `phase1/admission.json` |
| **Phase 1 → 2** | `prior-sweep`：列出并跑掉碰到 TARGET 的现成开关 + 一个上界臂；判 IMMOVABLE / SOLVED_BY_SWITCH / RESIDUAL | 测量 | `phase1/prior_sweep.json`（前两种 → PRIOR_SWEEP_STOP） |
| **Phase 1 → 2** | `classical-recall`：宽 Recall → 每对象隔离建模（Q1–Q8）→ `classical_check.py` → 步骤 H 排序（自动，事后汇报） | 建模 | `phase1/classical/`、`classical_anchors.json` |
| **Phase 1 → 2**（仅 ml 域） | `property-test`：每个锚点一个短脚本，在本项目代码 + 冻结 ckpt 上量一次声称的性质（不训练，分钟级）；明显失败的锚点剔除，量不出来的放行 | 验证（快检） | `anchor_tests.json`、`.property_tests_done` |
| RS 2.1–2.3 | 选择 + 生成（`overlays/generation.md`：gap 顺序、搬经典构造）→ 一致性 / formula repair | 约束 | `phase2_*` |
| **2.3 → 碰撞** | `soundness-gate`（机制级：S1 / S2 / S7） | 验证 | `soundness_early.json`（KILL → 停） |
| RS Phase 3 | 碰撞 → 审查 → 修订 → post-revision 审查 | — | `phase3_*` |
| **Phase 3 → 4** | `soundness-gate`（协议级，项目一次）→（卡级：部署合同 S0 + S1–S8，写进 `cards.json`）→ `problem-selection` | 验证 → 排序 | `protocol_audit.json`、`soundness_cards.json`、`selection.json` |
| RS Phase 4 | 写卡（可以先做实验、后写卡） | — | `phase4/` |
| 成熟方法槽 | 不走 RS 生成：把"用方法 X 解 bottleneck Y"写成一张卡，直接送卡级 gate | 验证 | `cards.json` |
| **每次训练后 FAIL**（os_next 最先检查） | `attribution`：按序判 EVALUATOR / IMPLEMENTATION / NOT_ENGAGED / GAP / METHOD；没归因不许出下一张卡 | 验证 | `<run>/attribution/<card>.json`、`cards.json` 的 `attribution` |
| **任何时候**（os_next 最先检查） | 结构审计（`mainline` §结构审计）：本 run 的方法卡累计 ≥2 张失败（KILL，或训练 FAIL 归因为 GAP / METHOD），或有一张归因为 GAP → 停止抽卡，判 GOAL_MISSET / STRUCTURAL / NOT_STRUCTURAL；前两种关闭本 run、回问题侧 | 验证 | `structural_audit.json` |

## 模型分工（默认值；项目可以在 `.open-scientist/model_routing.md` 里覆盖）
| 任务 | 档位 |
|---|---|
| **设计与路线**：经典建模的深入报告（每对象一个）；RS 2.1+2.2 选择与生成、formula repair、3.3 修订；主线 Crux 校验；结构审计；先验扫描判 `RESIDUAL` 后"残余缺口是什么、下一步打哪里"的判断 | 设计档（最强推理模型） |
| **预审与审查**：**soundness 验证器**（每张卡开跑前的预审：部署合同、前提、退化解、常理与量级）；**每次开跑前的代码审查**；实验结论复核与**失败归因**；Phase 0 写 query、0.4 分区、0.5 补漏；Phase 1 诊断；先验扫描的开关清单；经典宽 Recall；2.3 一致性检查；3.2 审查；post-revision 审查；Phase 4 填写；主线盲测首轮、因果排序 | 推理档 |
| **编排与实验**：主会话编排、现象测量、跑先验扫描的各臂、写实验代码、跑实验、确定性步骤、Phase 0 pattern tagging、4.x 的 plain derive | 执行档（便宜；它写的代码和它对结果的解读都不作数，必须过推理档） |

**独立性规则：生成者不能同时是验证者。**
- 设计档生成的卡，由推理档验证。
- 执行档（主会话）写的成熟方法卡，也由推理档验证。
- 执行档写的**代码**开跑前由推理档审查；执行档写的**实验结论**（含失败归因）由推理档复核后才写进事实表。执行档不自行决定路线：换 TARGET、放开约束、"这条线做不成"这类判断交设计档，再交用户。
- 推理档自己诊断出的 gap，再由推理档验证，这是已知的弱点。目前的缓解办法有两条：验证器在隔离 context 里只拿代码和文献，看不到诊断过程；PASS / CHECK 都只给一次单跑。

## 规则
- **RS 是生成核心，经典建模是解法侧的灵魂。** 每个实验都要能追溯到以下之一：某个 RS run 的卡（其机制来自一个经典锚点）、经过 gate 的 gap、`cards.json` 里的成熟方法卡。排序层和验证层只删除和排序，不自己立项；经典建模层只给构造，不选 bottleneck。
- **先用社区的先验。** 官方实现和社区仓里碰到 TARGET 的现成开关，在设计任何方法之前先跑掉（`prior-sweep`）；它们是基线，也可能就是结果。已有做法不是扣分项，差异化不是目标。
- **部署合同是硬边界。** `<project>/.open-scientist/deploy_contract.md` 写明部署时能读什么。部署路径读合同外的量的卡只能是上界对照（`role=upper_bound`），不能当方法、不能计入贡献；`role` 开跑前定，之后不改。判据和制度在结果之后不能改（改 = 新 TARGET）。
- **任何新 idea 训练前都要过验证器。** 包括 RS 的卡、主会话自己想的、用户提的，以及执行中临时冒出的改法。现成开关原样跑不算新 idea，不过验证器，但移植的代码照常过代码审查。
- **失败先归因再回溯。** 训练后 FAIL 的卡先做 `attribution`：评测器或实现的问题就修了重跑；机制没起作用最多重试一次；归因到 gap 立即回问题侧；归因到方法才算这张卡败了、换下一张。
- **问题侧和解法侧分开。** 挑 bottleneck 只按主线 / 支线；解法从经典原问题推导，不按“哪类贡献好看”挑。
- **连续失败先怀疑问题，不怀疑卡。** 同一 TARGET 上失败 ≥2 次，下一步是结构审计（目标是否设错、是否撞上当前合同内不可移除的约束），不是下一张卡。卡级验证器只看单卡，跨卡模式只有这一层能看到。CARD_KILLED 后"同 target 开新 run"只在审计判 NOT_STRUCTURAL 时成立。
- **主线只在新证据推翻时才改**，改动写进 `mainline.md` 的变更记录。撞车、RS 退役某个框架，都不算推翻主线的证据。
- **回测。** 每个实验结束后，更新 `cards.json` 里的 `outcome`，并在 `verifier_log.md` 记一行。只有 KILL 与已知赢家校准可检验；CHECK / single_run 记 `n/a`。
- 0.4 / 0.5 的 host 步骤放进隔离 sub-agent，只给 query 文件，不给我们的 claim。
- 离线检查不用等用户批准。超出训练预算、真机实验、commit / PR / 发布，要先问用户。
- **失败的方法清出项目，测量留下。** 失败卡 / 关闭的 run 的文件（run 目录、PREREG / RESULT、草稿）移到项目外的归档，agent 不读；项目里只留测量行、一行被证伪的前提和登记行（`attribution` skill「收尾」）。测量、评测工具、gap 表、生态图不归档；`facts.md` 里错了的行标 [已撤销]。
- 项目文件放在 `<project>/.open-scientist/`（模板见 `templates/`）：`mainline.md`、`facts.md`、`code_map.md`（交给验证器前删掉带结果的行）、`ecosystem_map.md`（官方 + 社区仓的开关与报告）、`deploy_contract.md`、`cards.json`、`verifier_log.md`、`model_routing.md`。

## 可选工具（不由 os_next 发出）
`gap-code-filter`：手动整理"默认但不必要的假设"四元组，以及"15 种模式 × 代码"设计表。

## 自检
`python3 scripts/selftest_os_next.py`（无参数）检查两件事：
- RS 的标签是否还在，防止上游改名后某一层静默失效；
- 各层的触发顺序（每层都声明了类型），两个 KILL 停点，准入 pending、先验扫描两种停点、失败归因与结构止损的计数；
- `classical_check.py` 对合成报告的判定（完整 / 只读摘要 / 缺失配）。
