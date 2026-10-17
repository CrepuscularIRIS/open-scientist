# Gap × operation selection — adapted detailed method

中文入口：[research-ideate](../../skills/research-ideate/SKILL.md)，完整构造见 [ideate_generate](ideate_generate.md)。共同记录见 [research-contract](../contracts/research-contract.md) 与 [record-api](../../docs/record-api.md)。

来源：`vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/ideate_select.txt`，原文 365 行。保留实际接口、移除测试、模式适用性、交付物兑现、替代操作与失败障碍；移除模式数配额、固定 sibling 数、固定随机抽取、配对白名单、旧文件布局和阶段流水线。示例模式与卡片从 [模式索引](../patterns/INDEX.md) 按需读取。

Mechanism selection takes the current diagnosis and proposes a mechanism binding, with a primary problem and only those additional components needed to answer it. Anchor-only is a legitimate outcome. Patterns are optional operational vocabulary, not mandatory quotas or novelty certificates. Selection and construction can happen in one context when useful; record the distinction between an unbound direction and a concrete mechanism.

Why preserve this detail: a component belongs because its operation is necessary, not because the paper should look larger. The source's removal test, deliverable check and positive obstacle requirements address concrete failures. The new suite removes the original pattern-count commitment, random audition, fixed schema files and fixed retry count.

Inputs:
- Current project/problem and candidate versions, original materials and explicit constraints.
- Diagnosis: failure conditions, stakes, closest comparisons, open questions and relevant method lineage.
- [Pattern index](../patterns/INDEX.md), only when operation vocabulary helps. Read Definition, Operational signature and When to apply for relevant patterns. Read sub-pattern tactics during construction when needed; no forced match to a taxonomy.
- Existing pattern combination examples, reachable from that index, are leads rather than an allowed-pair whitelist.
- Code interfaces, actual data access, user resources and unknowns.
- Prior findings, failed candidate versions and surviving assets when revising.

Prior findings are scoped constraints. On a revision:
- Read the prior verdict rationale and triggering findings, and avoid gap×operation combinations that would re-walk into the same documented rejection lesson, anti-pattern interaction or exact-mechanism collision. These are hypotheses about risks unless the actual evidence establishes the failure.
- Prefer a previously deferred question when it becomes necessary to the primary claim, but apply the same removal test. An anchor-only (or anchor-plus-chain) selection is a valid revision, especially when prior findings concentrated on its sibling entries.
- POSITIVE OBSTACLE DIRECTIVES: if the previous candidate carried blocking obstacle findings or an equivalent-to-naive judgment — "the mechanism did not confront X" — the named obstacle X becomes a requirement for the next mechanism, not just something to avoid. Prefer the operation whose natural mechanism must solve X head-on, and record that obligation in selection_rationale so construction inherits it.
- When those entries carry a structural_requirement, it is a load-bearing input: it states the identifying condition a mechanism needs, which sources of it are available versus excluded (and why), and what is worth salvaging from the failed attempt. Treat a source excluded by evidence or a user constraint as a constraint; a speculative concern remains uncertain. The salvage list contains assets a new selection may keep rather than re-derive. It may also re-scope: when the evidence shows the primary gap does not actually require the failed component, a design around the surviving component can be the cheapest live path.
- Keep the failed version, original evidence and reasoning in the assessment. Do not erase retry history or treat a renamed mechanism as a new answer. There is no fixed retry count; a new evidence-bearing action or materially different operation justifies continuing.

OPTIONAL — cross-run duplicate leads: related prior candidates may carry a title, mechanism and signature terms. These are SOFT negative anchors, weaker than demonstrated failure constraints: adjacent directions gravitate toward the same mechanism families, and silently reinventing an earlier mechanism wastes work.
(a) Do not prioritize a duplicate mechanism among otherwise equal options unless the current question genuinely demands it.
(b) When it does, state the substantive delta from the earlier candidate explicitly; source identity, scope and changed conditions matter more than wording.
(c) These anchors never veto selection on their own. Related candidate records are context, not literature: never cite them as published prior art.

Pattern reading details: read each relevant pattern's Definition (what the pattern is conceptually), Operational signature (the abstract move) and When to apply (conditions for reaching for it). Selection is by gap-operation fit at the WHAT / WHEN level, not by forcing a problem into a recipe's steps. Tactical HOW-level sub-patterns can be deferred until construction. If a proposed pairing does not have an example in the source corpus, name its dataflow and why it is scientifically needed; absence from the corpus is not a veto. Published pairings are not evidence that a pairing works in the current problem.

Selection process:

`intake` below is a working note assembled from the current project, not an API field. Contribution type is binding only when the user made it a requirement. If evidence suggests a different valuable deliverable, describe it as an option; do not force the taxonomy or silently change the user's goal. Custom operations can use the same checks without sub-pattern IDs.


