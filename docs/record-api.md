# Shared-record API

All tools require an explicit absolute `project_root` pointing to an existing
project directory. Only writes create `.open-scientist/records.sqlite3` there.
Nothing selects `$HOME`, the current directory, or the installed plugin as a
default project. The runtime does not fetch URLs, execute commands, or run jobs.

## Five operations

| MCP tool | Arguments besides `project_root` | Result |
|---|---|---|
| `records_put` | `kind`, `record_id`, `payload`, `expected_version` | New record |
| `records_get` | `record_id`, optional `version` | Exact record or latest |
| `records_list` | optional `kind` | All latest records; no hidden limit |
| `records_context` | optional `subject` exact reference | All latest records, referenced historical versions, unresolved feedback, stale-input notices |
| `records_history` | `record_id` | All revisions, oldest first |

Python equivalents are `Store(project_root).put(kind, record_id, payload,
expected_version)`, `.get(record_id, version=None)`, `.list(kind=None)`,
`.context(subject=None)`, and `.history(record_id)`.

New IDs require `expected_version: 0`. Updates require the current revision.
Every successful write appends a version. Stale writers fail; kind cannot change.
There is no delete/overwrite API. IDs contain ASCII letters, digits, `_.:-` and
start with an alphanumeric character (maximum 128 characters).

Records return `id`, `version`, `kind`, UTC `created_at`, and `payload`.
An exact reference is always `{"id":"candidate-a","version":1}`. References
resolve only inside the requested project's store and must already exist.

## Payloads

Payloads reject unknown fields. Required fields are shown first; omitted optional
lists default to empty. Text fields must contain non-whitespace characters.

| Kind | Required fields | Optional fields |
|---|---|---|
| `project` | `question: string` | `constraints: string[]`, `user_context: string`, `change_note: string` |
| `candidate` | `problem: Ref` to project, `mechanism: string`, `claims: {claim_id: text}` (nonempty) | `assumptions: string[]`, `predictions: string[]`, `parents: Ref[]` to candidates, `change_note: string` |
| `material` | `source: string`, `content: string` | `locator: string`, `scope: string` |
| `activity` | `objective: string`, `status: plan/running/completed/failed`, `plan: string`, `inputs: Ref[]` | `outputs: Ref[]`, `result: string`, `failure: string`, `change_note: string` |
| `assessment` | See the four variants below | — |

Material records contain sources and observations, not a global `supports` flag.
The caller supplies the actual source content/locator; recording is not source
verification. The same material can support one claim and contradict another.

Assessment payloads use a `type` discriminator:

- **finding**: `type`, `subject: Ref`, `claim: string`, `judgment`,
  `evidence: Ref[]` to materials, `rationale: string`, `scope: string`.
  `judgment` is `supported`, `partial`, `contradicted`, `contested`, `unknown`,
  `not_found`, `unreachable`, or `uncited`. If subject is a candidate, `claim`
  must be a key in that exact candidate version's `claims`. Findings with
  supported/partial/contradicted judgments need at least one material reference.
- **decision**: `type`, `subject: Ref`, `decision: pursue/refine/park/kill`,
  `rationale: string`; optional `evidence: Ref[]` to materials,
  `revisit_when: string`. An investment decision makes no scientific finding.
- **feedback**: `type`, `subject: Ref`, `source: human/agent`, `text: string`.
  Recording feedback does not mean it has been consumed. Revising a feedback
  record does not silently withdraw earlier versions: each remains unresolved
  until a disposition references that exact version. To replace an instruction,
  explicitly record a superseded disposition pointing to the replacement.
- **disposition**: `type`, `subject: Ref` to feedback or finding,
  `outcome: adopted/deferred/rejected/superseded`, `rationale: string`;
  optional `outputs: Ref[]`. Adopted/superseded needs an output reference;
  deferred remains unresolved. This is an accountable response, not permission
  to ignore a user instruction.

An activity plan has no outputs, result, or failure. Completed needs `result`;
failed needs `failure`. Updating a plan to running freezes its objective, plan,
and input versions. Later revisions cannot retroactively change those fields.
Transitions are plan→running/failed, running→completed/failed; terminal activities
cannot reopen. A caller may record an already completed activity as its first
version, but this does not establish preregistration. Results can be corrected
in a new terminal revision; history preserves the prior statement. A new test
or rerun needs a new activity ID.

Context deliberately returns the full project, even with `subject` supplied;
the optional subject identifies focus, not a hidden relevance filter. It also
returns exact historical dependencies and prior contrary findings. Nothing
silently drops the eleventh result or replaces an old referenced version with
latest. Stale-input notices ask for applicability review, not automatic reruns
or automatic revocation of scientific conclusions. Context has no independent
review blinding mode: the host must build the appropriate evidence-preserving
view from these records.

## CLI fallback

`python /absolute/plugin/path/scripts/records.py --project-root /absolute/project
put --kind project --record-id project --expected-version 0 --payload-file
/absolute/project/question.json`

Other subcommands: `get ID [--version N]`, `list [--kind KIND]`, `history ID`,
`context [--subject-id ID --subject-version N]`. A payload file is a JSON object;
`--payload-file -` reads stdin. Success prints JSON to stdout; validation errors
print to stderr and exit nonzero. The CLI uses the same Store and schema as MCP.

Run the stdio MCP server with `python /absolute/plugin/path/scripts/mcp_server.py`.
The server accepts a project root on every call and does not create a store at
startup. Storage durability is local SQLite; this is not a remote collaboration,
artifact backup, scheduling, or file-access sandbox service.
