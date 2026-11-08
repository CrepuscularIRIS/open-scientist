# Open Scientist 0.4

**ResearchStudio 出卡 + research taste 选择层。** RS 的 idea_spark 是主干，负责检索、瓶颈诊断、生成、审查和写卡。Open Scientist 在它的阶段之间插入选择层，把"选哪类贡献、选哪个方法、先做哪张卡"显式化，不再让 AI 每轮随意挑。

| 位置 | 层 | 作用 |
|---|---|---|
| Phase 0 之前 | `mainline` + `problem-selection`（目标函数 / 参数策略） | 三瓶颈主线；把目标写成要优化的函数 |
| Phase 0 → 1 | `innovation-lens` | 15 种创新类型 A–O（5 族），给方向排序 |
| Phase 1 → 2 | `gap-code-filter` | gap 对到代码行，找"默认但不必要的假设"；离线 oracle 准入；"15 种 ideation 模式 × 代码"设计层 |
| Phase 3 → 4 | `problem-selection` | 假设风险表、成功概率 × 影响、go / no-go、第一个证伪实验 |

驱动：`python3 scripts/os_next.py --dir <run_dir> --project <project> [--query "..."]`，流程见 `skills/open-scientist/SKILL.md`。
自检：`python3 scripts/selftest_os_next.py <已完成的 RS run 目录>`。
项目专属文件放在 `<project>/.open-scientist/`（模板见 `templates/`）。

与 0.3 的区别：去掉了 Forge 引擎、Research Companion、Co-Scientist 和类比推理；只保留 ResearchStudio、Anthropic 的选题框架，以及我们自己的方法论。

安装（本地）：
```bash
claude plugin marketplace add /path/to/open-scientist
claude plugin install open-scientist@open-scientist-local
```
检索用 arXiv + OpenReview + 本地库。凭据放在 `~/.config/open-scientist/.env`（安装后的插件副本没有 `.env`；建议软链接到你的 RS `.env`），开发副本也可放 `skills/idea-spark/.env`。不要提交。
