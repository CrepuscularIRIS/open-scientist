---
name: innovation-lens
description: Research-taste layer between IdeaSpark Phase 0 and Phase 1 (user, 2026-11-07). After the literature pool (lit_table.md) exists and BEFORE bottleneck diagnosis, run the 15 innovation types (A–O, grouped into 5 families) over the mainline bottlenecks and our measured facts, to confirm or adjust the mainline and to produce a RANKED list of lenses. Phase 1 and the Phase 2.1 selection then use that ranking instead of letting the model pick patterns ad hoc. Use whenever an IdeaSpark run reaches the end of Phase 0 (os_next emits this layer), when choosing or re-checking the paper mainline, or when the user asks which kind of contribution or "research taste" a direction has.
---

# 创新类型透镜（IdeaSpark Phase 0 → [本层] → Phase 1）

**为什么需要这一层**：RS 的 15 种 ideation 模式偏向工程推导（"怎么改"），每轮都由 AI 自己挑两种，挑法不稳定。
本层在诊断瓶颈之前，先用 15 种**创新类型**（"哪一类贡献"）筛选、排序方向，作为 research taste。我们只做方法论文，所以它决定的是**挑哪种方法**，不是要不要写理论或评测论文。

层次关系：
- **本层（innovation-lens）**：选贡献类型，排序；
- **Phase 1**：诊断瓶颈；
- **gap-code-filter**：对照代码、做准入审计、设计层（15 种 ideation 模式 × 代码）；
- **Phase 2**：生成方法。

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
1. **输入**：
   - 本轮的 `phase0/lit_table.md` 和 `user_query.txt`；
   - 项目的实测事实 `<project>/.open-scientist/facts.md`；
   - 主线和候选瓶颈 `<project>/.open-scientist/mainline.md`（`mainline` skill）；
   - 已有的候选清单（如果项目有）。
2. **逐个瓶颈扫 15 类**：每类写一句"在这个瓶颈上它意味着什么"。写不出来的标 ✗，不要硬凑。每个候选要写清：
   - 依据的实测，或者需要补的最小实验（数字 / 未测）；
   - 代码落点 `file:line`（如果有）；
   - 难度；
   - 方法论文适配度：能落成一个算法 = 高；只能落成分析或评测 = 低，只作为支撑；
   - 文献风险：lit_table 中最接近的论文。
3. **排序**（每个瓶颈取前 3 个）。依据依次是：
   - ① 证据强度：已实测 > 可离线准入 > 只能训练后才知道；
   - ② 方法论文适配度；
   - ③ 难度：用户偏好"中"，A、B 优先；
   - ④ 文献风险。
   排序是 research taste 的显式化，**不替代**后面的准入审计。
4. **确认主线**：如果前 3 中有某个瓶颈的候选全是低适配或高风险，就建议换瓶颈，或者降为附录，写进 `<project>/.open-scientist/mainline.md`。
5. **输出**：
   - `ideaspark_run/<slug>/phase0/innovation_lens.zh.md`（表格 + 排序 + 理由）；
   - 同名 `.json`：`{bottleneck: [{type, family, claim, evidence, code, difficulty, method_fit, lit_risk, rank}]}`。
6. **下游怎么用**：
   - **Phase 1**：sub-agent 的输入里加上这份文件，要求优先诊断与排名靠前的类型相对应的 gap，但不得为了迎合排序而编造 gap；
   - **Phase 2.1**：选 gap 和模式时，排序作为优先级和打破平局的依据；选了排名外的类型，要在 `composition_note` 里写明理由；
   - **gap-code-filter**：设计层的"15 模式 × 代码"表，按本层的类型排序展开。

## 规则
- 只用已实测或可准入的事实；问题必须真实存在，不从方法反推问题，证据保守。
- **类型只是挑选方向的依据，不是叙事模板**。不为了凑某个"高级"类型（C、H、I）去编问题。
- 方法论文优先：D、G、O 一般作为动机或评测部分，除非能直接落成算法。
- 难度为"极高"的（C）只列出，不作为主线，除非已经有反证数据（例如 A-37 对"确定性 WM 不能加推扰"的反证）。
