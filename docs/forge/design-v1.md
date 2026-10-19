# Research Forge — design

2026-10-18. A Claude Code plugin (and Mod) that merges ResearchStudio IdeaSpark, Research Companion and Co-Scientist into one general, domain-agnostic idea pipeline. Working name; it is meant to be merged into Open Scientist once stable.

## The one idea

All three source systems keep their knowledge as **static assets built once**: RS's 15+31 pattern cards, anti-pattern statistics and collision lexicon (1,947 papers, offline); Companion's generic 7-dimension rubric; Co-Scientist's fixed review criteria and Elo. Research Forge keeps their **procedures** and makes their **knowledge** a per-domain, versioned, source-traceable asset that is built from the domain's own materials and updated when evidence arrives.

## Three layers

```text
L1 Domain assets      .forge/domains/<slug>/v<N>/   (built by the domain pipeline, frozen per version)
   brief · queries · corpus · triage · readings+signatures · clusters · cards ·
   expectations · baselines · lexicon · crossmap · timeline · antipatterns · lessons
        │ read by                                     ▲ updated by
        ▼                                             │
L2 Idea pipeline      .forge/runs/<slug>/  (run.json pins domain version, mode, user's budget cap)
   bottleneck (RS P1) → select+generate (RS P2, Companion diverge, Co generation; cards optional)
   → citation gate → coherence gate (RS 2.3) → collision (RS 3.1, domain lexicon)
   → audit (RS 3.2 checks + expectations + Companion critic + strategist; deterministic hard floor)
   → revise → promote → collision + audit round 2 (advance/abandon only) | information-gain retry
   → idea card (RS P4, sections required by domain expectations) → decision gate
        │                                             │
        ▼                                             │
L3 Learning           lessons.jsonl, card revisions, routing statistics, backtest
```

## Dynamic assets (what used to be static)

| Asset | Replaces | Built from | Update trigger |
|---|---|---|---|
| `cards/` pattern cards (success conditions, failure modes, counterexamples) | RS 15+31 cards | signatures → suggested clusters → merge | new readings; counterexample from a run |
| `antipatterns.json` | RS `anti-patterns.md` (p_O stats) | outcome labels when present (OpenReview export, tiers), else qualitative from readings | new labels; lessons |
| `expectations.json` (what reviewers in this field demand) | Companion 7 dims, RS rubric | reviews when present; paper limitations and baselines sections | new labels/readings |
| `baselines.json` (standard baselines, datasets, metrics) | — | readings | new readings |
| `lexicon.json` (signature/alias terms, collision windows) | RS fixed 10/48-month windows | clusters + timeline | new corpus snapshot |
| `crossmap.json` (source→target object/operation/condition maps) | Companion brainstormer improvisation | cross_domain lane readings | run outcomes |
| `timeline.json` (per-cluster growth and saturation) | Companion/strategist timing guesses | corpus dates | new snapshot |
| `lessons.jsonl` | Co-Scientist meta-review (per run, lost after) | audit abandons, failed tests, decisions | every run |

Every asset row cites its sources (paper id + snapshot, reading id, run id). A domain version is frozen by `forge domain freeze`, which hashes every asset; idea runs pin `{domain, version}`.

## Roles and run modes

One plugin, three modes, selected by `userConfig.mode` (`auto` | `web` | `hitl`); `web` and `hitl` can combine (`web+hitl`). Each pipeline step declares a **role**; the mode decides who fills it.

| Role | auto | web | hitl |
|---|---|---|---|
| `design` (bottleneck, generation, revision) | local `forge-core` agent | ChatGPT Pro handoff | as auto/web |
| `review` (triage, profile, coherence, idea card) | local `forge-critic`, fresh context | coherence: Extra High handoff, new conversation; others local | as auto/web |
| `audit` (audit verdict) | local `forge-core` | Extra High handoff | as auto/web |
| `fast` (tagging, derivation, formatting) | local `forge-fast` | local | local |
| `operator` (scripts, records, files) | local | local | local |
| `gate` (run intake: question, budget cap, preferences; pursue/kill) | model decides from evidence | model decides | **human decides** |

