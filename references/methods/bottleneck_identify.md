# Bottleneck identification — adapted detailed method

中文入口：[research-diagnose](../../skills/research-diagnose/SKILL.md)。按 [共同合同](../contracts/research-contract.md) 和 [record-api](../../docs/record-api.md) 记录；下列 JSON 风格字段只是正文提纲，不是 API 参数。

来源：`vendor/research-studio/ResearchStudio-Idea/skills/idea_spark/references/system-prompts/bottleneck_identify.txt`（原文 220 行）。保留诊断、谱系、残差、规则固定、stakes 与范围推理；改写旧宿主门禁和路由。模型回忆只能提名，代码与运行事实可以推翻诊断。用户硬约束若需改变，交具体冲突供用户决定；待核解释可依据证据自行修订并留版本。

Diagnosis reads user intent, papers, code and observations, and writes an evidence-grounded bottleneck statement plus the next action. Selection of ideation patterns happens at mechanism selection, not here.

OPTIONAL REDIAGNOSIS INPUT: when a prior problem framing was challenged, read its version, the exact claims refuted, the original materials and surviving observations. Paper-pointed subsumption is one trigger; code facts, valid counterexamples and new constraints are others. Preserve why a framing was retired. Treat the relevant findings as NEGATIVE ANCHORS, not an instruction to discard all earlier work:
- If exact subsumption retired a claim, a new label does not make it novel. Check what changed in conditions, evidence or mechanism before reopening it. A new problem requires a new problem version, not just renamed prose.
- The killer papers define occupied ground: the new bottleneck must not be one they already resolve.
- Stopping this line remains legitimate if no distinct grounded problem or useful next investigation remains. Preserve observations and uncertainty; do not lower the bar to manufacture another gap.

When prior-art regression or shared assumptions matter, reconstruct the METHOD LINEAGE the bottleneck sits on. A new observation can be investigated without inventing a long genealogy.
A recent search can miss classical ancestors and collateral methods; a code observation can also expose a condition the retrieved papers never addressed. The coverage report decides where more history is needed.
Reconstructing the lineage moves this catch to the SOURCE: the regressive
cures become visible as existing tree nodes before any idea is generated,
instead of being caught and regenerated downstream.

Fuse two knowledge sources, each used where it is strong:
- **Retrieved papers** (grounded): the RECENT frontier — the leaves of the
  tree. Read their actual content and scope; being retrieved is not proof.
- **Your own internal knowledge** (parametric): the ESTABLISHED ancestry —
  the interior and root nodes that the current search may have missed. Use memory to nominate methods for verification. Build the
  ancestry only as far as the question needs. Walk backward until the root move relevant to the question becomes clear instead of stopping one paper behind the current frontier. Historical intervals can help expose missing coverage, but no era needs a placeholder node. The just-outside-the-search interval can be especially uncertain: name that coverage gap rather than assuming memory is complete. Deep textbook families are useful recognition cues but still need verification when a particular attribution or exact guarantee determines novelty. Record provenance and uncertainty for every node; age does not establish correctness. Verify a remembered method before using it to reject novelty.
  Direct-ancestry alone is not enough: a future cure often attacks a leaf's
  residual_problem through a mechanism that is NOT on that leaf's parent chain,
  so a tree built only by walking parents backward leaves that cure's position
  invisible and the regression undetected. So after the ancestry walk, for each
  frontier leaf's residual_problem, also enumerate the older method families
  that attacked the SAME residual through a DIFFERENT mechanism and add their
  oldest representatives as collateral nodes (is_collateral true, parent null,
  parametric, awareness-only). To enumerate them by recognition rather than free
  recall, derive relevant mechanism families that have historically
  attacked this bottleneck's residual — the families are specific to this
  bottleneck, not a fixed list — then check each family for a representative
  outside the retrieval window. A family with no such representative is simply
  declared absent; do NOT invent one to fill it.

