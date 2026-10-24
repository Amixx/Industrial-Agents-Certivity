# 08 Complex strategies: build on the swing results

## How to use this file

Two roles read this file:

- **The master**: a fresh chat told "read `brain/docs/todo/08-complex.md` and act as the master".
  It follows **Master protocol**, starts one lane agent per lane, keeps
  `out/experiments/STATUS-08.md` current, and talks to the owner.
- **A lane agent**: told "read `brain/docs/todo/08-complex.md` and run lane X". It follows
  **Lane protocol** in `brain/docs/todo/07-big-swings.md` (the same rules: own files only,
  commit only those paths, take every timestamp from `date`, no worktree, never push, never
  touch `main`), the **Shared brief** below, and its own lane section.

Checkout: `/Users/troy/Documents/Projects/Industrial-Agents-Certivity`, branch `big-swings`.
Lanes H to L write disjoint files, so they run in parallel. Lanes A to G are finished. Do not
edit their files except to read them. Do not edit `out/experiments/STATUS.md` (that ledger is
closed). This task's ledger is `out/experiments/STATUS-08.md`.

Written Saturday 24 Oct, 23:25 CEST. The engine freeze for task 06 is 02:00. The held-out
bumper lands at 08:00. A result after about 01:30 is a recommendation, not a code change.

## Is the vote a real strategy?

Yes, as a selector over runs that already disagree about paragraphs. No, as "run one pipeline
many times".

`out/rear-lamp-swing-A-votes7.json` keeps a row when 7 or more of 14 existing dev runs wrote
it, and uses the wording from a run that keeps the subject and condition. Local result: 351
rows, 156 matched, F2 0.702. The curve peaks at 7 to 8 votes. Weights barely move it. F2 rises
with the number of runs and, within a fixed number, with how different the runs are. Six
rewrite variants on one relevance pass reach about 0.66. Seven runs from different families
reach 0.696. On the bumper, a vote of Haiku prompt variants moved paragraph F2 by less than
0.03, and one Sonnet run beat it.

So the 0.702 is not a lucky threshold. It is also not a method for Sunday by itself. The 14
files already existed, some used dev-gold examples (those runs must not be copied into a new
prompt), and the platform has not scored this file. The best single platform score is 154
matched, F2 0.682. A gap of a few matches is inside the noise seen when the same Fable rows
scored 142 and 149.

What the row audit shows, from `eval.errors` at 23:20 and a join with the blend scores in
`out/experiments/B-scores.json`:

| File | Rows | Outside gold paragraphs | Missed on a cited paragraph | Gold paragraphs never cited | Fewer / equal / more rows than gold | F2 | F2 if outside rows are dropped |
|---|---|---|---|---|---|---|---|
| Fable | 332 | 155 | 34 | 15 | 12 / 79 / 16 | 0.646 | 0.752 |
| votes >= 7 | 351 | 151 | 23 | 11 | 7 / 77 / 27 | 0.702 | 0.813 |
| votes >= 4 | 463 | 224 | 20 | 9 | 4 / 64 / 45 | 0.658 | 0.806 |
| blend >= 0.20 | 358 | 155 | 22 | 26 | 3 / 68 / 34 | 0.635 | 0.732 |
| recall ceiling | 1,116 | 755 | 17 | 4 | 1 / 53 / 63 | 0.450 | 0.740 |
| votes >= 12 | 149 | 47 | 41 | 50 | 21 / 58 / 2 | 0.545 | 0.568 |
| cut, no examples | 337 | 148 | 22 | 20 | 9 / 78 / 20 | 0.675 | 0.780 |
| verbatim v3 | 311 | 141 | 36 | 17 | 12 / 82 / 13 | 0.640 | 0.731 |
| votes + keep score | 356 | 137 | 25 | 11 | 8 / 63 / 39 | 0.690 | 0.781 |

Reading that table:

- The vote's gain over Fable is real and split across both failure modes: 11 paragraphs never
  cited instead of 15, and 23 misses on cited paragraphs instead of 34. It pays for that with
  more over-splitting (27 paragraphs with more rows than the gold, against 16).
- Lowering the vote from 7 to 4 adds 5 matches and 73 rows on paragraphs with no gold. Two of
  the ten gold paragraphs votes7 skips are recovered. The other extra matches are on-cited
  granularity. The hit rate of the added rows is about 0.045, under the break-even of about 0.14.
- The vote already contains almost every gold paragraph with blend >= 0.30. Paragraphs at
  blend >= 0.30 that votes7 does not cite: 12, of which 3 are gold. At blend >= 0.20 the extras
  are 53 paragraphs and still only those 3 gold. Harvesting the tail to catch the remaining
  gold paragraphs adds junk at about 0.06 per row or worse.
