#!/usr/bin/env python3
"""Tier A synthetic cases: ablations of the real rear-lamp gold.

Every requirement in cases/dev-rear-lamp/expected.json is tagged with the lamp function(s) it depends on.
Each variant keeps only some functions; its expected.json is the subset of gold requirements whose rule is
satisfied by that variant. No new labels are invented, so these cases inherit the experts' labels.

Run from the repository root:

    python synthetic/make_tier_a.py

It writes synthetic/gold_function_tags.json and synthetic/cases/<case>/expected.json.
The spec.md of each case is hand-written and already in synthetic/cases/<case>/.

Standard library only.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "cases" / "dev-rear-lamp" / "expected.json"
OUT = Path(__file__).resolve().parent

# Functions: P = rear position lamp, S = stop lamp (S1/S2), R = reversing lamp, RR = rear retro-reflector (Class IA/IB).
# A variant is a set of functions plus whether the lamp is LED with electronics (which brings in UN R10).
RULES = {
    "ANY":       ("any light-signalling device, retro-reflectors included (UN R48 counts them as lamps)",
                  lambda f, led: bool(f)),
    "LAMP":      ("any light-emitting function (P, S or R)", lambda f, led: bool(f & {"P", "S", "R"})),
    "LED":       ("light-emitting function with LED modules / electronics", lambda f, led: bool(f & {"P", "S", "R"}) and led),
    "MULTI":     ("two or more functions grouped, combined or reciprocally incorporated", lambda f, led: len(f) >= 2),
    "RED":       ("a red rear function (P, S or RR)", lambda f, led: bool(f & {"P", "S", "RR"})),
    "P":         ("rear position lamp", lambda f, led: "P" in f),
    "S":         ("stop lamp", lambda f, led: "S" in f),
    "R":         ("reversing lamp", lambda f, led: "R" in f),
    "RR":        ("rear retro-reflector", lambda f, led: "RR" in f),
    "P_AND_SR":  ("position lamp reciprocally incorporated with a function switched ON with it (S or R)",
                  lambda f, led: "P" in f and bool(f & {"S", "R"})),
    "P_AND_S":   ("position lamp reciprocally incorporated with a stop lamp", lambda f, led: {"P", "S"} <= f),
    "S_OR_R":    ("stop or reversing lamp (functions that may not carry a logo)", lambda f, led: bool(f & {"S", "R"})),
    "P_OR_S":    ("lamps other than reversing lamps (UN R148 Annex 8 1.2.2)", lambda f, led: bool(f & {"P", "S"})),
    "P_OR_RR":   ("rear position lamp or rear retro-reflector (UN R48 5.18, movable components)",
                  lambda f, led: bool(f & {"P", "RR"})),
}


def _ids(prefix_range: tuple[int, int]) -> list[str]:
    a, b = prefix_range
    return [f"G-{n:04d}" for n in range(a, b + 1)]


def tag_for(req: dict) -> str:
    """The rule for one gold requirement. Decided per regulation and paragraph block, then by explicit id."""
    rid, reg = req["id"], req["source"]["regulation"]
    if reg == "UN R150":
        return "RR"
    if reg == "UN R10":
        return "LED"
    explicit = {
        # UN R48, general provisions (paragraph 5)
        **{i: "ANY" for i in ["G-0054", "G-0055", "G-0056", "G-0057", "G-0059", "G-0060", "G-0061",
                              "G-0077", "G-0078", "G-0079"]},
        "G-0062": "P", "G-0064": "P",              # 5.5.5 manufacturer logo: of these functions only P may carry one
        "G-0065": "MULTI", "G-0066": "MULTI",      # 5.7.1 grouped / combined / reciprocally incorporated
        "G-0067": "P_AND_SR",                      # 5.7.1.1 position lamp incorporated with a function switched ON with it
        "G-0068": "LAMP",                          # 5.7.2.1 does not apply to a single retro-reflector
        "G-0071": "LAMP", "G-0072": "LAMP",        # 5.9 photometric variation while switched ON
        "G-0073": "RED", "G-0074": "RED",          # 5.10 no red light to the front
        "G-0075": "P",                             # 5.11 position lamps switched together
        "G-0076": "P_OR_RR",                       # 5.18 movable components
        # UN R148
        "G-0167": "P", "G-0168": "R",              # 3.3.2.5.1.1 mounting arrow
        "G-0171": "LED",                           # 3.3.3.4 electronic control gear / non-replaceable sources
        "G-0185": "LED",                           # 3.3.4.6 markings on the light source module
        "G-0189": "P_AND_SR", "G-0190": "P_AND_S", # 4.5.3 reciprocal incorporation
        "G-0197": "S_OR_R",                        # 4.5.5 stop and reversing lamps shall not carry a logo
        "G-0199": "LED",                           # 4.6.1.2 single lamp with more than one light source
        "G-0208": "LED",                           # 4.8.1.2 light source modules / non-replaceable sources
        "G-0218": "P", "G-0219": "P",
        "G-0220": "S", "G-0221": "S",
        "G-0222": "R", "G-0225": "R", "G-0229": "R", "G-0230": "R",
        "G-0232": "P_OR_S",
    }
    for i in [*_ids((80, 85))]:
        explicit[i] = "R"                          # UN R48 6.4 reversing lamp
    for i in [*_ids((86, 100))]:
        explicit[i] = "S"                          # UN R48 6.7 stop lamp
    for i in [*_ids((101, 116))]:
        explicit[i] = "P"                          # UN R48 6.10 rear position lamp
    for i in [*_ids((117, 123))]:
        explicit[i] = "RR"                         # UN R48 6.14 rear retro-reflector, non-triangular
    for i in [*_ids((172, 179)), *_ids((203, 207))]:
        explicit[i] = "LED"                        # UN R148 3.3.3.5 / 4.7.2.4 replaceable light source modules
    for i in [*_ids((192, 196))]:
        explicit[i] = "P"                          # UN R148 4.5.5 logo inside the apparent surface
    if rid in explicit:
        return explicit[rid]
    if reg == "UN R148":
        return "LAMP"                              # markings, general specifications, test conditions, conformity
    raise KeyError(f"no rule for {rid} ({reg} {req['source'].get('paragraph')})")


# Each variant: case id -> (functions, LED electronics, one-line description)
VARIANTS = {
    "synth-a01-stop-tail-lamp":      ({"P", "S"}, True,  "rear position + stop lamp, LED, no reversing lamp, no retro-reflector"),
    "synth-a02-reversing-lamp":      ({"R"}, True,       "standalone LED reversing lamp"),
    "synth-a03-rear-retro-reflector":({"RR"}, False,     "standalone red rear retro-reflector, Class IA, no electronics"),
    "synth-a04-position-lamp-retro": ({"P", "RR"}, True, "LED rear position lamp with an integrated retro-reflector"),
    "synth-a05-position-reversing-lamp": ({"P", "R"}, True, "body-mounted LED rear position + reversing lamp"),
    "synth-a06-rear-combination-rfq":({"P", "S", "R", "RR"}, True, "the original product, re-described as a supplier RFQ (full gold)"),
    "synth-a07-rear-position-lamp":  ({"P"}, True,       "slim LED rear position lamp (light guide), position function only"),
}


def main() -> int:
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    reqs = gold["requirements"]
    tags = {r["id"]: tag_for(r) for r in reqs}

    (OUT / "gold_function_tags.json").write_text(json.dumps({
        "rules": {k: v[0] for k, v in RULES.items()},
        "tags": [{"id": r["id"], "regulation": r["source"]["regulation"], "paragraph": r["source"].get("paragraph"),
                  "rule": tags[r["id"]]} for r in reqs],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"tagged {len(reqs)} gold requirements: {dict(Counter(tags.values()))}\n")
    print(f"{'case':<34}{'n':>5}   by regulation")
    for case_id, (functions, led, _desc) in VARIANTS.items():
        keep = [r for r in reqs if RULES[tags[r["id"]]][1](functions, led)]
        folder = OUT / "cases" / case_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "expected.json").write_text(json.dumps(
            {"team_id": "team-00", "case_id": case_id, "requirements": keep}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        by_reg = Counter(r["source"]["regulation"] for r in keep)
        print(f"{case_id:<34}{len(keep):>5}   {dict(sorted(by_reg.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
