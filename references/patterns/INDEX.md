# 研究模式索引：15 主模式与 31 子模式

这是按研究问题查找历史原文的完整目录。原文逐字节保存在 `vendor/`，出处和校验值见 [source-manifest.json](../../docs/source-manifest.json)。下表是 Open Scientist 的检索摘要，不是原作者的逐字引文。

先用已观察到的障碍检索，确定需要某个动作后再展开原文。一次可以使用零张、一张或多张卡；没有模式数量配额，没有“未命中就必须挑最像的一张”的要求。原库的阶段门禁、硬编码路径、模型席位与提示词指令属于历史材料，不进入活动工作流。活动方法以 [研究合同](../contracts/research-contract.md) 及 `references/methods/` 为准。

阶段简称：**查证**＝读文献/代码/数据；**定题**＝问题和观察模型；**构造**＝机制；**测试**＝协议/测量；**审查**＝反例与证据；**改案**＝修改问题、候选或测试活动；**综合**＝结论与下一步。它们是使用场景，不是必须依次运行的阶段。

模式来自特定论文语料的归纳，原文的论文数量、Accept/Reject/Oral lessons 与“需要定理”等评价均是来源中的说法；迁移完整性不代表这些归纳已独立科学验证。拒稿教训应产生可检验问题，不能直接裁决另一领域的研究质量。类比的实体、约束和观测假设需要重新核验。

## 15 个主模式

| 原始 ID / 完整原文 | 触发问题 | 核心动作 | 可用场景 | 适用边界 |
|---|---|---|---|---|
| [assumption_audit_and_pivot][assumption_audit_and_pivot] | 关键前提不符合真实场景 | 明确前提，放松或反例化，再推导预测 | 查证、定题、构造、审查、改案 | 先证实前提负载；去掉无关假设没有贡献 |
| [architectural_operator_substitution][architectural_operator_substitution] | 某算子/表示造成成本或表达瓶颈 | 用替代算子保住所需性质 | 查代码、构造、测试、改案 | 更便宜不等于保真；比较同资源限制 |
| [generative_process_redesign][generative_process_redesign] | 继承的生成步骤成为瓶颈 | 将固定组件变为设计变量 | 查代码、构造、测试、改案 | 需区分表示、采样链和条件注入问题 |
| [controlled_diagnostic_design][controlled_diagnostic_design] | 测量可能混入捷径或混淆 | 独立操纵混淆，测真实属性 | 查证、定题、测试、审查、综合 | 独立 oracle；合成结论不能自动推广 |
| [unify_into_shared_representation][unify_into_shared_representation] | 多模态/任务被割裂处理 | 构造共享表示或接口 | 查代码、构造、改案 | 统一格式不自动产生科学收益 |
| [reframe_as_solvable_object][reframe_as_solvable_object] | 原问题难求解且存在结构同构 | 映射到成熟问题类并验证映射 | 定题、跨域查证、构造、改案 | 必须核验对象、前提和约束，而非只借名词 |
| [self_supervised_signal_engineering][self_supervised_signal_engineering] | 标签缺失但有可用内部/生成信号 | 构造代理监督并测试有效性 | 查数据、构造、测试、审查 | 代理与真实目标可能错位或形成反馈循环 |
| [structural_prior_encoding][structural_prior_encoding] | 领域结构已知而模型需重复学习 | 将不变量/结构编码到过程 | 定题、构造、审查 | 结构必须在目标系统成立；不要假设普适 |
| [algebraic_equivalence_unification][algebraic_equivalence_unification] | 两过程可能在做同一件事 | 推导等价关系并消去重复步骤 | 查证、构造、审查、简化 | 近似/有限样本情形不能冒充精确等价 |
| [heterogeneous_decomposition][heterogeneous_decomposition] | 统一处理掩盖组件异质性 | 按可测性质分组并差异处理 | 查代码、构造、测试 | 分组依据、代价及漂移均需测量 |
| [decompose_and_delegate][decompose_and_delegate] | 子问题有可靠外部求解器 | 生成结构化中间物并调用可核验求解 | 查代码、构造、审查 | 分工本身不是贡献；核验接口与反馈可靠性 |
| [relax_discrete_search_to_continuous][relax_discrete_search_to_continuous] | 离散设计空间搜索太昂贵 | 连续化或摊销结构搜索 | 构造、测试、改案 | 放松后的可行性与离散回投偏差需验证 |
| [adapt_via_conditioning][adapt_via_conditioning] | 每任务训练不可行 | 将任务表达为条件输入 | 查证、构造、可行性改案 | 验证新任务类别泛化；核算参考库成本 |
| [characterize_limit_then_surpass][characterize_limit_then_surpass] | 方法类存在可刻画的结构极限 | 明确极限，再构造超越该极限的对象 | 定题、构造、证明、审查 | 局部实验不足以证明整个方法类的极限 |
| [targeted_self_supervised_objective][targeted_self_supervised_objective] | 通用目标不捕捉下游属性 | 构造针对该属性的无标签目标 | 构造、测试、审查 | 目标下降不等于目标属性获得或下游改善 |

