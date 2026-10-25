# Split repair on the kb-lin15 file: F2 0.738 on dev (165 matches, 358 rows, uploaded 25 Oct 04:47 CET)

`split_repair.py` adds rows to long body paragraphs (600+ characters, 3+ numeric limits, 2+ rows): Opus splits each into verbatim quotes, one per obligation or limit, and quotes no existing row covers become rows. Input: `bench-out/kbbump/dev-l15-final-v2.json` (the kb-lin15 file with the paragraph-keyed duplicate drop).

    cd brain && PYTHONPATH=$PWD uv run --frozen python ../repro/split-repair/split_repair.py <in.json> <out.json>

Room for gold matches rose 174 to 180 for 17 rows, but the platform gave 165 against the base config's 166-172. Refuted.
