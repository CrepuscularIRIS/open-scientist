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

| criterion | 达标条件（`workflow_check` 会机械核对） | 负责技能 |
|---|---|---|
| question | 引用当前版本的 project | workflow / diagnose |
| literature | 至少一条带材料证据的 finding（supported/partial/contradicted/contested） | research-retrieve，再 review grounding |
| code | 至少一条带 locator（文件:行）的代码或数据 material | research-code |
| counterexamples | focus 候选的当前版本：每个 claim 都有 finding；所有 contradicted/contested 都已 disposition | research-review（GRILL），必要时 research-evolve |
| test_plan | 一个 activity，其 inputs 包含 focus 当前版本，且不是 failed | research-test |
| card | 一份在 focus 当前版本之后写入的 Card material | research-report |
| decision | 针对 focus 当前版本或当前 project 的 pursue/refine 决定 | research-decide |

只有 `workflow_check` 返回 ready，status=done 才能写入；否则后端拒绝。H 一旦修订，依赖它的 test_plan、card、decision、counterexamples 会自动失效，需要局部重做；question、literature、code 不受影响。这是结构检查，不判断科学真假：引用的记录本身必须是真实读过、真实运行过的东西。

另一种合法结局是**有依据的停止**：写一个附带 material 证据的 kill/park 决定，再把 workflow 设为 stopped，stop_reason=`evidence_based_stop`。例如问题已被前人解决、目标在现有数据上不可识别、价值不足。这和"做不下去"不同。

## 3. 每一轮：一个动作，一个检查点

```text
观察 → 选缺口 → 查重 → 执行一个技能 → 写记录 → 写检查点 → 检查是否该停
```

1. **观察。** 读最新的 workflow 和 `workflow_check`，只按需读取相关记录。`records_context` 只在启动、恢复和每次总览时读全量。
2. **选缺口。** 优先处理会改变下一决定的 open_issue（回退信号见第 4 节）；没有时，按下面的顺序补第一个未达标的验收项：

   `question → literature ∥ code → 确定 focus → counterexamples → test_plan → card → decision`

   还没有 focus 时，走 ABDUCE：先 research-diagnose，再 research-ideate 或 research-construct，产出一个 candidate，并把它设为 focus。
3. **查重。** 为动作起一个键：`<技能>:<对象@版本>:<意图>`，例如 `retrieve:h@2:alias-search`。如果历史检查点里已有同一个键，就不要重做；确有新理由时加 `#2` 并在 summary 写明原因。后端会拒绝重复的键。
4. **执行。** 按共同合同的六项交接调用一个专项技能。每个技能**第一次**用到时，通过宿主的技能机制加载它（Claude Code 用 Skill 工具调用 `open-scientist:research-…`，Codex 用 `$research-…`），按其中的方法执行；同一技能再次使用时可以沿用已加载的内容。不要凭印象代替专项方法。宿主工具负责实际检索、读代码和运行获授权的探测；不能越过 authorized / forbidden。
5. **先写研究记录**（material、finding、candidate、activity、decision），**再写检查点**：
   - actions_used +1
   - last_action：键、技能、问题、outcome（advanced / no_change / failed / needs_user）、summary、outputs
   - 更新 evidence、focus、stage、open_issues、next_action
6. **检查是否该停**（Co-Scientist 的终止判断，每个检查点之后都要做）：

| 情况 | 动作 |
|---|---|
| `workflow_check` ready | 收尾（第 7 节）→ status=done |
| actions_used 达到 max_actions | stopped，stop_reason=budget；summary 写出下一步本该做什么 |
| 连续两次 outcome 为 no_change/failed，且没有新增记录 | stopped，stop_reason=no_progress；写明缺的是哪种信息或资源 |
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

- 宿主支持子 Agent 时（Claude Code 中是插件自带的 `research-grill` agent），每个视角起一个独立上下文，只交审查包，不交作者的推理过程。
- 不支持时，顺序自查，并在 finding 的 rationale 里注明"自查"。
- 汇总时保留分歧，逐条标出证据，不按票数判真。每个 claim 写一条 finding；有效的反例走 research-evolve 或 diagnose。
- 只有分歧真的影响下一步投入时，才给用户选项（补测 / 换条件 / 收尾）。

## 6. 什么时候必须停下来问人

- 改变用户明确的目标、硬约束或研究对象（即 Q 的实质变化）。
- 动用 forbidden 中的资源，或授权之外的资源：训练、付费、长时间 GPU、改动共享代码。
- 两个方向在证据上并存，而选择取决于用户的偏好或资源。

问的时候给 2–4 个选项、推荐项、各自代价，写入 `question_for_user`。用户回答后，先写 feedback 和 disposition，再把 status 改回 active。

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

## 9. 检查点示例

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
