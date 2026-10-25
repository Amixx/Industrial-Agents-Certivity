# Regulation change: how the sub-goal diff works

Input: the requirements derived from one version of a UN Regulation, the PDF of that version and
the PDF of a later one. Output: the requirements that must change, each with the change, the new
text, the reason and the paragraph in the new PDF (`schemas/submission_subgoal.schema.json`).
No model, no network; about 1 s per pair.

On dev (UN R175 0.1.0 to 1.0.0) the platform scores flag recall 100.0%, flag precision 100.0%
and change accuracy 100.0% (`out/subgoal-dev-det-v6.json`). The results and every upload are in
[out/README.md](../out/README.md); the task and its Sunday steps in
[brain/docs/todo/05-subgoal.md](../brain/docs/todo/05-subgoal.md).

## Code

Everything is in the package `brain/brain/subgoal/`. Commands run from `brain/`.

| File | What it does |
|---|---|
| `__init__.py` | The API: `run` (a submission), `diff_assessment` (the changes, for the app), `validate`, `version_of`. |
| `__main__.py` | The command: `uv run python -m brain.subgoal --old-pdf … --new-pdf … --requirements-old … --case-id … --out …`. Exits 1 if the file fails `tools/validate.py`. |
| `text.py` | Normalised words (`bare`), units (`sentences`), the word diff (`word_ops`, `substantive`, `describe`), quotes and the 2,000-character limit (`quote`, `shorten`, `fit`). |
| `align.py` | Old and new units (`units`) and how they are paired (`align`, `kind`). |
| `changes.py` | Modified and removed rows for old requirements (`map_requirements`), added rows for new paragraphs (`obligations`, `fuse`, `added_changes`). |
| `score.py` | Strict local scorer against a gold: `uv run python -m brain.subgoal.score <file>`. |
| `survey.py` | `uv run python -m brain.subgoal.survey` diffs every base and latest pair in the corpus; `--synthetic` runs six known edits on each; `--main-goal "UN R48" …` runs the whole diff with the main goal's rows as old requirements. |

Tests: `brain/tests/test_subgoal.py`. The dev and corpus tests skip when the PDFs or the corpus
are missing.

## 1. Parsing

Both PDFs go through `brain.ingest.parse_pdf`, the parser of the main goal. The old script's
parser (`scripts/diff_regulation.py`) is not used, for three reasons:
- ingest gives every paragraph of the dev gold its label and page in the new PDF, including annex
  labels in the gold's style (`Annex 3 2.1`);
- it reproduces the gold's text. The gold quotes 5.1.6.2 as "Acceleration while creeping, In the
  case…", which is ingest's heading joined to the body with ", ";
- it is tested, and the 36 base and latest pairs of the package are already parsed with it.

Text is compared on `bare()` words: lower case, punctuation removed, "70%" and "70 per cent"
spelled one way, "6 seconds" and "6 s" too. Line breaks and page breaks never count as a change.
Ingest drops page headers and most footnotes, but a footnote marker glued to a word ("vehicle6",
"6This") can remain, so a renumbered marker is not a change either.

## 2. Alignment

The unit is a sentence or a list item ("(a) …", "(iv) …") inside a paragraph. The paragraph
heading ("Acceleration from standstill") is set aside, so a heading added above an unchanged
sentence changes nothing; a heading that ends in ":" is a lead-in and stays a unit.

Matching paragraphs by label fails on dev: old 5.1.4.1 became new 5.1.4.2 while new 5.1.4.1 is a
different provision, and the end of old 5.1.5 became new 5.1.5.1. So units are matched across the
whole document, in three passes:
1. **Exact.** Units with equal `bare()` words are a pair, under any label (same label first,
   then document order). This covers unchanged, renumbered and moved text.
2. **Merged.** A unit whose words contain two or more units of the other version, covering at
   least 80% of it, is paired with all of them. Some base PDFs are parsed with provisions glued
   together (R32 2.2.5 holds 2,801 characters and runs into section 4); without this pass their
   text would count as deleted and added again.
