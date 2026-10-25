import copy
import functools
import json
from collections import Counter
from pathlib import Path

import pytest

from brain.ingest import CORPUS, load, parse_pdf
from brain.models import Paragraph
from brain.paths import ROOT
from brain.subgoal import (
    Span,
    added_changes,
    align,
    describe,
    fit,
    fuse,
    kind,
    map_requirements,
    obligations,
    quote,
    run,
    sentences,
    shorten,
    substantive,
    system_name,
    units,
    validate,
    word_ops,
)
from brain.subgoal.score import score
from brain.subgoal.survey import synthetic_pairs

DEV = ROOT / "subgoal" / "dev"
EXPECTED = DEV / "expected.json"


def para(label: str, text: str, page: int = 1, heading: str | None = None) -> Paragraph:
    return Paragraph(
        id=f"UN R1|1|{label}",
        regulation="UN R1",
        version="1",
        role="base",
        label=label,
        number=label,
        page=page,
        page_end=page,
        heading=heading,
        text=text,
    )


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


def test_describe_uses_gold_wording() -> None:
    ops = substantive(
        word_ops("from standstill.", "both from standstill and, as relevant, while creeping.")
    )
    assert set(describe(ops).split("; ")) == {
        "'standstill.' became 'standstill and, as relevant, while creeping.'",
        "'both' was added",
    }


def test_sentences_split_list_items() -> None:
    text = "It shall be close to: (a) The forward speed, (b) 4 km/h rearward. It may be combined."
    assert sentences(text) == [
        "It shall be close to:",
        "(a) The forward speed,",
        "(b) 4 km/h rearward.",
        "It may be combined.",
    ]


def test_format_only_is_not_flagged() -> None:
    links = align(
        [para("5.1", "A speed of 70% shall be\nheld for 6 seconds.")],
        [para("5.1", "A speed of 70 per cent shall be held for 6 s.")],
    )
    assert links and all(not link.ops for link in links)


def test_heading_added_over_unchanged_sentence_is_not_flagged() -> None:
    old = [para("5.1.6", "The speed shall be low.")]
    new = [
        para(
            "5.1.6.1",
            "Acceleration from standstill The speed shall be low.",
            heading="Acceleration from standstill",
        )
    ]
    [link] = align(old, new)
    assert link.new is not None and link.new.label == "5.1.6.1" and link.ops == ()


def test_renumbered_section_is_not_flagged() -> None:
    old = [
        para("6.5", "The target shall be stationary."),
        para("6.6", "The test shall be repeated twice."),
    ]
    new = [
        para("6.6", "The target shall be stationary."),
        para("6.7", "The test shall be repeated twice."),
    ]
    links = align(old, new)
    assert {(link.old.label, link.new.label) for link in links if link.old and link.new} == {
        ("6.5", "6.6"),
        ("6.6", "6.7"),
    }
    assert all(not link.ops for link in links)


def test_split_paragraph_maps_each_sentence_to_its_new_home() -> None:
    old = [
        para(
            "6.5",
            "The offset shall be 0.2 m. The vehicle shall be stationary. "
            "A warm-up run may be made.",
        )
    ]
    new = [
        para("6.5.2", "The offset shall be 0.5 m."),
        para("6.6.1", "The vehicle shall be stationary."),
    ]
    by_old = {link.old.text: link for link in align(old, new) if link.old}
    assert by_old["The offset shall be 0.2 m."].new.label == "6.5.2"  # type: ignore[union-attr]
    assert by_old["The vehicle shall be stationary."].ops == ()
    assert by_old["A warm-up run may be made."].new is None


def test_new_paragraph_is_unclaimed() -> None:
    links = align(
        [para("5.1", "X shall be red.")],
        [para("5.1", "X shall be red."), para("5.2", "Y shall be blue.")],
    )
    assert [link.new.label for link in links if link.old is None and link.new] == ["5.2"]


def test_sentences_split_items_without_punctuation_but_not_references() -> None:
    text = (
        "(v) It is operational (vi) If closed, it is latched. See paragraph 5.1.5. (a) through (d)."
    )
    assert sentences(text) == [
        "(v) It is operational",
        "(vi) If closed, it is latched.",
        "See paragraph 5.1.5. (a) through (d).",
    ]


