# Research Forge — build plan

| Milestone | Delivers | Done when |
|---|---|---|
| **M1 Domain layer** ✅ | plugin skeleton; navigator framework; domain pipeline D0–D9 (brief → corpus → triage → readings+signatures → clusters → cards → profile → stats → freeze); asset validators; stdlib clustering; tests | `forge next` walks a fake project from empty to a frozen domain version with every step validated |
| **M2 Idea layer** ✅ | RS phases 1–4 rewritten to read the frozen domain; citation gate against card ids; collision using domain lexicon; audit + strategist; information-gain retry; idea card template + validator; lessons back to the domain | `forge next` walks an idea run end to end on fixtures |
| **M3 Modes** ✅ | routing table; `web_handoff` packets + receipts + serial queue; `gate` steps for hitl; per-artifact provenance | the same run switches mode without changing artifacts other than provenance |
| **M4 Mod** ✅ | hooks module: `/forge` command, pane (domain version, run state, pending gate/handoff), status line, mode from `userConfig` injected into the system prompt. Not done: a background runner (harvests are still started by the host's Bash tool) | `claude plugin validate` + `claude plugin test` pass; loads with `--plugin-dir` |
| M4.1 Review fixes ✅ | second review (2026-10-18, `analysis/research-forge-review-2026-10-18/`): gate re-checks in commands, content-hash acceptance, round-keyed web handoffs, stored mode/budget, repair cap, revision field whitelist; cards optional, expectations answerable n/a or challenged, user cap vs model estimate, hitl at intake; review evidence must resolve, full-text-only patterns and grounding, submission-event stats, lesson refs, smoothed clustering | the six reproductions now refuse or correct; a third adversarial review of the fixes (4 P1, 4 P2, 3 P3) also fixed; one regression test per finding (90 tests). Known limit: the repair cap counts provenance rows, so it needs a host that runs `run_after` |
| M4.2 Materials and evidence return | local PDFs, project repository (commit + files), failure fixtures and probe results as registered sources; `needs_evidence` / `needs_code_check` / `needs_domain_update` return paths instead of `do_not_generate` for missing material; a run reads new collision papers in full and feeds the domain | design approved, then two small real cases (wide-domain reading; a wrong code premise corrected by a cheap check) |
| M5 Backtest | time-split harness (domain built before T; compare with later outcomes when labels exist) | report on one real topic |

Out of scope until asked: OpenReview harvesting (outcome labels are an optional `labels.jsonl` input, review text an optional `reviews.jsonl`; Open Scientist's connector can produce them), Elo, training.

Status 2026-10-18: M1–M4 and M4.1 built; fixture tests and `claude plugin validate`/`test` pass. Not yet run: a full domain + idea run with real model steps. Not built: M4.2 (the review's D2/D3).
