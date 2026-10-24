"""Paragraph -> feature vector for the decision model ("does this paragraph carry a requirement
the product must fulfil?"). Features are deliberately generic (no lamp-specific words) so a model
fitted on the rear lamp transfers to a bumper:

  * function match: a product term appears in the paragraph's heading path or text;
  * other device: the heading path names a device the regulation defines but the product lacks;
  * section kind: definitions, administrative, marking, test procedure, annex;
  * content: modal verbs, numbers with units, length, depth;
  * graph: referenced from function-matched paragraphs, in-degree;
  * regulation probability from the regulation selector.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field

import numpy as np

from .graph import Graph
from .ingest import sources
from .models import Paragraph, ProductProfile

FEATURES = [
    "reg_prob",
    "func_path",
    "func_text",
    "func_own",
    "other_path",
    "other_text",
    "neutral",
    "is_definition",
    "is_admin",
    "is_marking",
    "is_test",
    "in_annex",
    "has_shall",
    "n_modal",
    "has_may_only",
    "has_units",
    "log_len",
    "depth",
    "heading_only",
    "n_children",
    "ref_from_func",
    "log_refs_in",
    "under_func_annex",
    "rule",
]

ADMIN = re.compile(
    r"application for|communication|approval number|notice of approval|transitional|penalt|"
    r"discontinued|names and addresses|modification|extension of approval|information document|"
    r"conformity of production|sampling|inspector|administrative|instructions|scope|"
    r"purpose|introduction|specimen|test report|technical service",
    re.I,
)
MARKING = re.compile(r"marking|marks?\b|unique identifier|trade name", re.I)
TEST = re.compile(r"\btest|measure|method|procedure|apparatus|conditions", re.I)
DEFINITION = re.compile(r"^[\"“']([^\"”']{2,80})[\"”']\s*(?:\([^)]*\)\s*)?(?:means|is|are)\b")
UNITS = re.compile(
    r"\d\s*(?:mm|cm|m|cd|lx|°|º|%|per cent|V|A|W|MHz|kHz|Hz|s|ms|min|h|kg|N|"
    r"km/h|K|nm|mcd)\b"
)
MODAL = re.compile(r"\b(shall|must)\b", re.I)
MAY = re.compile(r"\bmay\b", re.I)


def norm(text: str) -> str:
    text = text.lower().replace("‑", "-").replace("–", "-").replace("-", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    words = [
        w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
        for w in text.split()
    ]
    return " " + " ".join(words) + " "


@dataclass
class Context:
    """Everything per (product, regulation set) that the features need."""

    graph: Graph
    product_terms: dict[str, list[str]]  # regulation -> normalised phrases, " stop lamp "
    device_terms: dict[str, list[str]]  # regulation -> normalised defined terms the product lacks
    reg_prob: dict[str, float]
    func_ids: set[str]  # paragraphs whose own heading path matches the product
    ref_from_func: set[str]
    func_annexes: set[tuple[str, str]]  # (regulation, "Annex 3") referenced by func paragraphs
    other_sections: set[str] = field(default_factory=set)  # siblings of a section that matched
    about: set[str] = field(default_factory=set)  # regulations whose title names the product


def _path_text(p: Paragraph, g: Graph) -> str:
    titles = []
    for pid in [*p.path, p.id]:
        q = g.paragraphs.get(pid)
        if q is None:
            continue
        titles.append(q.heading or (q.text if len(q.text) < 120 else q.text[:60]))
    return norm(" | ".join(titles))


def _hits(text: str, terms: list[str]) -> int:
    return sum(text.count(t) for t in terms)


def product_terms(profile: ProductProfile) -> list[str]:
    raw = [*profile.keywords, *profile.parts, *profile.functions]
    terms = [norm(t) for t in raw if len(t) > 3]
    # A bare generic word ("lamp", "device") would match everything.
    return [t for t in dict.fromkeys(terms) if len(t.split()) >= 2 or len(t.strip()) > 6]


def head_words(profile: ProductProfile) -> list[str]:
    """Single nouns that name the product or a part: "bumper", "lamp", "reflector"."""
    words = []
    for t in [profile.product, *profile.parts]:
        tokens = norm(re.sub(r"\([^)]*\)", "", t)).split()
        if tokens and len(tokens[-1]) >= 4:
            words.append(f" {tokens[-1]} ")
    return list(dict.fromkeys(words))


def regulation_terms(
    profile: ProductProfile, paths: list[str], defined: Iterable[str] = ()
) -> list[str]:
    """Product phrases, plus head words that are discriminative in this regulation: present in
    under a quarter of its heading paths ("bumper" in R127 yes, "lamp" in R48 no). A part's head
    word is dropped where the regulation uses it as a modifier inside a defined term ("beam" of
    "Bumper beam" in R48's "dipped beam headlamp"); the product's own head word is kept."""
    terms = product_terms(profile)
    modifiers = " ".join(" " + " ".join(d.split()[:-1]) + " " for d in defined)
    own = head_words(profile.model_copy(update={"parts": []}))
    for w in head_words(profile):
        if w in terms or (w not in own and w in modifiers):
            continue
        if paths and sum(w in p for p in paths) / len(paths) < 0.25:
            terms.append(w)
    return terms


def build_context(
    profile: ProductProfile,
    corpus: dict[str, list[Paragraph]],
    graph: Graph,
    reg_prob: dict[str, float],
) -> Context:
    terms: dict[str, list[str]] = {}
    device_terms: dict[str, list[str]] = {}
    func_ids: set[str] = set()
    titles = {s.regulation: norm(s.title) for s in sources()}
    about: set[str] = set()
    # Device regulations often leave their terms to the installation regulation (R149 uses
    # R48's "dipped-beam headlamp"), so modifiers are looked up across all selected ones.
    all_defined = {
        norm(m[1]) for ps in corpus.values() for p in ps if (m := DEFINITION.match(p.text))
    }
    for reg, ps in corpus.items():
        paths = {p.id: _path_text(p, graph) for p in ps}
        defined = {norm(m[1]) for p in ps if (m := DEFINITION.match(p.text))}
        terms[reg] = regulation_terms(profile, list(paths.values()), all_defined)
        if _names(titles.get(reg, ""), product_terms(profile)):
            about.add(reg)
            func_ids.update(paths)
        device_terms[reg] = [
            d
            for d in defined
            if len(d.split()) >= 2 and not any(t in d or d in t for t in terms[reg])
        ]
        func_ids.update(pid for pid, path in paths.items() if _hits(path, terms[reg]))
    ref_from_func: set[str] = set()
    func_annexes: set[tuple[str, str]] = set()
    other = other_sections(corpus, graph, terms)
    for pid in func_ids:
        for target in graph.refs_out.get(pid, ()):
            for t in graph.subtree(target):
                ref_from_func.add(t)
            q = graph.paragraphs[target]
            if q.annex:
                func_annexes.add((q.regulation, " ".join(q.annex.split()[:2])))
    return Context(
        graph, terms, device_terms, reg_prob, func_ids, ref_from_func, func_annexes, other, about
    )


def _names(title: str, phrases: list[str]) -> bool:
    """The title names a product phrase, also with words in between: "front and rear protective
    devices" names "front protective device"."""
    words = set(title.split())
    return any(len(ph.split()) >= 2 and (ph in title or set(ph.split()) <= words) for ph in phrases)


def _title(p: Paragraph) -> str | None:
    if p.heading:
        return p.heading
    return p.text if len(p.text) < 90 and not MODAL.search(p.text) else None


def other_sections(
    corpus: dict[str, list[Paragraph]], graph: Graph, terms: dict[str, list[str]]
) -> set[str]:
    """Sections about something else: when one titled sibling names a product term ("6.3 Front
    fog lamp", "6.5 Bumpers"), its titled siblings that name none ("6.2 Dipped-beam headlamp",
    "6.17 Aerials") and their subtrees. Works where the regulation defines no device terms.
    Only the sections directly under a top-level section of the main body, where regulations
    list devices; deeper siblings are often steps of one procedure (R127 Annex 5 1.4 to 1.12)."""
    out: set[str] = set()
    for reg, ps in corpus.items():
        for p in ps:
            if p.annex or not p.number or "." in p.number:
                continue
            kids = [graph.paragraphs[c] for c in graph.children.get(p.id, [])]
            titled = [(k, t) for k in kids if (t := _title(k))]
            if len(titled) < 3:
                continue
            hit = [_hits(norm(t), terms[reg]) > 0 for _, t in titled]
            if any(hit):
                for (k, _), h in zip(titled, hit, strict=True):
                    if not h:
                        out.update(graph.subtree(k.id))
    return out


def vector(p: Paragraph, ctx: Context) -> list[float]:
    g = ctx.graph
    path = _path_text(p, g)
    text = norm(p.text[:3000])
    own = norm(p.heading or p.text[:120])
    devices = ctx.device_terms.get(p.regulation, [])
    terms = ctx.product_terms.get(p.regulation, [])
    func_path = _hits(path, terms) + (p.regulation in ctx.about)
    other_path = _hits(path, devices) + (p.id in ctx.other_sections)
    n_modal = len(MODAL.findall(p.text))
    annex_base = " ".join(p.annex.split()[:2]) if p.annex else ""
    is_definition = bool(DEFINITION.match(p.text)) or "definition" in path
    is_admin = bool(ADMIN.search(path)) or p.label.startswith("Rationale")
    is_marking = bool(MARKING.search(path))
    under_func_annex = (p.regulation, annex_base) in ctx.func_annexes
    content = n_modal > 0 or bool(UNITS.search(p.text)) or bool(MAY.search(p.text))
    # The transparent baseline: content, not a definition, not about another device, not
    # administrative (markings excepted), and annexes only when a matching section points there.
    rule = (
        content
        and not is_definition
        and not (other_path > 0 and func_path == 0)
        and (not is_admin or is_marking)
        and (p.annex is None or under_func_annex)
    )
    return [
        ctx.reg_prob.get(p.regulation, 0.0),
        float(func_path > 0),
        float(_hits(text, terms) > 0),
        float(_hits(own, terms) > 0),
        float(other_path > 0 and func_path == 0),
        min(_hits(text, devices), 5) / 5,
        float(func_path == 0 and other_path == 0),
        float(is_definition),
        float(is_admin),
        float(is_marking),
        float(bool(TEST.search(path))),
        float(p.annex is not None),
        float(n_modal > 0),
        min(n_modal, 6) / 6,
        float(n_modal == 0 and bool(MAY.search(p.text))),
        float(bool(UNITS.search(p.text))),
        math.log1p(len(p.text)) / 8,
        len(p.path) / 6,
        float(len(p.text) < 100 and n_modal == 0),
        min(len(g.children.get(p.id, [])), 10) / 10,
        float(p.id in ctx.ref_from_func),
        math.log1p(len(g.refs_in.get(p.id, ()))) / 3,
        float(under_func_annex),
        float(rule),
    ]


def matrix(paragraphs: list[Paragraph], ctx: Context) -> np.ndarray:
    return np.array([vector(p, ctx) for p in paragraphs], dtype=float)
