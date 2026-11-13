---
name: mainline
description: Mainline-first problem formulation (Open Scientist 0.10). Before RS Phase 1, find the ONE constraint that most limits the project goal and organise every other problem as a branch causally tied to it — via a blind first pass (an isolated agent that does not see our own hypotheses), a crux validation against our claims, and a causal-ordering audit (isolated Sol) that anchors every candidate to the baseline paper's own sections and to code file:line, with a counterfactual bottleneck test and a rule that the mainline changes only on new evidence. Use at the Phase 0 → 1 boundary (os_next emits it), when writing the RS query, or when choosing or re-checking the paper's bottlenecks.
---

# 主线优先（Problem formulation → bottleneck → causal structure）

**要的能力**：在既定目标下，找出**哪个约束决定了整个系统的上限**，并把其他问题组织成围绕它的因果结构；不是平铺"有哪些挑战"，也不是一路追问"更本质"。

**问题侧只用主线 / 支线挑 bottleneck，不用 research taste**（用户 2026-11-08）。按"哪类贡献好看"去挑问题，就是从方法反推问题；解法侧由 `classical-recall`（经典建模，soundness 门之后）负责。

**"最接近本质"的判据**（用来停止抽象，而不是无限往上抽）：主线是能满足下面四条的**最小充分**表述，
① 能把最多条 FACTS 解释为它的后果（其余问题是它的下游或并列支线）；
② 反事实检验下，修好它对目标的改善最大；
③ 能被一个具体实验或代码事实证伪；
④ 再往上抽象一层时，下一步该做什么不再改变——那一层就是停止点（例："WM 在名义分布外失真" vs "模型误差"：后者不改变我们该做的实验，就停在前者）。

一篇期刊方法论文 = 一条主线 + 最多两条支线（合计三个瓶颈），每个都用简单的方法解决：1–2 个自己的切入，其余集成成熟方法。瓶颈必须是项目里实际撞到、测到的。

**Lite 模式**（`OPEN_SCIENTIST_MODE=lite`）：跳过第 2 轮 Crux（不调设计档）；第 1 轮盲测的输出直接填 `mainline_first.json` 的 `final`（`blind` 同内容），第 3 轮因果排序照做——它是唯一能判上下游、触发 REORDER 的一轮。主线已定且没有新证据时，三轮都不跑，复制已有产物。

## 三轮（位置：RS Phase 0 结束、Phase 1 开始之前；产物 `phase0/mainline_first.json` + `phase0/causal_order.json`）

### 输入卫生（三轮都适用；2026-11-10 起，来自一次冷启动失败）
- **基线论文全文必读**：`<project>/.open-scientist/paper_fulltext/`，含附录与 Limitations。没有全文就先补，不开轮。agent 不得用项目自写的目标文件代替"论文是什么"。
- **派发前扫泄漏**：所有输入文件（含 GOAL、code_map、代码注释/docstring）扫一遍：实验编号（如 `A-\d+`、`R\d+`）、我们的臂名/方法名、过往结果数字、"已证实/已复现"类判断。GOAL 里的贡献表、候选表一律不进盲测。
- **发现泄漏即作废重跑**：某轮跑完才发现输入有泄漏 → 该轮及其下游产物全部作废，清理后从该轮重跑。不允许"清理后继续，因为它没把泄漏当证据"——锚定发生在定框架那一步，不需要引用数字。

### 第 1 轮：盲测首轮（Blind First Pass）
一个隔离 sub-agent（`model=sonnet`，推理档；Crux 校验才是设计档），**只给**：
- GOAL（`mainline.md` 的"目标函数"一节，原文）；
- FACTS（`facts.md`，只保留带出处的 [实测] 行）；
- **基线论文全文**（`paper_fulltext/`：贡献主张、评测轴、消融、附录里被删掉的设计及理由、Limitations）；
- 文献池（`phase0/lit_table.md`）和 `code_map.md`。

**不给**：`mainline.md` 的候选瓶颈表、我们的 claim、以前的 RS 卡。（陈述式的用户判断会诱导模型迎合；先独立判断，再对照。）

