#!/bin/zsh
# Rebuild the 0.724 upload of 25 Oct 01:10 from the cached LLM and Jev answers; a cache miss stops it.
#   zsh repro/run.sh      (from anywhere; writes repro/out/ and compares with repro/uploaded-0724.json)
set -e
H=${0:A:h}; W=${H:h}; O=$H/out; mkdir -p $O
cd $W/brain
[[ -e data/corpus ]] || { echo "link brain/data/corpus to a checkout's brain/data/corpus first"; exit 1; }
[[ -e data/cache ]] || { mkdir -p $H/cache && tar xzf $H/llm-cache.tgz -C $H/cache && ln -s $H/cache/.certivity-llm-cache data/cache; }
[[ -e data/kb.sqlite ]] || gunzip -c $H/kb.sqlite.gz > data/kb.sqlite
export BRAIN_LLM=claude-cli BRAIN_CLAUDE_CLI_BULK=claude-opus-5-5 BRAIN_JEV=1 TYPESAFE_API_KEY=cache-only
uv run --frozen python -c "
import sys, runpy, json
import brain.relevance as r, brain.keep as k, brain.claude_cli as c, brain.jev as j
def miss(*a, **kw): raise SystemExit('cache miss: a live call was attempted')
c.subprocess = type('S', (), {'run': staticmethod(miss)})
j._post = miss
r.RELATIVE_JEV = 0.20
orig = k.scores
rec = []
def scores(drafts, product):
    s = orig(drafts, product); rec.extend(s); return s
k.scores = scores
k.THRESHOLD = 0.0
sys.argv = ['pipeline', '$W/cases/dev-rear-lamp', '-o', '$O/j20f-all.json', '--team-id', 'team-06']
try:
    runpy.run_module('brain.pipeline', run_name='__main__')
finally:
    json.dump(rec, open('$O/j20f-all.pkeep.json', 'w'))
" > $O/j20f-all.log 2>&1 || { tail -3 $O/j20f-all.log; exit 1; }
PYTHONPATH=$PWD uv run --frozen python $H/section_stage.py $O/cut2-mark.json $O/j20f-all.json --pkeep $O/j20f-all.pkeep.json
uv run --frozen python $H/verbatim.py $O/cut2-mark.json $O/cut2-mark-verbatim.json --all
python3 -c "
import json
s = lambda f: [{k: r[k] for k in ('text', 'source', 'quote')} for r in json.load(open(f))['requirements']]
same = s('$O/cut2-mark-verbatim.json') == s('$H/uploaded-0724.json')
print('identical to the uploaded file' if same else 'DIFFERS from the uploaded file'); raise SystemExit(0 if same else 1)
"
