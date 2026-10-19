> Method text carried from Open Scientist 0.2 (`skills/research-test/SKILL.md`), kept whole. In 0.3 the study loop ([prompts/study/](../../../prompts/study/)) decides when this method runs, and records are written through a study commit ([contracts](../../../prompts/study/contracts.md)), not through the 0.2 MCP write tools or the auto-mode workflow record. Where this text names those, follow the commit contract instead; the method itself is unchanged.

# 将一个研究主张接到可执行、可解释的最小测试

目标是减少当前关键不确定性，而不是先完成一套庞大的实验矩阵。测试可以检验“问题是否存在”、内部程序是否一致、哪种解释更可能，或同条件下是否真的改善。一次测试只承担它能支持的判断。

开始读取 [共同合同](../../contracts/research-contract.md) 与当前 Q/H/T 版本。内部机制检查按需展开 [coherence trace](../../methods/coherence_trace.md)，这里保留 RS 的 T1–T5 推演与反例交接。实验区分力的定义共用 [falsification re-audit](../../methods/falsification_reaudit.md)，避免为生成、审查与测试各写一套不同标准。

## 需要哪些输入

| 输入 | 必须说清楚的内容 |
|---|---|
| 被检验主张 | 精确句子、范围、量词、candidate claim ID 或问题前提 |
| 版本 | H及Q的确切版本；若只是测量诊断，说明没有H |
| 最强竞争解释 | 同样能解释已有现象的 rival，不选明显弱的稻草人 |
| 预测 | 当前方法和 rival 各预期什么；什么结果会改变决定 |
| 可观测量 | 哪个实际代码/数据/仪器提供，何时可得 |
| 已知反证 | 原始实例、运行和争议处置；不可删去 |
| 资源与授权 | 时间、内存、GPU/API边界；未知保持未知 |

当前没有可区分预测时，先回 [research-construct](construct.md) 或 [research-diagnose](diagnose.md)，不以“先跑起来再找意义”替代计划。

## 步骤 1：选择最便宜但能区分的测试

比较静态事实、受控算术、单样例执行、小规模真实数据与正式实验分别能回答什么。可以用很小的测试发现致命结构问题；不能把小规模支持自动外推为真实总体收益。

优先检查风险最大的承重步骤。原机制对自己“最难部分”的解释也需要受审；损失信息可能发生在不起眼的预处理，而非作者最强调的模块。

写一个简洁的判别表：结果A在H下为何可能、在rival下为何不同；结果B会如何改变下一步。如果两种解释对所有可观察结果都相同，这次测试不能选赢家，即便便宜且容易完成。

若测试成本超出资源，把固定H与所需区分传给 [research-evolve](evolve.md) 的 feasibility。代理系统是否保留关键因果条件需要论证；只保留接口形状不够。

## 步骤 2：在执行前记录测试计划

计划包含：目标主张、输入与版本、脚本/命令、数据划分/样例、基线、预测、指标及计算方式、预算上限、失败/停止条件、输出位置。没有不确定性估计需求的纯算术无需硬塞多seed；涉及总体效果时考虑独立单位、方差与适当重复。

记录为 activity `status=plan`，关联准确输入版本。进入 running 后冻结原计划；修改路线要新 activity，不覆盖之前预测。测试已经执行但事前没记计划时，可以如实登记 completed，但明确这是事后记录，不能冒称预注册。

避免把阈值设成根据已见结果必然满足。探索得到的阈值可以产生新计划；旧结果不能倒过来验证新阈值。

## 步骤 3：内部程序按 T1–T5 检查

这五项是检查动作，不是五个独立服务。适用项有明确内容，不适用项说明理由，不制造假对照。

1. **T1 数据流与形式化**：引用原步骤，列消耗与产出、类型/维度、循环依赖、未绑定参数；有两种合理语义时分别测试，发现标注 reading-dependent。估计器须匹配声明的量、总体和条件。
2. **T2 数值推演**：选小而合法的具体实例，真正计算中间量。有可用且获授权的执行工具就运行短脚本，保存输入与输出；手算或建议代码标 unexecuted。构造恒等式或用一边定义分母得到的1.0不是证据。
3. **T3 边界探测**：检查规格允许的空集、单元素、并列、极值与预算边界。无合法性依据的怪异输入不能反驳明确排除它的主张。
4. **T4 主张到步骤**：哪一步建立性质；是已推导、条件成立、经验预测还是过强措辞。一个合法反例能否定全称命题；有利实例不能建立定理或平均效果。
5. **T5 同约束朴素基线**：独立构造更简单的比较者，信息、预算、时序与部署条件一致。单例相等可能是测试区分不足，不能立刻推出全局等价。

