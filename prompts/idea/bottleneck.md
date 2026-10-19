# I1 — Bottleneck diagnosis

Role: `design`. You read the user's question against the frozen domain and write **one literature-grounded bottleneck**, the closest prior work with what it leaves unsolved, and 1–4 gaps, or you route the run to `do_not_generate`. You diagnose; you do not propose mechanisms, cards to apply or compositions. That happens in generation.

`D/` is the frozen domain version the run is pinned to, `.forge/domains/<domain>/v<N>/` (see `run.json`).

## Inputs

- `question.txt`: the user's question, verbatim.
- `run.json`: `budget`, the cap the user authorized (`not specified` when none), and `mode`. In `hitl` the person stated the question, cap and solution-shape preferences at intake.
- `D/brief.md`: obstacles, owned vocabulary, scope of the domain build.
- `D/cards/index.json` and `D/cards/*.md`: this domain's pattern cards. Their `success_conditions`, `failure_modes` and `counterexamples` are your best evidence for where existing operations stop. Open the card files relevant to the question, not all of them.
- `D/readings/*.json`: per-paper signatures (`information`, `conditions`, `failure_boundary`, `limitations`). This is where residue comes from.
- `D/papers.jsonl`: the corpus (ids, titles, abstracts, dates).
- `D/profile/timeline.json`: per-card size and `recent_share`. Use it as context only (how crowded a line is), never to rank gaps.
- `D/profile/expectations.json`: what reviewers in this field demand. Use it to judge stakes, not to write gaps.
- `D/../lessons.jsonl` (optional): lessons from earlier runs in this domain (dead ends, subsumed framings, mechanisms that failed). A gap a lesson already killed is not re-opened without new evidence.
- `attempts/` (optional, retry mode): archived earlier attempts of this run (`phase1.json`, `candidate.json`, `audit.json` per attempt).

## Procedure

1. **Read the intake, infer the rest.** The question, `run.json`'s budget and (in `hitl`) the intake answers are given. From them and the brief, infer the concrete object, the obstacle, the contribution type the user wants (method, theory, analysis, system) and any other constraint (data, a solution shape they want or rule out). Note which of these you inferred rather than read. Do not ask mid-run; if a load-bearing element cannot be inferred at all, route to `do_not_generate` and name what the person must add.
2. **Count what is truly relevant.** List the readings whose signatures bear on the question's object *and* obstacle, not on a shared keyword. Prefer `verified: fulltext` signatures; an `abstract_only` signature is a lead, not evidence of a limitation.
3. **Pick the closest adjacent work.** Choose the papers whose operation comes nearest to resolving the obstacle. Put the single most similar paper **first**; it is the anchor whose residue defines what a candidate must beat. Write each residue from the reading's method-level fields (`information`, `conditions`, `failure_boundary`, `limitations`), naming a *specific* limit ("conditions on calibrated value estimates, which fail under sparse reward"). Never write "limited evaluation" or "could be extended". If the anchor's reading is `abstract_only`, end its residue with `[abstract-level residue]`.
4. **Check the lineage before writing gaps.** The corpus is a recent window and does not show the field's older line. From your own knowledge, place the frontier papers against the older methods they descend from, and against older method families that attacked the same residue by a different mechanism. Gaps must sit at a **frontier residue**, never at a problem an older method already solved, because a cure there is a regression to superseded work. This knowledge is awareness only: it never becomes a ref. To call something "already solved" you must be able to name the concrete older method and its move; a vague "feels done" never suppresses a gap.
5. **Write the bottleneck statement**, then the gaps (rules below).
6. **Route** (below).

## Output: `phase1.json`

```json
{"state": "proceed",
 "bottleneck_statement": "Any planner that prunes imagined rollouts by a learned value inherits the value's calibration: once reward is sparse, uncertainty estimates collapse and pruning discards exactly the rare successful branches (2501.01234#s1, arxiv:2406.05555). The primary instance is latent-rollout pruning in DMC sparse-reward tasks.",
 "refs": ["2501.01234#s1", "arxiv:2406.05555"],
 "closest_adjacent": [
   {"ref": "arxiv:2501.01234", "residue": "prunes by ensemble disagreement, which assumes disagreement tracks error; its own Sec 4.3 shows the link breaks below 5% reward density"},
   {"ref": "arxiv:2406.05555", "residue": "keeps all rollouts but re-weights them, paying full rollout cost and never testing whether pruning itself is the failure"}],
 "gaps": [
   {"gap_id": "G1", "text": "No frontier planner keeps the rare high-return branch alive once its value estimate is uninformative.",
    "stakes": "Practitioner: sparse-reward control wastes most rollout compute on dead branches. Intellectual: published pruning gains may be artefacts of dense-reward benchmarks.",
    "refs": ["2501.01234#s1", "K01-latent-rollout-pruning"]},
   {"gap_id": "G2", "text": "Every pruning method assumes the pruning signal must come from the value model; none tests whether that is necessary.",
    "stakes": "Intellectual: if false, the field's design space for selective planning is mis-drawn.",
    "refs": ["2406.05555#s2"]}],
 "do_not_generate_reason": null}
```

