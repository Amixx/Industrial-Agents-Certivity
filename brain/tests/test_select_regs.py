"""Regulation selection: the obligation-base ranking, the consolidation rule and the LLM prompt."""

from __future__ import annotations

from typing import Any

import pytest

from brain import select_regs
from brain.ingest import CORPUS, load_all
from brain.kb import store
from brain.kb.rank import ScopeCard, documents, rank
from brain.models import ProductProfile, RegulationChoice
from brain.paths import ROOT
from brain.profile import parse_spec

needs_corpus = pytest.mark.skipif(
    not (CORPUS / "UN_R148_base.jsonl").exists(), reason="run brain.ingest first"
)
LEGACY_LAMPS = {"UN R3", "UN R6", "UN R7", "UN R23", "UN R37", "UN R128"}
R148 = ScopeCard(
    "UN R148",
    "Light-signalling devices",
    "device_approval",
    "This Regulation applies to the following light-signalling devices (lamps).",
    (),
    ("UN R6", "UN R7"),
)
R7 = ScopeCard(
    "UN R7",
    "Position, stop and end-outline lamps",
    "device_approval",
    "This Regulation applies to front and rear position lamps and stop lamps.",
    ("UN R148",),
    (),
)


def _choice(reg: str, selected: bool) -> RegulationChoice:
    return RegulationChoice(
        regulation=reg,
        version="1",
        probability=0.9 if selected else 0.1,
        selected=selected,
        rationale="Device approval.",
    )


def _spec(case: str) -> ProductProfile:
    return parse_spec((ROOT / "synthetic" / "cases" / case / "spec.md").read_text())


def test_consolidated_regulation_replaces_selected_legacy_one() -> None:
    choices = [_choice("UN R148", True), _choice("UN R7", True), _choice("UN R19", True)]
    superseded_by = {"UN R148": (), "UN R7": ("UN R148",), "UN R19": ("UN R149",)}
    out = {c.regulation: c for c in select_regs.prefer_consolidated(choices, superseded_by)}
    assert out["UN R148"].selected and out["UN R19"].selected
    assert not out["UN R7"].selected
    assert "UN R148 is selected and consolidates it" in out["UN R7"].rationale


def test_review_prompt_carries_the_scope_cards(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def complete_json(system: str, prompt: str, schema: dict, **_: Any) -> dict:
        seen.update(prompt=prompt, schema=schema)
        return {
            "decisions": [
                {
                    "regulation": "UN R148",
                    "rationale": "Approves the lamp.",
                    "applies": True,
                    "p_applies": 0.9,
                },
                {
                    "regulation": "UN R7 - Position lamps",
                    "rationale": "Legacy.",
                    "applies": True,
                    "p_applies": 0.6,
                },
            ]
        }

    monkeypatch.setattr(select_regs.llm, "complete_json", complete_json)
    cards = {"UN R148": R148, "UN R7": R7}
    out = select_regs._llm_review(
        ProductProfile(product="rear lamp"),
        cards,
        [_choice("UN R148", True), _choice("UN R7", False)],
    )
    prompt = seen["prompt"]
    assert "UN R7 - Position, stop and end-outline lamps\nRole: device_approval" in prompt
    assert "Scope: This Regulation applies to front and rear position lamps" in prompt
    assert "Consolidated into: UN R148" in prompt and "Consolidates: UN R6, UN R7" in prompt
    assert seen["schema"]["properties"]["decisions"]["items"]["properties"]["regulation"][
        "enum"
    ] == ["UN R148", "UN R7"]
    assert [c.selected for c in out] == [True, True]
    final = select_regs.prefer_consolidated(out, {"UN R148": (), "UN R7": ("UN R148",)})
    assert [c.regulation for c in final if c.selected] == ["UN R148"]


@needs_corpus
def test_base_ranking_puts_installation_and_emc_first_on_the_dev_case() -> None:
    conn = store.connect()
    profile = parse_spec((ROOT / "cases" / "dev-rear-lamp" / "spec.md").read_text())
    ranked = [reg for reg, _ in rank(conn, profile, documents(conn))]
    assert ranked[0] == "UN R48"
    assert {"UN R10", "UN R148", "UN R150"} <= set(ranked[:5])


@needs_corpus
@pytest.mark.parametrize(
    ("case", "gold"),
    [
        ("synth-a03-rear-retro-reflector", {"UN R48", "UN R150"}),
        ("synth-a06-rear-combination-rfq", {"UN R10", "UN R48", "UN R148", "UN R150"}),
        ("synth-a07-rear-position-lamp", {"UN R10", "UN R48", "UN R148"}),
    ],
)
def test_selection_without_llm_finds_gold_and_skips_legacy_lamps(case: str, gold: set) -> None:
    choices = select_regs.choose(_spec(case), load_all("base"), use_llm=False)
    picked = {c.regulation for c in choices if c.selected}
    assert picked == gold
    assert not picked & LEGACY_LAMPS
    r150 = next(c for c in choices if c.regulation == "UN R150")
    assert r150.rationale.startswith("Device approval. Scope: This Regulation applies to retro")
