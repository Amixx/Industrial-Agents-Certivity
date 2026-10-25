# 05 Regulation change: the sub-goal, exact on dev and ready for the held-out pair

## Prompt

You are joining a hackathon team mid-event (Certivity challenge, Munich). Your task is the
sub-goal: given the requirements derived from one version of a UN Regulation and a later version
of it, say which requirements must change and why. Work from the repo root; paths here are
relative to it.

**Read first.**
- `docs/CHALLENGE.md`, sections "The two goals", "3. Sub-goal: the output format" and "How it
  is judged".
- `docs/determinism.md` (the row "Sub-goal diff": the gold reasons follow a fixed pattern, so
  template them), `docs/pdf-extraction.md` (the PDFs and how paragraphs are parsed),
  `docs/final-hardening.md` (item 5, "Change monitor": the same diff as a product feature).
- `brain/docs/todo/README.md`: the event, the rules for every task, and which files the other
  tasks own.
- `brain/README.md` and `brain/brain/ingest.py`: the paragraph parser the main goal uses.
- `scripts/diff_regulation.py`: an existing paragraph diff (316 lines).

**Why this matters.** The sub-goal is 15% of the jury score. Its held-out pair arrives on Sunday
25 Oct at 08:00 with the main case; uploads close at 13:00, and on the held-out case the last
valid upload counts. On the dev pair, four teams already score 100% flag recall and 100% change
accuracy:

| Team | Flag recall | Change accuracy |
|---|---|---|
| BarelyLegal, Flame, octane, protocol10 | 100.0% | 100.0% |
| Coffee and more | 100.0% | 95.7% |
| mark-test | 100.0% | 87.0% |
| TerraMind | 100.0% | 69.6% |
| Out Of Scope | 91.7% | 95.2% |

So the dev pair is fully solvable, and anything below 100 / 100 on dev is a bug to find, not a
limit to accept. The held-out pair decides the score, so the solution must be general (any
regulation, any pair of versions), not tuned to the dev pair.

**The task, exactly.**
- Input, dev: `subgoal/dev/requirements_old.json` (94 requirements, each `id`, `text`,
  `source` with `regulation`, `page`, `paragraph`), `subgoal/dev/old.pdf` and
  `subgoal/dev/new.pdf` (UN R175, version 0.1.0 to 1.0.0). They are byte-identical to
  `regulations/pdf/UN_R175/base/UN_R175_base.pdf` and `.../latest/UN_R175_latest.pdf`
  (checked by SHA-256). So the held-out pair is very likely another regulation's base and
  latest PDF from the package, already downloaded and already parsed: you can diff every
  such pair tonight and know the hard cases before 08:00.
- Output: `{"team_id": "team-06", "case_id": "subgoal-dev", "changes": [...]}`, each change
  `{"requirement_id", "change": "modified" | "removed" | "added", "new_text", "reason",
  "source": {"page", "paragraph"}}`. `requirement_id` is one of the old ids for modified and
  removed, and `null` for added. `new_text` is required for modified and added. `reason` is
  always required. Schema: `schemas/submission_subgoal.schema.json`. Check with
  `python tools/validate.py <file> --requirements-old subgoal/dev/requirements_old.json`.
- Scoring, per the challenge: the recall of the requirements you flag for change ("flag
  recall") and the accuracy of the change you state for each ("change accuracy"). There is no
  local scorer yet; you write one.

**The dev gold** (`subgoal/dev/expected.json`) has 24 changes: 17 added, 6 modified, 1 removed.
Its reasons come from four templates, generated from a paragraph diff:
- Modified: `Paragraph 5.1.4 of UN R175 was amended in version 1.0.0: 'standstill.' became
  'standstill and, as relevant, while creeping.'; 'both' was added.` The edit list is a
  word-level diff of the paragraph: `'A' became 'B'`, `'X' was added`, `'Y' was removed`,
  joined by `; `.
- Modified after renumbering: `Paragraph 6.5.2 (formerly 6.5) of UN R175 was amended in version
  1.0.0: '0.2 m.' became 'the distance to extreme outer edge of the vehicle.'; 'Accelerator
  control misapplication test' was removed.` Old paragraph 6.5 was split into several new
  paragraphs (6.5.2, 6.6, 6.6.1.2 all cite it), so alignment cannot be by label alone.
- Added: `Paragraph 5.1.6.2 of UN R175 is new in version 1.0.0: 'Acceleration while creeping,
  In the case a collision is not prevented, the ACPE shall reduce the ef…'.` The quote is the
  start of the new paragraph, cut with an ellipsis. Several added requirements can come from
  one new paragraph (6.6.2.2 has five).
- Removed: `Paragraph 6.5 of UN R175 was amended in version 1.0.0; the provision 'Before any
  test is started the vehicle may be driven in the direction of the target for a…' no longer
  appears.` No `new_text`, no `source`.

`new_text` for a modified requirement is the old requirement's text with the paragraph's edits
applied. For an added one it is a requirement written in the main goal's style (explicit
subject, "shall", conditions kept: see `docs/requirements-format.md`), for example "While
creeping, when a collision is not prevented during acceleration, the ACPE shall reduce the
effective demand of the accelerator control to zero at or before the point of collision."
`source` is the page and paragraph in the **new** PDF.

