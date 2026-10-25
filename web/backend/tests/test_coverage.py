import json
from pathlib import Path
from typing import Any

import pytest

from app import coverage, store
from app.models import Assessment
from app.paths import BRAIN_PYTHON


def row(id: str, paragraph: str, text: str) -> dict[str, Any]:
    source = {"regulation": "UN R1", "version": "1", "page": 1, "paragraph": paragraph}
    return {"id": id, "text": text, "source": source}


def assessment(requirements: list[dict[str, Any]], **extra: Any) -> Assessment:
    profile = {
        "productType": "",
        "vehicleCategory": "",
        "parts": [],
        "functions": [],
        "materials": [],
    }
    return Assessment.model_validate(
        {
            "id": "test",
            "createdAt": "",
            "spec": "",
            "profile": profile,
            "regulations": [],
            "requirements": requirements,
            "status": "complete",
            **extra,
        }
    )


@pytest.mark.skipif(not BRAIN_PYTHON.exists(), reason="needs the brain's venv")
def test_the_local_judge_gives_each_miss_one_reason(tmp_path: Path) -> None:
    expected = tmp_path / "expected.json"
    gold = [
        row("E1", "1", "The lamp shall emit red light."),
        row("E2", "2", "The housing shall be sealed against dust ingress."),
        row("E3", "2", "The housing shall resist vibration at 10 Hz."),
        row("E4", "3", "The lens shall be marked with the approval number."),
        row("E5", "5", "The seal shall withstand salt spray."),
    ]
    expected.write_text(json.dumps({"requirements": gold}))
    ours = assessment(
        [
            row("S1", "1", "The lamp shall emit red light."),
            row(
                "S2", "2", "The housing shall be sealed against dust ingress and resist vibration."
            ),
            row("S3", "3", "Each device carries a trade name."),
            row("S4", "9", "The bracket shall be black."),
        ],
        belowCut=[
            {
                **row("", "5", "")["source"],
                "score": 0.12,
                "cut": 0.15,
                "stage": "paragraph",
            }
        ],
    )
    judged = coverage.judge(ours, expected)
    assert judged["local"]["matched"] == 2
    reasons = {m["id"]: (m["reason"], m.get("nearest", {}).get("id")) for m in judged["missed"]}
    assert reasons == {
        "E3": ("split_finer", "S2"),
        "E4": ("worded_differently", "S3"),
        "E5": ("below_cut", None),
    }
    below = next(m for m in judged["missed"] if m["id"] == "E5")
    assert (below["score"], below["cut"]) == (0.12, 0.15)


def test_the_fingerprint_ignores_order_and_ids() -> None:
    a = [row("A", "1", "One."), row("B", "2", "Two.")]
    b = [row("X", "2", "Two."), row("Y", "1", "One.")]
    fp = coverage.fingerprint
    assert fp(assessment(a).requirements) == fp(assessment(b).requirements)
    assert fp(assessment(a).requirements) != fp(assessment(a[:1]).requirements)


def test_the_best_dev_upload_has_both_scores_and_every_miss_a_reason() -> None:
    store.load()
    lamp = next(a for a in store.assessments.values() if a.case_name == "Rear lamp, F2 0.794")
    found = coverage.coverage_for(lamp)
    assert found.has_answer and found.local and found.platform
    assert found.platform.file == "rear-lamp-consolidate-v2.json"
    assert (found.platform.uploads[-1].matched, found.platform.uploads[-1].f2) == (167, 0.794)
    assert found.local.matched + len(found.missed) == found.local.expected == 190
    assert all(m.reason == "below_cut" or m.nearest for m in found.missed)
    assert {d.regulation for d in found.excluded} >= {"UN R7", "UN R23", "UN R3"}


def test_the_front_bumper_has_no_expert_answer() -> None:
    store.load()
    bumper = next(a for a in store.assessments.values() if a.case_name == "Front bumper, F2 0.706")
    found = coverage.coverage_for(bumper)
    assert found.case == "heldout-front-bumper"
    assert not found.has_answer and found.local is None and not found.missed
    assert found.near_cut and found.excluded
    assert any(not n.kept and n.cut for n in found.near_cut)


def test_the_showcase_is_flagged_as_the_expert_answer_itself() -> None:
    store.load()
    found = coverage.coverage_for(store.assessments["f14b0208"])
    assert found.local and found.expert_copies == found.local.expected == 190
    assert found.engine_run
    lamp = store.assessments[found.engine_run]
    assert lamp.case_name == "Rear lamp, F2 0.794"
