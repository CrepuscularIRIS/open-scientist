---
name: attribution
description: Failure attribution before backtracking (Open Scientist 0.10). After a trained card fails — and before any other card is drafted, verified or trained — decide in a fixed order whether the evaluator, the implementation, a mechanism that never engaged, the gap itself, or the method's causal premise is what failed. Only gap and method failures count toward the structural stop-loss; a gap failure sends the run back to the problem side at once; evaluator and implementation failures are fixed and rerun. Also guards results against self-serving reinterpretation (changing the criterion after the fact, promoting an upper-bound arm). Use when os_next emits ATTRIBUTION_DUE, after any experiment finishes, or when the user asks whether a failure means the problem was mis-located or the method was wrong.
---

# 失败归因（回溯之前先分清：是 gap 定位错，还是方法不行）

**为什么有这一层**：一张训练卡没过线有五种原因，对应五种完全不同的下一步。以前全部记成"卡失败"，结果是：判据在当前合同内根本动不了，却连出 7 张方法卡；评测工具的伪影被当成现象追了三天；卡带来的真实副收益因为不在判据轴上被丢掉。

**什么时候做**：每张训练后 FAIL 的方法卡（`os_next` 输出 `ATTRIBUTION_DUE`），在起草下一张卡之前。**过线的结果也先过第 1、2 步**再记 PASS——伪影造成的"成功"和伪影造成的失败一样多。
**谁做**：主会话收集机械证据（配置日志、checkpoint 迭代数、基线复评、dump）；判断由一个**隔离的推理档 sub-agent** 写（不能是设计这张卡的调用）。它可以读这次实验的结果——它不是卡级验证器。给它：卡、PREREG、RESULT、dump 路径、`phase1/prior_sweep.json`、`deploy_contract.md`。

## 前置：PREREG 里要有的两个量
- **判据与制度**：指标、基线值、过线条件、训练长度 / checkpoint / 评测条件。先于结果写定。
- **`engagement_metric`**：机制如果起作用，**真实系统里**必然先变的那个中间量（不是想象 / 模型内部的量），以及怎么从 dump 里量。没有它，第 3 步无法判。

## 按顺序判，先命中的为准

| 序 | 归因 | 判定证据 | 下一步 | 算失败卡 |
|---|---|---|---|---|
| 1 | `EVALUATOR` | 同一批、同一工具哈希下复评基线臂，复现不了它在册的数字；工具哈希与 `protocol_audit.json` 不一致；被评的 checkpoint 不是预定迭代数；指标由伪影构成（提前终止的样本、陈旧缓冲区、各臂用了不同样本集） | 修工具、重审协议、重评。受影响的旧结论一并复查 | 否 |
| 2 | `IMPLEMENTATION` | 运行日志里的实际配置与卡不符（开关没生效、残留了上一张卡的改动）；事后代码审查发现实现与卡的机制不一致；训练崩溃或发散（记 `FAILED`，不是"无收益"） | 修代码、重审、重跑一次 | 否 |
| 3 | `NOT_ENGAGED` | 实现正确，但 `engagement_metric` 在真实系统里没变（包括：在模型内部变了、真实 rollout 里没变） | 只许在 PREREG 预先写明的一个旋钮上重试一次；再不动 → 记 `METHOD`（前提"该量可由此干预改变"被证伪） | 否（第二次算） |
| 4 | `GAP` | 机制起作用了，但判据在这个制度下不可动：`prior_sweep.json` 的上界臂没让它动；或基线在本制度下根本不出现该现象；或判据在某个合同约束的下游 | **立即**结构审计（`mainline` §结构审计），不再出卡 | 是，一张就触发审计 |
| 5 | `METHOD` | 机制起作用，判据可动（先验扫描里有臂在同一制度下让它动了），这张卡却没让它动或反向 | 写明被证伪的**因果前提**；同 TARGET 的下一张卡不得再依赖它 | 是 |

第 4、5 步的区别就是用户要的那个区分：**有别的臂能在同一制度下移动判据 → 方法不行；没有 → gap 或判据定位错了。** 没做过先验扫描、答不出这个问题时，先补扫描，不许直接记 `METHOD`。

## 同时记录
- `side_effects`：判据之外显著变好或变坏的轴（配对区间不含 0）。写进 `facts.md`，不因为不在判据轴上丢掉。
- `transfer_gap`：中间量在模型 / 想象内达标、在真实系统里没达标——单独写一句，这是一类可复用的负结果。

## 防止自我开脱（对结果的 reward hacking）
- **判据和制度在结果之后不能改。** 换指标、换 checkpoint、换评测条件让卡过线 = 新 TARGET + 新 PREREG，旧卡照记 FAIL。
- **上界臂和违反部署合同的卡不能升格为方法**，不论跑分多好。`role` 在开跑前定，之后不改。
- 一张卡不能因为"另一个轴变好了"改记 PASS；那是一条 [实测] 事实，可以成为新 TARGET 的现象来源。
- 归因 agent 判 `EVALUATOR` / `IMPLEMENTATION` 必须给出可复查的具体证据（日志行、哈希、复评数字）；"可能是实现问题"不成立，按顺序继续往下判。

## 收尾：把失败的方法清出项目
失败方法留在项目里的叙述（卡文、PREREG / RESULT、围绕它写的草稿、run 目录）会成为后面每个 agent 的锚点。归因写完后：
- 归因为 `METHOD` / `GAP` 的卡，以及被结构审计关闭的 run：把它的 run 目录、PREREG / RESULT、相关草稿移到项目外的归档目录（项目约定的 `<project>_archive_<日期>/`，附一份清单）。agent 不读归档。
- 项目里只留三样：`facts.md` 里的**测量行**（数字 + 制度，不带"所以应该……"的推论）；一行**被证伪的前提**（供去重，不写方向判断）；`cards.json` 的登记行（止损计数要用）。
- **测量、评测工具、gap 表、生态图不归档**——它们不是失败的方法。以前连续几次"全部归档重来"都没有解决问题，因为清掉的是测量、留下的是同一个生成器。
- 一条线结束（开关已解决 / 方法过线 / 审计关闭）后向用户汇报并停下；**不把失败改写成一篇分析或审计型的成果**——交付物类型由项目固定。

## 写盘
`<run>/attribution/<card id>.json`：
```json
{"card": "...", "attribution": "EVALUATOR | IMPLEMENTATION | NOT_ENGAGED | GAP | METHOD",
 "evidence": {"evaluator": "...", "implementation": "...", "engagement": "指标、基线值、本臂值",
              "movable": "引 prior_sweep 的哪个臂 / 不可动的依据"},
 "falsified_premise": "METHOD / 第二次 NOT_ENGAGED 时填",
 "side_effects": ["..."], "transfer_gap": null,
 "next": "fix_tool | fix_code_rerun | retry_knob:<名字> | structural_audit | next_card_without:<前提>"}
```
同时把 `"attribution": "<归因>: 一句话"` 写进 `<project>/.open-scientist/cards.json` 对应卡，在 `verifier_log.md` 记一行。`os_next` 只把 `GAP` / `METHOD` 计入结构止损。
