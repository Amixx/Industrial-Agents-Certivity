# Lane E: Verbatim anchoring

State: stopped by the master at 22:46 CEST (task handed to Cursor). Updated: 24 Oct 22:46 CEST.
Approved spend: $3. Spent: $1.16 (two Sonnet 5.5 API runs, $0.58 each).

## Checklist

- [x] E1 Candidate sentences of each paragraph of `rear-lamp-fable.json`, from
      `brain.obligations.sentences`, with heading path and parent clause. Done 22:41. Files:
      `out/experiments/E-candidates.json`, `brain/swing/e_verbatim.py`. Commit: see the
      "swing E" commit after 390a2ac.
      Found: 208 paragraphs, 509 sentences.
- [x] E2 A model writes each row as segments: `source` (verbatim from the paragraph),
      `context` (verbatim from the parent clause or heading path), `added` (free words, meant to
      be at most eight: subject or glue). The script checks every source/context segment
      against the text (case-insensitive), snaps near-copies, flags the rest. Done 22:45 (v1 and
      v2). Files: `out/rear-lamp-swing-E-v1.json` + `.log`, `out/rear-lamp-swing-E-v2.json` +
      `.log`. Spend $1.16.
      Found: v1 316 rows, 133 matched locally (F2 0.618); v2 (extra rules) 300 rows, 130
      matched (F2 0.613). Fable on the same paragraphs: 332 rows, 141 matched.
- [ ] E3 Word share against the source and row count against Fable's 332. Partly done: median
      word share 1.000 for both variants (gold 0.966, computed the same way against the gold's
      own paragraph); rows 316 and 300. Not yet: the distribution, and the share of the
      `added` words per row.
- [ ] E4 Every row names its subject and keeps its condition; read 20 rows by hand. Not done.
      Known problems already seen (below).
- [ ] E5 Nominate one file. Not done; no upload nominated.

Next: fix the four problems under Notes in `EXTRA_V2` (or a new `EXTRA_V3` with
`PROMPTS["v3"]`), then rerun (about $0.60 with Sonnet, cached per batch):

```bash
cd brain
BRAIN_LLM=anthropic PYTHONPATH=. uv run python swing/e_verbatim.py run v3 2>&1 | tee ../out/rear-lamp-swing-E-v3.log
BRAIN_LLM= uv run python -m eval.errors ../out/rear-lamp-fable.json ../out/rear-lamp-swing-E-v3.json
BRAIN_LLM= PYTHONPATH=. uv run python swing/e_verbatim.py read ../out/rear-lamp-swing-E-v3.json 20   # E4
```

Resuming a half-finished run: rerun the same `run <variant>` command. Every finished batch
comes back from `brain/data/cache/llm/` at $0; only missing batches are called again. A failed
batch prints "call failed" and is left out of the file, so check "paragraphs answered 208 of
208" in the log before scoring.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 22:43 | `rear-lamp-swing-E-v1.json` | Fable's 208 paragraphs; Sonnet 5.5 writes rows as verbatim segments plus subject/condition (`PROMPTS["v1"]`) | `big-swings`, `brain/swing/e_verbatim.py` | 316 | 133 / 0.618 | not uploaded | $0.58 |
| 22:45 | `rear-lamp-swing-E-v2.json` | as v1 plus rules for telegraphic labels, demonstratives, in-sentence lists, paragraph-wide conditions, imperatives (`PROMPTS["v2"]`) | `big-swings`, `brain/swing/e_verbatim.py` | 300 | 130 / 0.613 | not uploaded | $0.58 |

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

None nominated yet.

## Notes

- `claude -p` returned "Not logged in" for lane agents, so both runs used the API (Sonnet 5.5
  through `brain.llm`, cached). The script logs its own spend (`[cost]` lines in the log).
- The local lexical judge undercounts this style, as the task warned. Example: R10 Annex 10 2,
  v2 writes "The starting profile according to the International Standard ISO 16750-2 shall be
  applied to the supply lines ..." and the judge scores 0.00 against the gold because the gold
  row contains "not" (a later clause) and ours does not; the negation rule zeroes it. Do not
  decide v1 against Fable on the local count alone.
- Where v1/v2 lose against Fable (20 to 23 gold rows Fable matches and v2 does not, 12 the
  other way):
  1. Lists split by the sentence splitter into fragments: R148 3.3.3.5 ("bear the following
     markings. (a) On the light source module(s): (i) ..."). v1 wrote the items with the whole
     lead-in glued on ("In case ..., bear the following markings. (a) On ...: (i) The trade
     name ..."), v2 dropped them all. Fix: tell the model to build "<subject> shall bear <item>"
     with an added subject from the list header, and pass the raw text rather than splitter
     sentences for list-heavy paragraphs.
  2. Telegraphic labels copied into the row in v1 ("shall be Horizontal angle: 45° ...");
     v2 fixed most, not all ("shall be In accordance with paragraph 5.11.").
  3. The device is not inserted where the sentence names none (R148 5.2.7 "The colour of light
     emitted shall be red." in both variants; gold names the rear position lamp).
  4. Gold folds qualifying sentences and whole small lists into one row (R48 5.3 tolerance,
     R48 5.9.2, R48 6.10.8); our one-row-per-sentence rule splits them.
- The added-words limit is not enforced in code; v2 has 564 added words over 67 rows. Check
  that before nominating.
- Assembly drops the period before a segment that starts with "," (fixes "Table 4., except
  that").

## Report

Not written: the lane stopped at E2 on the master's instruction. What there is so far: with
selection fixed at Fable's paragraphs, verbatim rows score 130 to 133 locally against Fable's
141, but the local judge is known to be unreliable for this style, so the question is still
open and needs one upload of a fixed variant (v3).