Build `method_lineage` (below): root = the base formulation, interior =
parametric ancestors, leaves = the retrieved recent frontier; each node carries
the move it made over its parent and the residual_problem it left open. The
tree does two jobs at once: (a) it surfaces the unquestioned assumption every
leaf inherits from a shared ancestor — the old "what do all the closest_adjacent
papers silently share" question, now answered structurally by reading which
interior node every leaf descends from; and (b) it makes the POSITION of any
candidate cure visible, so a cure that would land on an existing interior /
ancestral node is recognized as a regression up front. A gap may arise from a frontier residual, a changed condition, a code/data observation, or a counterexample. Explain what prior methods already resolve under matching conditions; do not reject an observation merely because it is not a recent paper leaf.

Inputs (read actual project materials; there is no prescribed file layout):
- The user's original question, hard constraints, preferences and proposed solution shapes.
- The current project/problem version and material refs `{id, version}`.
- Relevant retrieved papers with raw source, read sections, coverage and failure status.
- Full-text evidence for candidate comparisons: read this BEFORE writing bottleneck or closest_adjacent — abstracts alone systematically underestimate residue because limitations / scope boundaries / implementation details that determine "what this paper actually did not do" live in method sections, not abstracts. For each comparison, read intro (positioning + contribution scope) and method (implementation specifics that disambiguate what was claimed vs what was actually built). Sources with failed full-text access only have abstract — treat their residue claims with appropriate uncertainty. Cheaper access path: read a material index first, then open only the papers you actually need instead of loading a whole text blob. Keep the identity and version of the canonical material alongside derived extracts; if a source is refreshed, evaluate which extracted claims need rereading.
- Code revision, entry points, actual configuration, sample data and available run evidence.
- Existing diagnoses, objections and decisions whose premises bear on this question.
Read full methods or source code before relying on a precise residual. Missing full text does not imply no limitation and does not imply a verified limitation: label the uncertainty. When code and paper differ, determine which is the actual system under study.

Resolve resources from explicit user limits and checked environment facts. Unknown budget stays unknown. Ask only a critical unresolved question when it controls the next action; continue independent authorized investigation. Do not silently reinterpret a hard requirement as an optional preference.

Content outline (these are method notes inside record bodies, not the record API schema):

