# Regulation change: how the sub-goal diff works

Input: the requirements derived from one version of a UN Regulation, the PDF of that version and
the PDF of a later one. Output: the requirements that must change, each with the change, the new
text, the reason and the paragraph in the new PDF (`schemas/submission_subgoal.schema.json`).
Code: `brain/brain/subgoal.py`. Scorer: `brain/eval/subgoal_score.py`. No model, no network.

## 1. Parsing

Both PDFs go through `brain.ingest.parse_pdf`, the parser of the main goal. The script's own parser
(`scripts/diff_regulation.py`) is not used, for three reasons:
- ingest gives every paragraph of the dev gold its label and page in the new PDF, including annex
  labels in the gold's style (`Annex 3 2.1`);
- it reproduces the gold's text. The gold quotes 5.1.6.2 as "Acceleration while creeping, In the
  case…", which is ingest's heading joined to the body with ", ";
- it is tested, and the 36 base and latest pairs of the package are already parsed with it.

Page headers, footers and footnotes are dropped by ingest. Text is compared on `bare()` tokens:
lower case, punctuation removed, "70%" and "70 per cent" spelled one way, "6 seconds" and "6 s"
too. Line breaks, page breaks and footnote markers therefore never count as a change. Table cell
text stays in the paragraph that holds the table, in both versions alike.

## 2. Alignment of old and new paragraphs

The unit of alignment is a span: a sentence, or a list item such as "(a) …", inside a paragraph.
Three passes:
1. **Same label.** Old and new paragraph with the same label and a token similarity of at least
   0.5 (`difflib` ratio on `bare()` tokens) are a pair.
2. **Renumbered.** Paragraphs left unpaired are matched across labels when their similarity is at
   least 0.8.
3. **Split, merged, moved.** Every old span not found word for word in its pair goes to the best
   new span anywhere in the document with similarity at least 0.5. Each new span is claimed by one
   old span only, best score first. An old span with no match is deleted. A new span no old span
   claims is new.

A requirement's reason says "(formerly X)" when the new label of its span differs from the label
of its old span. On dev, old 6.5 was split: its spans land in new 6.5.2, 6.6 and 6.6.1.2.

## 3. Diff classification

| Class | Rule | Flagged |
|---|---|---|
| Unchanged | `bare()` tokens equal, under any label | no |
| Formatting only | same as unchanged: spacing, line breaks, "%" against "per cent" | no |
| Amended | word operations remain after dropping those equal under `bare()` | yes |
| New | a new span no old span claims | yes, as added |
| Deleted | an old span with no new span | yes, as removed |

The edit list is a word-level `difflib` diff of the old and new span, in document order:
`'A' became 'B'`, `'X' was added`, `'Y' was removed`, joined by `; `.

## 4. Requirement mapping

A requirement's old span is the run of sentences, in its cited paragraph or that paragraph's
descendants, that best matches its text. A requirement can cite a parent paragraph, and one
paragraph can carry several requirements.

A requirement is flagged only when its own span changed. The dev gold decides this: old 6.5 holds
the source sentences of R-084 to R-090, and only R-084, R-085, R-086 (edited) and R-090 (gone) are
flagged. R-087 to R-089 come from sentences that survive unchanged.

## 5. Change records

- **Modified.** `new_text` is the old requirement with the span's edits applied, when each edit
  finds its place in the requirement text. Otherwise it is the new span.
- **Added.** One row per obligation in a new span: a sentence with "shall" or "may" (a sentence
  "X shall A, and may B" gives two rows), or each list item under a lead-in ending in ":". The
  lead-in itself is never a row. `new_text` comes from `brain.rewrite.deterministic`. Rows are
  only added in the top-level sections the old requirements cite: on dev that is sections 3 to 8,
  which leaves out the transitional provisions of section 12.
- **Removed.** The requirement's span has no new span anywhere in the new version.

## 6. Reasons and sources

| Change | Template |
|---|---|
| Modified | `Paragraph {new} of {reg} was amended in version {v}: {edits}.` |
| Modified, renumbered | `Paragraph {new} (formerly {old}) of {reg} was amended in version {v}: {edits}.` |
| Added | `Paragraph {new} of {reg} is new in version {v}: '{quote}'.` |
| Removed | `Paragraph {old} of {reg} was amended in version {v}; the provision '{quote}' no longer appears.` |

An added quote is the obligation's sentence or item, cut to 99 characters plus "…" when it is
longer than 100. A removed quote is the old source sentence, cut to 89 plus "…". Three dev gold
quotes are cut differently, and the gold orders some edit lists out of document order. No single
rule reproduces those, so on dev at most 21 of 24 reasons match exactly. `source` is the page and
label of the span in the new PDF; removed rows have none. The version comes from
`regulations/index.json`, found by the new PDF's SHA-256, or from `--to-version`.

## 7. Models

None. Every step above is a rule. The only text a model could improve is `new_text` of added rows,
which the deterministic rewrite writes in the main goal's style. If a model is ever added there,
it stays optional and the deterministic text is the default.

## 8. The change monitor

The same engine runs when a new version of a regulation lands, against the requirements of a
saved assessment:

```python
from brain.subgoal import diff_assessment

report = diff_assessment(old_pdf, new_pdf, requirements, to_version="1.0.0")
```

`report` is the submission dict. Each change also carries `old_span` and `new_span`, the sentence
before and after, so the app can show which sentence changed:

```json
{
  "requirement_id": "R-018",
  "change": "modified",
  "new_text": "The ACPE shall control acceleration when the vehicle is accelerated both from standstill and, as relevant, while creeping.",
  "reason": "Paragraph 5.1.4 of UN R175 was amended in version 1.0.0: ...",
  "source": {"page": 5, "paragraph": "5.1.4"},
  "old_span": "The ACPE shall control acceleration when the vehicle is accelerated from standstill.",
  "new_span": "The ACPE shall control acceleration when the vehicle is accelerated both from standstill and, as relevant, while creeping."
}
```

`web/backend` can call it with the assessment's requirements and the two PDF paths. The UI is out
of scope here.

## Command

From `brain/`:

```bash
uv run python -m brain.subgoal --old-pdf ../subgoal/dev/old.pdf --new-pdf ../subgoal/dev/new.pdf \
  --requirements-old ../subgoal/dev/requirements_old.json --case-id subgoal-dev --out ../out/subgoal-dev-det.json
uv run python -m eval.subgoal_score ../out/subgoal-dev-det.json
```