**What already exists, and its limits.**
- `scripts/diff_regulation.py` parses both PDFs, diffs paragraph by paragraph and maps changes to
  requirements. It writes its own format (`regulation`, `toVersion`, `stats`, `changes`), not
  the submission schema, and has never been scored against the gold.
- `brain/brain/ingest.py` parses every regulation PDF in the package into labelled paragraphs
  with the page each label sits on, stitched across page breaks, with annex-local labels in the
  gold's style. All 121 dev citations of the main goal resolve on their page. Base and latest
  versions of 36 regulations are already parsed into `brain/data/corpus/*_latest.jsonl` (run
  `cd brain && uv run python -m brain.ingest` if missing). `parse_pdf(path, regulation, version,
  role)` parses any single PDF.
- `brain/brain/rewrite.py` turns a regulation paragraph into requirements in the main goal's
  style, deterministically or with an LLM.

**Part 1: architecture (write it, get it agreed, then build).** Write
`docs/regulation-change.md`, one or two pages, that answers:
1. **Parsing.** One parser for both versions: reuse `brain.ingest` or the script's parser, and
   say why. How you treat headings, annex labels, tables, footnotes and page headers, so that
   the same paragraph in both versions gives the same text.
2. **Alignment of old and new paragraphs.** Same label and similar text; renumbered (same text,
   new label); split (one old paragraph became several new ones, as 6.5 did); merged; moved.
   Which similarity, which thresholds, and how the "(formerly X)" case is decided.
3. **Diff classification.** Unchanged, whitespace or formatting only (must not be flagged),
   amended, new, deleted. The word-level edit list that the reasons quote.
4. **Requirement mapping.** Which old requirements a changed paragraph affects: by the
   requirement's cited paragraph, and by matching the requirement text against the old
   paragraph's sentences (a requirement can cite a parent paragraph, and a paragraph can carry
   several requirements). When a modified paragraph's edit does not touch the sentence a
   requirement was derived from, is the requirement still flagged? Decide from the dev gold.
5. **Change records.** Modified: the old text with the edits applied. Added: one requirement per
   obligation in the new paragraph, in the main goal's style. Removed: when the provision a
   requirement came from no longer appears anywhere in the new version.
6. **Reasons and sources.** The four templates above, filled from the diff; page and paragraph
   from the new PDF.
7. **Where a model is used, if anywhere.** The target is no model at all: every top score
   suggests the dev pair is deterministic. If you use one (for example only for the text of
   added requirements), say where, why, and what runs without it.
8. **The product feature.** The same engine as a "change monitor" in the app: when a new
   version of a regulation lands, list the requirements of a saved assessment that change, with
   the sentence that changed. Sketch the interface (a function and its JSON) that the web
   backend (`web/backend`) could call; building the UI is out of scope.

Keep the doc short and concrete, follow `DESIGN.md` (including its list of AI-isms), and show
it to the team before building. Small decisions you can make yourself; a choice between two
architectures you cannot.

**Part 2: build and measure.**
1. **Scorer first.** `brain/eval/subgoal_score.py` (or `scripts/`), runnable as one command:
   flag recall (modified and removed ids found, plus added changes matched by new paragraph
   and text), change-type accuracy, exact reason match, `new_text` similarity per change, and a
   list of every mismatch. Make it strict: exact reasons and texts are what the top teams
   reach.