prompt 要点（照抄）：
> 目标与衡量标准如上。不参考任何人对本项目的既有判断，独立识别**当前限制目标实现的主要约束**。区分现象、根因、当前约束、工程障碍、技术切入点。最终收敛到**一条**有证据的主线。
> 主线的选择标准：因果解释力（能解释多少条 FACTS）、对目标的约束作用、反事实检验、证据强度。每个候选都写出它对应基线论文的哪一节（主张 / 评测轴 / 删掉的设计 / Limitations）。
> 先列 ≥3 个互相竞争的候选，再收敛。
> 输出：① 一句话主线；② 为什么它是主要约束而不是表面症状；③ 最多两个从属问题，各写清与主线的因果关系；④ 最有力的反例、适用边界、不确定性；⑤ 能改变这个判断的关键证据；⑥ 反事实瓶颈检验：假设主线被改善 10 倍，目标能改善多少、接着被什么卡住；⑦ 最后一句可行切入点。
> 不要用"本质上是 X"不断替换抽象；不要以模型架构或工程实现作为默认视角；证据不足就标"待验证假设"。

### 第 2 轮：Crux 校验
**另一个**隔离 sub-agent（`model=fable`），这时才给 `mainline.md` 的候选瓶颈表（我们的 claim）和第 1 轮的输出：
> 对两份主线（及盲测列出的竞争候选）做反事实检验。各自的瓶颈如果被解决，目标能改善多少、还受什么限制？哪一份对 FACTS 的解释力更强？**只有证据充分时才改主线**；不要为了综合而综合。允许推翻盲测、采用它的竞争候选；冷启动无 claim 时，至少拿盲测的两条候选互相对比，不得只修饰盲测结论。
> 输出：最终主线 + ≤2 支线（每条：一句 claim、与主线的因果关系、支撑的 FACTS 行、反事实检验结果）；被降为"其他"的条目及理由；双方分歧点，以及能裁决分歧的最小实验（离线优先）。

### 第 3 轮：因果排序检验（Causal-Ordering Audit）
**第三个**隔离 sub-agent（`model=sonnet`，6.1 Sol；不能是前两轮的同一调用）。它不提新候选，只检验并排序。
**只给**：`mainline_first.json` 里的候选 claim（盲测主线 + 竞争候选、Crux 的主线 / 支线 / 其他，只要 claim 一句，不带双方的论证）、基线论文全文、代码（只读）、`facts.md` 的 [实测] 行。**不给** `mainline.md`、RS 卡、PREREG / RESULT。

对**每个候选**逐项填（缺一项就标缺，不许补想象）：
1. **论文锚**：论文的哪一节、原文一句——它主张了什么 / 假设了什么 / 删掉了什么（及理由）/ 列为 Limitation；影响论文的哪个评测轴。找不到 → 标"论文外"（审稿人会问"为什么测这个轴"）。
2. **代码锚**：实现该设计选择的 `file:line`；核对复现代码与论文描述是否一致——不一致单独标"复现偏差"（不是论文的问题）。
3. **因果链**：论文的设计选择 → 代码机制 → 可观测现象（facts 行，或需要的最小测量）→ 目标轴。每个箭头标 [论文] / [代码] / [实测] / [猜测]。
4. **竞争解释**：每个 [猜测] 箭头，给出能产生同样现象的另一个原因，以及能把两者分开的测量和**放弃阈值**（例：仿真自身的有限差分非线性同样升高 → 不能归因于 WM）。

再做**候选之间**：两两判断 A 是否在 B 的上游（修好 A 会改变 B）、B 在 A 上游、独立、还是共同原因；给出依据（论文节 / 代码行 / facts 行）。

**排序规则**（机械执行）：
- 论文锚与代码锚都没有的候选不能当主线；
- 有论文 + 代码证据显示某候选在 Crux 主线的上游 → 它替换为主线（REORDER）；
- Crux 主线缺论文锚、或其链上关键箭头全是 [猜测] 且竞争解释无法区分 → REJECT_MAINLINE，取排序第一的合格候选；
- 否则 CONFIRM；纯判断分歧（无新证据）不改主线，记入 disputes。

