# OpenReview 投稿结果与评审：按需采集

本模块给领域适配补上"投稿事件 → 正式决定 → 评审原文"这一层，供对照打标（成功/失败/差距/审稿期望）和反模式统计使用。方法见 [domain-adaptation §6](../references/methods/domain-adaptation.md)，设计记录见工作区 `analysis/corpus-phase0/openreview-connector-spec.md`。

**按需**：由当前课题决定需要哪些会议-年份；采集单位是整个会议-年份，因为同主题、同年份的对照组和分母需要全量可见投稿。同一 `--root` 可被多个课题复用。

## 已实现与未实现

| 部分 | 状态 |
|---|---|
| API v2 会议型 venue（ICLR 2024–2026 已实测 group 配置一致） | 已实现 |
| 登录、token 只在内存、跨进程限流（≥7.3 秒/次）、429 共享冷却 | 已实现 |
| 全部投稿（接收/拒稿/撤稿/desk reject/待定）+ review / meta-review / decision / 评论 | 已实现 |
| 分页漂移检测（重叠校验、编号递增、count 变化）、断点恢复、按 pass 刷新 | 已实现 |
| 导出：课题子集 + 完整 venue 分母（按 status、按 primary_area × status） | 已实现 |
| 与 arXiv 语料的候选身份链接（仅 proposed） | 已实现 |
| API v1（ICLR 2018–2023）、TMLR（期刊流程） | 未实现；遇到会明确报 "not supported" |
| 签名抽取、聚类、反模式统计 | 未实现；属于后续阶段 |

## 命令

需要 OpenReview 账号：环境变量 `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD`，或 `--env-file`。匿名访问 `/notes` 会被 403 ChallengeRequiredError 拒绝。

```bash
python3 <plugin-root>/scripts/fetch_openreview.py --root <labels-root> \
  harvest --venue ICLR.cc/2025/Conference --venue ICLR.cc/2024/Conference --env-file <path/.env>

python3 <plugin-root>/scripts/fetch_openreview.py --root <labels-root> status

python3 <plugin-root>/scripts/fetch_openreview.py --root <labels-root> \
  export --output <project>/.open-scientist/domain/openreview.jsonl \
  --venue ICLR.cc/2025/Conference --query "world model" [--primary-area "..."] [--no-review-text]

python3 <plugin-root>/scripts/fetch_openreview.py --root <labels-root> \
  link --corpus-export <project>/.open-scientist/domain/papers.jsonl
```

- 普通重跑 = 续跑当前 pass；`--refresh` 总是新开一个 pass 从头取（旧 pass 和快照保留）。count 变化或分页漂移的报错会提示改用 `--refresh`。
- `--max-pages N` 用于试采，venue 记为 `partial`。
- 预算：账号限额 **500 次/小时**（实测，按账号计，可能与其他使用同一账号的进程共享）。ICLR 2025 共 11,672 件投稿，page_size=100 约 118 次请求，约 15 分钟。

## 数据语义

- 状态**只**来自官方 `content.venueid` 与 venue group 的映射；Decision 文本与之矛盾时 `conflict=true`，不改写状态。缺失、非字符串或未知的 venueid 记为 `unknown`，永不补成 `rejected`。
- accepted 的 tier（oral / spotlight / poster）取自 Decision 文本，取不到记 `unknown`。
- 每个 pass 只读一次 venue group，一个 pass 内不混用两套映射。导出只读每个 venue **最近一次完成的 pass**；没有完成 pass 时拒绝导出，除非 `--allow-partial`（manifest 标 `complete: false`）。
- 隐私：`authorids` 不入库；`~profile` 签名只记为 `public_user`；匿名审稿组名（`Reviewer_xxxx`）保留以关联同一审稿人的评论。raw 原文只在本地 `--root/raw/`。
- 链接只做规范化标题完全相同的 `same_work` 候选，`status=proposed`；不向 arXiv 记录传播任何状态、评分或评审。

导出每行一件投稿：来源 refs（forum、pass、raw 路径与 hash）、状态与原文、各评审的 rating / confidence / soundness / presentation / contribution 及文本字段、meta-review、评论计数。manifest 声明"可见投稿，不是总体接收率；决定标注的是一次投稿事件，不是实验成功或机制质量"。
