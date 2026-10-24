# Lane D: Hedged granularity, two cuts per likely paragraph

State: done. Updated: 24 Oct 23:00 CEST.
Approved spend: $2. Spent: $0.82.

No file was nominated. The platform cap was 4 of 5 used this hour, so D4 stops at the local score and the report.

## Checklist

- [x] D1 Natural experiment: union of `rear-lamp-mix.json` (split everything) and
      `rear-lamp-mix-examples-cut.json` (obligation cut), exact duplicates removed. Done 22:46.
      Files: `brain/swing/d_hedge.py`, `out/rear-lamp-swing-D-mix-cut-union.json`. Commit: see
      git log "swing D: steps 1 and 2". Spend $0.
      Found: union 660 rows, 155 matched, F2 0.546 (fine alone 395 / 148 / 0.641, coarse alone
      341 / 145 / 0.658). The cuts share 139 matched gold rows; either matches 154. +7 matches
      for +265 rows (0.03 per row, the break-even is about 0.13).
- [x] D2 Hedge selectively. Done 22:46. Files: `out/rear-lamp-swing-D-mix-cut-{union-near06,
      diff-fine,rel0.5-coarse,rel0.5-or-diff,first-near0.4}.json`,
      `out/rear-lamp-swing-D-fable-mix-first-near0.4.json`, `...-fable-mix-first-near0.5.json`,
      `...-kbjev-mix-first-near0.45.json`. Spend $0.
      Found: no selective hedge of the two Sonnet cuts beats a single cut (best 0.642 at
      relevance 0.6, coarse elsewhere; hedging only on gold paragraphs, an oracle, still loses:
      155 at 551). Hedging a coarser base from another model with the split rows that are not
      near duplicates (similarity < 0.4 to every base row on the paragraph) does win locally:
      Fable + split 359 rows / 150 / 0.670 (from 332 / 141 / 0.646); kb-jev + split
      442 / 164 / 0.682 (from 389 / 153 / 0.666).
- [x] D3 Rebuild the coarse side without examples. Done 22:47. Files: `brain/swing/d_cut.py`,
      `out/rear-lamp-swing-D-cut-noex.json` and `.log`. Spend $0.82 (Sonnet, 23 calls,
      109k in / 60k out; Opus relevance 115 cache hits).
      Check first: `d_cut.py --cut all --dry` reproduces `rear-lamp-mix.json` row for row from
      the cache, so the patch is `b7d6ee2`'s rewrite with only the split rule swapped.
      Found: the cut without examples is better locally than with them: 337 rows, 148 matched,
      F2 0.675 (with examples 341 / 145 / 0.658; split everything 395 / 148 / 0.641). Gold
      paragraphs with more rows than gold: 20 (split: 45). Hedges with the split rewrite:
      union 636 / 159 / 0.569; best selective rel0.6-coarse 351 / 148 / 0.666 (below the cut
      alone); cut + split rows with similarity < 0.45 on the cut's paragraphs
      (`first-near0.45`) 360 / 155 / 0.692, the best local F2 in this lane.
- [x] D4 Save the best hedge, score it locally, read the added rows, write the report.
      Done 23:00. No model calls. Spend still $0.82.
      Files: `out/rear-lamp-swing-D-cutnoex-mix-first-near0.45.json` (best local F2) and
      `out/rear-lamp-swing-D-cutnoex-mix-first-near0.4.json`, each with a `.log`.
      Command, from `brain/`, cache only:
      `BRAIN_LLM= PYTHONPATH=. uv run python swing/d_hedge.py ../out/rear-lamp-swing-D-cut-noex.json ../out/rear-lamp-mix.json --write cutnoex-mix --only first-near0.4 first-near0.45`
      Found: `first-near0.45` is 360 rows, 155 matched, requirement F2 0.692.
      `first-near0.4` is 352 rows, 153 matched, F2 0.688. The cut alone stays 337 / 148 / 0.675.
      Validate passes on both, and on the cut. Regulation F1 stays 1.000 and page F1 stays
      0.860, because the hedge adds rows only on paragraphs the cut already cites.
      All 23 added rows were read. Sixteen match nothing. The seven new matches repeat a
      clause the cut already wrote. No upload nominated.