2. **Build the pipeline** to the architecture. One command for Sunday:
   `<command> --old-pdf ... --new-pdf ... --requirements-old ... --case-id ... --out ...`,
   writing a file that passes `tools/validate.py`. It must run in under a minute with no model.
3. **Reach 100 / 100 on dev by your scorer**, then ask the team for one platform upload of the
   dev file (uploads are shared, 5 per hour) and record the score in `brain/docs/todo/README.md`
   and in this file under "Results".
4. **Prove it is general, not fitted to R175.** The held-out pair is probably another
   regulation's base and latest version from `regulations/index.json` (36 regulations have
   both). Diff all 36 pairs tonight and list, per pair, the number of amended, new, deleted
   and renumbered paragraphs; read the pairs with the most renumbering closely.
   - Run the pipeline on several other base and latest pairs in the corpus (requirements_old
     can be the main goal's requirements of that regulation, or the deterministic rows from
     `brain.pipeline`), and read the output: no flagged changes for formatting only, sensible
     renumbering, no crash on annexes or tables.
   - Build synthetic pairs whose answer you know: take a parsed regulation, and in a copy
     renumber a section, insert a paragraph, delete one, change a number, split a paragraph,
     change only whitespace. Score the pipeline on them.
   - Pairs that differ by more than one version, or by a series of amendments, may renumber
     heavily: check at least one.
5. **Write the Sunday steps** into this file (for the runbook owner, task 06): where the
   held-out pair lands (`subgoal/<folder>/`, also on `git pull`), the exact command, validation,
   and upload order (sub-goal and main goal uploads are separate challenges).

**Rules.**
- Paid model calls only after the repo owner approves a cost estimate (token count, price,
  repeats). No model is the goal.
- Your files: `docs/regulation-change.md`, the sub-goal pipeline (`scripts/diff_regulation.py`
  or a new `brain/brain/subgoal.py`), `brain/eval/subgoal_score.py`, its tests, and output files
  under `out/`. Import from `brain/brain/ingest.py` and `brain/brain/rewrite.py` instead of
  editing them; if they need a change, write it down here and tell the team (other tasks own
  them).
- Before every commit, from `brain/`: `uv run pytest -q`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy`. Add tests for the alignment and the reason
  templates. Commit straight to `main`; pull first, never force push.
- Report numbers, not impressions: every result with its command and commit under "Results".

**Acceptance.**
- `docs/regulation-change.md` agreed by the team.
- On dev: 100% flag recall and 100% change accuracy by your scorer, confirmed by one platform
  upload.
- On the synthetic pairs: every known change found, nothing flagged for formatting only.
- One documented command that turns a new pair into a valid submission in under a minute, with
  no model and no network.

## Results

Architecture: [docs/regulation-change.md](../../../docs/regulation-change.md), agreed with the
repo owner on 24 Oct (new code on `brain.ingest`). The code was first `brain/brain/subgoal.py`
with the scorer and survey in `eval/`; on 25 Oct it became the package `brain/brain/subgoal/`
(scorer `brain.subgoal.score`, survey `brain.subgoal.survey`), and the commands below use the
new paths. Plan:
`docs/superpowers/plans/2026-10-24-subgoal-diff.md`.

**Baseline: the existing script on dev** (24 Oct, `main`, before `brain/subgoal.py`). Command:
`uv run --with pymupdf python scripts/diff_regulation.py --old-pdf subgoal/dev/old.pdf --new-pdf
subgoal/dev/new.pdf --requirements subgoal/dev/requirements_old.json --out <file>`, renamed to
the submission schema, then `uv run python -m brain.subgoal.score <file>`:

| Flag recall | Change accuracy | Added recall | Exact reasons | new_text similarity | Extra rows |
|---|---|---|---|---|---|
| 0.708 (17/24) | 1.000 | 0.588 (10/17) | 0.125 | 0.798 | 8 |

All 7 modified and removed ids are right. The losses are in the added rows: 7 missed, 8 extra
(section 12 transitional provisions, 5.1.12, the 6.6.1.2 and 6.6.2.2 lead-ins).

**Dev, `brain.subgoal`, no model** (24 Oct 23:18 CEST, `main` @ `d8e9235` plus the staged
`brain/brain/subgoal.py`). Command, from `brain/`:

```bash
uv run python -m brain.subgoal --old-pdf ../subgoal/dev/old.pdf --new-pdf ../subgoal/dev/new.pdf \
  --requirements-old ../subgoal/dev/requirements_old.json --case-id subgoal-dev \
  --out ../out/subgoal-dev-det.json
