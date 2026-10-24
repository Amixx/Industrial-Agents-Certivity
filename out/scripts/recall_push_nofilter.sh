#!/bin/zsh
# Cached rerun of the recall-push run with the requirement filter off, recording each row's p_keep.
B=~/Personal/bench-out; R=~/Personal/Industrial-Agents-Certivity
cd ~/Personal/Industrial-Agents-Certivity-select/brain
source ~/.config/secrets/secrets.env
export BRAIN_LLM=claude-cli BRAIN_CLAUDE_CLI_BULK=claude-opus-5-5 BRAIN_JEV=1
uv run --frozen python -c "
import sys, runpy, json
import brain.relevance as r, brain.keep as k
r.RELATIVE_JEV = 0.20
orig = k.scores
rec = []
def scores(drafts, product):
    s = orig(drafts, product); rec.extend(s); return s
k.scores = scores
k.THRESHOLD = 0.0
sys.argv = ['pipeline', '$R/cases/dev-rear-lamp', '-o', '$B/j20f-all.json', '--team-id', 'team-06']
try:
    runpy.run_module('brain.pipeline', run_name='__main__')
finally:
    json.dump(rec, open('$B/j20f-all.pkeep.json', 'w'))
" > $B/j20f-all.log 2>&1
tail -3 $B/j20f-all.log
