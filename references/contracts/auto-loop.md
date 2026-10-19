> **0.2 historical contract.** Auto mode and its fixed acceptance list are superseded in 0.3 by the study loop ([design](../../docs/design.md) §5, [protocols](../protocols.md)). Kept so the 0.2 method texts that cite it stay readable.

# 自动模式：有边界地推进到研究里程碑

用户要求"自动研究 / 持续推进 / 直到交付"时使用。宿主 Agent 执行循环，`workflow` 记录保存检查点，`workflow_check` 判断是否达到交付标准。默认单 Agent；独立审查在需要时才分出。循环结构借鉴 Co-Scientist supervisor（解析目标 → 有界执行 → 每步后检查终止条件 → 收尾总览）和 PPT 的研究动作（ABDUCE → PROBE → GRILL → REPORT，新证据回到假设）。不引入 Elo、常驻进程或固定阶段文件。

## 1. 启动：把请求解析成一份运行合同

先读 [共同合同](research-contract.md) 和 [record-api](../../docs/record-api.md)。研究记录写在用户当前项目根目录，不能写到插件目录。

从用户原话提取以下内容，写入 project（问题与硬约束）和 workflow v1：

| 字段 | 内容 | 缺失时 |
|---|---|---|
| goal | 一句话的交付目标 | 默认"形成经过文献、代码与反例检查的研究方案" |
| criteria | 验收项，取自下表 | 默认全部七项；没有代码仓库时去掉 `code`，并在 open_issues 写明原因 |
| authorized / forbidden | 允许的动作（检索、读代码、廉价本地探测……）与禁止项（训练、付费 API、改动 main……） | 未提到的昂贵或不可逆动作一律视为禁止 |
| max_actions | 预算，按动作次数计 | 默认 20；用户给出时间或成本时换算后写入 open_issues |
| stage / next_action | 起点通常是 `frame` 与第一项待补的验收项 | — |

只有目标、硬约束或授权确实无法判断时，才问用户一个问题，并把它写进 `question_for_user`（status=waiting_user）。能从仓库和材料中查到的信息，不要问。

## 2. 验收项：完成必须有证据

先确定本次的**里程碑**，再选验收项。不要每次都套用整套七项：

| 里程碑 | 适用场景 | criteria |
|---|---|---|
| 问题诊断 `diagnosis` | 问题是否真实、失败在哪里还不清楚 | question、code（有仓库时）、literature、decision |
| 研究方案 `proposal` | 要一个可实现、经过审查的方案 | 全部七项；没有仓库时去掉 code |
| 判别结果 `probe_result` | 已授权运行判别实验 | question、counterexamples、test_plan、decision；test_plan 必须引用 completed 且有 outputs 的 activity（后端只核对"非 failed"，这一点靠 Agent 自觉） |

有效的负结论也可以完成里程碑：决定项可以是 park 或 kill，不强制 pursue。

| criterion | 达标条件（`workflow_check` 会机械核对） | 负责技能 |
|---|---|---|
| question | 引用当前版本的 project | workflow / diagnose |
| literature | 至少一条带材料证据的 finding（supported/partial/contradicted/contested） | research-retrieve，再 review grounding |
| code | 至少一条带 locator（文件:行）的代码或数据 material | research-code |
| counterexamples | focus 候选的当前版本：每个 claim 都有 finding；所有 contradicted/contested 都已 disposition | research-review（GRILL），必要时 research-evolve |
| test_plan | 一个 activity，其 inputs 包含 focus 当前版本，且不是 failed | research-test |
| card | 一份在 focus 当前版本之后写入的 Card material | research-report |
| decision | 针对 focus 当前版本或当前 project 当前版本的决定（pursue/refine/park/kill 均可） | research-decide |

只有 `workflow_check` 返回 ready，status=done 才能写入；否则后端拒绝。几条规则要记住：

- 被引用的记录如果出了新版本（例如 finding 被撤回、activity 变成 failed），旧引用不再算数。
- 当前 focus 候选的**任何版本**上出现过的 contradicted/contested finding，都要等它最近的一条 disposition 解除才算处理完：adopted、superseded，或附带输出证据的 rejected。把 finding 改写成 unknown，或者升级 H，都不能抹掉这笔账。
- 目标、验收项、预算、授权和禁止项属于**运行合同**。修改它们必须在 `user_input` 中引用一条之后写入的 human feedback；Agent 不能自行放宽。
- H 一旦修订，依赖它的 test_plan、card、decision、counterexamples 需要局部重做。literature、code 的材料可以复用，但如果 H 改变了信号或前提，要重新确认它们仍然支持新用途。这是结构检查，不判断科学真假：引用的记录本身必须是真实读过、真实运行过的东西。

另一种合法结局是**有依据的停止**：写一个附带 material 证据的 kill/park 决定，再把 workflow 设为 stopped，stop_reason=`evidence_based_stop`。例如问题已被前人解决、目标在现有数据上不可识别、价值不足。这和"做不下去"不同。

## 3. 每一轮：一个动作，一个检查点