**Step 1: Pick the anchor gap (type-bound).** From
`open_questions[]`, identify the single most important gap —
the one whose closure is most load-bearing for the bottleneck AND whose own
demanded deliverable matches `intake.contribution_type`. Read the gap's
verb: "give / yield / produce / construct a [fix that does X]" demands a
CONSTRUCTION (mechanism); "question / test whether / isolate" demands an
ANALYSIS or DIAGNOSTIC. The anchor must be a gap whose demanded artifact IS
the committed `contribution_type` — a construction gap when `method`, a
proof/analysis gap when `theory`. Binding the type here, at anchor
selection, is what guarantees the paper's load-bearing deliverable is the
type diagnosis committed to, so no separate set-level coverage step is needed
downstream. Add to selected_gaps as the anchor.

**Step 2a: Check whether composition is actually needed.** Check whether
the anchor's closure is best built as a CHAIN of two patterns: pattern A's
move produces an intermediate object O, and pattern B's move operates on O
to produce the deliverable the anchor demands. One target, one story, two
moves — this is how the corpus's multi-pattern Orals compose. Mechanics:
- Existing pattern pairings can suggest an operation. New pairings are admissible when their interface, conditions and differentiating consequence are explicit; membership alone proves neither coherence nor novelty.
- To adopt a chain you must state it concretely — "A's move yields O; B's
  move on O yields the demanded deliverable" — NAMING O. If you cannot name
  O, the chain is decorative; drop it.
- Record an adopted chain by setting the anchor entry's `companion_pattern`
  to the second pattern and writing the A→O→B statement in
  `companion_rationale`. (This generalizes companion_pattern beyond Step
  3b's deliverable-rescue trigger: a chain adopted here is a first-class
  composition choice, not a repair. Step 3b's realizability check still
  applies on top.)

**Step 2b: Audition siblings (admission by the REMOVAL TEST).** From the
remaining questions, inspect the ones whose resolution may be necessary for the primary claim. Do not randomly fill slots. Admission of an additional component requires BOTH tests:

- Coherence thread (NECESSARY, never sufficient): one of the five types
  below connects it to the anchor. NOTE: every gap in
  `open_questions[]` descends from the same bottleneck, so
  type (b) shared_question is satisfiable almost by construction — it can
  NEVER be the sole basis for admission. Five thread types:
    (a) **shared_object** — both legs use the same residual / theorem /
        model / forward model / divergence functional as their central
        mathematical primitive
    (b) **shared_question** — both legs attack the same bottleneck from
        different angles (e.g., one derives a bound, the other empirically
        validates it on the same regime)
    (c) **sequential_pipeline** — leg A's output is leg B's input; the
        legs form one pipeline rather than parallel modules
    (d) **shared_audit** — same auditing lens (e.g., "what implicit
        assumption is binding") applied to multiple sites within the
        bottleneck
    (e) **shared_evaluation** — both legs measured by / contribute to the
        same evaluation framework (e.g., a method leg + a benchmark leg
        validating it)
- REMOVAL TEST (DECISIVE): imagine the paper WITHOUT this sibling.
  Admission requires that the anchor's story is INCOMPLETE without it — at
  least one of: (i) the falsification of the anchor's claim becomes weaker
  or unrunnable; (ii) an obvious reviewer objection opens that this sibling
  closes; (iii) the anchor's claim loses verifiability. If the paper is
  merely "smaller but still sound" without it, the sibling FAILS — move it
  to deferred_gaps with reason "fails removal test — anchor stands without
  it". A sibling that needs its own NEW machinery (rather than riding the
  anchor's machinery) is a second paper, not a component — defer it.

Admitted siblings record their removal-test justification in
`selection_rationale` (auditable). Keep only components needed for the current bounded question.

If NO auditioned sibling passes, proceed anchor-only (with the Step 2a
chain when one was adopted). This is a normal outcome, NOT a failure: do
NOT resample additional batches hunting for admissible siblings, and do NOT
re-pick the anchor to make siblings admissible.

End state: one primary problem with only necessary supporting components. A single operation needs no special defense. Record deferred questions and why; do not resample until the design meets an artificial count.

**Step 3: Pick the pattern per gap (the anchor may carry deferred candidate operations).**

a. For EACH gap in selected_gaps, list the patterns whose move (per
   Operational signature, conditioned by When to apply) would, if applied
   to this gap, produce what's needed to close it (a derivation, a
   construction, a measurement, a probe — whatever the gap shape calls
   for). Keep distinct operations whose conditions are plausible.
   For the anchor gap, enumerate candidates by the residual the gap must
   close, not by the gap's surface verb: a pattern from a different
   mechanism family that closes the same residual through a different move
   must not be excluded because the gap was phrased in one family's
   vocabulary. When to apply is matched against the residual, so the
   enumeration spans families rather than collapsing to the most literal
   framing.
