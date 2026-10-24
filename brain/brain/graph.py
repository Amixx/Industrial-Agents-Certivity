"""Regulation graph built from the parsed text with regexes, no LLM.

Nodes are paragraphs (by id). Edges:
  * parent / child, from the numbering;
  * refers-to, from "paragraph 4.6.", "paragraphs 6.4.8., 6.7.8. and 6.9.8.", "paragraph 1.1. of
    Annex 4", "Annex 3", "Annex 4, Part 1";
  * regulation links, from "UN Regulation No. 148" (counted per regulation);
  * definitions, from '"Stop lamp" means ...' paragraphs: term -> paragraph id.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from .models import Paragraph

PARA_REF = re.compile(
    r"\b(?:paragraphs?|para\.)\s+(\d+(?:\.\d+)*\.?(?:\s*(?:,|and|or|to|-|–)\s*\d+(?:\.\d+)*\.?)*)",
    re.IGNORECASE,
)
NUMBER = re.compile(r"\d+(?:\.\d+)*")
OF_ANNEX = re.compile(r"^\s*(?:of|in|to)\s+(?:this\s+)?Annex\s+(\d+[A-Z]?)", re.IGNORECASE)
EXTERNAL = re.compile(
    r"^[\s,]*(?:of|in|to)\s+(?:the\s+)?(?:\d+\s+series\s+of\s+amendments\s+to\s+)?"
    r"(?:UN\s+)?Regulation\s+No",
    re.IGNORECASE,
)
ANNEX_REF = re.compile(r"\bAnnex\s+(\d+[A-Z]?)\b(?:\s*,?\s*Part\s+(\d+|[A-H])\b)?")
ANNEX_EXTERNAL = re.compile(r"^\s*(?:to|of)\s+(?:the\s+)?(?:UN\s+)?Regulation\s+No", re.I)
REG_LINK = re.compile(r"\b(?:UN\s+)?Regulations?\s+Nos?\.\s?(\d{1,3})\b")
DEFINITION = re.compile(r"^[\"“']([^\"”']{2,80})[\"”']\s*(?:\([^)]*\)\s*)?(?:means|is|are)\b")


@dataclass
class Graph:
    paragraphs: dict[str, Paragraph]
    children: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    refs_out: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    refs_in: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    reg_links: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    definitions: dict[str, list[tuple[str, str]]] = field(default_factory=lambda: defaultdict(list))

    def descendants(self, pid: str) -> list[str]:
        out, stack = [], list(reversed(self.children.get(pid, [])))
        while stack:
            node = stack.pop()
            out.append(node)
            stack.extend(reversed(self.children.get(node, [])))
        return out

    def subtree(self, pid: str) -> list[str]:
        return [pid, *self.descendants(pid)]

    def expand_refs(self, seeds: Iterable[str], hops: int = 1) -> dict[str, int]:
        """Paragraphs reachable from `seeds` over refers-to edges (including the referenced
        paragraph's subtree), with the hop count at which each was reached."""
        dist = {s: 0 for s in seeds}
        frontier = list(dist)
        for hop in range(1, hops + 1):
            nxt = []
            for node in frontier:
                for target in self.refs_out.get(node, ()):
                    for t in self.subtree(target):
                        if t not in dist:
                            dist[t] = hop
                            nxt.append(t)
            frontier = nxt
        return dist


def _label_index(paragraphs: list[Paragraph]) -> dict[tuple[str | None, str], str]:
    """(annex prefix or None, local number) -> paragraph id; the first occurrence wins."""
    index: dict[tuple[str | None, str], str] = {}
    for p in paragraphs:
        key = (p.annex, p.number) if p.number else (p.label, "")
        index.setdefault(key, p.id)
    return index


def _annex_base(annex: str | None) -> str | None:
    return " ".join(annex.split()[:2]) if annex else None


def _para_targets(
    p: Paragraph,
    index: dict[tuple[str | None, str], str],
    order: dict[str, int],
    ordered: list[str],
) -> set[str]:
    out: set[str] = set()
    for m in PARA_REF.finditer(p.text):
        tail = p.text[m.end() : m.end() + 80]
        if EXTERNAL.match(tail):
            continue
        annex_m = OF_ANNEX.match(tail)
        scopes: list[str | None]
        if annex_m:
            scopes = [f"Annex {annex_m[1]}"]
        elif p.annex:
            scopes = [p.annex, _annex_base(p.annex), None]
        else:
            scopes = [None]
        group = m.group(1)
        numbers = [n.rstrip(".") for n in NUMBER.findall(group)]
        found = []
        for n in numbers:
            for scope in scopes:
                if (scope, n) in index:
                    found.append(index[(scope, n)])
                    break
        out.update(found)
        if re.search(r"\bto\b|[-–]", group) and len(found) >= 2:  # a range: everything between
            lo, hi = sorted((order[found[0]], order[found[-1]]))
            if hi - lo < 200:
                out.update(ordered[lo : hi + 1])
    for m in ANNEX_REF.finditer(p.text):
        if ANNEX_EXTERNAL.match(p.text[m.end() : m.end() + 60]):
            continue
        label = f"Annex {m[1]}" + (f" Part {m[2]}" if m[2] else "")
        target = index.get((label, "")) or index.get((f"Annex {m[1]}", ""))
        if target:
            out.add(target)
    out.discard(p.id)
    return out


def build(corpus: dict[str, list[Paragraph]], known: set[str] | None = None) -> Graph:
    """Graph over the given regulations (regulation -> paragraphs of one version)."""
    g = Graph({p.id: p for ps in corpus.values() for p in ps})
    for regulation, paragraphs in corpus.items():
        index = _label_index(paragraphs)
        ordered = [p.id for p in paragraphs]
        order = {pid: i for i, pid in enumerate(ordered)}
        for p in paragraphs:
            if p.parent:
                g.children[p.parent].append(p.id)
            for target in _para_targets(p, index, order, ordered):
                g.refs_out[p.id].add(target)
                g.refs_in[target].add(p.id)
            for m in REG_LINK.finditer(p.text):
                other = f"UN R{m[1]}"
                if other != regulation and (known is None or other in known):
                    g.reg_links[regulation][other] += 1
            if d := DEFINITION.match(p.text):
                g.definitions[d[1].strip().lower()].append((regulation, p.id))
    return g
