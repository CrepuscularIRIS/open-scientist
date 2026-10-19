> **0.2 working-tree document**, kept as the collector reference. In 0.3 the collector is `forge/vendor/corpus.py`, run through `forge corpus` and the domain build.

# 第0步：随研究问题采集语料

本模块为领域适配提供项目本地元数据层。Companion/宿主从当前问题生成查询，采集后选择性读文献，生成领域方法卡。完整执行方法见 [domain-adaptation](../references/methods/domain-adaptation.md)。没有固定研究领域，没有新增后台服务或模型API依赖。

## 已实现与未实现

| 部分 | 当前状态 |
|---|---|
| arXiv显式ID/表达式查询、日期、分页与上限 | Python采集器已实现 |
| raw响应、内容hash、版本、双通道归属、恢复、JSONL导出 | 已实现；查询分页不是服务端一致性快照 |
| 本地论文库查找与PDF读取入口 | 复用已有search_papers；本采集器不复制/重建本地索引 |
| Companion→查询→全文阅读→领域卡→后续技能 | 已写入技能方法；由宿主Agent执行，尚无端到端模型质量验收 |
| OpenReview决策/评审批量连接器 | API v2会议型venue已实现，见[openreview-labels](openreview-labels.md)；API v1与TMLR未实现 |
| 自动签名模型/embedding/HDBSCAN/反模式统计程序 | 尚未实现；当前Agent可按方法做有来源的局部提取，不冒称统计完成 |

## 命令

无需安装依赖，Python 3.10+，当前跨进程锁使用POSIX `fcntl`（Linux/macOS；Windows未支持）。从任何项目目录调用插件中的绝对脚本路径；`--root`必须显式指定。

```bash
python3 <plugin-root>/scripts/forge.py corpus \
  --root <project>/.open-scientist/domain/corpus \
  harvest --config <project>/.open-scientist/domain/queries.json

python3 <plugin-root>/scripts/forge.py corpus \
  --root <project>/.open-scientist/domain/corpus status

python3 <plugin-root>/scripts/forge.py corpus \
  --root <project>/.open-scientist/domain/corpus \
  export --output <project>/.open-scientist/domain/papers.jsonl
```

再次harvest同一规范化配置恢复该run；已完成/达到设定上限的query不重抓。失败页不前移cursor，重新执行会再尝试。`--refresh`新建采样run、保留全部旧快照，不是抹掉重来。默认export当前run，可用`--run-id`导出历史run。

## 查询配置

Agent根据brief生成，不要求用户写JSON：

```json
{
  "name": "当前课题",
  "start_date": "2020-01-01",
  "end_date": "2026-10-18",
  "page_size": 25,
  "queries": [
    {"id": "target", "lane": "in_domain", "domain": "目标领域",
     "search_query": "ti:\"具体机制\" OR abs:\"领域术语\"", "max_results": 50},
    {"id": "analogy", "lane": "cross_domain", "domain": "候选源领域",
     "search_query": "ti:\"源领域操作\"", "max_results": 25}
  ]
}
```

search_query是arXiv原生表达式，保留OR、短语和字段；不同于便捷search_papers的关键词AND接口。日期追加为submittedDate过滤。每query最多1000条，每页最多100条；较大范围应显式分区，长期全量更新另用OAI-PMH，不在这里隐藏扩成整站抓取。

另一种query使用`ids`数组替代search_query，支持现代/旧式ID与vN，最多100条；明确ID不叠加主题日期过滤，便于纳入经典来源。未返回的ID标missing_ids，不冒充成功。见[联网测试用种子](../examples/corpus/reading-seeds.json)。[主题样例](../examples/corpus/phase0-pilot.json)只用于采集验证，实际任务应换成当前领域。

## 数据与状态

`corpus.sqlite3`含runs/tasks/requests/papers/snapshots/memberships：

