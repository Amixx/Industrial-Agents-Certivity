"""Lane F, step 2, the model feature: P(an expert list keeps this row) for every pool cluster.

    PYTHONPATH=. uv run python swing/f_keep.py [--tier strong|bulk] [--cap 2.0]

The prompt is the requirement filter of branch `kb-stack` (`brain/keep.py` at `c60e36c`),
copied here because that branch is not merged. It holds no dev gold text. Answers go through
`brain.llm` (cached in data/cache/llm/), so a rerun is free. The run stops once its new spend
passes `--cap` dollars. Writes `p_keep_<tier>` into each cluster of ../out/experiments/F-pool.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import anthropic.resources.beta.messages as M

from brain import llm
from swing.f_pool import OUT, POOL_PATH

BATCH = 30
PRICE = {"claude-sonnet-5-5": (2, 10, 0.2), "claude-opus-5-5": (4, 20, 0.2)}

SYSTEM = """You are a type-approval engineer reviewing a draft requirement list for one
automotive component. Each draft requirement was rewritten from a UN Regulation paragraph that is
already known to be relevant to the product. An expert's final list keeps the requirements the
component itself (or the vehicle, because of the component) must meet, and drops the rest.

Experts usually drop a requirement when it:
- applies only to a device category, function, variant or vehicle category the product does not
  have (for example a requirement for a high-mounted stop lamp, a dipped-beam headlamp, a
  triangular retro-reflector or category N3 vehicles, when the product has none of these);
- is an obligation on the applicant, the manufacturer's paperwork, the approval authority or the
  communication form (what to submit, what to state in the application, what the authority
  records, approval numbering, extension, notification);
- describes test equipment, laboratory set-up or measurement procedure without setting a limit
  or criterion the component must meet;
- is a generic administrative or transitional clause (dates, "Contracting Parties shall",
  conformity-of-production sampling for inspectors).

Experts usually keep a requirement that sets a construction, performance, photometric,
colorimetric, dimensional, position, marking, durability or electrical/EMC requirement or test
limit for the product's own functions, including conditional ones ("Where ... is used, ...") that
could apply to this product.

When unsure, lean to keep: a missed requirement costs four times as much as an extra one."""

SCHEMA = {
    "type": "object",
    "properties": {
        "keep": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "p_keep": {
                        "type": "number",
                        "description": "probability (0-1) that the expert list keeps it",
                    },
                },
                "required": ["id", "p_keep"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["keep"],
    "additionalProperties": False,
}

usage = [0, 0, 0, 0]  # calls, input, output, cache read
spent = [0.0]
lock = threading.Lock()
cap = [2.0]
_orig = M.Messages.create


def _create(self: Any, **kw: Any) -> Any:
    if spent[0] >= cap[0]:
        raise RuntimeError(f"lane F spend cap ${cap[0]:.2f} reached")
    r = _orig(self, **kw)
    u = r.usage
    pi, po, pc = PRICE.get(kw["model"], (10, 50, 0.25))
    with lock:
        i = u.input_tokens + (u.cache_creation_input_tokens or 0)
        cr = u.cache_read_input_tokens or 0
        usage[0] += 1
        usage[1] += i
        usage[2] += u.output_tokens
        usage[3] += cr
        spent[0] += (i * pi + u.output_tokens * po + cr * pc) / 1e6
    return r


M.Messages.create = _create  # type: ignore[method-assign]


def product() -> str:
    from brain.models import ProductProfile

    base = json.loads((OUT / "rear-lamp-main-a39acab.json").read_text())
    return ProductProfile(**base["profile"]).model_dump_json(
        include={"product", "vehicle_categories", "functions", "parts", "electronics"}
    )


def batch(chunk: list[tuple[str, dict[str, Any]]], prod: str, tier: llm.Tier) -> dict[str, float]:
    items = "\n".join(
        json.dumps(
            {
                "id": rid,
                "regulation": c["regulation"],
                "paragraph": c["paragraph"],
                "text": c["text"],
            },
            ensure_ascii=False,
        )
        for rid, c in chunk
    )
    prompt = (
        f"Product profile:\n{prod}\n\nDraft requirements (JSON lines):\n{items}\n\n"
        "Return p_keep for every id."
    )
    data = llm.complete_json(SYSTEM, prompt, SCHEMA, tier=tier, effort="low")
    return {k["id"]: min(1.0, max(0.0, float(k["p_keep"]))) for k in data["keep"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tier", default="strong", choices=["strong", "bulk"])
    ap.add_argument("--cap", type=float, default=2.0)
    args = ap.parse_args(argv)
    cap[0] = args.cap
    os.environ.setdefault("BRAIN_LLM", "anthropic")
    pool = json.loads(POOL_PATH.read_text())
    cs = pool["clusters"]
    # Sorted by paragraph so a batch reads like a draft list, as in the pipeline.
    order = sorted(range(len(cs)), key=lambda i: (cs[i]["regulation"], cs[i]["pkey"]))
    ids = [(f"r{i}", cs[i]) for i in order]
    prod = product()
    out: dict[str, float] = {}
    todo = ids
    for _ in range(2):
        chunks = [todo[i : i + BATCH] for i in range(0, len(todo), BATCH)]
        with ThreadPoolExecutor(8) as ex:
            for part in ex.map(lambda c: batch(c, prod, args.tier), chunks):
                out |= part
        todo = [(rid, c) for rid, c in todo if rid not in out]
        if not todo:
            break
    key = f"p_keep_{args.tier}"
    for i, c in enumerate(cs):
        c["f"][key] = out.get(f"r{i}", 0.5)
    POOL_PATH.write_text(json.dumps(pool, ensure_ascii=False))
    print(
        f"[cost] {llm.model_for(args.tier)}: {usage[0]} new calls, {usage[1]:,} in / "
        f"{usage[2]:,} out / {usage[3]:,} cache read; ${spent[0]:.2f}; "
        f"{len(todo)} rows unscored (set to 0.5)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
