"""Build the deterministic SQLite knowledge base from the ingested base corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from pathlib import Path

from ..graph import build as build_graph
from ..ingest import load_all, sources
from ..models import Paragraph
from ..obligations import modality
from ..paths import CASES, CORPUS, DATA
from ..rewrite import deterministic
from . import ontology, scope, spans

HERE = Path(__file__).parent
DB = DATA / "kb.sqlite"
OVERRIDES = DATA / "kb_overrides.jsonl"
PROV = "parser:deterministic"
_DEFINITION = re.compile(
    r"^[\"“']([^\"”']{2,100})[\"”']\s*(?:\([^)]*\)\s*)?(?:means|is|are)\b", re.I
)
_REG = re.compile(r"\b(?:UN\s+)?Regulations?\s+Nos?\.\s*(\d{1,3})\b", re.I)
_COMBINES = re.compile(r"combines the provisions of[^.]*?Nos?\.\s*([\d,\sand]+)", re.I)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def _role(title: str, reg: str) -> str:
    text = f"{reg} {title}".casefold()
    if "electromagnetic" in text:
        return "emc"
    if "installation" in text:
        return "installation"
    if "gtr" in text:
        return "gtr"
    if "vehicle" in text and "lamp" not in text:
        return "vehicle_approval"
    if any(x in text for x in ("light", "lamp", "reflect")):
        return "light_source" if "source" in text else "device_approval"
    return "device_approval"


def _parts(p: Paragraph) -> tuple[str | None, str | None, str | None, int]:
    if not p.annex:
        return None, None, None, len(p.path)
    bits = p.annex.split()
    annex = " ".join(bits[:2]) if len(bits) >= 2 and bits[0] == "Annex" else p.annex
    part = None
    appendix = None
    if "Part" in bits:
        i = bits.index("Part")
        part = " ".join(bits[i : i + 2])
    if "Appendix" in bits:
        i = bits.index("Appendix")
        appendix = " ".join(bits[i : i + 2])
    return annex, part, appendix, len(p.path)


def _clean_scope(text: str) -> str:
    return re.sub(r"\s*(?:\d+/|\(\d+\)|https?://\S+|www\.\S+).*$", "", text).strip()


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _load_overrides() -> list[dict[str, str]]:
    if not OVERRIDES.exists():
        OVERRIDES.write_text("")
    return [json.loads(line) for line in OVERRIDES.read_text().splitlines() if line.strip()]


def _apply_overrides(
    conn: sqlite3.Connection, overrides: list[dict[str, str]]
) -> tuple[int, list[str]]:
    applied = 0
    warnings = []
    rank = {"rule": 0, "llm": 1, "human": 2}
    for item in sorted(
        overrides,
        key=lambda x: (x.get("target_table", ""), x.get("target_id", ""), x.get("field", "")),
    ):
        table, target, field = item["target_table"], item["target_id"], item["field"]
        row = (
            conn.execute(f"SELECT * FROM {table} WHERE id = ?", (target,)).fetchone()
            if table in {"node", "obligation"}
            else None
        )
        if row is None:
            warnings.append(f"missing target {table}:{target}")
            continue
        if table == "obligation":
            quote = conn.execute(
                "SELECT quote_raw FROM obligation WHERE id=?", (target,)
            ).fetchone()[0]
            if _hash(quote) != item.get("quote_hash"):
                warnings.append(f"quote changed {target}")
                continue
        if field not in row.keys():
            warnings.append(f"unknown field {table}.{field}")
            continue
        existing = conn.execute(
            "SELECT source FROM provenance WHERE id=?", (f"override:{target}:{field}",)
        ).fetchone()
        if existing and rank.get(existing[0], 0) > rank.get(item.get("author", "rule"), 0):
            continue
        conn.execute(f"UPDATE {table} SET {field}=? WHERE id=?", (item["value"], target))
        conn.execute(
            "INSERT OR REPLACE INTO provenance VALUES (?,?,?,?,?)",
            (
                f"override:{target}:{field}",
                item.get("author", "human"),
                None,
                None,
                item.get("note", ""),
            ),
        )
        applied += 1
    return applied, warnings


def _coverage(conn: sqlite3.Connection) -> tuple[int, dict[str, int], list[str]]:
    expected_path = CASES / "dev-rear-lamp" / "expected.json"
    if not expected_path.exists():
        return 0, {}, []
    expected = json.loads(expected_path.read_text())["requirements"]
    supported = 0
    causes: dict[str, int] = {}
    examples: list[str] = []
    for req in expected:
        source = req["source"]
        label = re.sub(r"\.\s*table.*$", "", source["paragraph"], flags=re.I).strip()
        row = conn.execute(
            "SELECT id FROM node WHERE regulation=? AND label=?", (source["regulation"], label)
        ).fetchone()
        if row is None:
            key = "citation_unresolved"
        else:
            n = conn.execute(
                "SELECT count(*) FROM obligation WHERE node_id=? AND page_start=?",
                (row[0], source["page"]),
            ).fetchone()[0]
            key = "supported" if n else "no_modal_or_constraint_span"
        if key == "supported":
            supported += 1
        else:
            causes[key] = causes.get(key, 0) + 1
            if len([x for x in examples if x.startswith(key + ":")]) < 2:
                examples.append(f"{key}: {source['regulation']} {source['paragraph']}")
    return supported, causes, examples


def build_db(
    db: Path = DB,
) -> tuple[sqlite3.Connection, float, dict[str, int], tuple[int, dict[str, int], list[str]]]:
    import time

    started = time.monotonic()
    corpus = load_all("base")
    if len(corpus) < 56:
        raise RuntimeError(f"expected 56 base regulations, found {len(corpus)}; run brain.ingest")
    graph = build_graph(corpus, set(corpus))
    titles = {s.regulation: s.title for s in sources() if s.role == "base"}
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.executescript((HERE / "schema.sql").read_text())
    prov_note = "deterministic parser, graph and rewrite rules"
    conn.execute(
        "INSERT INTO provenance VALUES (?,?,?,?,?)",
        (PROV, "parser", "deterministic", None, prov_note),
    )
    for reg in sorted(corpus):
        ps = corpus[reg]
        version = ps[0].version
        conn.execute(
            "INSERT INTO regulation VALUES (?,?,?,?,?,?)",
            (
                reg,
                reg.removeprefix("UN "),
                version,
                titles.get(reg, reg),
                _role(titles.get(reg, ""), reg),
                PROV,
            ),
        )
        for order, p in enumerate(ps):
            annex, part, appendix, depth = _parts(p)
            kind = "paragraph"
            if p.number == "":
                kind = (
                    "annex" if annex and not part and not appendix else "part" if part else "annex"
                )
            conn.execute(
                "INSERT INTO node VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    p.id,
                    reg,
                    p.version,
                    kind,
                    p.label,
                    p.number,
                    annex,
                    part,
                    appendix,
                    p.parent,
                    depth,
                    order,
                    p.page,
                    p.page_end,
                    p.heading,
                    p.text,
                    json.dumps(p.page_breaks, separators=(",", ":")),
                ),
            )
            conn.execute("INSERT INTO fts_node VALUES (?,?,?)", (p.id, p.text, p.heading or ""))
            if p.number in {"1", "1.1"} or (
                p.heading and re.search(r"scope|purpose", p.heading, re.I)
            ):
                conn.execute(
                    "INSERT INTO scope_candidate VALUES (?,?,?,?,?,?,?,?)",
                    (
                        _hash(f"scope:{p.id}"),
                        reg,
                        p.id,
                        "heading_or_intro",
                        0.5,
                        p.text,
                        _clean_scope(p.text),
                        0,
                    ),
                )
    for reg in sorted(corpus):
        ps = corpus[reg]
        for p in ps:
            for order, span in enumerate(spans.extract(p)):
                raw = p.text[span.start : span.end]
                norm = spans.normalized(raw, p.heading)
                ctype, ctext = spans.condition(raw)
                mod = modality(raw)
                oid = f"{p.id}#{order}"
                det = next(
                    (d.text for d in deterministic(p, graph) if d.quote.strip() == raw.strip()), raw
                )
                n_modal = len(re.findall(r"\b(?:shall|must|may)\b", raw, re.I))
                conn.execute(
                    "INSERT INTO obligation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        oid,
                        p.id,
                        order,
                        span.source_kind,
                        span.start,
                        span.end,
                        p.page_at(span.start),
                        p.page_at(span.end),
                        raw,
                        norm,
                        mod,
                        n_modal,
                        ctype,
                        ctext,
                        None,
                        None,
                        None,
                        det,
                        None,
                        None,
                        None,
                        None,
                        None,
                    ),
                )
                conn.execute("INSERT INTO fts_obligation VALUES (?,?,?)", (oid, norm, det))
                for value_order, (
                    quantity,
                    minimum,
                    maximum,
                    unit,
                    tolerance,
                    value_raw,
                ) in enumerate(spans.values(raw)):
                    conn.execute(
                        "INSERT INTO obligation_value VALUES (?,?,?,?,?,?,?,?)",
                        (oid, value_order, quantity, minimum, maximum, unit, tolerance, value_raw),
                    )
                for target in sorted(graph.refs_out.get(p.id, ())):
                    target_p = graph.paragraphs[target]
                    conn.execute(
                        "INSERT OR IGNORE INTO obligation_ref VALUES (?,?,?,?)",
                        (oid, target, None, target_p.label),
                    )
            definition = _DEFINITION.match(p.text)
            if definition:
                name = definition[1].strip()
                eid = f"{reg}:{_slug(name)}"
                conn.execute(
                    "INSERT OR IGNORE INTO entity VALUES (?,?,?,?,?)",
                    (eid, name, "definition", reg, p.id),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO alias VALUES (?,?,?,?)",
                    (eid, name, name.casefold(), "definition"),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO fts_alias VALUES (?,?,?)", (eid, name, name.casefold())
                )
                conn.execute(
                    "INSERT OR IGNORE INTO edge VALUES (?,?,?,?)", (p.id, eid, "defines", PROV)
                )
        for src, targets in graph.refs_out.items():
            for dst in sorted(targets):
                conn.execute(
                    "INSERT OR IGNORE INTO edge VALUES (?,?,?,?)", (src, dst, "refers_to", PROV)
                )
        for p in ps:
            for match in _REG.finditer(p.text):
                target = f"UN R{match[1]}"
                if target in corpus and target != reg:
                    conn.execute(
                        "INSERT OR IGNORE INTO edge VALUES (?,?,?,?)",
                        (p.id, target, "cites_regulation", PROV),
                    )
        preamble = next((p.text for p in ps if p.label == "preamble"), "")
        for match in _COMBINES.finditer(preamble):
            for num in re.findall(r"\d+", match[1]):
                target = f"UN R{num}"
                if target in corpus:
                    conn.execute(
                        "INSERT OR IGNORE INTO edge VALUES (?,?,?,?)",
                        (reg, target, "supersedes", PROV),
                    )
    manifest = {
        "schema_hash": _hash((HERE / "schema.sql").read_text()),
        "git_commit": _git_commit(),
        "aliases_hash": _hash(""),
        "corpus_regulations": str(len(corpus)),
    }
    for path in sorted(CORPUS.glob("*_base.jsonl")):
        manifest[f"corpus:{path.name}"] = _hash(path.read_text())
    for key, value in sorted(manifest.items()):
        conn.execute("INSERT INTO manifest VALUES (?,?)", (key, value))
    ontology.load(conn)
    scope.load(conn)
    overrides = _load_overrides()
    applied, warnings = _apply_overrides(conn, overrides)
    if warnings:
        print(f"override warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  {warning}")
    conn.commit()
    counts = {
        name: conn.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        for name in (
            "regulation",
            "node",
            "scope_candidate",
            "obligation",
            "obligation_value",
            "obligation_ref",
            "entity",
            "alias",
            "edge",
            "attribute",
            "obligation_condition",
            "provenance",
            "manifest",
            "override",
        )
    }
    counts["overrides_applied"] = applied
    return conn, time.monotonic() - started, counts, _coverage(conn)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args(argv)
    conn, elapsed, counts, coverage = build_db(args.db)
    for name, count in counts.items():
        print(f"{name}: {count}")
    supported, causes, examples = coverage
    total = supported + sum(causes.values())
    print(f"dev gold span coverage: {supported}/{total} ({supported / total:.1%})")
    if causes:
        print("unsupported by cause:")
        for cause, count in sorted(causes.items()):
            print(f"  {cause}: {count}")
        for example in examples:
            print(f"  example {example}")
    print(f"runtime: {elapsed:.2f}s")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
