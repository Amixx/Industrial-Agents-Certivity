import re

import pytest

from brain import consolidate
from brain.graph import build
from brain.ingest import Line, parse_lines
from brain.models import Paragraph
from brain.rewrite import Draft


def _paragraph(text: str, label: str = "5.1") -> Paragraph:
    return parse_lines([Line(1, f"{label}. {text}", "")], "UN R42", "1.0", "base")[0]


def test_merge_uses_strong_llm_and_paragraph_text(monkeypatch: pytest.MonkeyPatch) -> None:
    paragraph = _paragraph("The lamp shall bear: (a) a mark; (b) a code.")
    graph = build({"UN R42": [paragraph]})
    drafts = [
        Draft(paragraph, "(a) a mark", "(a) a mark"),
        Draft(paragraph, "(b) a code", "(b) a code"),
    ]
    calls: list[tuple[str, str, str]] = []

    def answer(system: str, prompt: str, schema: object, **kwargs: object) -> dict[str, object]:
        calls.append((system, prompt, kwargs["tier"]))
        assert re.search(r'"text": "The lamp shall bear: \(a\) a mark; \(b\) a code\."', prompt)
        return {"paragraphs": [{"key": "UN R42|5.1", "decision": "MERGE"}]}

    monkeypatch.setattr(consolidate.llm, "available", lambda: True)
    monkeypatch.setattr(consolidate.llm, "complete_json", answer)
    out = consolidate.apply(drafts, graph)
    assert len(out) == 1
    assert out[0].text == out[0].quote == "The lamp shall bear: (a) a mark; (b) a code."
    assert calls and calls[0][0] == consolidate._SYSTEM and calls[0][2] == "strong"


def test_split_keeps_rows_and_rules_run_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    paragraph = _paragraph("The lamp shall bear: (a) a mark; (b) a code.")
    other = _paragraph("The lamp shall bear the mark.", "5.2")
    graph = build({"UN R42": [paragraph, other]})
    quote = "The lamp shall bear: (a) a mark; (b) a code."
    drafts = [
        Draft(paragraph, "(a) a mark", quote),
        Draft(paragraph, "(b) a code", quote),
        Draft(other, quote, "The lamp shall bear the mark."),
    ]
    monkeypatch.setattr(consolidate.llm, "available", lambda: True)
    monkeypatch.setattr(
        consolidate.llm,
        "complete_json",
        lambda *args, **kwargs: {"paragraphs": [{"key": "UN R42|5.1", "decision": "SPLIT"}]},
    )
    out = consolidate.apply(drafts, graph)
    assert [(d.paragraph.id, d.text) for d in out] == [(paragraph.id, quote), (other.id, quote)]
    assert out[0].text == out[0].quote


def test_without_llm_skips_merge_but_collapses_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paragraph = _paragraph("The lamp shall bear: (a) a mark; (b) a code.")
    graph = build({"UN R42": [paragraph]})
    quote = "The lamp shall bear: (a) a mark; (b) a code."
    drafts = [
        Draft(paragraph, "first", quote),
        Draft(paragraph, "second", quote),
        Draft(paragraph, quote, "different"),
    ]
    monkeypatch.setattr(consolidate.llm, "available", lambda: False)
    out = consolidate.apply(drafts, graph)
    assert len(out) == 1
    assert out[0].text == quote


def test_stage_flag_defaults_off_and_pipeline_checks_it(monkeypatch: pytest.MonkeyPatch) -> None:
    assert consolidate.ENABLED is False
    from brain import pipeline

    seen: list[bool] = []
    monkeypatch.setattr(
        consolidate, "apply", lambda drafts, graph: seen.append(True) or list(drafts)
    )
    monkeypatch.setattr(consolidate, "ENABLED", False)
    assert pipeline.consolidate.ENABLED is False
    assert not seen
