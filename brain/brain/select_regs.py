"""ProductProfile -> which regulations apply, with a probability and a rationale for each.

Deterministic scoring (always available), the sum of two rankings:
  * lexical: product terms found in the regulation's title, scope, section headings and
    definitions, vehicle-category compatibility with the scope, and the EMC regulation for a
    product with electronics;
  * obligation base: spec terms expanded through the entity aliases, matched against title,
    best scope candidate, headings and defined entities (`brain.kb.rank`).
A legacy regulation is never selected next to the consolidated regulation that supersedes it
(R148 over R7, R150 over R3). With an LLM configured, a model reviews every regulation from its
scope card (role, scope sentence, supersession) and decides.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field

from . import llm
from .ingest import sources
from .kb import store
from .kb.rank import ScopeCard, cards, rank
from .kb.rank import documents as kb_documents
from .models import Paragraph, ProductProfile, RegulationChoice
from .profile import ELECTRONICS

COMBINES = re.compile(r"combines the provisions of[^.]*?Nos?\.\s*([\d,\sand]+)", re.I)
CATEGORY = re.compile(r"\b([LMNOTRS])(\d)?\b")
EMC = re.compile(r"electromagnetic compatibility", re.I)
_STOP = frozenset("and or of the for with a an to in on".split())
VEHICLE = re.compile(
    r"(?:passenger|motor) car|(?:light )?(?:commercial |goods )?vehicle|"
    r"truck|bus|coach|trailer|motorcycle|moped|tractor"
)


@dataclass
class RegulationDoc:
    regulation: str
    version: str
    title: str
    scope: str
    headings: list[str]
    terms: list[str]
    body: str
    combines: list[str] = field(default_factory=list)


def _norm(text: str) -> str:
    text = text.lower().replace("‑", "-").replace("–", "-")
    text = re.sub(r"[^a-z0-9\- ]+", " ", text)
    words = [
        w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
        for w in text.split()
    ]
    return " " + " ".join(words) + " "


def documents(corpus: dict[str, list[Paragraph]]) -> dict[str, RegulationDoc]:
    titles = {s.regulation: s.title for s in sources()}
    out = {}
    for reg, ps in corpus.items():
        scope_ps = [p for p in ps if not p.annex and re.match(r"^\s*(scope|purpose)", p.text, re.I)]
        if scope_ps:
            start = ps.index(scope_ps[0])
            scope = " ".join(p.text for p in ps[start : start + 4])
        else:
            scope = " ".join(p.text for p in ps[:3])
        headings = [
            p.heading or p.text
            for p in ps
            if not p.annex
            and p.number
            and p.number.count(".") <= 1
            and (p.heading or len(p.text) < 80)
        ]
        terms = [m[1] for p in ps if (m := re.match(r"^[\"“']([^\"”']{2,80})[\"”']", p.text))]
        preamble = next((p.text for p in ps if p.label == "preamble"), "")
        combines = []
        if m := COMBINES.search(preamble):
            combines = [f"UN R{n}" for n in re.findall(r"\d+", m[1])]
        out[reg] = RegulationDoc(
            reg,
            ps[0].version if ps else "",
            titles.get(reg, ""),
            scope[:1500],
            headings,
            terms,
            " ".join(p.text for p in ps),
            combines,
        )
    return out


def _categories_ok(profile: ProductProfile, scope: str) -> bool:
    if not profile.vehicle_categories:
        return True
    found = CATEGORY.findall(scope[:600])
    if not found:
        return True
    for cat in profile.vehicle_categories:
        letter, digit = cat[0], cat[1:2]
        if any(f == letter and (not d or d == digit) for f, d in found):
            return True
    return False


def _product_term(phrase: str) -> bool:
    if VEHICLE.fullmatch(phrase):
        return False
    words = [w for w in phrase.split() if w not in _STOP]
    return not all(ELECTRONICS.fullmatch(w) for w in words)


def lexical_scores(profile: ProductProfile, docs: dict[str, RegulationDoc]) -> dict[str, float]:
    phrases = [_norm(k).strip() for k in profile.keywords + profile.parts + profile.functions]
    phrases = [p for p in dict.fromkeys(phrases) if len(p) > 3 and _product_term(p)]
    scores = {}
    for reg, d in docs.items():
        title, scope = _norm(d.title), _norm(d.scope)
        heads, terms, body = (
            _norm(" | ".join(d.headings)),
            _norm(" | ".join(d.terms)),
            _norm(d.body),
        )
        s = 0.0
        title_words, scope_words = set(title.split()), set(scope.split())
        for ph in phrases:
            key = f" {ph} "
            s += 3.0 * (key in title) + 2.0 * (key in scope) + 1.5 * (key in heads)
            s += 1.5 * (key in terms) + 0.3 * math.log1p(body.count(key))
            words = set(ph.split()) - _STOP
            if len(words) >= 2 and key not in title and words <= title_words:
                s += 2.0  # "front protective device" vs title "front and rear protective devices"
            elif len(words) >= 2 and key not in scope and words <= scope_words:
                s += 1.0
        if profile.electronics and EMC.search(d.title + " " + d.scope):
            s += 6.0
        if not _categories_ok(profile, d.scope):
            s *= 0.05
        scores[reg] = s
    for reg, d in docs.items():  # consolidated regulations replace the legacy ones they combine
        if scores.get(reg, 0) > 0:
            for legacy in d.combines:
                if legacy in scores:
                    scores[legacy] *= 0.1
    return scores


# With threshold 0.4 and scale 7.5 a regulation is selected from a summed score of about 3.8;
# on the labelled cases the lowest gold regulation sums to 4.6 and the highest decoy to 3.3.
KB_WEIGHT = 0.75
ROLES = {
    "installation": "Installation regulation",
    "device_approval": "Device approval",
    "vehicle_approval": "Vehicle approval",
    "emc": "Electromagnetic compatibility",
    "light_source": "Light sources",
    "gtr": "Global technical regulation",
}


def _clip(text: str, limit: int = 240) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _rationale(card: ScopeCard, lexical: float, base: float) -> str:
    parts = [f"{ROLES[card.role]}."]
    if card.scope:
        parts.append(f"Scope: {_clip(card.scope)}")
    if card.superseded_by:
        parts.append(f"Consolidated into {', '.join(card.superseded_by)}.")
    parts.append(f"Spec terms {lexical:.1f}, obligation base {base:.1f}.")
    return " ".join(parts)


def prefer_consolidated(
    choices: list[RegulationChoice], superseded_by: dict[str, tuple[str, ...]]
) -> list[RegulationChoice]:
    """Deselect every legacy regulation whose consolidated successor is also selected."""
    selected = {c.regulation for c in choices if c.selected}
    out = []
    for c in choices:
        newer = [r for r in superseded_by[c.regulation] if r in selected]
        if c.selected and newer:
            c = c.model_copy(
                update={
                    "selected": False,
                    "rationale": f"{c.rationale} Left out: {', '.join(newer)} is selected and "
                    "consolidates it.",
                }
            )
        out.append(c)
    return out


def choose(
    profile: ProductProfile,
    corpus: dict[str, list[Paragraph]],
    threshold: float = 0.4,
    scale: float = 7.5,
    use_llm: bool | None = None,
) -> list[RegulationChoice]:
    docs = documents(corpus)
    lexical = lexical_scores(profile, docs)
    conn = store.connect()
    base = dict(rank(conn, profile, kb_documents(conn)))
    scope_cards = cards(conn)
    scored = sorted(
        ((lexical[r] + KB_WEIGHT * base[r], r) for r in docs), key=lambda x: (-x[0], x[1])
    )
    choices = []
    for s, reg in scored:
        p = 1 - math.exp(-s / scale)
        choices.append(
            RegulationChoice(
                regulation=reg,
                version=docs[reg].version,
                probability=round(p, 3),
                selected=p >= threshold,
                rationale=_rationale(scope_cards[reg], lexical[reg], base[reg]),
            )
        )
    if use_llm is not False and (use_llm is not None or llm.available()):
        choices = _llm_review(profile, scope_cards, choices)
    return prefer_consolidated(choices, {r: c.superseded_by for r, c in scope_cards.items()})


_SYSTEM = """You are a type-approval engineer. Given a product and a list of UN Regulations
(title, role, scope and supersession), decide which regulations contain requirements the product
itself must fulfil.
Rules learned from expert answers:
- Cite the device regulation that approves the product, the installation regulation for the
  vehicle category when the product is installed on a vehicle, and the EMC regulation when the
  product contains electronics.
