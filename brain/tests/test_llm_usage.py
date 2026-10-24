"""Usage and cost accounting in brain.llm."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pytest

from brain import llm


def test_price_counts_cache_reads_at_their_rate() -> None:
    assert llm.price("claude-opus-5-5", 1_000_000, 0) == pytest.approx(4.0)
    assert llm.price("claude-opus-5-5", 0, 1_000_000, cache_read=1_000_000) == pytest.approx(20.2)
    assert llm.price("some-local-model", 10, 10) is None


def test_cache_hit_adds_cold_cost_but_not_spend(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setattr(llm, "CACHE", tmp_path)
    monkeypatch.setenv("BRAIN_LLM", "anthropic")

    def fake(*args: Any) -> dict[str, Any]:
        llm._local.cost = llm.record("claude-sonnet-5-5", 1000, 100)
        return {"ok": True}

    monkeypatch.setattr(llm, "_anthropic", fake)
    start = llm.usage()
    llm.complete_json("s", "p", {"type": "object"})
    llm.complete_json("s", "p", {"type": "object"})
    d = llm.usage_since(start)
    assert d["calls"] == 1 and d["cache_hits"] == 1
    assert d["cost_usd"] == pytest.approx(0.003)
    assert d["cold_cost_usd"] == pytest.approx(0.006)


def test_unpriced_model_is_counted(monkeypatch: Any) -> None:
    start = llm.usage()
    assert llm.record("qwen3.5:9b", 10, 10) is None
    d = llm.usage_since(start)
    assert d["unpriced_calls"] == 1 and d["cost_usd"] == 0


def test_append_widens_old_results(tmp_path: Path, monkeypatch: Any) -> None:
    from eval import suite

    results = tmp_path / "results.csv"
    results.write_text("time,case\n2026-10-24 10:00,dev\n")
    monkeypatch.setattr(suite, "RESULTS", results)
    suite.append([{"time": "t", "case": "dev", "wall_s": 12.5}])
    rows = list(csv.DictReader(results.open()))
    assert rows[0] == {"time": "2026-10-24 10:00", "case": "dev", "wall_s": ""}
    assert rows[1]["wall_s"] == "12.5"
