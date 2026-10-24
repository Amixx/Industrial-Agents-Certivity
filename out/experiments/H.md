# Lane H: a vote of three runs we can produce

State: blocked: approved spend is $0, and runs 2 and 3 are not in the cache. Updated: 24 Oct 23:49 CEST.
Approved spend: $0. Spent: $0. No API call was made.

## Checklist

- [x] H1 Reuse Opus relevance, blend weight 0.7, the pipeline cut, if the prompt matches.
      Done 24 Oct 23:49 CEST. File: `out/rear-lamp-main-a39acab.json` (reused, not rewritten).
      Commit: this step. Found: the current Sonnet prompt matches. 388 rows, 146 matched, F2 0.636.
      Opus relevance 113/113 cache hits. Sonnet rewrite of those 267 paragraphs 23/23 cache hits.
- [x] H2 Dry-run Sonnet relevance and rewrite, blend weight 0.85. No call made.
      Done 24 Oct 23:49 CEST. Files: `brain/swing/h_dry.py`, `out/experiments/H-dry.json`.
      Found: Sonnet relevance 0/113 cache hits, estimated $2.241. Rewrite set is unknown;
      the Opus weight-0.85 proxy (362 paragraphs) has 0/31 rewrite hits, estimated $1.116.
- [x] H3 Dry-run Haiku relevance at weight 0.85, Sonnet rewrite of the paragraphs Haiku selects.
      Done 24 Oct 23:49 CEST. Same files. Found: Haiku relevance 0/113 cache hits, estimated $0.112.
      Rewrite is a second cold set of about the same size, $1.116 on the same proxy.
- [ ] H4 Vote at 2 of 3 and at 3 of 3, representative text from run 2.
      Not run. `out/rear-lamp-swing-H-sonnet-w85.json` and `out/rear-lamp-swing-H-haiku-rel.json`
      do not exist. The historical 14 files were not added to this vote.

Next: when the ledger shows an approved spend for lane H of at least $4.59 (the cap in the brief is $6), produce runs 2 and 3 into `out/rear-lamp-swing-H-*`, then vote. Do not use `g_runs.py` for that: it writes `out/experiments/G-*`. Keep the Opus profile and the four regulations (they are cached). Set the relevance model only for `relevance.score`, wrap `relevance.blend` at weight 0.85 (assigning `WEIGHT` does nothing), and rewrite with `claude-sonnet-5-5` and main's current prompt. Dry-run again first; cache hits stay free.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 24 Oct 23:49 | out/rear-lamp-main-a39acab.json | reused: Opus relevance, blend 0.7, Sonnet rewrite, main's prompt (`d7683cd`) | pipeline, already on disk | 388 | 146 / 0.636 | not uploaded | $0 |
| 24 Oct 23:49 | (not written) | Sonnet relevance + Sonnet rewrite, blend 0.85 | h_dry.py | — | — | — | est. $3.36 |
| 24 Oct 23:49 | (not written) | Haiku relevance, blend 0.85, Sonnet rewrite | h_dry.py | — | — | — | est. $1.23 |

## Uploads

None. Run 1 is 10 matches behind votes7 (156 / 0.702). No file from this lane is ahead of it.

## Notes

Run 1 is `out/rear-lamp-main-a39acab.json`. The log at 22:35 CEST already recorded 115 Opus cache hits, 23 Sonnet cache hits, 267 paragraphs, 388 requirements, and $0. `brain/brain/rewrite.py` last changed in `d7683cd` at 21:44, before that file was written. The dry run, which refuses any network call, reproduces the log: regulations UN R148 0.95, UN R48 0.92, UN R150 0.88, UN R10 0.85; weight 0.7 keeps 267 paragraphs; the Sonnet rewrite of that list is 23 cache hits and $0. The prompt matches. The file was not regenerated.

Scored at 23:39 CEST with no model call:

- `tools/validate.py`: valid, 388 requirements.
- `tools/score_local.py`: regulation 4/4/4, F1 1.000. Page 62/53/49, precision 0.790, recall 0.925, F1 0.852.
- `eval.score`: requirement 388/190/146, precision 0.376, recall 0.768, F2 0.636. Page F2 0.894.

