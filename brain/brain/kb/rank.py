"""Regulations ranked against a product profile from the obligation base, and the scope card
(title, role, scope sentence, supersession) each ranking entry is explained with."""

from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass

from ..models import ProductProfile
from .ontology import stem
from .query import entities_for, scope

CATEGORY = re.compile(r"\b([LMNOTRS])(\d)?\b")
_CATEGORY_LIST = re.compile(r"\bcategor(?:y|ies)\s+(?:of\s+)?[LMNOT]\d?\b", re.I)
FIELDS = {"title": 3.0, "scope": 2.0, "headings": 1.0, "entities": 1.0}


@dataclass(frozen=True)
class ScopeCard:
    regulation: str
    title: str
    role: str
    scope: str
    superseded_by: tuple[str, ...]
    supersedes: tuple[str, ...]


def categories_ok(profile: ProductProfile, scope_text: str) -> bool:
    """False when the scope names vehicle categories and none of the product's is among them."""
    if not profile.vehicle_categories:
        return True
    found = CATEGORY.findall(scope_text[:600])
    if not found:
        return True
    for cat in profile.vehicle_categories:
        letter, digit = cat[0], cat[1:2]
        if any(f == letter and (not d or d == digit) for f, d in found):
            return True
    return False


def cards(conn: sqlite3.Connection) -> dict[str, ScopeCard]:
    edges: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"by": [], "of": []})
    for src, dst in conn.execute("SELECT src, dst FROM edge WHERE type='supersedes' ORDER BY 1, 2"):
        edges[dst]["by"].append(src)
        edges[src]["of"].append(dst)
    out = {}
    for reg, title, role in conn.execute("SELECT id, title, role_doc FROM regulation ORDER BY id"):
        if role is None:
            raise ValueError(f"{reg} has no role_doc; rebuild the obligation base")
        best = scope(conn, reg)
        out[reg] = ScopeCard(
            reg,
            title,
            role,
            best[0]["clean_text"] if best else "",
            tuple(edges[reg]["by"]),
            tuple(edges[reg]["of"]),
        )
    return out


def terms(profile: ProductProfile) -> list[str]:
    raw = [*profile.keywords, *profile.parts, *profile.functions]
    return [t for t in dict.fromkeys(x.casefold().strip() for x in raw) if len(t) > 3 or t == "esa"]


def hit(phrase: str, field: str) -> float:
    if f" {phrase} " in field:
        return 1.0
    words = set(phrase.split())
    return 0.5 if len(words) >= 2 and words <= set(field.split()) else 0.0


def documents(conn: sqlite3.Connection) -> dict[str, dict[str, str]]:
    """Stemmed title, best scope candidate, top-level headings and entity names per regulation."""
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
    spec_terms = terms(profile)
    hits = [h for h in entities_for(conn, spec_terms) if h["via"] != "head"]
    expansions: dict[str, dict[str, float]] = {t: {stem(t): 1.0} for t in spec_terms}
    owned: dict[str, dict[str, float]] = defaultdict(dict)
    for h in hits:
        name = stem(h["name"])
        weight = 0.8 * h["score"]
        if expansions[h["term"]].get(name, 0) < weight:
            expansions[h["term"]][name] = weight
        reg_hits = owned[h["term"]]
        reg_hits[h["regulation"]] = max(reg_hits.get(h["regulation"], 0), h["score"])
    scores = {}
    for reg, doc in docs.items():
        total = 0.0
        for term in spec_terms:
            best = (
                max(
                    weight * sum(w * hit(phrase, doc[f]) for f, w in FIELDS.items())
                    for phrase, weight in expansions[term].items()
                    if phrase
                )
                if any(expansions[term])
                else 0.0
            )
            total += best + 1.5 * owned[term].get(reg, 0.0)
        if _CATEGORY_LIST.search(doc["scope_raw"]) and not categories_ok(profile, doc["scope_raw"]):
            total *= 0.05
        scores[reg] = total
    for src, dst in conn.execute("SELECT src, dst FROM edge WHERE type='supersedes' ORDER BY 1, 2"):
        if scores.get(src, 0) > 0 and dst in scores:
            scores[dst] *= 0.1
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
