"""One ledger for everything the server spends on the Anthropic API (pipeline runs, briefs and
answers), with a budget that stops new calls once it is reached. The ledger lives in DATA_DIR,
so it starts again from zero on a host without a persistent disk."""

import json
import os
import threading
from typing import Protocol

from .paths import DATA_DIR

BUDGET_USD = float(os.environ.get("LLM_BUDGET_USD", "7.5"))

# The only models the server may call, with USD per million tokens:
# input, output, 5-minute cache write, cache read.
PRICES: dict[str, tuple[float, float, float, float]] = {
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
}

_LEDGER = DATA_DIR / "spend.json"
_lock = threading.Lock()


class BudgetExceeded(Exception):
    pass


class Usage(Protocol):
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int | None
    cache_read_input_tokens: int | None


def cost(model: str, usage: Usage) -> float:
    price_in, price_out, price_write, price_read = PRICES[model]
    tokens = (
        usage.input_tokens * price_in
        + usage.output_tokens * price_out
        + (usage.cache_creation_input_tokens or 0) * price_write
        + (usage.cache_read_input_tokens or 0) * price_read
    )
    return tokens / 1_000_000


def spent() -> float:
    if not _LEDGER.is_file():
        return 0.0
    total: float = json.loads(_LEDGER.read_text(encoding="utf-8"))["total_usd"]
    return total


def remaining() -> float:
    return BUDGET_USD - spent()


def check(need: float = 0.0) -> None:
    """Raise BudgetExceeded unless more than `need` dollars of the budget are left."""
    left = remaining()
    if left <= need:
        raise BudgetExceeded(
            f"The ${BUDGET_USD:.2f} API budget has ${max(left, 0):.2f} left; this needs ${need:.2f}"
            if need
            else f"The ${BUDGET_USD:.2f} API budget is used up"
        )


def record(cost: float) -> float:
    """Add `cost` to the ledger and return the new total."""
    with _lock:
        ledger = (
            json.loads(_LEDGER.read_text(encoding="utf-8"))
            if _LEDGER.is_file()
            else {"total_usd": 0, "calls": 0}
        )
        ledger["total_usd"] += cost
        ledger["calls"] += 1
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _LEDGER.write_text(json.dumps(ledger), encoding="utf-8")
        total: float = ledger["total_usd"]
        return total
