# 09 Sub-goal held-out: from 84.4% to 100% flag recall

## Prompt

You are joining a hackathon team on the last morning (Certivity challenge, Munich, Sunday 25 Oct).
Your task is the sub-goal on the **held-out** pair: given the requirements derived from one
version of a UN Regulation and a later version, say which requirements change and why. A diff
engine already exists and scores well; another team scores 100% on every measure, so the gold is
fully reachable. Find what the gold contains that we do not report, and get there with rules
that stay general. Work from the repo root; paths are relative to it.

**Deadline and upload rules (read twice).**
- Uploads close at **13:00 CET**. The platform allows 5 uploads per hour per challenge, shared
  with the team. **On the held-out case the last valid upload counts, not the best.** Our counting
  upload is `out/subgoal-heldout-inclusive-v7.json` (flag recall 84.4%). Never end on an
  experiment: if an experiment scores lower, upload v7 (or the best file) again as the last upload.
- You cannot upload yourself. The repo owner uploads the file you name and pastes back the
  scores. Ask for an upload only with a written expectation ("if X, recall rises to about Y").
- The leaderboard ranks by flag recall. The challenge judges the sub-goal by "the recall of the
  requirements you flagged for change, and the accuracy of the change you state for each one"
  (`docs/CHALLENGE.md`, "How it is judged"). Flag precision is shown but not judged, and change
  accuracy is computed on matched rows only, so an extra row costs nothing.

**Leaderboard at 09:45** (held-out, last valid upload per team):

| # | Team | Flag recall | Change accuracy | Flag precision |
|---|---|---|---|---|
| 1 | Team 1 | 100.0% | 96.7% | 100.0% |
| 2 | Coffee and more | 89.1% | 98.1% | 83.8% |
| 3 | BarelyLegal | 89.1% | 88.7% | 40.1% |
| 4 | **sudo you (us)** | **84.4%** | 88.0% | 23.3% |
| 5 | Farsighted | 79.7% | 89.6% | 35.2% |

Team 1's 100% precision and 100% recall means the gold follows rules that can be reproduced
exactly. That is the strongest hint you have.

**Read first.**
- `docs/CHALLENGE.md`: "The two goals", "3. Sub-goal: the output format", "How it is judged".
- `docs/regulation-change.md`: how our diff works, the inclusive mode, the limits. Short; read it all.
- `brain/docs/todo/05-subgoal.md`: the original task, its Results (every decision with its
  evidence) and the Sunday steps.
- `out/README.md`: the sub-goal run tables ("Sub-goal runs", "Sub-goal held-out runs") and the
  dated sections from "24 Oct, 23:18" onwards. Every upload and what it taught is there.
- `brain/brain/subgoal/` (about 1,300 lines) and `brain/tests/test_subgoal.py` (58 tests).

**The data.**

| Path | What it is |
|---|---|
| `subgoal/dev/` | Dev pair, UN R175 0.1.0 to 1.0.0: `old.pdf`, `new.pdf`, `requirements_old.json` (94), `expected.json` (the gold, 24 changes: 6 modified, 1 removed, 17 added). |
| `subgoal/heldout/` | Held-out pair, UN R171 base to latest (version 2.0.0): `files.json`, `requirements_old.json` (117 requirements, all `UN R171`), `old.pdf` and `new.pdf` (downloaded with `python tools/fetch_regulations.py`; byte-identical to `regulations/pdf/UN_R171/base` and `latest`). No gold. |
| `schemas/submission_subgoal.schema.json`, `tools/validate.py` | The format and the platform's own check (`new_text` at most 2,000 characters). |
| `brain/brain/ingest.py` | The PDF parser both versions go through. Owned by another task: import, do not edit; write needed changes down. |
| `scripts/diff_regulation.py` | The first diff script; superseded, kept for reference. |

Five old requirements cite a paragraph `tb:678427e5ef7cb6895725d6bf` (page 47): the gold's
generator labels tables with ids of that form. Our parser has no such ids.

**The code** (`brain/brain/subgoal/`, commands from `brain/`).

