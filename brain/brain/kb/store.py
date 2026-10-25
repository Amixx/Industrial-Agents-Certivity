"""The obligation base as the pipeline reads it: built on first use, with the committed
enrichment answers imported (one folder per answering model under `data/kb_answers/`)."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from ..paths import DATA
from .build import DB, build_db
from .enrich import import_answers

ANSWERS = DATA / "kb_answers"
_lock = threading.Lock()
_conns: dict[Path, sqlite3.Connection] = {}


def build(db: Path = DB) -> None:
    conn, *_ = build_db(db)
    for folder in sorted(p for p in ANSWERS.glob("*") if p.is_dir()):
        import_answers(conn, folder, folder.name)
    conn.close()


def connect(db: Path = DB) -> sqlite3.Connection:
    """A shared read-only connection, safe to use from the pipeline's worker threads."""
    with _lock:
        if db not in _conns:
            if not db.exists():
                build(db)
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _conns[db] = conn
        return _conns[db]
