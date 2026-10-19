# Open Scientist 0.3 · Claude Code / Codex 科研插件

**按问题推进的科研引擎。** 研究从用户的问题、代码和论文出发。Agent 每次提出一个下一步动作，代码先核对它的材料、版本、授权和产出合同，通过后才写入共享记录。

0.3 融合了四个来源：ResearchStudio、Research Companion、Co-Scientist 和 Open Scientist 0.2。设计原则是 **程序严格，资产自适应**：
- 读文献、先计划后执行、原始结果留存、独立审查、硬下限、双通道碰撞检索，这些程序固定不变。
- 领域卡、审稿期望、评审维度、测试协议、代码地图和检索计划，随领域与任务从证据重新生成。

设计见 [docs/design.md](docs/design.md)，不变的程序见 [references/protocols.md](references/protocols.md)。

## 和 0.2 的区别

| 0.2 | 0.3 |
|---|---|
| 11 个技能各自推进，另有 auto-loop 与固定 7 项验收 | 一个 **study** 推进器：Agent 提议，代码检查，原有 11 个入口转发到它 |
| 静态资产（RS 15+31 卡、Companion 7 维、Co 评分锚点）直接复用 | 静态资产只当 **种子**。每个 study 按需生成自己的资产，每条都标明证据；只靠种子的资产停留在 draft |
| 不分任务类型 | 10 种任务类型变体（机制、理论、诊断、分析、基准、系统、实证发现、扩展规律、综述、复现）。基准与数据集任务在 RS 中不受支持，这里是一等任务 |
| 测试由宿主自行执行，结果靠描述 | `run_test` 实际执行计划好的命令，记录 commit、退出码和带 hash 的 stdout/stderr。中断不算完成，也不会静默重跑 |
| 记录层依赖 pydantic 和 mcp | 只用 **Python 标准库**：记录库、MCP 服务器和导航器都不需要安装依赖 |
| RS 严格流水线不可用 | `build_domain`（RS 严格阅读流水线）与 `idea_run`（RS 严格 idea 链）作为 study 内的动作调用 |

## 先用起来

```bash
# Claude Code（从 GitHub 市场安装或更新）
claude plugin marketplace add CrepuscularIRIS/open-scientist
claude plugin install open-scientist@open-scientist-local     # 已装 0.2：claude plugin update open-scientist@open-scientist-local
```

在 Claude Code 里直接描述研究问题即可，例如“为什么 agent 跨会话丢记忆？先查代码里的原因”。`open-scientist` 技能会开一个 study 并逐步推进；`/open-scientist` 打开面板，`/config` 设置默认模式。Codex 的安装步骤见 [docs/install.md](docs/install.md)。

也可以从命令行直接驱动：

```bash
python3 scripts/forge.py next --project "$PWD" --study memory-loss --goal "为什么 agent 跨会话丢记忆？"
```

## 研究怎样推进

每一步都由 `forge next --study <slug>` 给出：
1. **intake**：记录问题 `q`（用户原话与硬约束），并写下 **kit**：任务类型、交付物、首批需要的资产、每种任务类型对应的变体。
2. **propose**：Agent 找出最可能改变下一个决定的未决问题，提出回答它的最便宜动作。动作有：
   - 诊断代码或数据；
   - 检索（先本地库）与阅读；
   - 生成资产；
   - 构造或演化机制；
   - 一致性检查、碰撞检索、独立审查；
   - 计划测试、执行测试、解读结果；
   - 决定、汇报、问人；
   - 调用 RS 严格流水线（`build_domain`、`idea_run`）。
3. **check**：代码检查输入是否存在、版本是否最新、是否在授权内、前置条件是否满足、是不是无效重复。超出授权（训练、付费、外发数据、超预算）的转给人决定；免费检索不问。
4. **commit**：动作产出先按合同校验，再写入记录库。
5. **停止条件**：
   - 交付物的完成条件满足后可以汇报，诊断类问题证实或推翻前提即可结束；
   - 连续 3 个动作没有新信息就停下交给人；
   - 排除一个解释、发现前提为假，都算进展。

## 什么变，什么不变

| 不变（程序） | 随领域 / 任务变（资产） |
|---|---|
| 先读后引；只有全文读过、代码检查过或实际执行过的材料，才能支持判断 | 领域：领域卡、审稿期望（带 `applies_when`）、基线、碰撞词表与时间窗、跨域映射、反模式统计 |
| 先计划后执行；对手解释必须预测出不同的观察结果 | 任务：评审维度、测试协议、交付标准、检索计划 |
| 原始结果留存；执行结果分类解读 | 项目：代码地图、运行环境、研究者画像 |
| Q/H/T 版本化；基于旧版本的提议被拒 | 审查通过前，资产不得标为 checked |
| 独立审查；硬下限；双通道碰撞检索 | — |
| 演化不原地修改，每个算子有对应约束；用户授权上限不可由步骤提高 | — |

## 共享记录与工具

- **记录**：每个 study 一个库，位于 `<project>/.forge/studies/<slug>/records.sqlite3`，只追加、带版本、精确引用 `{id, version}`。语义沿用 0.2 的 project / candidate / material / activity / assessment。0.2 的记录用 `forge records import` 导入为只读档案，只作历史阅读，不算证据。
- **MCP 服务器** `open-scientist`（标准库实现）：提供 `forge_next`、`records_context|get|list|history`、`papers_search`。没有写入工具，写入只能经过 study 的 commit。
- **本地论文库**：读取 `PAPER_SEARCH_LOCAL_DB`（默认 `/data/paper_index/local_papers.db`），只读，先本地后 arXiv。说明见 [docs/search-adapter.md](docs/search-adapter.md)。
- **OpenReview 投稿结果与评审文本**（可选）：见 [docs/openreview-labels.md](docs/openreview-labels.md)。

## 验证与局限

- **已覆盖**：`pytest` 覆盖 study 推进器的全部门禁（错误前提被实际执行的探针纠正、中断不重跑、不可判别的计划被拒、授权、无进展停止、资产证据规则、RS 严格链内嵌与吸收），以及 0.2 的记录、检索和 OpenReview 测试。`claude plugin validate` 和 `claude plugin test` 通过。
- **尚未验证**：在真实课题上的科研效果还没有评估。校验器检查结构、来源、版本与改动范围，不判断机制好坏，那是独立审查的工作，审查也可能出错。执行者记录来自宿主自报，不是身份认证。Agent 与这些文件在同一台机器上：手改策略、kit、批准、执行记录或提交标记会让 study 停下并报出来；但如果有人直接改写记录数据库，这些校验拦不住，只能让篡改更难、更显眼。

## 许可

MIT 与 Apache-2.0。来源与改编说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