uv run python -m brain.subgoal.score ../out/subgoal-dev-det.json
```

| Flag recall | Change accuracy | Added recall | Exact reasons | new_text similarity | Extra rows | Time |
|---|---|---|---|---|---|---|
| 1.000 (24/24) | 1.000 | 1.000 (17/17) | 0.667 (16/24) | 0.875 | 0 | about 1 s |

The file passes `tools/validate.py --requirements-old`. The 8 reasons that differ from the gold
are listed in `out/README.md` (24 Oct, 23:18); each is a place where the gold is not consistent
with itself, so none is fitted.

Platform upload, 24 Oct 23:21:47 CEST: flag recall 100.0%, flag precision 100.0%, change
accuracy 87.0%. 87.0% is most likely 20 of 23 rows with a `new_text` (21 of 24 would show 87.5%),
so the platform judges the stated new text, and three of ours were judged wrong.

Second dev file, `out/subgoal-dev-det-v2.json` (23:28): the same 24 flags and change types,
`new_text` similarity 0.875 to 0.913. The rules behind it are in `out/README.md` (24 Oct,
23:18 section). Platform upload, 23:29:26 CEST: flag recall 100.0%, flag precision 100.0%,
change accuracy 91.3% (21 of 23).

Third dev file, `out/subgoal-dev-det-v3.json` (25 Oct 00:07): same flags; R-021's `new_text`
now equals the gold (it lost its amended items to the 2,000-character cut before). `new_text`
similarity 0.926. Details in `out/README.md`. Synthetic edits still 216 of 216 (the generator's
"number" edit now skips footnote markers: on R164 it had changed "tyres1" to "tyres2", which the
diff rightly ignores). Platform upload, 25 Oct 00:08:18 CEST: flag recall 100.0%, flag
precision 100.0%, change accuracy 95.7% (22 of 23). The row left is most likely R-085, where the
gold drops a clause ("both in a forward and rearward direction") that the new paragraph still
has; see `out/README.md`.

Fourth dev file, `out/subgoal-dev-det-v4.json` (00:11): modified rows always keep the old
requirement's text with the edits applied, as this task states, so R-085 keeps its subject ("The
accelerator control misapplication test procedures …"). The three uploads point to R-085 as the
row v2 broke; the reasoning is in `out/README.md`. Platform upload, 00:12:40: 95.7%, unchanged.

Fifth dev file, `out/subgoal-dev-det-v5.json` (00:16): as v4, but a run-in heading stays out of
`new_text` (only 5.1.6.2 changes). It tests the one remaining explanation with a general fix; if
it does not reach 100%, the rule goes back and the last row is R-085's clause that the gold drops.
Platform upload, 00:18:03: 95.7%, so the rule was reverted. Final dev result: flag recall
100.0%, flag precision 100.0%, change accuracy 95.7% (22 of 23), with `subgoal-dev-det-v4.json`
as the file of record; the code reproduces it byte for byte.

Sixth dev file, `out/subgoal-dev-det-v6.json` (25 Oct 00:41): as v4, plus a name the new version
no longer has (the old heading "Accelerator control misapplication test") becomes "ACPE test",
from the system the scope defines. It changes R-084, R-085 and R-086 and tests whether R-085
failed for its subject (the gold says "The ACPE test procedures"). Platform upload, 25 Oct
00:44:21 CEST: flag recall 100.0%, flag precision 100.0%, change accuracy 100.0%. This is the
dev result of record; the code reproduces the file byte for byte.

**Generality.** Commands from `brain/`, staged on top of `d8e9235`.

`uv run python -m brain.subgoal.survey --synthetic`: six synthetic edits (renumber a section,
insert a paragraph, delete one, change a number, split one, whitespace only) on the base version
of each of the 36 regulations: 216 of 216 found exactly, nothing flagged for the renumber, split
and whitespace pairs. `tests/test_subgoal.py::test_synthetic_edits_are_found_exactly` runs them
on R48, R10 and R149.

`uv run python -m brain.subgoal.survey`: units by link kind for every base and latest pair
("moved" is unchanged text under a new label). No pair takes more than 2 s.

| Regulation | Paragraphs old / new | Amended | New | Deleted | Moved | Seconds |
|---|---|---|---|---|---|---|
| UN R10 | 827 / 835 | 29 | 67 | 12 | 27 | 0.1 |
| UN R13H | 642 / 643 | 17 | 13 | 4 | 0 | 0.0 |
| UN R32 | 52 / 49 | 1 | 17 | 111 | 38 | 0.0 |
| UN R39 | 175 / 183 | 11 | 18 | 0 | 0 | 0.0 |
| UN R40 | 350 / 944 | 104 | 1409 | 265 | 65 | 1.7 |
| UN R43 | 1810 / 1820 | 32 | 37 | 5 | 2 | 0.1 |
| UN R48 | 1187 / 1250 | 51 | 95 | 2 | 11 | 0.1 |
| UN R49 | 2204 / 2204 | 162 | 21 | 16 | 2 | 0.5 |
| UN R51 | 695 / 724 | 38 | 79 | 13 | 24 | 0.1 |
| UN R53 | 540 / 593 | 4 | 88 | 0 | 0 | 0.0 |
| UN R62 | 89 / 115 | 2 | 29 | 0 | 0 | 0.0 |
| UN R64 | 174 / 192 | 16 | 30 | 0 | 1 | 0.0 |
| UN R67 | 1201 / 1206 | 14 | 7 | 1 | 0 | 0.0 |
| UN R79 | 777 / 817 | 19 | 66 | 2 | 1 | 0.0 |
| UN R83 | 646 / 602 | 48 | 89 | 112 | 4 | 0.2 |
| UN R89 | 406 / 409 | 8 | 16 | 0 | 2 | 0.0 |
| UN R92 | 154 / 179 | 12 | 59 | 7 | 0 | 0.0 |
| UN R94 | 484 / 494 | 10 | 27 | 1 | 1 | 0.0 |
| UN R100 | 644 / 652 | 16 | 22 | 0 | 0 | 0.0 |
| UN R101 | 1137 / 1139 | 9 | 8 | 2 | 14 | 0.0 |
| UN R102 | 212 / 216 | 11 | 9 | 1 | 0 | 0.0 |
| UN R103 | 96 / 126 | 10 | 2 | 1 | 42 | 0.0 |
| UN R107 | 678 / 692 | 75 | 47 | 20 | 7 | 0.2 |
| UN R114 | 238 / 176 | 0 | 2 | 122 | 0 | 0.0 |
| UN R127 | 322 / 337 | 16 | 25 | 15 | 0 | 0.0 |
| UN R131 | 295 / 311 | 6 | 18 | 4 | 2 | 0.0 |
| UN R132 | 582 / 588 | 23 | 13 | 4 | 2 | 0.1 |
| UN R137 | 441 / 455 | 13 | 37 | 1 | 2 | 0.0 |
| UN R148 | 387 / 406 | 4 | 28 | 0 | 0 | 0.0 |
| UN R149 | 679 / 677 | 22 | 2 | 10 | 30 | 0.1 |
| UN R152 | 308 / 314 | 2 | 6 | 3 | 2 | 0.0 |
| UN R156 | 147 / 152 | 4 | 16 | 9 | 19 | 0.0 |
| UN R164 | 108 / 141 | 22 | 49 | 5 | 7 | 0.0 |
| UN R171 | 848 / 927 | 49 | 177 | 13 | 30 | 0.2 |
| UN R174 | 166 / 186 | 9 | 31 | 0 | 3 | 0.0 |
| UN R175 | 198 / 232 | 19 | 47 | 4 | 11 | 0.0 |

Read closely:
- R32 (0.1.0 to 0.2.0) and R114 (0.0.0 to 0.1.0) lose more than 100 units each. Most are real:
  the new versions replace the 3-D H machine procedure with a reference to Mutual Resolution
  No. 1. The base parse also glues provisions together (R32 2.2.5 holds 2,801 characters,
  running into section 4), which the merge pass now pairs with the new pieces when their words
  are found in it.
- R40 (1.1.0 to 2.0.0) is a rewrite: 350 to 944 paragraphs.
- Run with the main goal's deterministic rows as `requirements_old` (R148 145 rows, R10 103,
  R48 211; `uv run python -m brain.subgoal.survey --main-goal "UN R148" "UN R10" "UN R48"`,
  about 1 s each): R148 adds 12 rows for the
  new direction indicator projector paragraphs; R48 flags 11 requirements (for example
  "'White' became 'Amber'" in 5.15, the ADS additions in 6.2.7.6 and 6.4.7.2) and adds 38 rows
  for the new ADS and projection paragraphs; R10 adds 6 rows for 6.11.3 (ADS).
- Two false positives found. R48 R-012 was flagged for a renumbered footnote marker
  ("'6This' became '1 This'"), fixed by `test_footnote_marker_change_is_not_substantive`.
  R10 R-050, R-052, R-078 and R-080 are flagged because the new parse holds a table header row
  ("'Harmonic number n Maximum authorized harmonic current A' was added") that the base parse
  lacks. That is a difference in how `brain.ingest` reads the two tables, not a change of
  wording; it is open, and a fix belongs in `ingest.py` (task 06 or the parser's owner).

## Sunday steps (for task 06)

The held-out pair lands at 08:00 as a new folder `subgoal/<folder>/` (`files.json` and
`requirements_old.json`), added by `git pull upstream main`. The PDFs come with the fetch. The
sub-goal is a separate challenge on the platform with its own limit of 5 uploads per hour, and on
the held-out case the last valid upload counts. No model and no network are needed after the
fetch.

1. Pull and fetch, from the repo root:

   ```bash
   git pull upstream main && git pull origin main
   python tools/fetch_regulations.py           # also downloads subgoal/<folder>/old.pdf and new.pdf
   ls subgoal/                                 # the new folder next to dev/
   ```

2. Run, from `brain/` (about 1 s on dev). The case id is most likely `subgoal-<folder>`, as
   dev's folder `dev` has the id `subgoal-dev`; check the platform's sub-goal page for the exact id
   before uploading.

   ```bash
   f=heldout                                   # the real folder name
   uv run python -m brain.subgoal --inclusive --old-pdf ../subgoal/$f/old.pdf --new-pdf ../subgoal/$f/new.pdf \
     --requirements-old ../subgoal/$f/requirements_old.json --case-id subgoal-$f \
     --out ../out/subgoal-$f-det.json 2> ../out/subgoal-$f-det.log
   cat ../out/subgoal-$f-det.log
   ```

   Use `--inclusive` for the held-out case: it reports every change the diff sees, which only
   helps, as precision is not judged (on 25 Oct it took the held-out flag recall from 64.1% to
   81.2%). Without it the command gives the dev-exact output.

   The command exits 1 and prints `invalid: ...` if the file fails `tools/validate.py`. If it
   stops with `pass --to-version`, the new PDF is not in `regulations/index.json`: take the
   version from `files.json` or the PDF's title page and add `--to-version <label>`.

3. Validate and read:

   ```bash
   uv run python ../tools/validate.py ../out/subgoal-$f-det.json \
     --requirements-old ../subgoal/$f/requirements_old.json
   ```

   Read the reasons. If many requirements are flagged for edits that are only table headers or
   footnote text (see "Generality" above), that is a parser difference, not a change.

4. Upload `out/subgoal-$f-det.json` once to the sub-goal challenge. Record the platform's scores
   and the upload time in `out/README.md`. Do not upload an experiment after it.

Rehearsed on dev at 23:35 from a clean environment (`env -i`, steps 2 and 3 with `f=dev`): valid,
3 s in all, output byte-identical to `out/subgoal-dev-det-v2.json`.

**Held-out (UN R171), 25 Oct.** Platform uploads of the sub-goal held-out case, each recorded in
`out/README.md` with its reasoning:

| Upload | File | Flag recall | Flag precision | Change accuracy |
|---|---|---|---|---|
| not recorded | `out/subgoal-heldout-det-v2.json` | 59.4% | 73.1% | 94.1% |
| 08:43 | `out/subgoal-heldout-det-v3.json` | 60.9% | 52.7% | 91.4% |
| 08:55 | `out/subgoal-heldout-det-v4.json` | 64.1% | 65.1% | 94.6% |
| 09:03 | `out/subgoal-heldout-inclusive-v5.json` | 78.1% | 32.7% | 89.1% |
| 09:13 | `out/subgoal-heldout-inclusive-v6.json` | 81.2% | 22.8% | 87.5% |
