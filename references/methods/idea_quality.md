# Diagnosing idea quality

> Adapted research asset. This file contains the working method, not an instruction to run the archived workflow. Read only the part required by the current task. The [shared research contract](../contracts/research-contract.md) and [record API](../../docs/record-api.md) define persistence and version semantics. Legacy field names below describe optional working documents; they are not accepted record payloads. Candidate, material, activity, and assessment records remain the source of truth. Do not create every document or invoke another skill merely because this reference mentions it.

## Provenance and adaptation

Source: [archived original](../../vendor/research-studio/ResearchStudio-Idea/evaluation/idea_quality/SKILL.md).

Retained: A/B/C distinction, method depth/soundness/feasibility decomposition, evidence quotations, problem-fit gate, ties and anti-polish bias. Changed: optional scoring and panels; openness is evidence-limited; diagnostic weaknesses route to specific skills instead of iterative score optimization.

## Working method

# Idea Quality

Judge how strong a research idea is **at the idea stage** — before any experiments exist — and return a diagnostic assessment with reasons a reviewer would recognize. Scores are optional. The rubric judges the supplied argument and evidence; it is not a fresh literature search or experiment. Keep known raw counterevidence in scope, and state what cannot be established from the input.

## Input: an idea Markdown file

The idea is a `.md` file with three sections. Read the file, then map each section to what it feeds:

```markdown
# Title
<≤ ~15 words: the idea's handle>

## Motivation
<the bottleneck / gap the idea attacks, why it matters, and why it is still open>

## Method
<the proposed contribution as concrete numbered steps>
```

- **Title** → the handle.
- **Motivation** → feeds **Axis A** (is the problem worth attacking) and gives **Axis C** the "problem" half.
- **Method** → feeds **Axis B** (is the method good) and gives **Axis C** the "method" half.

If a section is missing or thin, infer the most reasonable reading from the rest and note the assumption in the report — do not stall asking for clarification. If the user passes two files (or one file with two ideas) and wants a comparison, run the **pairwise** track.

## Scope: what this judges, and what it deliberately does not

- **No experiments exist.** Every axis is a *reasoning-level* judgment — the kind a reviewer makes from an abstract before seeing results. **Never invent or assume experimental results to score with.** If a claim's truth would need an experiment, judge the *plausibility of its argument*, not an imagined outcome.
- **Not a prior-art check.** "Has someone already done this?" is a separate literature-collision task. Judge whether the idea is *good* (real gap, deep method, sound + on-target), NOT whether a near-duplicate exists. Judge the contribution's intrinsic ambition, not its novelty against a literature search.

A strong score means the supplied argument was assessed favorably under this rubric; it does not establish novelty, effectiveness, or acceptance.

## The three axes

Diagnose these three axes. They separate argument quality without pretending that text alone establishes factual novelty or experimental truth. None is a proxy for writing polish.

**A — Problem position quality.** Does the stated gap matter, and does the supplied evidence justify its claimed position? The text can expose a soft target or an unsupported openness claim. It cannot establish that the literature has genuinely left the gap open; route that uncertainty to research-retrieve/research-diagnose.
- Strong: a gap that matters and that the field has not closed; naming it is itself insightful.
- Weak: an obvious / already-handled problem, or a soft target chosen so it can be "solved" cheaply.
- *Why it exists:* when the author picks their own bottleneck, the cheapest way to look successful is to pick a soft target. This axis is what stops a soft-bottleneck-plus-trivial-fix from scoring well.

**B — Method quality.** Is the proposed method good in itself? If scoring, use ONE number, but in the Reason decompose into three named sub-judgments, because a single number otherwise hides *which* of them is weak:
- **depth** — a genuinely new mechanism / construction / reframing vs an incremental tweak (a new schedule, one extra loss term, a hyperparameter).
- **soundness** — does the "why it should work" argument hold up internally? Are assumptions justified, or is there hand-waving / an unstated condition / a logical gap? *Judge the method's own logic, regardless of which problem it aims at — fit is Axis C.*
- **feasibility** — is it buildable in principle, or does it require resources / oracles / data that don't plausibly exist? *This means "buildable", NOT "will get good numbers" — do not hallucinate results.* This is the softest sub-judgment; let depth dominate B and treat feasibility as a tie-breaker, not an equal third.
- *Note:* B is about the **magnitude and integrity of the method itself**, judged intrinsically — NOT whether a duplicate exists in the literature (separate prior-art task).

**C — Problem-fit.** Does the Method actually target and *plausibly resolve the specific gap in the Motivation* — rather than an adjacent, easier, or different problem?
- Strong: the method's mechanism clearly bears on the identified gap; if it works, that gap closes.
- Weak: a method aimed at a different problem than the one claimed, or one whose connection to the gap is asserted, not shown.
- *Boundary vs B-soundness:* B-soundness asks "is the method's own logic coherent?"; C asks "does that logic connect to THIS problem?" A method can be internally sound (B high) yet solve the wrong problem (C low); or on-target (C high) yet hand-wavy (B low). Keep them separate.

## Reviewer context and optional comparisons

