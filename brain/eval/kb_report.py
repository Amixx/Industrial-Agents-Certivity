"""Measure the knowledge base against the gold cases: spans, granularity, sections, scope and
the regulation ranking from spec terms.

uv run python -m eval.kb_report [--db data/kb.sqlite]   (build it first: python -m brain.kb.build)
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from brain.kb.build import DB
from brain.kb.ontology import stem
from brain.kb.query import entities_for, scope
from brain.models import ProductProfile
from brain.paths import CASES, DATA, ROOT
from brain.profile import parse_spec
from brain.select_regs import _categories_ok

from .judge import similarity
from .score import paragraph_key

THRESHOLD = 0.45
TOP = 12
SCOPE_REGS = (
    "UN R48",
    "UN R148",
    "UN R150",
    "UN R10",
    "UN R42",
    "UN R127",
    "UN GTR 9",
    "UN R26",
    "UN R149",
)
_CATEGORY_LIST = re.compile(r"\bcategor(?:y|ies)\s+(?:of\s+)?[LMNOT]\d?\b", re.I)
FIELDS = {"title": 3.0, "scope": 2.0, "headings": 1.0, "entities": 1.0}


def cases() -> list[Path]:
    return [CASES / "dev-rear-lamp", *sorted((ROOT / "synthetic" / "cases").glob("*/"))]


@dataclass
class Match:
    requirement: dict
    node: str | None
    obligation: dict | None
    score: float

    @property
    def covered(self) -> bool:
        return self.obligation is not None and self.score >= THRESHOLD

    @property
    def right_page(self) -> bool:
        return (
            self.obligation is not None
            and self.covered
            and self.obligation["page_start"] == self.requirement["source"]["page"]
        )


def _nodes(conn: sqlite3.Connection) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for node, reg, label in conn.execute("SELECT id, regulation, label FROM node ORDER BY ord"):
        out.setdefault((reg, paragraph_key(label)), node)
    return out


def _obligations(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    cur = conn.execute(
        "SELECT id, node_id, ord, page_start, quote_raw, det_text, source_kind, n_modal "
        "FROM obligation ORDER BY node_id, ord"
    )
    names = [d[0] for d in cur.description]
    out: dict[str, list[dict]] = defaultdict(list)
    for row in cur:
        item = dict(zip(names, row, strict=True))
        out[item["node_id"]].append(item)
    return out


def match(requirements: list[dict], nodes: dict, obligations: dict) -> list[Match]:
    out = []
    for req in requirements:
        source = req["source"]
        node = nodes.get((source["regulation"], paragraph_key(source.get("paragraph", ""))))
        best, best_score = None, -1.0
        for ob in obligations.get(node or "", []):
            score = max(
                similarity(req["text"], ob["quote_raw"]),
                similarity(req["text"], ob["det_text"] or ""),
            )
            if score > best_score:
                best, best_score = ob, score
        out.append(Match(req, node, best, max(best_score, 0.0)))
    return out


def coverage(matches: list[Match], obligations: dict) -> None:
    loose = sum(
        1
        for m in matches
        if m.node
        and any(o["page_start"] == m.requirement["source"]["page"] for o in obligations[m.node])
    )
    covered = [m for m in matches if m.covered]
    shared = Counter(m.obligation["id"] for m in covered if m.obligation)
    n = len(matches)
    print(f"  span coverage, some obligation on the gold page: {loose}/{n}")
    print(
        f"  span coverage, best obligation at similarity >= {THRESHOLD}: {len(covered)}/{n}, "
        f"right page {sum(m.right_page for m in matches)}/{n}, "
        f"unresolved citations {sum(m.node is None for m in matches)}"
    )
    print(
        f"  obligations that are the best match of 2+ gold requirements: "
        f"{sum(1 for c in shared.values() if c > 1)}"
    )


def granularity(matches: list[Match], obligations: dict) -> None:
    per_node = Counter(m.node for m in matches if m.node)
    pairs = [(len(obligations.get(node, [])), gold) for node, gold in per_node.items()]
    if not pairs:
        return
    print(
        f"  gold paragraphs {len(pairs)}: "
        f"obligations per paragraph {mean(p[0] for p in pairs):.2f}, "
        f"gold requirements per paragraph {mean(p[1] for p in pairs):.2f}; "
        f"equal {sum(a == b for a, b in pairs)}, more obligations {sum(a > b for a, b in pairs)}, "
        f"fewer {sum(a < b for a, b in pairs)}"
    )
    covered = [m for m in matches if m.covered and m.obligation]
    shared = Counter(m.obligation["id"] for m in covered if m.obligation)
    two = [m for m in covered if m.obligation and m.obligation["n_modal"] >= 2]
    split = sum(1 for m in two if m.obligation and shared[m.obligation["id"]] > 1)
    print(
        f"  two-modal obligations matched by gold: {len(two)}; gold keeps the sentence whole "
        f"{len(two) - split}, splits it {split}"
    )
    kinds = Counter(m.obligation["source_kind"] for m in covered if m.obligation)
    listed = sum(1 for m in matches if re.search(r"(?:^|\s)\([a-z]\)\s", m.requirement["text"]))
    print(
        "  covered gold by obligation kind: "
        + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
        + f"; gold texts that keep an enumeration together {listed}"
    )


def _section(node: str, level: int, parent: dict, depth: dict) -> str:
    while depth[node] > level - 1 and parent[node]:
        node = parent[node]
    return node


def sections(conn: sqlite3.Connection, matches: list[Match]) -> None:
    gold_nodes: dict[str, set[str]] = defaultdict(set)
    for m in matches:
        if m.node:
            gold_nodes[m.requirement["source"]["regulation"]].add(m.node)
    print("  | Regulation | Nodes | Gold paragraphs | Kept at depth 1 | depth 2 | depth 3 |")
    print("  |---|---|---|---|---|---|")
    for reg in sorted(gold_nodes):
        rows = conn.execute(
            "SELECT id, parent_id, depth FROM node WHERE regulation=? ORDER BY ord", (reg,)
        ).fetchall()
        parent = {r[0]: r[1] for r in rows}
        depth = {r[0]: r[2] for r in rows}

        shares = []
        for level in (1, 2, 3):
            keep = {_section(n, level, parent, depth) for n in gold_nodes[reg]}
            kept = sum(_section(r[0], level, parent, depth) in keep for r in rows)
            shares.append(kept / len(rows))
        print(
            f"  | {reg} | {len(rows)} | {len(gold_nodes[reg])} | "
            + " | ".join(f"{s:.0%}" for s in shares)
            + " |"
        )


def scope_table(conn: sqlite3.Connection) -> None:
    print("| Regulation | role_doc | Rule | Confidence | Best scope candidate |")
    print("|---|---|---|---|---|")
    for reg in SCOPE_REGS:
        role = conn.execute("SELECT role_doc FROM regulation WHERE id=?", (reg,)).fetchone()[0]
        best = scope(conn, reg)
        text = best[0]["clean_text"] if best else ""
        cut = text if len(text) <= 160 else text[:157] + "..."
        rule = f"{best[0]['rule']} | {best[0]['confidence']:.2f}" if best else "none | 0"
        print(f"| {reg} | {role} | {rule} | {cut} |")


def _terms(profile: ProductProfile) -> list[str]:
    raw = [*profile.keywords, *profile.parts, *profile.functions]
    return [t for t in dict.fromkeys(x.casefold().strip() for x in raw) if len(t) > 3 or t == "esa"]


def _hit(phrase: str, field: str) -> float:
    if f" {phrase} " in field:
        return 1.0
    words = set(phrase.split())
    return 0.5 if len(words) >= 2 and words <= set(field.split()) else 0.0


def documents(conn: sqlite3.Connection) -> dict[str, dict[str, str]]:
    docs: dict[str, dict[str, str]] = {}
    for reg, title in conn.execute("SELECT id, title FROM regulation ORDER BY id"):
        best = scope(conn, reg)
        headings = [
            h
            for (h,) in conn.execute(
                "SELECT heading FROM node WHERE regulation=? AND depth=0 AND heading IS NOT NULL "
                "ORDER BY ord",
                (reg,),
            )
        ]
        names = [
            n
            for (n,) in conn.execute(
                "SELECT name FROM entity WHERE regulation=? ORDER BY id", (reg,)
            )
        ]
        docs[reg] = {
            "title": f" {stem(title)} ",
            "scope": f" {stem(best[0]['clean_text']) if best else ''} ",
            "headings": " " + " | ".join(stem(h) for h in headings) + " ",
            "entities": " " + " | ".join(stem(n) for n in names) + " ",
            "scope_raw": best[0]["clean_text"] if best else "",
        }
    return docs


def rank(conn: sqlite3.Connection, profile: ProductProfile, docs: dict) -> list[tuple[str, float]]:
    """Regulations by how well the spec terms, expanded through the entity aliases, match each
    regulation's title, best scope candidate, top-level headings and defined entity names.

    One-word head matches are left out: "optical unit" would otherwise pull in every regulation
    that defines "units". The vehicle-category check applies only where the scope names
    categories in the M/N/L/O/T scheme, which GTRs do not use."""
    terms = _terms(profile)
    hits = [h for h in entities_for(conn, terms) if h["via"] != "head"]
    expansions: dict[str, dict[str, float]] = {t: {stem(t): 1.0} for t in terms}
    owned: dict[str, dict[str, float]] = defaultdict(dict)
    for hit in hits:
        name = stem(hit["name"])
        weight = 0.8 * hit["score"]
        if expansions[hit["term"]].get(name, 0) < weight:
            expansions[hit["term"]][name] = weight
        reg_hits = owned[hit["term"]]
        reg_hits[hit["regulation"]] = max(reg_hits.get(hit["regulation"], 0), hit["score"])
    scores = {}
    for reg, doc in docs.items():
        total = 0.0
        for term in terms:
            best = (
                max(
                    weight * sum(w * _hit(phrase, doc[f]) for f, w in FIELDS.items())
                    for phrase, weight in expansions[term].items()
                    if phrase
                )
                if any(expansions[term])
                else 0.0
            )
            total += best + 1.5 * owned[term].get(reg, 0.0)
        if _CATEGORY_LIST.search(doc["scope_raw"]) and not _categories_ok(
            profile, doc["scope_raw"]
        ):
            total *= 0.05
        scores[reg] = total
    for src, dst in conn.execute("SELECT src, dst FROM edge WHERE type='supersedes' ORDER BY 1, 2"):
        if scores.get(src, 0) > 0 and dst in scores:
            scores[dst] *= 0.1
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def ranking(conn: sqlite3.Connection, spec: Path, docs: dict, gold: set[str]) -> list[str]:
    ranked = rank(conn, parse_spec(spec.read_text()), docs)
    position = {reg: i + 1 for i, (reg, _) in enumerate(ranked)}
    top = ", ".join(f"{reg} {score:.1f}" for reg, score in ranked[:TOP])
    print(f"  top {TOP}: {top}")
    if gold:
        print("  gold ranks: " + ", ".join(f"{g} {position.get(g, '-')}" for g in sorted(gold)))
    return [g for g in sorted(gold) if position.get(g, TOP + 1) > TOP]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args(argv)
    if not args.db.exists():
        raise SystemExit(f"{args.db} is missing; run python -m brain.kb.build")
    conn = sqlite3.connect(args.db)
    nodes, obligations, docs = _nodes(conn), _obligations(conn), documents(conn)
    print("## Scope and role\n")
    scope_table(conn)
    misses: dict[str, list[str]] = {}
    for case in cases():
        expected = json.loads((case / "expected.json").read_text())["requirements"]
        print(f"\n## {case.name} ({len(expected)} gold requirements)\n")
        matches = match(expected, nodes, obligations)
        coverage(matches, obligations)
        granularity(matches, obligations)
        sections(conn, matches)
        gold = {r["source"]["regulation"] for r in expected}
        misses[case.name] = ranking(conn, case / "spec.md", docs, gold)
    for spec in sorted((DATA / "synthetic").glob("bumper-*/spec.md")):
        print(f"\n## {spec.parent.name} (no gold)\n")
        ranking(conn, spec, docs, set())
    print("\n## Ranking target\n")
    failed = {case: regs for case, regs in misses.items() if regs}
    if failed:
        for name, regs in failed.items():
            print(f"  {name}: outside the top {TOP}: {', '.join(regs)}")
    else:
        print(f"  every gold regulation of every case is within the top {TOP}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
