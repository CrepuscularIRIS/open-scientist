# Specification completeness and execution feasibility

> Adapted research asset. This file contains the working method, not an instruction to run the archived workflow. Read only the part required by the current task. The [shared research contract](../contracts/research-contract.md) and [record API](../../docs/record-api.md) define persistence and version semantics. Legacy field names below describe optional working documents; they are not accepted record payloads. Candidate, material, activity, and assessment records remain the source of truth. Do not create every document or invoke another skill merely because this reference mentions it.

## Provenance and adaptation

Source: [archived original](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/implementability_audit.txt).

Retained: skeptical engineer perspective, exact objects/estimators/dataflow, equation consistency, constant provenance, open author decisions, step alignment. Rendering guidance is optional and format-aware. Changed: no hidden design defaults or renderer-only scientific repairs; resource constraints are a separate output, not erased. New mechanism/parameter decisions create H revisions and local rechecks.

## Working method

Audit specification completeness for a concrete candidate version.

Invoke this audit when method steps leave implementation decisions implicit, before or during construction. Its job
is to make the method READABLE AND IMPLEMENTABLE: turn each `method_flow` step from a one-line gesture
into a specification a competent engineer could code from without inventing the load-bearing design
decisions themselves. The motivation for this step is that the generated method steps are often too
terse to understand — a reader cannot tell WHAT exactly to build because the concrete object (the input
format, the estimator, the data structure, the sub-procedure, how a quantity is actually computed) is
left implicit.

SKEPTICAL IMPLEMENTING-ENGINEER VIEW: inspect the method as an engineer who must ship it. If authorized independent review is useful, use a separate context with the same facts and constraints; otherwise do the explicit audit locally without pretending it is independent. The author's job was to argue the idea is good; your job is to make every step concrete enough
that there is no hand-waving left to hide behind. Read each step as "could I open an editor and write
this right now? If not, what exact object is missing?"

SPECIFICATION AND FEASIBILITY ARE DISTINCT. First ask whether the method defines its objects and operations independently of price. Do not silently simplify its mechanism to fit resources. Then separately list environment blockers against actual project constraints. A complete expensive specification is complete, not feasible. Missing resources go to research-evolve feasibility or research-decide; missing scientific design goes to research-construct. Unknown resources remain unknown.

Inputs:
- Exact candidate H version, its method steps, equations, claims, and load-bearing assumptions.
- The relevant code/data interfaces and original sources for proposed algorithms or constants.
- Existing open findings and counterexamples. Hide prior attractiveness scores, not decisive facts.
- Project constraints and test intent in a separate feasibility slice; keep this distinct from the specification verdict.
- The requested view if this audit was triggered while writing or translating.

What "underspecified" means (flag a step when ANY of these is true):
- The step names an operation but not the concrete object it runs on (e.g. "extract premises" without
  saying the unit, the extractor, or the output schema; "score consensus" without the exact estimator
  and what it ingests; "train a critic" without the loss, the feature vector, or how pairs are formed).
- A quantity is referenced but its computation is not defined (what goes in, what comes out, what shape).
- A threshold / hyperparameter is used but neither a value nor a principled way to set it is given.
- A sub-procedure is assumed to exist that is itself an unsolved or unspecified subsystem (a matcher, a
  labeler, a retrieval set) — name it and specify it.
- A reader fluent in the field still could not reconstruct the data flow between this step's input and
  output.
- A `key_equations[]` entry linked to this step does not faithfully encode what the step text says it
  computes: a quantity, restriction, weighting, or condition present in one and absent or contradicted
  in the other. Equations are authored AFTER every earlier gate has run, so they are the one layer no
  prior check has read. (Observed live: a step promising Shapley coalition weights whose equation
  sampled coalitions uniformly over the power set — that is the Banzhaf value, biased for the very
  quantity the step and its own defining equation commit to.) Fill by restating the equation to match
  the step whenever the step is the authority.
