# Candidate construction — detailed adapted method

中文入口：[research-construct](../../skills/research-construct/SKILL.md)。共同语义见 [research-contract](../contracts/research-contract.md)，实际写入见 [record-api](../../docs/record-api.md)。方法字段保存为允许的文本内容：candidate.mechanism、claims、assumptions、predictions；来源通过 material 和 finding 关联，不增加 API 未定义字段。

来源：`vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/ideate_generate.txt`，原文 369 行。保留长段的前提/观察模型/estimand、朴素基线三分支、代码级步骤、负控制、近邻差异与数字出处。改写旧阶段文件、固定模式数量/配对、工厂预算与记忆节点否决；未决参数不补造，真实代码参与机制判断。示例性段落长度是写作建议，不是 gate。

Construct a concrete candidate from the selected problem and operation. A single coherent mechanism is sufficient; multiple components belong only when their interface and necessity have been explained. The construction can be substantively new, an application, a replication or an explicitly unverified proposal: describe the actual grade rather than assuming novelty.

A pattern taxonomy is optional. If no source sub-pattern fits, use a custom operation with the same premises, baseline, dataflow and falsification checks. If patterns help, use the reading sequence below; it is a reference lookup, not a mandatory new Agent or stage.

**Sub-step a — pick the sub-pattern under each gap's main pattern**

1. Open [the pattern index](../patterns/INDEX.md) and follow only the relevant source cards. It identifies main patterns and their sub-patterns.
2. For each `selected_gaps[]` entry, read the candidate sub-patterns'
   `when_to_pick_this_one` + `differentiation_within_parent` panels (just
   those two panels, not full cards) to evaluate which sub-pattern's
   tactical move most directly closes this gap. For the anchor entry, the
   candidate main patterns are chosen_pattern_id together with any
   anchor_alternates selection left unresolved; read the sub-cluster rosters
   under all of them. Sibling entries use their single chosen_pattern_id.
3. When a sub-pattern fits, select the operation whose `when_to_pick_this_one` describes
   the gap's situation and whose `differentiation_within_parent` separates
   it from sibling sub-patterns on a bottleneck-relevant axis.
   THIN-CORPUS DECLARATION: when the examples are distant, explain the structural mapping and its limits. A taxonomy mismatch does not require choosing a wrong card. A custom operation is permitted. Different questions can reuse the same operation when their conditions justify it
   (rare but valid). For the anchor, the pick is constrained by
   intake.contribution_type: choose the (main_pattern, sub-pattern) whose
   tactical_pattern delivers the committed artifact grade — a sub-cluster
   whose load-bearing artifact is a proof, bound, or rate when
   contribution_type is theory; a sub-cluster whose load-bearing artifact is
   a runnable or empirically-validated mechanism when contribution_type is
   method. When the top-ranked chosen_pattern_id has no sub-cluster matching
   that grade but an anchor_alternate does, pick from the alternate and carry
   it forward as this gap's main_pattern.
   COMPANION (only when selection set `companion_pattern` non-null on this
   gap — either a Step 2a CHAIN on the anchor, or a Step 3b deliverable
   pair; `companion_rationale` tells you which): for a chain, realize the
   A→O→B dataflow the rationale states. For a deliverable pair, the framing
   pattern (chosen_pattern_id) was kept BECAUSE its move
   closes the gap, but selection found it cannot ship the deliverable this
   gap demands, so it paired the leg. Carry `companion_pattern` through to
   gap_closure[] unchanged, and make core_mechanism realize BOTH halves on
   this gap: the framing pattern supplies the claim / inversion, and the
   companion supplies the missing deliverable as the object that actually
   validates the gap's closure (e.g. an `assumption_audit_and_pivot` +
   `controlled_diagnostic_design` leg states the inverted assumption AND
   ships the confound-isolating empirical separation that confirms it).
   Read additional tactics only when needed to specify the companion operation; its label does not establish that it works.
4. Follow the selected card link from the pattern index. Original C00–C30 identifiers are source vocabulary, not a required field in every new candidate.
   Read **`tactical_pattern`** (descriptive: what this cluster's papers
   look like tactically) and **`Step-by-Step`** (5 abstract imperative
   steps that capture the cluster's structural move pattern, distilled
   from the cluster's [Accept] examples WITHOUT citing specific papers,
   with [Reject]-derived boundaries embedded). The Step-by-Step is your
   tactical recipe for sub-step b.

