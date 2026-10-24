"""Checks for the deterministic knowledge-base compiler."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from brain.graph import build as build_graph
from brain.ingest import load_all
from brain.kb.build import build_db


@pytest.fixture(scope="module")
def kb(tmp_path_factory: pytest.TempPathFactory) -> sqlite3.Connection:
    corpus = Path(__file__).parents[1] / "data" / "corpus"
    if not corpus.exists():
        pytest.skip("generated corpus is missing")
    db = tmp_path_factory.mktemp("kb") / "kb.sqlite"
    conn, _, _, _ = build_db(db)
    return conn


def test_schema_and_base_counts(kb: sqlite3.Connection) -> None:
    assert kb.execute("select count(*) from regulation").fetchone()[0] == 56
    assert kb.execute("select count(*) from node").fetchone()[0] == 25209
    assert kb.execute("select count(*) from pragma_table_info('attribute')").fetchone()[0] == 4
    assert (
        kb.execute(
            "select count(*) from sqlite_master where type='table' and name in "
            "('fts_node','fts_obligation','fts_alias')"
        ).fetchone()[0]
        == 3
    )


def test_exact_quote_and_page_break(kb: sqlite3.Connection) -> None:
    row = kb.execute(
        "select n.text,o.char_start,o.char_end,o.quote_raw,o.page_start,o.page_end "
        "from obligation o join node n on n.id=o.node_id "
        "where json_array_length(n.page_breaks_json)>0 and o.page_end>o.page_start limit 1"
    ).fetchone()
    assert row is not None
    assert row[2] > row[1]
    assert row[3] == row[0][row[1] : row[2]]
    assert row[5] > row[4]


def test_real_enumeration_table_and_telegraphic_spans(kb: sqlite3.Connection) -> None:
    kinds = {r[0] for r in kb.execute("select distinct source_kind from obligation")}
    assert {"enumeration_item", "table_row", "telegraphic"} <= kinds
    row = kb.execute(
        "select quote_raw from obligation where node_id like 'UN R148|%' "
        "and source_kind='enumeration_item' limit 1"
    ).fetchone()
    assert row is not None and row[0].startswith("(a)")


def test_dev_gold_citations_and_coverage(kb: sqlite3.Connection) -> None:
    expected = json.loads(
        (Path(__file__).parents[2] / "cases" / "dev-rear-lamp" / "expected.json").read_text()
    )
    for requirement in expected["requirements"]:
        source = requirement["source"]
        label = source["paragraph"].split(". Table", 1)[0]
        assert kb.execute(
            "select 1 from node where regulation=? and label=?", (source["regulation"], label)
        ).fetchone()
    supported, causes, _ = build_db.__globals__["_coverage"](kb)
    assert supported >= 181
    assert sum(causes.values()) == 190 - supported


def test_two_builds_have_identical_content_hashes(tmp_path: Path) -> None:
    if not (Path(__file__).parents[1] / "data" / "corpus").exists():
        pytest.skip("generated corpus is missing")
    first, _, _, _ = build_db(tmp_path / "one.sqlite")
    second, _, _, _ = build_db(tmp_path / "two.sqlite")

    def digest(conn: sqlite3.Connection) -> str:
        rows = []
        for table in (
            "regulation",
            "node",
            "obligation",
            "obligation_value",
            "obligation_ref",
            "entity",
            "alias",
            "edge",
            "manifest",
            "provenance",
        ):
            cols = [r[1] for r in conn.execute(f"pragma table_info({table})")]
            for row in conn.execute(f"select * from {table} order by {', '.join(cols)}"):
                rows.append((table, tuple(row)))
        return hashlib.sha256(repr(rows).encode()).hexdigest()

    assert digest(first) == digest(second)


def test_reference_graph_cycle_is_safe() -> None:
    corpus = load_all("base")
    graph = build_graph({"UN R148": corpus["UN R148"]}, {"UN R148"})
    node_ids = list(graph.paragraphs)[:2]
    graph.refs_out[node_ids[0]].add(node_ids[1])
    graph.refs_out[node_ids[1]].add(node_ids[0])
    assert graph.expand_refs([node_ids[0]], hops=4)[node_ids[0]] == 0
