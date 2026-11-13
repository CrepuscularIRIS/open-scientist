# Open Scientist 0.10

**0.10 的顺序：先量 → 先跑现成的 → 在残余缺口上设计 → 预审 → 实验 → 归因。**
- **现象准入只认实测**（带制度：训练长度 / checkpoint / 评测条件）；`pending` 不能进设计。
- **先验扫描（`prior-sweep`，测量层）**：设计任何方法之前，把官方实现和社区仓里碰到 TARGET 的现成开关全跑一遍，再跑一个上界臂。开关已解决 → 记为集成结果，不设计；判据不可动 → 回问题侧；还有残余 → 只针对残余设计，基线是最好的可部署开关。
- **部署合同**（`<project>/.open-scientist/deploy_contract.md`）：验证器在代码里追部署路径实际读什么；读了合同外的量的卡只能当上界对照，永远不是方法。
- **失败归因（`attribution`）**：训练后没过线的卡，先分清是评测器、实现、机制没起作用、gap 定位，还是方法本身，再决定回溯到哪一层。只有后两种计入结构止损。
- **一条线、两臂**：一次会话只推进一个 TARGET；两张卡跑这条线上两个不同类的臂（两个候选，或候选 + 对照），不跑多 seed。失败的方法清出项目，测量留下；交付物类型由项目固定，不因失败改成分析型。
- **不回避重叠、不强制查重、不预先绑定技术**：现象 → 最限制学习的环节 → 已有机制为什么不够 → 最简单的训练侧改动。
- **分工**：设计档出方法和路线判断；推理档做每张卡的预审、每次开跑前的代码审查、结论复核与归因；执行档编排和跑实验，它写的代码和结论都要过推理档。

**通用科研插件：对任意领域都适用**（ML、机器人、生物、物理、经济、控制……）。领域专属的东西只放在项目的 `<project>/.open-scientist/` 里（目标函数、主线、实测事实、系统地图），插件本身不带任何项目内容。

**ResearchStudio 生成 + 在 phase 边界插入三类层。** RS 的 idea_spark（已同步上游 #63：带版本收据的 quality flow、formula repair、`intervention_object`）是生成器。Open Scientist 插入的每一层都声明类型：
- **排序（rank）**：`mainline`（一条主线、≤2 条因果相连的支线，每个 bottleneck 一个 RS run）；`problem-selection`（只排没被杀的卡，步骤 H 六项）。
- **验证（verify）**：独立验证器（`agents/soundness-verifier.md`）只看代码和自己检索的文献，**不看项目自己的跑分**，只杀不排：gap 级、机制级（2.3 之后）、卡级（先判部署合同 S0，再评 S1–S8）；另有现象准入（主会话实测）和项目一次的协议审计。
- **经典建模（model，解法侧的核心）**：`classical-recall` 从 2010 年以前的经典原问题出发，按用户的 Q1–Q8 标准推出构造与保持性质（标准原文：`skills/classical-recall/references/modeling-standard.md`）；RS 2.2 把锚点的构造搬到代码上。
- **约束（overlay）**：`overlays/phase1.md`、`overlays/generation.md` 覆盖 RS prompt。

| 位置 | 层 | 类型 |
|---|---|---|
| 开 run 前 | 问题卡（`TARGET:` + 现象来源、竞争解释、切分 / 参照 / 货币） | 约束 |
| Phase 0 → 1 | `mainline`（盲测 → Crux → 因果排序检验：候选锚到基线论文章节 + 代码行） | 排序 + 验证 |
| Phase 1 | `overlays/phase1.md`（瓶颈是给定的） | 约束 |
| Phase 1 → 2 | `soundness-gate`（gap 级）→ 现象准入 → `classical-recall` → `property-test`（仅 ml 域：锚点性质训练前快检一次） | 验证 → 验证 → 建模 → 验证 |
| Phase 2.1–2.2 | `overlays/generation.md`（gap 顺序、搬经典构造） | 约束 |
| 2.3 → 碰撞 | `soundness-gate`（机制级 S1 / S2 / S7；KILL 省掉 Phase 3） | 验证 |
| Phase 3 → 4 | `soundness-gate`（协议级：评测工具按 sha256 钉死，改了即重审；卡级）→ `problem-selection` | 验证 → 排序 |

## 用于任意领域
- **检索开关** `OPEN_SCIENTIST_DOMAIN`：`ml`（默认）= arXiv + OpenReview + 本地 ML 会议语料库；`general` = **arXiv + OpenReview**（去掉只覆盖 ML 会议、且依赖本机索引的本地语料库；arXiv 加一个 6–24 个月的较早窗口）。不用 OpenAlex / Semantic Scholar。
- **验证器的证据**：有代码的项目看 `file:line`；没有代码的领域（湿实验、田野、理论）看项目里可检查的系统事实：协议、配置、数据字典、方程（`templates/.open-scientist/code_map.md` 是通用的系统地图模板）。
- **经典建模**：从任意学科的经典原问题出发（至少 5 个学科），"2010 年以前、顶会 / 奠基期刊"按本领域的经典期执行。
- **RS 的 15 个模式 + 31 个子模式**是从 ML 论文里归纳的；在其他领域只负责"怎么落地"，经典锚点负责"做什么"，没有合适的模式就 `sub_pattern: null`。
- 新项目：把 `templates/.open-scientist/` 复制到项目根目录，填 `mainline.md` 的目标函数、`facts.md`（只写本机实测）、`code_map.md`。

驱动：`python3 scripts/os_next.py --dir <run_dir> --project <project> [--query "..."]`，流程见 `skills/open-scientist/SKILL.md`。
自检：`python3 scripts/selftest_os_next.py`（无参数；检查依赖的 RS 标签、各层触发顺序与类型、`classical_check.py`）。
项目专属文件放在 `<project>/.open-scientist/`（模板见 `templates/`）。

与 0.7 的区别：通用化——检索开关（general = arXiv + OpenReview）、验证器接受非代码的系统事实、经典层的进入位置和成本改成跨领域写法、模板去掉项目内容。

与 0.6 的区别（0.7）：`innovation-lens`（15 种创新类型）删除，解法侧换成经典建模层；gap 门拆出现象准入；新增机制级与协议级验证、S7 经典前提；problem-selection 改用步骤 H 六项；每层声明类型；verifier_log 只检验 KILL。

与 0.5 的区别（0.6）：同步上游 RS #63（三方合并，保留本地库检索、关闭 Semantic Scholar）；os_next 按产物触发，并对依赖的 RS 标签做自检；新增 RS overlays、现象准入、跨 run 卡池、KILL 停点，以及模型分工（设计 / 推理 / 执行三档，生成者 ≠ 验证者）。旧版 run 目录不能续跑。

安装（本地）：
```bash
claude plugin marketplace add /path/to/open-scientist
claude plugin install open-scientist@open-scientist-local
```
检索用 arXiv + OpenReview + 本地库。凭据放在 `~/.config/open-scientist/.env`（安装后的插件副本没有 `.env`；建议软链接到你的 RS `.env`），开发副本也可放 `skills/idea-spark/.env`。不要提交。