## 31 个子模式

下列中文短名仅便于检索，原始稳定标识为 C00–C30；父模式关系保留原库。每一条均链接完整 tactical pattern、Step-by-Step、适用条件与失败教训。

| 卡 / 检索短名 | 原父模式 | 触发问题 → 核心动作 | 可用场景 | 适用边界 |
|---|---|---|---|---|
| [C00 固定模型的归因/不确定性][C00] | reframe_as_solvable_object | 需要逐单元责任/置信读数 → 映射为反事实、影响或分解对象 | 查代码、定题、构造、审查 | 归因需扰动核验；固定对象不等于竞争系统 |
| [C01 攻防信号位置][C01] | assumption_audit_and_pivot | 攻防只盯单一表示位置 → 检查被忽略的标签、激活或行为 | 查证、定题、构造、审查 | 威胁模型和可访问权限必须保持一致 |
| [C02 混淆隔离测量][C02] | controlled_diagnostic_design | 指标可能由捷径驱动 → 控制一个混淆并引入独立 oracle | 查代码、定题、测试、审查、综合 | 不用被评模型给自己定真值；限定外推范围 |
| [C03 统一条件输入][C03] | adapt_via_conditioning | 多任务缺少无需训练的适配 → 共享格式和参考资源 | 查证、构造、可行性改案 | 留出整类任务；参考库覆盖不能当作泛化证据 |
| [C04 非均匀压缩][C04] | heterogeneous_decomposition | 少数组件贡献大 → 保住高影响部分，压缩冗余部分 | 查代码、构造、测试 | 衡量真实影响、路由开销及分布变化 |
| [C05 替代识别条件][C05] | assumption_audit_and_pivot | 可识别性前提不成立 → 找另一类已存在的识别信息 | 定题、跨域查证、构造、审查 | 替代信号必须可观测且足够；不能凭类比保证可识别 |
| [C06 概率目标等价][C06] | algebraic_equivalence_unification | 多个损失/散度过程疑似重复 → 推导等价并简化估计链 | 构造、证明、简化、审查 | 声明分布、近似和有限样本条件 |
| [C07 内部信号驱动适配][C07] | self_supervised_signal_engineering | 无标签漂移/更新不稳 → 以内部状态定位故障并作适配信号 | 查代码、构造、测试 | 内部信号的优化不能替代真实任务验证 |
| [C08 生成与过滤数据][C08] | self_supervised_signal_engineering | 数据覆盖或质量不足 → 生成缺失区域并独立过滤 | 查数据、构造、测试 | 检查生成器覆盖、过滤偏差和循环标签 |
| [C09 有界影响中间对象][C09] | architectural_operator_substitution | 隐私/验证成本随维度爆炸 → 经紧凑中间对象约束影响 | 查代码、构造、证明、审查 | 需明确对手、敏感度与形式保证 |
| [C10 补回局部方法丢失结构][C10] | characterize_limit_then_surpass | 局部迭代遗漏关系结构 → 刻画极限并注入结构原语 | 定题、构造、证明、测试 | 注入成本受限；区分类极限与具体实现失败 |
| [C11 预算内选择/获取/停止][C11] | assumption_audit_and_pivot | 选择准则的成本或结构前提可疑 → 放松前提或重构问题类 | 查代码、定题、构造、测试、审查 | 原卡强调性能证明；不将该语料偏好作为所有研究的门禁 |
| [C12 网络结构替代][C12] | architectural_operator_substitution | 参数位置/连接方式卡住成本或表达 → 在对应位置换等价或理论支持结构 | 查代码、构造、简化 | 改变训练或推理条件时等价可能失效 |
| [C13 关系拓扑先验][C13] | structural_prior_encoding | 已知连接关系未被利用 → 将拓扑或图统计编码进模型 | 查数据、构造、审查 | 不把经验相关连接误认为可靠结构 |
| [C14 稠密交互替代][C14] | architectural_operator_substitution | 全对交互/attention昂贵 → 换保住所需性质的低成本算子 | 查代码、构造、测试 | 需证明或实测所需表达/检索能力，非只算复杂度 |
| [C15 生成表示重设][C15] | generative_process_redesign | 继承的几何/结构表示限制输出 → 改表示而非只调loss | 查代码、定题、构造、改案 | 确认任务确实不要求旧表示保护的性质 |
| [C16 对称性构造][C16] | structural_prior_encoding | 存在可刻画变换群 → 构造等变/不变算子 | 定题、构造、证明、审查 | 对称群必须在真实数据与目标上成立 |
| [C17 关系型自监督目标][C17] | targeted_self_supervised_objective | 目标属性是远近/排序/跨视图关系 → 改目标的配对结构 | 构造、测试、审查 | 采样与配对规则可能引入捷径 |
| [C18 模态间接口桥梁][C18] | unify_into_shared_representation | 新模态缺少成熟方法所需接口 → 构造tokenizer/序列化/投影 | 查代码、跨域查证、构造 | 验证接口保留信息；不能只宣称统一 |
| [C19 放松概率保证前提][C19] | assumption_audit_and_pivot | 界依赖过强独立/有界条件 → 找更弱充分条件并重推界 | 定题、证明、审查 | 新条件不可被过程自身破坏，常数须有意义 |
| [C20 正向过程约束逆问题][C20] | structural_prior_encoding | 可描述观测生成/退化 → 利用正向过程构造逆过程 | 查数据、定题、构造、测试 | 模型失配与不可识别性需要显式检查 |
| [C21 缺监督的序列决策][C21] | reframe_as_solvable_object | 无奖励/动作标签但有交互数据 → 重构可制造监督的对象 | 定题、跨域查证、构造 | 伪目标与真实决策价值不能默认一致 |
| [C22 摊销设计搜索][C22] | relax_discrete_search_to_continuous | 每种架构/目标都重新训练太贵 → 共享参数或预测结构选择 | 构造、测试、可行性改案 | 共享权重排序偏差、离散可行性需核验 |
| [C23 采样链组件重设][C23] | generative_process_redesign | 链太长/初始化差/控制僵硬 → 重设先验、时间表或条件注入点 | 查代码、构造、可行性改案 | 对同质量目标比较全成本，保护冻结模型约束 |
| [C24 条件通路与生成空间][C24] | generative_process_redesign | 骨干可生成但控制失败 → 改条件表达/注入方式/工作空间 | 查代码、构造、测试 | 不把控制信号变化的副作用误归因给机制 |
| [C25 可核验求解器协作][C25] | decompose_and_delegate | 子问题有解释器/规划器/求解器 → 生成中间表示，接收可核验反馈 | 查代码、构造、测试、审查 | 检查器覆盖不足不能升级为整体正确性 |
| [C26 比较监督与信用分配][C26] | self_supervised_signal_engineering | 只有偏好/质量评分且信用难分 → 构造比较目标与局部信号 | 查数据、构造、测试 | 评分方向、偏好来源和局部归因需独立验证 |
| [C27 博弈/均衡重构][C27] | reframe_as_solvable_object | 目标源于交互主体激励 → 映射到稳定点并用成熟求解器 | 定题、跨域查证、构造、审查 | 均衡存在/可求/对应原目标须分别论证 |
| [C28 多节点协议前提][C28] | assumption_audit_and_pivot | 协议位置/事件耦合假设可疑 → 调整分布式工作与资源关系 | 查代码、构造、测试、审查 | 通信、同步、失败模型必须进入成本与正确性比较 |
| [C29 收敛目标与正规条件][C29] | assumption_audit_and_pivot | 更新过程保证的目标或条件不适用 → 改条件或度量并推导速率 | 定题、证明、审查 | 不通过换成功定义伪造对原目标的改进 |
| [C30 训练谱结构替代][C30] | architectural_operator_substitution | 病态曲率/谱限制学习 → 重参数化或替换估计过程 | 查代码、构造、测试、审查 | 训练动力学性质不自动说明单次前向能力 |