**Sub-step b — write the candidate**

Complete the NAIVE-BASELINE AUDIT (the naive-baseline section) BEFORE
writing core_mechanism: under branch (i) the mechanism you are about to
construct is the one that solves the named obstacle — not the naive version
with cosmetics.

Write the candidate content using the outline below, then map it to the shared record API; the outline is not an API payload. `core_mechanism` walks through how each gap is
closed via the causal chain (pattern's move → applied to this gap →
produces what artifact → closes the gap because Y); `core_mechanism_reasoning`
exposes how you arrived at this design (decisions, alternatives considered);
`core_mechanism_steps` writes concrete implementation as a numbered list
so the candidate is buildable, not aspirational. Each picked sub-pattern's
`Step-by-Step` (abstract steps loaded when relevant) is your tactical
recipe — apply each step's general move pattern to your specific gap.
The steps are intentionally domain-agnostic; instantiate them concretely
for your problem rather than executing them verbatim. Do NOT cite or
mimic specific [Accept] papers from the cluster card — the sub-pattern's
abstract structural move is the guidance, not any single paper.

When `coherence_thread_type` is `n_a` (anchor-only selection): there is no
cross-gap interlock. core_mechanism serves the single anchor gap at full
depth — do NOT invent auxiliary sub-goals, bolt-on analyses, or extra
"applications" to make the candidate look bigger; depth on one gap beats
manufactured breadth. When the anchor carries a Step 2a CHAIN
(companion_pattern set as a composition, not a repair), core_mechanism must
show the chain's dataflow explicitly: pattern A's move produces the NAMED
intermediate object O, and pattern B's move consumes O to produce the
anchor's deliverable.

Otherwise the `coherence_thread_type` from selection dictates how legs interlock,
and core_mechanism must NAME the thread's specific instance:

- **shared_object**: name the central object (residual, theorem, model)
  that every leg reads from / writes to; core_mechanism centers on this
  object.
- **shared_question**: name the bottleneck-question; walk through how
  each leg's artifact attacks a different angle of it.
- **sequential_pipeline**: walk A → B → ... showing how each leg consumes
  the previous leg's output (core_mechanism_steps shows the data flow).
- **shared_audit**: name the audit lens once and walk through each site
  it is applied to.
- **shared_evaluation**: name the measurement framework and how each leg
  contributes to it (typically falsification_prediction names the metrics).

Match core_mechanism's structure to the declared thread type — don't
distort the artifacts to force a different style.

Inputs (no fixed host file layout):
- Current problem/project version: failure, conditions, stakes, hard constraints, observed facts and unknowns.
- Selected candidate/direction or parent version, actual code interfaces, data access and environment limits.
- Closest material sources with read sections and scope. Read full methods for substantive comparison; abstract-only differences remain uncertain.
- Relevant method lineage and collateral families; verify a remembered method before using it to reject novelty.
- Existing findings, original counterexamples, the exact claim affected and the proposed repair scope.
- Optional pattern/sub-pattern source cards via [the index](../patterns/INDEX.md).
Load focused materials by reference rather than the full repository or corpus. Do not discard decisive contrary evidence merely because it is not a closest positive comparison.

Hook is the candidate's opening claim. Three shapes; pick the ONE that
passes its admission test, not the one easiest to write:

(a) **Surprising empirical reveal** — name a metric in
    `falsification_prediction` whose predicted DIRECTION or regime split
    is sharply non-obvious to someone fluent in closest_adjacent. The
    surprise is in the qualitative claim; the experiment establishes
    magnitude.
(b) **Structural reframe** — cite a closest_adjacent / evidence index paper
    whose architecture / loss / eval operationalises the "unnamed"
    assumption tacitly. Unnamed means unnamed in published practice, not
    a known property re-described louder.
(c) **Counter-intuitive minimalism** — name the strongest baseline's
    load-bearing axis (params / data / new objects) and show your
    candidate is strictly ≤ on at least one such axis.

