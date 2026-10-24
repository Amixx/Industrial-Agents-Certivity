"""Checks for the decision-model features read from the obligation base."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from brain import features as F
from brain.graph import build
from brain.kb.ontology import stem
from brain.models import Paragraph, ProductProfile

SCHEMA = Path(__file__).parents[1] / "brain" / "kb" / "schema.sql"
REG = "UN R48"


def _para(
    number: str, text: str, heading: str | None = None, parent: str | None = None
) -> Paragraph:
    pid = f"{REG}|9.0|{number}"
    return Paragraph(
        id=pid,
        regulation=REG,
        version="9.0",
        role="base",
        label=number,
        number=number,
        page=1,
        page_end=1,
        heading=heading,
        text=text,
        parent=parent,
        path=[parent] if parent else [],
    )


@pytest.fixture
def kb() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA.read_text())
    conn.execute(f"INSERT INTO regulation VALUES ('{REG}', '48', '9.0', 't', NULL, NULL)")
    for i, number in enumerate(["2.1", "6.1", "6.1.1", "6.1.2"]):
        conn.execute(
            "INSERT INTO node (id, regulation, version, kind, label, number, depth, ord, page, "
            "page_end, text, page_breaks_json) VALUES (?,?,'9.0','paragraph',?,?,0,?,1,1,'','[]')",
            (f"{REG}|9.0|{number}", REG, number, number, i),
        )
    obligations = [  # node, ord, sub, modality
        ("6.1.1", 0, 0, "shall"),
        ("6.1.1", 1, 0, "may"),
        ("6.1.1", 1, 1, "may"),
        ("6.1.2", 0, 0, "may"),
        ("6.1.2", 1, 0, "other"),
    ]
    for number, ord_, sub, modality in obligations:
        node = f"{REG}|9.0|{number}"
        conn.execute(
            "INSERT INTO obligation (id, node_id, ord, source_kind, char_start, char_end, "
            "page_start, page_end, quote_raw, text_norm, modality, n_modal, condition_type, sub) "
            "VALUES (?,?,?,'sentence',?,?,1,1,'q','q',?,1,'none',?)",
            (f"{node}#{ord_}.{sub}", node, ord_, ord_ * 10, ord_ * 10 + 5, modality, sub),
        )
    conn.execute(
        f"INSERT INTO entity VALUES ('{REG}:rear-position-lamp', 'Rear position lamp', "
        f"'definition', '{REG}', '{REG}|9.0|2.1')"
    )
    conn.execute(f"INSERT INTO entity VALUES ('{REG}:lamp', 'Lamp', 'definition', '{REG}', NULL)")
    for entity, text in [("rear-position-lamp", "tail light"), ("lamp", "Lamp")]:
        conn.execute(
            "INSERT INTO alias VALUES (?,?,?,'seed')", (f"{REG}:{entity}", text, stem(text))
        )
    conn.execute("INSERT INTO fts_alias SELECT entity_id, text, norm FROM alias")
    return conn


def test_obligation_stats_count_source_obligations_only(kb: sqlite3.Connection) -> None:
    stats = F.obligation_stats(kb, [f"{REG}|9.0|{n}" for n in ["6.1", "6.1.1", "6.1.2"]])
    assert stats == {
        f"{REG}|9.0|6.1.1": F.ObligationStats(n=2, modal=1, may=1),
        f"{REG}|9.0|6.1.2": F.ObligationStats(n=2, modal=0, may=1),
    }


def test_obligation_stats_reject_paragraphs_missing_from_the_base(kb: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="not in the obligation base"):
        F.obligation_stats(kb, [f"{REG}|9.0|6.1", f"{REG}|9.0|7.1"])


def test_product_entities_skip_head_word_matches(kb: sqlite3.Connection) -> None:
    profile = ProductProfile(
        product="Rear lamp", parts=["Tail light optics"], keywords=["rear lamp"]
    )
    assert [e["entity_id"] for e in F.product_entities(kb, profile)] == [
        f"{REG}:rear-position-lamp"
    ]


def test_entity_names_join_the_product_terms(kb: sqlite3.Connection) -> None:
    heading = _para("6.1", "Rear position lamps", heading="Rear position lamps")
    shall = _para("6.1.1", "The lamp shall be red. It may be grouped.", parent=heading.id)
    may = _para("6.1.2", "The lamp may be grouped.", parent=heading.id)
    corpus = {REG: [heading, shall, may]}
    profile = ProductProfile(product="Rear lamp", parts=["Tail light"])
    ctx = F.build_context(profile, corpus, build(corpus), {REG: 1.0}, kb)
    assert " rear position lamp " in ctx.product_terms[REG]
    rows = {p.number: dict(zip(F.FEATURES, F.vector(p, ctx), strict=True)) for p in corpus[REG]}
    assert rows["6.1.1"]["func_path"] == 1.0
    assert rows["6.1"]["kb_n_obl"] == 0.0
    assert rows["6.1.1"]["kb_n_obl"] > 0
    assert (rows["6.1.1"]["kb_may_only"], rows["6.1.2"]["kb_may_only"]) == (0.0, 1.0)