def test_quote_cuts_like_the_gold() -> None:
    text = (
        "Acceleration while creeping, In the case a collision is not prevented, "
        "the ACPE shall reduce the effective demand"
    )
    assert quote(text, 100) == (
        "Acceleration while creeping, In the case a collision is not prevented, "
        "the ACPE shall reduce the ef…"
    )
    assert quote("Short.", 100) == "Short."


def test_requirement_citing_parent_is_mapped_to_child() -> None:
    old = [para("6.5", "Test conditions"), para("6.5.3", "The offset shall be 0.2 m.")]
    new = [para("6.5", "Test conditions"), para("6.5.3", "The offset shall be 0.5 m.")]
    reqs = [
        {
            "id": "R-1",
            "text": "The offset shall be 0.2 m.",
            "source": {"page": 1, "paragraph": "6.5"},
        }
    ]
    [c] = map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0")
    assert c["change"] == "modified" and c["source"]["paragraph"] == "6.5.3"
    assert (
        c["reason"] == "Paragraph 6.5.3 of UN R1 was amended in version 2.0.0: '0.2' became '0.5'."
    )
    assert c["new_text"] == "The offset shall be 0.5 m."


def test_unchanged_sentence_moved_to_another_paragraph_is_not_flagged() -> None:
    old = [para("6.5", "The offset shall be 0.2 m. The vehicle shall be stationary.")]
    new = [
        para("6.5", "The offset shall be 0.5 m."),
        para("6.6.1", "The vehicle shall be stationary."),
    ]
    reqs = [
        {
            "id": "R-2",
            "text": "The vehicle shall be stationary.",
            "source": {"page": 1, "paragraph": "6.5"},
        }
    ]
    assert map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0") == []


def test_deleted_sentence_is_removed_with_quote() -> None:
    old = [para("6.5", "The offset shall be 0.2 m. A warm-up run may be made before the test.")]
    new = [para("6.5", "The offset shall be 0.2 m.")]
    reqs = [
        {
            "id": "R-3",
            "text": "A warm-up run may be made.",
            "source": {"page": 1, "paragraph": "6.5"},
        }
    ]
    [c] = map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0")
    assert c == {
        "requirement_id": "R-3",
        "change": "removed",
        "reason": "Paragraph 6.5 of UN R1 was amended in version 2.0.0; the provision "
        "'A warm-up run may be made before the test.' no longer appears.",
    }


@functools.cache
def dev_pair() -> tuple[list[Paragraph], list[Paragraph]]:
    return (
        parse_pdf(DEV / "old.pdf", "UN R175", "0.1.0", "base"),
        parse_pdf(DEV / "new.pdf", "UN R175", "1.0.0", "latest"),
    )


needs_dev_pdfs = pytest.mark.skipif(not (DEV / "old.pdf").exists(), reason="dev PDFs not fetched")


@needs_dev_pdfs
def test_dev_modified_and_removed_match_gold() -> None:
    old, new = dev_pair()
    reqs = json.loads((DEV / "requirements_old.json").read_text())
    changes = map_requirements(reqs, old, align(old, new), "UN R175", "1.0.0")
    assert {(c["requirement_id"], c["change"]) for c in changes} == {
        ("R-015", "modified"),
        ("R-018", "modified"),
        ("R-021", "modified"),
        ("R-084", "modified"),
        ("R-085", "modified"),
        ("R-086", "modified"),
        ("R-090", "removed"),
    }
    sources = {c["requirement_id"]: c.get("source", {}).get("paragraph") for c in changes}
    assert (sources["R-084"], sources["R-085"], sources["R-086"]) == ("6.5.2", "6.6", "6.6.1.2")


@needs_dev_pdfs
def test_dev_reordered_requirement_covers_its_first_sentence() -> None:
    old, new = dev_pair()
    reqs = [
        r for r in json.loads((DEV / "requirements_old.json").read_text()) if r["id"] == "R-021"
    ]
    [c] = map_requirements(reqs, old, align(old, new), "UN R175", "1.0.0")
    assert "'between 1.0 m and' became 'not more than'" in c["reason"]
    assert "'(vi) If the vehicle is equipped" in c["reason"]


