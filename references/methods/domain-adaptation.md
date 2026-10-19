> **Superseded draft.** This was the 0.2 working-tree domain-adaptation method; 0.3 implements it as code (domain build, adaptive assets, study loop — [design](../../docs/design.md)). Kept as history.

# 随课题生成领域方法卡：Companion → 阅读 → 模式 → 研究

这是当前项目的领域适配方法，由宿主 Agent 执行。它不是另一套常驻服务，也不是先离线训练一个覆盖所有领域的分类器。旧 RS 15+31 卡仅作历史词表；新课题的操作、条件和反例必须来自本轮实际材料。

## 1. 什么时候进入

用户开始一个新领域/新问题，当前领域材料不足，或新的代码事实/反证使旧模式不再适用时进入。用户已提供 Companion Seed/讨论结果，就直接消费，不再访谈。用户仅要求核一条引用、修一个bug时，做局部工作，不先重建领域库。

完整回路是：

```text
Companion的问题与结构映射
  → 领域内＋跨领域查询计划
  → 本地论文读取与arXiv元数据采集
  → 选择性读全文/代码，提取有出处的操作签名
  → 按操作与条件归组，保留异例和未归类项
  → 按需补OpenReview决策、审稿理由、实验正反例
  → 生成当前领域方法卡/模式卡
  → diagnose / ideate / construct / test / review
  → 新材料、目标变化和失败反馈触发局部修订
```

先得到可用的几条领域机制，再扩充证据。无需等完整语料/所有标签齐全才能继续研究；但标签未核就不能输出质量统计结论。

## 2. Companion 的输出是搜索 brief，不是最终方案

Agent 从当前对话和项目材料整理一份短 brief，写到项目 `.open-scientist/domain/brief.md`，保留日期与原话来源：

- 目标领域、具体系统/对象、观察到或待核的障碍。
- 用户硬约束、可用代码/数据/信息、当前待决问题。
- 同领域术语、最近邻线索和需要查明的机制。
- 跨领域的**对象—操作—条件映射**及其不成立的可能性。
- 本轮阅读/检索范围与预算、需保留的反例和未知。

跨域不是再给同一查询换两个词。例如选择性观测问题可提名主动学习/因果识别，但必须说明这里的样本、选择过程、反馈和目标量分别对应什么。映射由文献与目标代码核验，不能只凭 Companion 的推荐。

当后续材料改变 brief，保留旧版与变化原因；目标改变涉及用户硬约束时才请求实质选择。新领域不要求用户手工填配置，Agent 负责把 brief 翻成查询。

## 3. 第0步：动态采集与可恢复语料

Agent 创建 `<project>/.open-scientist/domain/queries.json`，字段规范见 [采集器文档](../../docs/corpus-pipeline.md)。`name` 是本轮主题，`start_date/end_date` 来自实际需要，`queries` 每项保留 `lane`（in_domain/cross_domain）、`domain`、查询和上限。跨域分组指查询意图，不是假定所有命中都已具有迁移价值。

本地论文先用现有 `search_papers.py --sources local`，将结果报告与真实PDF路径留在项目中；不要为了建库复制整台机器论文。arXiv持久化采集用：

```bash
python3 <plugin-root>/scripts/build_corpus.py \
  --root <project>/.open-scientist/domain/corpus \
  harvest --config <project>/.open-scientist/domain/queries.json
python3 <plugin-root>/scripts/build_corpus.py \
  --root <project>/.open-scientist/domain/corpus \
  export --output <project>/.open-scientist/domain/papers.jsonl
```

根目录、查询、日期由本次任务推导，禁止把示例 `phase0-pilot.json` 固定套进用户课题。检索前核对已有 scope 和材料；同一配置重新执行是恢复，`--refresh` 建立新的采样快照。检索页不是一致性快照，刷新和大规模覆盖限制见文档。

采集器只保存 arXiv 元数据、原始 Atom、版本与查询来源；不会读全文、核OpenReview标签或产生模式。网络失败保留error和未推进的游标，capped标记采样截断，empty不能解释成新颖。明确ID获取不受主题日期筛选，是补查经典文献的入口。

本地材料和arXiv元数据是两份可追溯来源。只有显式ID/原文互链等证据才能确认同一论文；标题相似只提出匹配候选。不要把旧检索脚本用于展示的同名合并结果升级为语料身份真值。

## 4. 阅读先于机制签名

按当前问题挑同域最近邻、异域机制、负结果/限制和强朴素基线。读过的具体页/节/算法/附录/代码版本写入项目 `readings.jsonl`，每条引用论文snapshot或本地文件hash/路径、实际阅读范围和访问状态。

提取的是 `object → available information → operation → output → claimed effect`，另列成立条件、基线、证据、失败边界和迁移断点。身份、作者主张、reviewer意见、实际观测四类来源分别标明。摘要可产生“待正文确认的签名”，不能作为操作已核的依据。

如果贡献涉及代码行为或测量，调用 research-code 检查实现和输入；论文说了什么与代码做了什么可并存，不自动把一方当权威。没有代码访问能力就标实现未核。

签名存为项目 `signatures.jsonl`，用稳定ID、源snapshot/片段、抽取日期和核查状态。初期由当前Agent逐篇结构化；规模与实际收益足够时才另行选择embedding/聚类算法，不在此阶段自动调用付费批处理。

