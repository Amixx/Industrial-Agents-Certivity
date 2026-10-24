"""Lane K: tag the four expert-skip classes on the 4-vote file, then drop class sets.

    BRAIN_LLM= PYTHONPATH=. uv run python swing/k_filter.py selftest
    BRAIN_LLM= PYTHONPATH=. uv run python swing/k_filter.py tag
    BRAIN_LLM= PYTHONPATH=. uv run python swing/k_filter.py sweep
    BRAIN_LLM= PYTHONPATH=. uv run python swing/k_filter.py extras

Rules only. No model call. The gold file is read by `sweep` and `extras` after the cut,
to score and to name the five matches votes4 has and votes7 lacks. `tag` does not open it.

The four classes are the shared brief of task 08, with lane C's hand-read examples as the
wording to recognise. A row is tagged only when the text matches. Borderline rows are listed
as ambiguous and are not dropped.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from brain.paths import CASES
from eval.score import paragraph_key

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
EXP = OUT / "experiments"
VOTES4 = OUT / "rear-lamp-swing-A-votes4.json"
VOTES7 = OUT / "rear-lamp-swing-A-votes7.json"
TAGS = EXP / "K-tags.json"
EXPECTED = CASES / "dev-rear-lamp" / "expected.json"

# A kept number: a width, height, angle, voltage or photometric value. Paragraph numbers
# and table numbers do not count. Class 2 leaves these rows alone.
_UNIT = re.compile(
    r"°|º|\b(?:cd|mm|cm|mcd|lx|hz|khz|mhz|ghz)\b|\b\d+(?:[.,]\d+)?\s*v\b|per cent|%",
    re.I,
)
_SHALL = re.compile(r"\bshall\b", re.I)

# Class 1. How to prepare, immerse, spray, wipe or measure. Not the pass criterion.
_PROCEDURE = re.compile(
    r"\bprepar\w+\b.{0,40}\btest\b|"
    r"\btest plan\b|"
    r"\btest conditions\b|"
    r"\bmeasur\w+ instruments?\b|"
    r"\bmeasurement time\b|"
    r"\bvideo bandwidth\b|"
    r"\bspectrum analys|"
    r"\bshall be performed\b|"
    r"\bshall be arranged\b|"
    r"\bshall be subjected\b|"
    r"\bwater spray\b|"
    r"\bsalt[- ]spray\b|"
    r"\bimmers\w*\b|"
    r"\bshall be exposed\b|"
    r"\bcotton cloth\b|"
    r"\bwip(?:e|ed|ing)\b|"
    r"\bcleaned and dried\b|"
    r"\binspected visually\b|"
    r"\btest mixture\b|"
    r"\bindian ink\b|"
    r"\bfft\b|"
    r"\bshall be kept for\b|"
    r"\bshall be corrected\b|"
    r"\bflashing mode\b|"
    r"\boperated at a voltage\b|"
    r"\btested at rated current\b|"
    r"\bapparent surface\b.{0,200}\bshall be determined\b|"
    r"\bshall be measured from the (?:highest|lowest) point\b|"
    r"\bshall be measured\b|"
    r"\btest groups?\b|"
    r"\btechnical service shall perform\b",
    re.I,
)
# The pass criterion of the same test stays, even when the sentence also says "when tested".
_PASS = re.compile(
    r"shall not exceed|shall not be exceeded|"
    r"not less than|not more than|not greater than|"
    r"equal to or greater|equal or greater|"
    r"shall not show|shall show no|"
    r"shall prevent|"
    r"no water shall|"
    r"shall not penetrate|"
    r"minimum and maximum|"
    r"limits?\b.{0,50}\bshall apply",
    re.I,
)

# Class 2. The whole demand is orientation, count, bare presence, or "at the rear".
_COUNT = re.compile(
    r"\b(?:one|two|three|four|five|\d+) in number\b|"
    r"\bthe number of\b.{0,80}\bshall be (?:one|two|three|four|five|\d+)\b",
    re.I,
)
_ORIENT = re.compile(
    r"\bshall be oriented (?:rearwards|forwards|to the (?:side|front|rear))\b",
    re.I,
)
_AT_REAR = re.compile(
    r"\bshall be (?:positioned in length )?at the rear of the vehicle\b|"
    r"\bpositioned in length at the rear of the vehicle\b|"
    r"\bin length,? the .{0,80}?shall be at the rear of the vehicle\b",
    re.I,
)
_PRESENCE = re.compile(r"\bshall be present\b", re.I)
_COLOUR = re.compile(r"\bshall be (?:red|amber|white|selective yellow|yellow)\b", re.I)
_TELLTALE = re.compile(r"\bshall be provided with a\b.{0,40}\btell-tale\b", re.I)

# Class 3. The sentence introduces a variant as optional or absent.
# (name, pattern, skip when the row also states a kept unit)
_VARIANTS: tuple[tuple[str, re.Pattern[str], bool], ...] = (
    (
        "replaceable source",
        re.compile(
            r"(?<!non-)replaceable\b.{0,60}light source|"
            r"light source modules?|"
            r"led substitute|"
            r"exception of lamps with non-replaceable",
            re.I,
        ),
        False,
    ),
    ("control gear", re.compile(r"control gear", re.I), False),
    ("variable intensity", re.compile(r"variable (?:luminous )?intensity", re.I), False),
    ("interdependent", re.compile(r"interdependent lamp", re.I), False),
    ("logo", re.compile(r"manufacturer logo", re.I), False),
    ("trailer", re.compile(r"\btrailers?\b", re.I), False),
    ("side device", re.compile(r"side[- ](?:retro-?reflectors?|marker)", re.I), False),
    ("REESS", re.compile(r"\bREESS\b"), False),
    ("starter or ICE", re.compile(r"starter motor|internal combustion", re.I), False),
    ("no immunity functions", re.compile(r"immunity related function", re.I), False),
    ("manoeuvring lamp", re.compile(r"manoeuvr", re.I), False),
    ("fail-safe", re.compile(r"fail-?safe", re.I), False),
    (
        "low mount",
        re.compile(r"(?:less than|below|equal to or less than)\s*750\s*mm", re.I),
        False,
    ),
    ("assembly letter", re.compile(r"additional letter\s+\"[DY]\"", re.I), False),
    ("separable lens", re.compile(r"designed to be separated from the main body", re.I), False),
    ("movable component", re.compile(r"movable components|moving component", re.I), False),
    ("optional lamps", re.compile(r"\boptional lamps\b", re.I), False),
    ("outside the body", re.compile(r"not included into the lamp body", re.I), False),
    ("single approval mark", re.compile(r"single approval mark", re.I), True),
    ("reciprocal incorporation", re.compile(r"reciprocally incorporated", re.I), True),
)
_PRODUCT = re.compile(
    r"\b(?:rear position lamps?|stop lamps?|reversing lamps?|retro-?reflectors?)\b",
    re.I,
)
_OTHER_FUNCTION = re.compile(
    r"\b(?:direction indicators?|rear fog lamps?|end-outline marker lamps?|"
    r"front position lamps?|manoeuvring lamps?)\b",
    re.I,
)
_MOTOR = re.compile(r"\bmotor vehicles?\b|\bcategory M\b|\bM1\b", re.I)

# Class 4. The only demand delegates to a table, paragraph, section or regulation.
# A cross-reference that only names which approval or document is not a pointer.
# "according to Regulation No. 37" on its own stays. The obligation has to be the delegation.
_POINTER = re.compile(
    r"as specified in (?:the )?(?:table|figure|annex|paragraphs)\b|"
    r"requirements in (?:the )?table\b|"
    r"(?:specified|given|those) in (?:the )?table\b|"
    r"conform to (?:the )?(?:paragraphs?|sections?)\b|"
    r"comply with (?:the )?(?:paragraphs?|sections?|requirements of paragraph)\b|"
    r"fulfil(?:s|ls)? the requirements of paragraph|"
    r"meet the (?:requirements|provisions|failure provisions) of paragraph|"
    r"requirements of paragraph [\d.]+ shall (?:not )?be (?:satisfied|fulfilled|met)|"
    r"provisions of paragraphs? [\d.]+ shall not apply|"
    r"type[- ]approv\w* according to|"
    r"deemed to comply with paragraph",
    re.I,
)

# Sentences the rules must get right. These are the class definitions, not gold rows.
_SELFTEST: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("The sample shall be immersed in water for one hour.", (1,)),
    ("The outer surface shall be wiped with a cotton cloth.", (1,)),
    ("After the water spray, the surface shall not show any apparent surface changes.", ()),
    (
        "When tested by the method in Annex 10, the pulse amplitude shall not exceed +75 V.",
        (),
    ),
    ("The rear position lamp shall be oriented rearwards.", (2,)),
    ("The rear position lamp shall be positioned in length at the rear of the vehicle.", (2,)),
    ("The rear retro-reflector shall be present on motor vehicles.", (2,)),
    ("The number of stop lamps shall be two on all categories of vehicles.", (2,)),
    (
        "The rear position lamp shall have a horizontal visibility angle of 80° outwards.",
        (),
    ),
    (
        "An electronic light source control gear not included into the lamp body shall be marked.",
        (3,),
    ),
    ("The lamp shall conform to paragraphs 4. and 5.", (4,)),
    ("The lamp shall provide the minimum luminous intensity as specified in Table 4.", (4,)),
    ("The minimum luminous intensity shall be 4 cd as specified in Table 4.", ()),
    ("After the water immersion test, no water shall penetrate to the reflecting surface.", ()),
    ("The applicant shall specify the approval number according to Regulation No. 37.", ()),
    (
        "The lamp shall, with the exception of lamps with non-replaceable light sources, "
        "bear the category marking.",
        (3,),
    ),
    (
        "Lamps with non-replaceable light sources shall bear the rated voltage.",
        (),
    ),
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def row_key(r: dict[str, Any]) -> tuple[str, str | None, str]:
    return r["source"]["regulation"], paragraph_key(r["source"].get("paragraph")), r["text"]


def _head(text: str) -> str:
    """Drop an 'except ...' tail. A variant named only there is not what the sentence is for."""
    return re.split(r"\bexcept\b", text, maxsplit=1, flags=re.I)[0]


def _class1(text: str) -> str | None:
    if _PASS.search(text):
        return None
    hit = _PROCEDURE.search(text)
    return f"procedure: {hit.group(0)}" if hit else None


def _class2(text: str) -> str | None:
    if _UNIT.search(text) or len(_SHALL.findall(text)) != 1:
        return None
    if _ORIENT.search(text):
        return "orientation"
    if _AT_REAR.search(text):
        return "at the rear"
    if _COUNT.search(text):
        return "count"
    if _PRESENCE.search(text):
        return "bare presence"
    return None


def _class3(text: str) -> tuple[str | None, str | None]:
    """Return (class reason, ambiguous reason). A hit is one or the other, not both."""
    head = _head(text)
    has_unit = _UNIT.search(text) is not None
    product = _PRODUCT.search(head) is not None
    reasons: list[str] = []
    ambiguous: list[str] = []
    for name, cre, skip_if_unit in _VARIANTS:
        if not cre.search(head):
            continue
        if skip_if_unit and has_unit:
            continue
        if name == "manoeuvring lamp" and product:
            ambiguous.append("manoeuvring lamp named beside a product function")
            continue
        if name == "trailer" and _MOTOR.search(head):
            ambiguous.append("trailer mentioned in a motor-vehicle sentence")
            continue
        reasons.append(name)
    if reasons:
        return "variant: " + ", ".join(reasons), None
    if ambiguous:
        return None, ambiguous[0]
    if _OTHER_FUNCTION.search(head) and not product:
        return None, "other lamp function, not one of the brief's variants"
    return None, None


def _class4(text: str, class2: str | None) -> str | None:
    if class2 or _UNIT.search(text):
        return None
    hit = _POINTER.search(text)
    return f"pointer: {hit.group(0)}" if hit else None


def _ambiguous_extra(text: str, classes: list[int]) -> list[str]:
    """Borderline rows the shared brief does not decide. They are not dropped."""
    notes: list[str] = []
    if 2 not in classes and not _UNIT.search(text) and len(_SHALL.findall(text)) == 1:
        if _COLOUR.search(text):
            notes.append("colour: in lane C's list, not in the shared brief")
        if _TELLTALE.search(text):
            notes.append(
                "tell-tale presence: not orientation, count, presence of the lamp, or at the rear"
            )
    if (
        1 not in classes
        and _PASS.search(text) is None
        and re.search(r"\bshall be tested\b", text, re.I)
    ):
        notes.append("shall be tested, but not a prepare, immerse, spray, wipe or measure step")
    if re.search(r"\btest method shall\b", text, re.I) and 1 not in classes:
        notes.append("states what the test method must achieve, not how to run the test")
    return notes


def classify(text: str) -> dict[str, Any]:
    classes: list[int] = []
    reasons: list[str] = []
    ambiguous: list[str] = []
    c1 = _class1(text)
    if c1:
        classes.append(1)
        reasons.append(c1)
    c2 = _class2(text)
    if c2:
        classes.append(2)
        reasons.append(c2)
    c3, amb3 = _class3(text)
    if c3:
        classes.append(3)
        reasons.append(c3)
    if amb3:
        ambiguous.append(amb3)
    c4 = _class4(text, c2)
    if c4:
        classes.append(4)
        reasons.append(c4)
    ambiguous.extend(_ambiguous_extra(text, classes))
    return {"classes": classes, "reasons": reasons, "ambiguous": ambiguous}


def tag_rows(
    rows: list[dict[str, Any]], votes7: set[tuple[str, str | None, str]]
) -> list[dict[str, Any]]:
    tagged = []
    for i, r in enumerate(rows):
        rec = classify(r["text"])
        rec.update(
            {
                "index": i,
                "id": r["id"],
                "regulation": r["source"]["regulation"],
                "paragraph": r["source"].get("paragraph"),
                "in_votes7": row_key(r) in votes7,
                "text": r["text"],
            }
        )
        tagged.append(rec)
    return tagged


def counts(tags: list[dict[str, Any]], only_extra: bool = False) -> dict[str, int]:
    rows = [t for t in tags if not t["in_votes7"]] if only_extra else tags
    out = {"rows": len(rows), "ambiguous": 0}
    for n in (1, 2, 3, 4):
        out[f"class_{n}"] = sum(1 for t in rows if n in t["classes"])
    out["any"] = sum(1 for t in rows if t["classes"])
    out["ambiguous"] = sum(1 for t in rows if t["ambiguous"])
    out["neither"] = sum(1 for t in rows if not t["classes"] and not t["ambiguous"])
    return out


def selftest() -> int:
    failed = 0
    for text, expect in _SELFTEST:
        got = tuple(classify(text)["classes"])
        if got != expect:
            failed += 1
            print(f"FAIL {got} != {expect}: {text}")
    print(f"selftest {len(_SELFTEST) - failed}/{len(_SELFTEST)}")
    return 1 if failed else 0


def cmd_tag() -> int:
    doc = load(VOTES4)
    votes7 = {row_key(r) for r in load(VOTES7)["requirements"]}
    tags = tag_rows(doc["requirements"], votes7)
    payload = {
        "source": "out/rear-lamp-swing-A-votes4.json",
        "compared_with": "out/rear-lamp-swing-A-votes7.json",
        "method": "lexical rules in brain/swing/k_filter.py, no model call",
        "classes": {
            "1": "test procedure (prepare, immerse, spray, wipe, measure); pass criterion stays",
            "2": "installation one-liner: orientation, count, bare presence, or at the rear",
            "3": "variant the sentence itself introduces as optional or absent",
            "4": "pointer to a table, paragraph, section or regulation, with no value of its own",
        },
        "note": "ambiguous rows are not in classes and are not dropped",
        "summary_all": counts(tags),
        "summary_extra": counts(tags, only_extra=True),
        "rows": tags,
    }
    TAGS.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    print("all", payload["summary_all"])
    print("extra", payload["summary_extra"])
    print(f"wrote {TAGS}")
    return 0


def _keep(tag: dict[str, Any], drop: set[int]) -> bool:
    return not any(n in drop for n in tag["classes"])


SWEEPS: tuple[tuple[str, set[int]], ...] = (
    ("drop1", {1}),
    ("drop12", {1, 2}),
    ("drop123", {1, 2, 3}),
    ("drop1234", {1, 2, 3, 4}),
)


def write_submission(doc: dict[str, Any], rows: list[dict[str, Any]], path: Path) -> None:
    reqs = []
    for i, r in enumerate(rows, 1):
        rec = {k: r[k] for k in ("text", "source", "confidence", "quote") if k in r}
        reqs.append({"id": f"R-{i:04d}", **rec})
    out = {
        "team_id": doc["team_id"],
        "case_id": doc["case_id"],
        "requirements": reqs,
        "regulations": doc["regulations"],
        "profile": doc["profile"],
    }
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")


def _gold_match(
    rows: list[dict[str, Any]], gold: list[dict[str, Any]]
) -> list[tuple[int, int, float]]:
    from eval import judge

    return judge.match(rows, gold)


def f2(matched: int, rows: int) -> float:
    return 5 * matched / (760 + rows) if rows or matched else 0.0


def cmd_sweep() -> int:
    """Write the four cut files. Scores use the gold only here, after the classes are fixed."""
    doc = load(VOTES4)
    tags = load(TAGS)["rows"]
    if len(tags) != len(doc["requirements"]):
        raise SystemExit("K-tags.json does not match votes4; rerun tag")
    gold = load(EXPECTED)["requirements"]
    base_pairs = _gold_match(doc["requirements"], gold)
    base_hit = {i for i, _, _ in base_pairs}
    manifest = []
    for name, drop in SWEEPS:
        kept_idx = [t["index"] for t in tags if _keep(t, drop)]
        dropped = [t for t in tags if not _keep(t, drop)]
        rows = [doc["requirements"][i] for i in kept_idx]
        path = OUT / f"rear-lamp-swing-K-{name}.json"
        write_submission(doc, rows, path)
        pairs = _gold_match(rows, gold)
        matched_deleted = sum(1 for t in dropped if t["index"] in base_hit)
        line = {
            "file": path.name,
            "dropped_classes": sorted(drop),
            "rows": len(rows),
            "matched": len(pairs),
            "f2": round(f2(len(pairs), len(rows)), 3),
            "deleted": len(dropped),
            "deleted_matched": matched_deleted,
            "deleted_unmatched": len(dropped) - matched_deleted,
        }
        manifest.append(line)
        log = [
            "lane K filter on votes4",
            f"dropped classes {sorted(drop)}",
            f"rows {line['rows']}, matched {line['matched']}, F2 {line['f2']:.3f}",
            (
                f"deleted {line['deleted']}: matched {matched_deleted}, "
                f"unmatched {line['deleted_unmatched']}"
            ),
            "votes7 baseline: 351 rows, 156 matched, F2 0.702",
            "spend: $0 (no model call)",
        ]
        path.with_suffix(".log").write_text("\n".join(log) + "\n")
        print(line)
    (EXP / "K-sweep.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return 0


def cmd_extras() -> int:
    """The five gold rows votes4 matches and votes7 does not, and which class would drop them."""
    from eval import judge

    doc4 = load(VOTES4)
    doc7 = load(VOTES7)
    tags = load(TAGS)["rows"]
    gold = load(EXPECTED)["requirements"]
    m4 = _gold_match(doc4["requirements"], gold)
    m7 = judge.match(doc7["requirements"], gold)
    only4 = sorted(set(j for _, j, _ in m4) - set(j for _, j, _ in m7))
    by_gold = {j: (i, s) for i, j, s in m4}
    report = []
    for j in only4:
        i, sim = by_gold[j]
        tag = tags[i]
        g = gold[j]
        report.append(
            {
                "gold_index": j,
                "gold_regulation": g["source"]["regulation"],
                "gold_paragraph": g["source"].get("paragraph"),
                "gold_text": g["text"],
                "submitted_id": tag["id"],
                "submitted_paragraph": tag["paragraph"],
                "submitted_in_votes7": tag["in_votes7"],
                "similarity": round(sim, 3),
                "classes": tag["classes"],
                "ambiguous": tag["ambiguous"],
                "reasons": tag["reasons"],
                "deleted_by": [
                    name for name, drop in SWEEPS if any(n in drop for n in tag["classes"])
                ],
                "submitted_text": tag["text"],
            }
        )
    # Also the extra submitted rows that the original votes4 assignment matched.
    extra_hits = [t for t in tags if not t["in_votes7"] and t["index"] in {i for i, _, _ in m4}]
    payload = {
        "gold_rows_matched_by_votes4_not_votes7": len(report),
        "matches": report,
        "extra_submitted_rows_matched_in_votes4": [
            {
                "id": t["id"],
                "paragraph": t["paragraph"],
                "classes": t["classes"],
                "ambiguous": t["ambiguous"],
                "text": t["text"],
            }
            for t in extra_hits
        ],
    }
    (EXP / "K-extras.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    print(f"gold rows in votes4 but not votes7: {len(report)}")
    for rec in report:
        deleted = ",".join(rec["deleted_by"]) or "none"
        print(
            f"  {rec['submitted_id']} {rec['gold_regulation']} {rec['gold_paragraph']} "
            f"classes={rec['classes']} deleted_by={deleted} "
            f"in_votes7={rec['submitted_in_votes7']}"
        )
    print(f"extra submitted rows that votes4 matched: {len(extra_hits)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    sub.add_parser("tag")
    sub.add_parser("sweep")
    sub.add_parser("extras")
    args = ap.parse_args(argv)
    return {"selftest": selftest, "tag": cmd_tag, "sweep": cmd_sweep, "extras": cmd_extras}[
        args.cmd
    ]()


if __name__ == "__main__":
    raise SystemExit(main())