def test_amended_unit_prefers_its_own_paragraph_and_region_stays_local() -> None:
    old = [para("5.1", "A shall be red. The offset between the obstacle and the vehicle is 0.2 m.")]
    new = [
        para(
            "5.1", "A shall be red. In the case of an obstacle, the offset to the vehicle is 0.4 m."
        ),
        para("6.1", "X shall be blue."),
        para("6.5", "The offset between the pedestrian obstacle and the vehicle is 25 per cent."),
    ]
    links = align(old, new)
    moved = [link for link in links if link.old and link.old.text.startswith("The offset")]
    assert moved[0].new is not None and moved[0].new.label == "5.1"
    reqs = [
        {
            "id": "R-4",
            "text": "A shall be red. The offset between the obstacle and the vehicle is 0.2 m.",
            "source": {"page": 1, "paragraph": "5.1"},
        }
    ]
    [c] = map_requirements(reqs, old, links, "UN R1", "2.0.0")
    assert "blue" not in c["reason"] and "pedestrian" not in c["reason"]


def test_items_under_a_shall_lead_in_become_one_row_each() -> None:
    lead = "The procedure shall be as follows:"
    rows = obligations(
        [
            Span("6.6.2.2", 11, lead, 0),
            Span("6.6.2.2", 11, "(a) Position the vehicle at the start.", 1),
            Span("6.6.2.2", 11, "(b) Hold the vehicle stationary.", 2),
        ]
    )
    assert rows == [
        (
            "(a) Position the vehicle at the start.",
            "The procedure shall be to position the vehicle at the start.",
        ),
        (
            "(b) Hold the vehicle stationary.",
            "The procedure shall be to hold the vehicle stationary.",
        ),
    ]


def test_items_under_a_lead_in_without_shall_stay_one_row() -> None:
    rows = obligations(
        [
            Span("5.1.4.1", 5, "An intervention is not required when:", 0),
            Span(
                "5.1.4.1", 5, "(a) there is a warning; or (b) the speed is greater than 10 km/h.", 1
            ),
        ]
    )
    text = (
        "An intervention is not required when: (a) there is a warning; "
        "or (b) the speed is greater than 10 km/h."
    )
    assert rows == [(text, text)]


def test_sentence_with_shall_and_may_gives_two_rows_and_heading_is_quoted() -> None:
    sentence = "For tests without a target the ACPE shall be deactivated, and may be combined."
    rows = obligations([Span("6.6.1.1", 10, sentence, 0, lead="Without target,")])
    assert [q for q, _ in rows] == [f"Without target, {sentence}"] * 2
    assert rows[0][1] == (
        "For without target, for tests without a target the ACPE shall be deactivated."
    )


def test_sentence_without_modal_or_number_is_not_an_obligation() -> None:
    assert (
        obligations([Span("6.5.4", 10, "The orientation is to be determined by the service.", 0)])
        == []
    )
    assert (
        len(
            obligations(
                [Span("6.5.3", 10, "The offset is not more than 25 per cent of the width.", 0)]
            )
        )
        == 1
    )


def test_section_outside_requirement_scope_adds_nothing() -> None:
    new = [para("12.1.1", "Contracting Parties shall accept approvals.")]
    links = align([], new)
    assert added_changes(links, {"5", "6"}, "UN R1", "2.0.0") == []
    [c] = added_changes(links, {"12"}, "UN R1", "2.0.0")
    assert c == {
        "requirement_id": None,
        "change": "added",
        "new_text": "Contracting Parties shall accept approvals.",
        "reason": "Paragraph 12.1.1 of UN R1 is new in version 2.0.0: "
        "'Contracting Parties shall accept approvals.'.",
        "source": {"page": 1, "paragraph": "12.1.1"},
    }


def test_new_sentence_in_an_existing_paragraph_is_added() -> None:
    old = [para("5.1", "X shall be red.")]
    new = [para("5.1", "X shall be red. Y shall be blue.")]
    [c] = added_changes(align(old, new), {"5"}, "UN R1", "2.0.0")
    assert c == {
        "requirement_id": None,
        "change": "added",
        "new_text": "Y shall be blue.",
        "reason": "Paragraph 5.1 of UN R1 was amended in version 2.0.0: "
        "'Y shall be blue.' was added.",
        "source": {"page": 1, "paragraph": "5.1"},
    }


