# Thesis ledger

What we believe about scoring on the dev rear lamp, and the run that settled each belief. Upload numbers are platform matches out of 190; the files and methods are in the run log in [README.md](README.md). Statuses:

- **proved**: an upload or an exact local count settles it;
- **supported**: the evidence points one way, with room for noise;
- **refuted**: it lost beyond noise;
- **open**: untested or confounded;
- **shelved**: not worth a slot.

Measures:
- **reach**: gold rows on paragraphs we cite.
- **capacity**: the sum over paragraphs of min(our rows, gold rows). It bounds matches only if the judge pairs within paragraphs (thesis 8).
- **subset upload**: a file holding only some rows. Its matches equal those rows' share of the full file only if pairing is context-free, which is unproven. Subsets covering whole paragraphs are the safest.

**Noise.** The same Fable file scored 149 and 142, uploaded a minute apart. Treat any single-pair difference under about 7 matches as noise. The 156 file is the best of about 30 uploads, so its expected score is lower.

## Where the 0.724 file (156 matches, 317 rows) loses

| Step | Gold rows left | Lost |
|---|---|---|
| Regulations | 190 | 0 |
| Selection and rewrite | 184 | 6 by label; 1–3 by content (R150 Table 3 and Table A6-1 are covered under the parent paragraph; gold 4.5.3 and 5.18 sit beside our 4.5.3.1 and 5.18.1) |
| Section cut and rules | 183 | 1 |
| Platform match | 156 | 27. Capacity is 170, so 13 would need more rows on their paragraph if pairing is within paragraphs. |

## Theses

| # | Thesis | Status | Evidence | Next |
|---|---|---|---|---|
| 1 | Regulation choice is solved | proved | 4 of 4 on dev in every run | Check on the bumper |
| 2 | Selection loses little on dev | proved | Reach 184 of 190 before cuts, and 1–3 rows by content | Bumper unknown: Jev was fit on lamp regulations |
| 3 | Relative cut 0.20 or 0.15 beats 0.25 | open | Local dev reach +7 at 0.20, but the only platform pair goes the other way (0.20: 150, 0.25: 154), confounded with filter and prompt | Clean A/B upload |
| 4 | Rows on paragraphs gold doesn't cite match nothing | proved | `thesis-offgold`: those 106 rows alone match 2. Dropping them all would give F2 about 0.78 at the 0.724 file's mean of about 154 matches | A gold-free signal that finds them: the biggest lever left |
| 5 | The judge rewards the regulation's own words | supported for fragments, open for full sentences | 2×2 of the cut2-mark uploads: both quoted 156, fragments only 151, full sentences only 146, neither 149. Only the all-quoted cell stands out (+7, at the noise limit). Subset: Opus-completed fragments 45 against 53 as quotes | Keep quoting; replicate the 0.724 file |
| 6 | Plain sentence extraction converts as well as split and quote | refuted | Reach → matches: no-LLM 157 → 107, sentence-pick 181 → 142, splitless 175 → 140, ours 183 → 156 | none |
| 7 | Fewer, coarser rows score better | refuted | Splitless −9, sentence-pick −14 | none |
| 8 | The judge pairs only within paragraphs (capacity bounds matches) | refuted as a hard rule | `thesis-nolabels`: the same 317 texts cited as paragraph 1 still match 93. Pairing across paragraphs happens, so capacity is a soft guide, not a bound | none |
| 9 | Under-splitting costs matches, and adding the missing obligations wins them back | refuted locally for a broad pass | Capacity 170 against reach 183. Amp: 7 slots from merged separate obligations, 6 from obligations we don't write at all. An Opus pass adding every uncovered obligation as an exact quote (`bench-out/thesis/coverage.py`) added 108 rows for +8 capacity: 7% per row, below the 14.5% break-even. p_section doesn't pick out the useful ones | Only a much more targeted repair |
| 10 | Over-split paragraphs waste rows | supported | Subset of the 80 rows on 27 paragraphs where ours > gold (39 gold rows): 24 matches | Gold-free rules: 20 and 21 |
| 11 | A stronger or different rewrite model helps | refuted for a fresh Opus run | Sonnet, Sol, local models and Fable all land at 140–154. `opus-fresh` (same prompt, 342 rows, capacity 177): 146, about 8 below the 0.724 file's mean | none |
| 12 | Voting over several runs helps | shelved | The 7-run vote (146) also split R10 table rows, so it's confounded | none |
| 13 | An agent with file tools beats the pipeline | refuted | agent-v3: 116 | none |
| 14 | A hard p_keep filter at 0.40 helps | open | kb-jev with filter and section cut: matches 154 → 148, but F2 0.670 → 0.681; confounded | none planned |
| 15 | An Opus "would an expert cite this" pass improves selection or cuts | refuted | Local: as a cut, reach 183 → 179 at p ≥ 0.1; as a selector, 99 of 121 gold paragraphs at 521 paragraphs | none |
| 16 | Our local judge can rank writing changes | refuted | Own-subject: +13 local, +1 platform. Verbatim2: +2 local, −10 platform | none |
| 17 | Identical content scores up to about 7 apart | proved | Fable file: 149 and 142. The 0.724 file: 156, then 152 when re-uploaded unchanged. Near-identical cut2, cut2-rules and cut2-mark: 149, 150, 149 | Compare candidates against about 154, the 0.724 file's mean |
| 18 | Correct paragraph labels matter for requirement matching | proved | Same texts: 156 with our labels, 93 with every row cited as paragraph 1. Labels are worth about 63 matches | Label table rows and parent/child paragraphs the way gold does |
| 19 | Several wordings per fragment win more | shelved | An extra row pays only above a 14.5% hit rate | none |
| 20 | A list of cases or alternatives under one obligation is one gold row | supported | `consolidate` (with 21): 164 matches from 287 rows, F2 0.783, against the 0.724 file's mean of about 154 from 317. +10 is past the noise limit on one draw | Replicate; then apply the MERGE/SPLIT rule in the pipeline for the bumper |
| 21 | Rows sharing one quote are one gold row | supported, together with 20 | Shipped in the same file as 20, so the two aren't separated | none: both go in |
| 22 | Capacity predicts matches between files | refuted | `opus-fresh` had capacity 177 against the 0.724 file's 170 and matched 146 against about 154. More rows on gold paragraphs is not more matches | Judge candidates by upload, not by capacity |
