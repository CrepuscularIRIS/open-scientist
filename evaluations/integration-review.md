# Integration review: records, retrieval and four research handoffs

Date: 2026-10-17. Reviewer: a separate implementation subagent that inherited the
conversation and earlier source audit. This was **not blind evaluation**. The
reviewer did not author records/search runtime or the active skills reviewed here;
the reviewer did author the asset archive/importer. Asset checks therefore remain
author-side integrity checks rather than independent evidence.

Scope: inspect records/search runtime and relevant contracts/skills, execute
targeted tests, reproduce defects, and replay B03/B06/B08/B10 on temporary local
fixtures. No original research repository was modified, no external model/API
or GPU experiment was run, and no old job was resumed. Reported outcomes below
are software/procedure observations, not improvements in scientific research.

## Findings and dispositions

| ID | Reproduced issue | Impact | Owner disposition and reviewer verification |
|---|---|---|---|
| IR-1 | Revising one human feedback ID from v1 to v2 removed unresolved v1 from `context`, despite no disposition for v1 | An unconsumed user constraint could disappear from the default handoff | Records owner changed unresolved selection to all versions and included them in the historical dependency closure. Reviewer reran the original reproduction: both v1/v2 unresolved; v1 present in historical inputs. Resolved. |
| IR-2 | An Atom entry containing a valid arXiv ID but no title, summary or publication date returned `ok` and complete coverage | Incomplete retrieval could be mistaken for a successfully processed source | Search owner added required metadata checks. Reviewer repeated malformed fixture: `unavailable`, `coverage.partial=true`. Resolved. |
| IR-3 | A nullable local title reached `deduplicate` and raised `AttributeError` on `.lower()` | One malformed metadata row could abort the whole report rather than preserve other source outcomes | Search owner made dedup tolerate absent title and local retrieval report missing usable title as an error. Reviewer repeated direct `None` fixture without exception; updated search suite passed. Resolved. |
| IR-4 | Active coherence T4 described downgrading a scientific guarantee as merely a wording repair | A stronger recorded H claim could be silently weakened in a view | Core owner clarified that changing a recorded guarantee requires a new H version preserving the old refutation; only alignment to an already weaker recorded claim is view-only. Reviewer read the replacement paragraph. Resolved by document change; no fresh blind behavior test. |
| IR-5 | Diagnose instruction suggested structured material references directly in Project, although the runtime has no such field; its P1 numbering also diverged from shared bridge IDs | Could generate an invalid payload or route via a mismatched bridge | Diagnose owner changed linkage to finding(subject=project, evidence=material refs), prohibited unknown Project fields, and aligned P1-1 through P1-6 with the shared directory. Reviewer read the replacement. Resolved by document change; no fresh blind behavior test. |

The review did not treat not-yet-written skills during parallel authoring as
missing-file defects. Final link completeness must be checked after authoring.

### IR-1 minimal reproduction

Using a temporary real Store:

1. Put project `q@1`.
2. Put assessment feedback `f@1`, subject `q@1`, source `human`, text
   `Use no external API.`.
3. Put the same feedback ID as `f@2`, expected version 1, text
   `Read the local code first.`.
4. Call context without writing any disposition.

Before repair: unresolved feedback contained only `f@2`; historical inputs was
empty. After repair: unresolved feedback contains both versions and historical
inputs includes `f@1`. Explicit supersession/consumption still requires an exact
feedback version and a disposition. The data was never deleted from history;
the defect was its omission from the default actionable context.

### IR-2 and IR-3 minimal reproductions

The controlled transport returned this complete but semantically incomplete body:

```xml
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><id>https://arxiv.org/abs/2501.12345</id></entry>
</feed>
```

`search(["memory"], sources=["arxiv"])` now produces unavailable/partial rather
than a complete successful paper record. This uses a fixture transport, not a
successful live arXiv response. Separately,
`deduplicate([{"title": null, "url": "https://example.test/paper", "provenance": []}])`
no longer throws; the local source adapter reports an unusable title as a source
error rather than asserting complete retrieval coverage.

## Runtime and retrieval checks actually executed

Initial targeted run:

```bash
python -m pytest open-scientist/tests/test_records.py \
  open-scientist/tests/test_mcp.py open-scientist/tests/test_search.py -q
```

Observed **37 passed, 9 subtests passed** before the newly reproduced edge cases
were fixed. This result did not mean those edge cases were covered. After search
repairs, the separately rerun search suite observed **18 passed, 9 subtests**.
The IR-1 reproduction was independently rerun after its fix and returned the
expected two feedback revisions. A final repeat of the same targeted three-file
command after these repairs observed **42 passed, 9 subtests passed**. Broader
aggregate totals belong to the packaging run; this count excludes asset and
other later-added tests.

The tests exercise real temporary SQLite stores, exact versions, stale writer
conflicts, source material linkage, append-only API history, frozen started test
inputs, context preservation, local read-only retrieval, partial/error/empty
semantics, CLI entry points and MCP protocol behavior. Network failures use
controlled transport fixtures. Source lookup is retrieval-only; no source or
material has a global scientific `supports` status. Scientific relationships are
finding records scoped to subject, claim, evidence and conditions.

Code inspection confirms explicit project roots, no automatic job execution,
no fixed global research phase, and separate Candidate versus Activity records.
The context API supplies complete records and historical dependencies; it does
not create a blinded or relevance-filtered review packet. The host must assemble
that packet and disclose its actual independence.

## B03: code changes the meaning of a favorable score

Read active `research-code`, `research-diagnose`, `research-test`, the shared
contract and record API. Executed this temporary Python fixture:

