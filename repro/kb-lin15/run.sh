#!/bin/zsh
# kb-stack lineage (the 0.724 chain) on one case, live calls: pipeline with Jev relative 0.20 and no requirement filter, then section scores, the sqrt cut and rules, then verbatim.
#   zsh run.sh <name> <case dir> <include regs...>
set -e
N=$1; C=$2; shift 2
D=${0:A:h}; W=~/Personal/wt-backup-0724
cd $W/brain
source ~/.config/secrets/secrets.env
export BRAIN_LLM=claude-cli BRAIN_CLAUDE_CLI_BULK=claude-opus-5-5 BRAIN_JEV=1
EXC=("UN GTR 9" "UN R10" "UN R48" "UN R148" "UN R149" "UN R150" "UN R152" "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79")
uv run --frozen python - "$C" "$D/$N.json" "$@" -- "${EXC[@]}" <<PY > $D/$N.log 2>&1
import sys, runpy, json
import brain.relevance as r, brain.keep as k
args = sys.argv[1:]; case, out = args[0], args[1]; i = args.index('--'); inc, exc = args[2:i], args[i+1:]
r.RELATIVE_JEV = 0.20
orig = k.scores; rec = []
def scores(drafts, product):
    s = orig(drafts, product); rec.extend(s); return s
k.scores = scores; k.THRESHOLD = 0.0
sys.argv = ['pipeline', case, '-o', out, '--team-id', 'team-06', '--include', *inc, '--exclude', *exc]
try: runpy.run_module('brain.pipeline', run_name='__main__')
finally: json.dump(rec, open(out.replace('.json', '.pkeep.json'), 'w'))
PY
PYTHONPATH=$PWD uv run --frozen python $D/select.py $D/$N.json $D/$N.psec.json >> $D/$N.log 2>&1
PYTHONPATH=$PWD uv run --frozen python $D/stage.py $D/$N-cut.json $D/$N.json --pkeep $D/$N.pkeep.json --psec $D/$N.psec.json >> $D/$N.log 2>&1
uv run --frozen python $W/repro/verbatim.py $D/$N-cut.json $D/$N-final.json --all >> $D/$N.log 2>&1
tail -3 $D/$N.log
