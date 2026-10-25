# kb lineage, linear section cut 0.15, consolidation: F2 0.771 on dev (169 matches, 336 rows, uploaded 25 Oct 03:47 CET)

The candidate that holds up best on the bumper silver labels. Same chain as `../README.md` (the 0.724 file) with the section cut `p_keep * p_section >= 0.15` instead of `p_keep * sqrt(p_section) >= 0.3535`, then consolidation.

Dev, from the cached inputs in `..`:

    cd brain
    PYTHONPATH=$PWD uv run --frozen python ../repro/kb-lin15/stage.py OUT/cut.json ../repro/out/j20f-all.json --pkeep ../repro/out/j20f-all.pkeep.json --psec ../repro/p_section.json --lin --t 0.15
    uv run --frozen python ../repro/verbatim.py OUT/cut.json OUT/verb.json --all
    PYTHONPATH=$PWD uv run --frozen python ../repro/kb-lin15/merge_llm_any.py OUT/verb.json OUT/merge.json
    python3 ../repro/kb-lin15/consolidate.py OUT/merge.json OUT/final.json

A new case: `run.sh <name> <case dir> <regulations...>` runs the pipeline (Jev relative 0.20, no requirement filter), the section scores (`select.py`, one Opus call per section) and the sqrt cut; rerun `stage.py` with `--lin --t 0.15`, then verbatim, merge and consolidate as above. `score.py` scores files against the bumper silver labels; `sweep.py` sweeps the cut on dev and the bumper cases.

Bumper silver paragraph F2 (R42, R26, R127) at this cut: plain 0.789, sensors-fog 0.743. ready-for-main at its own 0.15 cut: 0.714, 0.622. The strict cut of the 0.79 file: 0.651, 0.657.

The duplicate drop in `consolidate.py` keys on regulation, paragraph and text. `uploaded-0771.json` was built when it keyed on text alone, which dropped identical text cited under a second paragraph; `dev-final-v2.json` is the dev file rebuilt with the current script (341 rows, room for 174 gold matches against 172).