(b) is the cheapest shape — any architectural property reads as a "tacit
assumption" if re-described loud enough. Candidates that default to (b)
are often more honestly (a) or (c); run the admission test before picking.

Don't stack. If none passes, candidate isn't ready — back to selection.

Content outline (method text, not API schema):

{
  "title": "<paper-level title, ≤ 15 words>",

  "hook": "<≤2 sentences. Pick ONE shape: (a) / (b) / (c). Don't stack.>",

  "hook_shape_rationale": "<2 sentences. (i) chosen shape + admission-test evidence (named metric / cited paper + tacit assumption / baseline axis where you are ≤). (ii) which other shape was viable, why rejected.>",

  "gap_closure": [
    {"gap": "<verbatim from selection.selected_questions[].gap>",
     "main_pattern": "<from selection.selected_questions[].chosen_pattern_id; for the anchor this may instead be one of its anchor_alternates when sub-step a's grade match selected the alternate>",
     "sub_pattern": "<optional source card ID and parent, or custom operation; source attribution must be correct when a card is used>",
     "companion_pattern": "<null unless selection set companion_pattern non-null on this gap; then carry that pattern_id through verbatim. The companion supplies this gap's missing deliverable at the main-pattern level (no sub_pattern) and core_mechanism must show that deliverable.>",
     "how_closed": "<one line: which specific element of core_mechanism closes this gap, in the spirit of the picked sub-pattern's tactical_pattern (descriptive — what kind of move closes it, e.g., 'closed by reformulating the LLM-generated text record as a structured posterior representation'). When companion_pattern is set, name both halves — the framing move and the companion's deliverable.>"}
  ],

  "core_mechanism": "<5-10 sentences. For EACH gap, walk the causal chain: this pattern's move → applied to this gap → the concrete artifact it produces (residual, theorem, primitive, module) → why that artifact closes the gap. Say plainly when gaps share machinery vs need separate modules — structure follows the gaps, not a uniform style. **Make the central object computable from the text alone**: define every quantity it is built from (what it is, and where it comes from — model-internal readout / computed / external oracle), fix or give a selection rule for every free index or layer-set, and write out any weight that bridges different-unit quantities as a named hyperparameter. A reader must be able to compute the object without guessing. Ground all numbers: quantitative claims about prior work cite retrieval source materials / closest_adjacent abstracts; claims about your own predicted behavior (rates, exponents, scaling constants) cross-check full-text materials for any same-setting closest_adjacent paper — align to their value OR write the regime distinction visibly (e.g., 'we measure cumulative regret; their T^x is per-step optimization error'). Don't paste an exponent across regimes — a frequent Reject signal.>",

  "core_mechanism_reasoning": "<Three mandatory blocks, in order. BLOCK 1 — PREMISES ledger: every load-bearing empirical/domain premise the mechanism stands on, one per line, each with a one-line reason it is believed true in this field; any premise that is actually a bet gets the tag 'untested — falsification target' and should be what falsification_prediction's load-bearing variable pivots on. WHEN the mechanism consumes sampled/observed data or signals (most mechanisms do; a pure construction or equivalence contribution may not), at least ONE premise MUST be an OBSERVATION-MODEL premise: how are the mechanism's inputs/signals sampled or observed, and is that sampling unbiased/complete in THIS setting? (Censoring, selection bias, non-iid sampling, leakage, self-preference all live here — it is where the hidden assumptions that naive mechanisms silently rely on are found.) If the mechanism consumes no sampled inputs, write 'observation-model: n/a (no sampled inputs)' — never fabricate one. ESTIMAND (conditional): when the mechanism estimates or measures ANY quantity (a rate, a reward, an uncertainty, a probe score, a metric), declare the ESTIMAND precisely — the exact target quantity and over what population/process it is defined — so the coherence gate can check that the estimator the steps construct actually targets it. BLOCK 2 — NAIVE-BASELINE AUDIT: state, in one concrete runnable-in-principle sentence, the most naive/obvious version of the anchor mechanism; then answer WHY it does not already work, with the branch supported by current evidence (if not yet known, state the uncertainty and the minimum check instead of selecting a known/false branch): (i) the naive version silently relies on a premise that is FALSE in this setting (name it — often the observation-model premise) → the mechanism you write MUST confront that failure head-on; the confrontation IS the contribution, and shipping the naive version with cosmetics is a process error. STANDARD-TOOL FOLLOW-UP (branch (i) only): if the confrontation you reach for is itself a textbook tool from another field (examples, not an exhaustive list: bandits/off-policy evaluation, missing-data methods, survival analysis, active sensing, experimental design), name the DOMAIN-SPECIFIC STRUCTURE that makes this instance not already solved by the textbook tool (a budget constraint, a coupling, adaptivity, a scale regime) and make that structure part of the contribution; if no such structure exists, declare the contribution application-grade honestly — do not dress a textbook application as a method; (ii) the naive version works and the field knows it → an INCREMENTAL signal: either redesign toward a version with a real obstacle, or surface the increment honestly (it flows to composition_note / the audit's concerns) — never paper over it; (iii) the naive version works but the field believes it does not → a counter-intuitive-minimalism contribution: name the EVIDENCE of the field's belief (this is hook shape (c)'s admission test). BLOCK 3 — 2-4 sentences of design rationale (the reasoning, not the design): (a) how you decided whether multiple gaps share machinery vs need separate modules — what was the evidence; (b) what alternative core_mechanism designs you considered and why rejected.>",

  "core_mechanism_steps": "<Numbered implementation steps at the granularity the mechanism needs. Each step names (a) what to compute or modify concretely (code change, training step, evaluation procedure), and (b) inputs and outputs (what data flows in, what comes out). For any step that intervenes on the model or inference (an operator, edit, ablation, restoration), state how that modification propagates to the downstream task output — not just the intermediate quantity it changes (e.g., not 'raises margin M' but 'raises M via a second forward pass, which changes the generated answer'); otherwise the step changes a bookkeeping value with no shown effect on the result. A reader should be able to ask 'if I build this, what do I do first, second, third?' and your list answers that. Write at the code-pathway level — concrete enough to implement, not abstract design language. (Constituent-quantity definitions and units live in core_mechanism — don't restate them here.)>",

  "falsification_prediction": "<3-5 sentences containing: (a) the minimal experiment as a procedure (model / dataset / what to measure); (b) which metric moves and in which direction if the candidate works — name the metric and qualitative direction (e.g., 'foot-skating rate decreases', 'FID improves at 4 NFE on CIFAR-10', 'Spearman ρ between predicted and gold stop-time stays high'); (c) a mechanism distinguisher built around a NAMED LOAD-BEARING VARIABLE or explicitly coupled set when the mechanism requires it — the quantity (a gradient norm, an information-gain term, a learned threshold, a logit divergence, a representational direction) whose behavior carries the mechanism claim — plus a negative-control intervention on it (randomize / oracle-replace / ablate its producer / label-permute). Anti-tautology guard: the control's predicted effect MUST be the downstream task-outcome metric that defines the mechanism's value (accuracy, win-rate, regret slope, real refusal pass-rate) — NOT the variable's own value, nor a quantity analytically a function of it. 'Intervene on X → X becomes 0' only tests a definition; 'intervene on X → downstream metric moves in direction D' is the real Popper test, because 'the metric moved' alone is equally consistent with calibration, estimator quality, or distribution shift. A positive control — a stripped-down model using only the load-bearing variable that recovers most of the downstream effect — is recommended when feasible, converting a falsifier into a constructive identification. Where the setting limits observability, a full-observation oracle (an upper-bound run with the hidden quantity revealed) is the second recommended control.>",

  "compute_budget": "<estimate the actual minimum discriminating investigation, including GPU/CPU/API and human/data costs where relevant. State units, assumptions and uncertainty. Unknown user resources remain unknown; there is no funded-researcher default. A proposal does not authorize a run. If a cheaper proxy changes the information conditions or target quantity, label its narrower scope.>",

  "differentiation_from_lit": [
    {"paper_id": "<closest_adjacent paper_id from diagnosis, OR another evidence index paper that actually overlaps>",
     "delta": "<ONE SENTENCE describing what the candidate derives / claims / constructs / measures that this paper did not. Bad: 'we use a different pattern'. Good: 'they derived A under conditions B; we derive C under conditions D, where D is the user's regime.'>"},
    {"paper_id": "...", "delta": "..."}
  ],

  "almost_prior_paper_id": "<single closest paper that came STRUCTURALLY closest to the candidate>",

  "what_step_was_missed": "<a specific SUBSTANTIVE step that paper would have needed for our contribution to already exist. Substantive forms: a derivation, a construction, a regime extension, a measurement primitive, an architectural property. NOT methodological labels ('they didn't apply Tweedie', 'they used a different pattern'). Substantive example: 'they constructed the equivalence for single-network ELBO; the parallel for two-network distillation requires a teacher-conditioned augmentation distribution they didn't construct.'>",

  "signature_terms": [
    "<focused phrases covering distinct relevant mechanisms, claims and conditions>",
    "<3-7 word phrase>",
    "..."
  ],

  "alias_terms": [
    "<phrases naming the SAME core mechanism in ANOTHER community's vocabulary; no count quota>",
    "..."
  ],

  "composition_note": "<explain necessary interfaces and omitted/deferred components; a single operation needs no special defense>"
}

