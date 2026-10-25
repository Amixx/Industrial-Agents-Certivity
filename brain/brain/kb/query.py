"""Read queries over the knowledge base. Every result is ordered deterministically."""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterable
from typing import Any

from .ontology import stem

Row = dict[str, Any]


def _rows(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[Row]:
    cur = conn.execute(sql, tuple(params))
    names = [d[0] for d in cur.description]
    return [dict(zip(names, row, strict=True)) for row in cur.fetchall()]


def _ids(nodes: Iterable[str]) -> str:
    return json.dumps(list(dict.fromkeys(nodes)))


def toc(conn: sqlite3.Connection, reg: str, depth: int = 0) -> list[Row]:
    """Nodes of `reg` down to `depth` (0 is the top level), in document order."""
    return _rows(
        conn,
        "SELECT id, kind, label, heading, depth, page FROM node "
        "WHERE regulation=? AND depth<=? ORDER BY ord",
        (reg, depth),
    )


def subtree(conn: sqlite3.Connection, node: str) -> list[Row]:
    """The node and all its descendants, in document order."""
    return _rows(
        conn,
        "WITH RECURSIVE sub(id) AS ("
        "SELECT ? UNION SELECT n.id FROM node n JOIN sub ON n.parent_id=sub.id) "
        "SELECT n.id, n.kind, n.label, n.heading, n.depth, n.page FROM node n JOIN sub USING (id) "
        "ORDER BY n.ord",
        (node,),
    )


def ancestors(conn: sqlite3.Connection, node: str) -> list[Row]:
    """Ancestors of the node from the top level down, without the node itself."""
    rows = _rows(
        conn,
        "WITH RECURSIVE up(id, n) AS ("
        "SELECT parent_id, 1 FROM node WHERE id=? AND parent_id IS NOT NULL "
        "UNION SELECT n.parent_id, up.n + 1 FROM node n JOIN up ON n.id=up.id "
        "WHERE n.parent_id IS NOT NULL) "
        "SELECT n.id, n.kind, n.label, n.heading, n.depth, n.page FROM node n JOIN up USING (id) "
        "ORDER BY up.n DESC",
        (node,),
    )
    return rows


def heading_path(conn: sqlite3.Connection, node: str) -> list[str]:
    """ "label heading" for each ancestor and the node itself, top level first."""
    rows = ancestors(conn, node) + _rows(
        conn, "SELECT label, heading FROM node WHERE id=?", (node,)
    )
    return [f"{r['label']} {r['heading']}" if r["heading"] else r["label"] for r in rows]


def obligations(conn: sqlite3.Connection, nodes: Iterable[str]) -> list[Row]:
    """Obligations of the given nodes, in document order."""
    return _rows(
        conn,
        "SELECT o.* FROM obligation o JOIN node n ON n.id=o.node_id "
        "WHERE o.node_id IN (SELECT value FROM json_each(?)) ORDER BY n.regulation, n.ord, o.ord",
        (_ids(nodes),),
    )


def ref_closure(
    conn: sqlite3.Connection, nodes: Iterable[str], max_hops: int = 2
) -> dict[str, int]:
    """Nodes reachable over `refers_to` within `max_hops`, with the fewest hops to each."""
    rows = conn.execute(
        "WITH RECURSIVE walk(id, hops) AS ("
        "SELECT value, 0 FROM json_each(?) "
        "UNION SELECT e.dst, walk.hops + 1 FROM walk "
        "JOIN edge e ON e.src=walk.id AND e.type='refers_to' WHERE walk.hops < ?) "
        "SELECT id, min(hops) FROM walk GROUP BY id ORDER BY min(hops), id",
        (_ids(nodes), max_hops),
    ).fetchall()
    return {node: hops for node, hops in rows}


def _reachable(conn: sqlite3.Connection, node: str, forward: bool) -> set[str]:
    src, dst = ("src", "dst") if forward else ("dst", "src")
    rows = conn.execute(
        f"WITH RECURSIVE walk(id) AS (SELECT ? UNION SELECT e.{dst} FROM walk "
        f"JOIN edge e ON e.{src}=walk.id AND e.type='refers_to') SELECT id FROM walk",
        (node,),
    ).fetchall()
    return {r[0] for r in rows}


def loop_partners(conn: sqlite3.Connection, node: str) -> list[str]:
    """Other nodes in the node's reference loop (its strongly connected component)."""
    component = _reachable(conn, node, True) & _reachable(conn, node, False)
    return sorted(component - {node})


def _match(text: str) -> str:
    words = re.findall(r"\w+", text.casefold())
    return " ".join(f'"{w}"' for w in words)


def search(conn: sqlite3.Connection, text: str, limit: int = 20) -> list[Row]:
    """Nodes whose text or heading contains every word of `text` (Porter-stemmed), best first."""
    query = _match(text)
    if not query:
        return []
    return _rows(
        conn,
        "SELECT f.id, n.regulation, n.label, n.heading, bm25(fts_node) AS score "
        "FROM fts_node f JOIN node n ON n.id=f.id WHERE fts_node MATCH ? "
        "ORDER BY score, f.id LIMIT ?",
        (query, limit),
    )


def _contains(haystack: list[str], needle: list[str]) -> bool:
    n = len(needle)
    return any(haystack[i : i + n] == needle for i in range(len(haystack) - n + 1))


def entities_for(conn: sqlite3.Connection, terms: Iterable[str]) -> list[Row]:
    """Entities whose aliases match the terms, best match per (term, entity).

    `via` is `exact` when the stems are equal, `head` when a one-word alias is the last word of
    the term, `contains` when one multi-word stem sequence contains the other and `fts` for a
    stemmed phrase hit in `fts_alias`.
    """
    aliases = conn.execute(
        "SELECT a.entity_id, a.text, a.norm, e.name, e.regulation FROM alias a "
        "JOIN entity e ON e.id=a.entity_id ORDER BY a.entity_id, a.text"
    ).fetchall()
    weight = {"exact": 1.0, "head": 0.8, "contains": 0.7, "fts": 0.6}
    best: dict[tuple[str, str], Row] = {}

    def keep(term: str, entity: str, name: str, reg: str, alias: str, via: str) -> None:
        old = best.get((term, entity))
        if old is None or weight[via] > old["score"]:
            best[(term, entity)] = {
                "term": term,
                "entity_id": entity,
                "name": name,
                "regulation": reg,
                "alias": alias,
                "via": via,
                "score": weight[via],
            }

    for term in dict.fromkeys(terms):
        stems = stem(term).split()
        if not stems:
            continue
        for entity, alias, norm, name, reg in aliases:
            alias_stems = norm.split()
            if alias_stems == stems:
                keep(term, entity, name, reg, alias, "exact")
            elif len(alias_stems) == 1 and len(stems) > 1 and stems[-1] == alias_stems[0]:
                keep(term, entity, name, reg, alias, "head")
            elif min(len(alias_stems), len(stems)) > 1 and (
                _contains(stems, alias_stems) or _contains(alias_stems, stems)
            ):
                keep(term, entity, name, reg, alias, "contains")
        if len(stems) > 1:
            for entity, alias, name, reg in conn.execute(
                "SELECT f.entity_id, f.text, e.name, e.regulation FROM fts_alias f "
                "JOIN entity e ON e.id=f.entity_id WHERE fts_alias MATCH ? ORDER BY f.entity_id",
                (f'text:"{" ".join(re.findall(r"\w+", term))}"',),
            ):
                keep(term, entity, name, reg, alias, "fts")
    return sorted(best.values(), key=lambda r: (r["term"], -r["score"], r["entity_id"]))


def superseded_by(conn: sqlite3.Connection, reg: str) -> list[str]:
    """Consolidated regulations that combine the provisions of `reg`."""
    return [
        r[0]
        for r in conn.execute(
            "SELECT src FROM edge WHERE dst=? AND type='supersedes' ORDER BY src", (reg,)
        )
    ]


def scope(conn: sqlite3.Connection, reg: str) -> list[Row]:
    """Scope candidates of `reg`, the default (`best`) first, then by confidence."""
    return _rows(
        conn,
        "SELECT node_id, rule, confidence, clean_text, raw_text, best FROM scope_candidate "
        "WHERE regulation=? ORDER BY best DESC, confidence DESC, node_id",
        (reg,),
    )
