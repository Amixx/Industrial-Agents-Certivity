"""Run brain.pipeline with every LLM call routed to `claude -p` on the subscription.

    cd ~/Personal/wt-sec/brain
    uv run --frozen python ~/Personal/bench-out/section-step/run.py STATS [--no-cut] -- <pipeline args>

Both tiers -> claude-opus-5-5; Jev on. Cache shared with the main
checkout. STATS gets a JSON line with new calls, cache hits and reported cost per model.
"""

import json
import os
import runpy
import subprocess as _sp
import sys
import threading
from collections import Counter
from pathlib import Path

for k in ("ANTHROPIC_API_KEY", "OPENAI_KEY", "OPENAI_API_KEY", "BRAIN_LLM"):
    os.environ.pop(k, None)

sys.path.insert(0, os.getcwd())
from brain import claude_cli, llm, sections  # noqa: E402

for k in ("ANTHROPIC_API_KEY", "OPENAI_KEY", "OPENAI_API_KEY", "BRAIN_LLM"):
    os.environ.pop(k, None)

stats_path = Path(sys.argv[1])
rest = sys.argv[2:]
if rest and rest[0] == "--no-cut":
    sections.ENABLED = False
    rest = rest[1:]
assert rest[0] == "--"
pipeline_args = rest[1:]

claude_cli.CACHE = Path.home() / "Personal/Industrial-Agents-Certivity/brain/data/cache"
MODELS = {"strong": "claude-opus-5-5", "bulk": "claude-opus-5-5"}
SLOTS = threading.BoundedSemaphore(5)
lock = threading.Lock()
calls: Counter = Counter()
hits: Counter = Counter()
cost: Counter = Counter()
tokens: Counter = Counter()


class Shim:
    def run(self, cmd, **kw):
        done = _sp.run(cmd, **kw)
        model = cmd[cmd.index("--model") + 1]
        out = done.stdout
        try:
            reply = json.loads(out[out.find("{") : out.rfind("}") + 1])
        except json.JSONDecodeError:
            reply = {}
        u = reply.get("usage") or {}
        with lock:
            calls[model] += 1
            cost[model] += reply.get("total_cost_usd") or 0.0
            for f in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                      "cache_creation_input_tokens"):
                tokens[f"{model}:{f}"] += u.get(f, 0)
        return done


claude_cli.subprocess = Shim()  # type: ignore[assignment]


def complete_json(system, content, schema, *, tier="bulk", effort="medium", max_tokens=16000):
    if isinstance(content, list):
        assert all(b["type"] == "text" for b in content), "image block reached claude -p"
        prompt = "\n\n".join(b["text"] for b in content)
    else:
        prompt = content
    model = MODELS[tier]
    key = {"system": system, "prompt": prompt, "schema": schema, "model": model}
    if claude_cli._cache_path(key).exists():
        with lock:
            hits[model] += 1
        return claude_cli.complete_json(system, prompt, schema, model)
    with SLOTS:
        return claude_cli.complete_json(system, prompt, schema, model)


dump: list = []
_cut = sections.cut


def cut(drafts, p_keep, p_section):
    for d, pk in zip(drafts, p_keep):
        p = d.paragraph
        dump.append([p.regulation, p.label, round(pk, 3), p_section[p.id]])
    return _cut(drafts, p_keep, p_section)


sections.cut = cut
llm.provider = lambda: "claude-cli"
llm.reads_images = lambda: False
llm.complete_json = complete_json

sys.argv = ["brain.pipeline", *pipeline_args]
try:
    runpy.run_module("brain.pipeline", run_name="__main__")
finally:
    stats_path.write_text(json.dumps({
        "section_cut": sections.ENABLED, "calls": calls, "cache_hits": hits,
        "cost_usd_reported": {k: round(v, 3) for k, v in cost.items()}, "tokens": tokens,
    }) + "\n")
    if dump:
        stats_path.with_suffix(".scores.json").write_text(json.dumps(dump))
