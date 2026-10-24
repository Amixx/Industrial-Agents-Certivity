"""Checks for the knowledge-base queries, the alias vocabulary and the scope candidates."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from brain.kb import ontology, query
from brain.kb.build import build_db
from brain.kb.scope import clean_text

SCHEMA = Path(__file__).parents[1] / "brain" / "kb" / "schema.sql"


@pytest.fixture(scope="module")
def kb(tmp_path_factory: pytest.TempPathFactory) -> sqlite3.Connection:
    if not (Path(__file__).parents[1] / "data" / "corpus").exists():
        pytest.skip("generated corpus is missing")
    conn, _, _, _ = build_db(tmp_path_factory.mktemp("kb") / "kb.sqlite")
    return conn


@pytest.fixture
def graph() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA.read_text())
    edges = [("a", "b"), ("b", "a"), ("b", "c"), ("c", "a"), ("c", "d"), ("x", "y")]
    conn.executemany("INSERT INTO edge VALUES (?,?,'refers_to',NULL)", edges)
    return conn


def test_ref_closure_terminates_on_cycles_and_bounds_hops(graph: sqlite3.Connection) -> None:
    assert query.ref_closure(graph, ["a", "a", "b"], max_hops=10) == {
        "a": 0,
        "b": 0,
        "c": 1,
        "d": 2,
    }
    assert query.ref_closure(graph, ["a"], max_hops=1) == {"a": 0, "b": 1}
    assert query.ref_closure(graph, ["x"], max_hops=5) == {"x": 0, "y": 1}


def test_loop_partners_are_the_strongly_connected_component(graph: sqlite3.Connection) -> None:
    assert query.loop_partners(graph, "a") == ["b", "c"]
    assert query.loop_partners(graph, "d") == []
    assert query.loop_partners(graph, "x") == []


def test_stems_meet_across_word_forms() -> None:
    assert ontology.stem("retro-reflecting") == ontology.stem("Retro-reflective") == "retro reflect"


def test_unknown_alias_entity_fails(graph: sqlite3.Connection, tmp_path: Path) -> None:
    path = tmp_path / "aliases.json"
    path.write_text(json.dumps({"tail light": ["UN R48:no-such-entity"]}))
    with pytest.raises(ValueError, match="no-such-entity"):
        ontology.load(graph, path)


def test_entities_for_aliases_and_stems(kb: sqlite3.Connection) -> None:
    found = {r["entity_id"] for r in query.entities_for(kb, ["retro-reflecting"])}
    assert {"UN R48:retro-reflective-device", "UN R3:retro-reflection"} <= found
    brake = {(r["entity_id"], r["via"]) for r in query.entities_for(kb, ["brake light"])}
    assert {("UN R48:stop-lamp", "exact"), ("UN R7:stop-lamp", "exact")} <= brake
    seeded = kb.execute("SELECT count(*) FROM alias WHERE source='seed'").fetchone()[0]
    assert seeded > 50
    assert (
        kb.execute("SELECT count(*) FROM fts_alias").fetchone()[0]
        == kb.execute("SELECT count(*) FROM alias").fetchone()[0]
    )


def test_scope_is_a_real_scope_statement(kb: sqlite3.Connection) -> None:
    r148 = query.scope(kb, "UN R148")[0]
    assert r148["best"] == 1
    assert r148["clean_text"].startswith(
        "This Regulation applies to the following light-signalling"
    )
    assert "Stop lamps" in r148["clean_text"]
    gtr9 = query.scope(kb, "UN GTR 9")[0]
    assert gtr9["rule"] == "gtr_part_b_scope"
    assert "shall apply to the frontal surfaces" in gtr9["clean_text"]
    r48 = query.scope(kb, "UN R48")[0]["clean_text"]
    assert r48.endswith("installation of lighting and light-signalling devices.")
    leaks = kb.execute(
        "SELECT count(*) FROM scope_candidate WHERE clean_text LIKE '%www.%' "
        "OR clean_text LIKE '%http%' OR clean_text LIKE '%Consolidated Resolution%'"
    ).fetchone()[0]
    assert leaks == 0
    roles = dict(kb.execute("SELECT id, role_doc FROM regulation"))
    assert roles["UN R48"] == "installation"
    assert roles["UN R148"] == "device_approval"
    assert roles["UN R10"] == "emc"
    assert roles["UN R42"] == "vehicle_approval"


def test_clean_text_strips_footnotes_per_node() -> None:
    raw = (
        "Scope This Regulation applies to vehicles of category M1 1/ with regard to x. "
        "1/ As defined in Annex 7 to the Consolidated Resolution (R.E.3).\n"
        "Components 2 As defined in R.E.3 -www.unece.org/trans/main.html"
    )
    assert (
        clean_text(raw)
        == "This Regulation applies to vehicles of category M1 with regard to x. Components"
    )


def test_tree_queries(kb: sqlite3.Connection) -> None:
    node = "UN R48|9.3.0|6.2.2"
    assert [a["label"] for a in query.ancestors(kb, node)] == ["6", "6.2"]
    assert query.heading_path(kb, node)[:2] == [
        "6 Individual specifications",
        "6.2 Dipped-beam headlamp",
    ]
    labels = [r["label"] for r in query.subtree(kb, "UN R48|9.3.0|6.2")]
    assert labels[0] == "6.2" and "6.2.2" in labels and all(x.startswith("6.2") for x in labels)
    top = query.toc(kb, "UN R148", 0)
    assert all(r["depth"] == 0 for r in top) and top[0]["label"] == "preamble"
    assert all(o["node_id"] == node for o in query.obligations(kb, [node]))
    assert query.superseded_by(kb, "UN R7") == ["UN R148"]
    assert query.search(kb, "retro-reflecting devices")[0]["regulation"] in {"UN R150", "UN R3"}


def test_real_reference_loop(kb: sqlite3.Connection) -> None:
    node = "UN GTR 9|0.3.0|5.2.1"
    assert "UN GTR 9|0.3.0|7.3" in query.loop_partners(kb, node)
    closure = query.ref_closure(kb, [node], max_hops=1)
    assert closure[node] == 0 and closure["UN GTR 9|0.3.0|7.3"] == 1