- Prefer the newer consolidated regulation over the legacy regulations it combines (e.g. R148
  over R6/R7/R23/R38, R149 over R19, R150 over R3/R104).
- Do not cite regulations about other systems of the vehicle, other vehicle categories, or
  test equipment only. Recall matters more than precision, but do not pad.
- Cite a light-source regulation (filament or LED light sources) only when the product is, or
  ships with, a replaceable light source of a category that regulation approves. Light sources
  built into the lamp are approved with the lamp under its device regulation."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "regulation": {"type": "string"},
                    "rationale": {
                        "type": "string",
                        "description": "one or two sentences, written before the decision",
                    },
                    "applies": {"type": "boolean"},
                    "p_applies": {
                        "type": "number",
                        "description": "probability (0-1) that the regulation applies",
                    },
                },
                "required": ["regulation", "rationale", "applies", "p_applies"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["decisions"],
    "additionalProperties": False,
}


def _card_text(card: ScopeCard) -> str:
    lines = [
        f"{card.regulation} - {card.title}",
        f"Role: {card.role}",
        f"Scope: {card.scope[:700]}",
    ]
    if card.supersedes:
        lines.append(f"Consolidates: {', '.join(card.supersedes)}")
    if card.superseded_by:
        lines.append(f"Consolidated into: {', '.join(card.superseded_by)}")
    return "\n".join(lines)


