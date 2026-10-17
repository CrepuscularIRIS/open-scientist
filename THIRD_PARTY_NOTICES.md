# Third-party source and adaptation notices

This package combines new MIT-licensed integration code/documentation with the
following retained assets. The root license does not replace their licenses.

| Source | Retained license | Location |
|---|---|---|
| ResearchStudio | MIT | [license](licenses/research-studio/LICENSE), [archive](vendor/research-studio/LICENSE) |
| Research Companion | MIT | [license](licenses/research-companion/LICENSE), [archive](vendor/research-companion/LICENSE) |
| Co-Scientist | Apache-2.0 | [license](licenses/co-scientist/LICENSE), [archive](vendor/co-scientist/LICENSE) |

Exact repository commits, paths, dirty status and file hashes are in
[source-manifest.json](docs/source-manifest.json). Four pre-existing Companion
working-tree modifications were preserved; the archive is a snapshot of those
files, not a claim that they are all identical to upstream HEAD.

The files under `references/methods/` are modified adaptations, with provenance
and change notices at their beginnings or ends. Core scientific reasoning and
paragraphs are retained where applicable; host paths, fixed stages, model panels,
default budgets and conflicting evaluation rules have been adapted. The skill
documents also derive from the credited source methods. Apache-derived content
retains the original Apache-2.0 terms and notices. No source root NOTICE file
was present in the inspected snapshots.

The independent local/arXiv adapter uses the installed corpus's schema and the
public arXiv API; it does not copy the unrelated installed paper-search code or
redistribute its PDFs/database. Writing-skills and mcp-builder were used as
authoring guidance, not bundled as assets or represented as our original work.