Next: nothing. The lane is done.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 22:46 | `rear-lamp-swing-D-mix-cut-union.json` | Union of `mix` (split) and `mix-examples-cut`, exact duplicates removed | `big-swings` `d_hedge.py` | 660 | 155 / 0.546 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-union-near06.json` | Same, second-file rows with similarity >= 0.6 to a kept row dropped | same | 439 | 152 / 0.634 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-diff-fine.json` | Both cuts where their row counts differ, split elsewhere | same | 489 | 154 / 0.616 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-rel0.5-coarse.json` | Both cuts where relevance >= 0.5, cut elsewhere | same | 405 | 147 / 0.631 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-rel0.5-or-diff.json` | Both cuts where relevance >= 0.5 or counts differ | same | 508 | 154 / 0.607 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-first-near0.4.json` | Split, plus cut rows with similarity < 0.4 to every split row | same | 408 | 148 / 0.634 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-fable-mix-first-near0.4.json` | Fable, plus split rows with similarity < 0.4, on Fable's paragraphs | same | 359 | 150 / 0.670 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-fable-mix-first-near0.5.json` | Same at < 0.5 | same | 375 | 150 / 0.661 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-kbjev-mix-first-near0.45.json` | kb-jev, plus split rows with similarity < 0.45 | same | 442 | 164 / 0.682 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-cut-noex.json` | `main` pipeline, Opus relevance (cached), Sonnet rewrite with `b7d6ee2`'s prompt and the obligation cut, no expert examples | `big-swings` `d_cut.py` | 337 | 148 / 0.675 | not uploaded | $0.82 |
| 23:00 | `rear-lamp-swing-D-cutnoex-mix-first-near0.4.json` | No-example cut, plus split rows with similarity < 0.4 on the cut's paragraphs | `big-swings` `d_hedge.py` | 352 | 153 / 0.688 | not uploaded | $0 |
| 23:00 | `rear-lamp-swing-D-cutnoex-mix-first-near0.45.json` | Same at similarity < 0.45. Best local F2 in the lane | same | 360 | 155 / 0.692 | not uploaded | $0 |

Requirement matched and F2 are from `uv run python -m eval.score` (lexical judge, 190 expert rows). `tools/score_local.py` does not compute that F2.

## Local metrics

Every `out/rear-lamp-swing-D-*.json` below passed `uv run python ../tools/validate.py` (exit 0). Regulation and page precision, recall and F1 are from `uv run python ../tools/score_local.py`. Requirement matched count and F2 are from `uv run python -m eval.score`. Scored 24 Oct 22:56 CEST from `brain/`.

| File | Validate | Reg P / R / F1 | Page P / R / F1 (cited / expected / matched) | Req matched / F2 |
|---|---|---|---|---|
| `rear-lamp-swing-D-cut-noex.json` | pass, 337 rows | 1.000 / 1.000 / 1.000 | 0.803 / 0.925 / 0.860 (61 / 53 / 49) | 148 / 0.675 |
| `rear-lamp-swing-D-cutnoex-mix-first-near0.4.json` | pass, 352 rows | 1.000 / 1.000 / 1.000 | 0.803 / 0.925 / 0.860 (61 / 53 / 49) | 153 / 0.688 |
| `rear-lamp-swing-D-cutnoex-mix-first-near0.45.json` | pass, 360 rows | 1.000 / 1.000 / 1.000 | 0.803 / 0.925 / 0.860 (61 / 53 / 49) | 155 / 0.692 |
| `rear-lamp-swing-D-mix-cut-first-near0.4.json` | pass, 408 rows | 1.000 / 1.000 / 1.000 | 0.803 / 0.925 / 0.860 (61 / 53 / 49) | 148 / 0.634 |
| `rear-lamp-swing-D-fable-mix-first-near0.4.json` | pass, 359 rows | 1.000 / 1.000 / 1.000 | 0.781 / 0.943 / 0.855 (64 / 53 / 50) | 150 / 0.670 |
| `rear-lamp-swing-D-fable-mix-first-near0.5.json` | pass, 375 rows | 1.000 / 1.000 / 1.000 | 0.781 / 0.943 / 0.855 (64 / 53 / 50) | 150 / 0.661 |
| `rear-lamp-swing-D-kbjev-mix-first-near0.45.json` | pass, 442 rows | 1.000 / 1.000 / 1.000 | 0.781 / 0.943 / 0.855 (64 / 53 / 50) | 164 / 0.682 |
| `rear-lamp-swing-D-mix-cut-union-near06.json` | pass, 439 rows | 1.000 / 1.000 / 1.000 | 0.790 / 0.925 / 0.852 (62 / 53 / 49) | 152 / 0.634 |
| `rear-lamp-swing-D-mix-cut-diff-fine.json` | pass, 489 rows | 1.000 / 1.000 / 1.000 | 0.790 / 0.925 / 0.852 (62 / 53 / 49) | 154 / 0.616 |
| `rear-lamp-swing-D-mix-cut-rel0.5-coarse.json` | pass, 405 rows | 1.000 / 1.000 / 1.000 | 0.790 / 0.925 / 0.852 (62 / 53 / 49) | 147 / 0.631 |
| `rear-lamp-swing-D-mix-cut-rel0.5-or-diff.json` | pass, 508 rows | 1.000 / 1.000 / 1.000 | 0.790 / 0.925 / 0.852 (62 / 53 / 49) | 154 / 0.607 |
| `rear-lamp-swing-D-mix-cut-union.json` | pass, 660 rows | 1.000 / 1.000 / 1.000 | 0.790 / 0.925 / 0.852 (62 / 53 / 49) | 155 / 0.546 |