- paper以arXiv base ID定身份；v1/v2和同版本元数据变更保存不同快照，不按标题合并。
- 原始Atom保存`raw/<sha256>.xml`；request有URL、时间、状态、hash与错误。下载到的非Atom/错误feed也留原件，不写成零篇成功。
- 元数据有title/abstract/authors、首次提交与更新日期、version、category、DOI/journal_ref/comment、摘要/PDF链接；缺失保留null，读取元数据不等于读全文。
- membership关联精确snapshot与query/lane。领域内/跨域是发现路径；同一论文可以来自两者，不重复统计为两篇。
- 每页所有记录与cursor在同一SQLite事务中提交。进程意外结束的running request恢复标interrupted；只读HTTP可能重新请求，不承诺网络exactly-once。

export每paper选择该run观察到的最高version作为展示字段；同版本以该run最近一次请求观察为准，不用全库首次见到时间排序。另带observed_snapshots和逐query/版本来源；同query再次观察相同snapshot时membership指向最近请求，所有请求/raw仍保留。它不是完整版本历史导出；完整历史在DB/raw中保留。JSONL旁的manifest包含run、采集范围/错误/截断。所有论文默认`review_status=not_collected`、`fulltext_status=not_read`、`signature_status=not_extracted`，不生成accept/reject或质量分。显式指定不存在的run_id会报错，不覆盖现有导出。

| query状态 | 含义 |
|---|---|
| complete | 本次查询返回范围已处理，不代表领域穷尽 |
| capped | 达到用户设定采样上限，有未取完结果 |
| empty | 合法响应为零，不能作为新颖性证据 |
| error | 网络/解析/范围/重复页异常，cursor未推进 |
| missing_ids | 显式ID未全部返回，保留已获得的材料与缺失列表 |
| pending | 尚有后续页或尚未执行 |

harvest有error/missing_ids时退出2；capped是有意采样，退出0但query_exhausted=false。状态/导出不调用模型或联网。source的HTTP失败在requests里保存错误和Retry-After；没有获取到响应体时raw为空，不伪造原件。

按[arXiv接口说明](https://info.arxiv.org/help/api/user-manual.html)与[限流要求](https://info.arxiv.org/help/api/tou.html)，本工具跨本机同用户采集进程串行，并在请求结束后至少间隔3.1秒；不自动重试。HTTP 429或带Retry-After的错误会停止本轮后续查询，保留pending；实际HTTP层把服务要求的冷却时间写入共享锁，提前恢复会立即报冷却错误，不继续请求。429未给有效Retry-After时使用60秒保守冷却。其他检索进程/其他机器仍需调用者统一协调，不可并行绕限流。单次网络socket超时30秒，不是整个请求严格墙钟限额；若用户给硬运行期限，宿主需设置总进程超时。

按提交时间排序可减少新投稿插入导致的分页漂移，但API没有快照保证：排序并列、索引变更仍可能造成遗漏。页内重复身份、跨页重复ID或页计数超过totalResults都会报错且不提交该页，不能用重复命中填满完成计数。断点恢复是本地进度，不等于完整增量同步；跨较长时间应refresh、比对ID覆盖，不用旧cursor证明新增论文已全采集。修改过的旧论文也不一定落在新提交窗口内；需显式刷新已知ID。

## 与研究记录的关系

corpus是可重读的来源缓存，项目`records.sqlite3`仍是Q/H/T与研究判断的事实源。Agent将真正使用的论文/领域卡路径、版本和范围以material引用写入研究记录；不把每条检索命中自动转换成supported finding。JSONL中的待采集标记不由采集器自动升级。

## 后续OpenReview接线约定

下一步以公开venue配置和submission/forum为单位取decision/review，保留note/revision、raw字段、观察时间与匹配证据。accepted/rejected/withdrawn/desk_rejected/pending/unknown分别保存；同篇多次投稿是多件事件。标题近似匹配只产生候选链接，不能转移标签。接收标签不是经验结果，更不是模式因果质量。

本模块没有修改records schema、现有MCP工具或自动循环完成条件。新增语料能力不能被用来声称此前工作流缺陷已修复。
