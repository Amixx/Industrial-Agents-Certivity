# Synthetic cases, Tier A: ablations of the real gold

Seven extra evaluation cases built from `cases/dev-rear-lamp/expected.json`. No new labels were invented: each
case keeps only some of the rear lamp's functions, and its `expected.json` is the subset of the experts' 190
requirements that still applies. Use them to test **function-aware regulation and section selection**.

These files are derived from the hackathon data, so the hackathon data licence applies (`LICENSE-DATA.md`).

## How the labels were made

1. Every gold requirement is tagged with the function(s) it depends on: `P` rear position lamp, `S` stop lamp,
   `R` reversing lamp, `RR` rear retro-reflector, plus whether the lamp has LED electronics (which brings in UN R10).
2. Each tag is a rule. Examples: `LAMP` = any light-emitting function; `MULTI` = two or more functions in one
   housing; `P_AND_S` = position lamp incorporated with a stop lamp; `RED` = a red rear function.
   All rules and all 190 tags are in `gold_function_tags.json`.
3. A case keeps a requirement if its rule holds for that case's functions.

`make_tier_a.py` regenerates everything from the gold file: `python synthetic/make_tier_a.py`.

## The cases

| case | functions | n | regulations | full rear-lamp gold scored against it (reg P / page P) |
|---|---|---|---|---|
| synth-a01-stop-tail-lamp | P + S, LED | 136 | R10, R148, R48 | 0.75 / 0.68 |
| synth-a02-reversing-lamp | R, LED | 101 | R10, R148, R48 | 0.75 / 0.55 |
| synth-a03-rear-retro-reflector | RR, passive | 57 | R150, R48 | 0.50 / 0.38 |
| synth-a04-position-lamp-retro | P + RR, LED | 165 | R10, R148, R150, R48 | 1.00 / 0.85 |
| synth-a05-position-reversing-lamp | P + R, LED | 134 | R10, R148, R48 | 0.75 / 0.64 |
| synth-a06-rear-combination-rfq | P + S + R + RR, LED | 190 | R10, R148, R150, R48 | 1.00 / 1.00 |
| synth-a07-rear-position-lamp | P, LED | 119 | R10, R148, R48 | 0.75 / 0.58 |

The last column is a baseline: a pipeline that ignores the spec and always answers with the full rear-lamp gold.
Recall is 1.00 for all of them, so the cases test **precision**: does your pipeline drop what does not apply?

- `a03` is the strongest negative test: no electronics, so no UN R10, and no light source, so no UN R148.
- `a06` is the original product rewritten with different words (tail light, brake light, back-up light, reflex
  reflector). Its answer is the full gold, so it tests robustness to the wording of the spec, not ablation.
- `a01`, `a04`, `a07` say which functions live in **other** components (in `a01`: indicator, reversing and fog
  lamp). A good pipeline must not add UN R6, R38 or the matching UN R48 paragraphs for them.
- Legacy decoys to watch in every case: UN R7 (replaced by R148), R23 (R148), R3 (R150), R37 and R128
  (light sources: neither is in the gold, not even R128 for the LED lamps).

## Scoring your pipeline on all cases

Put one output per case in a folder, named `<case_id>.json`, then:

```
python synthetic/score_all.py outputs
```

This gives regulation- and page-level precision and recall per case, like `tools/score_local.py`. The
requirement-level score needs a model and is only computed on the platform; for that level, compare your texts
with the `text` fields of these expected files using your own LLM judge.

## How far to trust these labels

High, but not perfect. They assume the experts labelled each function the same way regardless of which other
functions were present. Tags worth a second look by someone who knows the regulations:

- `G-0062`, `G-0064`, `G-0192`–`G-0196` (logo provisions) tagged `P`: of these functions only the position lamp
  may carry a logo (UN R148 4.5.5 forbids it on stop and reversing lamps, `G-0197`).
- `G-0112` (UN R48 6.10.5.2, retro-reflector area excluded from the position lamp's apparent surface) tagged `P`,
  not `P` + `RR`.
- `G-0123` (UN R48 6.14.7, retro-reflector may share surface with another lamp) tagged `RR`, not `RR` + a lamp.
- `G-0073`, `G-0074` (UN R48 5.10, no red light to the front) tagged `RED`, so they are dropped for the
  reversing-lamp-only case.

## Variants deliberately left out of Tier A

- **High-mounted stop lamp (CHMSL, S3/S4)**: the gold only has the S1/S2 paragraphs of UN R48 6.7, so a subset
  would miss the S3/S4 installation rules.
- **Filament instead of LED**: dropping UN R10 is right, but the gold has no filament-specific paragraphs, so a
  subset would miss them.

Both need new labels from the regulation text (Tier B).
