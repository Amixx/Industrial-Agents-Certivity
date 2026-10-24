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
repo owner on 24 Oct (new `brain/brain/subgoal.py` on `brain.ingest`). Plan:
`docs/superpowers/plans/2026-10-24-subgoal-diff.md`.

**Baseline: the existing script on dev** (24 Oct, `main`, before `brain/subgoal.py`). Command:
`uv run --with pymupdf python scripts/diff_regulation.py --old-pdf subgoal/dev/old.pdf --new-pdf
subgoal/dev/new.pdf --requirements subgoal/dev/requirements_old.json --out <file>`, renamed to
the submission schema, then `uv run python -m eval.subgoal_score <file>`:

| Flag recall | Change accuracy | Added recall | Exact reasons | new_text similarity | Extra rows |
|---|---|---|---|---|---|
| 0.708 (17/24) | 1.000 | 0.588 (10/17) | 0.125 | 0.798 | 8 |

All 7 modified and removed ids are right. The losses are in the added rows: 7 missed, 8 extra
(section 12 transitional provisions, 5.1.12, the 6.6.1.2 and 6.6.2.2 lead-ins).
