# Lane D: Hedged granularity, two cuts per likely paragraph

State: stopped by the master at D4 (task handed to Cursor). Updated: 24 Oct 22:48 CEST.
Approved spend: $2. Spent: $0.82.

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
      (`first-near0.45`) 360 / 155 / 0.692, the best local F2 in this lane. Not yet saved as a
      file.
- [ ] D4 Nominate the best hedged file, prediction first.

Next (D4, all free, no model calls):
1. Save the best hedge from `brain/`:
   `BRAIN_LLM= PYTHONPATH=. uv run python swing/d_hedge.py ../out/rear-lamp-swing-D-cut-noex.json ../out/rear-lamp-mix.json --write cutnoex-mix --only first-near0.4 first-near0.45`
   (expect 352 / 153 / 0.688 and 360 / 155 / 0.692).
2. Read 20 of the added split rows by hand (are they real extra obligations or rewordings?).
3. Nominate, prediction first. Candidates: `rear-lamp-swing-D-cutnoex-mix-first-near0.45.json`
   (my proposal: predict platform about 150 matched, F2 0.67; the cut style lost 7 against the
   local judge on its one upload, the split rows probably gain a little) and, as the question
   "does a cheap hedge lift the best file", `rear-lamp-swing-D-fable-mix-first-near0.4.json`
   (359 rows, local 150; predict platform about 151, F2 0.675). Also worth a plain upload of
   `rear-lamp-swing-D-cut-noex.json` alone (local 148 / 0.675): it answers whether the cut
   lost on the platform because of the examples or because of the cut.
4. Transfer check, then the report (Rules, item 5).

Nothing is half-finished: the only paid run (D3) completed and is saved. No paid step is left
in this lane.

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

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

## Notes

- Hedging two cuts of the same model (Sonnet split vs Sonnet cut) does not pay locally: they
  match the same 138 to 139 gold rows and differ on only 15 to 20, half of those on wording,
  not granularity. Even an oracle that hedges only on gold paragraphs loses (155 at 551 rows).
- What pays is a coarse base plus the split rows that are lexically new on the base's own
  paragraphs (0.2 to 0.33 matches per added row at similarity < 0.4, above the 0.13
  break-even). More than half of the new matches fall on paragraphs where the base has fewer
  rows than the gold. The gain is spread over all four regulations (Fable + split: R148 +1,
  R48 +4, R150 +1, R10 +3).
- Caveat: the added rows are chosen for being lexically different, which is exactly what the
  lexical judge rewards. The platform judge may already credit the base's paraphrase, so
  expect about half the local gain there. Only an upload settles it.
- Transfer: the hedge keeps the base's paragraph set, so the silver bumper labels (paragraph
  level) are unchanged by construction. `synth-a03`'s gold is 57 dev gold rows (R150, R48), so
  it is not independent: restricted to those regulations, Fable + split goes 187 / 43 / 0.518 to
  200 / 44 / 0.514, kb-jev + split 179 / 46 / 0.565 to 217 / 48 / 0.539 (neutral to negative).
  A real transfer check needs two rewrites on a bumper case (about $0.85 per Sonnet rewrite,
  plus relevance if not cached); not run.
- Sunday cost of the method: one extra Sonnet split rewrite of the selected paragraphs
  (about $0.85 and 30 s on the lamp) plus `d_hedge.py` (free, seconds).
- Analysis scripts used for the oracle, sweep and per-regulation numbers were throwaway; the
  numbers above can be regenerated with `d_hedge.py` policies `first-near<t>`.

## Report