def test_new_item_footnote_or_consumed_sentence_in_an_old_paragraph_is_not_added() -> None:
    old = [para("5.1", "X shall be red provided: (a) It is day; (b) It is dry. Z shall be green.")]
    new = [
        para(
            "5.1",
            "X shall be red provided: (a) It is day; (b) It is dry; (c) It is above 5 °C. "
            "3 This condition shall be reviewed by 2032. Z shall be green. W shall be blue.",
        )
    ]
    links = align(old, new)
    consumed = {s.index for s in units(new) if s.text.startswith("W ")}
    assert added_changes(links, {"5"}, "UN R1", "2.0.0", consumed=consumed) == []


def test_unchanged_lead_in_paragraph_is_not_added() -> None:
    old = [para("3.2", "It shall be accompanied by the documents below:")]
    new = [para("3.2", "It shall be accompanied by the documents below:")]
    assert added_changes(align(old, new), {"3"}, "UN R1", "2.0.0") == []


def test_run_requires_version_when_unknown(tmp_path: Path) -> None:
    other = tmp_path / "new.pdf"
    other.write_bytes((DEV / "new.pdf").read_bytes() + b"%")
    reqs = json.loads((DEV / "requirements_old.json").read_text())
    with pytest.raises(ValueError, match="pass --to-version"):
        run(DEV / "old.pdf", other, reqs, case_id="x")


@needs_dev_pdfs
def test_dev_scores_100_100() -> None:
    reqs = json.loads((DEV / "requirements_old.json").read_text())
    submission = run(DEV / "old.pdf", DEV / "new.pdf", reqs, case_id="subgoal-dev")
    assert submission["team_id"] == "team-06" and submission["case_id"] == "subgoal-dev"
    assert all("old_span" not in c for c in submission["changes"])
    r = score(submission, json.loads(EXPECTED.read_text()))
    assert (r.flag_recall, r.change_accuracy, r.extra) == (1.0, 1.0, 0), r.mismatches


def test_fit_cuts_long_text_at_a_unit_boundary() -> None:
    text = " ".join(f"({i}) Item {i} shall be red;" for i in range(200))
    cut = fit(text, 2000)
    assert len(cut) <= 2000 and cut.endswith(";") and text.startswith(cut)
    assert fit("Short.", 2000) == "Short."


@needs_dev_pdfs
def test_dev_submission_is_valid() -> None:
    reqs = json.loads((DEV / "requirements_old.json").read_text())
    submission = run(DEV / "old.pdf", DEV / "new.pdf", reqs, case_id="subgoal-dev")
    assert validate(submission, reqs) == []


needs_corpus = pytest.mark.skipif(
    not (CORPUS / "UN_R48_base.jsonl").exists(), reason="corpus not ingested"
)


@needs_corpus
@pytest.mark.parametrize("regulation", ["UN R48", "UN R10", "UN R149"])
def test_synthetic_edits_are_found_exactly(regulation: str) -> None:
    pairs = synthetic_pairs(load(regulation, "base"))
    assert [name for name, *_ in pairs] == [
        "renumber",
        "insert",
        "delete",
        "number",
        "split",
        "whitespace",
    ]
    for name, old, new, expected in pairs:
        found = {
            (link.old.label if link.old else "", kind(link))
            for link in align(old, new)
            if kind(link) != "unchanged"
        }
        assert found == expected, name


def test_glued_old_unit_matches_its_new_pieces() -> None:
    old = [
        para(
            "2.2.5",
            '"Capacity" means the fuel-tank capacity as specified by the manufacturer. '
            "3. APPLICATION FOR APPROVAL The application for approval shall be submitted by the "
            "vehicle manufacturer.",
        )
    ]
    new = [
        para("2.2.5", '"Capacity" means the fuel-tank capacity as specified by the manufacturer.'),
        para("3", "APPLICATION FOR APPROVAL", heading="APPLICATION FOR APPROVAL"),
        para("3.1", "The application for approval shall be submitted by the vehicle manufacturer."),
    ]
    links = align(old, new)
    assert all(kind(link) == "unchanged" for link in links)
    assert sorted(link.new.label for link in links if link.new) == ["2.2.5", "3.1"]
    reqs = [
        {
            "id": "R-5",
            "text": "The application for approval shall be submitted by the vehicle manufacturer.",
            "source": {"page": 1, "paragraph": "2.2.5"},
        }
    ]
    assert map_requirements(reqs, old, links, "UN R1", "2.0.0") == []
    assert added_changes(links, {"2", "3"}, "UN R1", "2.0.0") == []


