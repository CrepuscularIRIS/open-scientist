# Plain-language research views

> Adapted research asset. This file contains the working method, not an instruction to run the archived workflow. Read only the part required by the current task. The [shared research contract](../contracts/research-contract.md) and [record API](../../docs/record-api.md) define persistence and version semantics. Legacy field names below describe optional working documents; they are not accepted record payloads. Candidate, material, activity, and assessment records remain the source of truth. Do not create every document or invoke another skill merely because this reference mentions it.

## Provenance and adaptation

Source: [archived original](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/derive_plain.txt).

Retained: register transformation, no invented facts, natural Chinese order, method-step alignment, and readable notation. Rendering advice now depends on the actual requested format rather than an archived renderer. Changed: one requested view at a time; no fixed model tier or mandatory derive pipeline. Added: unresolved issues and evidence boundaries must survive translation; scientific changes return to construction.

## Working method

# Plain-register derivation and translation

You derive the plain-language (普通版) fields of the technical view from its ALREADY-WRITTEN
technical fields. This is register transformation and translation, NOT authoring: every statement
you write must be derivable from a technical field that already exists in the expansion. You add
no invented facts, mechanisms, numbers, or caveats. Existing findings and uncertainty from the exact record basis must remain visible. If a technical field is unclear,
render it faithfully at the same level of precision — do not resolve ambiguity by inventing.

Use a model/tool appropriate to the task; no fixed cheap seat is required. The input is the finished technical view and exact candidate version. Read the technical fields from which the requested plain fields derive, plus unresolved issues and evidence boundaries that must survive compression. Other views are optional.

## Optional presentation advice

Choose notation and formatting for the requested output and its actual renderer. These are readability suggestions, not a scientific gate or a requirement to use a particular engine.

- In Markdown, backticks usually keep code identifiers such as `torch.no_grad` distinct from mathematical variables. Preserve identifiers exactly.
- If the selected viewer supports math, LaTeX may be appropriate; otherwise use readable Unicode or plain-text notation. No Unicode-only or no-LaTeX rule applies to all fields.
- If a viewer interprets dollar delimiters as math, escape literal currency and check delimiter balance. A plain-text viewer may need no such escaping.
- Place a displayed equation close to its defining operation and explain its variables. Use the chosen format's ordinary line-breaking rules.
- Check the rendered output when rendering matters; do not assume the archived KaTeX/card implementation is active.
- Formatting must preserve quantities, conditions, uncertainty, and scientific meaning. An equation correction belongs to a separately recorded scientific change.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▸ CHINESE WORD ORDER — applies to EVERY `_zh` field below

An English relative clause becomes a SEPARATE Chinese clause. It does NOT become a
modifier in front of the noun. Chinese cannot carry a long pre-nominal modifier: the
reader has to reach the end before learning what is being described, and the sentence
reads as translated rather than written.

The test is mechanical — if what sits before 的 runs past ~18 characters with no comma,
split it. Put the noun first and let the description follow as its own clause.

  WRONG  一个在九个部分正确而只在一个部分失败的程序会得到与完全坏掉的程序相同的分数
  RIGHT  一个程序九个部分都对、只有一个部分错，它拿到的分数却和完全坏掉的程序一样

  WRONG  引用不存在菜单命令或视频从未演示过的 API 签名的技能会通过同样的检查
  RIGHT  有的技能引用了不存在的菜单命令，有的引用了视频从未演示过的 API 签名 —— 它们
         通过的检查和正确技能完全一样

Two more calques to avoid: `held-out` is 留出 (not 保留), and "the two bits" is 两个二值
判定 (not 两个位, which reads as two positions).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Output (a flat derive_map JSON)

When a structured derive map is useful, save only the requested fields from this vocabulary at a project-selected path. A plain Markdown rewrite is equally valid:

```json
{
  "title_zh": "...",
  "plain_motivation_en": "...",
  "plain_motivation_zh": "...",
  "plain_method_steps_en": [...],
  "plain_method_steps_zh": [...],
  "plain_method_modules_en": [...],
  "plain_method_modules_zh": [...]
}
```

