#!/bin/zsh
# kb-lin15 chain on dev, every model call on the Anthropic API: Opus 5.5 for the pipeline, Fable 5.1 for section scores and list merge/split.
set -e
D=${0:A:h}; W=~/Personal/wt-backup-0724; K=${0:A:h:h}/kb-lin15
cd $W/brain
source ~/.config/secrets/secrets.env
export BRAIN_LLM=anthropic BRAIN_MODEL_STRONG=claude-opus-5-5 BRAIN_MODEL_BULK=claude-opus-5-5 BRAIN_JEV=1
uv run --frozen --with anthropic python - $W/cases/dev-rear-lamp $D/dev.json <<'PY' > $D/dev.log 2>&1
import sys, json
import brain.relevance as r, brain.keep as k, brain.pipeline as P, brain.llm as L
case, out = sys.argv[1:3]
r.RELATIVE_JEV = 0.20
orig = k.scores; rec = []
def scores(drafts, product):
    s = orig(drafts, product); rec.extend(s); return s
k.scores = scores; k.THRESHOLD = 0.0
try: P.main([case, '-o', out, '--team-id', 'team-06'])
finally:
    json.dump(rec, open(out.replace('.json', '.pkeep.json'), 'w'))
    print('api usage', json.dumps(L.usage()))
PY
tail -2 $D/dev.log
PYTHONPATH=$PWD uv run --frozen --with anthropic python $D/api_llm.py claude-fable-5-1 high $K/select.py $D/dev.json $D/dev.psec.json >> $D/dev.log 2>&1
PYTHONPATH=$PWD uv run --frozen --with anthropic python $K/stage.py $D/dev-cut.json $D/dev.json --pkeep $D/dev.pkeep.json --psec $D/dev.psec.json --lin --t 0.15 >> $D/dev.log 2>&1
uv run --frozen --with anthropic python $W/repro/verbatim.py $D/dev-cut.json $D/dev-verb.json --all >> $D/dev.log 2>&1
PYTHONPATH=$PWD uv run --frozen --with anthropic python $D/api_llm.py claude-fable-5-1 high $K/merge_llm_any.py $D/dev-verb.json $D/dev-merge.json >> $D/dev.log 2>&1
python3 $K/consolidate.py $D/dev-merge.json $D/dev-final.json >> $D/dev.log 2>&1
grep "api usage\|wrote\|rows" $D/dev.log
