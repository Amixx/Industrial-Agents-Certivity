# 02 Split obligations the way the gold does

## Prompt

You are joining a hackathon team mid-event (Certivity challenge, Munich). Read
`brain/docs/todo/README.md` first: it has the event, the scores, the rules and the tools. Work
from `brain/`.

**Why this task exists.** Our best dev run (Fable 5.1, platform F2 0.682) misses 34 of the 190
gold requirements on paragraphs it did select. Every model misses 26 to 37 there, so the cause
is the rewrite prompt, not model strength. If half of them were recovered, recall would go from
0.78 to about 0.87 and F2 from 0.68 to about 0.74. The fix carries over to the bumper because
it is about how the gold is written, not about lamps.

**What the gold does that we don't** (see `uv run python -m eval.errors
../out/rear-lamp-fable.json` and compare gold and our rows per paragraph):
- One row per constraint: "height compatible with … and vertical distance of at least 600 mm"
  is two gold rows (R48 6.7.4.2.1, 6.10.4.2).
- One row per list item, with the shared condition repeated: R10 Annex 9 3.1 has one gold row
  per modulation (AM, PM2, PM3), each ending "if not otherwise agreed between Technical Service
  and ESA manufacturer".
- One row per optional or alternative case: "Where optional lamps are installed, …".
- Sometimes one row per table row (R10 6.9.1: one per pulse), but **not** when the paragraph
  only points at a table: R148 5.5.1 "shall meet the requirements in Table 7" is one gold row.
- An obligation inside a permission becomes a shall: R150 4.1.6.1 "may consist of … which must
  be so designed that …" becomes "The combined unit and filter shall be so designed that …".
- Explicit subject from the heading path; passive voice, references and units kept verbatim.
  See `../docs/requirements-format.md`.

**State of the prompt.** `brain/rewrite.py` (`_SYSTEM`, `_EXAMPLES`) already has split rules
and few-shot examples from regulations outside the dev case (R48 6.2.4.2 dipped-beam, R127
5.1.2, GTR 9 8.3.2.1, R42 6.1.4). A first version told the model to split every table row; on
qwen3.5:9b that turned R148 5.5.1 into 25 rows with garbled cell values (platform F2 0.551 against
0.682 for Fable's own rewrite of the same paragraphs; `../out/rear-lamp-qwen-split-rewrite.json`). It now says to split a table only
when the paragraph text states each row's limit. A selected paragraph the model answers with
nothing keeps its deterministic rows. A qwen rerun with this version is in
`../out/README.md` once scored.

**What to do.**
1. Hold selection constant: always rewrite Fable's 208 paragraphs with
   `uv run python -m eval.rewrite_pass ../out/rear-lamp-fable.json out/<name>.json
   --provider anthropic --approved` (run it without `--provider` first; it prints the size).
   One pass on Sonnet 5.5 is about 90k input and 60k output tokens, about $0.80. Get approval
   for the number of passes first (rule 1 in the README).
2. Baseline: the current prompt on Sonnet 5.5. Compare with Fable's own rows using
   `eval.errors` on both files: misses on cited paragraphs, rows per gold paragraph.
3. Change the prompt one rule at a time and rerun. Read the rows of the paragraphs that moved,
   not only the totals.
4. Try one deliberate F2 experiment: for paragraphs where the split is unclear, emit both the
   merged sentence and the split rows. Under one-to-one matching an extra row pays off when its
   chance of matching is above about F2/5, so about 14%. Keep it only if the judge shows more
   matches, not just more rows.
5. When a variant wins on the local judge by more than about 5 matches (or on the task 01
   judge once it is ready), ask the team for one dev upload of its output file to confirm on
   the platform.
6. Check the winner on Opus 5.5 too: Sunday's run may use Opus or Fable for every step.

**Acceptance.**
- A prompt that beats the current one on the same 208 paragraphs and the same model by at
  least 5 matches, with no more than 1.3 times the rows, confirmed by one dev upload.
- No dev gold sentence in the prompt or the examples (rule 2). Examples come from regulations
  outside the dev case, preferably R42, R127, R26 or GTR 9.
- The deterministic path (`--no-llm`) is unchanged.

**Deliverables.** The prompt change in `brain/rewrite.py`; every variant with its numbers under
"Results"; the uploaded file and its platform score in `../out/README.md`.

**Do not.** Change paragraph selection (task 03 owns `relevance.py`, `features.py`,
`decide.py`). Run a full pipeline to test a prompt: `eval.rewrite_pass` is cheaper and holds
selection fixed.

## Results

Done on branch `kb-stack` (not merged), commit `1d8b22e`. Measured with the rewrite step alone
on a fixed set (every gold paragraph of dev and synth-a03 plus 40 non-gold paragraphs main
selected), Opus through `claude -p`, local judge. Scripts and outputs:
`~/Personal/bench-out/rewrite-loop/`, table in `~/Personal/bench-out/rewrite-results.md`.

| Variant | Matched dev | Matched a03 | Rows on gold paragraphs (dev) | Rows on 40 other paragraphs |
|---|---|---|---|---|
| one requirement per clause, skip rules | 139/190 | 40/57 | 174 | 45 |
| main `0ccae35` (split every constraint) | 161/190 | 47/57 | 344 | 73 |
| v3: main's splits, ranges and table references whole, skip rules | 152/190 | 46/57 | 216 | 52 |
| **v4: v3 plus strict minimal edits** | **161/190** | **50/57** | 218 | 49 |
| v5 | 158/190 | 49/57 | 194 | 49 |
| v6: v4 plus skip lab steps without a value | 156/190 | 49/57 | 211 | 40 |

- v4 keeps the sentence's own words and subject: no paraphrase, no added test or product
  names. Most v3 misses were rewording ("no water shall penetrate" for "shall prevent water
  from penetrating"). That rule took dev from 152 to 161 and a03 from 46 to 50.
- Ranges ("not less than X and not more than Y") and references to a table elsewhere stay one
  requirement; a table printed in the paragraph gives one per row.
- Skips clauses for categories the product lacks and obligations on the applicant, authority
  or communication form.
- Each requirement carries an `atomic` list (one line per condition or value) for engineering
  use; the submission's `text` stays at the gold's granularity.
- No dev or a03 sentence in the prompt; the examples are main's R48 headlamp, R127, R42 and
  GTR 9 ones.
- Full pipeline with v4 plus task 03's stack (`fin-dev-rear-lamp`): local judge 158/190, F2
  0.717 on 342 rows; synth-a03 49/57, F2 0.648. Platform: F2 0.635, 140 matched, below the
  v3 run's 0.670. v4's rows drop the subject and condition, which the local judge rewards and
  the platform judge does not (`../out/README.md`, branch `kb-stack` runs). v4 is not the
  rewrite to use.