写 `phase0/causal_order.json`：
```json
{"verdict": "CONFIRM | REORDER | REJECT_MAINLINE",
 "candidates": [{"claim": "...", "paper_anchor": {"section": "...", "quote": "...", "eval_axis": "..."} ,
                 "code_anchor": ["file:line"], "repro_mismatch": "...|null",
                 "chain": [{"from": "...", "to": "...", "tag": "论文|代码|实测|猜测"}],
                 "rivals": [{"arrow": "...", "rival": "...", "test": "...", "abandon_if": "..."}]}],
 "edges": [{"up": "...", "down": "...", "evidence": "..."}],
 "order": ["claim", "..."],
 "first_measurement": {"test": "...", "confound_control": "...", "abandon_if": "..."}}
```
REORDER / REJECT_MAINLINE → 按 `order` 改写 `mainline_first.json` 的 `final`，并在 `mainline.md` 变更记录写一行。`first_measurement` 的放弃阈值是预注册的：测出来触发就放弃该主线，不再加解释续命。

**REORDER 必须传到本 run 的 TARGET**（2026-11-11，来自 u2-reward-v2：REORDER 判"平移不变性上游于奖励结构"，TARGET 仍留在奖励侧，后面 7 张卡全在下游打转）：新主线如果在本 run `TARGET:` 的上游，二选一，不许原样进 Phase 1——
① 改写 `phase0/user_query.txt` 的 `TARGET:` 指向新主线（问题卡重写），再进 Phase 1；
② 本 run 停止，给新主线开新 run。
只有当本 run 能写出"上游约束为什么不卡住这个 TARGET"的一句话论证（引 `causal_order.json` 的 edge 和反事实）时，才可以保留原 TARGET，并把这句话写进 `mainline.md` 变更记录。`first_measurement` 若是裁决上下游的检验，先做它（离线优先），再进 Phase 1。

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
第 3 轮定下的主线和每条支线，各作为一条 gap 级 claim 送 `soundness-gate`（验证器只看代码 + 文献）。主线被 KILL → 主线改为次优候选，并在变更记录里写明。

## 一个 bottleneck 一个 RS run
RS 一次只出一个 anchor 的卡。主线和每条支线各开一个 RS run（`ideaspark_run/<slug>-main`、`-b1`、`-b2`），`phase0/user_query.txt` 第一行写 `TARGET: mainline | branch:1 | branch:2`；同一份 `mainline_first.json` 复制进每个 run 的 `phase0/`。

**问题卡**（经典建模手册 §5 步骤 A，写在 `TARGET:` 行之后、事实之前；`classical-recall` 和验证器都读它）：
- **现象来源**：真实轨迹 / 实测（引 facts.md 的行）/ 文献 / 假想小例子，写明是哪一种；
- **一句话困难**：不先给它起方法名（不能先叫它 credit assignment，再用名字证明需要新信用算法）；
- **两个竞争解释**：能导致同样表现的另外两种原因；
- **切分 / 参照 / 货币**：哪个行动块是单位；相对哪种替代或后续策略比较；用什么量结算（真实回报、存活、跟踪误差……）。三者都可以是设计选择。用成熟方法解的那条不开 RS run（见 `soundness-gate`）。

## 下游怎么用
- RS Phase 1 拿到 `mainline_first.json` 作为附加输入：gap 要标出属于主线、哪条支线，或与主线无关。
- `soundness-gate` 用它给每条 gap / 卡定主线位置；排序时主线优先，支线其次。
- `classical-recall`（解法侧）只给已准入的主线 / 支线找经典原问题并建模，主线先做。
- `problem-selection` 的"影响"一项，按"是否作用在主线上"打分。

## 结构审计（连续失败时回到问题侧；2026-11-11）
**为什么有这一节**：u2-reward-v2 在同一 TARGET 上连败 7 张卡（4 KILL + 3 训练 FAIL，含验证器唯一 PASS 卡），三张训练卡同一签名（yaw 改善、XY 不动、body 付出）。失败不是"卡不够好"，而是 TARGET 在一个不可移除约束（actor 观测平移不变）的下游——换多少张卡都一样。卡级验证器只看单张卡，看不到这种跨卡模式，所以要单独一层。

**触发**（`os_next` 机械判定，`STATE: STRUCTURAL_AUDIT`）：同一 run 在 `cards.json` 里 ≥2 张方法卡失败，**来源不限**（RS 卡、成熟方法槽、主会话或用户临时提的卡）。失败 = 验证器 KILL，或训练后 FAIL 且 `attribution` 为 `GAP` / `METHOD`（0.10：训练后 FAIL 先做 `attribution` skill；归因到评测器 / 实现 / 机制没起作用的不计；`role` 为 `baseline` / `upper_bound` 的臂不计）。**只要有一张归因为 `GAP`，一张就触发**——判据在本制度下不可动时，不需要第二张卡来确认。触发后停止抽卡：不起草、不送验证器、不训练新卡。编排者在第 1 张失败后也应主动对照 `causal_order.json`，kill / fail 理由指向 TARGET 上游时不必等第 2 张。

