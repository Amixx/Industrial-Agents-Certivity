# Benchmarks

How well the requirement engine (`brain/`) does on the rear lamp case with different language
models, and what each run costs. Every benchmark run gets a row in the run log below, on any
branch, and a dated section under Results that says what changed. When a file is uploaded,
add the platform's scores and the upload time to its row and section (see `AGENTS.md`).

## Run log

All times 24 Oct 2026, CEST. Local scores use `brain/eval/score.py` (matched of 190 expert
rows, requirement F2). Platform matched is recall times 190. Code names the commit or branch
that produced the file; branch code is not on `main` unless it says so.

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| before 18:45 | `brain/out/dev-upload.json` | gpt-5.5 relevance, gpt-5.4-mini rewrite; cited R26 too | `main` | 407 | 138 / 0.591 | (18:45) 145 / 0.621 | not logged |
| 19:49 to 19:57 | `rear-lamp-sonnet.json` | Sonnet 5.5 on every step | `brain-claude-models` @ `fd2777b` | 344 | 131 / 0.593 | (20:10) 140 / 0.634 | $3.08 |
| 19:49 to 19:57 | `rear-lamp-opus.json` | Opus 5.5 on every step | `brain-claude-models` @ `fd2777b` | 338 | 139 / 0.633 | (20:06) 143 / 0.651 | $6.36 |
| 19:49 to 19:57 | `rear-lamp-fable.json` | Fable 5.1 on every step | `brain-claude-models` @ `fd2777b` | 332 | 141 / 0.646 | (20:05) **149 / 0.682**; (20:04, as team-00) 142 / 0.650 | $16.52 |
| | `rear-lamp-deterministic.json` | No LLM | `edc8f1f` | 778 | 112 / 0.364 | (20:23) 107 / 0.348 | $0 |
| | `rear-lamp-main-cli.json` | `main` at `7644efe`: Opus relevance, Sonnet rewrite, through `claude -p` | `kb-stack` | 368 | | (21:05 to 22:16) 143 / 0.634 | subscription |
| | `rear-lamp-kb-deterministic.json` | Obligation base, no LLM | `kb-stack` | 864 | | (21:05 to 22:16) 108 / 0.333 | $0 |
| | `rear-lamp-kb-jev.json` | Obligation base, Jev blend cut 0.25, Opus everywhere | `kb-stack` @ `5f6e476` | 389 | | (21:05 to 22:16) 154 / 0.670 | subscription |
| | `rear-lamp-kb-jev-filter-v4.json` | The above plus requirement filter and minimal-edit rewrite | `kb-stack` @ `1d8b22e` | 342 | / 0.717 | (21:05 to 22:16) 140 / 0.635 | subscription |
| | `rear-lamp-kb-sol-rewrite.json` | Paragraphs of `kb-jev` rewritten by GPT-6.1 Sol | `kb-stack` | 420 | | (21:05 to 22:16) 143 / 0.606 | subscription |
| | `rear-lamp-qwen-split-rewrite.json` | Fable's 208 paragraphs rewritten by qwen3.5:9b, split prompt of `0ccae35` | `dcf1740` | 446 | 137 / 0.568 | (21:47) 133 / 0.551 | $0 |
| 22:00 | `rear-lamp-mix-examples-cut.json` | Opus relevance, Sonnet rewrite with expert examples and the obligation cut | `brain-model-mix-examples` @ `e5e0d25` | 341 | 145 / 0.658 | (22:14) 138 / 0.627 | $1.13 |
| 22:45 | `rear-lamp-kb-v5-rewrite.json` | Paragraphs of `kb-jev` rewritten by Opus; prompt names the device and repeats the condition in every row | `kb-stack` @ `1d8b22e` plus an uncommitted prompt | 363 | 158 / 0.703 | (22:48) 148 / 0.659 | subscription |
| 21:55 | `rear-lamp-deterministic-sibling.json` | No LLM, with sibling routing and the regulation-title rule; decision model refit | `main` @ `b7d6ee2` (reproduced at `a39acab`) | 647 | 111 / 0.394 | (22:57) 106 / 0.377 | $0 |
| 21:33 to 22:14 | `rear-lamp-qwen-split2-rewrite.json` | Fable's 208 paragraphs rewritten by qwen3.5:9b, narrowed table rule and empty-answer fallback | `main` @ `d7683cd`, `eval.rewrite_pass` | 411 | 143 / 0.611 | | $0 |
| 22:15 to 22:28 | `rear-lamp-gemini-relevance.log` | Relevance only: gemini-3.8-flash (free tier) on 425 dev paragraphs; AUC 0.998 (gpt-5.5 0.987) | `main` @ `bb829ec`, `out/scripts/gemini_relevance.py` | n/a | | | $0 |
| 22:30 to 22:49 | `rear-lamp-gemini-relevance.log` | Relevance only: gemini-3.5-flash (free tier) on 1,100 dev paragraphs; AUC 0.974 (gpt-5.5 0.968) | `main` @ `bb829ec`, `out/scripts/gemini_relevance.py` | n/a | | | $0 |
| 22:52 | `rear-lamp-kb-recall-push.json` | `kb-jev`'s rewrite prompt, Jev cut at 0.20 of each regulation's best (was 0.25), requirement filter on; Opus everywhere | `kb-stack` @ `1d8b22e` with the rewrite prompt of `6f5a1c1` | 390 | 156 / 0.678 | (23:21) 150 / 0.652 | subscription |
| 23:34 | `rear-lamp-kb-own-subject.json` | The above with a rewrite prompt that keeps the sentence's own subject ("The markings shall ...") and names the device only when the sentence has none; model judge 163 against 150 for the run above | the above plus an uncommitted prompt | 396 | 163 / 0.705 | (23:39) 151 / 0.653 | subscription |
| 22:20 to 22:50 | `rear-lamp-agent-v3.json` | One Opus agent (`claude -p`, effort high) with only file tools, the spec, the image and the regulation texts with tables of contents; short prompt, TSV output converted to a submission | `out/scripts/agent-v3/` | 302 | 108 / 0.508 | (22:54) 116 / 0.546 | subscription |
| 23:50 | `rear-lamp-kb-section-cut.json` | Rows of `rear-lamp-kb-recall-push.json` (filter off) kept when p_keep times a section-level Opus score is at least 0.2; the section score comes from one call per section with all its cited paragraphs side by side. Same 116 gold paragraphs, 24 fewer rows outside them | `out/scripts/section_select.py`, `section_measure.py` | 363 | 156 / 0.695 | (23:49) 151 / 0.672 | subscription |
| 23:52 | `rear-lamp-kb-section-cut2.json` | Same rows and scores as the run above, kept when p_keep times the square root of the section score is at least 0.354 (the lowest 26% dropped); 115 gold paragraphs, 31 fewer rows | `out/scripts/section_select.py` | 332 | | (23:54) 149 / 0.682 | subscription |
| 25 Oct 00:03 | `rear-lamp-kb-section-cut2-rules.json` | `rear-lamp-kb-section-cut2.json` without 6 rows whose quote only points elsewhere ("See Table 4", "Failure provisions: See paragraph 4.6.") or only brings other paragraphs into force ("shall conform to the requirements set forth in paragraphs 4. and 5."); none of the 6 is on a gold paragraph. Paragraph estimate 0.684 against 0.680 for the source | `out/scripts/section_stage.py` | 326 | | (25 Oct 00:10) 150 / 0.691 | $0 |
| 25 Oct 01:05 | `rear-lamp-kb-jev-cut.json` | Rows of `rear-lamp-kb-jev.json` (154 platform matches) cut with main's Sunday rule: filter p_keep at least 0.40, then p_keep times the section score at least 0.2, then the pointer and approval-mark rule. p_keep scored by Opus for the saved rows (`out/scripts/pkeep_saved.py`, saved as `rear-lamp-kb-jev.pkeep.json`); section scores from the section-cut run. Estimate was 153 matches, F2 0.705 | `out/scripts/pkeep_saved.py` | 326 | | (25 Oct 01:01) 148 / 0.681 | subscription |
| 25 Oct 00:20 | `rear-lamp-kb-section-cut2-mark.json` | The row above without 9 rows that spell out the approval mark ("a circle surrounding the letter E", "the number of this Regulation followed by the letter R"); none is on a gold paragraph and no gold row reads like one. Expect 150 matches, F2 0.696 | `out/scripts/section_stage.py` | 317 | | (25 Oct 00:50) 149 / 0.692 | $0 |
| 25 Oct 01:08 | `rear-lamp-kb-section-cut2-mark-verbatim.json` | `rear-lamp-kb-section-cut2-mark.json` with each row's text replaced by its `quote`, the exact source sentence, wherever that quote belongs to one row only (285 of 317); rows that share a quote (list items, table rows) keep the rewrite. Same rows, paragraphs and pages | inline script, see section below | 317 | | (25 Oct 01:10) **156 / 0.724** | $0 |
| 25 Oct 01:12 | `rear-lamp-kb-section-cut2-mark-verbatim2.json` | The verbatim file with the rewrite kept for 75 rows whose quote is a fragment: list items ("(b) A variable luminous intensity control;"), clauses ending in ";" or ":", table cells; 210 of 317 rows verbatim | `out/scripts/verbatim.py` (without `--all`) | 317 | | (25 Oct 01:52) 146 / 0.678 | $0 |
| 25 Oct 01:57 | `rear-lamp-kb-section-cut2-mark-fragquote.json` | The opposite split of the verbatim2 file: the 75 fragment rows (list items, ";"/":" clauses, table cells) take their quote, the 201 full-sentence rows keep the rewrite | inline script on the three files above | 317 | | (25 Oct 02:01) 151 / 0.701 | $0 |
| 25 Oct 01:22 | `rear-lamp-kb-sentence-pick-cut.json` | The 194 paragraphs of `rear-lamp-kb-section-cut2-mark.json` rewritten by Opus with one requirement per obligation sentence (minimal edit, no extra splits), text replaced by the quoted sentence, then Opus p_keep per row, the section cut and the three rules | `out/scripts/sentence_rewrite.py`, `out/scripts/pkeep_saved.py`, `out/scripts/section_stage.py` | 285 | | (25 Oct 01:25) 142 / 0.679 | not logged (two Opus passes, subscription) |
| 25 Oct 01:26 | `rear-lamp-sunday-pipeline-verbatim.json` | The Sunday pipeline end to end on dev: `ready-for-main` with Jev (test conditions count as technical, refit on dev), Opus on both tiers via `claude -p`, the rewrite prompt of `6f5a1c1`, requirement filter 0.40, linear section cut 0.2, the three rules; then each row's text replaced by its quote (334 of 366) | `ready-for-main` @ `df982ee`, `out/scripts/claude_cli_run.py`, `out/scripts/verbatim.py --all` | 366 | | (25 Oct 01:45) 156 / 0.693 | $4.84 (reported by `claude -p`) |
| 25 Oct 00:20 | `rear-lamp-kb-splitless-cut2-mark.json` | Recall-push setup (filter off) rewritten with one requirement per sentence, split only at lettered or numbered list items, then the section cut and the pointer, umbrella and approval-mark rules | `out/scripts/section_stage.py` | 271 | | (25 Oct 00:42) 140 / 0.679 | $0 |
| 22:35 | `rear-lamp-main-a39acab.json` | `main`'s defaults at `a39acab`: Opus relevance, Sonnet rewrite with the prompt of `d7683cd` | `big-swings` (no code change) | 388 | 146 / 0.636 | not uploaded | $0.84 |
| 22:55 | `rear-lamp-swing-A-votes7.json` | Vote over 14 dev runs, Jaccard 0.5, votes >= 7, share-claude text | `big-swings`, `swing/a_sweep.py` | 351 | 156 / 0.702 | not uploaded | $0 |
| 22:55 | `rear-lamp-swing-A-votes4.json` | The same, votes >= 4 | `big-swings`, `swing/a_sweep.py` | 463 | 161 / 0.658 | not uploaded | $0 |
| 22:41 | `rear-lamp-swing-B-full.json` | Opus relevance (cached), Sonnet rewrite, blend >= 0.03 | `big-swings`, `swing/b_recall.py` | 1,382 | 158 / 0.369 | not uploaded | $2.03 |
| 22:45 | `rear-lamp-swing-B-full005.json` | The above, blend >= 0.05 | `swing/b_tail.py` | 862 | 158 / 0.487 | not uploaded | $0 |
| 22:45 | `rear-lamp-swing-B-union.json` | B-full plus 254 uncovered pool medoids | `swing/b_tail.py` | 1,636 | 169 / 0.353 | not uploaded | $0 |
| 22:45 | `rear-lamp-swing-B-ceiling.json` | The union, blend >= 0.05 | `swing/b_tail.py` | 1,116 | 169 / 0.450 | not uploaded | $0 |
| 22:45 | `rear-lamp-swing-B-cut020.json` | B-full, blend >= 0.20 | `swing/b_tail.py` | 358 | 142 / 0.635 | not uploaded | $0 |
| 22:42 | `rear-lamp-swing-C-votes13.json` | Clusters written by all 13 runs | `big-swings`, `swing/c_precision.py` | 105 | 71 / 0.410 | not uploaded | $0 |
| 22:42 | `rear-lamp-swing-C-votes12.json` | Clusters written by 12 or 13 runs | `swing/c_precision.py` | 149 | 99 / 0.545 | not uploaded | $0 |
| 22:42 | `rear-lamp-swing-C-votes10.json` | Clusters written by 10 or more runs | `swing/c_precision.py` | 217 | 118 / 0.604 | not uploaded | $0 |
| 22:42 | `rear-lamp-swing-C-kbjev-top150.json` | kb-jev's 150 highest-confidence rows | `swing/c_precision.py` | 150 | 82 / 0.451 | not uploaded | $0 |
| 22:42 | `rear-lamp-swing-C-both-v6-c05.json` | Votes >= 6 and confidence >= 0.5 | `swing/c_precision.py` | 120 | 78 / 0.443 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-union.json` | Union of split and example-cut rewrites | `big-swings`, `d_hedge.py` | 660 | 155 / 0.546 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-union-near06.json` | Same, drop second-file rows at similarity >= 0.6 | `d_hedge.py` | 439 | 152 / 0.634 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-diff-fine.json` | Both cuts where row counts differ | `d_hedge.py` | 489 | 154 / 0.616 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-rel0.5-coarse.json` | Both cuts where relevance >= 0.5 | `d_hedge.py` | 405 | 147 / 0.631 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-rel0.5-or-diff.json` | Both cuts where relevance >= 0.5 or counts differ | `d_hedge.py` | 508 | 154 / 0.607 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-mix-cut-first-near0.4.json` | Split, plus cut rows below similarity 0.4 | `d_hedge.py` | 408 | 148 / 0.634 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-fable-mix-first-near0.4.json` | Fable plus split rows below similarity 0.4 | `d_hedge.py` | 359 | 150 / 0.670 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-fable-mix-first-near0.5.json` | Same at similarity < 0.5 | `d_hedge.py` | 375 | 150 / 0.661 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-kbjev-mix-first-near0.45.json` | kb-jev plus split rows below similarity 0.45 | `d_hedge.py` | 442 | 164 / 0.682 | not uploaded | $0 |
| 22:46 | `rear-lamp-swing-D-cut-noex.json` | Obligation cut, no expert examples | `d_cut.py` | 337 | 148 / 0.675 | not uploaded | $0.82 |
| 23:00 | `rear-lamp-swing-D-cutnoex-mix-first-near0.4.json` | No-example cut plus split rows below similarity 0.4 | `d_hedge.py` | 352 | 153 / 0.688 | not uploaded | $0 |
| 23:00 | `rear-lamp-swing-D-cutnoex-mix-first-near0.45.json` | Same at similarity < 0.45 | `d_hedge.py` | 360 | 155 / 0.692 | not uploaded | $0 |
| 22:43 | `rear-lamp-swing-E-v1.json` | Verbatim segments plus subject and condition, Fable's paragraphs | `swing/e_verbatim.py` | 316 | 133 / 0.618 | not uploaded | $0.58 |
| 22:45 | `rear-lamp-swing-E-v2.json` | v1 plus rules for labels, lists, conditions | `swing/e_verbatim.py` | 300 | 130 / 0.613 | not uploaded | $0.58 |
| 23:03 | `rear-lamp-swing-E-v3.json` | v2 plus list rebuild, provisos kept whole, device inserted | `swing/e_verbatim.py` | 311 | 137 / 0.640 | not uploaded | $0.63 |
| 22:59 | `rear-lamp-swing-F-votes-logit.json` | Leave-one-regulation-out logistic on log(votes) and Opus keep score | `swing/f_fit.py` | 356 | 154 / 0.690 | not uploaded | $1.25 |
| 22:44 | `experiments/G-bumper-plain-haiku-base-s0.json` | Haiku relevance and rewrite, plain bumper. Local column is silver paragraph P/R/F2, not the lamp judge | `swing/g_runs.py` | 173 | 0.55 / 0.54 / 0.541 | none (bumper) | $0.069 |
| 22:47 | `experiments/G-bumper-plain-haiku-base-s1.json` | Same, seed 1. Paragraph P/R/F2 | `g_runs.py` | 243 | 0.46 / 0.60 / 0.563 | none | $0.071 |
| 22:47 | `experiments/G-bumper-plain-haiku-alt-s0.json` | Reworded relevance prompt. Paragraph P/R/F2 | `g_runs.py` | 177 | 0.54 / 0.61 / 0.596 | none | $0.061 |
| 22:47 | `experiments/G-bumper-plain-haiku-alt-s2.json` | Alt prompt, seed 2. Paragraph P/R/F2 | `g_runs.py` | 197 | 0.50 / 0.57 / 0.552 | none | $0.067 |
| 22:48 | `experiments/G-bumper-plain-haiku-base-s3-verbatim.json` | Verbatim rewrite prompt. Paragraph P/R/F2 | `g_runs.py` | 169 | 0.48 / 0.63 / 0.590 | none | $0.065 |
| 22:48 | `experiments/G-bumper-plain-haiku-base-s4-b40.json` | Seed 4, batch 40. Paragraph P/R/F2 | `g_runs.py` | 328 | 0.37 / 0.63 / 0.548 | none | $0.077 |
| 22:57 | `experiments/G-bumper-plain-vote1-anchor-6.json` | Paragraph vote, min 1 of 6 Haiku runs. Paragraph P/R/F2 | `g_runs.py vote` | 456 | 0.31 / 0.78 / 0.598 | none | $0 |
| 22:57 | `experiments/G-bumper-plain-vote2-anchor-6.json` | Min 2 of 6. Paragraph P/R/F2 | `g_runs.py vote` | 311 | 0.40 / 0.67 / 0.592 | none | $0 |
| 22:57 | `experiments/G-bumper-plain-vote3-anchor-6.json` | Min 3 of 6. Paragraph P/R/F2 | `g_runs.py vote` | 232 | 0.48 / 0.64 / 0.602 | none | $0 |
| 22:57 | `experiments/G-bumper-plain-vote4-anchor-6.json` | Min 4 of 6. Paragraph P/R/F2 | `g_runs.py vote` | 155 | 0.63 / 0.61 / 0.616 | none | $0 |
| 22:57 | `experiments/G-bumper-plain-vote-cluster-mr2.json` | Row clusters, >= 2 runs. Paragraph P/R/F2 | `g_runs.py vote` | 301 | 0.41 / 0.67 / 0.595 | none | $0 |
| 22:57 | `experiments/G-bumper-plain-vote-cluster-mr3.json` | Row clusters, >= 3 runs. Paragraph P/R/F2 | `g_runs.py vote` | 206 | 0.48 / 0.64 / 0.602 | none | $0 |
| 22:57 | `experiments/G-bumper-plain-vote-cluster-mr4.json` | Row clusters, >= 4 runs. Paragraph P/R/F2 | `g_runs.py vote` | 134 | 0.63 / 0.60 / 0.604 | none | $0 |
| 22:59 | `experiments/G-bumper-plain-sonnet-base-s0.json` | Sonnet relevance and rewrite, weight 0.7. Paragraph P/R/F2 | `g_runs.py` | 138 | 0.78 / 0.79 / 0.789 | none | $1.088 |
| 23:00 | `experiments/G-bumper-plain-opus-ref.json` | Opus relevance (cached) plus Sonnet rewrite. Paragraph P/R/F2 | `g_runs.py` | 123 | 0.75 / 0.67 / 0.686 | none | $0.225 |
| 23:03 | `experiments/G-bumper-plain-sonnet-w85.json` | Sonnet, blend weight 0.85. Paragraph P/R/F2 | `g_runs.py` | 143 | 0.79 / 0.85 / 0.838 | none | $0.257 |
| 23:04 | `experiments/G-bumper-sensors-fog-haiku-base-s0.json` | Haiku, fog bumper. Paragraph P/R/F2 on the 4 labelled regulations | `g_runs.py` | 652 | 0.58 / 0.52 / 0.534 | none | $0.271 |
| 23:08 | `experiments/G-bumper-sensors-fog-haiku-base-s1.json` | Same, seed 1. Paragraph P/R/F2 | `g_runs.py` | 717 | 0.39 / 0.49 / 0.467 | none | $0.266 |
| 23:08 | `experiments/G-bumper-sensors-fog-haiku-alt-s0.json` | Alt prompt. Paragraph P/R/F2 | `g_runs.py` | 550 | 0.59 / 0.45 / 0.470 | none | $0.249 |
| 23:08 | `experiments/G-bumper-sensors-fog-haiku-base-s3-verbatim.json` | Verbatim rewrite. Paragraph P/R/F2 | `g_runs.py` | 492 | 0.41 / 0.49 / 0.474 | none | $0.253 |
| 23:08 | `experiments/G-bumper-sensors-fog-vote1-anchor-4.json` | Paragraph vote, min 1 of 4. Paragraph P/R/F2 | `g_runs.py vote` | 1120 | 0.34 / 0.66 / 0.554 | none | $0 |
| 23:08 | `experiments/G-bumper-sensors-fog-vote2-anchor-4.json` | Min 2 of 4. Paragraph P/R/F2 | `g_runs.py vote` | 711 | 0.49 / 0.52 / 0.516 | none | $0 |
| 23:08 | `experiments/G-bumper-sensors-fog-vote3-anchor-4.json` | Min 3 of 4. Paragraph P/R/F2 | `g_runs.py vote` | 461 | 0.65 / 0.48 / 0.505 | none | $0 |
| 23:08 | `experiments/G-bumper-sensors-fog-vote4-anchor-4.json` | Min 4 of 4. Paragraph P/R/F2 | `g_runs.py vote` | 249 | 0.74 / 0.30 / 0.339 | none | $0 |
| 23:11 | `experiments/G-bumper-sensors-fog-sonnet-w85.json` | Sonnet, blend weight 0.85, fog bumper. Paragraph P/R/F2 on the 4 labelled regulations | `g_runs.py` | 519 | 0.74 / 0.79 / 0.779 | none | $4.330 |
| 23:47 | `rear-lamp-swing-I-tables.json` | votes7 plus one row per value line of UN R10 Tables 1, 2a, 2b, 3a and 3b | `swing/i_tables.py` | 379 | 163 / 0.716 | (25 Oct 00:22) 146 / 0.641 | $0 |
| 23:50 | `rear-lamp-swing-L-drop12.json` | Weight-0.7 file, drop test-procedure and installation classes | `swing/l_filter.py` | 315 | 138 / 0.642 | not uploaded | $0 |
| 23:52 | `rear-lamp-swing-K-drop1.json` | votes4, drop the test-procedure class | `swing/k_filter.py` | 407 | 158 / 0.677 | not uploaded | $0 |
| 23:55 | `rear-lamp-swing-J-drop12.json` | votes7, drop test-procedure and installation classes. Not adopted: 142 matches, under the 151 floor | `swing/j_classes.py` | 271 | 142 / 0.689 | not uploaded | $0 |
| 23:55 | `rear-lamp-swing-H-sonnet-w85.json` | Sonnet relevance and rewrite, blend weight 0.85 | `swing/h_run.py` | 403 | 136 / 0.585 | not uploaded | $3.16 |
| 23:56 | `rear-lamp-swing-H-haiku-rel.json` | Haiku relevance, blend weight 0.85, Sonnet rewrite | `swing/h_run.py` | 520 | 138 / 0.539 | not uploaded | $1.17 |
| 23:57 | `rear-lamp-swing-H-vote2.json` | Vote of the Opus 0.7 run, the Sonnet 0.85 run and the Haiku run, 2 of 3 | `swing/h_vote.py` | 388 | 144 / 0.627 | not uploaded | $0 |
| 23:57 | `rear-lamp-swing-H-vote3.json` | The same three runs, 3 of 3 | `swing/h_vote.py` | 253 | 111 / 0.548 | not uploaded | $0 |
| 23:58 | `rear-lamp-swing-L-w85-drop12.json` | Sonnet weight 0.85, drop test-procedure and installation classes | `swing/l_filter.py` | 345 | 130 / 0.588 | not uploaded | $0 |

Lane G's local column is paragraph precision / recall / F2 against 67 silver bumper paragraphs. Every other row is requirement matched / F2 on the rear lamp. Empty cells were not recorded when the run was made.

**Sub-goal runs** (UN R175 0.1.0 to 1.0.0, `subgoal/dev`, 24 changes in the gold). The code of
each run was staged on top of `d8e9235` and not committed in between; the committed code (the
package `brain/brain/subgoal/`) reproduces `subgoal-dev-det-v4.json` byte for byte. Local scores
use `brain/brain/subgoal/score.py` (at the time `brain/eval/subgoal_score.py`).

| Run | File | Method | Code | Changes | Local flag recall / change accuracy / exact reasons | Platform (upload) | Spend |
|---|---|---|---|---|---|---|---|
| 23:18 | `subgoal-dev-det.json` | `brain.subgoal`, no model: unit alignment, templated reasons | `main` @ `d8e9235` plus staged `brain/brain/subgoal.py` | 24 (6 modified, 1 removed, 17 added) | 1.000 / 1.000 / 0.667 | (23:21:47) flag recall 100.0%, flag precision 100.0%, change accuracy 87.0% | $0 |
| 23:28 | `subgoal-dev-det-v2.json` | As above, plus: moved requirements take the new wording, items with their own modal stand alone, a clause after the last item applies to every item, run-in headings kept, "For X the Y shall A, and may B" gives "X may B", footnote markers ignored, merged units | `main` @ `d8e9235` plus staged changes | 24 (6 modified, 1 removed, 17 added) | 1.000 / 1.000 / 0.667 (new_text similarity 0.913, was 0.875) | (23:29:26) flag recall 100.0%, flag precision 100.0%, change accuracy 91.3% | $0 |
| 25 Oct 00:07 | `subgoal-dev-det-v3.json` | As v2, plus: a long or cut-off modified text drops its unfinished last fragment and unchanged sub-lists before its end; an item with its own modal keeps a procedure lead-in as "During …"; run-in headings read "For …, …" | `main` @ `d8e9235` plus staged changes | 24 (6 modified, 1 removed, 17 added) | 1.000 / 1.000 / 0.667 (new_text similarity 0.926; R-021 now equals the gold) | (00:08:18) flag recall 100.0%, flag precision 100.0%, change accuracy 95.7% | $0 |
| 25 Oct 00:11 | `subgoal-dev-det-v4.json` | As v3, but a modified requirement always keeps its own text with the edits applied (the task's rule); the new sentence only when an edit finds no place | `main` @ `d8e9235` plus staged changes | 24 (6 modified, 1 removed, 17 added) | 1.000 / 1.000 / 0.667 (new_text similarity 0.910) | (00:12:40) flag recall 100.0%, flag precision 100.0%, change accuracy 95.7% | $0 |
| 25 Oct 00:16 | `subgoal-dev-det-v5.json` | As v4, but a run-in heading stays in the quote and out of `new_text` (only 5.1.6.2 differs from v4): a one-row test | `main` @ `d8e9235` plus staged changes | 24 (6 modified, 1 removed, 17 added) | 1.000 / 1.000 / 0.667 (new_text similarity 0.909) | (00:18:03) flag recall 100.0%, flag precision 100.0%, change accuracy 95.7% | $0 |
| 25 Oct 00:41 | `subgoal-dev-det-v6.json` | As v4, plus: a name the new version no longer has (the old heading "Accelerator control misapplication test") becomes the system named in the scope ("ACPE test") | `main` @ `8a75a2a` plus the commit that adds the stale-name rule | 24 (6 modified, 1 removed, 17 added) | 1.000 / 1.000 / 0.667 (new_text similarity 0.915) | (00:44:21) flag recall 100.0%, flag precision 100.0%, **change accuracy 100.0%** | $0 |

## What is measured

**Case.** The rear lamp (`cases/dev-rear-lamp`) is the only case with expert answers: 190
requirements from 4 regulations (R148, R48, R150, R10) on 53 pages. Every run below is one
full pass on that case.

**The loop.** One run is:

1. `brain.pipeline` reads the spec and the exploded view and writes the submission JSON.
2. `tools/validate.py` checks the file against the platform format.
3. `tools/score_local.py` scores regulation and page level against `expected.json`.
4. `brain/eval/score.py` adds F2 and the requirement-level proxy.

**Scores.** The judges use F2, which weights recall four times as much as precision: a missed
requirement costs more than an extra one. All scores in the tables are F2.

| Level | What counts as a match | Scored by |
|---|---|---|
| Regulation | The cited regulation is in the answer | `tools/score_local.py` (official matching) |
| Page | Same regulation, version and page, or the same paragraph | `tools/score_local.py` (official matching) |
| Requirement | The requirement says the same thing as an expected one | The platform's LLM judge, after upload |

The requirement score in the tables is a local stand-in for the platform judge
(`brain/eval/judge.py`): word overlap within the same regulation, zero for opposite meaning,
a penalty for mismatched numbers. Use it to compare our own runs, not as the platform score.

**Cost.** The pipeline logs the tokens and dollars of every run. Responses are cached in
`brain/data/cache/llm/`, so rerunning a step is free, and the cost reported for a rerun is
what the cached responses cost when they were made. List prices in USD per million tokens:

| Model | Input | Output | Cache read |
|---|---|---|---|
| Claude Sonnet 5.5 (`claude-sonnet-5-5`) | 2 | 10 | 0.20 |
| Claude Opus 5.5 (`claude-opus-5-5`) | 4 | 20 | 0.20 |
| Claude Fable 5.1 (`claude-fable-5-1`) | 10 | 50 | 0.25 |

## Results

Each Claude row runs one model on every step: product profile, regulation review, paragraph
relevance and rewrite. Relevance cut-off 0.20.

### Platform scores

Each file in this folder was uploaded to the dev case on the submission platform on 24 Oct
2026, between 20:05 and 20:23 CEST. The requirement level is the platform's model judge.
Matched is recall times 190. The platform shows F1 for pages; page F2 here is computed from its
page precision and recall.

| File | Model | Requirements | Requirement P / R / F2 | Matched of 190 | Page P / R / F2 | Regulation P / R |
|---|---|---|---|---|---|---|
| `rear-lamp-deterministic.json` | None (deterministic) | 778 | 0.138 / 0.563 / **0.348** | 107 | 0.400 / 0.906 / 0.723 | 1.00 / 1.00 |
| `rear-lamp-sonnet.json` | Sonnet 5.5 | 344 | 0.407 / 0.737 / **0.634** | 140 | 0.817 / 0.925 / 0.901 | 1.00 / 1.00 |
| `rear-lamp-opus.json` | Opus 5.5 | 338 | 0.423 / 0.753 / **0.651** | 143 | 0.790 / 0.925 / 0.894 | 1.00 / 1.00 |
| `rear-lamp-fable.json` | Fable 5.1 | 332 | 0.449 / 0.784 / **0.682** | 149 | 0.781 / 0.943 / 0.905 | 1.00 / 1.00 |

All three models selected exactly the 4 expected regulations. Fable 5.1 scored highest on
requirements: 0.048 above Sonnet 5.5 for 5.4 times the cost, and 0.031 above Opus 5.5 for 2.6
times the cost. Opus 5.5 is 0.017 above Sonnet 5.5 for about twice the cost. These are single
runs, so read the gaps against the variance note below.

Where the extra matches come from, by the local judge (`brain/eval/judge.py`):

| Model | Rows from paragraphs not in the gold (match nothing) | Gold rows missed on a selected paragraph | Gold rows missed on a paragraph not selected |
|---|---|---|---|
| Sonnet 5.5 | 175 | 26 | 33 |
| Opus 5.5 | 160 | 37 | 14 |
| Fable 5.1 | 155 | 34 | 15 |

The stronger models choose paragraphs better: fewer wasted rows and fewer missed paragraphs.
The misses on selected paragraphs stay at 26 to 37 for every model. Those come from the
rewrite splitting less finely than the gold (one gold row per table row, list item or optional
case), which a larger model does not fix.

### Rewrite-only runs

These hold paragraph selection fixed: they rewrite exactly the 208 paragraphs that
`rear-lamp-fable.json` cites, with a different model or prompt (`brain/eval/rewrite_pass.py`),
so the gap to the Fable row is the rewrite alone.

| File | Rewrite | Requirements | Requirement P / R / F2 | Matched of 190 | Page P / R / F2 | Uploaded |
|---|---|---|---|---|---|---|
| `rear-lamp-qwen-split-rewrite.json` | qwen3.5:9b on Ollama, split prompt of `0ccae35` | 446 | 0.298 / 0.700 / **0.551** | 133 | 0.820 / 0.943 / 0.916 | 24 Oct 21:47 CEST |

- Against Fable's own rewrite of the same paragraphs (0.682, 149 matches) it loses 0.131. It
  writes 34% more rows and matches 16 fewer requirements.
- The prompt of `0ccae35` told the model to split every row of a table. On qwen that turned
  table references into dozens of rows with garbled cell values (UN R148 5.5.1, one gold row,
  became 25) and left 30 of the 208 paragraphs empty, five of them gold. `d7683cd` keeps table
  references whole and falls back to the deterministic rows for an empty answer.
- The run took 37 minutes on an M5 with 16 GB (52 batches of 4 paragraphs, temperature 0,
  thinking off) and cost nothing.

### Branch `kb-stack` runs

Uploaded on 24 Oct between 21:05 and 22:16 CEST. Every LLM step ran through `claude -p` or
`codex exec` on a subscription, so the dollar figures in the logs are what `claude -p` reports,
not a bill. Code is on branch `kb-stack` (not merged).

| File | Configuration | Requirements | Requirement P / R / F2 | Matched of 190 | Page P / R / F1 |
|---|---|---|---|---|---|
| `rear-lamp-main-cli.json` | `main` at `7644efe`: Opus relevance, Sonnet rewrite | 368 | 0.389 / 0.753 / **0.634** | 143 | 0.806 / 0.943 / 0.870 |
| `rear-lamp-kb-deterministic.json` | obligation base, no LLM | 864 | 0.125 / 0.568 / **0.333** | 108 | 0.418 / 0.925 / 0.576 |
| `rear-lamp-kb-jev.json` | `5f6e476`: obligation base, Jev blend cut 0.25, Opus everywhere | 389 | 0.396 / 0.811 / **0.670** | 154 | 0.781 / 0.943 / 0.855 |
| `rear-lamp-kb-jev-filter-v4.json` | `1d8b22e`: the above plus the requirement filter and the minimal-edit rewrite | 342 | 0.409 / 0.737 / **0.635** | 140 | 0.785 / 0.962 / 0.864 |
| `rear-lamp-kb-sol-rewrite.json` | the 214 paragraphs of `rear-lamp-kb-jev.json` rewritten by GPT-6.1 Sol with a prompt that names the device in every row | 420 | 0.340 / 0.753 / **0.606** | 143 | 0.794 / 0.943 / 0.862 |
| `rear-lamp-kb-v5-rewrite.json` | the same 214 paragraphs rewritten by Opus with that prompt | 363 | 0.408 / 0.779 / **0.659** | 148 | 0.781 / 0.943 / 0.855 |

- The minimal-edit rewrite lost 14 matches. Its rows drop the subject and the condition ("Test
  pulse 1 shall be applied ...", "In each direction a tolerance of ±3° shall be allowed."),
  which the platform judge does not match. The local judge scored the same file 0.717, its
  largest error so far.
- Sol's rewrite of the same paragraphs lost 11 matches against Opus's. It wrote 31 more rows,
  over-split a few paragraphs (UN R150 5.1.4.4.1 into 6 extra rows) and left 7 paragraphs
  without a requirement. The model and the prompt both changed, so this does not isolate the
  prompt.
- The same prompt on Opus lost 6 matches against the `kb-jev` rewrite, with 26 fewer rows,
  while the local judge counted 5 more. Both minimal-edit prompts (v4 and this one) scored
  higher locally and lower on the platform: the local judge rewards the regulation's own
  wording, the platform judge does not.
- With the LLM regulation review on, the obligation base changes no selected regulation on dev,
  synth-a06, the plain bumper or the bumper with sensors and fog lamp, against `main`'s
  selection with the same light-source rule. Without the LLM it keeps R150 on synth-a06 and R42
  on the plain bumper, which the lexical ranking alone drops.

### Branch `brain-model-mix-examples`: expert examples and the obligation cut

Run at 22:00, uploaded at 22:14 CEST. Code is on branch `brain-model-mix-examples` at
`e5e0d25` (not merged); the file is `rear-lamp-mix-examples-cut.json` with its log.

Configuration: `main`'s default models at `b7d6ee2` (Opus 5.5 for profile, regulation review
and relevance; Sonnet 5.5 for the rewrite), plus two rewrite changes behind flags:
- `BRAIN_REWRITE_EXAMPLES=1`: each paragraph comes with the three most similar paragraphs the
  dev experts cite (TF-IDF over the text) and the exact expert rows written from them, leaving
  out the paragraph's own regulation so it never sees its own answer.
- `BRAIN_REWRITE_CUT=obligation`: replaces the split-everything rule of `0ccae35` with one row
  per obligation, splitting only table rows, list items with their own values and optional
  cases.

| | Requirements | Requirement P / R / F1 / F2 | Matched of 190 | Page P / R / F1 | Regulation P / R |
|---|---|---|---|---|---|
| Platform | 341 | 0.405 / 0.726 / 0.520 / **0.627** | 138 | 0.831 / 0.925 / 0.875 | 1.00 / 1.00 |
| Local judge | 341 | 0.425 / 0.763 / 0.546 / 0.658 | 145 | 0.831 / 0.925 / 0.875 | 1.00 / 1.00 |

- 11 matches and 0.055 below Fable, and below the plain Opus run.
- The platform found 7 fewer matches than the local judge, where the Claude runs above scored 4
  to 9 more. The cut merges rows the experts keep apart; word overlap still counts a merged row,
  but the platform judge wants the same scope, condition and constraint. Like the minimal-edit
  rewrite on `kb-stack`, a style change that the local judge rewards lost on the platform.
- Relevance answers came from the cache of the Opus run, so the run paid only for the Sonnet
  rewrite ($1.13). From an empty cache it costs about $5.50.
- One upload; identical files have scored up to 7 matches apart.

### 24 Oct, 21:30 to 22:50: narrowed table rule, deterministic routing, Gemini relevance

- **qwen3.5:9b rewrite with the narrowed table rule** (`rear-lamp-qwen-split2-rewrite.json`).
  The same 208 paragraphs as `rear-lamp-qwen-split-rewrite.json`, with `d7683cd`: a paragraph
  that points at a table stays one requirement, and an empty model answer keeps the
  deterministic rows. Rows fall from 446 to 411 and inside gold paragraphs from 276 to 207;
  local matches rise from 137 to 143 (Fable's own rewrite: 141). Not uploaded yet. The local
  judge overcounted the previous qwen file by 4, so expect a platform score a little below the
  local one. The run lost 5 batches when the Ollama server stopped at 22:04; the rerun took the
  other 47 from the cache and recomputed those 5 (see the log).
- **Deterministic path with sibling routing** (`rear-lamp-deterministic-sibling.json`). The
  feature changes of `b7d6ee2`: sections next to one that names the product count as other
  devices, and a regulation whose title names the product (R42) counts as about it. On dev 647
  rows instead of 778, page F2 0.758 instead of 0.723, local requirement F2 0.394 instead of
  0.364. This is the Sunday fallback when no model is available. Uploaded 22:57: requirement
  P 0.164 / R 0.558 / F2 0.377 (106 matches), page P 0.480 / R 0.887 / F2 0.758, regulations
  1.00 / 1.00. Against the old deterministic file (0.348, 107 matches from 778 rows) it keeps
  the same matches with 131 fewer rows. The local judge counted 5 too many, as it does on
  verbatim text, so the upload confirmed the expected floor and added no new information.
  Without a model the path stays at about 0.35 to 0.38; the model-backed runs score 0.62 to
  0.68.
- **Gemini relevance** (`rear-lamp-gemini-relevance.log`, write-up in `brain/docs/gemini.md`).
  Paragraph level only, no submission. Gemini 3.5 Flash reaches AUC 0.974 on 1,100 dev
  paragraphs (gpt-5.5 0.968 on the same ones), but the free tier allows about 20 requests per
  model per day, and UN R48 was not reached.

### 25 Oct, 00:00: pointer rule and a split-less rewrite

- **Pointer rule.** Six rows of section-cut2 quote a paragraph that holds no obligation of its own: a heading with "See Table 4" or "See paragraph 4.6.", or a clause that only brings other paragraphs into force. None sits on a gold paragraph. Uploaded at 00:10: 150 matches on 326 rows, F2 0.691 (precision 46.0%, recall 78.9%), up from 0.682.
- **Approval-mark rule.** Nine rows spell out the approval mark the authority assigns: the circled E, the regulation number followed by R, the symbols. None is on a gold paragraph, and no gold row reads like one. Uploaded at 00:50: 149 matches on 317 rows, F2 0.692 (precision 47.0%, recall 78.4%), a tie with the pointer-rule file (150 on 326, 0.691).
- **Verbatim text.** The best file with each row's text swapped for its source sentence (285 of 317 rows; rows sharing a sentence keep the rewrite) scored 156 / 0.724 at 01:10, against 149 / 0.692 for the same rows rewritten: 7 more matches from wording alone, the first writing change that moved the platform. The expert rows keep the regulation's own sentence; the rewrite's narrowed subjects and added conditions cost matches.
- **Fragments rewritten.** Keeping the rewrite for the 75 rows whose quote is a list item, a clause ending in ";" or ":", or a table cell scored 146 / 0.678 at 01:52 (precision 46.1%, recall 76.8%), 10 matches under the all-verbatim file on the same rows. The platform prefers the raw fragment too; the pipeline uses the quote for every row whose quote is its own. The calibrated local judge had predicted +2.
- **Fragments quoted, sentences rewritten.** If the effects added up, quoting only the fragments would score 149 + 10 = 159. It scored 151 / 0.701 at 02:01 (precision 47.6%, recall 79.5%): above the all-rewrite file, below the all-quote file. The two halves interact, or the platform varies by several matches between uploads; quote everything stays the rule.
- **Sentence picking.** Fable's diagnosis said our rows break sentences where the expert does not: on paragraphs where our row count equals the gold count, 90% of gold rows match, against 68% elsewhere. So Opus rewrote the best file's 194 paragraphs as one row per obligation sentence (396 rows), each row took its sentence as text, and Opus p_keep plus the section cut chose 285. Locally it reached 181 gold rows and matched the gold count on 80 paragraphs (78 for the best file). Uploaded at 01:25: 142 matches, F2 0.679 (precision 49.8%, recall 74.7%), 14 matches under the verbatim file. Whole sentences picked afresh convert worse than our rewrite's rows with their own quotes; the row boundaries the int prompt draws are worth keeping.
- **The Sunday pipeline with verbatim text.** `ready-for-main` run fresh on dev, with the fixed Jev and the cut tuned for the bumper (filter 0.40, linear section cut), then the verbatim swap. Its paragraphs reach 175 gold rows against 183 for the best file, so we expected 0.66 to 0.70. Uploaded at 01:45: 156 matches on 366 rows, F2 0.693 (precision 42.6%, recall 82.1%). It matches as many rows as the best file, 89% of the reachable gold rows against 85%: the verbatim gain carries over to a fresh run, and the extra 49 rows are what separate it from 0.724.
- **kb-jev with the Sunday cut.** The 154-match `kb-jev` upload, cut to 326 rows with main's rule (filter 0.40, linear section cut 0.2, the three rules), scored 148 / 0.681 at 01:01: the cut cost 6 matches, where on the recall-push rows it cost one. Pages recall fell to 92.5% (98.1% for section-cut2-mark).
- **Split-less rewrite.** The expert list has 184 rows on the gold paragraphs we cite; our rewrite writes 223. A rule of one requirement per sentence, split only at list items, brings that to 176. After the section cut, 151 gold rows can still pair with a row on their own paragraph, against 169 before, so the platform may find fewer matches even though precision rises. The paragraph estimate (matches as 149/183 of the gold rows on cited paragraphs) cannot see that, so this file needs an upload to settle it. Uploaded with the approval-mark rule at 00:42: 140 matches on 271 rows, F2 0.679 (precision 51.7%, recall 73.7%). Writing fewer rows per paragraph lost 10 matches, more than the precision gained; the platform pays for the expert's split.
### 24 Oct, 23:18: the sub-goal on dev, no model

`subgoal-dev-det.json`, from `brain.subgoal` (design in `docs/regulation-change.md`). Both PDFs
go through `brain.ingest`; old and new sentences and list items are aligned on normalised words,
and the reasons are filled from a word diff. Flag recall 1.000 and change accuracy 1.000 against
`subgoal/dev/expected.json`, with no extra rows; the old `scripts/diff_regulation.py` scored
0.708 / 1.000 with 8 extra rows. 16 of 24 reasons match the gold exactly. The other 8 differ
where the gold is not consistent: edit order (R-018), one replacement written as several word
edits (R-021), the heading of old 6.5 counted as removed (R-084), edits it leaves out (R-085),
two added quotes cut at 109 instead of 99 characters (5.1.4.1, 6.5.3), one quoted whole at 106
(6.6.1.1), and one that quotes the lead-in instead of the item (6.6.2.1). `new_text`
similarity is 0.875. The run takes about 1 s and passes
`tools/validate.py --requirements-old`.

Uploaded at 23:21:47: flag recall 100.0%, flag precision 100.0%, change accuracy 87.0%. 87.0%
reads as 20 of 23, not 21 of 24 (that would show 87.5%), and Coffee and more's 95.7% is 22 of
23. So the platform most likely judges `new_text` on the 23 rows that have one, and three of
ours were judged wrong. The platform does not say which.

`subgoal-dev-det-v2.json` (23:28) targets the texts that read wrong, not only differently:
6.6.2.2 (e) read "shall be to in the case …" (the item has its own "shall"), 6.6.2.1 (a)
lacked "as reasonably practical …" (a clause after the last item), 5.1.6.2 lacked "while
creeping" (its run-in heading), 6.6.1.1's second row had the ACPE as subject, and R-084 and
R-086 kept the name of a test the new version no longer has. Each fix is a general rule with a
unit test (`brain/tests/test_subgoal.py`). Flags and change types are the same as the 23:18
file. Uploaded at 23:29:26: flag recall 100.0%, flag precision 100.0%, change accuracy 91.3%
(21 of 23, one more than the first file).

`subgoal-dev-det-v3.json` (25 Oct 00:07) fixes R-021, the one text that lost content. The old
requirement is 2,000 characters, cut by the schema mid-clause ("… and the vehicle is"), and its
amended text was 2,524 characters, so the v2 file cut the end and lost the amended items (d)(ii)
to (iv). Now an unfinished last fragment goes first, then the largest sub-list that holds no
edit ("(c) …, i.e.: (i) … (iv) …" becomes "(c) …;"), and the end is cut only if that is not
enough. The result equals the gold's R-021 character for character, which suggests the gold was
shortened the same way. Two smaller texts read better: 6.6.2.2 (e) keeps its procedure ("During
the procedure for each test with a creeping vehicle, in the case …") and 5.1.6.2 reads "For
acceleration while creeping, in the case …". Uploaded at 00:08:18: flag recall 100.0%, flag
precision 100.0%, change accuracy 95.7% (22 of 23).

The one row left is most likely R-085. Every other row says what the gold says, most of them word
for word. Our R-085 is the new 6.6 sentence: "The test procedures shall be performed both in a
forward and rearward direction and at least with the ACPE interventions triggered at …". The
gold leaves out "both in a forward and rearward direction", although both the old requirement
and the new paragraph contain it, and its own reason does not list that as an edit. Matching it
would mean dropping a provision the regulation still has, so the text stays as it is.

Reading the three uploads together points elsewhere, though. v1 had 3 rows wrong, v2 2, v3 1.
R-021 was wrong in v1 and v2 and fixed in v3, and v1's 6.6.2.2 (e) was broken ("shall be to in
the case …"). v2 fixed two rows and broke one. Of the rows v2 changed, R-084, R-086, 6.6.2.1 (a)
and 6.6.1.1 now equal the gold word for word, so the broken one is R-085 (or, less likely,
5.1.6.2). v2 had started giving moved requirements the new sentence, and R-085 became "The test
procedures shall …" instead of v1's "The accelerator control misapplication test procedures
shall …": the scope was lost. `subgoal-dev-det-v4.json` (00:11) goes back to the task's own rule
("the old requirement's text with the paragraph's edits applied") for every modified row, which
keeps each requirement's explicit subject. R-084, R-085 and R-086 are again v1's texts; every
other row is v3's. Uploaded at 00:12:40: change accuracy still 95.7%, so R-085's subject was not
the problem.

With four uploads, three explanations fit the scores. (1) R-085 fails for "both in a forward and
rearward direction", which v1, v3 and v4 all keep and the gold drops; no general rule removes a
clause the new paragraph still has. (2) 5.1.6.2 fails in every phrasing. (3) 5.1.6.2 fails only
when its run-in heading is written into the text: v1 sent the bare sentence, v2 to v4 the
heading. Only (3) has a general fix, so `subgoal-dev-det-v5.json` tests it: it differs from v4
in that one row. Uploaded at 00:18:03: still 95.7%, so (3) is ruled out and the v5 rule is
reverted; the code again writes v4's file byte for byte.

**Where this left the sub-goal on dev at 00:18** (overtaken at 00:44, see the next section):
flag recall and flag precision 100%, change accuracy
95.7% (22 of 23), with general rules only. The last row is most likely R-085: the gold drops
"both in a forward and rearward direction", which the old requirement and the new paragraph
both contain and which its own reason does not list as an edit. Matching it would mean deleting
regulation text, which no general rule should do, so the 22 of 23 stands. The final dev file is
`subgoal-dev-det-v4.json`.

### 25 Oct, 00:41: names the new version no longer has

`subgoal-dev-det-v6.json` tests a second explanation for R-085: its subject. v3 sent "The test
procedures shall …" (the new sentence, no scope) and v4 "The accelerator control misapplication
test procedures shall …" (the old name); both scored 95.7%. The gold says "The ACPE test
procedures". The old name comes from the heading of old 6.5, and the words "accelerator control
misapplication test" appear nowhere in the new version, so the name is stale. The rule: when the
heading of a requirement's old paragraph (or of its parents) appears nowhere in the new version,
its name in the modified text becomes the system the regulation's scope defines ("ACPE", from
"… (ACPE)" in section 1) plus the head noun: "ACPE test". Without a system defined in the scope,
only the head noun stays. On dev it changes R-084 ("For the ACPE test, …"), R-085 ("The ACPE test
procedures …") and R-086 ("The procedure for each ACPE test …"); on R148, R10 and R48 with the
main goal's rows it changes nothing.

Uploaded at 00:44:21: flag recall 100.0%, flag precision 100.0%, change accuracy 100.0%. So the
last row was R-085's subject, not the clause "both in a forward and rearward direction" that the
gold drops: the judge accepts the extra clause but not a scope it cannot place. The earlier
reading (a gold inconsistency, not worth a rule) was wrong; the rule is general and costs
nothing elsewhere. v6 is the dev file of record.

### Cost per run

From the pipeline logs (`rear-lamp-<model>.log`).

| Model | Calls | Tokens in / out | Cost |
|---|---|---|---|
| None (deterministic) | 0 | 0 | $0 |
| Sonnet 5.5 | 137 | 844k / 158k | $3.08 |
| Opus 5.5 | 138 | 867k / 159k | $6.36 |
| Fable 5.1 | 136 | 860k / 173k | $16.52 |

### Local proxy against the platform

The same files scored offline with `brain/eval/score.py`, next to the platform. The last row is
the earlier OpenAI upload (`brain/out/dev-upload.json`: gpt-5.5 relevance, gpt-5.4-mini
rewrite).

| File | Matched, platform | Matched, local judge | Requirement F2, platform | Requirement F2, local judge |
|---|---|---|---|---|
| `rear-lamp-deterministic.json` | 107 | 112 | 0.348 | 0.364 |
| `rear-lamp-sonnet.json` | 140 | 131 | 0.634 | 0.593 |
| `rear-lamp-opus.json` | 143 | 139 | 0.651 | 0.633 |
| `rear-lamp-fable.json` | 149 | 141 | 0.682 | 0.646 |
| `brain/out/dev-upload.json` | 145 | 138 | 0.621 | 0.591 |
| `rear-lamp-qwen-split-rewrite.json` | 133 | 137 | 0.551 | 0.568 |
| `rear-lamp-mix-examples-cut.json` | 138 | 145 | 0.627 | 0.658 |

The local judge ranks the three Claude runs in the platform's order. On their rewrites it finds
4 to 9 fewer matches than the platform. It finds more than the platform on the deterministic
file's verbatim sentences (5 more) and on qwen's short split rows (4 more). Its error depends on
the writing style, so it cannot compare two rewrite styles; upload to the dev case for that, or
use a model judge calibrated against these rows (`brain/docs/todo/01-model-judge.md`). Regulation and page levels match the platform, since both use
`tools/score_local.py`.

### Which code produced the files

- **Claude runs:** commit `fd2777b` on branch `brain-claude-models` (troy, 24 Oct 19:58), which
  is `edc8f1f` on `main` plus the `BRAIN_MODEL` switch, streamed Claude requests and cost
  logging. The runs are from 19:49 to 19:57. The files moved here in `f018379` and reached
  `main` in `d730a11`; `5d9ae13` set `team_id` to `team-06` for the upload.
- **Deterministic run:** the no-LLM path at `edc8f1f`, which later commits on `main` have not
  changed. A rerun on `main` gives the same 778 requirements, row for row.
- **Prompts in these runs:** the domain-neutral relevance prompt with cut-off 0.20, and the
  rewrite prompt with parent clauses. Three of that rewrite prompt's four few-shot examples are
  dev gold answers (UN R48 6.4.4.2, UN R48 5.7.1, UN R150 4.1.1), which flatters the dev score by
  a few rows.

- **Rewrite-only qwen run:** the rewrite prompt and `llm.py` of `0ccae35` (split rules,
  temperature 0 for local models), qwen3.5:9b through Ollama 0.40.10 at a 16k context, on the
  paragraphs of `rear-lamp-fable.json`. The harness became `brain/eval/rewrite_pass.py` in
  `dcf1740`.

Each run's submission and log are in this folder: `rear-lamp-deterministic.json`, and
`rear-lamp-<model>.json` with `rear-lamp-<model>.log` (the pipeline log, which ends with the
token count and cost). All submissions pass `tools/validate.py`.

### Earlier run

`brain/out/dev-llm.json` came from an older version of the pipeline: Opus for profile,
review and relevance with cut-off 0.10, and Sonnet for the rewrite. It selected R26 as a fifth
regulation. Rescored with today's proxy: regulation F2 0.952, page F2 0.877, requirement F2
0.591, requirement recall 0.726. Its cost was not tracked.

### Big swings, 24 Oct 23:14

Seven lanes on branch `big-swings`, scored locally because the platform hour was already at 4 of 5 uploads. Full write-up: the Results section of `brain/docs/todo/07-big-swings.md`.

Agreement across existing runs is the lamp result that moves requirement F2: votes of 7 or more match 156 of 190 in 351 rows (F2 0.702), against Fable's local 141 / 0.646. Writing the low-relevance tail, hedging two cuts, a verbatim rewrite, and a learned row selector do not beat that. On the bumper, one Sonnet run at blend weight 0.85 is the Sunday file (plain paragraph F2 0.838, about $1.15 cold; fog F2 0.779, $4.33). A Haiku vote barely moves bumper F2. Spend for the task: $14.92.

### Complex strategies, 25 Oct 00:02

Five lanes on branch `big-swings`, scored locally. The owner closed the platform queue at 23:36. Full write-up: the Results section of `brain/docs/todo/08-complex.md`.

Splitting the collapsed pulse and voltage lines of UN R10 6.9.1 is the only local gain: votes7 plus those table rows is 379 rows, 163 matched, F2 0.716. The four expert-skip classes do not beat votes7 on the 7-vote file (best cut 271 / 142 / 0.689) or on the 4-vote file (best cut 407 / 158 / 0.677). A vote of three new runs loses to the reused Opus file (144 / 0.627 against 146 / 0.636). Sonnet at blend weight 0.85 on the lamp is 136 / 0.585, and the skip filter leaves it at 130 / 0.588. Sunday stays one Sonnet run at weight 0.85 on the bumper. Spend for this task: $4.34, all of it lane H. Event total $19.26 of the $70 ceiling.

The owner uploaded `rear-lamp-swing-I-tables.json` at 25 Oct 00:22:08 CEST (379 requirements, 224.5 KB). Scored at 00:22:51. Requirements: precision 0.385, recall 0.768, F1 0.513, F2 0.641, which is 146 of 190. Pages: precision 0.831, recall 0.925, F1 0.875. Regulations: 1.00 / 1.00. The platform is 17 matches and 0.075 F2 under the local judge, and 3 matches and 0.041 F2 under Fable's platform score of 149 / 0.682.

## Run-to-run variance

The same model on the same case does not give the same output. A first Sonnet 5.5 run cited
69 pages (page F2 0.872) where the run in the table cited 60 (page F2 0.901). Treat
differences of a few points between single runs as noise. For a decision that depends on a
small gap, run each model more than once on fresh caches.

## Reproduce

`BRAIN_MODEL` and the cost log exist only on branch `brain-claude-models` (`fd2777b`), not on
`main`. On `main`, set `BRAIN_MODEL_STRONG` and `BRAIN_MODEL_BULK` to the same model id instead;
the run then logs no cost.

From `brain/` on that branch, with `ANTHROPIC_API_KEY` and `BRAIN_LLM=anthropic` in `brain/.env`
(see `brain/.env.example`):

```bash
out=../out/rear-lamp-sonnet
BRAIN_MODEL=sonnet uv run python -m brain.pipeline ../cases/dev-rear-lamp -o $out.json 2> $out.log
uv run python ../tools/validate.py $out.json
uv run python ../tools/score_local.py $out.json
uv run python -m eval.score $out.json
```

`BRAIN_MODEL` takes `sonnet`, `opus`, `fable`, `haiku` or a full model id. A rerun reads the
cache and costs nothing; to measure a model again, move `brain/data/cache/llm` aside first.

Paid runs need the owner's approval and a cost estimate first (see `CLAUDE.md`). Measured cost
of one rear lamp run: Sonnet 5.5 about $3, Opus 5.5 about $6.50, Fable 5.1 about $16.50.
