---
name: open-scientist
description: Use when the user wants research driven from their question, papers, code or data — diagnosing whether a reported problem is real, finding and reading prior work (local paper library first), building a field's pattern cards and reviewer expectations, constructing or evolving a mechanism, planning and running a discriminating test, reviewing a claim, deciding pursue/refine/park/kill, or producing an idea card or report. Drives the Open Scientist study loop one checked step at a time. Skip for a single citation lookup, a plain code fix, or a summary of one paper.
---

# Open Scientist

Open Scientist runs research as a **study**: the user's question, worked one action at a time. You propose the next action; code checks that its inputs exist, that its versions are current, that it stays inside the user's authorization, and that its output meets the action's contract. Only then is the output written to the project's record store. The procedures that make research trustworthy are fixed ([protocols](../../references/protocols.md)):
- read before cite;
- plan before run;
- raw results kept;
- independent review;
- the hard floor;
- two-channel collision search.

What adapts is everything this field and this task need: cards, expectations, rubric, test protocol, code map, retrieval plan. Each is built from evidence for this study ([design](../../docs/design.md)).

## The loop

```bash
OS="python3 <plugin-root>/scripts/forge.py"        # <plugin-root> = the folder holding .claude-plugin/
$OS next --project "$PWD" --study <slug> --goal "<the user's words, verbatim>" --json   # first call only: --goal [--mode] [--budget]
$OS next --project "$PWD" --study <slug> --json                                         # every later call
```

The MCP tool `forge_next` (server `open-scientist`) returns the same step, if you prefer tools to the shell. The slug is a short kebab-case name for the question.

Do exactly the step returned, then call `next` again. Stop at a terminal step and tell the person what its notes say.

| Step `type` | Do |
|---|---|
| `bash` | Run each `run[]` command verbatim. Long ones (`run_test`, harvests) may run in the background; wait for them. |
| `llm` | Do the step yourself or in a sub-agent, in an **isolated context** when its role is `review` or `audit`. Pass it the `prompt` path, `inputs[]`, `outputs[]`, `errors[]` (FIX lines), `notes[]` and `batch[]`. When the outputs are written, run every `run_after[]` command at once (it records provenance and accepts the outputs). |
| `human_gate` | Ask the person what the notes say: intake (question, budget cap, constraints), an authorization (a proposal outside the policy), an `ask_human` question, or a decision in a human-decisions study. Record **their** words with the command in the notes, then run any `run_after[]`. Never answer for them. |
| `web_handoff` | Send `inputs[0]` (packet.md) to ChatGPT in a new conversation (web channel only), save the reply to `outputs[0]`, and record it with the `handoff mark` command in the notes. |
| `terminal` | Report `notes[]`: `done`, `stuck` (no progress, or a step keeps failing), `budget`, `need_goal`, `policy`, or a delegate's end. |

Steps of a delegated strict chain carry `scope`: `build_domain` runs RS's reading pipeline, and `idea_run` runs RS's idea chain. Treat them like any other step; their `run_after` already names the right scope.

## Rules

- **The proposal is the only control flow.** At a `propose` step, follow [prompts/study/propose.md](../../prompts/study/propose.md): name the open question most likely to change the next decision, and the cheapest action that answers it.
  - The table there maps open questions to actions.
  - Go back when the evidence says so. A contradicted premise means revise the question; it does not mean build on it.
  - Stop when the deliverable is met.
- **Write only through commits.** Each action writes files in its folder and the records in `commit.json` ([contracts](../../prompts/study/contracts.md)). Read records with `forge records context --project "$PWD" --study <slug>` or the `records_*` MCP tools (each study has its own store, `.forge/studies/<slug>/records.sqlite3`). Never edit a store, `study.json`, the kit, approvals or COMMITTED markers by hand; never call `study commit|exec|collide|absorb|answer` out of order or for another proposal: they refuse, and hand-edited control files stop the study. A person changes the policy with `forge study policy`.
- **Local papers first.** Use the `papers_search` tool or `scripts/search_papers.py`. A hit is a lead; a full-text reading pins its version or file hash; an empty search is not novelty.
- **Authorization.** Searches, reading, code inspection and cheap local runs proceed without asking. Training, paid runs, sending data off the machine, more budget than authorized, and changes to the user's hard constraints go to a person; code routes them.
- **Modes.** `--mode` is the shorthand for two settings stored in `study.json`:
  - the channel: local, or the web for design and challenge steps;
  - participation: auto, or a person making the decisions.
  
  `auto` = local + auto; `web` = web + auto; `hitl` = local + human decisions; `web+hitl` = both. The study keeps them; a later `--mode` does not switch them.
- **Keep your own context small.** Sub-agents read and write files and reply in a few lines.

## Other entries

- `next --domain <slug> --topic "..."`: build a field's assets with RS's strict pipeline (corpus → triage → full-text reading → signatures → cards → profile → frozen version).
- `next --run <slug> --domain <frozen> --question "..."`: RS's strict idea chain on a frozen domain.

Studies call both as `build_domain` and `idea_run` actions. Use these entries directly only when the user asks for a domain build or an idea card by itself.

Old skill names from 0.2 (`research-workflow`, `research-test`, …) forward here. Their full method texts now live in [references/methods/actions/](../../references/methods/actions/).