def _prompt(profile: ProductProfile, scope_cards: dict[str, ScopeCard]) -> str:
    listing = "\n\n".join(_card_text(c) for c in scope_cards.values())
    return (
        f"Product profile:\n{profile.model_dump_json(indent=1)}\n\n"
        f"Regulations:\n\n{listing}\n\nReturn one decision per regulation."
    )


def _ask(profile: ProductProfile, scope_cards: dict[str, ScopeCard]) -> dict[str, dict]:
    schema = json.loads(json.dumps(_SCHEMA))
    item = schema["properties"]["decisions"]["items"]
    item["properties"]["regulation"] = {"type": "string", "enum": sorted(scope_cards)}
    data = llm.complete_json(
        _SYSTEM, _prompt(profile, scope_cards), schema, tier="strong", effort="high"
    )
    # Models sometimes echo "UN R3 - Retro-reflecting devices"; key by the id prefix.
    return {d["regulation"].split(" - ")[0].strip(): d for d in data["decisions"]}


def _llm_review(
    profile: ProductProfile, scope_cards: dict[str, ScopeCard], choices: list[RegulationChoice]
) -> list[RegulationChoice]:
    listed = {c.regulation: scope_cards[c.regulation] for c in choices}
    verdict = _ask(profile, listed)
    missing = {r: card for r, card in listed.items() if r not in verdict}
    if missing:  # one retry with only the omitted regulations
        verdict |= _ask(profile, missing)
    out = []
    for c in choices:
        v = verdict.get(c.regulation)
        if v is None:
            out.append(
                c.model_copy(update={"rationale": c.rationale + " No LLM verdict, scores only."})
            )
            continue
        applies = bool(v["applies"])
        p = min(1.0, max(0.0, float(v["p_applies"])))
        # Keep the probability consistent with the decision the model made.
        p = max(p, 0.5) if applies else min(p, 0.49)
        out.append(
            RegulationChoice(
                regulation=c.regulation,
                version=c.version,
                probability=round(p, 3),
                selected=applies,
                rationale=f"{v['rationale']} ({c.rationale})",
            )
        )
    return sorted(out, key=lambda c: -c.probability)


def dump(choices: list[RegulationChoice]) -> str:
    return json.dumps([c.model_dump() for c in choices], indent=1)
