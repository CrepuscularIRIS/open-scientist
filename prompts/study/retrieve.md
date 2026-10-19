# Retrieve: find candidate sources, local library first

Role: `fast`. You register what a search **returned**, as leads. Reading is a separate action. Method: [OS retrieve](../../references/methods/actions/retrieve.md) (decision-oriented brief, query perspectives, relevance × use, nomination vs. admission) and [intent-recognition](../../references/methods/intent-recognition.md).

## Procedure

1. Write the brief in one paragraph: the open question, what a useful source would show, and what would make it irrelevant.
2. **Local first.** Search the local paper index:
   - with the `papers_search` MCP tool (`sources: ["local"]`), or
   - with `python3 <plugin>/scripts/search_papers.py --queries 'a|b' --sources local --json <action folder>/local.json`.
   
   Query from the brief's terms, plus another community's name for the same thing.
3. **Then arXiv**, only if the local results leave the question open, or the question needs recent work (`sources: ["arxiv"]`). If the kit has a `retrieval_plan`, follow its `enough_when`.
4. Keep the search report file (it records each source's status: empty, missing_index, timeout, rate_limited). An empty or failed source is reported as such, never as "no prior work".

## Commit

- One material per source worth reading next: type `paper`, access `identity` (or `abstract` if you only saw the abstract), `source` (`arxiv:<id>` or the local index id), `locator` (URL or `pdf_path`), `content` (why it matters to the open question).
- One material for the search report itself (type `log`, with `path` and `sha256`).

## Never

- Mark a search hit as read.
- Admit a paper you remember but no search returned (nomination ≠ admission).
- Read here.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