## 跨阶段检索例

- **C02 不等到生成候选才用。** 读到评测代码用被测模型的共识作真值时，先用 C02 的独立 oracle 检查定题；测试设计再取其单变量干预；出结果后用其生态有效性边界约束结论。
- **C11 不必产生一张 C11 风格论文。** 读到 Agent 只记录选中样本时，用其选择规则检查找观察模型缺口；检索另一领域修复方法；审查时再问预算与选择前提是否相同。
- **C25 可以审查执行层。** 有“工具执行成功”的日志时，检查工具到底验证哪个中间对象；其成功不能代替科学假设成立。
- **C06 与 simplify 可共同使用。** 若两模块可证明等价，删除重复模块，保留等价条件与原版本；若仅在特例等价，则把特例写入测试范围。

组合采用具体问题驱动的移除测试与新预测：如果删除一部分仍保持全部关键预测，它可能是附带工具；如果组合无法说明中间对象、相互作用或区别于亲本的预测，则保留为并列候选。原库 `companion-combos.md` 是历史观察，不是允许/禁止组合的白名单。

[adapt_via_conditioning]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/adapt_via_conditioning.md
[algebraic_equivalence_unification]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/algebraic_equivalence_unification.md
[architectural_operator_substitution]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/architectural_operator_substitution.md
[assumption_audit_and_pivot]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/assumption_audit_and_pivot.md
[characterize_limit_then_surpass]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/characterize_limit_then_surpass.md
[controlled_diagnostic_design]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/controlled_diagnostic_design.md
[decompose_and_delegate]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/decompose_and_delegate.md
[generative_process_redesign]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/generative_process_redesign.md
[heterogeneous_decomposition]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/heterogeneous_decomposition.md
[reframe_as_solvable_object]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/reframe_as_solvable_object.md
[relax_discrete_search_to_continuous]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/relax_discrete_search_to_continuous.md
[self_supervised_signal_engineering]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/self_supervised_signal_engineering.md
[structural_prior_encoding]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/structural_prior_encoding.md
[targeted_self_supervised_objective]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/targeted_self_supervised_objective.md
[unify_into_shared_representation]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/unify_into_shared_representation.md
[C00]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C00.md
[C01]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C01.md
[C02]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C02.md
[C03]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C03.md
[C04]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C04.md
[C05]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C05.md
[C06]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C06.md
[C07]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C07.md
[C08]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C08.md
[C09]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C09.md
[C10]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C10.md
[C11]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C11.md
[C12]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C12.md
[C13]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C13.md
[C14]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C14.md
[C15]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C15.md
[C16]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C16.md
[C17]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C17.md
[C18]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C18.md
[C19]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C19.md
[C20]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C20.md
[C21]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C21.md
[C22]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C22.md
[C23]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C23.md
[C24]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C24.md
[C25]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C25.md
[C26]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C26.md
[C27]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C27.md
[C28]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C28.md
[C29]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C29.md
[C30]: ../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/ideation-sub-patterns/C30.md