b. For each candidate pattern (per gap), judge substantively: does this
   pattern's move, applied to this gap, actually produce what's needed?
   "X's move applied to gap Y closes Y because Z" is the judgment, NOT
   surface similarity matching. Pick the pattern whose move most directly
   closes the gap. PRIOR-SOLUTION CHECK: compare the proposed operation with concrete known methods and their conditions. A remembered lineage node is a retrieval lead, not a veto. If verified prior work already supplies the same operation and guarantee under the same conditions, state the remaining contribution honestly; change the mechanism or classify the work as application/replication if appropriate. Code may show the supposed missing component already exists. Carry the exact overlap and unresolved difference into construction.
   DELIVERABLE REALIZABILITY (all legs). After picking the pattern whose move
   best closes a gap, check it can actually SHIP the deliverable that gap
   demands at the type the problem needs. A runnable / empirically-validated
   mechanism is the native deliverable of `architectural_operator_substitution`,
   `generative_process_redesign`, `self_supervised_signal_engineering`,
   `decompose_and_delegate`; a proof / bound / rate / class-separation is the
   native deliverable of `characterize_limit_then_surpass` or a theory-only
   audit. The failure this catches: a framing-strong pattern whose honest
   deliverable is the wrong type — canonically `assumption_audit_and_pivot` on
   a `method` problem, where the audit correctly names and inverts an
   assumption but its honest output is an identifiability claim, not the
   empirical artifact a `method` paper ships. Never resolve this by
   over-claiming a theorem the leg cannot prove, and never silently down-scope
   the leg to a weaker claim. Use one of two resolutions:
     - RE-PICK — drop the framing pattern and make the deliverable-owning
       pattern the `chosen_pattern_id` directly (no companion).
     - PAIR — keep the framing pattern as `chosen_pattern_id` and name a
       `companion_pattern` that owns the missing deliverable. The companion
       is chosen by deliverable-fit and an explicit dataflow: its operation owns the deliverable the framing operation cannot produce
       (e.g. for an audit leg whose validation IS an empirical separation,
       `controlled_diagnostic_design` owns the confound-isolating separation).
       Give the reason in `companion_rationale`.
   Choose RE-PICK vs PAIR by whether the framing move is the gap's IDENTITY.
   When the gap exists precisely BECAUSE an assumption was never tested — its
   wording is itself an audit/pivot (`tests whether …`, `no leaf asks whether …`,
   `assumes X but none questions X`) — the audit IS the contribution; keep it
   primary and PAIR, since re-picking would demote the headline (the overturned
   assumption) to implicit framing and lose what makes the gap novel. RE-PICK
   only when the inversion is incidental and the gap's real demand is just the
   diagnostic or mechanism. Leave `companion_pattern` null whenever the chosen
   pattern already ships the demanded type — most legs need no companion.
   ANCHOR OBLIGATION (anchor leg only). Step 1 bound the anchor gap to
   `intake.contribution_type`, so the anchor LEG — its `chosen_pattern_id`
   together with any `companion_pattern` — must carry that committed artifact:
   either the chosen pattern ships it directly, or, when the chosen pattern is
   the load-bearing framing move, its companion does. This is the same
   realizability rule above with one added guarantee: for the anchor the
   demanded type is fixed by `contribution_type`, not by the gap alone. Prefer
   a single clean pattern for the anchor when its framing pattern is not itself
   load-bearing — a headline reads better undivided — but PAIR is legitimate
   when the audit is the contribution. Record where the committed-type artifact
   lives (the anchor's pattern, or its companion) in `deliverable_coverage`.
   ANCHOR DEFERRED BINDING: selection at Step 3 reads only Definition /
   Operational signature / When to apply — the WHAT/WHEN level — and cannot
   see whether the chosen parent's sub-cluster roster carries a sub-cluster
   whose load-bearing artifact matches intake.contribution_type. That is a
   HOW-level property held in the sub-cluster cards, which only construction
   reads. So for the anchor gap, if more than one candidate survives the
   substantive judgment, the REGRESSION CHECK, and the ANCHOR OBLIGATION, do
   NOT collapse to one: record the top-ranked candidate as chosen_pattern_id
   and useful unresolved alternatives as anchor_alternates. construction makes
   the final pick among them once it reads the sub-cluster grades. Sibling
   gaps always collapse to a single chosen_pattern_id.
c. The same pattern may be chosen for multiple gaps if its move closes
   what each of them needs (this produces a 1-leg paper). Different
   patterns across gaps may be chosen if each gap needs a distinct move
   (this produces a multi-leg coordinated paper).
d. A known pattern distribution may be recorded as optional context; it never supplies a quota, exclusion rule or novelty verdict. A crowded family needs a substantive comparison, and a new family needs evidence for its applicability, not a claim that rarity itself is value.
e. Declare `coherence_thread_type` (one of the 5 from Step 2b), or `n_a`
   when the selection is anchor-only — there is no cross-gap interlock to
   type. The thread's
   specific instance (the named object, question, pipeline, audit lens, or
   framework) is produced by construction inside `core_mechanism` —
   selection's job is to commit to the type, not to pre-name the instance.

Content outline (selected fields for a candidate/assessment body; not record API arguments):

{
  "selected_gaps": [
    // selected_gaps[0] is the anchor; selected_gaps[1..] are coherent siblings.
    {
      "gap": "<question and exact project version reference>",
      "chosen_pattern_id": "<optional known pattern_id or custom operation; fit the problem, not the taxonomy>",
      "anchor_alternates": ["<useful additional operations, ranked, anchor entry only — the deferred-binding candidate set construction chooses from alongside chosen_pattern_id. Empty for sibling entries and when the anchor has a single clear best fit>"],
      "companion_pattern": "<null by default; a valid pattern_id when EITHER (Step 2a, anchor entry only) a chained composition was adopted — the second pattern whose move consumes the named intermediate object the anchor pattern produces — OR (Step 3b, any entry) the DELIVERABLE REALIZABILITY check fires: chosen_pattern_id is the right framing move but cannot ship the deliverable this gap demands under intake.contribution_type. Either way name the actual interface and contribution; a corpus pairing is optional evidence, not a permission gate.>",
      "companion_rationale": "<empty when companion_pattern is null. For a Step 2a chain: the A→O→B statement — what object O the anchor pattern's move yields, and what the companion's move on O produces. For a Step 3b pair: which deliverable chosen_pattern_id cannot ship for this contribution_type, and why this companion owns it.>",
      "selection_rationale": "<2 sentences: (a) for anchor, why most load-bearing for the bottleneck; for sibling, how this gap connects to the anchor under coherence_thread_type. (b) what the chosen pattern's move closes in this gap. Anchor entries can compress (a) since the anchor's load-bearing claim doubles as its connection statement.>"
    }
  ],

  "coherence_thread_type": "shared_object | shared_question | sequential_pipeline | shared_audit | shared_evaluation | n_a (anchor-only selection)",

  "deliverable_coverage": "<one line from the Step 3b ANCHOR OBLIGATION: the declared intake.contribution_type, and where in the anchor LEG the load-bearing deliverable of that type lives — the anchor's chosen_pattern_id, or its companion_pattern when the chosen pattern is the load-bearing framing move (e.g. 'method — anchor gap → architectural_operator_substitution yields the runnable fix', or 'method — anchor gap → assumption_audit_and_pivot framing + companion controlled_diagnostic_design ships the empirical separation').>",

  "user_direction_disposition": {
    // Classify the user's original direction as hard constraint or provisional solution.
    // Hard constraints stay binding. A different user goal requires a user decision.
    // A provisional mechanism may be revised with evidence and an explicit explanation.
    "verdict": "adopted | departed | n_a",
    "user_wanted": "<VERBATIM from intake.user_direction; omit when n_a>",
    "chosen": "<what the anchor gap + pattern composition actually targets; omit when n_a>",
    "why_departed": "<REQUIRED when departed. Argue from the GAP: what the chosen path closes that theirs does not, or what theirs costs (a new architecture, paired data, a retrain) that the chosen path avoids. 'Cleaner' and 'more general' are not reasons. If you cannot write this, you have not actually justified departing and should re-examine the anchor.>"
  },

  "composition_note": "<why each operation is needed; one operation is ordinary, not an exception>",

  "deferred_gaps": [
    {"gap": "<question and exact project version reference>",
     "reason": "<one line: fails removal test — anchor stands without it / no coherence thread connects this gap to the anchor / out of scope / future work>"}
  ]
}

Version rule:

Refer to the exact problem version. If selection reveals a necessary change in the question, record its rationale and return to diagnosis rather than silently rewriting the question inside a candidate. Changes to the user's declared objective require their decision; revisions to a provisional diagnosis stay within the authorized inquiry. Candidate variants can share a problem without forcing all unselected questions into this candidate.

Notes:

- The 15 valid `pattern_id` values: `reframe_as_solvable_object`,
  `assumption_audit_and_pivot`, `algebraic_equivalence_unification`,
  `heterogeneous_decomposition`, `architectural_operator_substitution`,
  `structural_prior_encoding`, `characterize_limit_then_surpass`,
  `self_supervised_signal_engineering`, `targeted_self_supervised_objective`,
  `controlled_diagnostic_design`, `unify_into_shared_representation`,
  `adapt_via_conditioning`, `generative_process_redesign`,
  `decompose_and_delegate`, `relax_discrete_search_to_continuous`.

Record material sources, candidate directions and selection assessments through the shared API; use `{id, version}` refs. Do not write a legacy stage file.
