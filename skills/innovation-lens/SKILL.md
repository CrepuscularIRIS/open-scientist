---
name: innovation-lens
description: SOLUTION-side research taste (Open Scientist 0.6). After the soundness gate has admitted the bottlenecks (mainline + branches) and BEFORE RS Phase 2.1, run the 15 innovation types (A–O, 5 families) over each admitted bottleneck to rank SOLUTION ANGLES (how to solve it), so Phase 2.1 picks gap × pattern by an explicit taste ranking instead of ad hoc. It never selects, adds or re-ranks bottlenecks — problems are chosen by the mainline layer and the soundness gate. Use when os_next emits the lens layer before Phase 2, or when the user asks which kind of solution / contribution type fits an admitted bottleneck.
---

# 解法透镜（Research Taste 只用在解法侧）

**位置**：soundness 门（gap 级）之后、RS Phase 2.1 之前。产物 `phase1/solution_lens.json`。

**分工（用户 2026-11-08）**：
- **问题侧**（挑哪个 bottleneck）：只由 `mainline`（主线 / 支线，最小充分的问题表述）和 `soundness-gate` 决定。research taste 不参与：按"哪类贡献好看"去挑问题，会从方法反推问题。
- **解法侧**（怎么解）：本层用 15 种创新类型给每个已准入的 bottleneck 排**解决角度**，作为 Phase 2.1 的优先级。

本层不新增、不删除、不重排 bottleneck；主线的解法先排，支线其次。

## 15 种类型，按 5 族分组
| 族 | 核心问题 | 类型 | 对应的 IdeaSpark 模式（覆盖情况） |
|---|---|---|---|
| **01 假设创新** | 这个假设真的必要吗？ | **A** 去除不必要的默认假设（中） / **C** 挑战公认的基础假设（极高） / **M** 反例与边界条件驱动（中高） | A ↔ assumption_audit_and_pivot ✓；C 只有部分对应；M ↔ characterize_limit_then_surpass（部分） |
| **02 知识创新** | 是否忽略了某个已有的知识？ | **B** 跨领域理论迁移（中高） / **E** 被忽略的约束：守恒律、不变量、对称性（中高） / **H** 隐藏变量或中间机制（高） / **I** 统一看似不同的方法（高） | E ↔ structural_prior_encoding ✓；I ↔ algebraic_equivalence_unification / unify_into_shared_representation ✓；**B、H 没有专门的模式** |
| **03 问题创新** | 是否一直在优化错误的问题？ | **D** 问题重定义（高） / **G** 重新设计优化目标（中高） / **O** 评价范式重构（中高） | D ↔ reframe_as_solvable_object ✓；G ↔ targeted_self_supervised_objective（部分）；O ↔ controlled_diagnostic_design（只覆盖审计，不覆盖建评测） |
| **04 机制创新** | 是否有更直接、更高效的实现？ | **F** 从失败案例反推机制（中） / **J** 改变分解粒度（中） / **K** 改变资源分配（中） / **L** 监督信号重构（中） | J ↔ heterogeneous_decomposition / decompose_and_delegate ✓；L ↔ self_supervised_signal_engineering ✓；**F、K 没有专门的模式** |
| **05 规律创新** | 现有结论在什么条件下成立？ | **N** 利用规模或场景变化（中高），以及 F、M 中的机制分析 | **没有专门的模式** |

IdeaSpark 没有覆盖或只部分覆盖的：B、C、F、H、K、M、N、O（以及部分 G）。这些在本层显式补上。

## 步骤
1. **输入**：`phase1/soundness_gaps.json`（已准入的 gap 及其主线 / 支线位置）、`phase0/mainline_first.json`、`phase0/lit_table.md`、`<project>/.open-scientist/code_map.md`。
2. **逐个已准入的 bottleneck 扫 15 类**：每类写一句"用这类思路解它，具体是什么改动"。写不出来的标 ✗，不硬凑。每个角度写清：
   - 代码落点 `file:line`；
   - 难度；
   - 方法论文适配度：能落成一个算法 = 高，只能落成分析或评测 = 低；
   - 文献风险：lit_table 里最接近的论文（arXiv 编号）；
   - 是否属于"集成成熟方法"（可以直接用别人领域内的方法）。
3. **排序**（每个 bottleneck 取前 3）：① 能否直接作用到验证器确认的那条代码路径（S2 的缺口）；② 方法论文适配度；③ 难度（偏好中等，简单可靠优先）；④ 文献风险。
4. **输出**：`phase1/solution_lens.zh.md`（表格 + 排序 + 理由）与 `phase1/solution_lens.json`：`{"<gap_id>": {"position": "mainline|branch", "angles": [{"type", "family", "change", "code", "difficulty", "method_fit", "lit_risk", "mature_method", "rank"}]}}`。
5. **下游**：Phase 2.1 按这份排序挑 gap × 模式，主线的 gap 先挑；选了排名外的角度要在 `composition_note` 里写明理由。生成的卡照常过卡级 soundness 门。

## 规则
- 只给已准入的 bottleneck 排解法；不借"某类贡献更高级"回头改问题。
- **类型只是挑解法的依据，不是叙事模板**。不为了凑某个"高级"类型（C、H、I）去改写问题。
- 方法论文优先：D、G、O 一般作为动机或评测部分，除非能直接落成算法。
- 难度为"极高"的（C）只列出，不作为主线，除非已经有反证数据（例如 A-37 对"确定性 WM 不能加推扰"的反证）。
