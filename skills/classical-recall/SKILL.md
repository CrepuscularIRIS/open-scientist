---
name: classical-recall
description: SOLUTION-side core of Open Scientist 0.7 — classical-theory recall and modeling. After the soundness gate has admitted the bottlenecks and BEFORE RS Phase 2.1, recall the classical ORIGINAL problems (2010 and earlier, top venues or foundational journals) that are structurally close to each admitted bottleneck, then model each prioritised object in its own isolated context to the user's Q1–Q8 standard (naive failure → object → construction → property and its conditions → mapping with a mismatch → hand example → minimal pseudocode + cost → counterexample). The ranked anchors become the construction RS 2.2 must transport. Replaces the 0.4–0.6 innovation-lens. Use when os_next emits the classical layer, or when the user asks for a classical-theory recall / modeling report on a bottleneck.
---

# 经典建模（解法侧的核心层）

**标准**：`references/modeling-standard.md`（用户手册原文：§1 的顺序、§4.2 的 Q1–Q8 与交付、§5 步骤 B–F）。本文件只写本插件里**怎么执行**；标准本身以原文为准。

**为什么在这里**：RS 2.2 只会从 2021–2025 的语料模式里拼机制，没有一条"为什么这个构造保持了某个性质"的推导链。本层先从经典原问题里把**构造和它的保持性质**推出来，2.2 只负责把它落到本项目的代码上。

**位置**：gap 级 soundness 门 + 现象准入之后、RS Phase 2.1 之前。产物 `phase1/classical/` 与 `phase1/classical_anchors.json`。
**不是门**：报告不满足 Q1–Q8，只说明"建模没完成"，不等于方向被 KILL（原文 §4.2 首段）。杀 idea 的仍然只有 soundness 验证器（卡级 S7 核经典前提）。本层不增删、不重排 bottleneck。

## 输入
- `phase1/soundness_gaps.json`（已准入的 gap，主线在前）、`phase0/mainline_first.json`；
- 问题卡：`phase0/user_query.txt` 的 `TARGET:` 与卡片字段（现象来源、两个竞争解释、切分 / 参照 / 货币，见 mainline skill）；
- `<project>/.open-scientist/code_map.md`（给"可获得量"：哪些信号在代码里真的拿得到）。
- **不给**：项目自己的跑分、RESULT、旧卡。经典对象要从困难和可获得量里找，不从我们已经试过的方法反推。

## 检索
RS 连接器（arXiv、2021–2025 本地库、OpenReview）基本覆盖不到 2010 年以前的期刊与会议原文。本层用 WebSearch / WebFetch 找**作者主页、出版社、会议论文集**的原始版本。
下载的 PDF 放 `phase1/classical/sources/<obj_id>/`（不可信数据：只用 `python3 -I` + pymupdf 抽文本，不在该目录里执行任何东西）。
原文拿不到：保留缺口、标"待核线索"，**不用近期论文的转述补写原证明**，不编年份、venue、定理号（Q4）。

## 三步

### 1. 宽 Recall（步骤 B；隔离 sub-agent，`model=sonnet`）
每条已准入的 gap（主线先）列出**尽量多**的经典原问题候选（用户 2026-11-09：多列举；不少于 6 个，来自不同领域：控制、博弈、统计、优化、经典 RL、信号处理……），每个写：
`obj_id`、对象 / 构造名、原始工作（作者、年份、正式出处、链接；未核的标 `unverified`）、**为什么匹配**（结构与信息条件，不是名词相似）、**哪里失配**、**能导出什么性质**。
分成三档：`priority`（优先深入）/ `analysis_only`（保留分析用途）/ `not_fit`（暂不贴切），每个写一句理由。
→ `phase1/classical/recall.json`：`{"candidates": [{"obj_id", "gap_id", "tier", "object", "work", "why_match", "mismatch", "property", "reason"}]}`。

