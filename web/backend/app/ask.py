"""Short spoken answers to a developer's follow-up question about part of a report, from the
Anthropic API on the owner's key. Every call's cost goes into a ledger, and calls stop once the
ledger reaches the budget.
"""

import json
import logging
import os
import threading
from typing import Any

import anthropic

from .models import AskAnswer, Requirement
from .paths import DATA_DIR

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 1024
BUDGET_USD = float(os.environ.get("ASK_BUDGET_USD", "5"))

# USD per million tokens for MODEL: input, output, 5-minute cache write, cache read.
PRICE_IN, PRICE_OUT, PRICE_CACHE_WRITE, PRICE_CACHE_READ = 2.00, 10.00, 2.50, 0.20

SYSTEM = """You answer a product engineer's follow-up question about a UN Regulation compliance
report for their component. The engineer selected part of the report and asked about it by voice,
and your answer is read aloud.

- Answer in at most three short sentences of plain spoken English: no lists, no markdown, no
  symbols that don't read aloud. Say numbers with their units.
- Use the language an engineer uses, not legal language.
- Base every sentence on the requirements below and list the ids it rests on in `cites`.
- If the requirements don't answer the question, say so in one sentence with empty `cites`.
  Never invent values."""

_LEDGER = DATA_DIR / "spend.json"
_lock = threading.Lock()
_client: anthropic.Anthropic | None = None

log = logging.getLogger("uvicorn.error")


class BudgetExceeded(Exception):
    pass


def spent() -> float:
    if not _LEDGER.is_file():
        return 0.0
    total: float = json.loads(_LEDGER.read_text())["total_usd"]
    return total


def _record(cost: float) -> float:
    with _lock:
        ledger = (
            json.loads(_LEDGER.read_text()) if _LEDGER.is_file() else {"total_usd": 0, "calls": 0}
        )
        ledger["total_usd"] += cost
        ledger["calls"] += 1
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _LEDGER.write_text(json.dumps(ledger))
        total: float = ledger["total_usd"]
        return total


def _cost(usage: anthropic.types.Usage) -> float:
    tokens = (
        usage.input_tokens * PRICE_IN
        + usage.output_tokens * PRICE_OUT
        + (usage.cache_creation_input_tokens or 0) * PRICE_CACHE_WRITE
        + (usage.cache_read_input_tokens or 0) * PRICE_CACHE_READ
    )
    return tokens / 1_000_000


def _schema(ids: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "sentences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "cites": {"type": "array", "items": {"type": "string", "enum": ids}},
                    },
                    "required": ["text", "cites"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["sentences"],
        "additionalProperties": False,
    }


def ask(question: str, selection: str, requirements: list[Requirement]) -> AskAnswer:
    global _client
    if spent() >= BUDGET_USD:
        raise BudgetExceeded(f"The ${BUDGET_USD:.2f} question budget is used up")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set on the server")
    _client = _client or anthropic.Anthropic()
    listing = "\n".join(
        f"{r.id} | {r.source.regulation} paragraph {r.source.paragraph}, page {r.source.page} "
        f"| {r.text}"
        for r in requirements
    )
    response = _client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "between_tools"},
        system=[
            {"type": "text", "text": SYSTEM},
            {
                "type": "text",
                "text": "Requirements (id | source | text):\n" + listing,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {
                "role": "user",
                "content": f"Selected text from the report:\n<selection>\n{selection}\n"
                f"</selection>\n\nQuestion: {question}",
            }
        ],
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": _schema([r.id for r in requirements])},
        },
    )
    cost = _cost(response.usage)
    total = _record(cost)
    log.info(
        "ask: %s in, %s out, %s cache write, %s cache read, $%.4f, total $%.4f",
        response.usage.input_tokens,
        response.usage.output_tokens,
        response.usage.cache_creation_input_tokens,
        response.usage.cache_read_input_tokens,
        cost,
        total,
    )
    if response.stop_reason != "end_turn":
        raise RuntimeError(f"Answer stopped early: {response.stop_reason}")
    text = next(b.text for b in response.content if b.type == "text")
    return AskAnswer.model_validate(
        {**json.loads(text), "cost_usd": cost, "spent_usd": total, "budget_usd": BUDGET_USD}
    )