A single reviewer is sufficient by default. If independent review is authorized and useful, provide the same candidate facts, constraints, and raw counterevidence while hiding model identity and prior scores. Retain each disagreement rather than forcing consensus. The rubric is a reasoning assessment, not a literature search or experimental finding. Fixed model seats are not part of this adaptation.

## Scoring: dual-track

The **absolute** track is optional when a score helps the user compare. When comparing two ideas, ALSO run the **pairwise** track — and treat pairwise as the trustworthy signal, because relative judgments are far less noisy than absolute numbers (which bunch around 3/5). The absolute 0–100 is a readable secondary readout, not a calibrated truth.

Per axis, score **1–5** (integer). There are deliberately no fixed level descriptors — instead **every score quotes the specific phrase / element of the idea that justifies it.** A score with no quoted evidence is not allowed; the evidence requirement, not a rubric table, is what keeps scores honest. Judge **substance, not length or fluency** — a short crisp idea can score 5; a long polished one can score 2.

### Track 1 — Absolute (per idea)

Overall score (equal weight, each axis 1→0 and 5→full):
```
overall = round(100 * (A + B + C - 3) / 12)
```
Verdict band: `strong` ≥ 67 · `borderline` 34–66 · `weak` < 34.

**A/C gate (overrides the band).** A and C are near-necessary, B is not — so:
- If **A ≤ 2 OR C ≤ 2**, the verdict cannot be `strong` (cap at `borderline` at best), regardless of the number. Reason: a great method on a trivial problem (low A), or a great problem with a method that doesn't address it (low C), is not a strong idea — and the equal-weight mean would otherwise mislead. State the cap and why in one line.
- A low **B alone does NOT cap**: a simple method that genuinely addresses an important problem (counter-intuitive minimalism) can still be strong.

### Track 2 — Pairwise (comparing two ideas)

For each axis state which idea is stronger (**Idea 1 / Idea 2 / tie**) and why, in one line; for axis B, note per-sub-judgment (depth / soundness / feasibility) which arm wins so the diagnostic isn't lost. Then give an overall winner **holistically** — but problem-fit (C) is near-necessary: **a decisive C loss usually decides the overall, even if that idea wins A and B**, because a method that doesn't fit its problem isn't the better idea. Decide each axis independently; do not let one axis sway the others.

**Judge blind to source.** If two ideas are compared as part of an evaluation, do NOT factor in which system/model produced which — provenance is not evidence of quality. (For this to be fair, the two inputs must share the same Title/Motivation/Method format; flag it if they don't.)

## Output format

For a single idea:

```
## Idea Review — <title>

**Decomposition**
- Problem / gap (from Motivation): …
- Method (the proposed move): …
- Why it should work: …
(assumptions inferred, if any: …)

**Axis scores**
| Axis | Score (1–5) | Evidence (quoted from the idea) | Reason |
|------|-------------|----------------------------------|--------|
| A — Problem position | | | |
| B — Method quality | | | depth: … · soundness: … · feasibility: … |
| C — Problem-fit | | | |

**Overall: NN / 100  ·  Verdict: strong | borderline | weak**
<if the A/C gate fired: one line naming the cap and why>

**Strongest point:** <one sentence>
**Most fixable weakness:** <one sentence, phrased as what would raise the score>
```

For a comparison, output the absolute block for each idea, then:

```
## Pairwise verdict (Idea 1 vs Idea 2)
| Axis | Stronger | Why (one line) |
|------|----------|----------------|
| A — Problem position | 1 / 2 / tie | |
| B — Method quality | 1 / 2 / tie | depth / soundness / feasibility: who wins each |
| C — Problem-fit | 1 / 2 / tie | |

**Overall winner: Idea 1 | Idea 2 | tie** — <one–two sentence rationale; if a decisive C loss drove it, say so>
```

## Anti-bias rules (why they matter)

- **Quote evidence for every score.** A bare number is a vibe, and vibes don't separate strong ideas from weak ones; tying each score to a specific claim makes the judgment auditable and the comparison fair.
- **Judge substance, not length / fluency / formatting.** A confident, well-structured write-up can dress up a thin idea — resist rewarding presentation, especially in B-soundness where fluent prose most easily hides an unsound step.
- **Stay at the idea stage.** Don't imagine experimental results to justify a score. If verifying a claim would need an experiment, score the *argument's plausibility*, not a hallucinated outcome.
- **In comparisons, judge blind to source.** Which model or system produced an idea is not evidence about its quality; ignore it.

## Route the diagnosis, not the score

- A evidence gap: research-retrieve; A value/target concern: research-diagnose or research-decide.
- B soundness/specification: research-construct/research-review; B resources: research-evolve feasibility.
- C problem-method mismatch: research-diagnose or research-construct.
- Mere prose weakness: research-report, preserving method and uncertainty.
- Reassess only after relevant evidence, mechanism, or question changes. A lower score is not a reason to run an endless polishing loop. A high score is not a scientific finding or execution authorization.
- Cite candidate text for reasoning and source material for empirical claims. Never manufacture a supported finding from a score alone.
