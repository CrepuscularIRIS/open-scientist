# Open Scientist 0.5

**ResearchStudio 出卡 + 主线优先 + soundness 门。** RS 的 idea_spark 是主干，负责检索、瓶颈诊断、生成、审查和写卡。Open Scientist 在它外面加两件事：先找出限制目标的**一条主线**（盲测首轮 + Crux 校验），再用一个**独立的验证器 agent** 对每条 gap 和每张卡判 KILL / CHECK / PASS，让 idea 在训练之前就被杀掉。方法论只给通过的条目排序。

| 位置 | 层 | 作用 |
|---|---|---|
| Phase 0 → 1 | `mainline` | 盲测首轮（不看我们的 claim）+ Crux 校验；一条主线、≤2 条因果相连的支线、反事实瓶颈检验 |
| Phase 1 → 2 | `soundness-gate`（gap 级） | 验证器 `agents/soundness-verifier.md` 按固定评分表（现象实测、因果归属、代码一致、反事实瓶颈、口径伪影）打分；只删不增；主线优先排序 |
| Phase 3 → 4 | `soundness-gate`（卡级）→ `problem-selection` | 再加"机制可行"一项；只有 PASS 的卡进入排序和训练 |

可选工具：`innovation-lens`（15 种创新类型）、`gap-code-filter`（默认假设四元组 + 15 种模式 × 代码）。

驱动：`python3 scripts/os_next.py --dir <run_dir> --project <project> [--query "..."]`，流程见 `skills/open-scientist/SKILL.md`。
自检：`python3 scripts/selftest_os_next.py <已完成的 RS run 目录>`。
项目专属文件放在 `<project>/.open-scientist/`（模板见 `templates/`）。

与 0.4 的区别：主线优先表述取代 innovation-lens 作为 Phase 0 → 1 的层；独立验证器（soundness-gate）取代 gap-code-filter 作为 Phase 1 → 2 的层，并在 Phase 4 前对卡再判一次；problem-selection 只排 PASS 的卡。

安装（本地）：
```bash
claude plugin marketplace add /path/to/open-scientist
claude plugin install open-scientist@open-scientist-local
```
检索用 arXiv + OpenReview + 本地库。凭据放在 `~/.config/open-scientist/.env`（安装后的插件副本没有 `.env`；建议软链接到你的 RS `.env`），开发副本也可放 `skills/idea-spark/.env`。不要提交。
