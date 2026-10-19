# D4 — Read a paper and extract operation signatures

Role: `read`. One paper per output file. Run each paper in an isolated context when you can; the batch is just the next papers the navigator wants.

## Inputs

- `brief.md` — the obstacles and cross-domain mappings this build cares about.
- `papers.jsonl` — find the batch paper's row (`arxiv_id`, `snapshot_id`, `title`, `abs_url`, `pdf_url`).
- The paper itself. Read the **method and experiments**, not just the abstract. Find the latest version on the abs page (`v1`, `v2`, ...), then read `https://arxiv.org/html/<arxiv_id>v<N>`, or the PDF `https://arxiv.org/pdf/<arxiv_id>v<N>`. Record exactly which version and sections you read.

## Output: `readings/<arxiv_id with / replaced by _>.json`

```json
{
  "arxiv_id": "2501.01234",
  "snapshot_id": "<copy from papers.jsonl>",
  "title": "...",
  "access": {"source": "arxiv_html", "locator": "https://arxiv.org/html/2501.01234v2", "version": "v2", "sections_read": ["3 Method", "4.2 Ablations", "Appendix B"]},
  "summary": "Two or three sentences: problem, mechanism, strongest evidence.",
  "signatures": [
    {
      "sig_id": "2501.01234#s1",
      "object": "what the method acts on (a concrete thing)",
      "information": "what information the operation has access to — and what it does NOT",
      "operation": "the move itself, as a verb phrase someone could implement",
      "output": "what the operation produces",
      "claimed_effect": "the effect the authors claim, with the metric",
      "conditions": ["assumption or regime under which it is claimed to work"],
      "evidence": {"kind": "reported_experiment", "locator": "Table 3; Sec 4.2"},
      "failure_boundary": "where it is shown or likely to stop working; 'not reported' is allowed",
      "verified": "fulltext"
    }
  ],
  "baselines": [{"name": "DreamerV3", "kind": "method"}, {"name": "DMC suite", "kind": "benchmark"}],
  "limitations": ["limitation stated by the authors, quoted or closely paraphrased with a locator"]
}
```

Rules:

- One signature per distinct operation; most papers have 1–3. A paper's framing sentence is not a signature; the move that produces the result is.
- `information` matters most for later merging: two methods with the same verb but different information access are different mechanisms.
- `evidence.kind`: `reported_experiment`, `theorem`, `author_claim` (asserted without direct evidence), or `observed` (you checked it yourself, e.g. ran code).
- If you could only read the abstract, set `access.source` to `abstract_only` and every signature's `verified` to `abstract_only`. Such signatures are reading leads, not checked mechanisms: they cannot make a card a pattern or ground an idea's premise. Do not pad them.
- For `arxiv_html`/`arxiv_pdf`, `access.version` is the version you read and the locator is that versioned URL; an unversioned URL is refused because it does not pin the text.
- `baselines`: methods, datasets, metrics and benchmarks the paper compares against or evaluates on, as named in the paper.
- Copy `snapshot_id` exactly; it pins the metadata row you were given (title, abstract, dates), not the full text. `access.version` pins the text.

## Never

- Cite or describe content you did not read. If a section was unavailable, say so in `sections_read` and `failure_boundary`.
- Rate the paper's quality or novelty.
