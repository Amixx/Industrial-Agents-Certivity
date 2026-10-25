"""Seed vocabulary: trade and colloquial names mapped to the entities the regulations define."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from functools import cache
from pathlib import Path

from ..paths import DATA

ALIASES = DATA / "aliases.json"


@cache
def _stemmer() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("CREATE VIRTUAL TABLE t USING fts5(x, tokenize='porter')")
    conn.execute("CREATE VIRTUAL TABLE v USING fts5vocab(t, 'instance')")
    return conn


@cache
def stem(text: str) -> str:
    """Lowercased Porter stems of `text`, tokenised exactly as the FTS5 tables tokenise it."""
    conn = _stemmer()
    conn.execute("DELETE FROM t")
    conn.execute("INSERT INTO t VALUES (?)", (text,))
    return " ".join(term for (term,) in conn.execute("SELECT term FROM v ORDER BY offset"))


def load(conn: sqlite3.Connection, path: Path = ALIASES) -> int:
    """Stem every alias, add the seed aliases and rebuild `fts_alias`; returns the seed count."""
    raw = path.read_text()
    seeds: dict[str, list[str]] = json.loads(raw)
    known = {eid for (eid,) in conn.execute("SELECT id FROM entity")}
    for text, entity_ids in seeds.items():
        unknown = sorted(set(entity_ids) - known)
        if unknown:
            raise ValueError(f"{path.name}: {text!r} maps to unknown entities {unknown}")
    for entity_id, text in conn.execute("SELECT entity_id, text FROM alias").fetchall():
        conn.execute(
            "UPDATE alias SET norm=? WHERE entity_id=? AND text=?", (stem(text), entity_id, text)
        )
    added = 0
    for text in sorted(seeds):
        for entity_id in sorted(set(seeds[text])):
            added += conn.execute(
                "INSERT OR IGNORE INTO alias VALUES (?,?,?,?)",
                (entity_id, text, stem(text), "seed"),
            ).rowcount
    conn.execute("DELETE FROM fts_alias")
    conn.execute(
        "INSERT INTO fts_alias SELECT entity_id, text, norm FROM alias ORDER BY entity_id, text"
    )
    conn.execute(
        "INSERT OR REPLACE INTO manifest VALUES ('aliases_hash', ?)",
        (hashlib.sha256(raw.encode()).hexdigest(),),
    )
    return added