The web is serial: a handoff step writes a packet and a receipt, and the step waits for the reply file. A handoff belongs to one step of one attempt and audit round (`handoff/<step>-a<N>-r<M>/`) and records the fingerprint of the run files it was built from; when those change, the packet is superseded rather than its reply ingested. A run stores its mode in `run.json`; changes go through `forge run set-mode` and are kept in `mode_history`. Provenance rows record the requested route and, for web handoffs, the route the person observed; neither is an authenticated identity.

## Navigator

Borrowed from RS: `forge next --project <dir> [--json]` reads the files on disk and prints exactly one step (`bash`, `llm`, `web_handoff`, `human_gate`, or `terminal`). It is read-only and idempotent; resuming is calling it again.

- **Acceptance by content.** Each LLM step lists its `deps`. The provenance command the host runs after the step stamps each output with its own hash and its deps' hashes. A dep that changes makes the output stale and its step returns (with a note naming the dep); an output edited after acceptance goes back through its step; an output never stamped gets an `accept` step that records it as unknown-origin. The provenance command stamps only while the navigator is at that step, takes the deps from the navigator, and never re-accepts a byte-identical output against changed deps. A promoted revision is pinned by hash for round 2. Deterministic outputs use content fingerprints. Dep identity is the path under `.forge/`, so moving a project keeps its stamps.
- **Commands re-check.** `run collide|promote|retry|render|close|finish` refuse unless the navigator's next step is exactly that command. DONE stores the hashes of the files the decision rests on and stops counting when any of them changes.
- **Bounded loops.** Abandoned attempts are capped (3, information-gain rule); a step whose output fails validation 5 times in one attempt and round stops the run as `stuck` for a person.

## Quality signal

No domain experts are assumed. Order of evidence: (1) time-split backtest — build L1 from materials before date T, generate, compare with outcomes after T; (2) LLM judges calibrated against that backtest; (3) the web's strongest model as final-selection judge; (4) human gates in `hitl`. Accept/reject measures "passes review", not empirical truth; real experiment outcomes are a later second channel. Labels are optional inputs, one row per submission event; anti-pattern flags compare within one venue-year stratum. Without labels every statistic says `no_outcome_labels`.

## Evidence rules

- **Discovery is not reading.** A paper in the corpus or the collision pool can be cited as context. Only a full-text reading (versioned arXiv URL, sections listed) can make a card a pattern (≥ 2 papers) or ground a premise. Abstract-only signatures are leads.
- **Expectations are questions, not a checklist.** Each has `applies_when` and evidence; its strength is checked against that evidence (`observed_in_reviews` needs review text in `reviews.jsonl`, `common_practice` needs ≥ 3 read papers). The audit answers each required one for the candidate: met, unmet, not applicable (with a reason), or challenged (with evidence). Only unmet blocks `advance`.
- **Cards are material.** A gap may be closed by zero, one or several cards; no count is rewarded.
- **The user's cap is not the model's estimate.** `resources.authorized_limit` is the user's budget from `run.json`, copied verbatim and never changed by a step. `resources.estimate` is the model's, and a `feasibility` revision may cut it with a cheaper test that keeps the variable, control, metric and direction.
- **Revisions name their fields.** Each audit target lists the field paths it allows (within its scope); the validator compares the revision with its base field by field. It checks what changed, not whether the change kept the science; the round-2 audit judges that.
- **Run observations are lessons.** A failure seen in a run is cited as `lesson:<key>`, never as a paper.

## Reuse map

| From | Kept | Dropped |
|---|---|---|
| ResearchStudio | `next` navigator, phase graph, citation/coherence gates, collision channels, 5 audits, information-gain retry, idea-card fields, seats | static 15+31 cards as required taxonomy, fixed windows, OpenReview in phase 0 |
| Research Companion | brainstormer cross-field moves, 7-dimension critic, strategist (comparative advantage, timing, scoop risk), conclusion-first test, blind panel | fixed model slots, generic rubric as final authority |
| Co-Scientist | generate→review→compare→evolve loop, meta-review feedback (now persistent lessons), only-cite-fetched-sources, clustering/dedup (ported, stdlib TF-IDF) | Elo tournament, resident supervisor, multi-provider LLM routing |
| Open Scientist | arXiv corpus collector and OpenReview connector (vendored), records backend (optional) | — |
