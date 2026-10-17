# Relevance, use and question-directed reading

Adapted from RS's
[relevance partition rubric](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/relevance-partition-rubric.md),
[Paper Search relevance filter](../../vendor/research-studio/ResearchStudio-Idea/skills/paper_search/SKILL.md),
and [Scoop Check, steps 3–5](../../vendor/research-studio/ResearchStudio-Idea/skills/scoop_check/SKILL.md).
Source attribution and the archived texts are retained; this document changes
their active filtering and reading contract.

## Preserve the strongest original filtering rule

Lexical scores rank; they do not understand. They admit generic-word noise and
miss synonym-only matches. Judge against the **USER'S ORIGINAL QUESTION**, not
only the rephrased query. Base title/abstract triage on text actually read; a
paper whose abstract was not read cannot be declared irrelevant from an absent
keyword. Preserve “the abstract does not say” as uncertainty rather than resolving it.

A wrong exclusion is a recall loss that downstream diagnosis may never notice.
When unsure, retain the item as an unresolved lead. Do not remove an item simply
for being older, less novel, a baseline, outside the familiar taxonomy or from
another field. The active reading set can be small while raw provenance remains.

## Separate topic proximity from use

The archived core/adjacent/off_topic partition makes same-field mechanism papers
eligible for full text while adjacent baselines and outside-taxonomy papers may
be excluded. That policy is unsuitable for a reusable research suite.

For each selected source, record a short use statement:

| Use | What to look for | Limits |
|---|---|---|
| Same-setting baseline | Inputs, method, assumptions, actual results | Similar task does not establish same mechanism |
| Cross-field mechanism | Operation, invariant, information requirements | Transfer remains a separate hypothesis |
| Counterexample | Exact claim scope, legal instance and result | A different setting may not refute the target claim |
| Measurement/diagnostic | Confound, protocol, matched control | An evaluation paper may be more urgent than a method paper |
| Survey navigation | Vocabulary and references to originals | Cite original evidence for transferred factual claims |
| Source identity | Title, author, ID, version, canonical location | Finding a source is not checking its scientific claim |

“Off topic” is justified only when no useful relation to the current question can
be explained. Retain its raw reference and reason; a later question can reopen it.
No minimum number of retained papers is required to proceed. Scarce coverage is
a limitation to report, not a reason to invent weakly relevant material.

## Choose deep reads by the question they can settle

Select the papers most likely to overturn or inform the current claim, not those
whose titles look closest. A same-mechanism paper in another domain can matter
more than many recent papers in the target domain. An ambiguous abstract can be
a reason to read the method, not a reason to mark a mismatch.

Read the source sections that determine the answer:

- Contributions/introduction for framing and stated novelty.
- Algorithm/equations/code for the actual operation and available information.
- Theorem statement/proof/limitations for conditions and guarantees.
- Experiments/appendix/configuration for controls, scale, evaluation and data splits.
- Related work for a bounded next citation when a named predecessor matters.

Do not force a fixed number of deep reads or passages. Stop when the current
comparison has decisive passages and its unresolved conditions are explicit.
If the relevant content is very long, record the partial scope actually inspected.

## Full-text verification is not abstract summarization

Retain the Scoop Check requirement: two papers that describe the same mechanism
with different variable names must come out as a match, and two that share
vocabulary but differ in premises, objective, available information or guarantees
must come out as a difference. Name which it is, and cite the passage that decides it.

A compact read record contains:

- Exact source identity/version and location actually opened.
- Task inputs/outputs, operation, and key condition relevant to this question.
- Short actual excerpt or precise page/section/line, with explanation.
- What the excerpt supports, contradicts or leaves unresolved.
- Whether target code/data satisfy the source conditions, or that this is untested.

Use an existing local PDF/text or an accessible original HTML page. Reading a
connector abstract or another model's summary is not reading the method. A PDF
path is only a locator until opened. Do not copy entire local collections into
project records; store source pointers and the short evidence needed for judgment.

When full text is unavailable, use accessible abstracts or original previews if
useful, explicitly name the surface read and limit the resulting claim. Distinguish
unreachable from not_found; neither proves the relevant work does not exist.

## Identity, support, applicability

1. Resolve source identity from a canonical page/file and consistent metadata.
2. Check whether the original content supports the exact claim in the stated
   direction, system and strength; partial support is not full support.
3. Check the target mapping separately. A source guarantee can be correctly cited
   while its assumptions fail in the target setting.

Shared records store source snippets as material and per-claim judgments as
assessment findings. They have no global “verified paper” switch.

## Changes from the archived source

Removed same-field-only eligibility, taxonomy-based full-text exclusion,
method-before-diagnostic ranking and automatic exclusion of all surveys.
Kept conservative triage, abstract/full-text distinction, closest-passage evidence,
explicit assumptions, graceful access fallback and bounded reading.
