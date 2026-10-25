"""Short spoken answers to a developer's follow-up question about part of a report, from the
Anthropic API on the owner's key. Every call's cost goes into the spend ledger.
"""

import json
import logging
import os
from typing import Any

import anthropic

from . import spend, voice
from .models import AskAnswer, Requirement

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 1024

SYSTEM = """You answer a product engineer's follow-up question about a UN Regulation compliance
report for their component. The engineer selected part of the report and asked about it by voice,
and your answer is read aloud.

- Answer in at most three short sentences of plain spoken English: no lists, no markdown, no
  symbols that don't read aloud. Say numbers with their units.
- Use the language an engineer uses, not legal language.
- Base every sentence on the requirements below and list the ids it rests on in `cites`.
- If the requirements don't answer the question, say so in one sentence with empty `cites`.
  Never invent values."""

_client: anthropic.Anthropic | None = None

log = logging.getLogger("uvicorn.error")


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
    spend.check()
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
    cost = spend.cost(MODEL, response.usage)
    total = spend.record(cost)
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
    answer = AskAnswer.model_validate(
        {**json.loads(text), "cost_usd": cost, "spent_usd": total, "budget_usd": spend.BUDGET_USD}
    )
    if voice.enabled():
        answer.speech_id = voice.remember(" ".join(s.text for s in answer.sentences))
    return answer