def test_item_with_its_own_modal_is_not_fused() -> None:
    rows = obligations(
        [
            Span("6.6.2.2", 11, "The procedure shall be as follows:", 0),
            Span("6.6.2.2", 11, "(e) If it fails the maker shall show compliance.", 1),
        ]
    )
    assert rows == [
        (
            "(e) If it fails the maker shall show compliance.",
            "During the procedure, if it fails the maker shall show compliance.",
        )
    ]


def test_clause_after_the_last_item_applies_to_every_item() -> None:
    rows = obligations(
        [
            Span("6.6.2.1", 11, "The speed shall be as close to:", 0),
            Span("6.6.2.1", 11, "(a) The maximum creeping speed forward,", 1),
            Span(
                "6.6.2.1", 11, "(b) 4 km/h rearward, As reasonably practical without a warning.", 2
            ),
        ]
    )
    assert [text for _, text in rows] == [
        "The speed shall be as close to the maximum creeping speed forward as reasonably practical"
        " without a warning.",
        "The speed shall be as close to 4 km/h rearward as reasonably practical without a warning.",
    ]


def test_run_in_heading_is_kept_as_condition() -> None:
    [(quoted, text)] = obligations(
        [
            Span(
                "5.1.6.2",
                6,
                "In the case of a collision, the ACPE shall cut the demand.",
                0,
                lead="Acceleration while creeping,",
            )
        ]
    )
    assert quoted == (
        "Acceleration while creeping, In the case of a collision, the ACPE shall cut the demand."
    )
    assert text == (
        "For acceleration while creeping, in the case of a collision, the ACPE shall cut "
        "the demand."
    )


def test_second_modal_takes_the_for_phrase_as_subject() -> None:
    rows = obligations(
        [
            Span(
                "6.6.1.1",
                10,
                "For tests without a target the ACPE shall be off, and may be combined.",
                0,
            )
        ]
    )
    assert [text for _, text in rows] == [
        "For tests without a target the ACPE shall be off.",
        "Tests without a target may be combined.",
    ]


def test_moved_requirement_keeps_its_own_subject_with_the_edits_applied() -> None:
    old = [
        para("6.5", "Old test The test procedure shall be performed at 1.0 m.", heading="Old test")
    ]
    new = [
        para(
            "6.6",
            "Test procedures The test procedures shall be performed at 1.5 m.",
            heading="Test procedures",
        )
    ]
    reqs = [
        {
            "id": "R-6",
            "text": "The old test procedure shall be performed at 1.0 m.",
            "source": {"page": 1, "paragraph": "6.5"},
        }
    ]
    [c] = map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0")
    assert c["source"]["paragraph"] == "6.6"
    assert c["new_text"] == "The old test procedures shall be performed at 1.5 m."


def test_footnote_marker_change_is_not_substantive() -> None:
    assert (
        substantive(word_ops("the vehicle. 6This is a note.", "the vehicle. 1 This is a note."))
        == []
    )
    assert substantive(word_ops("within 6 s.", "within 8 s.")) != []


def test_shorten_drops_a_dangling_tail_and_unchanged_sublists_first() -> None:
    text = (
        "The ACPE shall act, provided: (a) The road is dry; (b) The sensing is clear, i.e.: "
        "(i) The light is at least 1000 Lux; (ii) There is no fog; (c) The situation is clear, "
        "i.e.: (i) The obstacle is a wall at least 1.0 m wide. "
        "(ii) The direction is straight and the"
    )
    short = shorten(text, ["a wall at least 1.0 m wide"], limit=170)
    assert short == (
        "The ACPE shall act, provided: (a) The road is dry; (b) The sensing is clear; "
        "(c) The situation is clear, i.e.: (i) The obstacle is a wall at least 1.0 m wide."
    )
    assert shorten("Short.", [], limit=100) == "Short."


