# Open Scientist 0.6

**ResearchStudio 生成 + 主线优先 + soundness 门。** RS 的 idea_spark（已同步上游 #63：带版本收据的 quality flow、formula repair、`intervention_object`）是生成器。Open Scientist 在它外面做三件事：
1. **问题侧**：先找出限制目标的一条主线（盲测首轮 + Crux 校验），再找与它因果相连的 ≤2 条支线，每个 bottleneck 开一个 RS run；
2. **soundness 门**：独立验证器（`agents/soundness-verifier.md`）只看代码和自己检索的文献，**不看项目自己的跑分**，在训练前杀掉 idea；
3. **解法侧**：research taste（15 种创新类型）只给已准入的 bottleneck 排解决角度。

| 位置 | 层 | 作用 |
|---|---|---|
| Phase 0 → 1 | `mainline` | 一条主线、≤2 条支线、反事实瓶颈检验；Phase 1 由 `overlays/phase1.md` 把它当硬输入 |
| Phase 1 → 2 | `soundness-gate`（gap 级）+ 现象准入 → `innovation-lens`（解法侧） | KILL 删除；只排解法；Phase 2 由 `overlays/generation.md` 按 gate 顺序选 anchor |
| Phase 3 → 4 | `soundness-gate`（卡级）→ `problem-selection` | 卡写进跨 run 的 `cards.json`；KILL → 停在 CARD_KILLED，开新 run |

驱动：`python3 scripts/os_next.py --dir <run_dir> --project <project> [--query "..."]`，流程见 `skills/open-scientist/SKILL.md`。
自检：`python3 scripts/selftest_os_next.py`（无参数；检查依赖的 RS 标签 + 各层触发顺序）。
项目专属文件放在 `<project>/.open-scientist/`（模板见 `templates/`）。

与 0.5 的区别：同步上游 RS #63（三方合并，保留本地库检索、关闭 Semantic Scholar）；os_next 按产物触发，并对依赖的 RS 标签做自检；新增 RS overlays、现象准入、跨 run 卡池、KILL 停点，以及模型分工（设计 / 推理 / 执行三档，生成者 ≠ 验证者）。旧版 run 目录不能续跑。

安装（本地）：
```bash
claude plugin marketplace add /path/to/open-scientist
claude plugin install open-scientist@open-scientist-local
```
检索用 arXiv + OpenReview + 本地库。凭据放在 `~/.config/open-scientist/.env`（安装后的插件副本没有 `.env`；建议软链接到你的 RS `.env`），开发副本也可放 `skills/idea-spark/.env`。不要提交。
