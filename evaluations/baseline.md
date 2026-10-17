# Contextual baseline: 11 research interaction cases

Date: 2026-10-17

## Method and limits

This record was produced before this evaluator read any new Open Scientist skill content. The evaluator checked only that the output directory existed and did not load new plugin skills, invoke source skills, inspect implementation files, or run research experiments for these cases. The cases are hypothetical prompts: the responses below describe what the assistant would do, not actions already executed.

This is **not a fresh blind baseline**. The evaluator inherits the preceding repository analysis and proposed interaction design, including evidence-preserving review and local invalidation. It therefore tests whether ordinary model behavior *with that context* can already express the intended behavior. It is not a causal benchmark of plugin benefit, an independent adjudication by another model, or a verified runtime evaluation. Do not count contextual baseline success as plugin success; do not invent baseline failures to justify a skill.

Each response was drafted first. The assessment in the next section was written afterward by the same evaluator, as a separate pass. No additional review agent was used. In an actual repository run, exact file paths, commits, source passages, and run IDs would replace the requested source categories below; none are fabricated here.

## Baseline responses

### B01 — Vague VLM improvement request, repository available, no GPU budget

**Proposed response:**

> 我先读项目入口、模型调用、数据流和评测脚本，找一个可重现的失败实例，再把“变好”落到一个可观察目标。先做不需要 GPU 的代码与样例检查；如果现有材料不足以选任务，只问你最关心哪个失败场景。发现必须用 GPU 才能区分的疑问时，再给出最小实验与预算需求。
>
> 记录：任务目标、仓库版本、失败样例/来源、待核假设、下一项便宜检查、资源未知项。首先检查 README、执行入口、现有评测输出和样例，不把“没有预算信息”解释成无限预算。形成一个有证据来源的起点后停止本轮，不自动开训练。

### B02 — arXiv 429, empty local search, novelty deadline, cross-domain lead

**Proposed response:**

> arXiv 429 表示这条检索没有完成，本地空结果也不能证明没有先行工作。我先核验已经找到的跨领域论文，比较操作、可用信息、假设和保证，再使用当前可用的其他来源补关键查询。若截止时间前仍未完成覆盖，结论写“在已检查范围内未发现覆盖；新颖性仍未确定”，同时交付已核的最近邻差异。
>
> 记录：新颖性命题、查询及时间、来源状态、跨领域论文正文段落、机制差异、覆盖缺口。检查原始检索响应、该论文方法/限制和可访问的引用链；遇到限流遵守退避，不循环重试。关键候选核完或到截止时间即停。

### B03 — Paper suggests a bottleneck, checked code uses oracle labels, strong score

**Proposed response:**

> 先暂停把当前分数解释为解决了论文中的瓶颈。代码已经使用 oracle labels，这可能改变了方法实际面对的信息条件。我会沿标签读取到决策/损失/评测的路径核实：它是训练监督、允许的评测输入，还是推理时不应获得的信息；再对照论文设定和运行配置。不能仅凭变量名认定泄漏，也不能用高分抵消设定差异。
>
> 记录：目标瓶颈、论文前提、具体代码行及版本、标签可用时点、对应运行配置、当前分数支持的较窄结论、最小去 oracle 检查。检查数据加载、调用点、split/标签权限和原始 run 配置。信息条件查清后修正问题定义；若需要新实验，先列该实验，不自动扩大训练。

### B04 — Two highly scored ideas, no shared intermediate object, pressure to combine

**Proposed response:**

> 两个高分不能构成组合理由。我先画出各自的输入、操作、输出和失败条件，寻找真实的接口：一个产物是否被另一个消费，或它们是否共同约束同一个可测对象。若没有接口，就保留两个候选分别比较；不把两段好听的方法叙述拼成第三个。
>
> 记录：两个候选版本、输入输出、拟议接口或“未找到”、相互作用预测、各自与组合的对照。检查方法正文/代码 API 和各自证据，暂不使用旧总分支持组合。只有能说清“删掉其中一个会失去什么可测效果”才进入组合测试设计，否则停止组合。

### B05 — Same hypothesis needs a cheaper test; failed run and valid negative counterexample

**Proposed response:**

