# v2-merge: F2 0.787 on dev (160 matches, 256 rows, uploaded 25 Oct 03:24 CET)

The consolidate file (`../consolidate/uploaded-0783.json`) with every paragraph of 2+ rows judged ONE or SEVERAL by Opus (`merge-decisions.json`); ONE becomes one verbatim row unless the paragraph is over 2,000 characters. `build.py merge <consolidate file>` rebuilds it from the saved decisions.