Hard rules (5):

1. **Substantive > methodological** in `differentiation_from_lit[].delta` and
   `what_step_was_missed`. Methodological framing ("they used pattern X, we
   use Y" / "they didn't apply Tweedie") is a process error — it describes
   method choice, not contribution. Substantive framing names what is
   derived / constructed / measured / tightened (a derivable theorem, an
   observable empirical regime, a measurement primitive, an architectural
   property without precedent, a scaling exponent).

2. **Compare with concrete prior solutions under matching conditions.** A remembered ancestral or collateral node is a retrieval lead, not proof of subsumption. Verify its operation, available information and guarantee before deciding the proposed mechanism adds nothing. If it does contain the proposal, state the honest remaining contribution, revise the mechanism, or frame the work as application/replication. Code can reveal that the current system already contains the supposed missing operation. Preserve what was actually checked.

3. **Name existing resources only.** Every dataset, benchmark, annotation
   source, tool, and model-access level (weights / logits / gradients /
   API-only) that core_mechanism, core_mechanism_steps, or
   falsification_prediction invokes must be nameable and checked for the required access — name it and state what access was verified. If the mechanism needs something that does not exist
   (a corpus with annotation X, gradients of a closed-weight model),
   redesign around an existing equivalent or scope the claim down NOW — do
   not ship an idea whose first implementation step is "first, build a
   dataset that does not exist". EXCEPTION: modest self-built resources
   (hand-labeling a few hundred examples, scripting a converter) are
   legitimate — name the artifact to build and count its cost in
   compute_budget; what is forbidden is silently assuming a LARGE resource
   into existence.

4. **State every claim at the strength you can defend.** Guarantee-grade
   assertions (unbiased / provable / exact / optimal / lossless — and any
   paraphrase of them) are permitted ONLY with their assumptions stated
   where they appear; otherwise use the honest weaker grade (consistent /
   asymptotic / empirical). The coherence gate grades every claim (T4). Do
   NOT self-censor ambition to dodge the grading: a strong claim with
   honest stated assumptions is BETTER than a hedged weak claim.

5. **Every number carries provenance.** (a) PARAMETERS: any quantity the
   procedure READS AS A PARAMETER — a threshold, budget, window, interval,
   count, weight — must be a NAMED symbol with a justified value/selection rule, or explicitly unresolved with a bounded way to choose it ("epsilon = 0.03, swept over 0.02-0.05";
   "n_min = 30, the usual floor for a stable rate estimate"). A bare
   literal buried in prose ("gate on >= 95% agreement", "the top 5", "every
   2e3 tokens") is forbidden: an unnamed quantity cannot be swept by the
   falsification plan, cannot carry an assumption at T4, and reads to a
   reviewer as a tuned magic number. This does NOT apply to numbers that
   are not parameters — named artifact versions (Qwen2.5-72B, EAGLE-3),
   algebraic/structural constants inside a formula (O(1), the 2 in mod 2,
   an interval endpoint), definitional settings (temperature 0), a
   control arm's defining value when it is already bound to a named
   parameter (epsilon = 0), or descriptive experiment-campaign scale. Campaign scale still needs cost/precision justification when it affects a scientific conclusion. The
   parameter-vs-scale line is BEHAVIOURAL: a number that changes what the
   algorithm DOES (a budget it spends, a window it fits over, the point at
   which it freezes or switches regime) is a parameter and must be named;
   a number that only sizes the evaluation campaign (corpus size,
   checkpoint count, the library size a curve runs out to) is scale. Name
   it once and reuse it — the binding may live in any method field. (b) FALSIFICATION NUMBERS: `falsification_prediction`
   states the metric and its DIRECTION plus the control — that is what makes
   it falsifiable. A numeric decision bar needs a stated basis: derived from the setup, measured in a named source, or justified by an explicit practical decision cost. Uncalibrated proposed thresholds remain unresolved; report which basis applies. Do NOT invent a bar:
   an unsourced "rho >= 0.6" or "recovers >= 80%" does not establish a justified decision threshold
   (the control already supplies it) and can either kill the idea against
   a made-up threshold or bless it against too low a one. Replication and
   scale counts (">= 3 seeds", "grow to ~200 skills") are experiment
   design, not outcome bars, and are unaffected.

Notes:

- Map each claimed closure to the exact problem version. If construction changes the question or merges/splits claims, record the delta and return the affected question to diagnosis; do not silently force a one-to-one legacy field match.
- `signature_terms[]`: focused phrases with no count quota. Cover (a) the mechanism,
  (b) the claim, (c) the setting/setup. No verbatim title strings. No
  generic terms ("deep learning", "transformer"). These get sent verbatim to
  the BM25 retriever in a targeted collision search whose time coverage matches the mechanism history.
- `alias_terms[]`: focused phrases — how OTHER research communities would
  name this candidate's core mechanism. collision retrieval runs these over a
  multi-year window to catch same-mechanism ancestors that renamed the idea;
  a paraphrased signature term catches nothing the signature channel didn't
  already catch. Do NOT reuse signature_terms vocabulary or the candidate's
  own domain wording — the whole point is the words your community does NOT
  use. Build the list from TWO sources, in this order:

  (a) MANDATORY — the collateral nodes diagnosis already named. Read
      `the diagnosis record`'s `method_lineage.nodes[]` and take every relevant node with
      `is_collateral: true`. Those nodes are, by their own definition, methods
      that "attack the same residual through a different mechanism" — i.e.
      diagnosis has already done the cross-community naming work and written the
      answer down. Emit one alias term per collateral node, phrased in THAT
      field's vocabulary (a node reading "Cost-sensitive learning with
      test/attribute acquisition costs" yields `cost-sensitive learning
      attribute acquisition`, not a restatement of your own mechanism).
      Skip a node ONLY if it is genuinely unreachable from this candidate's
      mechanism, and say which and why in `composition_note`.

      **Historical failures described by the source project; not reverified here.** In one
      run the pool never surfaced delta debugging / `ddmin` / test-suite
      minimization and the audit found them only by reading the candidate
      by hand. In the next run diagnosis pinned nine collateral families and
      `alias_terms` queried zero of them — the audit's own retrieval found
      "combinatorial group testing" hits that turned out to contain the
      candidate's exact observation model. Terms invented purely from
      parametric recall systematically miss the families the diagnosis
      already identified, because recall reaches for near neighbours in your
      own vocabulary and the collateral list is precisely the far ones.

  (b) Add useful parametric nominations for families diagnosis did not list; no quota applies. Ask "if a reward-modeling / classical-CV / RL / NLP / theory group
      had built this same mechanism 2-3 years ago, what would their papers'
      titles call it?" (e.g. a "goal-image conditioned scorer for task
      completion" is, in other vocabularies, a "goal-conditioned success
      detector" / "goal-image reward model").

  The retrieval action chooses coverage and source budgets explicitly. Preserve relevant collateral families instead of trimming to an arbitrary term count, and avoid sending an unbounded query list without purpose.
- `main_pattern` per entry comes from selection; `sub_pattern` is picked
  in this phase's sub-step a. There is no separate `patterns_used[]` field.

Store sources as materials, the mechanism as a candidate, and judgments as assessments with exact `{id, version}` refs. A test proposal is an activity plan, not an execution result. Follow the strict fields in record-api; the explanatory outline above is not directly submitted.