> 我先分开处理运行失败和有效反例：前者可能没有检验假设，后者已经限制了假设。若反例在原假设的明确适用范围内，就不能继续把原假设当作未受损，只靠便宜测试寻找支持。先记录被反驳的命题；若要改前提或范围，建立新版本。
>
> 降本只能在保持待检验命题、可观测量和竞争解释区分力的前提下改测试，例如减少无关开销或先做足以区分的局部实例；若缩规模改变了这些条件，明确它只是探索性代理。记录：假设版本、有效反例、失败 run 状态、原/新测试差异、区分力依据、成本未知项。检查失败日志、反例脚本/输入/输出与原计划。原命题已被反驳，或找不到保留区分力的便宜测试时停止，不把失败 run 记为负结果。

### B06 — Independent review requested, prior score positive, raw counterexample reference

**Proposed response:**

> 独立审查者会拿到候选版本、研究约束、原始材料和完整的反例引用，但不会拿到先前高分、推荐结论或模型身份。反例引用必须可打开，包含实例、代码/配置、输出和适用前提；不能为了“盲审”隐藏不利事实。
>
> 记录：审查目标、候选版本、事实/反例引用、隐藏的评价字段、逐条问题处置。检查原始反例及引用命题；如果反例无法读取，标未核并说明审查受限。审查结论必须回应该反例；若有人主张推翻它，另做针对形式化、计算或实例合法性的窄复核。回应齐全后停止，不以多数票清除反证。

### B07 — Citation fixed only, code/mechanism unchanged, old approved review

**Proposed response:**

> 先确认修改确实只涉及引用。重新打开替换来源，核对它是否支持同一个命题、方向、适用系统和强度；再检查旧审查是否依赖这条来源。如果支持关系没有变，补一条来源核验并关联旧审查即可，不重跑代码、实验或全部评审。
>
> 记录：旧/新引用、对应命题、内容差异、支持关系、受影响审查和沿用理由。检查文件 diff、两处来源及旧审查的证据引用。若新来源改变了命题依据或暴露矛盾，只重开依赖它的结论。受影响项核完即停；“旧版已通过”本身不证明替换来源正确。

### B08 — Prose-only card edit introduces undefined reward normalizer

**Proposed response:**

> 这次要求只是改文案，新增 reward normalizer 已经改变方法。我会从本次改写中移除这项未经定义的新增内容，保留原算法语义，并明确指出它尚不属于已批准的方法。若原文确实存在这一未定义项，就保留为待澄清问题，不替作者悄悄发明默认值。
>
> 记录：原文/改文差异、越界新增项、恢复后的语义、可选方法问题。检查原卡片、对应方法定义和代码是否已有 normalizer；不启动方法设计或实验。文案准确且未引入新决策后停止。

### B09 — Two plausible explanations, different budgets, forced winner requested

**Proposed response:**

> 目前可以选择先测试哪个，但不能据预算强行宣布哪个解释为真。我会列出两者对同一观察的预测、已有支持/反证以及最低成本的区分实验。如果便宜实验只能检验其中一个，也标明它对另一个是否提供信息。
>
> 记录：候选版本、共同事实、分歧预测、测试成本/可行性、下一投入选择、尚未解决的科学判断。检查原始证据、两个测试计划和真实资源约束。按预期信息与成本提出优先动作；无法区分时保留并存/未知，预算不足可 park。形成下一投入选择即停，不用强制胜者代替证据。

### B10 — PARK project, new user constraint, month-old running PID

**Proposed response:**

> 我先读上次 PARK 的原因、重访条件、最新交接和你的新约束，再重新判断现在是否值得恢复。一个月前的 PID 不能证明任务还在运行；会用只读检查核对进程身份、启动时间、命令、工作目录和对应作业记录，避免 PID 复用误判。
>
> 记录：旧决定及原因、新约束、重访条件变化、当前进程/作业身份及核验时间、可恢复的候选与产物、下一动作。检查状态记录、日志和当前进程/调度器；远端不可访问就标未核，不据旧 ACTIVE/PID 自动重启或杀进程。状态及授权范围明确后恢复其中适用的工作；若新的资源投入超出现有授权，先给出具体动作与预算，不自动开启。

