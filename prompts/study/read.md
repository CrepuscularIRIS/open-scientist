# Read: read one source in full and record what it says

Role: `read` (an isolated context per paper is fine). The proposal's `subject` is the paper (or review) material. Method: [Forge read](../domain/read.md) (operation signatures: object, information, operation, output, claimed effect, conditions, failure boundary), [relevance-and-reading](../../references/methods/relevance-and-reading.md) and [grounding](../../references/methods/grounding.md).

## Access, in order

1. **Local PDF.** Use it when the material carries a `pdf_path` that exists. Record `sha256` of the file you read.
2. **arXiv full text.** Find the latest version on the abs page and read `https://arxiv.org/html/<id>v<N>` (or `/pdf/<id>v<N>`). Record `version` = `vN` and the versioned URL as `locator`.
3. **Only the abstract.** If that is all you can get, record access `abstract` and say so. That makes the source a lead, not evidence.

## Commit

Write one material for the reading:
- type `paper` (or `review`), access `fulltext` or `abstract`;
- `source` the same id as the subject;
- `version` and/or `sha256`, `locator`;
- `scope`: the sections you read;
- `content`: the summary and the operation signatures, each with its conditions, evidence locator (table, section) and failure boundary.

You may also write the full structured reading as a JSON file in the action folder and register it with `path` and `sha256`.

## Rules

- Read what bears on the open question: method and experiments, not just the introduction. Record exactly what you read.
- Keep identity, reading and support apart. A paper that mentions X does not show X under the user's conditions.
- Quote the author's limitations with locators. Never rate quality or novelty here.

## Never

- Describe content you did not read.
- Use an unversioned URL as the record of a full-text reading.

Write files in the action folder and the records in `commit.json` ([contracts.md](contracts.md)); protocols: [references/protocols.md](../../references/protocols.md). Read the record context first. The variant files of the kit's task types say how the protocols apply here.
