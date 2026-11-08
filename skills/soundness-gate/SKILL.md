---
name: soundness-gate
description: Kill ideas before training (Open Scientist 0.5). Host procedure that sends each RS gap (after Phase 1) and each RS card (after Phase 3) to the independent soundness-verifier agent, one isolated call per claim, then applies the mechanical KILL / CHECK / PASS rule, runs the single cheapest offline check for CHECK items, and rewrites the gap list / card list ordered mainline first, branches second. Use whenever os_next emits the soundness-gate layer, before writing any PREREG that needs training, or when the user asks whether a problem or idea is sound.
---

# Soundness 门（先杀 idea，再训练）

**为什么**：过去的 idea 多数要训练一次才被杀（例如 A-50：告诉策略真实延迟并不消除名义代价）。很多可以提前从代码和已有事实判出来。
本门把"这个问题 / 这张卡站不站得住"交给一个**独立的验证器 agent**（`soundness-verifier`，Sol），它只打分、只判决，不提新点子。
RS 仍然负责生成；本门只删除和排序，不新增 claim。

## 两个位置
| 位置 | 输入的 claim | 产物 / 完成标记 |
|---|---|---|
| **Phase 1 → 2**（gap 级） | `phase1_output.json` 的每条 gap（含 k3.1 合并进来的） | `phase1/soundness_gaps.json`、`phase1/.gap_filter_done` |
| **Phase 3 → 4**（卡级） | `final_candidate.json` / `refined_candidate.json`，以及 `mainline.md` 里在册、还没测过的卡 | `soundness_cards.json`，然后才写 `selection.json` |

## 流程
1. **列 claim**：每条 gap / 卡一个 id，附上 `phase0/mainline_first.json` 给它定的主线 / 支线位置。
2. **派验证器**：每条 claim 一个隔离调用，`subagent_type=open-scientist:soundness-verifier`（frontmatter 已定 `model: sonnet`；若插件 agent 不可用，用 `general-purpose model=sonnet`，并把 `agents/soundness-verifier.md` 的正文作为 prompt 开头）。
   - prompt 只给路径：CLAIM（写成一个小 JSON 文件）、GOAL、FACTS、CODE_MAP、OUTPUT=`<run>/soundness/<id>.json`。
   - **不给**：RS 的审查意见、我们对这条 claim 的看法、其他 claim 的判决（防锚定）。
   - 多条 claim 并行派。
3. **机械聚合**（主会话不改判决）：
   - KILL → 从列表移除，原文和理由留在 `soundness_*.json` 的 `killed[]`；
   - CHECK → 主会话执行验证器给的那**一个**离线检查（≤ 1 h CPU / 已有 ckpt 评测；不训练；`null` 就跳过），把结果写进 FACTS，再对这条 claim **重派一次**验证器（新 context）。第二次出 0 → KILL；仍是 CHECK（无 0）→ gap 级照常进 Phase 2，卡级标 `single_run`：允许**一次**单跑实验定对错（PREREG 写明是哪一项没定）；
   - PASS → 保留。
4. **排序（主线优先）**：保留的条目先按 `mainline_relation` 分组（mainline → branch → unrelated），组内按 `total/max` 降序。unrelated 只在主线和支线都空时才进 Phase 2。
5. **写回**：
   - gap 级：保留条目写进 `phase1_output.json` 的 `what_phase_0_did_not_address`（原列表另存 `*_unfiltered`），`touch phase1/.gap_filter_done`；
   - 卡级：写 `soundness_cards.json`，再按 `problem-selection` 只对 PASS 的卡排序、定第一个证伪实验。
6. **汇报**：一张表：claim、主线 / 支线、分数、判决、一句理由。结论先行，[实测] / [猜测] 分标。

## 规则
- 验证器的判决只能被**新证据**推翻（离线检查结果、新实验），不能被主会话或 RS 的论证推翻。
- 不追问"有没有更本质的问题"。主线只在新证据推翻时才改（见 `mainline` skill）。
- 训练只给 PASS 和 `single_run` 的卡；KILL 的不训。PASS 可以直接开跑；`single_run` 只给一次，结果决定去留。单卡实验的预期结果也写进 PREREG，作为对验证器的回测。
- 回测：每次实验结束，把实际结论与验证器当时的判决对比，记进 `<project>/.open-scientist/verifier_log.md`（一行一条：claim、判决、实际结果、对 / 错）。错判多的那一项，说明评分表要改。

`soundness_*.json` 格式：`{"level": "gap|card", "kept": [{"id", "mainline_relation", "total", "max", "verdict", "file"}], "killed": [...], "unresolved": [...], "order": ["id", ...]}`。