votes7, from the brief, is 351 rows, 156 matched, F2 0.702. Run 1 is the only one of the three that can be scored today. It is the best single run this lane has, and it loses to votes7 by 10 matches.

`brain/swing/h_dry.py` builds the real prompts and reads `brain/data/cache/llm/`. A miss raises before the SDK, and `_anthropic` is replaced so a bug cannot spend. Profile and regulation review stay on the cached Opus answers (2 calls, both hits, inside the 115). Relevance is 2,805 candidate paragraphs in batches of 25 (113 calls). The token estimate is calibrated to `out/rear-lamp-mix-noimage.log` (115 Opus calls, 667,122 in / 98,058 out / 77,770 cache read, $4.65). Rebuilding that log from the same prompts came out $4.689. Haiku rates are the ones in `g_runs.py`: $0.10 / $0.50 / $0.01 per million tokens. They are not in the run-log price table.

Rewrite dollars scale `out/rear-lamp-mix.log`: 23 Sonnet calls, $0.854, the same prompt, about $0.0032 per paragraph. Weight 0.85 with the cached Opus scores keeps 362 paragraphs. Those 31 batches are all cache misses ($1.116 by prompt characters, $1.158 by the per-paragraph rate). Sonnet and Haiku scores are not cached, so their paragraph lists are not known. The 362 figure is a size proxy, not their selection. It already shares no rewrite batch with the cached 267, so a different list does not get cheaper. Relevance does not depend on that list: every candidate is scored, and that cost is fixed.

| Piece | Cache | Estimate |
|---|---|---|
| Run 1, whole file | reused | $0 |
| Run 2, Sonnet relevance, 113 batches | 0 hits | $2.241 |
| Run 2, Sonnet rewrite, ~362 paragraphs | 0 hits on the proxy | $1.116 |
| Run 3, Haiku relevance, 113 batches | 0 hits | $0.112 |
| Run 3, Sonnet rewrite, ~362 paragraphs | 0 hits on the proxy | $1.116 |
| Both new runs | | $4.59 |

$4.59 is under the $6 cap in the brief. The approved amount is $0, so nothing was run. Relevance is fixed. Rewrite is about $0.0032 per selected paragraph, paid twice because the two lists will not share batches. Both rewrites stay inside the leftover $3.65 of the cap unless each list is larger than about 570 paragraphs. The Opus weight change itself, 267 to 362, is the only size this lane could measure without spending.

Swapping the strong model for the whole pipeline, which is what `g_runs.py` does, is a different call. Sonnet's profile for this spec and drawing is already cached. Sonnet regulation review, using the Opus profile text, is one miss at about $0.08. Haiku profile and regulation review are both misses, together under $0.01. Those calls are not in the $4.59. This lane keeps the Opus profile so the three runs differ only in paragraph selection.

## Report

The vote was not run. Two of the three files do not exist, and making them is about $4.59 of new API spend against an approved cap of $0. Run 1, reused from cache, scores 146 matched and F2 0.636, which is 10 matches behind votes7 (156 / 0.702). Whether three runs we produce ourselves reach most of the 14-run gain is still open.

| File | Rows | Matched | F2 | New spend |
|---|---|---|---|---|
| votes7 (lane A) | 351 | 156 | 0.702 | $0, already on disk |
| Run 1, Opus relevance, weight 0.7 | 388 | 146 | 0.636 | $0, reused |
| Run 2, Sonnet, weight 0.85 | not written | | | $3.36 estimated |
| Run 3, Haiku relevance, Sonnet rewrite, weight 0.85 | not written | | | $1.23 estimated |

**Uploads.** None.

**Transfer.** Not run. There is no voted file to take to the bumper.

**Sunday.** Not answered. The lamp vote of these three runs does not exist, so this lane cannot say that diversity of this kind fails, and it cannot say that it reaches 0.702. If the spend is approved, the two new runs are about $4.59 together at a selection near 362 paragraphs, on top of run 1 which is free. The commands and the cache counts are in Notes.