- A numeric constant in a `key_equations[]` entry linked to this step has no provenance — nothing in the
  step text, the claims, or a cited paper says where it came from. An invented constant manufactures
  rigor the method never earned (observed live: a made-up per-pair variance that made a sample size
  read as derived when it was assumed, and load-bearing — a plausible alternative value moved the
  required sample outside the range the step itself states). EXEMPT, needing no separate provenance:
  literals fixed by the notation (a parity modulus, an exponent, the 1/m of a mean, a summation bound)
  and values pinned by an already-stated quantity (the z-quantiles implied by a stated α or target
  power) — flag the free input they multiply, never the notation. Fill by naming the source; leave
  `open` when only a pilot measurement by the authors can supply the value.

How to FILL a hole:
- Supply the concrete object: exact input representation, the named algorithm / estimator / model class,
  the output schema, the intermediate data structure, the precise definition of any referenced quantity,
  and source-backed parameter choices already present in the approved method or code. A newly proposed default is a design proposal, not an editorial fill; state its reason and effect and return it for an H revision.
- Preserve everything the original step already specified — units, parameters, symbols, inputs/outputs —
  and only ADD the missing concreteness. Never delete or contradict the original mechanism.
- Stay faithful to `core_claim` / `sub_claims`: you are specifying HOW to build the stated method, not
  proposing a different or better one. Do not add steps, do not remove steps, do not rename mechanisms.
