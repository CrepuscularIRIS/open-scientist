# 本地安装、依赖与验证

这是面向 Codex 与 Claude Code 本地执行环境的插件，两者共用 `skills/`、`scripts/` 与记录后端。Claude Code 清单位于 `.claude-plugin/`，见第 2b 节。主入口采用root `plugin.json`、`mcp.json`，同时提供 `.codex-plugin/plugin.json` 与 `.mcp.json` 兼容清单。格式依据 [OpenAI插件打包文档](https://developers.openai.com/plugins/build/plugins)；本地MCP的 `${PLUGIN_ROOT}` 路径依据 [官方本地MCP示例](https://developers.openai.com/plugins/deploy/desktop-only)。

## 1. 准备Python依赖

在插件源码目录执行，选择Codex能找到的 `python3`：

```bash
python3 -m pip install .
```

记录CLI需要Pydantic2，MCP需要Python MCP SDK 1.x；两者现在都是必需依赖（旧的 `'.[mcp]'` 写法仍然可用）。宿主用 PATH 中第一个 `python3` 启动服务；缺包时启动脚本会打印缺少的包名和对应的安装命令。检索适配器只用标准库，可直接运行。插件不自动下载模型或安装运行时。若使用虚拟环境，启动Codex时让该环境的python3在PATH中，或将本地MCP清单的command明确指向该Python；不要把研究项目根目录设置成插件路径。

本版对源码包做了本机SDK通信检查；换机器仍需安装依赖并验证。插件压缩包不打包平台绑定的虚拟环境。

## 2. 注册并安装本地插件

插件目录自带 `.agents/plugins/marketplace.json`，其中source.path指向当前根目录。以本机路径为例：

```bash
codex plugin marketplace add /path/to/open-scientist
codex plugin add open-scientist@open-scientist-local
```

换目录时替换第一行的绝对路径。安装会更新Codex用户的插件配置；本次制作没有替你执行这两条命令。桌面端可在对应本地marketplace里选择插件；刷新或新开会话后核对十一项skills与 `research-records`。本地安装使用缓存副本，修改源码后需要按客户端支持的刷新流程更新缓存；仅改原目录不保证当前会话立即变更。

名称以宿主显示为准，例如 `$open-scientist:research-workflow`。没有MCP时仍可通过记录CLI运行；不能因为服务未启用就把研究状态写到另外的隐式文件夹。

## 2b. 在 Claude Code 中加载

Claude Code 读取 `.claude-plugin/plugin.json`。其中 `research-records` 服务使用 `${CLAUDE_PLUGIN_ROOT}`；Claude Code 不展开 Codex 的 `${PLUGIN_ROOT}`。根目录 `.mcp.json` 保持 Codex 写法，Claude 清单用同名服务覆盖它。

只在当前会话试用、不改全局配置：

```bash
claude --plugin-dir /path/to/open-scientist
```

长期安装（会写入 Claude Code 用户插件配置）。从 GitHub 安装：

```bash
claude plugin marketplace add CrepuscularIRIS/open-scientist
claude plugin install open-scientist@open-scientist-local
```

或从本地克隆安装：

```bash
claude plugin marketplace add /path/to/open-scientist
claude plugin install open-scientist@open-scientist-local
```

在会话中用 `/mcp` 确认 `plugin:open-scientist:research-records` 为 connected。工具名显示为 `mcp__plugin_open-scientist_research-records__records_put` 等；技能里写的 `records_put/get/list/context/history` 指的就是这些工具。技能显示为 `open-scientist:research-workflow` 等 11 项。本地路径 marketplace 与 `--plugin-dir` 都直接读源码目录：修改后开新会话或执行 `/reload-plugins` 即生效。只验证插件清单用 `claude plugin validate .claude-plugin/plugin.json`；对目录执行 validate 只检查 marketplace。

## 3. 配置本机论文索引

默认读取 `/data/paper_index/local_papers.db`。其他机器通过环境变量指定兼容索引：

```bash
export PAPER_SEARCH_LOCAL_DB=/absolute/path/to/local_papers.db
python3 scripts/search_papers.py --queries 'visual memory|active perception' --sources local arxiv --max-papers 10 --timeout 8 --budget-seconds 20
```

索引schema及故障说明见 [search-adapter](search-adapter.md)。缺索引时报告 `missing_index`，仍可检索arXiv；没有网络时保留本地结果和远端失败状态。不自动建库、不修改原论文库、不把未完成搜索解释成零命中。

## 4. 验证本地包

```bash
python3 -m pip install '.[test]'
python3 -m pytest -q
python3 scripts/import_assets.py check
python3 scripts/validate_package.py
python3 examples/bridge_replay.py
```

最后一条仅运行合成微型案例并写临时项目；它不是正式科研实验。完整说明见 [examples](../examples/README.md)。生产项目的记录命令每次都必须传入明确的 `--project-root`，具体字段见 [record API](record-api.md)。

## 故障定位

| 现象 | 检查 |
|---|---|
| 插件未出现 | marketplace路径、安装状态、当前客户端是否已刷新；不要只看目录存在 |
| MCP启动失败 | 清单所用python3能否import mcp/pydantic（启动脚本会打印缺包）；Codex看`${PLUGIN_ROOT}`，Claude Code看`${CLAUDE_PLUGIN_ROOT}`是否被展开 |
| 某skill未列出 | SKILL.md前置name/description与目录，native plugin/read结果 |
| JSON写入被拒 | record-api中真实payload、引用是否已写入同项目、expected_version是否过期 |
| 检索为空 | 分开看每源的状态、年份/词覆盖和truncated，不推断新颖性 |
| arXiv超时 | 保留本地结果，限额后停止；本机本次live probe未验证远端成功 |

Claude Code 的 `--plugin-dir` 加载与 MCP 实际读写已验证，见 [验证记录](validation.md)；`claude plugin install` 长期安装路径未在本机执行。公共目录发布、跨设备远端服务与线上科研质量评估均不是本地源码包验证的同义词，本版未宣称这些路径通过。
