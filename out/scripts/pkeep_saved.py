"""p_keep for the rows of a saved submission, through claude -p (Opus), as the pipeline's filter scores them."""
import json, sys
from types import SimpleNamespace as NS
from pathlib import Path
from brain import claude_cli, keep, llm
claude_cli.CACHE = Path.home() / "Personal/Industrial-Agents-Certivity/brain/data/cache"
def complete_json(system, content, schema, *, tier="bulk", effort="medium", max_tokens=16000):
    return claude_cli.complete_json(system, content, schema, "claude-opus-5-5")
llm.complete_json = complete_json
llm.batching = lambda a, b, w: (a, 6)
src, out = sys.argv[1], sys.argv[2]
sub = json.load(open(src))
product = json.dumps({k: sub["profile"][k] for k in ("product", "vehicle_categories", "functions", "parts")})
drafts = [NS(paragraph=NS(regulation=r["source"]["regulation"], label=r["source"]["paragraph"]), text=r["text"]) for r in sub["requirements"]]
json.dump(keep.scores(drafts, product), open(out, "w"))
print("scored", len(drafts))
