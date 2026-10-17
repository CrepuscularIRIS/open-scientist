# Reporting and decision skill authoring checks

Date: 2026-10-17.

## Method and honest limits

Read writing-skills and its test-driven-development background before authoring.
Read evaluations/baseline.md before authoring: all 11 contextual responses passed.
B08, B09, and B10 already articulate the intended behaviors without the new skills.
There is no observed failing baseline to claim as RED, and no measured improvement.
The user-authorized task is detailed migration and packaging of existing assets.
The shorter default size guidance was overridden by the explicit detailed-skill request.
No deployed host, research experiment, or independent model outcome is claimed here.
No additional evaluator or subprocess model was launched for these checks.

The sequence below is a same-author synthetic application replay, not a fresh blind
agent evaluation and not a causal test of skill effectiveness. Assertions inspect
concrete proposed outputs against the fixture; they do not demonstrate that an
agent will read the decisive source or persist correct records in a real session.
Future evaluation needs fresh-context agent runs with matched task/evidence/budget,
actual files and tools, and independent outcome adjudication.

## Authoring checklist and sequence

- [x] Read baseline before new skills; preserve its PASS results and limitations.
- [x] Read governing research contract and current record API.
- [x] Write report skill and supporting methods/templates first.
- [x] Apply report skill to the synthetic case below before writing decide skill.
- [x] Inspect report response separately against each expected behavior.
- [x] Write decide skill after the report replay.
- [x] Apply decide skill to investment/resumption cases and inspect separately.
- [x] Verify owned Markdown links and schema terminology against the current integration files.
- [ ] Fresh-context pressure testing and matched no-guidance comparison: not run.
- [ ] Deployment in a host: not run; outside this authoring check.

## Report replay R1: prose-only edit plus inconvenient old evidence

### Synthetic input supplied to this authoring pass

Task: Rewrite the following method for a non-specialist. No algorithm change.
H1 mechanism: For each sample set, compute the arithmetic mean of its rewards.
H1 claim universal-robustness: This aggregation is robust to arbitrarily large outliers.
Code excerpt: `reward = sum(rewards) / len(rewards)`.
Draft under review: Normalize rewards by their estimated uncertainty before averaging.
H0 is low ranked and parked, but carries the exact synthetic instance [0, 0, 300].
Its mean is 100, while [0, 0, 0] has mean 0; the changed input is one unbounded outlier.
The fixture specifies that this instance is within H1's claimed scope.
These are authored fixture facts, not results from a real research execution.

### Skill-enabled response produced during this replay

> 对这一组样本，把各样本的奖励相加，再除以样本数，得到平均奖励。
>
> 本次改写保留 H1 的算术平均；“按不确定性归一化”没有出现在原方法或代码中，
> 已从文案中移除。它若要成为方法的一部分，需要另行定义并作为新的 H 版本。
>
> H1 当前也不能声称对任意大异常值稳健。即使 H0 已停用且评分低，其给出的
> [0, 0, 300] 仍是适用于这一全称主张的反例：一个异常值把均值从 0 改为 100。
> 该反例应保留在 universal-robustness 的 finding 中，不能因候选排名过滤。
> 本次只完成文案及证据边界说明；未修改算法、运行实验或写入虚构记录。

### Separate assessment after response

| Expected behavior | Observed response evidence | Result |
|---|---|---|
| Preserve arithmetic-mean mechanism | First paragraph explicitly describes sum divided by count | PASS for this text |
| No invented normalizer | Says removed and new H required for separate design | PASS for this text |
| Keep low-ranked/parked counterexample | Includes H0, exact values, and affected claim | PASS for this text |
| Distinguish view from H change | States no algorithm edit; new H only for scientific design | PASS for this text |
| No fake execution/persistence | Explicitly says no experiment or fabricated record write | PASS for this text |
| Stop at prose boundary | Does not begin implementation or a new test | PASS for this text |

R1 passed this authored response check before research-decide was written.
This is not evidence of a new ability over B08, which already passed the baseline.

## Decision replay D1: budget preference versus scientific truth

### Synthetic input

Explanations A and B both fit the observed aggregate score. A's next test costs one
local CPU hour; B's proposed test needs unavailable data. No supplied observation
distinguishes A from B. The user wants the strongest justified next action.

### Skill-enabled response

> 现在还不能判定 A 或 B 哪个解释正确。A 的成本较低只影响投入顺序。
> 先核实 A 的一小时检查是否会产生两种解释不同的预测；如果会，就 pursue
> 这一项已授权的局部检查，同时保留 B。若它只重复已知现象，就 refine 测试，
> 不把便宜当作信息价值。B 因数据不可得暂时 park，重访条件是取得适用数据，
> 或找到保持区分力的替代测量；没有新建自动监控或运行昂贵作业。