- Of the 23 gold rows missed on a paragraph votes7 does cite, 7 are one table, UN R10 6.9.1
  (ten pulse and voltage rows collapsed into three umbrella sentences), and 3 are the
  modulation table in UN R10 Annex 9 3.1. Several of the rest dropped a condition or tripped
  the local judge's negation rule ("shall prevent water" against "no water shall penetrate").
  A second cut of every paragraph is the wrong tool. A split of tables is the right one.
- Inside gold paragraphs, the 12-vote file matches 98 of 102 rows. Its failures are the 47
  rows on paragraphs the experts skip, and too few rows on the paragraphs it does cite. The
  precision ceiling is paragraph choice. Lane C's hand read of those misses names four classes:
  test-procedure steps, installation one-liners ("oriented rearwards", "two in number"),
  equipment the product does not have, and rows that only point at another table or section.

The headroom a new method can actually take: delete a large share of the 151 outside rows
without deleting matches (the oracle, which cheats by using the gold, reaches F2 0.813), and
expand the two EMC tables (about 10 of the 23 on-cited misses). Do not lower the vote, do not
write the blend tail, and do not hedge two rewrites of the same paragraph.

## Master protocol

Same as `07-big-swings.md`, with these differences:

1. Ledger is `out/experiments/STATUS-08.md`. Create it from the 07 template if it is absent.
2. Order of value: J, K, I, H, L. J and K and I spend nothing or almost nothing and answer the
   two gaps above. H tests whether a vote we generate ourselves works. L is the single-run
   control.
3. Budget is not approved until the owner answers. Ask once: "J $1, K $1, I $1, H $6, L $5.
   Which may spend? Hard ceiling stays $70 for the whole event, of which the swings spent
   $14.92." Write the answer in the ledger.
4. No platform upload. Owner at 23:36 on 24 Oct: do not upload anything, including
   `rear-lamp-swing-A-votes7.json`. Score only with `tools/validate.py`,
   `tools/score_local.py`, and `uv run python -m eval.score` from `brain/`. Do not nominate a
   file and do not set a lane to "waiting for upload".
5. `claude -p` is not logged in. Paid steps use the API inside the lane cap. Dry-run or count
   cache hits before calling a step free.
6. At 01:30, or when every lane is done: write **Results** at the end of this file, fold new
   run-log rows into `out/README.md`, commit the ledger, this file, and `out/README.md`.

Lane message, one agent per lane, this checkout, no worktree:

> Read `brain/docs/todo/08-complex.md` in `/Users/troy/Documents/Projects/Industrial-Agents-Certivity`
> and run lane X, following "Lane protocol" in `brain/docs/todo/07-big-swings.md`. Resume from
> `out/experiments/X.md` if it exists. Approved spend for this lane: $N (from
> `out/experiments/STATUS-08.md`). Score with `tools/validate.py`, `tools/score_local.py`, and
> `eval.score`. Do not nominate an upload and do not set your status to "waiting for upload".
> The owner closed the platform queue at 23:36. Take every timestamp from `date`.

Own paths, same pattern as 07: lane H writes `out/experiments/H.md`, `out/experiments/H-*`,
`out/rear-lamp-swing-H-*`, `brain/swing/h_*`. Same for I, J, K, L.

## Shared brief

Read `07-big-swings.md` for the score, the platform table, and the rules. The rules still hold.
No dev gold text in a prompt. Do not build on `BRAIN_REWRITE_EXAMPLES`. Import from `brain/`
and `eval/`. Do not edit `brain/brain/*.py` or `brain/eval/*.py`.

Break-even is unchanged: one match is worth about seven wasted rows, and a row is worth adding
when its chance of matching is above about 0.14.

Base files, already on disk:

- `out/rear-lamp-swing-A-votes7.json`, `out/rear-lamp-swing-A-votes4.json`
- `out/experiments/A-pool.json` (clusters, votes, member texts)
- `out/experiments/B-scores.json` (blend, llm, decision-model score, gold row count per paragraph)
- `out/rear-lamp-fable.json` and the other dev files listed in 07
- Lane C's four miss classes, in the report of `out/experiments/C.md`

The four classes, to be applied as rules or as a model judgement, never as gold sentences:

1. Test procedure: how to prepare, immerse, spray, wipe, or measure a sample. The pass
   criterion of the same test stays.
2. Installation one-liner: orientation, count, bare presence, or "at the rear", with no number
   the experts would keep (widths, heights, angles stay).
3. Conditional on equipment the requirement itself introduces as optional or absent: a variant
   the sentence exists only to cover.
4. Pointer: the row's only demand is "as specified in Table N" or "conform to paragraphs X
   and Y", and it states no value of its own.