@needs_dev_pdfs
def test_dev_long_requirement_keeps_its_amended_items() -> None:
    old, new = dev_pair()
    reqs = [
        r for r in json.loads((DEV / "requirements_old.json").read_text()) if r["id"] == "R-021"
    ]
    [c] = map_requirements(reqs, old, align(old, new), "UN R175", "1.0.0")
    assert len(c["new_text"]) <= 2000
    assert c["new_text"].endswith("not more than 25 per cent of the vehicle width.")
    assert "The direction of travel is straight" not in c["new_text"]


def test_system_name_is_the_most_frequent_acronym_not_a_standard() -> None:
    new = [
        para("1.1", "This Regulation applies to the Acceleration Control for Pedal Error (ACPE)."),
        para("2.1", "Light emitting diode (LED) means a light source. The LED. The LED. The LED."),
        para("5.1", "The ACPE shall act. The ACPE shall warn per ISO 1234 and ISO 5678."),
        para("5.2", "The ACPE shall stop. The ACPE shall log. The ACPE shall reset."),
    ]
    assert system_name(new, minimum=3) == "ACPE"
    assert system_name([para("5.1", "Per ISO 1 and ISO 2 and ISO 3.")], minimum=3) == ""
    switched = [para("5.1", "Switch ON and OFF. OFF. OFF. OFF.")]  # frequent, never defined
    assert system_name(switched, minimum=3) == ""


def test_a_name_the_new_version_no_longer_has_becomes_the_system_name() -> None:
    old = [
        para(
            "6.5",
            "Misapplication test The test procedure shall be performed at 1.0 m.",
            heading="Misapplication test",
        )
    ]
    new = [
        para(
            "6.6",
            "Test procedures The test procedures shall be performed at 1.5 m.",
            heading="Test procedures",
        )
    ]
    reqs = [
        {
            "id": "R-7",
            "text": "The misapplication test procedure shall be performed at 1.0 m.",
            "source": {"page": 1, "paragraph": "6.5"},
        }
    ]
    [c] = map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0", new=new, system="ACPE")
    assert c["new_text"] == "The ACPE test procedures shall be performed at 1.5 m."


def test_number_words_are_a_spelling_variant() -> None:
    assert substantive(word_ops("within three seconds", "within 3 seconds")) == []
    assert substantive(word_ops("within three seconds", "within 4 seconds")) != []


def test_footnote_marker_after_a_closing_quote_is_not_substantive() -> None:
    assert substantive(word_ops('the "DETA"1, value', 'the "DETA"4, value')) == []


def test_same_paragraph_rewrite_pairs_at_a_lower_similarity() -> None:
    old = [
        para(
            "5.5.4",
            "When the system is disabled due to insufficient engagement by the driver, at the "
            "latest upon the deactivation of the powertrain, the system shall request that the "
            "driver reads the driver information material and confirms it.",
        )
    ]
    new = [
        para(
            "5.5.4",
            "When the system is disabled due to insufficient engagement by the driver, the system "
            "shall only be re-enabled after a deliberate action and a display of their "
            "responsibilities.",
        )
    ]
    [link] = align(old, new)
    assert kind(link) == "amended"
    elsewhere = [new[0].model_copy(update={"label": "7.1", "id": "x"})]
    assert {kind(link) for link in align(old, elsewhere)} == {"deleted", "new"}


def test_strong_match_elsewhere_beats_a_weak_one_in_the_same_paragraph() -> None:
    old = [
        para(
            "5.3.2",
            "A manoeuvre shall not be initiated if the system has presented an EOR to the driver "
            "in the 7 seconds leading up to the initiation of the manoeuvre.",
        ),
        para(
            "5.3.2.1",
            "In addition, further strategies shall be implemented to ensure appropriate driver "
            "engagement prior to the initiation of the manoeuvre.",
        ),
    ]
    new = [
        para(
            "5.3.2",
            "The strategies shall be implemented to ensure appropriate driver engagement prior to "
            "the initiation of the manoeuvre, which shall be documented.",
        )
    ]
    by_old = {link.old.label: link for link in align(old, new) if link.old}
    assert kind(by_old["5.3.2"]) == "deleted"
    assert kind(by_old["5.3.2.1"]) == "amended"