### Separate assessment

PASS for this text: scientific uncertainty is preserved; investment and truth are
separate; the cheap test must discriminate; B has a concrete revisit condition;
no experiment or automation is falsely claimed. Actual cost estimation, data
availability, execution, and record persistence were not tested.

## Decision replay D2: PARK with changed constraint and old PID

### Synthetic input

The stored decision parks H2 until dataset access is granted. A new user message
says the dataset cannot be used. A month-old handoff contains PID 4312 and ACTIVE.
No current process identity or live remote status is supplied.

### Skill-enabled response

> 继续 park H2：原来的恢复条件没有满足，新约束还排除了原数据路线。
> PID 4312 和 ACTIVE 是历史记录，不能证明当前作业身份，也不触发恢复或停止。
> 若需要核对运行状态，先做只读的进程/作业身份检查；当前只可标未核。
> 下一可行调查是寻找满足数据约束、仍能区分原假设的替代测量。若必须改变
> 机制或主张，就提出新 H，而不是改写已执行测试。记录新约束和对应决定后，
> 对用户反馈写明采用及其具体输出引用；此处未执行这些写入或检查。

### Separate assessment

PASS for this text: park remains justified; new constraint is consumed in the
proposed reasoning; stale PID is not trusted; alternative route retains
scientific discrimination; no resumption, termination, or record write is invented.
Live identity checking and durable feedback disposition remain untested.

## Refactor notes from document inspection

Inspection after the replays found several retained source instructions that
would contradict optional views: exactly seven translation fields, all three
language fields, archived phase4 assembly commands, and assumptions that archived
validators run. These were removed or explicitly converted to optional field
vocabulary and caller checks. The specification reference now separates sourced
clarifications from new load-bearing parameters; the latter require H revisions.
This was a document-consistency correction, not a discovered model failure.

Both skill bodies retain detailed process, input/output, branch, stop, example,
trap, and provenance sections. The methods preserve substantial source paragraphs
with targeted semantic changes and archive links; they are not vendor pointers alone.

## Local document verification

Checked all relative Markdown links in the 13 owned files after writing: no missing
targets at that time. Verified research-report has 220 lines and research-decide
has 221, with name and trigger-only description frontmatter. Searched the five
method adaptations for historical run-directory instructions, fixed translation
field counts, old host names, and legacy assembly commands: none remained from
the searched patterns. Read the current shared contract and record API; examples
use semantic references and do not claim their optional view JSON is API input.
This is source/document inspection, not plugin installation or scientific validation.

## Follow-up adaptation check: renderer assumptions and active critic

The integration review identified legacy presentation requirements in the adapted
RS methods: Unicode-only/no-math-engine instructions sat beside unconditional
KaTeX assumptions. Replaced the entire rendering advice in expand, derive_plain,
and implementability_audit with optional, format-aware guidance. The selected
view may use plain text, Unicode, or LaTeX according to its actual renderer;
scientific meaning and parameter provenance remain mandatory. Vendor originals
were not edited. This correction removes a portability inconsistency, not a
measured model-behavior regression.

Added companion-critic.md as an active method reference using the full original
Idea Critic, retaining its seven dimensions, strongest arguments for/against,
conditional value test, riskiest assumption, and prior-evaluation logic. Targeted
changes remove source-host paths and mandatory competitor timelines, distinguish
strategic value from scientific truth, route unknown novelty to retrieval, and
prevent weak narrative from acting as a kill gate. Independent first review and
revision-aware strategy now have distinct access to prior scores. Report and
decide link this reference; the review-skill owner was notified.

### Additional same-author application check C1

Synthetic input: The mechanism is plausible but untested. Its abstract is dull,
novelty has not been checked, and another laboratory may work on it soon. The
user asks for an honest recommendation, not a new experiment.

Response: “Weak storytelling is not enough to kill the line. Keep scientific
status unknown, identify the concrete capability whose value matters, and route
the exact nearest-prior comparison to research-retrieve. Any prediction about
the other laboratory is uncertain unless supported by current evidence. Choose
refine for the named evidence/value gaps; do not fabricate a strong conclusion,
a scientific winner, or a competitor deadline. No experiment is started.”

Separate assessment: PASS for this text on value/truth separation, uncertain
forecast, unknown-novelty routing, no narrative-only kill, and execution boundary.
This remains an authored synthetic response, not an independent agent test.

Rechecked the 14 owned documents: no missing relative Markdown links. Current
skill lengths are report 221 and decide 222 lines. Searched the three RS methods
for the obsolete mandatory Unicode/KaTeX/no-math-engine assumptions; remaining
renderer mentions describe conditional advice or explicit non-assumptions.