**怎么做**：一个隔离 sub-agent（推理档 `model=sonnet`；不能是生成这些卡的调用）。只给：本 run 的 `phase0/user_query.txt`、`mainline_first.json`、`causal_order.json`、每张失败卡的一句话机制 + `intervention_object` + kill_reasons / 失败签名（RESULT 的行为摘要，不给跑分表）、`facts.md` 的 [实测] 行、代码（只读）。逐项回答：
1. **共同签名**：失败理由是各自独立（不同 S 项、不同机制缺陷），还是同一个模式（同一前提被反驳、训练结果同向偏移）？列出证据。
2. **干预位置**：每张卡的 `intervention_object` 作用在 `causal_order` 因果链的哪一环？是否全部在某个约束的下游？那个约束本身有没有任何一张卡碰过？
3. **约束是否可移除**：该上游约束属于 ① 目标设立错（TARGET 选在下游、或判据本身不可达）；② 当前合同内结构性不可能（例：观测对某变量不变、goal 固定的那个约束），只能放开一个被固定的参数才能动；③ 不是约束，只是这几张卡各自有缺陷。
4. **反事实**：如果放开该约束（给出最小的放开方式，代码 `file:line`），哪张已失败的卡会变得可行？给一个离线可做的裁决检验和放弃阈值。

写 `<run>/structural_audit.json`：
```json
{"decision": "GOAL_MISSET | STRUCTURAL | NOT_STRUCTURAL",
 "failures_at_audit": 2,
 "signature": "...", "upstream_constraint": "...", "constraint_owner": "target | contract | none",
 "release_option": {"what": "...", "code": ["file:line"], "test": "...", "abandon_if": "..."},
 "summary": "一段话"}
```
**判决之后**：
- `GOAL_MISSET` → 本 run 关闭；回本 skill 第 1–3 轮，以审计为**新证据**重定主线 / TARGET（变更记录写一行），新 run。
- `STRUCTURAL` → 本 run 关闭；用 `problem-selection` 的问题反转（放开一个固定参数 / 换等值目标 / 反问数据回答了什么）。放开的若是 goal 或项目宪法固定的约束（观测合同、平台、论文类型），**先问用户**，不得自行改目标。
- `NOT_STRUCTURAL` → 只换来**一张**新卡的额度；再失败就重审（`failures_at_audit` 递增）。
审计判决同样记进 `verifier_log.md` 一行，事后回测（例如放开约束后的卡是否成立）。

## 主线什么时候能改
- 只在**新证据**（新实验结果、离线检查、验证器 KILL 了主线本身、**结构审计判 GOAL_MISSET / STRUCTURAL**、先验扫描判 `IMMOVABLE`）推翻时改；
- **测到新现象时回查被搁置的条目**：Phase 1 里标成 unrelated 的 gap、以前弃掉的候选，判断都是在当时的制度下做的。新测到的现象（例：只在长训练后出现的退化）落在哪条被搁置的 gap 上，那条 gap 就重新打开、重新准入；"已弃条目不翻案"只对没有新测量的争论成立。不许只用现有主线去解释新现象；
- 不因为一轮讨论"听起来更深刻"而改；
- 改的时候在 `mainline.md` 记一行：旧主线 → 新主线、推翻它的证据。

## 选题判据（保留）
0. 社区（官方实现的 issue / README、复现仓的失败记录）写明的问题可以直接作为 TARGET 的来源，不需要从论文文字推导；但进设计之前仍要在本机测到（准入 `measured`）。
1. 在自己的系统上测到现象，有数字，并记下它出现的制度（训练长度 / checkpoint / 评测条件）。
2. 到基线论文自己的消融对照上复测，或用别人发布的权重复测（只评测）：对照上也存在 → 领域问题；只在自己的范式里存在 → 本设置特有，适合作"自己的"切入；对照上消失 → 回代码找原因。

## 项目文件 `<project>/.open-scientist/mainline.md`
模板见插件 `templates/.open-scientist/mainline.md`：目标函数、固定的那一个约束、主线、支线、其他候选、已有结果、主线变更记录。