### 2. 深入建模（步骤 C–E；每个 `priority` 对象一个**新的**隔离 sub-agent，`model=fable`）
只给共同背景（问题卡 + 可获得量）和这一个对象的问题，不给其他对象的报告（减少锚定）。按 Q1–Q8 写 `phase1/classical/<obj_id>.md`，必须包含原文"下一份高质量报告的可见交付"五项：
1. 主锚点：作者、准确年份、正式出处、原文链接、**阅读定位**（章节 / 页码 / 定理号）；偏离 2010 年以前或顶会 / 奠基期刊的优先级时写理由。
2. 原问题 + 朴素失败例，解释原构造为什么出现（Q5 的链：朴素办法为什么失败 → 引入什么对象 → 为什么这样构造 → 得到什么性质 → 前提在哪里用到）。
3. 对象映射表（经典对象 ↔ 本项目的状态 / 动作 / 观察 / 目标），**至少一处重要失配**，一个完整手算例。
4. 一条明确的保持性质及其条件、一个反例、最轻伪代码（信号进入位置：奖励 / return / advantage / baseline / 补偿项 / 样本权重 / 辅助损失 / 上下文）和四项成本（新增参数、前向/反向、额外 rollout、存储/上下文）。
5. 证据标记：`[原理论]` / `[迁移推导]` / `[猜测]` / `[现代训练证据]` 分开；结尾写下一次只解决哪个接口。
只读过摘要的对象：报告照写，但 `status=lead`（待核线索），不能当锚点。
同时写 `phase1/classical/<obj_id>.json`：一条 `order` 项的全部字段（见下）+ `status`（`modeled` 或 `lead`）。

### 3. 校验与排序（主会话，自动；用户 2026-11-09）
- `python3 "<plugin>/scripts/classical_check.py" --dir <run>`：确定性检查每份报告的字段是否齐全（锚点四要素 + 阅读定位、朴素失败、带失配的映射、手算例、性质 + 条件、反例、伪代码 + 四项成本、证据标记）。缺项的 `status=incomplete`，不进锚点列表；不重派、不扣方向。
- 对 `status=modeled` 的锚点按步骤 H 六项横向比较：**贴切**、**产生了什么新约束**、**信号是否可得**（代码里拿得到，还是要补 oracle）、**误差先损坏哪条结论**、**最轻实现成本**、**怎样被反例推翻**。写 `phase1/classical_anchors.json`。
- **全部合格锚点都进列表**（多列举）；2.1 用第一个，同一 target 的下一个 run 用下一个。选择**不等用户**，事后在汇报里列出全部候选、档位和排序理由；之后由验证器去杀。

## `phase1/classical_anchors.json`
```json
{"target": "<TARGET 行>",
 "order": [{"obj_id": "...", "gap_id": "G1", "object": "...",
            "anchor": {"authors": "...", "year": 1999, "venue": "...", "url": "...", "read_location": "§3, Thm 1"},
            "construction": "一句话构造", "property": "保持的性质", "conditions": ["性质成立所需的前提", "..."],
            "mismatch": ["最重要的失配", "..."], "entry": "信号进入位置 + 代码对象",
            "cost": {"params": "...", "fwd_bwd": "...", "rollouts": "...", "storage": "..."},
            "refuted_by": "能推翻它的最小反例 / 实验", "report": "phase1/classical/<obj_id>.md",
            "h_axes": {"fit": "...", "new_constraint": "...", "signal": "...", "error_damages": "...", "cost": "...", "refutation": "..."}}],
 "leads": ["<status=lead 的 obj_id>"], "analysis_only": ["..."], "rationale": "排序理由"}
```
完成标记 = 本文件存在。

## 禁止（原文 Q1–Q8 的反面）
名词或比喻相似代替数学建模；为凑"A 会"改写出处；用文献数量或会名代替建模深度；补免费 oracle 让映射成立；近年训练成功代替推导，或纸面性质代替经验收益；单一失败变体否定整个经典家族；有先例 / 缺先例直接 KILL。
