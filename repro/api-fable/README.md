# kb-lin15 chain on the Anthropic API, Fable for section scores and list merge: F2 0.772 on dev (168 matches, 328 rows, uploaded 25 Oct 04:24 CET)

Every model call goes to the API (`BRAIN_LLM=anthropic`): Opus 5.5 for the pipeline (profile, regulations, drafting, keep scores), Fable 5.1 for the section scores (`../kb-lin15/select.py`) and the MERGE/SPLIT call (`../kb-lin15/merge_llm_any.py`). `api_llm.py` routes those two scripts' `claude_cli.complete_json` calls to `brain.llm._anthropic`, closing every object schema with `additionalProperties: false` as the API requires. The cut, verbatim and consolidation steps are as in `../kb-lin15/`.

    zsh repro/api-fable/run.sh      # writes dev*.json next to this README; about $9.35 cold, 4 minutes

Spend: Opus pipeline $7.92 (267 calls), Fable section scores $1.34 (30 calls), Fable merge $0.09.

Differences from the `claude -p` route: the API reads the case image, so the profile has 32 terms against 20 and paragraph selection keeps 293 paragraphs against 330 (110 gold paragraphs cited against 116); the API path sends no thinking setting. Fable's section scores separate cited from uncited paragraphs at AUC 0.753 against Opus's 0.711 on the 228 paragraphs both scored.