```python
samples = [(0, 0), (0, 1)]

def predict(observed, target, training=False):
    return target if training else observed

def evaluate(training):
    return sum(predict(x, y, training) == y for x, y in samples) / len(samples)
```

The declared report configuration used `training=True`. Observed outputs were
`reported_score=1.0` and `label_free_score=0.5`. The issue is the demonstrated
information path under that report configuration, not the variable name
`target`, and not an assertion that training supervision is always leakage.

The replay wrote a real Activity plan, advanced it to running, executed the
fixture, saved source/output Materials, advanced Activity to completed, and
wrote a contradiction Finding against the exact candidate claim that this
report establishes label-free inference. Candidate stayed version 1; the
original scope and failed claim were preserved. No training was started and no
population performance conclusion was drawn from two synthetic samples.

Observed bridge: code/configuration evidence → claim-scoped review → diagnosis
of which score interpretation remains valid. This demonstrates the intended
software handoff on a toy fixture, not real ML evaluation integrity.

## B06: prior positive score does not remove raw counterevidence

Read active `research-review` and the review-context contract. The temporary
Candidate claimed that keeping the most salient token always preserves the
relevant token, with any nonempty token list declared legal. Executed:

```python
tokens = [
    {"token": "a", "salience": 9, "relevant": False},
    {"token": "b", "salience": 1, "relevant": True},
]
kept = max(tokens, key=lambda token: token["salience"])
assert kept["relevant"] is False
```

Saved input/output as Material and a contradiction Finding. Revised that Finding
to contested because the author challenged legality. Context still contained
the exact prior contradictory version and original material. A separate
hypothetical old-review material contained `score=9; recommended pursue`.

The reviewer manually assembled a packet containing exact Q/H, constraints,
raw counterexample input/output and the legality question. An assertion checked
that the old score/recommendation were absent and raw counterevidence present.
The original premise admits the displayed list; the universal claim is refuted
for that scope. This says nothing about failure prevalence.

**Boundary:** no fresh reviewer was spawned for this packet. This inherited
context already knew the score and source design. Packet fidelity and history
retrieval were exercised; independent judgment, automatic blinding and model
uplift were not.

## B08: prose-only rewrite cannot invent a normalizer

Read active `research-report`, its view boundary and existing method definition.
Created temporary original/proposed/after cards. Original mechanism:
`Compute arithmetic mean of observed rewards.` The proposed edit added
`normalizes it by reward uncertainty`, which neither the Candidate nor the
fixture method defines.

The accepted prose became:

> The method adds the observed rewards and divides their sum by the number of
> observations.

The temporary output file was actually written. Before/after serialized
Candidate history was equal and remained version 1. The added uncertainty
normalizer was absent. No new mechanism, parameter, test activity or experiment
was created merely to improve prose.

This is a concrete view-edit replay by an informed reviewer, not evidence that
the skill introduces an ability absent from the no-skill baseline.

## B10: PARK, new constraint and a stale recorded PID

Read active `research-workflow` and `research-decide`. The temporary store held:

- A park decision because a remote dataset was unavailable, with the explicit
  revisit condition of a verified authorized local mirror.
- An Activity recorded as running, whose historical plan mentioned
  `2026-09-17`, PID `4242`, and an inaccessible fixture host.
- New human feedback: `Use local data only; no remote calls or jobs.`.

The replay created project `q@2` with the new constraint, then recorded an
adopted disposition pointing to that actual output reference. Context showed no
unresolved feedback for this instruction. It preserved the old job record at
its original version/status and recorded a new park decision for `q@2` because
the local mirror was still absent. No restart, kill, SSH call, monitor or new job
occurred.

The historical PID's present identity was **unverified**. An inaccessible
fixture host gives no basis to claim process liveness or termination. Preserving
the historical running record while reporting its current status as unknown is
intentional; a new user constraint is not evidence that the old run ended.

## Interpretation and remaining limits

All four bounded replays took a concrete action and preserved the relevant
Q/H/T/View distinction. They did not run a fixed full workflow. They complement
runtime tests with host-side interpretation and record-writing exercises.

The baseline already passed the stated response behaviors, and this reviewer
inherited the authoring context. There is no matched control, independent blind
panel or measured research-quality gain. The replays cannot establish robust
behavior across long projects, live model calls, remote experiments or real
literature novelty disputes. Live successful arXiv retrieval, Codex desktop
installation and end-to-end scientific benefit are outside this review's
verified scope.

### Skill snapshot identifiers

SHA-256 of the relevant files at this review checkpoint (later edits require
an applicability check; these are not model-performance hashes):

| Skill | SHA-256 |
|---|---|
| research-code | `4578d3f6c6f222b7ec57acc59090ff9f677df7b166da7b277debb0ebd31eb8a3` |
| research-diagnose | `b3e04ebbe421dbc5185bd8e1a178e0c89a9a0454663b01b1e7b107e907e27ad6` |
| research-test | `d685ccf3c933333ed7c59465286e0309d74602fa7ebcc91508bbf7ca6b20d590` |
| research-review | `891388c7ce9d1f40bc8b5887d269665cd90b740fc03e82adf297929fd4ca4ba9` |
| research-report | `ecf333116a452f60ff1a2484d5323e4ede896e211622dd216f2778ef3902090c` |
| research-workflow | `d9ed9874bf5f56d9023953a0329229bcdee31202790ef33c3a40e6d162354e30` |
| research-decide | `a8a0ec5d256b5575e8f06bcd3c7e92de48b58f62fa1449b0dfa678161f6899c9` |
