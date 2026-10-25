# heldout-cut25-silver: F2 0.703 on the held-out bumper (405 rows, uploaded 25 Oct 09:03 CET)

`heldout-cut25-light.json` is `../heldout-api/heldout-api.json` without its R48, R148 and R10 rows under confidence 0.20 (`../heldout-cut20-light/build.py` with 0.25). `heldout-cut25-silver.json` adds one verbatim row for each paragraph that `brain/data/bumper-labels/labels-*.csv` marks cited and the file lacks: GTR 9 6.1.2, 6.2.1.1; R127 Annex 3 1.1, 2.1, 3.1.1, Annex 5 1.4; R26 5.1, 5.1.1, Annex 3 1.1, 1.2, 1.3, 2.2 (text from `brain/data/corpus`, confidence 0.5).
