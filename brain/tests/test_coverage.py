from typing import Any

from eval.coverage import coverage


def row(id: str, paragraph: str, text: str) -> dict[str, Any]:
    source = {"regulation": "UN R1", "version": "1", "page": 1, "paragraph": paragraph}
    return {"id": id, "text": text, "source": source}


EXPECTED = [
    row("E1", "1", "The lamp shall emit red light."),
    row("E2", "2", "The housing shall be sealed against dust ingress."),
    row("E3", "2", "The housing shall resist vibration at 10 Hz."),
    row("E4", "3", "The lens shall be marked with the approval number."),
    row("E5", "4. Table 1", "The intensity shall be at least 4 cd."),
    row("E6", "5", "The seal shall withstand salt spray."),
]
SUBMITTED = [
    row("S1", "1", "The lamp shall emit red light."),
    row("S2", "2", "The housing shall be sealed against dust ingress and resist vibration."),
    row("S3", "3", "Each device carries a trade name."),
    row("S4", "4", "Minimum luminous intensity 4 cd applies."),
    row("S5", "9", "The bracket shall be black."),
]
CUT = [{"regulation": "UN R1", "paragraph": "5.", "score": 0.12, "cut": 0.15, "stage": "paragraph"}]


def test_each_miss_gets_one_reason_and_the_nearest_row_on_its_paragraph() -> None:
    out = coverage(SUBMITTED, EXPECTED, CUT)
    assert out["local"]["matched"] == 2
    missed = {m["id"]: m for m in out["missed"]}
    assert {i: m["reason"] for i, m in missed.items()} == {
        "E3": "split_finer",  # one row on paragraph 2 against the expert's two
        "E4": "worded_differently",
        "E5": "worded_differently",  # "4. Table 1" is paragraph 4
        "E6": "below_cut",
    }
    assert (missed["E3"]["nearest"]["id"], missed["E3"]["nearest"]["paired_with"]) == ("S2", "E2")
    assert "paired_with" not in missed["E4"]["nearest"]
    assert missed["E5"]["nearest"]["id"] == "S4"
    assert (missed["E6"]["score"], missed["E6"]["cut"]) == (0.12, 0.15)
    assert "nearest" not in missed["E6"]
    extra = {e["id"]: e["on_expert_paragraph"] for e in out["extra"]}
    assert extra == {"S3": True, "S4": True, "S5": False}
