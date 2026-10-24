#!/bin/zsh
# Minimal Opus agent on the dev case, in a folder holding only the spec, the image and the regulation texts.
B=~/Personal/bench-out; A=$B/agent-dev3
cd $A
claude -p --restricted --strict-mcp-config --tools Read Grep Glob Write Edit \
  --permission-mode acceptEdits --model claude-opus-5-5 --effort high \
  --system-prompt "You are a type-approval engineer for UN vehicle regulations." \
  --output-format stream-json --verbose \
  "$(cat $B/agent-prompt-v3.md)" > $B/agent-dev3.jsonl 2> $B/agent-dev3.err
ls -la $A/requirements*.tsv
tail -c 600 $B/agent-dev3.jsonl
