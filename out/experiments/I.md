# Lane I: one row per value in a table, added to the 7-vote file

State: running. Updated: 24 Oct 23:45 CEST.
Approved spend: $0 at launch. The ledger at 23:33 allows a planned $1; this lane does not use it. Spent: $0.
No paid calls. No Sonnet. Rows come from the source text of the table.

Question: expanding UN R10 6.9.1 and Annex 9 3.1, and any similar table the vote collapsed, recovers matches the local judge can see. Does it, and at how many extra rows?

Baseline: `out/rear-lamp-swing-A-votes7.json`, 351 rows, 156 matched, F2 0.702. Missed on a cited paragraph: 23.

A value line is one cell that states a number: one pulse, polarity, or test method, in one supply system or one frequency band. "Not applicable" is not a value line. A new row is dropped when its token Jaccard against a votes7 row on the same paragraph is 0.6 or above and the two rows cite the same value numbers (lane A's number rule: different numbers are not the same requirement).

## Checklist

- [x] I1 List candidate paragraphs before spending. Done 23:37. Files: `out/experiments/I.md`.
      Commit: this commit. Found: four EMC paragraphs in votes7, listed below. Two are collapsed
      tables (6.9.1, 6.8.2.1), one is a table with the 12 V lines missing (6.7.1), and Annex 9 3.1
      is already one row per modulation line. Photometric tables were seen and left alone.
      Spend $0.
- [x] I2 Emit one row per value line. Drop paraphrases. Union with votes7. Done 23:45. Files:
      `brain/swing/i_tables.py`, `out/rear-lamp-swing-I-tables.json`,
      `out/rear-lamp-swing-I-tables.log`, `out/experiments/I-lines.json`. Commit: this commit.
      Found: 33 value lines parsed, 28 kept, 5 dropped. Kept 12 on 6.9.1, 14 on 6.8.2.1, 2 on
      6.7.1 (the 12 V lines). Dropped the two 6.7.1 24 V lines (Jaccard 1.0, same numbers) and
      all three Annex 9 3.1 modulation lines (Jaccard 1.0 against votes7). Union is 379 rows.
      Spend $0.
- [ ] I3 Score the union. Matches gained on those paragraphs, rows added, F2, and missed-on-cited
      against 23.

Next: `python tools/validate.py out/rear-lamp-swing-I-tables.json`,
`python tools/score_local.py out/rear-lamp-swing-I-tables.json`, and from `brain/`
`uv run python -m eval.score` and `uv run python -m eval.errors` on the union and on votes7.

## Candidates

Counted from `brain/data/corpus/UN_R10_base.jsonl` and the laid-out pages of
`regulations/pdf/UN_R10/base/UN_R10_base.pdf` (pages 10 to 12 and 98). votes7 row counts are
from `out/rear-lamp-swing-A-votes7.json`. Every one of these can be split from that source
text without a model.

| Paragraph | Page | What the source is | Value lines | votes7 rows | Decision |
|---|---|---|---|---|---|
| UN R10 6.9.1 | 12 | Tables 3a and 3b, pulse and voltage levels | 12 | 3 umbrellas, none of the voltages | Emit 12 |
| UN R10 6.8.2.1 | 11 | Tables 2a and 2b, frequency band and test level by method | 14 | 3 umbrellas, none of the levels | Emit 14 |
| UN R10 6.7.1 | 10 | Table 1, maximum pulse amplitude | 4 | 3 (umbrella + the two 24 V lines) | Emit the 2 missing 12 V lines |
| UN R10 Annex 9 3.1 | 98 | Modulation list (a) AM, (b) PM2, (c) PM3 | 3 | 5, one per modulation plus two prose rows | Already split. Do not emit |

### UN R10 6.9.1, Tables 3a and 3b

votes7 keeps three sentences: the method (ISO 16750-2 and ISO 7637-2, "levels given in Tables 3a and 3b"), the FPSC rule for pulses 1, 2a, 2b, 3a and 3b, and the starting-profile rule pointing at ISO 16750-1. None of them carries a voltage, a pulse count, or a class letter from the tables.

Table 3b, one line per pulse and per system. Duration and the two FPSC classes sit on that same line.

| Pulse | 12 V | 24 V | Duration | Related | Not related |
|---|---|---|---|---|---|
| 1 | -75 V | -450 V | 500 pulses | III | III |
| 2a | +37 V | +37 V | 500 pulses | I | III |
| 2b | +10 V | +20 V | 10 pulses | II | III |
| 3a | -112 V | -150 V | 1 h | I | III |
| 3b | +75 V | +150 V | 1 h | I | III |

Table 3a, starting profile, one line per system. Both systems are level II, 10 pulses. Functional status: B for an ESA which shall be operational during engine start phases, and C for other ESA, under functions related to immunity related functions; D under functions not related to immunity related functions. The sentence after the table (starting profile only for ESAs that could be installed on an internal-combustion engine started with a 12 V/24 V starter motor) is the condition on these two lines, not a thirteenth line.

12 lines. Subject: immunity of the ESA to transient disturbances conducted along 12/24 V supply lines.

### UN R10 6.8.2.1, Tables 2a and 2b

votes7 keeps the method sentence and two pointers ("given in Table 2a", "given in Table 2b"). Methods, in column order: stripline, TEM cell, BCI, ALSE, reverberation chamber. Ranges below 2 GHz, same order: 20 to 400 MHz, 20 to 200 MHz, 20 to 400 MHz, 80 to 2,000 MHz, LUF to 2,000 MHz. Above 2 GHz only ALSE and the reverberation chamber apply (2,000 to 6,000 MHz); the other three cells are "Not applicable".

Table 2a, test level in over 90 per cent of the 20 to 6,000 MHz band:

| Method | Below 2 GHz | Above 2 GHz |
|---|---|---|
| Stripline | 60 V/m | not applicable |
| TEM cell | 75 V/m | not applicable |
| BCI | 60 mA | not applicable |
| ALSE | 30 V/m | 10 V/m |
| Reverberation chamber | 21 V/m | 7 V/m |

Table 2b, minimum test level over the whole band. Same ranges.

| Method | Below 2 GHz | Above 2 GHz |
|---|---|---|
| Stripline | 50 V/m | not applicable |
| TEM cell | 62,5 V/m | not applicable |
| BCI | 50 mA | not applicable |
| ALSE | 25 V/m | 8 V/m |
| Reverberation chamber | 18 V/m | 6 V/m |

14 lines. Subject: immunity of the ESA to electromagnetic radiation.

### UN R10 6.7.1, Table 1

| Polarity | 12 V | 24 V |
|---|---|---|
| Positive | +75 V | +150 V |
| Negative | -100 V | -450 V |

votes7 already has the two 24 V lines, in the form "the positive/negative pulse amplitude for vehicles with 24 V systems shall not exceed ...". The 12 V lines are absent. Emit those two, in that same form, with +75 V and -100 V. Do not restate the method sentence.

### UN R10 Annex 9 3.1

The source is three modulation clauses, not a grid:

- (a) AM, 1 kHz, 80 per cent, 20 to 400 MHz
- (b) PM2, Ton 3 µs, period 3,333 µs, 2,700 to 3,100 MHz
- (c) PM3, Ton 500 µs, period 1,000 µs, 380 to 2,700 MHz and 3,100 to 6,000 MHz

votes7 R-0049, R-0050 and R-0051 are those three clauses, plus the 20 to 6,000 MHz measurement sentence and the dwell-time sentence. Every measurement token in the source is already in the vote. A new row would be a paraphrase. Leave it listed. Do not spend, and do not emit.

### Seen, not candidates

These cited paragraphs are not a collapsed pulse, voltage, frequency-band, or modulation table:

- UN R10 6.5.2.1 and 6.6.2.1. Three frequency-band sentences each. votes7 already has one row per band, and no measurement token is missing. Not a table.
- UN R10 Annex 9 3.2. One sentence listing spot frequencies as an alternative procedure. Not a table. A second cut of that sentence would be a copy.
- UN R148 5.2.1 (Table 4), 5.5.1 (Table 7), 5.8.1 (Table 10), Annex 8 2.1 (Table A8-1), and UN R150 5.1.4.4.1 (Table 3). The vote does collapse these into "see Table N", but the cells are luminous intensities and retro-reflection coefficients, not pulses, voltages, frequency bands, or modulation types. Left alone.
- UN R148 5.2.2 and 5.5.2. Pointers ("See Table 4", "See Table 7"), not tables.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

No nomination unless the union's local F2 beats 0.702 by more than about 5 matches.

## Notes

Gold is used only at scoring. The lines above were taken from the regulation text. Paragraphs that would need a model to split are none: the four candidates are readable from the source. Approved spend is $0, so a paragraph that had needed a model would have stayed listed and unsplit.

## Report

Filled in at the end.