Keep derived view fields separate from candidate definitions and executed test records. Do not call archived phase4 assembly commands or rewrite a research claim through this optional map.

## Field schemas

**`title_zh`** — Chinese translation of `title`. Natural academic Chinese; keep proper nouns and
method acronyms in English (e.g. GRPO, PB-GRPO).

**`plain_motivation_en`** — plain-language English rendering of the finished `motivation.*` fields
for a reader outside this subfield. Simplify the LANGUAGE only — never drop the load-bearing
mechanism. Spell out every abbreviation on first use (e.g. 'GRPO (Group Relative Policy
Optimization)'). Multi-paragraph prose mirroring problem_framing → why_now → why_prior_stopped →
what_changes_when_gap_closes.

**`plain_motivation_zh`** — Chinese 普通版 counterpart. Same content and mechanism; keep code
identifiers, math symbols, file paths, and method/abbreviation acronyms in English (e.g. GRPO,
m_q, A_i). Obeys CHINESE WORD ORDER above.

**`plain_method_steps_en`** and **`plain_method_steps_zh`** — per-step plain rendering mirroring
`method_flow.steps`: SAME step_ids, SAME count, SAME order. Each entry:
`{step_id, what_to_do, why_this_makes_sense}`. Preserve units / parameters / inputs / outputs;
drop only the jargon framing fields (`linked_component`, `linked_falsification`).

**`plain_method_modules_en`** and **`plain_method_modules_zh`** — group the steps into named
modules. Each entry: `{module_id, purpose_oneline, step_ids}`. Derive the grouping from
`method_flow` (its step titles and the modules implied by the technical prose); the same grouping
must appear in both languages.

Distinguish three useful kinds of step when presenting a technical method. The order helps readers understand dependencies; it is not a required renderer implementation:

1. **Pre-existing setup** the contribution is built ON — the frozen backbone, the planner, the data
   pipeline, exposing an internal tensor. Leave these unclaimed (or name one module
   `Background`): they belong first, because the reader cannot implement the contribution without
   knowing what it attaches to. Keep them at FULL implementation detail — this bucket is what tells
   an author what they are building on, so brevity here is a defect, not a virtue.
2. **The contribution** — one module per coherent mechanism.
3. **Validation apparatus** — ablation switches, control/baseline arms, evaluation protocol,
   oracle measurements, estimator checks. These are NOT background: they are things you do AFTER
   the mechanism exists, and they are unreadable before it. Give them their own trailing module
   (e.g. `M<last>_validation`) so the test apparatus follows the mechanism it evaluates. Do not make validation look like a prerequisite that the reader must digest before seeing the idea.

## Hard rules

1. **Mirror rule**: `plain_method_steps_{en,zh}` MUST mirror `method_flow.steps` exactly — same
   `step_id`s, same count, same order. Check this alignment explicitly; do not assume an archived validator ran.
2. **Symbol rendering**: choose plain text, Unicode, or rendered math according to the requested view. Preserve mathematical meaning, code identifiers, and units. Explain quantities in words when that helps the audience; do not omit a necessary definition because the chosen renderer differs.
3. **No new content**: if you find yourself writing a sentence with no source in the technical
   fields, delete it. Fidelity beats fluency.
4. **Register**: the zh fields target a domain-newcomer reader (研究生新生能读懂); the en plain
   fields target a technically-literate reader outside this subfield. Neither is a children's
   explanation — keep every quantity and condition.

## Current execution boundary

The JSON vocabulary above is an optional view representation, not a record API payload. Generate only requested languages and views. When translation exposes an undefined mechanism or missing parameter, retain the open question and hand it to research-construct; do not resolve it by inventing a value. A purely linguistic change stays a View change. Any proposed scientific correction is separately recorded as a finding before H is revised. Check that uncertainty, negative evidence, units, scope, and conditional tense survive the rewrite.
