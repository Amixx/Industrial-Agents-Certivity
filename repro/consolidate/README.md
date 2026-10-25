# Consolidate: F2 0.783 on dev (164 matches, 287 rows, uploaded 25 Oct 02:52 CET)

Built from the 0.724 file (`../uploaded-0724.json`, rebuilt by `../run.sh`) in two steps:

1. `merge_llm.py`: Opus labels each list paragraph MERGE (the items are cases, conditions or alternatives under one obligation) or SPLIT (each item is a separate thing owed). A MERGE paragraph becomes one row whose text is the whole paragraph, verbatim. Output: `thesis-merge-conditions.json` (310 rows), which holds Opus's decisions.
2. `build_consolidate.sh`: rows sharing one quote in a paragraph collapse to one row with the quote as text, then exact duplicate texts are dropped. Output: `uploaded-0783.json`.

The scripts use absolute paths from the machine they ran on; `merge_llm.py` imports `brain` (run from `brain/` with `PYTHONPATH=.`).
