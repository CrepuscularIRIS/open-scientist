# v0.1 验证记录

日期：2026-10-17。验证对象是本目录源码包。下述证据分层保留；文件齐全、自动化测试通过、提示词回放和科研效果不是同一件事。

## 交付内容

- 11项技能正文，合计1,994行。
- 25份活动方法参考，合计3,101行；包含RS长提示词、Companion三角色方法、Co审查与四种演化。
- 15张主模式卡＋31张子模式卡的完整原文与按需索引。
- 110个来源文件，1,047,178字节，原始归档逐字节核对；来源、commit、dirty状态、SHA-256、许可随包记录。
- 32条触发式桥接合同、5种可选Card视图、5类共享记录和5个MCP工具。

行数只描述交付范围，不是质量评分。活动方法是有标注的适配，不能称所有段落均逐字未改。完整原文另存vendor。

## [已核] 自动化与真实接口

最终完整命令 `python -m pytest -q`：**62 passed，9 subtests passed**（含 Claude Code 适配新增的 5 项）。

覆盖实际SQLite读写、精确历史引用、并发版本冲突、非法关联/状态拒绝、历史反证/材料与未消费反馈保留、CLI跨目录访问、SDK stdio MCP initialize/list_tools/call_tool、真实临时FTS数据库、arXiv Atom解析与失败分类、来源去重、资产篡改/遗漏/漂移、包内链接检查和合成桥接演示。

测试中外部HTTP边界使用受控响应；不能将Atom解析测试说成arXiv线上成功。记录层不独立核验来源，不提供科学推理自动失效或保证保密的盲审包。

`python scripts/import_assets.py check --source-root /path/to/source-repos`：110份文件及原仓库快照检查通过。原RS与Co工作树仍干净，Companion仍只有迁移前已有的四个修改。

Codex实际 `plugin/read` 识别到 **11项带open-scientist命名空间的skills** 与 **research-records MCP配置**；原始返回见 [native-plugin-read.json](../evaluations/native-plugin-read.json)（公开前将本机绝对路径替换为 `/path/to/open-scientist`，其余字段未改）。返回 `installed=false`，说明本次完成的是原生解析验证，没有悄悄安装到用户全局环境。MCP通信另由真实SDK客户端独立测试。

## [已核] Claude Code 适配

新增 `.claude-plugin/plugin.json` 与 `.claude-plugin/marketplace.json`。Claude Code 只展开 `${CLAUDE_PLUGIN_ROOT}`，因此清单内联同名 `research-records` 服务，覆盖根目录为 Codex 保留的 `${PLUGIN_ROOT}` 写法。Codex 清单、`.mcp.json` 与 `mcp.json` 未改。

- 对照：只有根 `.mcp.json` 时，`claude -p --plugin-dir` 的 init 事件中 `plugin:…:research-records` 为 **failed**，没有 records 工具。
- 修改后：同一检查为 **connected**，5 个 `mcp__plugin_open-scientist_research-records__records_*` 工具与 11 项 `open-scientist:research-*` 技能均出现。
- 真实调用：headless Claude Code 通过 MCP 对临时项目执行 `records_put`（返回 version 1）和 `records_get`（读回同一记录），项目下生成 `.open-scientist/records.sqlite3`。
- `claude plugin validate --strict` 对插件清单和 marketplace 清单均通过；`tests/test_hosts.py` 检查两套清单的名称/版本一致、Claude 变量、启动脚本存在、同名覆盖与 `mcp` 必需依赖。

未执行 `claude plugin marketplace add` / `install`（会改用户全局配置）。未在 Claude Code 中做科研任务回放。

## [已核／未核] 双源检索

真实本机索引检索成功，可返回论文元数据、来源及本地PDF路径；只读查询，不复制PDF、不重建数据库。

arXiv live probe在本次网络条件下返回timeout。适配器保留本地结果并标记部分覆盖，未把超时变成empty。远端成功路径仅由Atom fixture验证，**本机联网成功尚未核实**。时间预算限制后续请求调度，标准库网络超时不是硬进程截止。

## [已核] 合成执行桥接

[bridge_replay.py](../examples/bridge_replay.py) 实际执行微型Python程序并写入临时研究项目：

1. 帧仍在但查询未命中：代码事实改变问题版本，保留旧材料。
2. 合法反例与退出码7的运行失败分别保存：保留旧预测、H修订与新的未执行T。
3. 未定义normalizer产生真实NameError：先写finding与H新版本，再写新Card；原Card保留，反馈有处置，PARK有重访条件。

这些是作者编排的确定性集成演示。它们验证数据链与边界，不证明Agent能在全新科学问题上自主做出正确判断。详情见 [演示说明](../examples/README.md) 和 [验证边界](../evaluations/bridge-replay.md)。

## [已核] 跨作者审查与修复

[integration-review](../evaluations/integration-review.md) 记录了5项发现及修复：旧human feedback被新版隐藏、不完整Atom被标成功、NULL标题崩溃、降级主张被误当纯文案、diagnose记录字段与桥接编号不一致。前三项经过复现/回归，后两项核对活动文档。另做B03/B06/B08/B10真实临时fixture回放，但上下文继承了本次设计。

## [边界] writing-skills检查

使用已安装Superpowers writing-skills的先看基线、逐skill撰写/回放、根据问题修订的方式。用户明确要求详细保真迁移，因此没有按通用短skill建议删成摘要。运行时代码的关键行为测试先观察失败再实现。

[baseline](../evaluations/baseline.md) 中11场景在继承设计上下文的文字回答上已经全部通过，没有虚构无skill失败。各authoring文件记录了逐skill检查：

- [core](../evaluations/authoring-core.md)
- [retrieval](../evaluations/authoring-retrieval.md)
- [diagnose/ideate/construct](../evaluations/authoring-phase1.md)
- [review/evolve](../evaluations/authoring-review.md)
- [report/decide](../evaluations/authoring-reporting.md)

没有进行fresh-context匹配预算A/B、真实科研效果、完整安装后宿主自动调用、Claude Code中的科研任务回放、公共目录发布验收。不能据本轮声称插件已提高idea质量。下一轮科学效用评估应比较实际有效发现、反例保留、决策改变、重复率与成本，而非卡片长度。
