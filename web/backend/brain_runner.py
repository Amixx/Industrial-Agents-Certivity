"""Runs `brain.pipeline.run` for the web backend, inside the brain's own environment.

    brain/.venv/bin/python web/backend/brain_runner.py SPEC IMAGE OUT

IMAGE may be an empty string. RUN_PRICES (JSON: model -> USD per million tokens for input,
output, cache write, cache read) lists the only models an API call may use; a call to any other
model fails. Calls go out without server-side fallbacks, so a declined request never moves to
another model. Once the run's spend reaches RUN_BUDGET_USD, further calls fail.

Progress goes to stderr: the brain's own log lines, a `[cost] calls=N usd=X` line every few
calls, and a `[partial] {json}` line with each step's result (profile, regulations, paragraph
count, rewritten requirements) as soon as it is known.

OUT receives {"submission", "error", "cost"} whether or not the run succeeds, and holds the cost
so far after every call, so a killed run still leaves its spend behind.

Every brain call shares one API client.
"""

import json
import os
import sys
import threading
import traceback
from pathlib import Path
from typing import Any

import anthropic
import anthropic.resources.beta.messages as beta_messages
import anthropic.resources.messages as messages
import brain.pipeline as pipeline

PRICES: dict[str, list[float]] = json.loads(os.environ["RUN_PRICES"])
BUDGET_USD = float(os.environ["RUN_BUDGET_USD"])
COST_EVERY = 10  # calls between [cost] lines

OUT = Path(sys.argv[3])

_lock = threading.Lock()
_usage: dict[str, dict[str, int]] = {}
_client: anthropic.Anthropic | None = None
_new_client = anthropic.Anthropic


def _shared_client(**kw: Any) -> anthropic.Anthropic:
    global _client
    with _lock:
        _client = _client or _new_client(**kw)
        return _client


def _write(result: dict[str, Any]) -> None:
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(result))
    tmp.replace(OUT)


def _cost(model: str, u: dict[str, int]) -> float:
    price_in, price_out, price_write, price_read = PRICES[model]
    tokens = (
        u["input"] * price_in
        + u["output"] * price_out
        + u["cache_write"] * price_write
        + u["cache_read"] * price_read
    )
    return tokens / 1_000_000


def _total() -> float:
    return sum(_cost(model, u) for model, u in _usage.items())


def _summary() -> dict[str, Any]:
    models = [
        {"model": model, **u, "cost_usd": _cost(model, u)} for model, u in sorted(_usage.items())
    ]
    return {"total_usd": _total(), "models": models}


def _guard(create: Any) -> Any:
    def guarded(self: Any, **kw: Any) -> Any:
        model = kw.get("model")
        if model not in PRICES:
            raise RuntimeError(f"model {model} is not allowed on the server")
        kw.pop("fallbacks", None)
        betas = [b for b in kw.pop("betas", []) if not b.startswith("server-side-fallback")]
        if betas:
            kw["betas"] = betas
        with _lock:
            if _total() >= BUDGET_USD:
                raise RuntimeError(f"run budget of ${BUDGET_USD:.2f} reached")
        response = create(self, **kw)
        u = response.usage
        with _lock:
            row = _usage.setdefault(
                model,
                {"calls": 0, "input": 0, "output": 0, "cache_write": 0, "cache_read": 0},
            )
            row["calls"] += 1
            row["input"] += u.input_tokens
            row["output"] += u.output_tokens
            row["cache_write"] += u.cache_creation_input_tokens or 0
            row["cache_read"] += u.cache_read_input_tokens or 0
            calls = sum(r["calls"] for r in _usage.values())
            _write({"submission": None, "error": "run did not finish", "cost": _summary()})
            if calls % COST_EVERY == 0:
                print(f"[cost] calls={calls} usd={_total():.4f}", file=sys.stderr, flush=True)
        return response

    return guarded


beta_messages.Messages.create = _guard(beta_messages.Messages.create)  # type: ignore[method-assign]
messages.Messages.create = _guard(messages.Messages.create)  # type: ignore[method-assign]
anthropic.Anthropic = _shared_client  # type: ignore[misc,assignment]


def _partial(data: dict[str, Any]) -> None:
    print(f"[partial] {json.dumps(data)}", file=sys.stderr, flush=True)


def _report(name: str, describe: Any) -> None:
    """Wrap pipeline step `name` so its result is also printed as a partial."""
    step = getattr(pipeline, name)

    def wrapped(*args: Any, **kw: Any) -> Any:
        result = step(*args, **kw)
        _partial(describe(result))
        return result

    setattr(pipeline, name, wrapped)


_report("build_profile", lambda profile: {"profile": profile.model_dump()})
_report("review", lambda choices: {"regulations": [c.model_dump() for c in choices]})
_report("select_paragraphs", lambda result: {"paragraph_count": len(result[0])})
_report(
    "clean",
    lambda result: {
        "requirements": [
            {
                "text": d.text,
                "regulation": d.paragraph.regulation,
                "version": d.paragraph.version,
                "page": d.paragraph.page,
                "paragraph": d.paragraph.label,
            }
            for d in result[0]
        ]
    },
)


def main() -> int:
    spec, image = sys.argv[1:3]
    result: dict[str, Any] = {"submission": None, "error": None}
    try:
        result["submission"] = pipeline.run(
            Path(spec).read_text(), Path(image) if image else None, case_id="web"
        )
    except Exception as e:
        traceback.print_exc()
        result["error"] = f"{type(e).__name__}: {e}"
    with _lock:
        result["cost"] = _summary()
        _write(result)
    return 0 if result["error"] is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
