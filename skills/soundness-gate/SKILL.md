---
name: soundness-gate
description: Kill ideas before training (Open Scientist 0.10). Host procedure that sends each RS gap (after Phase 1), each candidate mechanism (after the coherence gate, before collision) and each RS card (after Phase 3) to the independent soundness-verifier agent, one isolated call per claim, then applies the mechanical KILL / CHECK / PASS rule. The verifier sees only code and literature, never the project's own results or scores (no reward hacking), checks every card against the project's deployment contract (a card that reads anything outside it is an upper bound, never the method); and rewrites the gap list / card list ordered mainline first, branches second. Use whenever os_next emits the soundness-gate layer, before writing any PREREG that needs training, or when the user asks whether a problem or idea is sound.
---

# Soundness 门（先杀 idea，再训练）

**为什么**：很多 idea 要做一次实验（训练、湿实验、仿真、田野）才被杀，而其中不少可以提前从**代码 / 协议和文献**判出来。本门里的"训练"泛指任何花资源的实验。
本门把"这个问题 / 这张卡站不站得住"交给一个**独立的验证器 agent**（`soundness-verifier`，Sol），它只打分、只判决，不提新点子。
**验证器看不到我们的实验结果和跑分**（DIGEST、RESULT、runs、dump 一律不给）：否则就是用我们的跑分给我们的 idea 打分（reward hacking），而且对还没跑过的新 idea 根本杀不掉。它只用代码（`file:line`）和自己检索的文献（arXiv / OpenReview / 本地库）。
"现象是否真实存在"仍由主会话按宪法实测，那是另一道关，不交给验证器。
RS 仍然负责生成；本门只删除和排序，不新增 claim。

**任何 idea 都要过**：除了下表几个位置，主会话自己想的、用户提的、执行中临时冒出的改法，写 PREREG 之前都按卡级派一次验证器。

## 位置（本门只**验证**：杀 / 准入；排序由 mainline 与 problem-selection 负责）
| 位置 | 输入的 claim | 产物 / 完成标记 |
|---|---|---|
| **Phase 1 → 2**（gap 级，S1–S5） | `phase1_output.json` 的每条 gap（含 k3.1 合并进来的） | `phase1/soundness_gaps.json`、`phase1/.gap_filter_done` |
| **Phase 1 → 2**（现象准入，主会话） | 保留下来的每条 gap | `phase1/admission.json` |
| **2.3 之后、碰撞之前**（机制级，只评 S1 / S2 / S7） | 规范候选（`refined_candidate.json` / `repaired_candidate.json`）+ 它用的经典锚点 | `soundness_early.json`（KILL → 不跑 Phase 3） |
| **Phase 4 之前**（协议级，项目一次） | 项目的评测工具与判据脚本 | `<project>/.open-scientist/protocol_audit.json` |
| **Phase 3 → 4**（卡级：先判部署合同 S0，再评 S1–S6、S8，带锚点加 S7） | `final_candidate.json` / `refined_candidate.json`，以及 `mainline.md` 里在册、还没测过的卡 | `soundness_cards.json`，然后才写 `selection.json` |

## 流程
1. **列 claim**：每条 gap / 卡一个 id，附上 `phase0/mainline_first.json` 给它定的主线 / 支线位置。
2. **派验证器**：每条 claim 一个隔离调用，`subagent_type=open-scientist:soundness-verifier`（frontmatter 已定 `model: sonnet`；若插件 agent 不可用，用 `general-purpose model=sonnet`，并把 `agents/soundness-verifier.md` 的正文作为 prompt 开头）。
   - prompt 只给路径：CLAIM（写成一个小 JSON 文件；其中的数字只是前提；卡级带 `deploy_inputs`、`train_only_signals`、`engagement_metric`、`degenerate_solutions`、`baseline_switch`）、**DEPLOY_CONTRACT**（`<project>/.open-scientist/deploy_contract.md`，卡级必给）、GOAL（目标函数定义）、CODE_ROOTS + CODE_MAP（只能是代码地图：删掉指向实验目录、带结果数字的行）、**REF_ROOTS**（官方实现 + 与 claim 相关的社区参考仓，卡级 / 准入实验必给；验证器按强化规则 7 做实现对表）、PLUGIN 路径、WORK=`<run>/soundness/<id>/`、OUTPUT=`<run>/soundness/<id>.json`。
   - **不给**：FACTS / DIGEST、任何 RESULT / runs / 跑分（含 `phase1/prior_sweep.json`，它带我们的结果），RS 的审查意见，我们对这条 claim 的看法，其他 claim 的判决（防锚定）。
   - 多条 claim 并行派。