| File | What it does |
|---|---|
| `__init__.py` | `run`, `diff_assessment(old_pdf, new_pdf, requirements, to_version=None, inclusive=False)`, `validate`, `version_of`. |
| `__main__.py` | `uv run python -m brain.subgoal --old-pdf … --new-pdf … --requirements-old … --case-id … --out … [--inclusive]`. Exits 1 if the file fails validation. |
| `text.py` | `bare` (normalised words: "70%" = "70 per cent", "6 seconds" = "6 s", "three" = "3"), `sentences` (units: sentences and list items), `word_ops`, `substantive` (drops spelling variants and footnote markers), `describe`, `quote`, `shorten`, `fit`. |
| `align.py` | `units`, `align` (exact, merged, then similar pairs; same paragraph at 0.5, a one-to-one rewrite in place at 0.4), `kind`. |
| `changes.py` | `map_requirements` (modified and removed rows), `obligations`, `fuse`, `added_changes`, `system_name`, `top`, and the inclusive branches. |
| `score.py` | `uv run python -m brain.subgoal.score <file>`: strict scorer against `subgoal/dev/expected.json`. |
| `survey.py` | `uv run python -m brain.subgoal.survey [--synthetic \| --main-goal "UN R48" …]`. |

**Commands.**

```bash
cd brain
# held-out, the counting mode
uv run python -m brain.subgoal --inclusive --old-pdf ../subgoal/heldout/old.pdf \
  --new-pdf ../subgoal/heldout/new.pdf --requirements-old ../subgoal/heldout/requirements_old.json \
  --case-id subgoal-heldout --out ../out/subgoal-heldout-inclusive-v8.json
uv run python ../tools/validate.py ../out/subgoal-heldout-inclusive-v8.json \
  --requirements-old ../subgoal/heldout/requirements_old.json
# dev must stay exact (default mode): byte-identical to the 100% file
uv run python -m brain.subgoal --old-pdf ../subgoal/dev/old.pdf --new-pdf ../subgoal/dev/new.pdf \
  --requirements-old ../subgoal/dev/requirements_old.json --case-id subgoal-dev --out /tmp/dev.json
cmp /tmp/dev.json ../out/subgoal-dev-det-v6.json
uv run python -m brain.subgoal.survey --synthetic | grep -vc ' ok$'   # must print 0
```

## What was done, and the scores

**Dev** (UN R175; the platform judges `new_text` on the 23 rows that have one). Six uploads; the
code reproduces v6 byte for byte.

| File | Flag recall / precision / change accuracy | What it taught |
|---|---|---|
| `subgoal-dev-det.json` | 100 / 100 / 87.0 | flags right; three texts wrong (R-021 cut at 2,000 characters, a broken fused item, a wrong subject) |
| `-v2` | 100 / 100 / 91.3 | items with their own "shall" stand alone; giving moved requirements the new sentence broke R-085 |
| `-v3` | 100 / 100 / 95.7 | cut long texts by dropping unchanged sub-lists, not the end: R-021 now equals the gold |
| `-v4`, `-v5` | 100 / 100 / 95.7 | the run-in heading was not the cause |
| `-v6` | **100 / 100 / 100** | a name the new version no longer has ("accelerator control misapplication test") becomes the scope's system name ("ACPE test") |

**Held-out** (UN R171). Counts from the percentages: the gold has **64 changes**.

| Upload | File | Rows | Recall | Precision | Change acc. | Matched | What changed |
|---|---|---|---|---|---|---|---|
| (08:3x) | `subgoal-heldout-det-v2.json` | 52 | 59.4% | 73.1% | 94.1% | 38 | default mode after six rules from reading the first output |
| 08:43 | `subgoal-heldout-det-v3.json` | 74 | 60.9% | 52.7% | 91.4% | 39 | +22: requirements unchanged in a paragraph amended around them; only 1 matched, reverted from the default |
| 08:55 | `subgoal-heldout-det-v4.json` | 63 | 64.1% | 65.1% | 94.6% | 41 | +11: new full sentences inside old paragraphs as added rows; 3 matched |
| 09:03 | `subgoal-heldout-inclusive-v5.json` | 153 | 78.1% | 32.7% | 89.1% | 50 | `--inclusive`: added rows from every non-administrative section (Annex 3 and 4: 63 rows), new list items, the v3 rule; 9 matched |
| 09:13 | `subgoal-heldout-inclusive-v6.json` | 228 | 81.2% | 22.8% | 87.5% | 52 | +75: 13 renumbered requirements, 62 sentences without a modal verb or in administrative sections; 2 matched |
| 09:40 | `subgoal-heldout-inclusive-v7.json` | 232 | **84.4%** | 23.3% | 88.0% | 54 | +4: requirements with a changed paragraph below their cited one; 2 matched |