```text
观察 → 选缺口 → 查重 → 执行一个技能 → 写记录 → 写检查点 → 检查是否该停
```

1. **观察。** 读最新的 workflow 和 `workflow_check`，只按需读取相关记录。`records_context` 只在启动、恢复和每次总览时读全量。
2. **选动作。** 不按验收项顺序机械补齐，按以下优先级：
   1. 用户的新指令，或仍在运行的执行任务；
   2. 推翻当前路线的有效反证或测量故障（见第 4 节）；
   3. 承重前提里最影响决策的那个不确定性；
   4. 达成里程碑还缺的内容；
   5. 表达整理。

   每步写一句理由，格式是"如果这项检查得到 A 或 B，下一步分别怎么变"。廉价、已授权的探测可以早于完整成卡；否定结果可以结束错误分支，不必为凑出一个正向方案硬造新方法。

   还没有 focus 时，走 ABDUCE：先 research-diagnose，再 research-ideate 或 research-construct，产出一个 candidate，并把它设为 focus。
3. **查重。** 为动作起一个键：`<技能>:<对象@版本>:<意图>`，例如 `retrieve:h@2:alias-search`。如果历史检查点里已有同一个键，就不要重做；确有新理由时加 `#2` 并在 summary 写明原因。后端会拒绝重复的键。
4. **执行。** 按共同合同的六项交接调用一个专项技能。只要当前执行上下文里没有这个技能，就要加载：首次使用、会话恢复、上下文压缩之后、新开的子 Agent，都算"没有"。例如第一次用到时，通过宿主的技能机制加载它（Claude Code 用 Skill 工具调用 `open-scientist:research-…`，Codex 用 `$research-…`），按其中的方法执行；同一技能再次使用时可以沿用已加载的内容。不要凭印象代替专项方法。宿主工具负责实际检索、读代码和运行获授权的探测；不能越过 authorized / forbidden。
5. **先写研究记录**（material、finding、candidate、activity、decision），**再写检查点**：
   - actions_used +1
   - last_action：键、技能、问题、outcome（advanced / no_change / failed / needs_user）、summary、outputs
   - 更新 evidence、focus、stage、open_issues、next_action
6. **检查是否该停**（Co-Scientist 的终止判断，每个检查点之后都要做）：

| 情况 | 动作 |
|---|---|
| `workflow_check` ready | 收尾（第 7 节）→ status=done |
| actions_used 达到 max_actions | stopped，stop_reason=budget；summary 写出下一步本该做什么 |
| 最近的动作没有改变事实覆盖、候选间的区分、风险判断、可执行性或交付完整度（反复记录同样的未知不算进展），换一条证据路线后仍然如此 | stopped，stop_reason=no_progress；说明在当前授权内，合理的替代路线为什么都不足以继续 |
| 需要越权的资源或访问 | stopped，stop_reason=blocked；或 waiting_user，请求授权 |
| 需要用户做实质方向选择（第 6 节） | waiting_user，附选项与推荐 |
| 证据表明应停 | 写 kill/park 决定 → stopped，stop_reason=evidence_based_stop |
| 以上都不成立 | 写 next_action，进入下一轮 |

不要在每个技能完成后把控制权交回用户；只在上表规定的情况下停。

## 4. 新证据要回到正确的位置

| 发现 | 回到 | 记录变化 |
|---|---|---|
| 检索到同条件下同机制的工作（R-1） | research-construct 或 research-evolve，修订贡献；若无实质差异，则做有依据的停止 | 新 H，或 kill/park 决定 |
| 代码或数据推翻了问题前提（P1-4/P1-6） | research-diagnose | 新 Q 版本；focus 清空或指向修订后的候选。若改变的是用户的硬目标，转 waiting_user |
| 审查发现缺少必要信号（P2-4） | research-ideate 或 research-construct，带着 structural requirement | 新 H |
| 测试太贵或不可行（P2-5） | research-evolve 的 feasibility | 新 activity（T），H 不变 |
| 两种解释无法区分（R-6） | research-test 设计判别实验，或进入 GRILL | 新 T，或保留并存 |
| 主张超出证据 | research-report 收窄措辞 | 只改视图，或新 H |

回退只重做受影响的部分，旧记录保留。回退本身算一个动作，也要写检查点。

## 5. GRILL：多视角独立审查

在两种时候进入 GRILL：focus 的承重 claim 第一次需要 finding 时；准备收尾前仍有 contested 时。按 [review-context](review-context.md) 准备审查包：隐藏旧分数和推荐，保留原始反证和约束。

PPT 的三个视角：

| 视角 | 要回答的问题 |
|---|---|
| 召回 | 还有哪些相近机制或已有工作？换个名字的同一方法？ |
| 对手审查 | 这条解释最容易在哪里失败？最强的竞争解释是什么？ |
| 对抗攻击 | 对幸存的主张，能否构造合法反例或找到击穿它的观察？ |