`eval.score` also prints a page F2 (0.897 on the cut and on both cut-noex hedges, 0.906 on the Fable and kb-jev hedges, 0.894 on the mix-and-example-cut hedges). That is not the score_local page F1.

Same lexical judge, printed by `d_hedge.py` and not saved as their own files, for the no-example cut plus the split rewrite. `first-near0.4` and `first-near0.45` match the table above.

| Keep split rows below similarity | Rows | Matched | F2 |
|---|---|---|---|
| cut alone | 337 | 148 | 0.675 |
| 0.35 | 348 | 153 | 0.690 |
| 0.40 | 352 | 153 | 0.688 |
| 0.45 | 360 | 155 | 0.692 |
| 0.50 | 370 | 155 | 0.686 |
| 0.60 | 387 | 155 | 0.676 |
| union, exact duplicates only | 636 | 159 | 0.569 |

The seven extra matches at 0.45 fall as R148 +3 (46 to 49), R48 +3 (43 to 46), R150 +1 (32 to 33), R10 unchanged (27).

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

None. The hour already had 4 of 5 uploads, so this lane does not add one.

## Notes

- Hedging two cuts of the same model (Sonnet split vs Sonnet cut) does not pay locally: they
  match the same 138 to 139 gold rows and differ on only 15 to 20, half of those on wording,
  not granularity. Even an oracle that hedges only on gold paragraphs loses (155 at 551 rows).
- What pays on the lexical judge is a coarse base plus the split rows that are lexically new
  on the base's own paragraphs (0.2 to 0.33 matches per added row at similarity < 0.4, above
  the 0.13 break-even). The D4 read below says those matches are mostly the judge failing the
  longer sentence, not new obligations. The gain on the earlier Fable and kb-jev hedges
  (R148 +1, R48 +4, R150 +1, R10 +3 for Fable + split) should be read the same way until
  someone checks the added rows against the base text.
- The added rows are chosen for being lexically different, which is what this judge rewards.
  Similarity is also zeroed when one sentence has "not" and the other does not, so a complete
  sentence that adds "need not" or "does not" loses to a shorter copy that omits that clause.
- Transfer: the hedge keeps the base's paragraph set (checked: the 0.45 file cites the same
  paragraphs as `cut-noex`, none added, none dropped). The silver bumper labels are paragraph
  level, so this hedge cannot move paragraph recall or precision on R42, R127, R26 or GTR 9.
  A second rewrite on a bumper was not run: it would be a paid call, and this lane has no
  paid step left.
- `synth-a03` gold is 57 rows (R150, R48). 59 dev gold rows share that text, and all 44
  synth paragraphs are paragraphs the dev gold also cites, so it is not an independent case.
  Restricted to those two regulations, against that gold: cut 191 rows / 45 / 0.537, the 0.45
  hedge 207 / 46 / 0.529, Fable 187 / 43 / 0.518, Fable + split 200 / 44 / 0.514. One more
  match, a lower F2.
- Sunday cost of the method, if anyone still wants it: one extra Sonnet split rewrite of the
  selected paragraphs (about $0.85 and under a minute on the lamp; the D3 cut was 23 calls
  and $0.82) plus `d_hedge.py` (free, seconds). The lamp split is already cached.
