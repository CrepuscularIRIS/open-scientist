# Verbatim source archive — historical reference data

This directory preserves selected original documents from ResearchStudio,
research-companion and Co-Scientist, including their original paragraphs,
schemas, examples, prompts and license notices. They are **non-executable
historical source material**, not installed Open Scientist skills or active
instructions. No upstream runtime engine was imported.

The files deliberately retain old commands, absolute paths, model names,
role instructions, state gates, paper-count claims and author judgments.
Do not execute those commands or adopt those policies merely because a document
is present here. Active skills use the adapted methods and contracts under
`references/`; the [pattern index](../references/patterns/INDEX.md) provides
on-demand access to the complete originals. Archive reading does not activate a
skill. Citation to an archived paragraph is evidence of what the source says,
not verification that its method or empirical claims are correct.

## Scope and provenance

| Archive | Original checkout | Included material |
|---|---|---|
| `research-studio/` | `ResearchStudio` | Full `idea_spark/references/`; IdeaSpark, paper search, scoop check and IdeaQuality skill sources; LICENSE |
| `research-companion/` | `research-companion` | All agents and principles; Claude and Codex main skills; LICENSE |
| `co-scientist/` | `Co-Scientist` | All plugin skill documents and references; all configuration prompt documents; LICENSE |

The directory hierarchy below each archive slug is unchanged from its source
repository. Bytes are copied from the **working tree**, so pre-existing local
edits are retained. Each file's repository, HEAD commit, relative path, dirty
status, size and SHA-256 are recorded in
[source-manifest.json](../docs/source-manifest.json). HEAD alone does not identify
a dirty file's content; use its recorded hash. Source LICENSE files are duplicated
under `licenses/` for convenient distribution. A root NOTICE, if present in a
future import, is likewise copied and recorded.

Read [asset-migration.md](../docs/asset-migration.md) for reproducible integrity
checks, the exact snapshot scope and the boundary between faithful archival
copying and adapted active methods.
