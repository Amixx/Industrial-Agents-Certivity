#!/bin/zsh
# Held-out bumper on the Anthropic API, Opus for every call, the 7 gold regulations forced in.
set -e
cd ${0:A:h:h:h}/brain
source ~/.config/secrets/secrets.env
BRAIN_JEV=1 BRAIN_JEV_KB=1 BRAIN_CONSOLIDATE=1 \
  BRAIN_MODEL_STRONG=claude-opus-5-5 BRAIN_MODEL_BULK=claude-opus-5-5 \
  uv run --frozen python -m brain.pipeline ../cases/heldout-front-bumper --llm api --team-id team-06 \
  --include "UN R42" "UN R26" "UN R127" "UN R10" "UN R48" "UN R148" "UN GTR 9" \
  -o ${0:A:h}/heldout-api.rerun.json