3. **机械聚合**（主会话不改判决）：
   - KILL → 从列表移除，原文和理由留在 `soundness_*.json` 的 `killed[]`；
   - **UPPER_BOUND**（卡级）→ `cards.json` 里 `role` 改为 `upper_bound`。它不是方法卡：先验扫描还缺上界臂时可以作为对照跑一次，否则不跑；跑分再好也不计入贡献、不能过验收。要成为方法，只能重写成部署路径不读合同外量的新卡，重新送审；
   - `existing_switch` 非空 → 先把那个开关补进 `phase1/prior_sweep.json` 并跑它（`prior-sweep` skill），按扫描判决再决定这张卡还训不训；
   - **便宜的卡只派一轮**：卡的 `est_gpu_h` 不超过项目便宜线（`deploy_contract.md` 的"便宜线"，默认 3 GPU-h）时，CHECK 不补材料、不重派，直接标 `single_run`——一次跑比一轮文本审查便宜，由实验和失败归因裁决。超过便宜线的卡走下一条的两轮；
   - CHECK → 按 `decisive_unknown` 补一次**材料**（指向它没找到的代码位置，或补一组检索 query；仍然不给跑分），重派一次验证器（新 context）。第二次出 0 → KILL；仍是 CHECK（无 0）→ gap 级照常进 Phase 2，卡级标 `single_run`：允许**一次**单跑实验定对错（PREREG 写明 decisive_unknown）；
   - PASS → 保留。
4. **机械排列（不是判断）**：保留的条目按 `mainline_relation` 分组（mainline → branch → unrelated），组内按 `total/max` 降序。这只是把 mainline 层已定的位置照抄成顺序，本门不做排序判断。unrelated 只在主线和支线都空时才进 Phase 2。
5. **写回**：
   - gap 级：保留条目写进 `phase1_output.json` 的 `what_phase_0_did_not_address`（原列表另存 `*_unfiltered`），`touch phase1/.gap_filter_done`；
   - 卡级：写 `soundness_cards.json`，再按 `problem-selection` 只对 PASS 的卡排序、定第一个证伪实验。
5b. **现象准入**（gap 级，主会话做，不交给验证器；单独的完成标记）：本 run 要设计方法的每条 gap 必须**先在本机测到现象**，再进任何设计步骤。写 `phase1/admission.json`：`{"gaps": [{"id", "phenomenon": "measured|pending|out_of_scope", "evidence": "facts.md 的行 / 测量脚本 + 数字", "regime": "现象出现的训练长度 / checkpoint / 评测条件"}]}`。
   - `measured`：有数字、有制度。之后的先验扫描和所有卡都在这个 `regime` 下判。
   - `pending`：还没测。`os_next` 停在 `ADMISSION_PENDING`，**不进先验扫描、经典建模、生成**。测量本身如果是一次现成开关的训练（例：社区基线同配置单跑），它就是先验扫描的一个臂，照样先跑，不许排到新方法后面。
   - `out_of_scope`：别的支线的 gap，只留档；本 run 的卡不得以它为依据。
   - 测了但现象不出现 → 从文件里删掉该 gap，在 `facts.md` 记一行反例。
   - 文献或基线论文的自述不能代替测量，也不能否定一个可测的现象（见验证器强化规则 3）。