def test_rewrite_in_place_needs_one_unpaired_unit_on_each_side() -> None:
    old = [
        para(
            "5.3.7",
            "A manoeuvre shall only be initiated if the driver is not detected to be disengaged, "
            "and (a) has commanded the system to perform the manoeuvre for a driver-initiated "
            "manoeuvre; or (b) has acknowledged the system's intention as needed for a "
            "driver-confirmed manoeuvre; or (c) is given sufficient notice to react for a "
            "system-initiated manoeuvre. Motoric disengagement may not be considered when HORs "
            "are being withheld by the system.",
        )
    ]
    new = [
        para(
            "5.3.7",
            "A manoeuvre shall only be initiated if the driver is not deemed to be disengaged (as "
            "specified in paragraphs 5.5.4.2.4. and 5.5.4.2.5.) for more than 2 seconds "
            "immediately prior to its start, and: (a) Has commanded the system to perform the "
            "manoeuvre for a driver-initiated manoeuvre; or (b) Has acknowledged the system's "
            "intention as needed for a driver-confirmed manoeuvre; or (c) Is given sufficient "
            "notice to react for a system-initiated manoeuvre. Motoric disengagement may not be "
            "considered when HORs are being withheld by the system.",
        )
    ]
    link = next(link for link in align(old, new) if link.old)
    assert kind(link) == "deleted"  # one old unit against four new ones: no rewrite in place
    text = (
        "When the driver is not detected to be disengaged, and (a) has commanded the system to "
        "perform the manoeuvre for a driver-initiated manoeuvre; or (b) has acknowledged the "
        "system's intention as needed for a driver-confirmed manoeuvre; or (c) is given "
        "sufficient notice to react for a system-initiated manoeuvre, the system shall initiate "
        "a manoeuvre, except that motoric disengagement may not be considered when HORs are being "
        "withheld by the system."
    )
    reqs = [{"id": "R-8", "text": text, "source": {"page": 1, "paragraph": "5.3.7"}}]
    [c] = map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0")
    assert "'detected' became 'deemed'" in c["reason"]


def test_heading_running_into_lowercase_text_stays_in_the_text() -> None:
    p = para(
        "5.3.7.2.4.11",
        "Where the manoeuvre is performed the circumstances shall be described.",
        heading="Where the manoeuvre is performed the",
    )
    assert [u.text for u in units([p])] == [
        "Where the manoeuvre is performed the circumstances shall be described."
    ]


def test_sentence_after_a_paragraph_number_is_its_own_unit() -> None:
    text = (
        "It is required by paragraph 5.3.6.1.1. The maker shall explain it. See 5.1.5. (a) to (d)."
    )
    assert sentences(text) == [
        "It is required by paragraph 5.3.6.1.1.",
        "The maker shall explain it.",
        "See 5.1.5. (a) to (d).",
    ]


def test_lead_in_about_the_following_keeps_its_colon() -> None:
    assert (
        fuse(
            "The system shall only drive off if both of the following conditions are fulfilled:",
            "(a) The driver is attentive.",
        )
        == "The system shall only drive off if both of the following conditions are fulfilled: "
        "the driver is attentive."
    )


def test_untouched_sentence_in_an_amended_paragraph_is_not_flagged() -> None:
    # Held-out upload of 25 Oct 08:43: flagging these matched 1 gold row of 22.
    old = [para("6.5", "The offset shall be 0.2 m. The vehicle shall be stationary.")]
    new = [para("6.5", "The offset shall be 0.5 m. The vehicle shall be stationary.")]
    reqs = [
        {
            "id": "R-2",
            "text": "The vehicle shall be stationary.",
            "source": {"page": 1, "paragraph": "6.5"},
        }
    ]
    assert map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0") == []