{
  "intake": {
    "source_notes": "<state which fields came from the user, environment inspection, retrieved sources or inference; unknown is a legitimate value>",
    "domain": "...", "venue": "...", "time": "...", "data": [...], "compute": "...",
    "expertise": "...", "preference": "theory|empirical|both", "baseline": "...",
    "user_direction": "<VERBATIM span from the user's question naming the SOLUTION SHAPE they want ('unify the four modalities into one space'), or n_a. Copy their words — do not paraphrase, do not repair, do not generalize. Classify whether this is a hard constraint or a proposed hypothesis. Hard constraints remain binding; a proposed hypothesis may be revised with reasons and a versioned record.>",
    "excluded_direction": "<VERBATIM span naming a solution shape the user ruled OUT ('not retrieval-based'), or n_a. Same copying rule.>",
    "limitation": "...", "contribution_type": "theory|method|benchmark|system|application|scaling|empirical_reveal",
    "_inferred_fields": ["<field names that were inferred from context, not stated by user>"]
  },

  "bottleneck_statement": "<one paragraph stitching the user's stated limitation with the literature evidence into a single concrete gap. Must cite the materials that actually establish the failure; there is no minimum paper count. NOT a category label like 'optimization bottleneck' or 'representation problem' — write a specific structural gap. State the FAILURE (what breaks, under what condition, and why the current machinery cannot produce the needed quantity), NOT the absence of a specific cure: 'no method maintains a per-prompt signal that survives across visits' smuggles one mechanism (a persistent baseline) into the diagnosis and forces every downstream gap and idea to be that one mechanism. Write it so that several distinct cures could each address it — e.g. 'once a group saturates, no within-group statistic can produce a non-zero advantage numerator, so the gradient vanishes' admits persistence, resampling, regrouping, off-policy correction, etc.>",

  "closest_adjacent": [
    {
      "paper_id": "<paper_id from lit_table>",
      "is_anchor": "<identify the closest meaningful comparison; multiple anchors may be needed for different conditions, and no invented anchor is required for a new observation>",
      "summary_and_residue": "<2 sentences: what the move that paper made; what their method does NOT close — the residue this candidate could pick up>"
    }
  ],

  "open_questions": [
    "<Entries grounded in a specific unsolved condition; check whether older methods solve the same condition. Code/data observations and changed regimes are legitimate gap origins. Mix of two kinds: (additive) an unmet NEED no retrieved leaf achieves — phrased as the outcome that is missing, NOT as a prescribed mechanism or location. 'No leaf makes the advantage survive a zero-variance group' is a need; 'no paper fixes it purely in the baseline term without touching the sampler' prescribes the cure and forbids alternatives — that spends the novelty here and forces an incremental downstream idea, so do not write gaps that way. AND (subtractive) — the assumption EVERY leaf silently inherits from a shared ancestor node (read it straight off the tree: the interior node all current leaves descend from), phrased as the unasked question, e.g. 'no retrieved paper tests whether <shared component X> is necessary rather than assumed'. Name the assumption being questioned and STOP there — do NOT append the specific replacement you have in mind ('...whether a baseline that persists across visits is what breaks it' has both chosen the cure AND landed on an existing ancestral node; '...whether the baseline must be computed from the current group at all' leaves the cure open). selection and construction choose the cure; diagnosis only opens the question. Include at least one subtractive entry whenever the tree shows a shared inherited assumption, because mechanism selection only sees gaps listed here. EVERY entry must END with an inline stakes clause: ' — stakes: <who hits this failure and what it costs. Practitioner costs (wrong outputs, wasted compute, blocked deployment) and intellectual costs (results that do not transfer, a field-wide assumption that would invalidate published conclusions, a missing theory that blocks principled design) are COEQUAL — a foundational gap whose cost is that the field's conclusions rest on an unexamined assumption is a full-strength gap even with no deployment scenario>'. A gap for which NEITHER cost type can be concretely written is retrieval negative-space, not a gap — do not emit it (rule 11).>"
  ],

  "method_lineage": {
    "line": "<one line: the method line this bottleneck sits on — e.g. 'per-prompt advantage/baseline estimation for policy-gradient RL'>",
    "nodes": [
      {
        "node_id": "<short id, e.g. 'n0', 'n1'>",
        "method": "<method or move name — e.g. 'REINFORCE with running-average baseline', 'value/critic baseline', 'GRPO (group-relative, no critic)', 'KRPO (Kalman-filter baseline)'>",
        "move": "<one line: the move this node made OVER its parent>",
        "parent": "<node_id of the parent, or null for the root>",
        "provenance": "retrieved:<paper_id> | parametric",
        "historical_context": "<optional date/era, verified or uncertain>",
        "confidence": "<high | medium | low — confidence follows what was actually read and checked, not the age or retrieval status>",
        "residual_problem": "<one line: what this node left open. For a frontier leaf this is a candidate gap site; for an interior node it is what a DESCENDANT already addressed.>",
        "is_frontier_leaf": "<true for a current frontier node; other grounded observations may also be gap sites>",
        "is_collateral": "<true for a sideline node attached by shared residual_problem rather than by descent — an older method FAMILY that attacked the same residual through a DIFFERENT mechanism; parent may be null, provenance records actual support; not automatically a shared ancestor. Default false / omit for ancestry-chain and frontier nodes.>"
      }
    ],
    "notes": "<(1) PROVENANCE DISCIPLINE: nodes marked `retrieved:<paper_id>` are grounded and citable as prior art; nodes marked `parametric` are reconstructed from your internal knowledge and are AWARENESS-ONLY — they prevent regression but are NOT cited as prior art and carry no hard novelty claim (their dates/attributions may be approximate). (2) ANTI-FABRICATION: a shallow lineage is legitimate when the line is genuinely young — emit only the nodes you actually know; do NOT invent ancestors to pad the tree. (3) ANTI-OVER-CONSERVATISM: to flag a candidate cure as 'an existing node' (a regression), you MUST name the concrete prior method (name + its move); if you cannot name a specific one, do NOT flag it — a vague 'feels done before' must never suppress a gap. The tree degrades gracefully: deep on old lines (where the recent-only window is most blind), shallow on young lines (where retrieval already covers the frontier). (4) COLLATERAL NODES: a node with is_collateral true is a sideline attached by shared residual_problem, not a member of the leaves' descent chain — it exists only to make a cure's position visible for regression (job b). It is not automatically a shared ancestor. A gap at changed conditions can be examined here as elsewhere; check the actual relationship.>"
  },

  "domain_pattern_distribution": {
    "optional": "<only when an existing corpus actually has useful tags; never tag papers just to fill this field>",
    "n_total": "<total distinct sources in the declared corpus>",
    "n_on_topic": "<distinct on-topic sources: exclude off-core rows and collapse duplicates retrieved via multiple sources; make the denominator explicit>",
    "patterns": [
      {"pattern_id": "<source pattern label>", "count": "<distinct sources using the operation>", "share": "<count / n_on_topic>"}
    ],
    "notes": "<the most-used operation in this declared corpus and what limitations those sources share, or no shared limitation visible. Primary and secondary labels both count, so counts may sum to more than n_on_topic. This is optional descriptive context, not a novelty score, generation signal, admission gate, saturation threshold or reason to avoid a mechanism.>"
  },

  "next_action": "construct | investigate | reframe | decision | blocked",

  "missing_conditions": [   // populated when a missing condition prevents this action
    {
      "condition": "<the missing or contradicted condition>",
      "next_investigation": "<bounded action or user decision needed>",
      "match_evidence": "<why this trigger fires for this query>"
    }
  ],

  "remedial_steps": [   // populated when a missing condition prevents this action
    "<specific source read, code check, observation or user clarification that would change the next action>"
  ]
}

