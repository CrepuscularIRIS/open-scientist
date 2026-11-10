---
name: property-test
description: Quick pre-experiment check of classical anchors (Open Scientist 0.9, ml domain only). After classical-recall writes phase1/classical_anchors.json and before RS Phase 2.1, run each anchor's claimed property once on this project's real code path (frozen checkpoint / logged data, no training, minutes). A clear failure drops the anchor; anything not measurable without training passes through. scripts/property_check.py applies the verdict. A speed aid, not a rigour gate. Use when os_next emits the property-test layer.
---

# 性质快检（经典锚点在实验前跑一次脚本）

**目的**：经典锚点的建模报告声称"某性质在本项目上保留"（Q4 条件 + Q5 失配）。训练前花几分钟，在本项目真实代码上量一次这条性质；明显不成立的锚点不必等一次训练才发现。
思路借自 TCSExam（arXiv 2611.07962）：claim 先过脚本，再信文字。**这是提速手段，不是严格验证**——RS 的目的是快速出方法，过 baseline、方法讲得通就够。

**只在 `OPEN_SCIENTIST_DOMAIN=ml` 时发出**；`general` 域跳过。

## 做法（主会话，每个锚点 ≤ 30 分钟）
1. 对 `classical_anchors.json` 的 `order` 里的锚点（至少第一个），写一个短脚本 `phase1/property_tests/<obj_id>.py`：在冻结 ckpt / 已有 replay 上，量报告里最关键的那条性质（优先测 Q5 失配点）。通过阈值写在脚本顶部，跑之前定好。
2. 可选：在 Q6 手算例上先跑一下，确认脚本本身没写错。
3. 结果写进 `phase1/anchor_tests.json`：
```json
{"tests": [{"obj_id": "...", "script": "phase1/property_tests/<obj_id>.py", "measures": "...", "threshold": "...",
            "T2": {"pass": true, "value": "...", "ckpt": "..."}}]}
```
   训练前量不出来 → `"T2": {"pass": null, "why": "..."}`。
4. `python3 "<plugin>/scripts/property_check.py" --dir <run> --write`：`pass=false` → KILL（移出 `order`，记 `killed_by_test`）；`true` → PASS；`null` → UNTESTABLE（保留）。写完成标记 `phase1/.property_tests_done`。

全部锚点被 KILL → 同一 bottleneck 回 `classical-recall` 取下一批对象。KILL 只否定这个锚点在这个映射下的用法，不否定整个经典家族。

## 下游
- RS 2.1 只用留在 `order` 里的锚点。
- 卡级 S7 可以引用 `anchor_tests.json` 里已测过的条件。
- 实验结束后，在 `verifier_log.md` 一并记下快检判决（快检过了、训练却没收益，是有用的反例）。