3. **Similar.** Units left over are paired when their `difflib` ratio is at least 0.5: within the
   same paragraph first, then across paragraphs, best score first. Trying the same paragraph
   first keeps an amended item of 5.1.5 in 5.1.5 instead of pairing it with a similar new
   sentence in 6.5.3.

An old unit with no pair is deleted; a new unit no old unit claims is new.

| Class | Rule | Flagged |
|---|---|---|
| Unchanged | equal `bare()` words, or a merged pair, under any label | no |
| Formatting only | the same: spacing, line breaks, "%" against "per cent", footnote markers | no |
| Amended | word edits remain after dropping those equal under `bare()` | yes |
| New | a new unit no old unit claims | yes, as added |
| Deleted | an old unit with no new unit | yes, as removed |

## 3. Requirement mapping

A requirement's old span is the run of consecutive units, in its cited paragraph or that
paragraph's descendants (the whole document if the label is not found), that best matches its
text by shared words regardless of order: a requirement often reorders its clauses ("When X, the
ACPE shall …"). Its new span is the new units its units became, plus unclaimed new units between
them in the same paragraphs, so an inserted item such as 5.1.5 (vi) is part of the amendment. A
run of a lead-in ("… as follows:") and one item is cut to the item.

A requirement is flagged only when its own span changed. The dev gold decides this: old 6.5 holds
the source sentences of R-084 to R-090, and only R-084, R-085, R-086 (edited) and R-090 (gone) are
flagged. R-087 to R-089 come from sentences that survive unchanged. A span that only moved,
merged or split is not flagged.

## 4. Change records

- **Modified.** `new_text` is the old requirement with the span's edits applied, as the task
  states. This keeps the requirement's explicit subject: the new 6.6 sentence alone says "The
  test procedures shall …", R-085 says "The accelerator control misapplication test procedures
  shall …". When an edit finds no place in the requirement, `new_text` is the new span.
  Both alternatives cost the last dev row on the platform: the new sentence alone ("The test
  procedures …", no scope) and the old name kept ("The accelerator control misapplication test
  procedures …", a test the new version no longer has).
- **Stale names.** A requirement often names what its paragraph was about, from the paragraph's
  heading ("For the accelerator control misapplication test, …"). When that heading's words
  appear nowhere in the new version, the name is replaced by the system the scope defines
  ("This Regulation applies to … (ACPE)" in section 1) plus the head noun: "ACPE test". Without a
  system defined in the scope only the head noun stays. On R148, R10 and R48 this changes
  nothing.
- **Long texts.** The schema allows 2,000 characters. An old requirement of exactly that length
  was cut mid-clause, so its unfinished last fragment is dropped. A text still too long drops
  whole sub-lists that hold no edit, largest first ("(c) …, i.e.: (i) … (iv) …" becomes
  "(c) …;"), and only then is cut at a sentence boundary. On dev this gives the gold's R-021
  exactly; cutting from the end had lost the amended items.
- **Added.** Rows come only from paragraphs that are new as a whole (a new sentence inside an old
  paragraph is part of that paragraph's amendment) and only in the top-level sections the old
  requirements cite (on dev 3 to 8, which leaves out the transitional provisions of section 12).
  One row per obligation: a sentence with shall, must or may, or with a number and a unit
  (5.1.4.1, 6.5.3); each item under a lead-in with a modal verb; a lead-in without one stays one
  row with its items. The text:
  - lead-in and item are fused: "X shall be as follows:" and "(a) Hold …" give "X shall be to
    hold …";
  - an item with its own modal stands alone, after "During …" when the lead-in names a procedure
    or test;
  - a clause after the last item ("…, as reasonably practical …") applies to every item;
  - a run-in heading ending in "," ("Acceleration while creeping,") becomes the condition ("For
    acceleration while creeping, …");
  - "For X the Y shall A, and may B" gives two rows, "For X the Y shall A." and "X may B.".
- **Removed.** The requirement's span has no new unit anywhere in the new version.

## 4b. The inclusive mode (held-out runs)

`--inclusive` (`run(..., inclusive=True)`) reports every change the diff sees, for recall. The
challenge judges the sub-goal by flag recall and change accuracy, the leaderboard ranks by flag
recall, and change accuracy only counts matched rows, so an extra row costs nothing. On top of
the default it adds:
- added rows from every section, not only the cited ones, and from every new sentence, list
  items and sentences without a modal verb included;
- a requirement whose own sentence is unchanged when its paragraph was amended around it, when it
  moved unchanged to a new number ("was renumbered …; its wording did not change"), or when a
  paragraph below its cited one changed.

The default stays the dev-exact behaviour (100% on dev). On the held-out pair (UN R171) the
default scored flag recall 64.1%; the inclusive steps took it to 78.1%, 81.2% and 84.4%
(`out/subgoal-heldout-inclusive-v7.json`, change accuracy 88.0%).

## 5. Reasons and sources

| Change | Template |
|---|---|
| Modified | `Paragraph {new} of {reg} was amended in version {v}: {edits}.` |
| Modified, moved | `Paragraph {new} (formerly {old}) of {reg} was amended in version {v}: {edits}.` |
| Added | `Paragraph {new} of {reg} is new in version {v}: '{quote}'.` |
| Removed | `Paragraph {old} of {reg} was amended in version {v}; the provision '{quote}' no longer appears.` |

The edit list is a word-level diff of the old and new span, in document order: `'A' became 'B'`,
`'X' was added`, `'Y' was removed`, joined by `; `. An added quote is the obligation's sentence or
item (with a run-in heading in front), cut to 99 characters plus "…" when longer than 100; a
removed quote is the old sentence, cut to 89 plus "…". `source` is the page and label in the new
PDF; removed rows have none. The version comes from `regulations/index.json`, found by the new
PDF's SHA-256, or from `--to-version`.

16 of 24 dev reasons match the gold exactly. The other 8 differ where the gold is not consistent
with itself (edit order, edits it leaves out, three quotes cut at other lengths), so none is
fitted.

## 6. Models

None. Every step is a rule. The gold's new texts read like a model's rewrite; a model could match
their style more closely, but it would stay optional and the rules would stay the default.

## 7. The change monitor

The same engine runs when a new version of a regulation lands, against the requirements of a
saved assessment:

```python
from brain.subgoal import diff_assessment

changes = diff_assessment(old_pdf, new_pdf, requirements, to_version="1.0.0")
```

`changes` is the submission's list of changes (`brain.subgoal.run` wraps it with `team_id` and
`case_id`). Each modified change also carries `old_span` and `new_span`, the text before and
after, so the app can show which sentence changed. `to_version` can be left out when the new PDF
is in `regulations/index.json`:

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

The web app runs it on an assessment's Updates tab (`/a/{id}/updates`): upload a newer PDF of a
cited regulation, or compare with the newest version in the corpus. `web/backend/subgoal_runner.py`
calls `diff_parsed` (the same diff on versions already parsed and aligned) and turns the alignment
links into one hunk per changed paragraph for the page's word diff. Unchanged sentences, formatting
and renumbering are left out, and so is text that only moved within a paragraph. An upload whose
sentences are less than 50% unchanged against the cited version is refused as a different
document. Precomputed runs for the seeded assessments are in `data/regulation-updates/`.

## How it was checked

- Dev: flag recall and change type 100% by `brain.subgoal.score`; on the platform flag recall
  100.0%, flag precision 100.0%, change accuracy 100.0% (six uploads: 87.0, 91.3, 95.7, 95.7,
  95.7, 100.0; what each one taught is in `out/README.md`).
- Six synthetic edits (renumber a section, insert, delete, change a number, split, whitespace
  only) on the base version of all 36 regulations: 216 of 216 found exactly, nothing flagged for
  the renumber, split and whitespace edits.
- Every base and latest pair diffs in under 2 s. R148, R10 and R48 with the main goal's rows as
  old requirements give sensible flags (R48 5.15 "'White' became 'Amber'", the ADS additions).

## Limits

- **Table headers.** In R10 the new parse holds a table header row ("Harmonic number n Maximum
  authorized harmonic current A") that the base parse lacks, which flags 4 requirements. The fix
  belongs in `brain/ingest.py`.
- **Empty input.** `run` reads the regulation from the first old requirement, so an empty
  `requirements_old.json` fails.
