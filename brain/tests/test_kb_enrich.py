"""Checks for the enrichment pass, against a fake model and against answer files."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from brain import llm
from brain.kb import build, enrich

REG = "UN R150"
P = "UN R150|1.2.1|"


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not (Path(__file__).parents[1] / "data" / "corpus").exists():
        pytest.skip("generated corpus is missing")
    db = tmp_path_factory.mktemp("kb") / "kb.sqlite"
    conn, _, _, _ = build.build_db(db)
    conn.close()
    return db


@pytest.fixture
def conn(built: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> sqlite3.Connection:
    overrides = tmp_path / "overrides.jsonl"
    overrides.write_text("")
    monkeypatch.setattr(build, "OVERRIDES", overrides)
    return _copy(built, tmp_path / "kb.sqlite")


def _copy(src: Path, dst: Path) -> sqlite3.Connection:
    source = sqlite3.connect(src)
    target = sqlite3.connect(dst)
    source.backup(target)
    source.close()
    target.close()
    return enrich.connect(dst)


def _tag(quote: str, **changes: Any) -> dict[str, Any]:
    tag = {
        "subject": None,
        "kind": "requirement",
        "level": "device",
        "categories": [],
        "response": None,
        "exception": None,
        "ears": quote,
        "values": None,
        "conditions": [],
        "derived": [],
    }
    return tag | changes


def _negated(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        "SELECT o.id FROM obligation o JOIN node n ON n.id=o.node_id WHERE n.regulation=? "
        "AND o.quote_raw LIKE '% shall not %' ORDER BY n.ord, o.ord LIMIT 1",
        (REG,),
    ).fetchone()
    return str(row[0])


def _answers(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """One answer per R150 batch, with the special cases the tests look at."""
    negated = _negated(conn)
    special: dict[str, dict[str, Any]] = {
        f"{P}5.1.1#0": {
            "subject": "n1",
            "derived": [
                {
                    "derivation": "clause",
                    "text": "When tested according to paragraph 5.1.7., every retro-reflector "
                    "of the Classes IA and IB shall meet the dimensions and shape requirements.",
                    "variant": [],
                },
                {
                    "derivation": "clause",
                    "text": "When tested according to paragraph 5.1.7., every retro-reflector "
                    "of the Classes IA and IB shall meet paragraphs 5.1.4. to 5.1.5.",
                    "variant": [],
                },
            ],
        },
        f"{P}5.1.4.4.1#1": {
            "kind": "limit",
            "conditions": [{"attribute": "device_class", "op": "in", "value": "IA,IB"}],
            "derived": [
                {
                    "derivation": "variant",
                    "text": "Class IA and IB retro-reflectors of Red colour shall meet Table 3.",
                    "variant": [
                        {"attribute": "colour", "value": "red"},
                        {"attribute": "device_class", "value": "IA"},
                    ],
                },
                {
                    "derivation": "variant",
                    "text": "Purple retro-reflectors shall meet Table 3.",
                    "variant": [{"attribute": "colour", "value": "purple"}],
                },
            ],
        },
        f"{P}5.1.4.3#1": {"ears": "The manufacturer shall specify the perimeter within 5 mm."},
        f"{P}5.1.4.3#0": {"subject": "e999"},
    }
    quote = conn.execute("SELECT quote_raw FROM obligation WHERE id=?", (negated,)).fetchone()[0]
    special[negated] = {"ears": quote.replace(" shall not ", " shall ", 1)}
    out = {}
    for b in enrich.batches(conn, REG):
        tags = []
        for i, oid in enumerate(b.obligations):
            item = {"id": f"o{i + 1}"} | _tag(b.quotes[oid], **special.get(oid, {}))
            tags.append(item)
        answer: dict[str, Any] = {
            "new_entities": [],
            "obligations": tags,
            "tested_by": [],
            "installs": [],
            "aliases": [],
            "relations": [],
        }
        if f"{P}5.1.1#0" in b.obligations:
            pos = f"o{b.obligations.index(f'{P}5.1.1#0') + 1}"
            answer["new_entities"] = [
                {"ref": "n1", "name": "Retro-reflector of Class IA", "kind": "device"}
            ]
            answer["aliases"] = [{"entity": "n1", "text": "Class IA reflex reflector"}]
            answer["tested_by"] = [
                {"obligation": pos, "target": "Annex 4"},
                {"obligation": pos, "target": "Annex 99"},
            ]
        out[b.prompt_hash] = answer
    return out


def _fake(conn: sqlite3.Connection, calls: list[str]) -> Any:
    by_content = {b.content: b.prompt_hash for b in enrich.batches(conn, REG)}
    answers = _answers(conn)

    def complete_json(
        system: str, content: str, schema: dict[str, Any], **_: Any
    ) -> dict[str, Any]:
        assert system == enrich._SYSTEM and schema == enrich.SCHEMA
        calls.append(content)
        return answers[by_content[content]]

    return complete_json


def _row(conn: sqlite3.Connection, oid: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM obligation WHERE id=?", (oid,)).fetchone()
    assert row is not None
    return row


def _reasons(conn: sqlite3.Connection, target: str) -> list[str]:
    return [
        r[0] for r in conn.execute("SELECT reason FROM enrich_rejection WHERE target=?", (target,))
    ]


def test_writes_tags_derived_rows_and_rejections(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(llm, "complete_json", _fake(conn, calls))
    result = enrich.run(conn, [REG], "bulk", workers=2)
    assert len(calls) == len(enrich.batches(conn, REG))

    lead = _row(conn, f"{P}5.1.1#0")
    assert (
        lead["kind"] == "requirement"
        and lead["subject_entity_id"] == "UN R150:retro-reflector-of-class-ia"
    )
    assert lead["provenance_id"] is None
    field = conn.execute(
        "SELECT p.source, p.model, p.prompt_hash FROM field_provenance f "
        "JOIN provenance p ON p.id=f.provenance_id "
        "WHERE f.target_id=? AND f.field='kind'",
        (lead["id"],),
    ).fetchone()
    assert field[0] == "llm" and field[1] == llm.model_for("bulk") and field[2]

    clause = _row(conn, f"{P}5.1.1#0/1")
    assert clause["derivation"] == "clause" and clause["parent_obligation_id"] == lead["id"]
    assert (clause["char_start"], clause["char_end"], clause["page_start"]) == (
        lead["char_start"],
        lead["char_end"],
        lead["page_start"],
    )
    assert clause["quote_raw"] == lead["quote_raw"] and clause["sub"] == 1
    assert "dimensions and shape" in clause["text_norm"]
    assert (
        conn.execute("SELECT 1 FROM obligation WHERE id=?", (f"{P}5.1.1#0/2",)).fetchone() is None
    )
    assert any("adds numbers" in r for r in _reasons(conn, lead["id"]))

    variant = _row(conn, f"{P}5.1.4.4.1#1/1")
    assert variant["derivation"] == "variant" and json.loads(variant["variant_json"]) == {
        "colour": "red",
        "device_class": "IA",
    }
    assert variant["kind"] == "limit"
    assert [
        tuple(r)
        for r in conn.execute(
            "SELECT attribute, op, value FROM obligation_condition "
            "WHERE obligation_id=? ORDER BY attribute",
            (variant["id"],),
        )
    ] == [("colour", "eq", "red"), ("device_class", "eq", "IA")]
    assert any("unknown value purple" in r for r in _reasons(conn, f"{P}5.1.4.4.1#1"))

    for oid, reason in (
        (f"{P}5.1.4.3#1", "adds numbers"),
        (f"{P}5.1.4.3#0", "unknown entity e999"),
        (_negated(conn), "drops a negation"),
    ):
        assert any(reason in r for r in _reasons(conn, oid)), oid
        assert _row(conn, oid)["kind"] is None
    assert result.derived == 2

    assert conn.execute(
        "SELECT 1 FROM edge WHERE src=? AND dst=? AND type='tested_by'", (lead["id"], f"{P}Annex 4")
    ).fetchone()
    assert any("unknown target" in r for r in _reasons(conn, lead["id"]))
    alias = conn.execute("SELECT source FROM alias WHERE text='Class IA reflex reflector'")
    assert alias.fetchone()[0] == "llm"


def test_resume_skips_batches_with_the_same_prompt_hash(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(llm, "complete_json", _fake(conn, calls))
    first = enrich.run(conn, [REG], "bulk")
    n = len(calls)
    second = enrich.run(conn, [REG], "bulk")
    assert len(calls) == n and second.skipped == n and second.written == 0 and first.skipped == 0


def test_override_wins_over_enrichment(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    oid = f"{P}5.1.4.4.1#0"
    quote = _row(conn, oid)["quote_raw"]
    item = {
        "target_table": "obligation",
        "target_id": oid,
        "quote_hash": build._hash(quote),
        "field": "kind",
        "value": "marking",
        "author": "human",
        "note": "checked",
    }
    build._apply_overrides(conn, [item])
    derived_override = item | {
        "target_id": f"{P}5.1.1#0/1",
        "quote_hash": build._hash(_row(conn, f"{P}5.1.1#0")["quote_raw"]),
        "field": "ears_text",
        "value": "Fixed by hand.",
    }
    build.OVERRIDES.write_text(json.dumps(derived_override) + "\n")
    monkeypatch.setattr(llm, "complete_json", _fake(conn, []))
    enrich.run(conn, [REG], "bulk")
    row = _row(conn, oid)
    assert row["kind"] == "marking" and row["level"] == "device"
    assert _row(conn, f"{P}5.1.1#0/1")["ears_text"] == "Fixed by hand."


def test_estimate_calls_nothing(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def refuse(*_: Any, **__: Any) -> dict[str, Any]:
        raise AssertionError("estimate called the model")

    monkeypatch.setattr(llm, "complete_json", refuse)
    rows = enrich.estimate(conn, [REG, "UN R42"])
    n = len(enrich.batches(conn, REG))
    assert rows[0][:2] == (REG, n) and all(r[3] > 0 and r[4] > 0 for r in rows)
    total = conn.execute(
        "SELECT count(*) FROM obligation o JOIN node n ON n.id=o.node_id WHERE n.regulation=?",
        (REG,),
    ).fetchone()[0]
    assert rows[0][2] == total and all(
        len(b.obligations) <= enrich.BATCH for b in enrich.batches(conn, REG)
    )
    db = Path(conn.execute("PRAGMA database_list").fetchone()[2])
    assert enrich.main(["--db", str(db), "--estimate", "--regs", REG]) == 0
    assert f"{REG:<14}{n:>7}" in capsys.readouterr().out


TABLES = (
    "obligation",
    "obligation_value",
    "obligation_condition",
    "entity",
    "alias",
    "edge",
    "provenance",
    "field_provenance",
    "enrich_rejection",
    "attribute",
)


def _dump(conn: sqlite3.Connection) -> dict[str, list[tuple[Any, ...]]]:
    return {t: sorted(tuple(r) for r in conn.execute(f"SELECT * FROM {t}")) for t in TABLES}


@pytest.mark.parametrize("jsonl", [False, True])
def test_export_import_round_trip_matches_live(
    built: Path,
    conn: sqlite3.Connection,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    jsonl: bool,
) -> None:
    monkeypatch.setattr(llm, "complete_json", _fake(conn, []))
    enrich.run(conn, [REG], "bulk")
    live = _dump(conn)

    other = _copy(built, tmp_path / "imported.sqlite")
    out = tmp_path / "batches"
    assert enrich.export(other, [REG], out) == len(enrich.batches(other, REG))
    answers = _answers(other)
    files = sorted(out.glob("*.json"))
    exported = [json.loads(f.read_text()) for f in files]
    assert {"system", "content", "schema", "batch_id", "prompt_hash"} <= set(exported[0])
    filled = [e | {"answer": answers[e["prompt_hash"]]} for e in exported]
    if jsonl:
        source = tmp_path / "answers.jsonl"
        source.write_text("".join(json.dumps(f) + "\n" for f in filled))
    else:
        for f, payload in zip(files, filled, strict=True):
            f.write_text(json.dumps(payload))
        source = out
    db = Path(other.execute("PRAGMA database_list").fetchone()[2])
    other.close()
    argv = ["--db", str(db), "--import", str(source), "--source-model", llm.model_for("bulk")]
    assert enrich.main(argv) == 0
    assert _dump(enrich.connect(db)) == live


def test_import_rejects_stale_and_malformed_answers(
    conn: sqlite3.Connection, tmp_path: Path
) -> None:
    b = enrich.batches(conn, REG)[0]
    stale = {"batch_id": b.id, "prompt_hash": "0" * 64, "answer": {}}
    broken = {"batch_id": b.id, "prompt_hash": b.prompt_hash, "answer": {"obligations": "none"}}
    path = tmp_path / "answers.jsonl"
    path.write_text(json.dumps(stale) + "\n" + json.dumps(broken) + "\n")
    result = enrich.import_answers(conn, path, "manual")
    reasons = {reason for _, reason in result.rejected}
    assert "no batch with this prompt hash" in reasons and "malformed answer" in reasons
    assert result.written == 0
    prov = conn.execute("SELECT 1 FROM provenance WHERE prompt_hash=?", (b.prompt_hash,))
    assert prov.fetchone() is None