- 三个视角**按问题选用**，不是每次都派齐三个：
  - 贡献依赖"没人做过"，或者跨领域的来源不清 → 召回；
  - 同样的观察可能来自另一种机制 → 对手审查；
  - 存在承重的全称主张，或者可以构造可执行的反例 → 对抗攻击。

  简单的引文核对不需要独立审查。
- 宿主支持子 Agent 时（Claude Code 中是插件自带的 `research-grill` agent），每个选用的视角起一个独立上下文。审查包里要包含：方法的完整定义和推导、原始反证、约束条件、相关方法文件的绝对路径（`references/methods/critique.md`、`grounding.md`、`falsification_reaudit.md` 等），以及本地论文检索的可用方式。隐藏旧分数和推荐结论，但不要删掉方法成立所需的推导。
- 不支持时，顺序自查，并在 finding 的 rationale 里注明"自查"。
- 汇总时保留分歧，逐条标出证据，不按票数判真。每个 claim 写一条 finding；有效的反例走 research-evolve 或 diagnose。
- 只有分歧真的影响下一步投入时，才给用户选项（补测 / 换条件 / 收尾）。

## 6. 什么时候必须停下来问人

- 改变用户明确的目标、硬约束或研究对象（即 Q 的实质变化）。
- 动用 forbidden 中的资源，或授权之外的资源：训练、付费、长时间 GPU、改动共享代码。
- 两个方向在证据上并存，而选择取决于用户的偏好或资源。

判断原则是"这个决定归谁、是否已有授权"。普通的数据缺口和科学分歧，由 Agent 先去查证或设计判别检查，不因为存在分歧就问人。

问的时候给 2–4 个选项、推荐项、各自代价，写入 `question_for_user`。用户回答后，先把回答写成 human feedback，再在新的检查点里通过 `user_input` 引用它，把 status 改回 active；没有这条回答，后端拒绝恢复。只是打开项目、读取记录，不算用户授权继续。

## 7. 总览与收尾

- 每 5 个动作，以及收尾之前，做一次总览（类似 Co-Scientist 的 metareview）。内容包括：已知与未知、最强反证、重复出现的失败模式、预算余量。写成一条 material（source=`overview`），并据此更新 open_issues。重复的失败模式要变成具体约束，而不是继续换说法重试。
- 收尾时 research-report 生成 Card（默认构造卡；用户要求时加方向卡或挑战卡），research-decide 写 pursue/refine 决定，`workflow_check` 通过后写 done。
- 交给用户的最终回复：交付状态、验收表、Card 位置、最小判别实验、最强剩余风险、下一步建议。done 只表示里程碑达成，不表示方法有效。

## 8. 恢复

1. 找到最新的 workflow 记录，读 `workflow_check` 和最近 3 个检查点。
2. waiting_user：先把问题转给用户。paused：确认用户希望继续。
3. 状态为 running 的 activity，先核实进程或作业身份，不能凭旧状态重启。
4. 从 next_action 继续；历史里已有的动作键不重复执行。
5. 用户改变了预算或授权：写一个新的检查点版本，在 open_issues 记下原因。

## 9. 已知限制

- 检查点在动作**执行之后**才写入。如果动作执行完、检查点还没写就中断了，恢复时看不到这个动作，可能重复执行。只读检索重复无妨；训练、付费、外部提交这类动作，恢复时要先核对实际产物或作业，不能盲目重放。
- MCP 不拦截 Bash。时间、成本、GPU 的硬上限要靠宿主的超时、权限设置或 runner；协议里的预算只是记账，不是强制执行。
- 验收是结构检查：只核对记录的类型、版本和链接是否成立。后端不区分一条 material 是代码、论文还是笔记，所以证据是否真实、是否相关，要靠审查和宿主轨迹来判断。
- human feedback 由 Agent 代为写入，`source=human` 只是一项记录声明，不是不可伪造的授权。

## 10. 检查点示例

```json
{"goal": "经文献、代码与反例检查的研究方案", "project": {"id": "q", "version": 2},
 "criteria": ["question", "literature", "code", "counterexamples", "test_plan", "card", "decision"],
 "max_actions": 20, "actions_used": 6, "status": "active", "stage": "grill",
 "focus": {"id": "h", "version": 1},
 "evidence": {"question": [{"id": "q", "version": 2}], "literature": [{"id": "f-prior", "version": 1}],
              "code": [{"id": "m-store", "version": 1}]},
 "authorized": ["检索", "读代码", "CPU 上小于 5 分钟的本地探测"], "forbidden": ["训练", "付费 API"],
 "last_action": {"key": "code:q@2:store-path", "skill": "research-code", "question": "帧是否被保存？",
                 "outcome": "advanced", "summary": "store() 保存全部帧；问题在检索", "outputs": [{"id": "m-store", "version": 1}]},
 "open_issues": ["h@1 的 c2 尚无独立审查"],
 "next_action": {"skill": "research-review", "question": "c1/c2 能否经受三视角审查？", "why": "counterexamples 未达标"}}
```

示例字段与 [record-api](../../docs/record-api.md) 一致；ID 与内容为虚构，不代表已完成的研究。