A filter is good when rows it deletes outside gold paragraphs outnumber rows it deletes that
the local judge had matched, by enough to raise F2. Report both counts. The oracle column in
the table above is the ceiling, not a method: do not drop rows by checking them against the gold.

## Lanes

### J. Delete the expert-skip classes from the 7-vote file

**Question.** Of the 151 rows in votes7 that sit on paragraphs the experts never cite, how
many do the four classes catch, and how many of the 156 matches do they destroy?

**Cap:** $1. Prefer rules with no model call. A Haiku judgement over the 351 rows is inside
the cap if the rules are ambiguous. No dev gold in the prompt.

1. Tag every row of `rear-lamp-swing-A-votes7.json` with the four classes. Save the tags to
   `out/experiments/J-tags.json`.
2. Sweep: drop class 1, drop 1+2, drop 1+2+3, drop all four. For each file write rows, matched,
   F2, and how many deleted rows were matched versus unmatched.
3. The winning cut is the one with the best F2 that still matches at least 151 (the gain has
   to be larger than the platform noise). Read 15 deleted rows and 10 kept rows that the judge
   did not match.
4. Report whether this is a Sunday rule (text only, no vote required) or whether it only works
   on rows a vote already kept.

### K. The same filter on the 4-vote file

**Question.** Votes4 has 5 more matches and 73 more junk rows than votes7. Are those junk rows
the four classes, so that filtering votes4 beats votes7?

**Cap:** $1. Same tagging method as J, implemented in this lane's own module so the lanes do
not wait on each other. Do not import J's code. If both discover a shared bug in the class
definitions, write it in your notes. Do not edit J's files.

1. Tag `rear-lamp-swing-A-votes4.json`. The interesting rows are the 112 that votes7 does not
   contain.
2. Sweep the same class sets. Compare each result with votes7's 156 / 0.702.
3. Separately, report the 5 matches votes4 has and votes7 lacks: which class, if any, would
   have deleted them?
4. A win is F2 above 0.702 with the extra matches still present. A loss that deletes the extra
   matches and keeps the junk is also a result: the classes are not the votes4 waste.

### I. One row per value in a table, added to the 7-vote file

**Question.** Expanding UN R10 6.9.1 and Annex 9 3.1, and any similar table the vote collapsed,
recovers matches the local judge can see. Does it, and at how many extra rows?

**Cap:** $1. The paragraphs are few. Sonnet may rewrite only those paragraphs. Cached calls
are free.

1. Find paragraphs where the source is a table or a list of valued cases (pulses, voltages,
   frequency bands, modulation types) and the vote file has fewer rows than the table has
   value lines. Start with the two R10 paragraphs named above. List the candidates in the
   lane file before spending.
2. Emit one row per value line. The row keeps the table's numbers and names the subject.
   It must not restate the umbrella sentence the vote file already has. Drop a new row that
   is only a paraphrase of an existing row (similarity 0.6 or above against a row on the same
   paragraph).
3. Score the union with votes7. Report matches gained on those paragraphs, rows added, and F2.
   Also run `eval.errors` and record "missed on a cited paragraph" against votes7's 23.
4. Do not expand paragraphs that are not tables. Lane D already showed that a second cut of
   ordinary prose adds copies.

### H. A vote we generate, from three selections that differ

**Question.** Does a vote of three runs we can produce on Sunday reach most of the 14-run
gain, or was 0.702 an artifact of pooling tonight's history?

**Cap:** $6. Dry-run first and print cache hits. Stop if the estimate exceeds the cap.