Routing follows the actual uncertainty, not a binary pipeline gate:
- A concrete, worthwhile and sufficiently grounded problem can proceed to ideation or construction.
- Too broad / no anchor: narrow the observed target through Seed and code/data inspection.
- Insufficient search or unreachable sources: request a targeted retrieval with explicit coverage limits.
- Few papers but a reproducible new observation: preserve the observation and investigate alternative explanations.
- Resources missing: distinguish a discriminating cheaper path from a proxy that changes the question; record park conditions if needed.
- Already solved under the same conditions: revise the novelty claim or hand back an application/replication task.
- No remaining valid problem or no new discriminating action: stop this loop with reasons and retained evidence.

Hard rules:

1. `bottleneck_statement` Must cite the materials that actually establish the failure; there is no minimum paper count. Unverified premises stay explicitly uncertain; a code or data observation need not be recast as a literature claim.

2. `closest_adjacent[]` contains the actually relevant comparisons, with material refs. A missing closest source is an uncertainty, not permission to invent an entry. The residue half of `summary_and_residue` MUST name a *specific* limit (e.g., "treats preconditioning as a design choice rather than as a derived consequence"), not a generic "limited evaluation" or "could be extended".

3. `bottleneck_statement` is NOT a category label. If you find yourself writing "the bottleneck is assumption-related" or "this is a representation problem", rewrite as a concrete structural statement.

4. Keep problem diagnosis separate from solution commitment. A solution lead may be noted as a lead, but must not define the failure by its own absence.

5. Hand a grounded question to research-ideate or research-construct when appropriate; use method patterns only when they help explain an actual operation.

6. **The lineage checks prior solutions; it does not restrict where problems originate.** Additive and subtractive questions compete on their evidence and stakes. A remembered ancestor is a verification lead, not an automatic veto. If it solves the same problem under the same conditions, name the exact overlap; otherwise retain the regime difference. Only the affected premise or framing is reopened.