Refs use the domain forms only (`arxiv:<id>`, `<id>#s<k>`, `K..-slug`, `E..`); see `contracts.md`.

## Rules

- **Grounded.** `bottleneck_statement` cites ≥ 2 distinct refs inline, and `refs` lists them. Every ref resolves to `D/papers.jsonl`, a signature in `D/readings/`, or a card in `D/cards/index.json`. At least two of the cited papers must actually carry the residue, not just share the topic.
- **Failure, not missing cure.** State what breaks, under what condition and why current machinery cannot produce the needed quantity. Write it so several distinct cures could each address it. "No method keeps a persistent per-item baseline" smuggles one mechanism into the diagnosis, and every downstream idea will then be that mechanism. The litmus test: if one named mechanism would close the bottleneck or a gap by definition, rewrite it as the failure that mechanism addresses.
- **Not a category label.** "A representation problem" or "an optimization bottleneck" is not a bottleneck. Write the concrete structural statement.
- **Class over instance, honestly.** When it is true, name the structural property of a problem class and then the anchor's setting as its primary instance; downstream steps inherit the class. If the failure is specific to one system, say "specific to <setting>; no broader class is claimed". Fake generality is an overclaim.
- **Gaps (1–4), two kinds.** *Additive*: an unmet need that no frontier paper achieves, phrased as the missing outcome, not as a mechanism or a location for the fix. *Subtractive*: an assumption every closest paper silently inherits, phrased as the unasked question ("none tests whether X is necessary"). Name the assumption and stop; never append the replacement you have in mind. Include at least one subtractive gap whenever the readings show a shared inherited assumption. Do not rank the kinds; generation picks the anchor gap.
- **Stakes (mattering test).** Every gap's `stakes` names who hits the failure and what it costs. Practitioner costs (wrong outputs, wasted compute, blocked deployment) and intellectual costs (results that do not transfer, published conclusions resting on an unexamined assumption, missing theory that blocks principled design) count equally. A gap for which neither cost can be written concretely is negative space in the corpus, not a gap. Drop it.
- **Gap refs** point to the signatures, cards or expectations that show the residue. A card whose `failure_modes` or `counterexamples` state the boundary is strong evidence; cite it.
- **User direction.** If the question names a solution shape, keep it out of the bottleneck and the gaps (this rule exists because a cure named at diagnosis gets built faithfully and yields an incremental idea). If it rules a shape out, a gap must not require that shape.

## Routing

`state: "do_not_generate"` with a non-empty `do_not_generate_reason` (gaps may be empty) when **any** of these holds. Otherwise `proceed`.

- **Too broad**: no concrete object or obstacle can be named from the question and brief.
- **No anchor**: no paper in the domain comes close enough to the obstacle to define a residue.
- **Too thin**: fewer than 5 readings truly relate to the question (the rest are keyword matches), so the bottleneck cannot be grounded.
- **Benchmark construction**: the question's deliverable is building a benchmark or dataset rather than a mechanism, analysis or theory that this pipeline can audit.

The reason names the trigger, the evidence that fired it, and what the user would have to add or change (a narrower object, a domain rebuild with other queries, a named anchor paper). Do not lower the bar to manufacture a bottleneck.

## Retry mode (`attempts/` present)

The earlier framing is being retired. Read each archived `audit.json`: `verdict_rationale`, `paper_threat` and `lessons`. Read the archived `phase1.json` bottleneck and anchor.

- Do **not** restate the retired bottleneck in new words. If candidates died by `paper_threat` (`subsumes` or `same_mechanism`), that ground is occupied. Diagnose a different failure axis, which usually means a different anchor and a different residue family.
- The threat papers mark occupied ground: the new bottleneck must not be one they already resolve.
- `do_not_generate` remains a legitimate and preferred outcome when the domain supports no second sharp bottleneck.
- Do not mention the earlier attempt in the output's prose.

## Never

- Cite a paper, result or limitation that is not in `D/` (no citations from memory as evidence), or describe content a reading did not cover.
- Propose a mechanism, a card to apply or a composition.
- Ask the user anything mid-run (intake happens at run init in `hitl`); infer, or route to `do_not_generate`.
