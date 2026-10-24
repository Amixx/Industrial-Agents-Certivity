"""Run brain.pipeline and log calls, cache hits and dollars per model."""

import sys
import threading
from collections import defaultdict

import anthropic.resources.beta.messages as M

from brain import llm

PRICE = {
    "claude-sonnet-5-5": (2, 10, 0.2),
    "claude-opus-5-5": (4, 20, 0.2),
    "claude-fable-5-1": (10, 50, 0.25),
}
usage = defaultdict(lambda: [0, 0, 0, 0])  # calls, in, out, cache read
hits = defaultdict(int)
lock = threading.Lock()
orig = M.Messages.create


def create(self, **kw):
    r = orig(self, **kw)
    u = r.usage
    with lock:
        a = usage[kw["model"]]
        a[0] += 1
        a[1] += u.input_tokens + (u.cache_creation_input_tokens or 0)
        a[2] += u.output_tokens
        a[3] += u.cache_read_input_tokens or 0
    return r


M.Messages.create = create
orig_cj = llm.complete_json


def cj(system, content, schema, *, tier="bulk", **kw):
    payload = {
        "provider": llm.provider(),
        "model": llm.model_for(tier),
        "system": system,
        "content": content,
        "schema": schema,
        "effort": kw.get("effort", "medium"),
    }
    if llm._cache_path(payload).exists():
        with lock:
            hits[llm.model_for(tier)] += 1
    return orig_cj(system, content, schema, tier=tier, **kw)


llm.complete_json = cj
from brain.pipeline import main  # noqa: E402

code = main(sys.argv[1:])
total = 0.0
for m, (c, i, o, cr) in usage.items():
    pi, po, pc = PRICE.get(m, (0, 0, 0))
    cost = (i * pi + o * po + cr * pc) / 1e6
    total += cost
    print(
        f"[cost] {m}: {c} new calls, {i:,} in / {o:,} out / {cr:,} cache read; ${cost:.2f}",
        file=sys.stderr,
    )
for m, h in hits.items():
    print(f"[cost] {m}: {h} cache hits", file=sys.stderr)
print(f"[cost] total new spend ${total:.2f}", file=sys.stderr)
sys.exit(code)
