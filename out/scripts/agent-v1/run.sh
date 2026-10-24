#!/bin/zsh
# Minimal Opus agent on the dev case, in a folder holding only the spec, the image and the regulation texts.
B=~/Personal/bench-out; A=$B/agent-dev
cd $A
claude -p --restricted --strict-mcp-config --tools Read Grep Glob Write Edit \
  --permission-mode acceptEdits --model claude-opus-5-5 --effort high \
  --system-prompt "You are a type-approval engineer for UN vehicle regulations." \
  --output-format stream-json --verbose \
  "$(cat $B/agent-prompt.md)" > $B/agent-dev.jsonl 2> $B/agent-dev.err
ls -la $A/submission*.json
tail -c 600 $B/agent-dev.jsonl
