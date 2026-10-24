# Bumper labels

A small expert answer key for a front bumper, so the engine can be checked on a product it was not tuned on. The rear lamp is the only case with expert answers.

`bumper-labels.csv` lists every numbered paragraph of UN R42, R127, R26 and GTR 9 in document order, without the approval communication forms (Annex 1).

`labels-r42-r26.csv` and `labels-r127-gtr9.csv` are silver labels: Claude Opus read every row against the plain bumper spec (`data/synthetic/bumper-plain/spec.md`), calibrated on what the lamp expert cited. The `.md` files next to them give the reasoning per section. 67 paragraphs are cited; GTR 9 as a whole is marked not cited, with its paragraphs labelled as if it were. An expert's corrections replace them row by row.

## How to label

The question for each row: would an expert cite this paragraph in the requirement list for a plain front bumper of an M1 passenger car (cover, foam absorber, beam, lower grille, towing eye cover; no lamps or sensors)?

- Put `y` or `n` in `cited`. Leave a row empty if you are unsure.
- A mark on a heading row covers everything below it, until a row with its own mark. For example, `n` on "DEFINITIONS" covers all definitions.
- A mark on `(whole regulation)` covers the whole regulation. Use `n` there if an expert would not cite that regulation at all, for example GTR 9 next to R127.
- `note` is free text, for example "only if the bumper has a towing eye".

Marking whole sections first and then the exceptions inside them takes about 30 to 60 minutes.
