import json

import pytest

from brain.graph import build
from brain.ingest import CORPUS, Line, load_all, parse_lines
from brain.models import Paragraph
from brain.obligations import condition, modality, sentences
from brain.paths import CASES
from brain.profile import parse_spec
from brain.rewrite import Draft, deterministic
from brain.verify import faithful

HAVE_CORPUS = (CORPUS / "UN_R148_base.jsonl").exists()
needs_corpus = pytest.mark.skipif(not HAVE_CORPUS, reason="run brain.ingest first")


def test_sentences_keep_references_and_abbreviations_together() -> None:
    text = (
        "The lamp shall comply with paragraph 4.6. of this Regulation. "
        "It shall meet UN Regulation No. 48 requirements. However, it may be red."
    )
    assert [s for _, s in sentences(text)] == [
        "The lamp shall comply with paragraph 4.6. of this Regulation.",
        "It shall meet UN Regulation No. 48 requirements.",
        "However, it may be red.",
    ]


def test_modality_and_condition() -> None:
    assert modality("The lamps shall not be red.") == "shall not"
    assert modality("Lamps may be grouped.") == "may"
    kind, cond = condition("When tested at 13.5 V, the lamp shall emit 60 cd.")
    assert kind == "when" and cond == "When tested at 13.5 V"


def _paragraphs(*texts: str) -> list[Paragraph]:
    lines, prev = [], ""
    for t in texts:
        lines.append(Line(1, t, prev))
        prev = t
    return parse_lines(lines, "UN R48", "9.3.0", "base")


def test_rewrite_telegraphic_and_however() -> None:
    ps = _paragraphs(
        "5. Individual specifications",
        "5.1. Reversing lamp",
        "5.1.1. Position",
        "5.1.1.2. In height: not less than 250 mm and not more than 1,200 mm above the ground.",
        "5.1.2. Colour",
        "5.1.2.1. The light shall be white. However, it may be amber in 6 V systems.",
    )
    graph = build({"UN R48": ps})
    by_label = {p.label: p for p in ps}
    (height,) = deterministic(by_label["5.1.1.2"], graph)
    assert height.text.startswith("The reversing lamp shall be not less than 250 mm")
    (colour,) = deterministic(by_label["5.1.2.1"], graph)
    assert colour.text == "The light shall be white, except that it may be amber in 6 V systems."


def test_faithful_rejects_invented_numbers() -> None:
    (p,) = _paragraphs("5.1. The lamp shall emit 60 cd.")
    assert faithful(Draft(p, "The lamp shall emit 60 cd.", ""))
    assert not faithful(Draft(p, "The lamp shall emit 61 cd.", ""))


def test_parse_spec_dev_case() -> None:
    profile = parse_spec((CASES / "dev-rear-lamp" / "spec.md").read_text())
    assert profile.vehicle_categories == ["M1"]
    assert "stop lamp" in profile.keywords and profile.electronics


@needs_corpus
def test_graph_follows_failure_provision_reference() -> None:
    corpus = load_all("base")
    g = build({r: corpus[r] for r in ("UN R148", "UN R48")}, set(corpus))
    assert "UN R148|1.6.0|4.6" in g.refs_out["UN R148|1.6.0|5.5.6"]
    assert g.reg_links["UN R48"].most_common(1)[0][0] == "UN R148"


@needs_corpus
def test_dev_regulation_selection_matches_gold() -> None:
    from brain.select_regs import choose

    corpus = load_all("base")
    profile = parse_spec((CASES / "dev-rear-lamp" / "spec.md").read_text())
    picked = {c.regulation for c in choose(profile, corpus, use_llm=False) if c.selected}
    assert picked == {"UN R10", "UN R48", "UN R148", "UN R150"}


