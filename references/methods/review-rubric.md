# Review rubric: claims, assumptions and discriminating evidence

Use these distinctions to explain a judgment, not to manufacture a total score. A score is optional when the user needs comparison; leave a dimension unknown rather than guessing. Record the evidence and scope that decide the judgment.

## Novelty

Judge relative to the literature actually searched, not a general sense of the field. Name the closest prior mechanism, including older work under different vocabulary.

Useful distinctions are: the mechanism is already published; known parts are assembled with no new interaction; a specific operation, transport step, causal link or guarantee differs; or retrieval coverage is insufficient to decide.

Novelty by relabeling is not a new contribution. Search the mechanism in plain words and compare premises, available information and guarantees. Similar topic labels do not prove equivalence, and different application nouns do not prove a new mechanism.

Do not interpret the absence of retrieved papers as confirmation that no prior work exists. Keep a concrete delta separate from confidence in search coverage.

## Correctness and support

Ask whether the mechanism can be true given its exact definitions and known evidence. Separate internal consistency, direct evidentiary support, plausible but untested steps, and empirical effectiveness.

Two claims in one hypothesis that cannot both hold are a defect in the current formulation, not merely an interesting open question. Identify the contradictory statements and their premises before proposing a repair.

An internally consistent mechanism can still fail empirically. A mechanism consistent with the literature is not thereby established. Even if every step has a supporting source, assembly into a new setting may remain untested.

Direct contrary evidence can refute a load-bearing claim in scope. A valid single counterexample suffices against a universal claim; finite success examples do not prove universality. For average-case claims, inspect sampling, comparison and uncertainty rather than treating one instance as a population estimate.

## Testability

Use [the shared falsification definition](falsification_reaudit.md) for all first reviews and revision checks.

A confirmatory test is not a discriminating test. “We would see X” carries little identification value if the leading alternative also predicts X. Explain what observation would separate them and what each result would mean.

The testability of an experiment and the truth of its target hypothesis are distinct. A deficient test requires a better plan or an honest limit, not an invented negative scientific result.

## Feasibility

Judge the discriminating experiment against actual timescale, data/model access, compute, reagents, samples, budget and existing tooling. Missing resource information remains unknown; do not assume an unlimited lab.

A cheap proxy is useful only with an argument that it preserves the relevant prediction difference. If a method change is necessary, classify it as H evolution; if only the testing route changes while H stays fixed, classify it as T redesign.

## Findings, not one overloaded verdict

Use the active record API judgments for individual claims. Explain the underlying category in rationale:

- Direct contradiction or inconsistency: specify the affected claim and evidence.
- Prior coverage: identify the published mechanism and what the candidate adds or does not add.
- Better-supported alternative: name it and the observations it explains more economically or directly.
- Missing required step: state the operation or premise that remains undefined.
- Unresolved but plausible: say what is unknown and which test could settle it.

The original Co-Scientist rubric used `missing_piece` for an absent required step, while its observation prompt used the same term for a positive new explanation. Do not migrate that ambiguity. Use explicit prose such as “required step missing” or “candidate explanation of observation”; neither becomes an API enum.

A review being complete is not scientific approval. A hypothesis can receive a complete review containing a decisive contradiction. An investment decision to continue may still be rational for a salvageable subproblem, and must remain a separate decision.

## Assumption decomposition

List every load-bearing assumption as a single testable claim. “The bacterium colonizes the ileum” is a claim; “the mechanism works” is not a useful decomposition.

Do not restate the full hypothesis as an assumption. Distinguish definitions, environmental premises, causal assertions, and empirical generalization. A user constraint is not a model prediction to be casually revised.

For each assumption, state plausible, uncertain or implausible as a provisional analytical description and provide a source or a reasoned limitation. If the literature is silent, write silent/uncertain rather than calling the assumption supported.

Name the weakest assumption: whose failure collapses the proposed explanation or practical benefit fastest? State what observation would decide it and whether that observation is available under current constraints.

One directly contradicted load-bearing assumption may refute the affected mechanism claim. Preserve useful instruments, controls, subclaims or measurements that do not depend on it; “fatal for this explanation” need not mean “all work is worthless.”

## Worked example

A hypothesis says a bacterial enzyme releases a metabolite that antagonizes a nuclear receptor in the ileum and causes inflammation.

A weak review calls the mechanism interesting and gives all dimensions a middling-to-high score. A useful review checks the actual receptor direction and finds a source showing agonism, not antagonism, in the relevant system. It also checks whether the proposed concentration is compatible with the stated absorption behavior.

The reviewer distinguishes the source-backed direction contradiction from an uncomputed concentration concern. It asks whether the anticipated outcome was already published and whether the proposed experiment merely reconfirms it.

The receptor claim receives the appropriate scoped finding. The transport step may still be a distinct research question; if retained, it becomes an explicit revised candidate rather than quietly inheriting the old explanation's appeal.

## Provenance and replacements

Adapted from [Co-Scientist review rubric](../../vendor/co-scientist/plugin/skills/reviewing-hypotheses/reference/rubric.md). Preserved near-original distinctions about actual literature, internal consistency, discriminating tests, realistic feasibility, assumption decomposition and salvage.

Replaced forced scalar anchors and a single ordered verdict with evidence-scoped findings. Resolved `missing_piece` ambiguity; added explicit universal-versus-empirical evidence logic and Q/H/T classification. Testability delegates to one active shared definition.