@needs_dev_pdfs
def test_dev_added_rows_match_gold_paragraphs() -> None:
    old, new = dev_pair()
    sections = {"3", "4", "5", "6", "7", "8"}
    changes = added_changes(align(old, new), sections, "UN R175", "1.0.0")
    assert Counter(c["source"]["paragraph"] for c in changes) == Counter(
        {"5.1.4.1": 1, "5.1.6.2": 1, "6.4.2": 1, "6.5.1": 1, "6.5.3": 1, "6.5.5": 1}
        | {"6.6.1.1": 3, "6.6.2.1": 3, "6.6.2.2": 5}
    )


def test_inclusive_mode_adds_items_every_section_and_sentences_without_a_modal() -> None:
    old = [
        para("5.1", "X shall be red provided: (a) It is day; (b) It is dry."),
        para("Annex 4 2", "The test shall be run once."),
    ]
    new = [
        para("5.1", "X shall be red provided: (a) It is day; (b) It is dry; (c) It is warm."),
        para("Annex 4 2", "The test shall be run once."),
        para("Annex 4 3", "The test shall be repeated at 20 km/h."),
        para("16.1", "Contracting Parties shall accept approvals."),
        para("2.28", "A highway-like road is a road with two lanes."),
    ]
    links = align(old, new)
    assert added_changes(links, {"5"}, "UN R1", "2.0.0") == []
    rows = added_changes(links, {"5"}, "UN R1", "2.0.0", inclusive=True)
    assert [r["source"]["paragraph"] for r in rows] == ["5.1", "Annex 4 3", "16.1", "2.28"]


def test_inclusive_mode_flags_an_untouched_sentence_in_a_paragraph_amended_in_place() -> None:
    old = [para("5.3", "The system shall detect boundaries. The system shall warn the driver.")]
    new = [
        para("5.3", "The system shall detect boundaries. The system shall warn the driver at once.")
    ]
    reqs = [
        {
            "id": "R-9",
            "text": "The system shall detect boundaries.",
            "source": {"page": 1, "paragraph": "5.3"},
        }
    ]
    links = align(old, new)
    assert map_requirements(reqs, old, links, "UN R1", "2.0.0") == []
    [c] = map_requirements(reqs, old, links, "UN R1", "2.0.0", inclusive=True)
    assert c["change"] == "modified" and c["new_text"] == "The system shall detect boundaries."
    assert c["reason"] == (
        "Paragraph 5.3 of UN R1 was amended in version 2.0.0: 'driver.' became 'driver at once.'."
    )


def test_inclusive_mode_flags_a_requirement_whose_paragraph_was_renumbered() -> None:
    old = [
        para("6.5", "The target shall be stationary."),
        para("6.6", "The test shall be repeated."),
    ]
    new = [
        para("6.6", "The target shall be stationary."),
        para("6.7", "The test shall be repeated."),
    ]
    reqs = [
        {
            "id": "R-10",
            "text": "The target shall be stationary.",
            "source": {"page": 1, "paragraph": "6.5"},
        }
    ]
    links = align(old, new)
    assert map_requirements(reqs, old, links, "UN R1", "2.0.0") == []
    [c] = map_requirements(reqs, old, links, "UN R1", "2.0.0", inclusive=True)
    assert c["change"] == "modified" and c["source"]["paragraph"] == "6.6"
    assert c["new_text"] == "The target shall be stationary."
    assert c["reason"] == (
        "Paragraph 6.6 (formerly 6.5) of UN R1 was renumbered in version 2.0.0; its wording did "
        "not change."
    )


def test_inclusive_mode_flags_a_requirement_whose_cited_subtree_changed() -> None:
    old = [para("6.2", "Lane changes shall be safe."), para("6.2.1", "The gap shall be 1 s.")]
    new = [para("6.2", "Lane changes shall be safe."), para("6.2.1", "The gap shall be 2 s.")]
    reqs = [
        {
            "id": "R-11",
            "text": "Lane changes shall be safe.",
            "source": {"page": 1, "paragraph": "6.2"},
        }
    ]
    links = align(old, new)
    assert map_requirements(reqs, old, links, "UN R1", "2.0.0") == []
    [c] = map_requirements(reqs, old, links, "UN R1", "2.0.0", inclusive=True)
    assert c["change"] == "modified" and c["new_text"] == "Lane changes shall be safe."
    assert c["reason"] == (
        "Paragraph 6.2 of UN R1 was amended in version 2.0.0: paragraph 6.2.1 below it changed."
    )