@needs_corpus
def test_pipeline_dev_case_is_valid_and_scores() -> None:
    from brain.pipeline import run
    from eval.score import score

    sub = run((CASES / "dev-rear-lamp" / "spec.md").read_text(), use_llm=False)
    expected = json.loads((CASES / "dev-rear-lamp" / "expected.json").read_text())
    result = score(sub, expected)
    assert result["regulation_level"]["f2"] == 1.0
    assert result["page_level"]["f2"] > 0.65


def test_faithful_accepts_numbers_from_ancestors() -> None:
    (child,) = _paragraphs("6.1. The exhaust system shall not suffer any damage.")
    text = "After each impact test specified in annex 3, the exhaust system shall not be damaged."
    assert not faithful(Draft(child, text, ""))
    assert faithful(Draft(child, text, ""), "After each impact test specified in annex 3 to this")


def test_judge_maximises_acceptable_matches_and_respects_polarity() -> None:
    from eval.judge import match, similarity

    assert similarity("The lamp shall be red.", "The lamp shall not be red.") == 0.0
    sims = {("a", "x"): 0.90, ("a", "y"): 0.46, ("b", "x"): 0.46, ("b", "y"): 0.44}
    sub = [{"text": t, "source": {"regulation": "R"}} for t in ("a", "b")]
    exp = [{"text": t, "source": {"regulation": "R"}} for t in ("x", "y")]
    pairs = match(sub, exp, threshold=0.45, sim=lambda s, e: sims[(s, e)])
    assert len(pairs) == 2


def _para(i: int) -> Paragraph:
    return Paragraph(
        id=f"UN R42|0|{i}",
        regulation="UN R42",
        version="0",
        role="base",
        label=str(i),
        number=str(i),
        page=1,
        page_end=1,
        text="The device shall ...",
    )


def test_relevance_retries_unscored_then_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    from brain import relevance
    from brain.models import ProductProfile

    paragraphs = [_para(i) for i in range(4)]
    graph = build({"UN R42": paragraphs}, {"UN R42"})
    calls: list[int] = []

    def flaky(chunk: list[Paragraph], *_: object) -> dict[str, float]:
        calls.append(len(chunk))
        if len(calls) == 1:
            raise TimeoutError
        return {p.id: 0.5 for p in chunk}

    monkeypatch.setattr(relevance, "_batch", flaky)
    scores = relevance.score(
        paragraphs, graph, ProductProfile(product="bumper"), batch=2, workers=1
    )
    assert set(scores) == {p.id for p in paragraphs}

    monkeypatch.setattr(relevance, "_batch", lambda chunk, *_: {chunk[0].id: 0.5})
    with pytest.raises(RuntimeError, match="unscored after a retry"):
        relevance.score(paragraphs, graph, ProductProfile(product="bumper"), batch=2, workers=1)


def test_prompted_json_accepts_a_bare_array() -> None:
    from brain.llm import _extract_json

    schema = {"type": "object", "properties": {"paragraphs": {"type": "array"}}}
    reply = 'Here you go:\n```json\n[{"id": "a", "p_cited": 0.4}]\n```'
    assert _extract_json(reply, schema) == {"paragraphs": [{"id": "a", "p_cited": 0.4}]}
    assert _extract_json('{"paragraphs": []} trailing', schema) == {"paragraphs": []}


def test_rewrite_keeps_deterministic_rows_when_the_model_answers_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from brain import rewrite

    paragraphs = [_para(i) for i in range(2)]
    for p in paragraphs:
        p.text = "The device shall be marked with the trade name of the applicant."
    graph = build({"UN R42": paragraphs}, {"UN R42"})
    answer = {
        "paragraphs": [
            {"id": paragraphs[0].id, "requirements": [{"text": "Rewritten.", "quote": "q"}]},
            {"id": paragraphs[1].id, "requirements": []},
        ]
    }
    monkeypatch.setattr(rewrite.llm, "complete_json", lambda *_, **__: answer)
    drafts = rewrite._batch(paragraphs, graph, "bumper")
    assert [d.text for d in drafts] == [
        "Rewritten.",
        "The device shall be marked with the trade name of the applicant.",
    ]
