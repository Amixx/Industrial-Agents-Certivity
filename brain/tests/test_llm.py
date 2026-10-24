"""The Claude wiring in brain.llm, without network calls."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest

from brain import llm


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("BRAIN_LLM", "BRAIN_MODEL", "BRAIN_MODEL_STRONG", "BRAIN_MODEL_BULK"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(llm, "_usage", {"paid": {}, "cached": {}})


def test_claude_aliases_and_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAIN_LLM", "anthropic")
    assert llm.model_for("strong") == "claude-opus-5-5"
    assert llm.model_for("bulk") == "claude-sonnet-5-5"
    monkeypatch.setenv("BRAIN_MODEL", "fable")
    assert llm.model_for("strong") == llm.model_for("bulk") == "claude-fable-5-1"
    monkeypatch.setenv("BRAIN_MODEL_BULK", "claude-haiku-5-5")
    assert llm.model_for("bulk") == "claude-haiku-5-5"


def test_cost_counts_cache_reads_and_writes() -> None:
    usage = {
        "claude-sonnet-5-5": {
            "calls": 2,
            "input": 1_000_000,
            "output": 100_000,
            "cache_read": 1_000_000,
            "cache_write": 1_000_000,
        }
    }
    assert llm.cost(usage) == pytest.approx(2.0 + 1.0 + 0.2 + 2.5)
    assert llm.cost({"some-local-model": usage["claude-sonnet-5-5"]}) is None


def test_anthropic_streams_and_records_usage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sent: dict[str, Any] = {}
    message = types.SimpleNamespace(
        stop_reason="end_turn",
        stop_details=None,
        content=[types.SimpleNamespace(type="text", text='{"ok": true}')],
        usage=types.SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
        ),
    )

    class Stream:
        def __enter__(self) -> Stream:
            return self

        def __exit__(self, *exc: object) -> None:
            pass

        def get_final_message(self) -> Any:
            return message

    class Client:
        def __init__(self, **kwargs: Any) -> None:
            self.beta = types.SimpleNamespace(messages=self)

        def stream(self, **request: Any) -> Stream:
            sent.update(request)
            return Stream()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Client))
    monkeypatch.setattr(llm, "CACHE", tmp_path)
    result, counts = llm._anthropic(
        "claude-fable-5-1", "sys", "user", {"type": "object"}, "high", 100
    )
    assert result == {"ok": True} and counts["output"] == 5
    assert sent["model"] == "claude-fable-5-1"
    assert sent["output_config"]["effort"] == "high"
    assert "thinking" not in sent and "temperature" not in sent
    assert sent["fallbacks"] == "default"
    assert llm.usage()["claude-fable-5-1"]["output"] == 5

    message.stop_reason = "max_tokens"
    with pytest.raises(RuntimeError, match="token limit"):
        llm._anthropic("claude-fable-5-1", "sys", "user", {"type": "object"}, "high", 100)

    # complete_json caches the response with its usage; a cache hit is free but reported.
    message.stop_reason = "end_turn"
    monkeypatch.setenv("BRAIN_LLM", "anthropic")
    monkeypatch.setattr(llm, "_usage", {"paid": {}, "cached": {}})
    assert llm.complete_json("sys", "user", {"type": "object"}) == {"ok": True}
    assert llm.complete_json("sys", "user", {"type": "object"}) == {"ok": True}
    assert llm.usage()["claude-sonnet-5-5"]["calls"] == 1
    assert llm.usage(cached=True)["claude-sonnet-5-5"]["calls"] == 1