v7 holds 60 modified, 4 removed, 168 added rows. The default mode (`subgoal-heldout-det-v4.json`)
holds 21 modified, 4 removed, 38 added. Each upload's reasoning is in `out/README.md`.

**What did not work, or did not help.**
- Flagging every requirement whose sentence is untouched but whose paragraph was amended (v3):
  1 of 22 matched. The gold flags a requirement only when its own sentence changed, as on dev.
- On dev, giving moved requirements the new sentence instead of their own text with the edits
  applied cost a row: the bare new sentence loses the subject's scope.
- On dev, dropping the run-in heading from added texts changed nothing (95.7% before and after).
- References to renumbered paragraphs: no old requirement cites a paragraph that moved.
- Recurring terminology replacements: none (only "definitely" to "definitively" three times).
- Of the 57 requirements still unflagged in v7, only 4 had any change in or below their cited
  paragraph, and v7 already added those. For the rest our diff sees no change at all.

## Where the last 10 gold rows probably are

Nobody has looked at these with fresh eyes. Check each against the data before you build.
1. **Tables.** The gold cites tables by `tb:` ids, and our parser flattens table text into the
   paragraph (`brain/ingest.py`). Changes inside tables (7.2.3.1's reporting table, the
   5.5.4.2.6.5.4 timing table, the Annex 3 Appendix 4 capability table on page 47 that
   R-113 to R-117 cite) may be gold rows, labelled by a table id, that we report under a
   paragraph label or not at all. Find how a `tb:` id is formed (its 24 hex characters; look at
   the dev package and `regulations/` for other occurrences) and whether we can produce it.
2. **Added-row granularity and labels.** We report 168 added rows; the gold's added rows are
   matched one to one, probably by paragraph and text. If the gold splits a sentence into two
   obligations where we report one (dev did: "shall be deactivated if necessary, and may be
   combined" gave two rows), or labels a row with a parent or child paragraph, we miss it. Compare
   our dev added rows with `subgoal/dev/expected.json` for every splitting rule; apply them all.
3. **Modified vs removed and moved.** Our 4 removed rows (R-023, R-025, R-036, R-066) and the
   13 renumbered rows: the gold may count some as modified with a different paragraph, which
   matters for change accuracy (88.0% means about 6 matched rows have the wrong change or text).
4. **Change accuracy.** 88.0% on about 50 rows with `new_text`. The dev lessons hold: keep the
   requirement's own subject, apply the edits, and replace names the new version dropped.

**Using the uploads.** Each upload returns the number of matched rows (precision times rows).
Because extra rows are free, the safe experiment is v7 plus a new bucket of candidate rows: if
recall rises, keep the bucket. Never remove v7 rows in an experiment you might end on.

## Rules

- No paid model calls without the repo owner's approval and a cost estimate (`CLAUDE.md`; the
  provider is off unless `BRAIN_LLM` is set). No model is the goal.
- Keep the default mode dev-exact: `cmp` with `out/subgoal-dev-det-v6.json` after every change,
  and the synthetic edits at 216 of 216. Held-out-only rules go behind `--inclusive`.
- Every new rule is general (no labels, ids or strings from R171 or the dev gold in the code) and
  gets a test in `brain/tests/test_subgoal.py`, written first.
- Record every run in `out/README.md` before you report it: a row in "Sub-goal held-out runs"
  and a dated section (date and time CEST, commit, method, row count, platform scores when
  uploaded). Commit the results with the code that produced them.
- Before every commit, from `brain/`: `uv run pytest -q`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy`. Commit to `main`; pull first; never force push.
- Do not edit `brain/brain/ingest.py`; write needed parser changes down for its owner.
- Docs and commit messages follow `DESIGN.md`, including its list of AI-isms.

## Acceptance

- A held-out upload with flag recall above 84.4% (100% is the target), its scores recorded.
- The counting upload at 13:00 is the best file, not an experiment.
- Dev unchanged (100% on all three by the platform; `cmp` passes), all tests green.

## Results

(fill in)
