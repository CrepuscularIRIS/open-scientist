# I7 — Decision gate: pursue, park or kill

Role: `gate`. You close the run with one decision and the evidence for it. This step is adapted from Research Companion's Decide phase and the strategist's triage (Mode 1) and opportunity-cost analysis (Mode 4). The difference is that the evidence is the run's own files, not a conversation.

## Inputs

- `idea_card.json`: the claim, feasibility, `kill_switch`, `expectation_coverage`, `reviewer_concerns` and `domain_landscape`.
- `audit.json`: the verdict and its rationale, the hard-floor checks, blocking dispositions, the seven critic scores, and `strategy` (timing, scoop risk).
- `run.json`: the question the run was asked, plus the pinned `{domain, version}`.

## Who decides

- **`auto` / `web`.** The model decides from the evidence on disk and writes `decided_by: "model"`.
- **`hitl`.** The navigator marks this step as a `gate`, and the host does not decide. The host shows the human a short evidence summary (≤ 10 lines):
  - the audit verdict and critic scores;
  - expectation rows at `gap` or `partial`;
  - scoop risk and the strongest collision threat;
  - the feasibility verdict and its binding constraint;
  - the `kill_switch`.

  The host then presents the three options, each with a one-line consequence. It may label one as a recommendation. It records the human's choice and reasons with `decided_by: "human"`. If the human picks park without saying what would change, the host proposes concrete `revisit_conditions` and confirms them with the human. Never write `decided_by: "human"` without the human's answer.

## How to decide

Read the hard evidence first and judgment second.

1. **Hard limits.** If `audit.verdict` is `abandon`, a blocking finding is upheld, or `paper_threat.kind` is `subsumes` or `same_mechanism`, the decision is never `pursue`.
2. **Triage table** (from the strategist's Mode 1):

| Signal | pursue | park | kill |
|---|---|---|---|
| Audit | `advance`; concerns have responses | `revise` items wait on something external | `abandon`, or the core premise is refuted |
| Competition | `scoop_risk` low or medium, with a substantive delta | threat is near but unpublished, or the timing is wrong (`recent_share` saturated or too early) | subsumed, or same mechanism |
| Expectations | every required row is `met` or `partial` | a `gap` needs a resource that does not exist yet | a `gap` the idea cannot close by its nature |
| Feasibility | `feasible` or `tight`, with a named binding cost | the first decisive test exceeds the user's `resources.authorized_limit`, or a missing artifact | infeasible in principle |
| Conclusion-first | `nugget_sentence` states a compelling, specific takeaway | — | the takeaway is hollow or generic even if every test succeeds |

3. **Opportunity cost** (from the strategist's Mode 4).
   - Weigh the expected value, accounting for risk, against `resources.estimate`. `pursue` never authorizes spend beyond `resources.authorized_limit`; when it is `not specified`, the first step names what the first decisive test costs, for the person to approve.
   - Prefer `pursue` when the falsification experiment is a cheap, decisive test of the riskiest premise, even when uncertainty is high. Failing fast is cheap.
   - Ignore sunk effort: the pipeline already spent it.
   - Flag the excitement bias. A fresh idea feels stronger than its evidence. Score the evidence, not the feeling.
4. **Factual disagreement is not averaged away.** If the card and the audit disagree, for example on feasibility or timing, say which file says what. Then decide on the more conservative reading, or set `park` with the disagreement as the revisit condition.

## Output: `decision.json`

```json
{"decision": "pursue", "rationale": "...", "revisit_conditions": "...", "decided_by": "model"}
```

- **`rationale`** is 3–8 sentences. It names the evidence it rests on: the audit verdict and the scores that drove it, expectation ids (`E03`), scoop risk and the threat's `arxiv:` id, the feasibility verdict, and the `kill_switch`. What it adds for each decision:
  - **pursue**: the first step, which is the single riskiest assumption to test, specific and runnable (usually the falsification experiment on the load-bearing variable). Add the biggest remaining risk.
  - **park** or **kill**: end with `Lesson: <one sentence the domain should learn from this run>`, written as a reusable statement with refs. Examples: a card failure mode that fired in this setting (`K04-...`), a mechanism subsumed by `arxiv:...`, an expectation (`E02`) this family of ideas cannot meet, or a cross-domain map that broke. The navigator records lessons separately; you only state the lesson.
  - **kill**: also say what is worth salvaging, if anything (a sub-idea, a measurement, a negative result).
- **`revisit_conditions`** must be **concrete and checkable**:
  - **park**: required. Give an observable trigger: a named dataset or tool release, a budget at or above a stated level, the threat paper's results, an expectation becoming satisfiable. "If circumstances change" is not a condition.
  - **pursue**: the `kill_switch` condition, plus any scoop trigger that would reopen the decision.
  - **kill**: what evidence would justify reconsidering, or `none`.
- **`decided_by`**: `model` or `human`, as described above.

## Never

- Pursue against the hard limits, or downplay a concern the card lists.
- Invent evidence that is not on disk, or cite papers from memory.
- Decide for the human in `hitl`.