8. **Anchor content sufficiency.** Before finalizing a residual, read the closest method and, where available, the relevant implementation. If only an abstract is accessible, retain an explicit abstract-level uncertainty. A fetch-success flag does not establish that equations, rules and scope were actually present. Request targeted missing sections through research-retrieve, without depending on old cache paths or shell entry points.

   **8b. Rule-pinning ledger — MANDATORY whenever the diagnosis treats a paper as the SYSTEM UNDER STUDY** (i.e. downstream phases will simulate, replay, or check faithfulness against its procedure, rather than merely citing its result). Fetch success is not the same as fetch sufficiency: `source_used` records that a path returned text, not that the text contains the rules. Emit an `anchor_rule_pinning` object with two explicit lists:

       "anchor_rule_pinning": {
         "paper_id": "<the subject>",
         "method_chars": <int, from the full-text materials>,
         "pinned": ["<rule fixed VERBATIM by the fulltext, one per entry>", ...],
         "unpinned": ["<rule the fulltext does NOT fix — free parameter>", ...],
         "sufficient_for_faithful_generator": true | false,
         "why": "<if false, what a downstream generator would have to guess>"
       }

   Cover at minimum: the accept/reject or selection predicate, what it is computed over, the population/batch sizes, the update rule, the iteration count, and tie-breaking. Put a rule in `pinned` ONLY if you can quote the sentence that fixes it.

   **Historical motivation reported by the source project; not reverified here.** A subject whose method section extracted to 2,528 chars was reported as grounded (`html_arxiv`) and the top-up no-opped; the body ended mid-sentence, immediately before the update equation. 8 of 16 needed rules were unpinnable, and no phase said so — so the candidate's simulator, the 2.3 gate's faithfulness re-build, and the audit all reasoned about a procedure none of them could check against the paper. The transferable lesson is to persist missing rules instead of relying on a fetch-success marker.

   When `unpinned` is non-empty, ALSO write a matching hard constraint into the output for construction: identify which claims depend on each unpinned parameter, and propose a justified sensitivity check; a single chosen setting supports only that setting. A single-point claim on a free parameter is indistinguishable from a claim manufactured by choosing that parameter — so make the uncertainty and sensitivity check explicit.

10. **Problem-level, not solution-level (applies to `bottleneck_statement` AND every `open_questions` entry).** Diagnose the failure; let construction invent the cure. Litmus test: if one specific named mechanism/representation/operator would "close" the gap by definition, the gap is solution-shaped — rewrite it as the failure that mechanism would address, phrased so that several distinct mechanisms could each be a candidate. Two reasons this is load-bearing, not stylistic: (a) novelty named at diagnosis time cannot be improved on downstream — selection and construction will faithfully build the one cure you named, so an incremental cure named here yields an incremental idea no matter how good the rest of the pipeline is; (b) a narrow literature window cannot tell you whether the mechanism you smuggled into the gap is in fact a decades-old classical move (a running-average / value baseline, a moving target network, a curriculum, etc.) that the recent papers have already superseded — a solution-shaped gap therefore silently re-proposes superseded prior art and an equally narrow collision check will not catch it. Keeping the gap at the problem level defers the cure to construction where multiple candidates compete, instead of locking in the first (usually most conservative) one.

11. **The mattering test (applies to every `open_questions` entry).** Being unaddressed in the inspected retrieval window is NOT evidence a gap matters — it may be unaddressed because it is a non-problem. Every gap must therefore carry the inline stakes clause defined in the field spec, and the litmus is concrete: if you can name NEITHER a practitioner scenario NOR an intellectual cost (invalid conclusions, non-transferring results, blocked principled design) where this failure costs something specific, the entry is retrieval negative-space and must not be emitted. Downstream consequence if you skip this: construction will faithfully build a mechanism around the non-problem and every later gate will validate internal consistency against it — a domain expert then reads the final card as attacking a problem nobody has.

12. **Structural-property framing (class over instance).** Write `bottleneck_statement` and each gap as a STRUCTURAL PROPERTY of a problem class when one honestly exists — name the property (e.g. "any verification schedule that adapts to observed acceptances censors its own future observations"), then name the anchor's setting as the PRIMARY INSTANCE where the property bites. This costs nothing when true and buys transfer: downstream phases inherit the framing, so the final card claims the class, not one system. The honesty constraint is absolute: if the failure genuinely is specific to one system's quirk, say so plainly ("this gap is specific to <setting>; no broader class is claimed") — manufacturing fake generality is itself an overclaim and reads worse to an expert than an honest class-of-one.
