import json

import pytest

from brain.ingest import CORPUS, Line, follows, load, parse_lines, parse_pdf, sources
from brain.paths import CASES
from eval.gold_check import missing


def _lines(*texts: str, page: int = 1) -> list[Line]:
    out, prev = [], ""
    for t in texts:
        out.append(Line(page, t, prev))
        prev = t
    return out


def test_follows() -> None:
    assert follows((1,), None)
    assert follows((3, 3, 1), (3, 3))  # child
    assert follows((3, 4), (3, 3, 2))  # back up one level
    assert follows((4,), (3, 3, 2))
    assert not follows((3, 2), (3, 3))  # backwards
    assert not follows((5, 1, 7), (3, 3))  # jump into a deep unseen paragraph


def test_table_cell_does_not_derail_numbering() -> None:
    lines = _lines(
        "3.2. Approval",
        "3.2.1. A separate approval is required.",
        "Front position lamp MA",
        "5.1.",  # a table cell that looks like a label
        "3.2.2. When two or more lamps are grouped, it shall be approved.",
        "3.3. Approval marking",
    )
    labels = [p.label for p in parse_lines(lines, "UN R148", "1.6.0", "base")]
    assert labels == ["3.2", "3.2.1", "3.2.2", "3.3"]


def test_wrapped_reference_is_not_a_label() -> None:
    lines = _lines("5.1. The lamp shall comply with paragraph", "5.2. of this Regulation.")
    paragraphs = parse_lines(lines, "UN R148", "1.6.0", "base")
    assert [p.label for p in paragraphs] == ["5.1"]
    assert paragraphs[0].text.endswith("5.2. of this Regulation.")


def test_inline_sequential_labels_split_paragraphs() -> None:
    lines = _lines("5.1.1. First condition, or 5.1.2. Second condition, or 5.1.3. Third condition.")
    paragraphs = parse_lines(lines, "UN R26", "4.0.0", "base")
    assert [p.label for p in paragraphs] == ["5.1.1", "5.1.2", "5.1.3"]
    assert [p.text for p in paragraphs] == [
        "First condition, or",
        "Second condition, or",
        "Third condition.",
    ]


def test_inline_cross_reference_does_not_split() -> None:
    lines = _lines("5.1. First condition, see paragraph 5.1.2. The next condition.")
    paragraphs = parse_lines(lines, "UN R26", "4.0.0", "base")
    assert [p.label for p in paragraphs] == ["5.1"]
    assert "paragraph 5.1.2." in paragraphs[0].text


def test_r26_sequential_labels_have_separate_text_boundaries() -> None:
    source = next(s for s in sources() if s.regulation == "UN R26" and s.role == "base")
    paragraphs = parse_pdf(source.pdf, source.regulation, source.version, source.role)
    selected = [p for p in paragraphs if p.label in {"5.1.1", "5.1.2", "5.1.3"}]
    assert [p.label for p in selected] == ["5.1.1", "5.1.2", "5.1.3"]
    assert selected[0].text.endswith("or")
    assert selected[1].text.endswith("or")
    assert "5.1.2." not in selected[0].text
    assert "5.1.3." not in selected[1].text
    assert selected[1].parent == selected[0].parent
    assert selected[2].parent == selected[0].parent


def test_annex_parts_prefix_labels() -> None:
    lines = _lines(
        "1. Scope",
        "Annex 1 Communication",
        "1. Name",
        "Annex 6 Environmental Testing",
        "Annex 2 Minimum requirements",
        "1.2. The lamp shall",
        "Part 1 - Photometric",
        "1. General",
        "1.1. Details",
    )
    paragraphs = parse_lines(lines, "UN R150", "1.2.1", "base")
    labels = [p.label for p in paragraphs]
    assert labels == [
        "1",
        "Annex 1",
        "Annex 1 1",
        "Annex 2",
        "Annex 2 1.2",
        "Annex 2 Part 1",
        "Annex 2 Part 1 1",
        "Annex 2 Part 1 1.1",
    ]
    by_label = {p.label: p for p in paragraphs}
    assert by_label["Annex 2 Part 1 1.1"].parent == by_label["Annex 2 Part 1 1"].id
    assert by_label["Annex 2 Part 1"].parent == by_label["Annex 2"].id


def test_page_breaks_are_tracked() -> None:
    lines = [Line(3, "4.1. The lamp shall be red", ""), Line(4, "and bright.", "x")]
    (p,) = parse_lines(lines, "UN R148", "1.6.0", "base")
    assert (p.page, p.page_end) == (3, 4)
    assert p.page_at(p.text.index("bright")) == 4


@pytest.mark.skipif(not (CORPUS / "UN_R148_base.jsonl").exists(), reason="run brain.ingest first")
def test_every_dev_gold_citation_is_parsed_on_its_page() -> None:
    expected = json.loads((CASES / "dev-rear-lamp" / "expected.json").read_text())
    corpus = {r: load(r) for r in {x["source"]["regulation"] for x in expected["requirements"]}}
    assert missing(expected, corpus) == []
