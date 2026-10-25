# Thesis ledger

What we believe about scoring on the dev rear lamp, and the run that settled each belief. Upload numbers are platform matches out of 190; the files and methods are in the run log in [README.md](README.md). Statuses:

- **proved**: an upload or an exact local count settles it;
- **supported**: the evidence points one way, with room for noise;
- **refuted**: it lost;
- **open**: not yet tested;
- **shelved**: not worth a slot.

Two measures recur:
- **reach**: gold rows on paragraphs we cite. The paragraph metric counts it exactly from the files.
- **subset upload**: a file holding only some rows. Its matches are those rows' exact contribution.

## Step by step: where the 0.724 file (156 matches, 317 rows) loses

| Step | Gold rows left | Lost |
|---|---|---|
| Regulations | 190 | 0 |
| Selection and rewrite | 184 | 6 |
| Section cut and rules | 183 | 1 |
| Platform match | 156 | 27: 13 because we have fewer rows than gold on that paragraph, 14 with a row that doesn't match |

Precision side: 106 rows on paragraphs gold doesn't cite, and 41 rows beyond gold's count on gold paragraphs.

## Theses

| # | Thesis | Status | Evidence | Next |
|---|---|---|---|---|
| 1 | Regulation choice is solved | proved | 4 of 4 on dev in every run | Check on the bumper |
| 2 | Selection loses little on dev | proved | Reach 184 of 190 before cuts | Bumper unknown: Jev was fit on dev |
| 3 | Relative cut 0.20 or 0.15 beats 0.25 | supported | Dev reach +7 at 0.20; bumper silver hits 42 → 44 (0.20) and 48 (0.15) | Rewrite only the new paragraphs, then upload |
| 4 | Rows on paragraphs gold doesn't cite match nothing | supported | Every cut upload landed within about 1 match of the paragraph metric, which assumes this | none |
| 5 | The judge rewards the regulation's own words over completed or reworded text | supported | Verbatim 149 → 156. Fragment subset: 53 as bare quotes, 45 as standalone sentences. Full file, fragments quoted vs rewritten: 151 vs 146 | Keep quoting; stop rewording |
| 6 | Plain sentence extraction converts as well as split and quote | refuted | Reach → matches: no-LLM 157 → 107, sentence-pick 181 → 142, splitless 175 → 140, ours 183 → 156 | none |
| 7 | Fewer, coarser rows score better | refuted | Splitless −9, sentence-pick −14 | none |
| 8 | Matches follow the count ceiling: per paragraph, at most min(our rows, gold rows) | supported | Ceiling against matches: 170/156, 171/154, 151/140, 122/107 | none |
| 9 | Under-splitting costs about 13 matches | open | 13 gold rows on cited paragraphs have no row of ours to pair with | One row per list item or table row where a paragraph has more items than rows, quoted |
| 10 | Extra rows on over-split paragraphs are pure cost | open | 80 rows on 27 paragraphs that hold 39 gold rows | Subset upload `thesis-oversplit` (25 Oct 02:45) |
| 11 | A stronger or different rewrite model helps | refuted | Sonnet, Sol, local models and Fable all land at 140–154; Fable's +6 came in an older setup | none |
| 12 | Voting over several runs helps | refuted | 7-run vote: 146 | none |
| 13 | An agent with file tools beats the pipeline | refuted | agent-v3: 116 | none |
| 14 | A hard p_keep filter at 0.40 helps | refuted | It cost kb-jev 6 matches | none |
| 15 | An Opus "would an expert cite this paragraph" pass improves selection or cuts | refuted | Local: as a cut, reach falls 183 → 179 at p ≥ 0.1; as a selector, 99 of 121 gold paragraphs at 521 paragraphs | none |
| 16 | Our local judge can rank writing changes | refuted | Own-subject: +13 local, +1 platform. Verbatim2: +2 local, −10 platform | Use subset uploads for writing questions |
| 17 | Identical content can score up to about 7 matches apart | open | Reported in the knobs review, not yet reproduced by us | Re-upload one subset unchanged |
| 18 | Paragraph labels don't matter at the requirement level | shelved | At most 3 gold rows have different labels, so the payoff is under 1 point | none |
| 19 | Writing several wordings of each fragment wins more | shelved | An extra row pays only above a 15% hit rate, which would need 90+ matches against 53 | none |