## 5. 聚类与归并的对象是操作，不是标题风格

先按操作和必要条件列候选机制组。解释组内共同点、组间差别、边界例和不能归类项；同一论文可以有多个签名。不因都属于某个领域就合并，也不强制全部塞进旧15+31分类。

相似性/embedding只提出待核分组。归并前至少核对信息权限、操作步骤、假设、保证与测量目标；不同前提导致不同预测时保留子组。单篇可形成“案例卡”，不足以宣称已发现普适模式。

记录每个组使用哪些signature版本、归并理由、例外和待核问题。数据少时可保留索引列表，不必做HDBSCAN或输出漂亮但无证据的簇图。

## 6. 决策、成功/失败和审稿期望是不同标签

OpenReview补证据时按 venue/year/track 读取配置、submission、review、decision、revision；参考[官方Notes检索文档](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc)。当前采集器尚未实现此连接器，宿主可在授权范围内读取公开原站，保存真实来源；不可将字段空白补为reject。

| 标签 | 对象与可接受依据 | 禁止推断 |
|---|---|---|
| accepted / rejected | 某次投稿、特定会场/年份/轨道的正式决定或官方状态字段 | arXiv只有预印本、搜不到接收记录→rejected |
| withdrawn / desk_rejected / pending / unknown | 对应原站状态/可见性 | 一律合并成研究失败 |
| empirical success / failure | 某条件下具体主张、实验与对照；标作者报告或实际复核 | 接收→方法有效，拒稿→实验失败 |
| gap | 明确目标下现有方法缺少什么及证据 | reviewer认为贡献弱→客观没有研究价值 |
| reviewer expectation | 指定review/元评审中的要求、理由、分歧和时间 | 单个意见→整个领域共识 |

保留原始decision文本、forum/note ID、版本、时间和标准化规则。相似标题匹配不能传播标签；同一工作后来改投接收不覆盖早先拒稿。缺评审、缺决定和不可见分别记录。

没有官方决策仍可做机制卡，review_outcome写not_collected/unknown；不能声称已经形成“成功/失败质量判据”。局部可见样本的比例注明分母，不冒称会议总接收率。统计以论文/研究家族计数，不能把多个版本和review当独立论文。

## 7. 领域卡生成、核查与使用

使用 [领域方法卡模板](../templates/domain-pattern-card.md)。默认面向研究者的一页包含：当前障碍、可复用操作、适用条件、源领域→目标领域映射、关键实例/反例、最小核查和仍未知的部分。详细阅读、公式、标签和计数放附件。

卡片从当前项目证据生成，存于 `.open-scientist/domain/cards/`，用 `INDEX.md` 给出用途和状态；不改插件内静态模式库。状态为 `case`（一个有来源的案例）、`candidate_pattern`（候选归纳）、`checked_for_scope`（对指定范围核查）、`needs_revision`。checked不等于目标迁移成功。

生成后调用 research-review 做窄核查：每个机制是否有原文、源条件是否遗漏、实例是否独立、反例是否被隐藏、标签是否确实官方、目标迁移是否仍是猜测。检查失败就修卡/补阅读，不靠高总分通过。

下游ideate/construct优先读取与当前障碍相关的项目卡及原文，然后才按需读静态RS参考。只带需要的卡，不全量注入；无卡可用时仍允许开放式构造。卡是研究素材，不能成为必须命中的模板。

## 8. 反模式统计与更新

反模式应是“在条件C下反复出现的具体操作缺陷”，例如用目标不可见标签选择样本、缺同预算基线、把相关指标当机制辨识；必须回到每个案例的材料。拒稿理由可以提名待核反模式，不直接证明其因果效应。

统计按领域/年份/会场/问题类型分层；报告纳入、排除、未知和冲突数量及独立工作数。若要训练/验证质量判据，先按论文家族和时间划分，不能用未来decision或终稿泄漏到投稿前预测；小样本只作定性线索。第0步不输出模式胜率或因果排序。

新来源、反例、版本或目标代码变化时，更新相关reading/signature/card，保留旧版和改变原因。不每次重建所有卡，不自动改变全局skill，不在未请求时创建后台抓取或训练。

## 9. 完成边界

第0步完成：查询范围明确，元数据/raw/版本/失败/进度可查，可恢复与导出；状态明确标未读全文、未核决策、未抽签名。领域适配完成：当前待决问题已有足够可核材料和可用卡，剩余覆盖缺口可见，卡的目标迁移仍按实际证据标识。

若用户请求完整自动领域适配，元数据采集成功后继续按本方法选择性阅读与生成，不在“脚本退出0”时结束；若只授权第0步，就交采集结果及后续接口，不擅自扩成全量评审挖掘或模型训练。

本方法结合RS原资产、Companion的结构映射及Co-Scientist的证据/反馈原则。相关文献包括 [PeerRead](https://aclanthology.org/N18-1149/)、[ResearchAgent](https://aclanthology.org/2025.naacl-long.342/)、[Si等的研究想法人评研究](https://arxiv.org/abs/2409.04109)；它们提供数据和方法参考，不是本插件已提升科研质量的证明。
