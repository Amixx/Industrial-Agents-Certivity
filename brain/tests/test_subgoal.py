import copy
import json

from brain.paths import ROOT
from eval.subgoal_score import score

DEV = ROOT / "subgoal" / "dev"
EXPECTED = DEV / "expected.json"


def test_gold_scores_itself_perfectly() -> None:
    gold = json.loads(EXPECTED.read_text())
    r = score(gold, gold)
    assert (r.flag_recall, r.change_accuracy, r.reason_exact, r.extra) == (1.0, 1.0, 1.0, 0)


def test_wrong_change_type_costs_accuracy_not_recall() -> None:
    gold = json.loads(EXPECTED.read_text())
    sub = copy.deepcopy(gold)
    sub["changes"][6]["change"] = "modified"  # R-090 removed -> modified
    r = score(sub, gold)
    assert r.flag_recall == 1.0 and r.change_accuracy == 23 / 24
    assert any("R-090" in m for m in r.mismatches)


def test_added_rows_match_within_their_paragraph() -> None:
    gold = json.loads(EXPECTED.read_text())
    sub = copy.deepcopy(gold)
    sub["changes"][7]["source"]["paragraph"] = "9.9"  # 5.1.6.2 moved away
    r = score(sub, gold)
    assert r.flag_recall == 23 / 24 and r.extra == 1