The three runs, lamp, same rewrite prompt (`main`'s current Sonnet prompt), selection differs:

1. Opus relevance already cached, blend weight 0.7, the pipeline cut. This file may already
   exist (`rear-lamp-main-a39acab.json` or a sibling). Reuse it if the prompt matches. Do not
   pay again.
2. Sonnet relevance and rewrite, blend weight 0.85, the setting lane G found. New calls.
3. Haiku relevance, blend weight 0.85, Sonnet rewrite of the paragraphs Haiku selected.

Then vote at 2 of 3 and at 3 of 3, representative text from run 2 (Sonnet, subject and
condition kept). Score both. Compare with votes7 (156 / 0.702) and with the best of the three
single runs. On the plain bumper, lane G already showed a Haiku vote losing to one Sonnet run.
If the lamp vote of these three loses to run 2 alone, say so: diversity of this kind is not
enough, and Sunday stays a single Sonnet run.

Do not include the historical 14 files in this vote. That experiment is lane A, and it is done.

### L. One Sonnet run at weight 0.85, then the four-class filter

**Question.** The Sunday control. Does the bumper winner, on the lamp, plus the skip filter,
come within 5 matches of votes7?

**Cap:** $5. If lane H is already running the Sonnet weight-0.85 lamp file, wait for that file
and do not pay for a second copy. Until it exists, do the filter design on
`rear-lamp-main-a39acab.json` (weight 0.7, 388 rows, 146 matched) so the lane is not idle.
Say which base file the final number uses.

1. Produce or reuse the Sonnet weight-0.85 lamp submission.
2. Apply the four classes with this lane's own copy of the rules.
3. Report the unfiltered and filtered F2 next to votes7 and next to lane G's bumper numbers,
   so the master can see whether the lamp and the bumper agree.
4. Write the exact command a Sunday operator would run, with the measured cost and wall time.

## Results

Written 25 Oct 00:02 CEST, from the lane reports, after `eval.errors` on each headline file. Every score is local. Nothing was uploaded. Spend is $4.34, all of it lane H (Sonnet weight 0.85 $3.16, Haiku relevance $1.17). J, K, I and L spent $0. With the swings' $14.92, the event total is $19.26 of the $70 ceiling.

A perfect local score is F2 1.0: 190 matched rows and 190 submitted rows. The lift named for each file is the larger of three counterfactuals: drop every row on a paragraph the experts never cite, turn the misses on a cited paragraph into matches without adding rows, or add one matching row for each gold row on a paragraph the file never cites.

| Lane | File | Rows | Matched | F2 | Biggest lift toward 1.0 |
|---|---|---|---|---|---|
| J, classes on votes7 | no cut adopted; votes7 stands | 351 | 156 | 0.702 | 151 outside rows, to 0.813 |
| J, least-bad cut | drop classes 1 and 2 | 271 | 142 | 0.689 | 30 on-cited misses, to 0.834 |
| K, classes on votes4 | drop class 1 | 407 | 158 | 0.677 | 172 outside rows, to 0.794 |
| I, table lines added | votes7 plus 28 value lines | 379 | 163 | 0.716 | 151 outside rows, to 0.825 |
| H, vote of three new runs | 2 of 3 | 388 | 144 | 0.627 | 28 on-cited misses, to 0.749 |
| H, best single run | reused Opus, weight 0.7 | 388 | 146 | 0.636 | 177 outside rows, to 0.747 |
| L, Sunday control | Sonnet weight 0.85, drop 1 and 2 | 345 | 130 | 0.588 | 34 gold rows never cited, to 0.720 |

**Outside rows.** The four classes catch 86 of the 151 votes7 rows on paragraphs the experts never cite, and they destroy 43 of the 156 matches. Class 1 deletes about four unmatched rows per match, under the break-even of about seven. Class 3 deletes 19 matches to catch 21 outside rows. No votes7 cut still matches 151, so none is adopted. The same rules lower F2 on Fable, on the weight-0.7 file, and on the Sonnet weight-0.85 file. On votes4, dropping class 1 keeps 158 matches in 407 rows (F2 0.677). That is two matches above votes7 and 0.025 F2 below it. The five extra matches are four different classes. Filtering the loose vote does not beat the tight one.

**Collapsed tables.** One table pays. UN R10 6.9.1 goes from 3 of 10 gold rows to 10 of 10, at 12 added rows, and the union is 379 rows, 163 matched, F2 0.716. Misses on a cited paragraph fall from 23 to 16. Tables 2a, 2b and the two missing 12 V lines add 16 rows and no matches. Annex 9 3.1 was already one row per modulation. The 151 outside rows are still the largest gap on that file (dropping them reaches 0.825). The split is a parser for three lamp tables. A bumper that does not cite them gains nothing from it.

**A vote we generate.** It loses to one run. Opus at weight 0.7, reused, is 146 / 0.636. Sonnet at weight 0.85 is 136 / 0.585. Haiku relevance with a Sonnet rewrite is 138 / 0.539. The 2-of-3 vote is 144 / 0.627. The 3-of-3 vote is 111 / 0.548. Both votes are below the Opus file, and both are well below votes7. The 0.702 figure belongs to the 14-file pool. These three selections do not reproduce it. On the 2-of-3 vote the largest remaining gap is the 28 gold rows missed inside paragraphs it already cites.

**Sunday.** One Sonnet run at blend weight 0.85, the bumper command from lane G, stays the Sunday file. On the lamp that same setting is 403 rows, 136 matched, F2 0.585, ten matches behind the Opus weight-0.7 file, and the skip filter moves it to 345 / 130 / 0.588. The lamp and the bumper disagree about the weight. The filter does not close the gap on either lamp base. Lane G's measured fog command remains 134 s and $4.33; a cold plain bumper of that size is about 60 s and about $1.15. Do not append the four-class filter, and do not spend Sunday on a second relevance model unless the paragraph choice on the bumper is the thing that fails.