完整方法及原文保留段落见 [coherence trace](../../methods/coherence_trace.md)。改变原核心主张以避开失败是研究修订，不能叫“只是修一个词”。

## 步骤 4：把计划交给宿主执行

MCP记录层不执行命令、不启动后台worker、不选择模型。用宿主提供的本地/远程工具完成已授权操作；不存在必须设置某个模型槽位的前置条件。

实际执行记录：命令、工作目录、代码commit/dirty状态、配置、输入身份、设备/依赖、开始结束时间、退出码、stdout/stderr与产物地址。大文件保留引用和hash，避免整份输出塞入每条记录。

若任务越过当前预算/权限，保留已经完成的准备与具体测试计划后说明缺口。已有授权不重复索要。单纯需要GPU不代表自动允许开训练或新租实例。

中断时保存可恢复位置；恢复先核进程/作业身份，不能用旧PID决定重启或杀进程。不要承诺“稍后监控”而未创建用户明确要求的监控。

## 步骤 5：按结果类型解释，不能只填 pass/fail

| 类型 | 证据特征 | 下一动作 |
|---|---|---|
| 执行/测量失败 | OOM、输入缺失、指标脚本不正确、配置未加载 | failed或测量finding；修工具/协议，未检验部分仍unknown |
| 机制反证 | 合法条件下与明确主张矛盾，原始输出可核 | 固定原主张与范围，review核争议，evolve或diagnose修订 |
| 区分力不足 | 两解释预测相同，或对照也获得相同信号 | 修改T而非宣布两者都正确 |
| 局部支持 | 结果符合H并排除指定rival，但范围有限 | claim-scoped partial/supported，写清条件与未排除解释 |
| 尚未知 | 原始输出缺失、来源不明、数值不确定性太大 | 指明缺口，不能按直觉选择成功/失败 |

Activity completed 只说明执行结束。支持关系由 assessment单独描述，原始结果是 material。空结果、运行失败和负结果须分别记录。

## 步骤 6：失败交接要能指导下一构造

对真正承重的反例给出：原主张、原句、实例合法性、脚本与输出、解释依赖、受影响claim。进一步能推出结构需求时，说明：

- 必需的信号、能力或对比究竟是什么。
- 在当前约束下哪些来源可用，哪些被排除，排除理由和成本。
- 哪些测量、控制或实现可挽救，哪些主张应退役。

没有证据推导具体需求时写未知，不发明“增加一个模块”作为万能修复。反例只改变H就回construct/evolve；共同问题前提错误才回diagnose；有效但不值得做交decide。没有新结构或新信息时结束该分支。

## 记录示例

实际payload见 [record-api](../../../docs/record-api.md)。测试步骤描述放activity.plan；执行输出先写material，再将引用放activity.outputs；最后用finding绑定确切候选claim。

```json
{"type":"finding","subject":{"id":"h1","version":1},"claim":"all_inputs_recoverable","judgment":"contradicted","evidence":[{"id":"counterexample-output","version":1}],"rationale":"这个合法输入使两个状态映射成同一表示，解码无法区分。","scope":"仅反驳原文声明的全称可恢复保证；没有测量真实分布平均收益。"}
```

上述引用须已经存在。示例为payload形状，不代表本次已经完成了一个科研实验。

## 贯穿例：失败运行与合法反例同时存在

一项GPU测试因OOM失败，另一个CPU小实例证明声称“所有输入可恢复”的编码将两种合法输入映射到同一点。OOM只限制原测试是否执行；合法碰撞已经反驳全称保证。不能把两者平均为“结果不稳定”，也不能换一个更便宜的有利例子冲淡反例。

先保存两项不同活动和原始材料。若继续研究，明确退役原全称主张并建立新H，或证明该实例违反原先已声明的前提；不得事后新增前提抹掉旧失败。新测试仍须有区分力。

## 验收与停止

能够从材料重建运行、看到原预测与反例的对应关系，才算完成一次执行桥接。计划、脚本存在、命令启动或终端返回都不足以证明科研闭环。边界清楚的unknown比假定success更有用；本技能完成不要求实验支持原假设。

## 来源与适配

保留RS coherence的T1–T5、同条件naive、原句/执行证据/structural_requirement；接Co review的rival与testability、feasibility中的替代测试，以及Companion的riskiest assumption与继续投入判断。新增真正的plan→host execution→raw material→claim finding接口；取消固定阶段文件与自动merge，修正原文过度否定单反例的措辞。
