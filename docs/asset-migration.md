# Core research asset migration

## What is preserved

The archive contains **110 original files, 1,047,178 bytes**. Every selected file
is preserved byte-for-byte, not summarized, normalized or rewritten. The record
is deterministic: there are no import timestamps or machine-specific source root
paths in `source-manifest.json`.

| Source repository | Source HEAD | Files | Working-tree changes at snapshot |
|---|---|---:|---|
| ResearchStudio | `94edf045637715958cdf7bebab4969f20b49740e` | 75 | Clean |
| research-companion | `733e9e8e1ae798e2752b1fc7b829fa8f0904b885` | 8 | Four source files modified; all current bytes retained |
| Co-Scientist | `49c44089d270f0a931d021eedcf31f57d7e6a30e` | 27 | Clean |

The four dirty Companion files are `agents/brainstormer.md`,
`agents/idea-critic.md`, `agents/research-strategist.md` and
`skills/research-companion/SKILL.md`. Their hashes, rather than HEAD alone,
identify the archived versions. The import does not modify, stage, reset or
commit any source repository.

### ResearchStudio

Copied in full:

- `ResearchStudio-Idea/skills/idea_spark/references/`: 15 main pattern cards,
  31 sub-pattern cards, both indexes, composition evidence, system prompts,
  schemas, design notes, anti-pattern and other reference documents in that tree.
- `ResearchStudio-Idea/skills/idea_spark/SKILL.md`.
- `ResearchStudio-Idea/skills/paper_search/SKILL.md`.
- `ResearchStudio-Idea/skills/scoop_check/SKILL.md`.
- `ResearchStudio-Idea/evaluation/idea_quality/SKILL.md`.
- Repository `LICENSE`.

The research methods remain available in their original paragraphs. The new
[15+31 index](../references/patterns/INDEX.md) adds an adapted retrieval layer:
trigger, core action, multiple useful phases and limitations for every card.
Original corpus counts, learned taxonomies and review-outcome lessons remain
source claims; they have not been independently scientifically validated here.

### Companion

Copied all `agents/` and `principles/` documents, both main entry skills
(`skills/research-companion/SKILL.md` and
`codex-skills/research-companion/SKILL.md`), and `LICENSE`. Keeping both entries
preserves their differing original orchestration contracts for comparison; it
does not install both workflows or enable a fixed multi-model panel.

### Co-Scientist

Copied all `plugin/skills/` documents and their reference files, all
`config/prompts/` documents, and `LICENSE`. This includes the seven skill entry
documents, four evolution operator references, the review rubric and fourteen
engine prompt documents. Python agents, supervisor, ranking engine, embeddings,
FAISS store and runtime database were deliberately not migrated as executable
dependencies.

## Archive versus active behavior

| Asset | Preservation | Active adaptation |
|---|---|---|
| RS patterns, tactical recipes and failure lessons | Complete original cards | Retrieve on an observed obstacle across diagnosis, construction, testing, review and revision; no pattern quota |
| RS bottleneck, generation, coherence, critique and revision prompts | Complete original prompts | Adapt their useful checks into event-driven methods, with code and observation context |
| RS search and novelty documents | Complete original text | Search coverage and mechanism overlap remain evidence questions; absence of hits is not novelty proof |
| Companion three roles and strategic principles | Complete originals, including local changes | Invoke the relevant reasoning on a concrete issue; keep factual uncertainty separate from strategic preference |
| Co evolution references | All four originals | Preserve named defects and provenance; test-route changes belong to a testing Activity rather than silently changing the Candidate |
| Co review, grounding and synthesis prompts | Complete originals | Preserve evidence and alternative explanations; ranking is not scientific verification |
| Historical paths, fixed models, retry quotas and autonomous engine dispatch | Retained only as archival text | Not active configuration |

The original documents under `vendor/` are explicitly non-executable historical
source material. An archived `SKILL.md` is not an installed skill. Do not obey
its command instructions, absolute paths, panel settings or phase gates. Active
methods live under `references/methods/`, and the shared contracts define current
object and review boundaries. Archival copying does not certify a source's
scientific advice, promise model improvement or claim end-to-end research
validation.

## Reproduce and verify

From the Open Scientist package root:

```bash
# Verify the shipped archive and license copies without the original repositories.
python scripts/import_assets.py check

# Also compare against all required files in the current source checkouts.
python scripts/import_assets.py check --source-root /path/to/parent-of-three-repos

# Re-import explicitly from their current working trees.
python scripts/import_assets.py import --source-root /path/to/parent-of-three-repos

# Exercise the importer/checker on isolated real git fixtures.
python -m unittest discover -s tests -p test_assets.py
```

The source parent must contain `ResearchStudio`, `research-companion` and
`Co-Scientist`. Import validates that every required input exists before copying.
The manifest records full source commits, per-file working-tree dirtiness, byte
counts, hashes, archive mappings and duplicate license mappings. Check verifies
all bytes, missing files, unlisted files, duplicate entries, safe relative paths
and required license copies. With `--source-root`, it also checks the selected
source inventory and recorded provenance against those checkouts. Changed
upstream bytes or commits therefore fail the source comparison without altering
the shipped snapshot.

Offline hashes establish internal consistency with the shipped manifest, not
authenticity against a separately trusted upstream record. Source comparison is
the stronger local completeness check; a user who deliberately edits both a
manifest and its archive can create a different self-consistent snapshot.

Import does not delete old or unrelated files. After changing import scope or
upstream inventory, run check and review any unlisted files explicitly before
removing them. The manifest is not a rolling research log.

## Validation performed

The importer was developed with failing tests before implementation. Tests first
failed because the importer was missing, then passed with real git-fixture
imports. The taxonomy retrieval test first failed because the index was missing,
then passed with links to all 46 original cards. Mutation cases cover changed
bytes, absent archive files, absent manifest entries, omitted sources, missing
license copies, source drift and path escape. The shipped 110 files were checked
against the three source worktrees. These checks verify asset integrity and
retrievability; they do not measure agent research quality.