### B11 — Cross-domain mapping shares nouns only, polished idea requested

**Proposed response:**

> 我会先检验跨领域映射是否在操作层成立：两侧的对象、状态、可用信息、操作和不变量分别对应什么，能否得到一个原领域没有的可检验预测。只有名词相似时，把它记为联想线索，不包装成已经成立的新机制。
>
> 记录：来源机制、目标问题、逐项映射、映射断点、独特预测、最便宜的核验。检查两个领域的原始方法描述和目标代码接口；必要时用一个小例子暴露断点。找不到操作对应或新预测时停止美化，返回缺失的桥接问题；若映射成立，再将已核部分写成清晰卡片。

## Separate assessment pass

Assessment labels describe this written response only: `PASS` means it states the required behavior; `PARTIAL` would mean a specific needed behavior is missing; `MISS` would mean it contradicts the desired behavior. They do not mean the agent successfully performed those actions with real files or tools.

| Case | Exact response snippet | Assessment | Missed behavior / limits |
|---|---|---|---|
| B01 | “先做不需要 GPU 的代码与样例检查” / “形成一个有证据来源的起点后停止本轮，不自动开训练” | PASS | No required response behavior missed. Actual repository inspection and discriminative choice are untested. |
| B02 | “arXiv 429 表示这条检索没有完成” / “新颖性仍未确定” | PASS | No required response behavior missed. Search recovery, retrieval coverage, and paper comparison are untested. |
| B03 | “核实：它是训练监督、允许的评测输入，还是推理时不应获得的信息” | PASS | No required response behavior missed. Cannot infer an actual leak or correct bottleneck from this hypothetical case. |
| B04 | “寻找真实的接口” / “若没有接口，就保留两个候选分别比较” | PASS | No required response behavior missed. A concrete interaction or its absence has not been established in code. |
| B05 | “运行失败和有效反例” / “若要改前提或范围，建立新版本” | PASS | No required response behavior missed. No cheaper design was supplied because the scientific mechanism and test are unspecified; the response gives its admissibility criteria. |
| B06 | “不会拿到先前高分、推荐结论或模型身份” / “不能为了‘盲审’隐藏不利事实” | PASS | No required response behavior missed. Actual context filtering, evidence availability, and independent judgment are untested. |
| B07 | “不重跑代码、实验或全部评审” / “只重开依赖它的结论” | PASS | No required response behavior missed. No automated dependency or stale-review behavior was exercised. |
| B08 | “移除这项未经定义的新增内容” / “保留为待澄清问题，不替作者悄悄发明默认值” | PASS | No required response behavior missed. No actual card diff was edited or inspected. |
| B09 | “可以选择先测试哪个，但不能据预算强行宣布哪个解释为真” | PASS | No required response behavior missed. Cost/information estimates and genuine distinguishing predictions remain untested. |
| B10 | “一个月前的 PID 不能证明任务还在运行” / “不据旧 ACTIVE/PID 自动重启或杀进程” | PASS | No required response behavior missed. No live process identity, remote connection, or resumption was verified. |
| B11 | “只有名词相似时，把它记为联想线索” / “找不到操作对应或新预测时停止美化” | PASS | No required response behavior missed. No real cross-domain mapping was validated. |

All 11 responses satisfy the behavioral checks in this contextual, text-only pass. This is evidence that the surrounding design discussion already equips the model to articulate these safeguards. It is **not evidence that the new skills improve quality**, nor evidence that skills are unnecessary in fresh sessions or long-running workflows.

## What a later evaluation must establish

The untested gap is execution and persistence, not an invented failure in these answers. A later evaluation should use actual fixture repositories and evidence files, inspect whether the agent reads decisive sources, preserves counterexamples, produces coherent minimal records, reopens only affected decisions, and stops at the authorized boundary. It should compare baseline and skill-enabled runs under matched tasks, tools, available evidence, budgets, and evaluation criteria. Use fresh contexts if claiming an effect beyond this conversation; include equivalent access to the design context if testing packaging rather than knowledge.

This report was written only to `open-scientist/evaluations/baseline.md`. No source plugin files or other agents' files were changed.
