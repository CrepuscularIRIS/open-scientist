---
name: soundness-gate
description: Kill ideas before training (Open Scientist 0.9). Host procedure that sends each RS gap (after Phase 1), each candidate mechanism (after the coherence gate, before collision) and each RS card (after Phase 3) to the independent soundness-verifier agent, one isolated call per claim, then applies the mechanical KILL / CHECK / PASS rule. The verifier sees only code and literature, never the project's own results or scores (no reward hacking); and rewrites the gap list / card list ordered mainline first, branches second. Use whenever os_next emits the soundness-gate layer, before writing any PREREG that needs training, or when the user asks whether a problem or idea is sound.
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
| **Phase 3 → 4**（卡级，S1–S6，带锚点加 S7） | `final_candidate.json` / `refined_candidate.json`，以及 `mainline.md` 里在册、还没测过的卡 | `soundness_cards.json`，然后才写 `selection.json` |

## 流程
1. **列 claim**：每条 gap / 卡一个 id，附上 `phase0/mainline_first.json` 给它定的主线 / 支线位置。
2. **派验证器**：每条 claim 一个隔离调用，`subagent_type=open-scientist:soundness-verifier`（frontmatter 已定 `model: sonnet`；若插件 agent 不可用，用 `general-purpose model=sonnet`，并把 `agents/soundness-verifier.md` 的正文作为 prompt 开头）。
   - prompt 只给路径：CLAIM（写成一个小 JSON 文件；其中的数字只是前提）、GOAL（目标函数定义）、CODE_ROOTS + CODE_MAP（只能是代码地图：删掉指向实验目录、带结果数字的行）、PLUGIN 路径、WORK=`<run>/soundness/<id>/`、OUTPUT=`<run>/soundness/<id>.json`。
   - **不给**：FACTS / DIGEST、任何 RESULT / runs / 跑分，RS 的审查意见，我们对这条 claim 的看法，其他 claim 的判决（防锚定）。
   - 多条 claim 并行派。
3. **机械聚合**（主会话不改判决）：
   - KILL → 从列表移除，原文和理由留在 `soundness_*.json` 的 `killed[]`；
   - CHECK → 按 `decisive_unknown` 补一次**材料**（指向它没找到的代码位置，或补一组检索 query；仍然不给跑分），重派一次验证器（新 context）。第二次出 0 → KILL；仍是 CHECK（无 0）→ gap 级照常进 Phase 2，卡级标 `single_run`：允许**一次**单跑实验定对错（PREREG 写明 decisive_unknown）；
   - PASS → 保留。
4. **机械排列（不是判断）**：保留的条目按 `mainline_relation` 分组（mainline → branch → unrelated），组内按 `total/max` 降序。这只是把 mainline 层已定的位置照抄成顺序，本门不做排序判断。unrelated 只在主线和支线都空时才进 Phase 2。
5. **写回**：
   - gap 级：保留条目写进 `phase1_output.json` 的 `what_phase_0_did_not_address`（原列表另存 `*_unfiltered`），`touch phase1/.gap_filter_done`；
   - 卡级：写 `soundness_cards.json`，再按 `problem-selection` 只对 PASS 的卡排序、定第一个证伪实验。
5b. **现象准入**（gap 级，主会话做，不交给验证器；单独的完成标记）：每条保留的 gap 要有本机实测（引用 FACTS 的一行）或一个已排队的最小测量。写 `phase1/admission.json`：`{"gaps": [{"id", "phenomenon": "measured|pending", "evidence": "facts.md 的行 / 测量脚本"}]}`。`pending` 的 gap 可以进 Phase 2，但对应的卡在测量出来之前不开训练。
5b'. **机制级**（2.3 之后）：claim = 规范候选的机制 + `intervention_object` + 经典锚点（`classical_report` 指向 `phase1/classical/<obj_id>.md`），`level=mechanism`，只评 S1 / S2 / S7。KILL → `soundness_early.json` 顶层写 `"verdict": "KILL"` 与 `kill_reasons`（os_next 停在 CARD_KILLED，省掉整套 Phase 3）；CHECK / PASS → 照常进碰撞。RS 走 ABANDON 重生成新候选时，删掉 `soundness_early.json`，让新候选重判。
5b''. **协议级**（项目一次；评测工具改动后重做）：把项目的判据脚本（例如固定口径配对判决、探针）作为一条 `level=card` 的 claim，只评 S6（加强化规则 4 的协议审计）。结论写 `protocol_audit.json`：`{"tools": [{"path", "sha256", "verdict", "issues"}], "date"}`。`sha256` 是审计时该文件的哈希（0.9）：文件一改，`os_next` 判审计过期并重发本层。以后卡级 S6 只核卡自己的指标与对照，工具本身的口径引用这里的结论。
5c. **卡登记**（卡级）：每张卡的判决追加到 `<project>/.open-scientist/cards.json`（`{"cards": [{"id", "run", "title", "target", "verdict", "total", "max", "decisive_unknown", "date", "outcome": null}]}`）；实验出结果后填 `outcome`，并在 `verifier_log.md` 记一行。
5d. **KILL 之后**：卡级 KILL → 不写卡、不训练；`soundness_cards.json` 顶层写 `"verdict": "KILL"` 和 `kill_reasons`，os_next 会停在 CARD_KILLED，提示在同一 target 上开新 run（kill_reasons 写进 query 作为负约束）。同一 bottleneck 连续 2 个 run 被杀 → 回 `mainline` 层。gap 级全部 KILL → 本 run 停止，回 `mainline` 层重定 target。
6. **汇报**：一张表：claim、主线 / 支线、分数、判决、一句理由。结论先行，[实测] / [猜测] 分标。

## 规则
- 验证器的判决只能被**新证据**推翻（新代码事实、新文献、单跑实验的结果），不能被主会话或 RS 的论证推翻。实验结果用来回测验证器，不回喂给它。
- 不追问"有没有更本质的问题"。主线只在新证据推翻时才改（见 `mainline` skill）。
- 训练只给 PASS 和 `single_run` 的卡；KILL 的不训。PASS 可以直接开跑；`single_run` 只给一次，结果决定去留。单卡实验的预期结果也写进 PREREG，作为对验证器的回测。
- 回测：每次实验结束，把实际结论与验证器当时的判决对比，记进 `<project>/.open-scientist/verifier_log.md`（一行一条：claim、判决、实际结果、对 / 错）。**只有两种判决可检验**：KILL（被杀的 idea 若后来在别处被证明有效 = 误杀）和对已知赢家的校准（不误杀）。CHECK / single_run 的卡无论单跑成败都记 `n/a`，不记"对"——验证器只杀不排，它的分数不预测效果。错判集中在某一项，说明评分表那一项要改。

**成熟方法槽不走 RS 生成**：主线 / 支线里用别人成熟方法解决的那条，直接把"在本设置用方法 X 解 bottleneck Y"作为一张卡送验证器（卡级），PASS / CHECK 后写 PREREG；不跑 RS Phase 2–4（RS 的新颖性 hard floor 只适用于我们自己的 1–2 个切入）。

`soundness_*.json` 格式（卡级另有顶层 `verdict` 与 `kill_reasons`，供 os_next 读）：`{"level": "gap|card", "kept": [{"id", "mainline_relation", "total", "max", "verdict", "file"}], "killed": [...], "unresolved": [...], "order": ["id", ...]}`。