- Analysis scripts used for the oracle, sweep and per-regulation numbers were throwaway; the
  numbers above can be regenerated with `d_hedge.py` policies `first-near<t>`.

### D4 read of the added rows

`first-near0.45` adds 23 split rows on 18 paragraphs the cut already cites. All 23 were read
against the cut rows on the same paragraph and against the quote. Sixteen match no expert row.
They are slices of a sentence the cut kept whole: one cell of a luminous-intensity table, the
minimum height taken off a full height range, "shall not be rough" taken off "not rough and
easy to clean", "80° outwards" taken off "45° inwards and 80° outwards", a tell-tale note
already inside the failure alternative, and three slices of one optional-lamp sentence
(vertical distance, 600 mm, and the height clause's neighbours). One added row is a sentence
the cut skipped ("for M1 and N1, no special requirement"); it is not an expert row.

The seven rows that do match are still not new obligations:

1. R148 3.3.1.1.1, "markings shall be clearly legible". The cut already says legible and
   indelible, then adds the marking-space sentence, and the extra tokens pull it to similarity
   0.29. The short row matches at 0.50 and drops "indelible". The cut row itself is unmatched.
2. R148 3.3.3.5, additional symbols after the module identification code. That clause is
   inside the cut's module-code row, which is already matched.
3. R148 3.3.3.5, the approval mark need not be the same but both marks come from the same
   applicant. Same long cut row, already matched.
4. R48 6.7.4.2.1, optional stop lamps at a height compatible with width and symmetry. The cut
   states that sentence and continues with the vertical distance and "not less than 600 mm".
   Token overlap with the short row is 0.40; similarity is 0 because of "not". The cut row is
   already matched.
5. R48 6.10.4.2, the same pattern for optional rear position lamps (overlap 0.46, similarity 0).
   The cut row is already matched.
6. R48 6.10.5.2, the 12.5 cm² unobstructed view. The cut row has that sentence plus "any
   retro-reflector that does not transmit light being excluded" (overlap 0.70, similarity 0
   on "does not"). The cut row is already matched.
7. R150 5.1.4.3, the Class IA or IB illuminating surface inside a 200 mm circle. The cut row
   has that sentence plus the 100 cm² limit and "need not necessarily attain this area"
   (overlap 0.66, similarity 0). The cut row is already matched.

The cut lost none of its 148 matches. The hedge's +7 is the lexical judge scoring a shorter
copy, not seven obligations the coarse cut failed to write.

## Report

A fine cut and a coarse cut of the same paragraphs do not beat the coarse cut alone: the saved union of the split rewrite and the example cut is 660 rows, 155 matches and requirement F2 0.546, the no-example cut alone is 337 rows, 148 matches and F2 0.675, and every both-cuts file in the table above sits below that cut. The best selective hedge, the no-example cut plus split rows under similarity 0.45, reaches 360 rows, 155 matches and F2 0.692, but the read of all 23 added rows found no obligation the cut had missed: 16 match nothing and the other 7 are shorter copies of sentences the cut already wrote, which this judge drops once the longer sentence contains "not" or extra clauses.

The curve is the threshold table in Local metrics. At similarity 0.45 the file is valid, regulation precision, recall and F1 stay 1.000, and page precision, recall and F1 stay 0.803, 0.925 and 0.860 (61 cited, 53 expected, 49 matched), the same pages as the cut. Requirement F2 moves from 0.675 to 0.692. Loosening the gate to a full union of the rebuilt cut and the split rewrite prints 636 rows, 159 matches and F2 0.569, which gives back the gain. No file was nominated for upload.

Transfer. Paragraph sets of the hedge and the cut are the same, so the silver bumper labels (paragraph level, R42, R127, R26, GTR 9) cannot move. On `synth-a03` (57 rows, R150 and R48, text shared with the dev gold) the hedge goes from 45 matches at 191 rows, F2 0.537, to 46 matches at 207 rows, F2 0.529.

Sunday. The method fits the 08:00 to 13:00 window: one extra Sonnet rewrite of the selected paragraphs, about $0.85 and under a minute on a lamp-sized case, then `d_hedge.py` for free. It is not the variant to run. It does not change which paragraphs are cited, and the requirement gain does not survive a second case.