- If a hole genuinely requires a design decision you cannot make without overclaiming (a choice the
  method's authors must own, where any confident fill would be fabrication), DO NOT invent detail.
  Mark it `severity: "open"` and state precisely what decision is needed. Honest open holes are far more
  valuable than confident-sounding guesses — surfacing them is the whole point of an adversarial audit.

## Optional presentation advice

Choose notation and formatting for the requested output and its actual renderer. These are readability suggestions, not a scientific gate or a requirement to use a particular engine.

- In Markdown, backticks usually keep code identifiers such as `torch.no_grad` distinct from mathematical variables. Preserve identifiers exactly.
- If the selected viewer supports math, LaTeX may be appropriate; otherwise use readable Unicode or plain-text notation. No Unicode-only or no-LaTeX rule applies to all fields.
- If a viewer interprets dollar delimiters as math, escape literal currency and check delimiter balance. A plain-text viewer may need no such escaping.
- Place a displayed equation close to its defining operation and explain its variables. Use the chosen format's ordinary line-breaking rules.
- Check the rendered output when rendering matters; do not assume the archived KaTeX/card implementation is active.
- Formatting must preserve quantities, conditions, uncertainty, and scientific meaning. An equation correction belongs to a separately recorded scientific change.

Optional working output (not a record API payload); persist issue findings and substantive candidate changes separately:

{
  "underspecified_points": [
    // Record ONLY genuinely-open holes (severity:"open") — authorial decisions that drive an inline 【…】
    // marker (rule 6). A hole you can confidently fill goes straight into enriched_steps with NO entry here
    // Existing sourced definitions may be clarified directly. New scientific choices need separate findings and H revisions. Emit [] when none are open.
    // Not rendered into the card.
    {
      "step_id": "<the method_flow step_id this hole belongs to>",
      "hole": "<one sentence: the specific object / quantity / sub-procedure left implicit>",
      "fill": "<the concrete specification that closes it — what to build, named method, input/output, existing source-backed value if defined. For severity=open, instead state the design decision the authors must make and the axis of choice.>",
      "severity": "open"
      // Only open holes are recorded here. A hole you can confidently fill folds into enriched_steps with
      // NO entry (do NOT emit severity:"filled" records — pure audit bloat).
      // open   = genuinely needs an authorial design decision; left honest, NOT fabricated. For EVERY open
      //          point you MUST also surface it to the reader by writing a 【作者需决定：…】 / 【author decision: …】
      //          annotation INLINE in that step's enriched text (each requested language field), placed right
      //          after the sentence it qualifies — see rule 6. This JSON entry stays the audit trail; the
      //          inline 【…】 is what the reader sees. Check that every open point remains visible.
    }
  ],

  "enriched_steps": [
    // For a full method view, one entry per method step; for a selected excerpt, identify omitted steps explicitly. Requested language fields are optional.
    // After semantic review these detailed texts MAY replace the corresponding view prose (a renderer may map
    // method_flow.steps[].what_changes ← what_changes, plain_method_steps_en[].what_to_do ← what_to_do_en,
    // plain_method_steps_zh[].what_to_do ← what_to_do_zh, keyed by step_id). All other step fields
    // (title, why_this_step, why_this_makes_sense, linked_component, linked_falsification, input, output,
    // and the linked equations) are left untouched, so keep your text consistent with them.
    {
      "step_id": "S1",
      "what_changes": "<pro-register detailed replacement: the concrete operation with every implicit object made explicit (input representation → named transformation/estimator/model → output schema), folding in the relevant `filled` holes for this step. Preserve all original units/parameters/symbols. This is the professional-card Method text; it may be several sentences.>",
      "what_to_do_en": "<std-register (普通版) English detailed replacement for plain_method_steps_en[this step].what_to_do: the same concrete content in plain language a practitioner outside the subfield can follow, spelling out abbreviations on first use. Preserve implementation detail; drop only jargon framing.>",
      "what_to_do_zh": "<std-register 中文 detailed replacement for plain_method_steps_zh[this step].what_to_do: natural fluent Chinese, NOT a word-for-word translation; keep identifiers / symbols / acronyms / file paths in English. Spell out each acronym's English full name on its FIRST appearance in the card, e.g. 自然语言推理(Natural Language Inference, NLI), thereafter the bare acronym. Same concrete content as what_to_do_en.>"
    }
  ]
}

Hard rules:

1. A full-method view keeps the same step IDs, count, and order. A selected excerpt states its boundaries. Check coverage explicitly; no archived validator is assumed to run.

2. Treat an executed test's inputs, prior predictions, and results as immutable history. A change to mechanism, load-bearing parameter, or claim creates H revision; a changed test plan creates T before execution.

3. Do not implement a new design inside a prose repair. Separate specification clarification from proposed mechanism changes, preserving the original and change rationale.

4. Report specification completeness and environment feasibility separately. A resource blocker does not prove the mechanism false; an undefined estimator does not become defined by unlimited compute.

5. Honesty over completeness: a hole you cannot fill without fabricating belongs in `underspecified_points`
   with `severity: "open"`, not papered over inside `enriched_steps`. The enriched text for that step
   should still be as concrete as honestly possible and may say the open decision is left to the authors.

6. Inline placement of open-decision annotations: for each `severity:"open"` point, embed a
   【作者需决定：…】 (in what_to_do_zh) / 【author decision: …】 (in what_to_do_en and what_changes) annotation
   DIRECTLY AFTER the specific sentence the decision bites — not appended at the end of the step, and not
   in a separate section. The annotation is a tight restatement of the decision + its axis of choice (no
   "the audit found", no meta). A step may carry several (place each after its own sentence). Keep the
   requested language fields consistent: the same decisions annotated at the same points.

7. Introduce formal quantities where readers can find their definition. In a step-by-step view, keeping equations beside their steps often helps. In another requested format, use clear cross-references rather than assuming a renderer imposes a particular order.

8. Std-register (普通版) readability contract — the std fields (what_to_do_en, what_to_do_zh) are read by a
   practitioner OUTSIDE the subfield, so each one must stand on its own with no untranslated jargon and no
   dangling reference:
   (a) Spell out every acronym's English full name on its FIRST appearance in the card, then use the bare
       acronym — e.g. 自然语言推理(Natural Language Inference, NLI) / Natural Language Inference (NLI).
   (b) In what_to_do_zh, do NOT drop a bare English jargon WORD into the Chinese sentence when a plain Chinese
       term exists: write 支持/蕴含 not "entail", 反对 not "contest". (Identifiers, acronyms, symbols, file
       paths, dataset/tool names stay English — those are not jargon words.)
   (c) The std prose must be self-contained: never reference a numeric threshold, default value, or symbol
       that appears ONLY in the pro `what_changes` or inside an equation. In particular never call something a
       "placeholder / 占位" in the std text, because the value it stands in for is not shown there — state the
       quantity in plain words instead (e.g. "嵌入相似度要高到什么程度才算同一条" not "聚类阈值只是占位").
   (d) Spell out terse logical/notational shorthand the first time it appears — e.g. write "给前提套个逻辑否定词
       『非』(即直接取反)" not a bare "加『非』".

Output: a specification finding with exact subject version, optional proposed enriched text, environment blockers listed separately, and a targeted next action.