5b'. **机制级**（2.3 之后）：claim = 规范候选的机制 + `intervention_object` + 经典锚点（`classical_report` 指向 `phase1/classical/<obj_id>.md`），`level=mechanism`，只评 S1 / S2 / S7。KILL → `soundness_early.json` 顶层写 `"verdict": "KILL"` 与 `kill_reasons`（os_next 停在 CARD_KILLED，省掉整套 Phase 3）；CHECK / PASS → 照常进碰撞。RS 走 ABANDON 重生成新候选时，删掉 `soundness_early.json`，让新候选重判。
5b''. **协议级**（项目一次；评测工具改动后重做）：把项目的判据脚本（例如固定口径配对判决、探针）作为一条 `level=card` 的 claim，只评 S6（加强化规则 4 的协议审计）。结论写 `protocol_audit.json`：`{"tools": [{"path", "sha256", "verdict", "issues"}], "date"}`。`sha256` 是审计时该文件的哈希（0.9）：文件一改，`os_next` 判审计过期并重发本层。以后卡级 S6 只核卡自己的指标与对照，工具本身的口径引用这里的结论。
5c. **卡登记**（卡级）：每张卡的判决追加到 `<project>/.open-scientist/cards.json`（`{"cards": [{"id", "run", "title", "target", "role": "method|baseline|upper_bound", "deploy_inputs", "baseline_switch", "est_gpu_h", "engagement_metric", "verdict", "total", "max", "decisive_unknown", "date", "outcome": null, "attribution": null}]}`）；实验出结果后填 `outcome`，训练后 FAIL 的再按 `attribution` skill 填 `attribution`，并在 `verifier_log.md` 记一行。`role` 在开跑前定，之后不改。
5d. **KILL 之后**：卡级 KILL → 不写卡、不训练；`soundness_cards.json` 顶层写 `"verdict": "KILL"` 和 `kill_reasons`，os_next 会停在 CARD_KILLED，提示在同一 target 上开新 run（kill_reasons 写进 query 作为负约束）。被杀的卡照样登记进 `cards.json`（verdict KILL）；新 run 的 `phase0/same_target_runs.txt` 写上同一 TARGET 之前各 run 的名字（一行一个）——失败按 TARGET 累计，换目录不清零。同一 TARGET 累计 2 张卡 KILL 或训练 FAIL（任何来源，含成熟方法卡）→ `os_next` 停在 STRUCTURAL_AUDIT，按 `mainline` 的「结构审计」一节回到问题侧，不再抽卡。gap 级全部 KILL → 本 run 停止，回 `mainline` 层重定 target。
5e. **开跑前代码审查**（每一次训练或评测工具改动，含先验扫描里移植的开关）：执行档写的代码不直接开跑。派一个隔离的推理档 sub-agent，给 diff、卡（或开关的对表）、运行命令；它逐项核：实现是否就是卡写的机制、开关是否真的生效、有没有上一张卡的残留改动、评测入口和基线臂是否同口径、部署路径是否仍满足合同。BLOCK 必须修完再审；审查期间可以跑 smoke。
5f. **跑完之后**：结论段交推理档复核一次；训练后 FAIL → `attribution` skill（先分清评测器 / 实现 / 机制没起作用 / gap / 方法，再决定回溯到哪）。
6. **汇报**：一张表：claim、主线 / 支线、分数、判决、一句理由。结论先行，[实测] / [猜测] 分标。

## 规则
- 验证器的判决只能被**新证据**推翻（新代码事实、新文献、单跑实验的结果），不能被主会话或 RS 的论证推翻。实验结果用来回测验证器，不回喂给它。
- 不追问"有没有更本质的问题"。主线只在新证据推翻时才改（见 `mainline` skill）。
- **设计之前先量、先跑现成的**：没有 `measured` 的准入和 `phase1/prior_sweep.json`（`prior-sweep` skill），不起草方法卡。每张卡的基线是扫描里最好的可部署开关，不是未改动的基线。
- 训练只给 PASS 和 `single_run` 的卡；KILL 的不训。PASS 可以直接开跑；`single_run` 只给一次，结果决定去留。单卡实验的预期结果也写进 PREREG，作为对验证器的回测。
- 回测：每次实验结束，把实际结论与验证器当时的判决对比，记进 `<project>/.open-scientist/verifier_log.md`（一行一条：claim、判决、实际结果、对 / 错）。**只有两种判决可检验**：KILL（被杀的 idea 若后来在别处被证明有效 = 误杀）和对已知赢家的校准（不误杀）。CHECK / single_run 的卡无论单跑成败都记 `n/a`，不记"对"——验证器只杀不排，它的分数不预测效果。错判集中在某一项，说明评分表那一项要改。

**成熟方法槽不走 RS 生成**：主线 / 支线里用别人成熟方法解决的那条，直接把"在本设置用方法 X 解 bottleneck Y"作为一张卡送验证器（卡级），PASS / CHECK 后写 PREREG；不跑 RS Phase 2–4（RS 的新颖性 hard floor 只适用于我们自己的 1–2 个切入）。

`soundness_*.json` 格式（卡级另有顶层 `verdict` 与 `kill_reasons`，供 os_next 读）：`{"level": "gap|card", "kept": [{"id", "mainline_relation", "total", "max", "verdict", "file"}], "killed": [...], "unresolved": [...], "order": ["id", ...]}`。
