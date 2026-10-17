# Mechanism collision and a defensible delta

Adapted from [RS Scoop Check](../../vendor/research-studio/ResearchStudio-Idea/skills/scoop_check/SKILL.md)
and [RS collision vocabulary](../../vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/intent-recognition.md).
The original decomposition, full-body comparison and delta structure are retained.
The original overlap-count scoring and “empty means most novel” rule are removed.

## 1. Decompose what is actually claimed

Break the proposed novelty into four labelled dimensions:

- **Problem framing** — task definition, inputs, outputs, evaluation regime.
- **Core mechanism** — architecture, algorithm, proof technique or data construction.
- **Key insight** — why it should work and what prior approaches lack.
- **Application domain** — where it applies and how broadly.

These structure the comparison; they do not contribute equal votes to novelty.
Add the exact assumptions, available information, optimization objective and
claimed guarantee. A new domain by itself may not change the scientific mechanism.
Likewise, sharing a domain and task does not mean an algorithmic result is already covered.

## 2. Look for renamed ancestors, not just near-identical titles

Search the candidate's own terms and another community's names for the same
technical move. Retain recalled papers as nominated leads until resolved.
Include a concrete predecessor when its operation could subsume the candidate,
even if old. Use current work to check recent coverage, not to erase older results.
Read the nearest body passages before making an overlap judgment.

No source success count or keyword hit count proves coverage. Local empty,
arXiv 429, a missing index and an inaccessible paper are different observations.
Default retrieval uses the actual local+arXiv adapter; original-source lookup and
available citation chains can fill a specific gap within the remaining budget.

## 3. Compare mechanisms under matched conditions

For the proposed work and each meaningful predecessor, record:

| Dimension | Required comparison |
|---|---|
| Objects and operations | What enters, what transformation runs, what is produced |
| Available information | Labels, future data, oracle signals, training/inference access |
| Objective | What is optimized or estimated; whether it is the same quantity |
| Assumptions | Conditions needed by each statement, not just favorable examples |
| Guarantee | Theorem, empirical claim, heuristic or design intention |
| Evidence scope | Data, protocol, scale and code actually inspected/run |
| Residual difference | A concrete unmatched operation, premise or discriminating prediction |

An overlap argument should construct the correspondence or show a specific
special case. A difference argument should locate the unmatched step/condition
and explain why it matters. “Different variable names” and “different benchmark”
are not sufficient defenses by themselves.

If body reading changes the abstract-level impression, update the finding with
the deciding passage. Keep the earlier record for provenance rather than rewriting
the past. If the predecessor's decisive method is inaccessible, keep the overlap
question unresolved; do not use the polished abstract to close it.

## 4. State a delta without inventing a result

Retain the original structure:

> Unlike [closest prior work], which [does X under assumption Y], the proposed
> work [does X′ / drops Y / extends to Z], yielding [concrete measurable benefit].

Adapt the last slot to the actual evidence. Before the test, write “to test whether
[measurable benefit]” or “with the prediction that […]”. After a valid experiment,
state only the measured result under the recorded conditions. A hoped-for benefit
does not become fact because it appears in a delta sentence.

If no crisp delta can be written, identify the unresolved or subsumed part and
return a concrete refinement question. Do not manufacture rhetorical distance.
When no comparator was found, report that fact with the search boundaries;
there is no defensible “closest prior work” slot to fabricate.

## 5. Return the specific finding, not an artificial novelty level

Useful outputs are: evidence of subsumption; a supported narrower difference;
a possible difference awaiting a concrete check; or unresolved coverage/support.
Record the claim-level judgment and cited materials using the shared-record API.
Investment decisions such as park/kill remain separate from scientific findings.

Do not calculate `level = 5 - matching_axes`, vote across dimensions or declare
“most novel” when search returns zero. Do not use a shared field as proof of sameness
or a new field as proof of novelty. Do not rank candidates by how many words differ.

Finish with: the closest checked mechanism, its deciding passage/conditions,
the remaining difference or ambiguity, searched scope and failures, and the next
cheapest action that could change the judgment. Stop when that question is answered
or the budget is exhausted; resume only the missing part if new evidence arrives.
