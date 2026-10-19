# 安装、升级与验证

Open Scientist 0.3 只依赖 Python 3.10+ 标准库，无需 `pip install`。跨进程锁使用 POSIX `fcntl`，因此支持 Linux 和 macOS，暂不支持 Windows。

## 1. Claude Code

```bash
claude plugin marketplace add CrepuscularIRIS/open-scientist
claude plugin install open-scientist@open-scientist-local
```

本地开发时也可以用 `claude --plugin-dir <本仓库>` 加载。插件包含以下内容：
- 技能：`open-scientist`，以及 0.2 的 11 个入口（转发到 `open-scientist`）；
- 子代理：`forge-core`、`forge-critic`、`forge-fast`、`forge-operator`、`research-grill`；
- Mod 面板 `/open-scientist`，以及 `/config` 中的默认模式；
- MCP 服务器 `open-scientist`。

**从 0.2 升级**

```bash
claude plugin update open-scientist@open-scientist-local
```

升级后注意三点：
- MCP 服务器从 `research-records` 改名为 `open-scientist`。工具名随之变化，且 0.3 不再提供写入工具。
- 旧记录可以导入为只读档案：`python3 scripts/forge.py records import --project <项目> --from <项目>/.open-scientist/records.sqlite3`，写入 `<项目>/.forge/archive/open-scientist-0.2.sqlite3`，可用 `forge records context --project <项目> --archive` 查看。档案只作历史阅读，不会被任何完成条件或引用当作证据；需要沿用的材料，在新 study 中重新检索、阅读并登记。
- 如果在用户级注册过独立的 `open-scientist-papers` 服务器，插件自带的 `papers_search` 可以替代它。用户级配置由你决定是否修改，插件不会去动它。

## 2. Codex

```bash
codex plugin marketplace add <本仓库或其克隆目录>
codex plugin add open-scientist@open-scientist-local
```

Codex 读取以下文件：
- `plugin.json`（含 `extensions.com.openai`）与 `mcp.json`；
- 兼容的 `.codex-plugin/plugin.json` 与 `.mcp.json`；
- `.agents/plugins/marketplace.json`。

Codex 没有子代理，需要独立上下文的步骤（coherence、review）改为先保存再顺序自审，并在记录中说明。

## 3. 本机论文索引

`papers_search` 和 `scripts/search_papers.py` 只读访问 `PAPER_SEARCH_LOCAL_DB`（默认 `/data/paper_index/local_papers.db`，SQLite FTS5，schema 见 [search-adapter](search-adapter.md)）。没有索引时，本地来源报告 `missing_index`，检索继续查 arXiv。不会自动建索引，也不会扫描目录。

## 4. 验证

```bash
python3 -m pytest tests -q
claude plugin validate .claude-plugin/plugin.json
claude plugin test .
```

## 故障定位

| 现象 | 原因与处理 |
|---|---|
| `forge: refused: the study's next step is …` | 命令调用顺序不对。先运行 `forge next` 并照做 |
| `stuck` | 连续无进展，或某一步反复不合格。看 notes 与 FIX 行，由人决定缩小问题、补材料或停止 |
| `authorize` | 提议超出授权（训练、付费、外发数据、超预算）。用 `forge study answer --approve/--deny --text "<原话>"` 记录人的决定 |
| `domain_changed` / `revision_changed` | 冻结的领域版本或已提升的修订被改动。恢复文件，或重新开一个 run/study |
