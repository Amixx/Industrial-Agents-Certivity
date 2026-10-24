"""Lane J of task 08: tag four expert-skip classes on the 7-vote file.

Text rules only. No model call, and the gold file is not an input to a tag. Gold is used
later, by the sweep, only to score a cut that was already chosen from the tags.

    cd brain && BRAIN_LLM= PYTHONPATH=. uv run python swing/j_classes.py tag
    cd brain && BRAIN_LLM= PYTHONPATH=. uv run python swing/j_classes.py sweep
    cd brain && BRAIN_LLM= PYTHONPATH=. uv run python swing/j_classes.py samples
    cd brain && BRAIN_LLM= PYTHONPATH=. uv run python swing/j_classes.py sunday

The four classes are the shared brief of brain/docs/todo/08-complex.md. A row can carry
more than one. Ambiguous rows are recorded and are not dropped.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BRAIN = ROOT / "brain"
OUT = ROOT / "out"
VOTES7 = OUT / "rear-lamp-swing-A-votes7.json"
TAGS = OUT / "experiments" / "J-tags.json"
SWEEP = OUT / "experiments" / "J-sweep.json"
EXPECTED = ROOT / "cases" / "dev-rear-lamp" / "expected.json"

# A kept number is a width, height, angle, intensity or other value of the row's own.
# Paragraph numbers and table numbers do not count. Count words ("two in number") do not.
_OWN_VALUE = re.compile(
    r"\d[\d.,]*\s*(?:mm|cm2|cm²|cm|metres?|m|°|cd|%|per cent|v|db|khz|mhz|ghz|µs|μs)\b"
    r"|\d\s*:\s*\d"
    r"|\d+\s*'"
    r"|[\d⁰¹²³⁴⁵⁶⁷⁸⁹][^\n]{0,6}cd\b",
    re.I,
)

# The pass criterion of a test stays. These phrases veto class 1 even when the same
# sentence names the method.
_PASS = re.compile(
    r"no water shall"
    r"|shall not be considered to have passed"
    r"|no cracking"
    r"|no standing pool"
    r"|shall not show"
    r"|shall not fall below"
    r"|must be visible"
    r"|shall be below the"
    r"|limits shall be"
    r"|limit shall remain"
    r"|shall be equal to or greater"
    r"|shall not be permissible"
    r"|no degradation of performance"
    r"|shall not exceed",
    re.I,
)

_AFTER_TEST = re.compile(r"\bAfter (?:undergoing|the|completion)\b", re.I)

_C1: tuple[tuple[str, str], ...] = (
    (r"\bimmersed\b", "immerse the sample"),
    (r"\bimmersion test shall be repeated\b", "immerse the sample"),
    (r"\bwiped with\b", "wipe the sample"),
    (r"\bcotton cloth\b", "wipe or dry with a cotton cloth"),
    (r"\bsaline mist\b", "salt-spray the sample"),
    (r"\batomiz", "produce the salt spray"),
    (r"\bwater spray test\b", "run the water spray"),
    (r"\bshall be stripped of all removable parts\b", "prepare the sample"),
    (r"\bshall be divided into\b", "allocate samples to groups"),
    (r"\bselected at random\b", "allocate samples"),
    (r"\bkept by the laborator", "hold samples at the laboratory"),
    (r"\bshall submit \w+ samples\b", "submit samples"),
    (r"\bsubjected(?:\s+\w+){0,2}\s+to the\b", "put the sample into a named test"),
    (r"\bshall be kept for \d+ consecutive hours\b", "condition the sample"),
    (r"\ballowed to cool for\b", "condition the sample"),
    (r"\bshall then be fully tested\b", "allocate samples onward"),
    (r"\bshall be measured (?:by the method|according to|inside the field)\b", "how to measure"),
    (r"\bmeasurements shall be made\b", "how to measure"),
    (r"\bmeasurements shall be repeated\b", "how to measure"),
    (r"\bshall be made separately\b", "how to measure"),
    (r"\bmeasurement results shall be added\b", "how to combine measurements"),
    (r"\ball measurements\b", "how to measure"),
    (r"\bintensities shall be measured with the light source continuously lit\b", "how to measure"),
    (r"\bshall be carried out according to the method\b", "how to measure"),
    (
        r"\btesting of the colour\b.{0,120}\bshall be carried out according to\b",
        "how to measure colour",
    ),
    (r"\bshall be operated as specified by the applicant\b", "how the lab operates the lamp"),
    (r"\boperated for testing\b", "how the lab operates the source"),
    (r"\bfor testing the voltage supplied\b", "set the test voltage"),
    (r"\bshall be rotated about\b", "position the sample for measurement"),
    (r"\bmay be rotated about\b", "position the sample for measurement"),
    (r"\bshall be placed in the position\b", "position the sample for measurement"),
    (r"\btest procedure described in\b", "apply a named procedure"),
    (r"\bshall be illuminated by CIE\b", "how to illuminate the sample"),
    (r"\bnormal operation mode\b", "set the sample's operating mode"),
    (r"\bshall be switched on and shall be stimulated\b", "prepare the sample"),
    (r"\bstate of charge \(SOC\)", "set the sample's state of charge"),
    (r"\bcurrent shall be set to\b", "set the sample's current"),
    (r"\bfrequency step size and dwell time shall be chosen\b", "how to step the measurement"),
    (r"\bshall be applied to the supply lines\b", "how to apply the test pulses"),
    (r"\bshall be observed for moisture\b", "how to inspect the sample"),
    (r"\binspected visually\b", "how to inspect the sample"),
    (r"\bshall be cleaned\b", "clean the sample before a measurement"),
    (r"\blightly shaken\b", "prepare the sample"),
    (r"\btested by the method\b", "measure by a named method"),
    (r"\bmeasured by the method\b", "measure by a named method"),
)

_C1_AMB: tuple[tuple[str, str], ...] = (
    (
        r"\bshall be tested for radiated and conducted emissions\b",
        "names the tests the ESA undergoes, not how to prepare or measure the sample",
    ),
    (r"\bcorrection factor of 20 dB\b", "a measurement correction that states 20 dB"),
    (
        r"\bRI verification of the retro-reflectors shall be performed only\b",
        "limits which angles are verified, and states those angles",
    ),
    (r"\b200 mm diameter\b", "a measurement aperture that states 200 mm"),
    (r"\blimited to 100 cm2\b", "a measurement area that states 100 cm2"),
    (
        r"\b(?:height above the ground|position of the lamp with regard to height)\b"
        r".{0,80}\bshall be measured\b",
        "defines installed height, not a laboratory sample step",
    ),
    (r"\bdirection of observation shall be shifted\b", "shifts the direction of observation"),
    (
        r"\bresistance of the front surface\b.{0,120}\bshall be checked\b",
        "says the resistance shall be checked, without a prepare, spray or wipe step",
    ),
    (
        r"\bfrequency range and general test conditions shall be based on ISO\b",
        "points at ISO 11452-1 for the conditions",
    ),
)

_POINTER: tuple[tuple[str, str], ...] = (
    (
        "only demand is a table",
        r"\b(?:as specified in|specified in|requirements in|given in|listed in) (?:the )?tables?\b",
    ),
    (
        "only demand is a paragraph or annex",
        r"\bset forth in (?:paragraphs?|annexes?|annex|tables?)\b",
    ),
    (
        "other sections apply",
        r"\brequirements contained in sections\b",
    ),
    (
        "pertinent requirements shall be applied",
        r"\brequirements pertinent to\b",
    ),
    (
        "in accordance with a paragraph",
        r"\bshall be in accordance with paragraph\b",
    ),
    (
        "deemed to comply with a paragraph",
        r"\bdeemed to comply with paragraph\b",
    ),
    (
        "failure provisions of a paragraph",
        r"\bfailure provisions of paragraph\b",
    ),
    (
        "provisions of other paragraphs shall be observed",
        r"\bprovisions of the relevant paragraphs\b",
    ),
    (
        "tests carried out according to an annex",
        r"\bshall be carried out according to Annex\b",
    ),
    (
        "type approval as specified in paragraph 6",
        r"\bas specified in the relevant subparagraphs of paragraph\b",
    ),
)

# Lane C called these pointers. The shared brief requires no value of the row's own,
# and these sentences restate a distance or an angle, so they stay out of the drop.
_C4_AMB: tuple[tuple[str, str], ...] = (
    (
        r"\bto verify paragraphs\b",
        "verifies other paragraphs, and also states a distance or a limit",
    ),
    (
        r"\bas specified in paragraph 2\.10\.7\b",
        "visibility defined by a paragraph reference, while the sentence also states the angles",
    ),
)

_C3: tuple[tuple[str, str], ...] = (
    (r"(?i)^(?:where|in case|in the case).{0,180}LED substitute", "LED substitute light source"),
    (r"\bin case replaceable light source module", "replaceable light source module"),
    (r"\bin case of replaceable (?:UN approved )?light source", "replaceable light source"),
    (r"\bin the case of replaceable (?:UN approved )?light source", "replaceable light source"),
    (r"\bnot included into the lamp body\b", "control gear outside the lamp body"),
    (r"\bdoes not include an electronic oscillator\b", "oscillator the sentence says is absent"),
    (
        r"\b(?:are not switched, contain no switches|do not include inductive load)\b",
        "switches or inductive load the sentence says are absent",
    ),
    (r"\bfail-safe\b", "temporary fail-safe replacement"),
    (r"\bif the optional lamps are installed, the optional lamps\b", "optional lamps"),
    (r"\bonly if a rear side-marker lamp is installed\b", "optional rear side-marker"),
    (r"\bREESS\b", "REESS charging configuration"),
    (r"\btraction battery\b", "traction battery"),
    (r"\bif such an indication is necessary\b", "TOP mark only if the indication is necessary"),
    (r"\bmarking material of Class\b", "retro-reflective marking material"),
    (r"\bmarking plates of Class\b", "retro-reflective marking plates"),
    (
        r"\bintended to be installed with its H plane at a mounting height less than 750 mm\b",
        "the low-mount case is the whole sentence",
    ),
    (r"\bspecial power supply\b", "special power supply"),
    (
        r"The lamp approved with light source\(s\) according to UN Regulation No\. 37\b",
        "a lamp approved with a Regulation 37 source",
    ),
    (
        r"\bapproved for one or more replaceable light source categories\b",
        "replaceable light-source categories",
    ),
    (
        r"\bin the case of lamps with an electronic light source control gear\b",
        "electronic light source control gear",
    ),
    (
        r"\bin the case of lamps with a variable luminous intensity control\b",
        "variable luminous intensity control",
    ),
    (r"\bin the case of lamps with a secondary operating mode\b", "secondary operating mode"),
    (
        r"\bIn case of a lamp controlled by an electronic light source control gear\b",
        "a lamp controlled by control gear",
    ),
    (r"\btell-tale shall be optional\b", "an optional tell-tale"),
    (r"\bAdditional retro-reflecting devices\b", "additional retro-reflectors"),
)

_C3_AMB: tuple[tuple[str, str], ...] = (
    (
        r"\breciprocally incorporated\b",
        "reciprocally incorporated, and the sentence does not say optional or absent",
    ),
    (
        r"\bnon-replaceable light source",
        "non-replaceable light source: the product's LED modules may be this case",
    ),
    (
        r"\bhidden by\b",
        "hidden by vehicle parts, and the sentence does not say optional or absent",
    ),
    (r"(?<!not )designed to be separated\b", "an outer lens designed to be separated"),
    (r"\bouter lens is used for several devices\b", "one outer lens used for several devices"),
    (
        r"\bIn case a light source category or categories or type",
        "a restricted light-source category",
    ),
)

_CHECKS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("The sample shall be immersed for 10 minutes in water.", (1,)),
    ("After the test, no water shall penetrate the reflector.", ()),
    ("The rear position lamp shall be oriented rearwards.", (2,)),
    ("The stop lamp shall be oriented towards the rear.", (2,)),
    ("The lamp shall be not less than 350 mm above the ground.", ()),
    ("The lamp shall have a horizontal angle of 45° inwards.", ()),
    ("Where the lamp has an LED substitute light source, mark it.", (3,)),
    ("The lamp shall meet the minimum intensity specified in Table 4.", (4,)),
    ("Meet the requirements in Table 4, except 60 cd is permitted.", ()),
    ("The lamp shall conform to the requirements set forth in paragraphs 4. and 5.", (4,)),
    ("After undergoing the tests, colour satisfies paragraph 5.1.5.", ()),
    ("The colour of the light emitted by the stop lamp shall be red.", ()),
    ("The rear position lamps shall be two in number.", (2,)),
    ("The rear retro-reflector shall be present on motor vehicles.", (2,)),
    ("In length, the rear retro-reflector shall be at the rear of the vehicle.", (2,)),
    ("The lamp shall be positioned in length at the rear of the vehicle.", (2,)),
    ("The two samples shall be divided into four groups of two.", (1,)),
    ("The device shall be lightly wiped with a cotton cloth.", (1,)),
    (
        "Where the ESA does not include an electronic oscillator above 9 kHz, "
        "it is deemed to comply with paragraph 6.3.2.",
        (3,),
    ),
    ("If the optional lamps are installed, the optional lamps shall be placed high.", (3,)),
    ("When tested by the method in Annex 10, amplitude shall not exceed 150 V.", ()),
    ("Connections shall be in accordance with paragraph 5.11.", (4,)),
    ("Mark the voltage, in the case of lamps with an electronic light source control gear.", (3,)),
    ("To verify paragraphs 5.10.1, no visibility at 25 m in front.", ()),
)


def stamp() -> str:
    return subprocess.check_output(["date", "+%d %b %H:%M %Z"], text=True).strip()


def _hit(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.I) is not None


def own_value(text: str) -> bool:
    return _OWN_VALUE.search(text) is not None


def _reasons(patterns: tuple[tuple[str, str], ...], text: str) -> list[str]:
    return [why for pattern, why in patterns if _hit(text, pattern)]


def _class2(text: str) -> tuple[str, str] | None:
    """Return (definite or ambiguous, kind) for an installation one-liner."""
    kind = None
    if _hit(text, r"\bshall be oriented (?:rearwards|towards the rear)\b"):
        kind = "orientation"
    elif _hit(text, r"\bin number\b"):
        kind = "count"
    elif _hit(
        text,
        r"\bnumber of lamps mounted on the vehicle shall be equal to the number indicated\b",
    ):
        kind = "count"
    elif _hit(text, r"\bshall be two \S.+ devices and one "):
        kind = "count"
    elif _hit(text, r"\bshall be one device mandatory\b"):
        kind = "count"
    elif _hit(text, r"\bshall be (?:mandatory|present)\b") and not _hit(text, r"tell-tale"):
        kind = "presence"
    elif _hit(text, r"\bpositioned in length at the rear of the vehicle\b"):
        kind = "at the rear"
    elif _hit(
        text, r"\bin length, the rear retro-reflector\b.{0,80}\bat the rear of the vehicle\b"
    ):
        kind = "at the rear"
    elif _hit(
        text,
        r"\b(?:lamp|retro-reflector) shall be at the rear of the vehicle\b",
    ):
        kind = "at the rear"
    if kind is None:
        return None
    if own_value(text):
        return ("ambiguous", kind)
    return ("definite", kind)


def _pointer_hit(text: str) -> str | None:
    for why, pattern in _POINTER:
        if _hit(text, pattern):
            return why
    return None


def tag_text(text: str) -> dict[str, Any]:
    """Classes the row belongs to, from its text alone."""
    classes: list[int] = []
    ambiguous: list[dict[str, str]] = []
    reasons: list[str] = []

    if not _PASS.search(text):
        hits = _reasons(_C1, text)
        if hits:
            classes.append(1)
            reasons.append("class 1: " + "; ".join(dict.fromkeys(hits)))
    if 1 not in classes:
        for pattern, why in _C1_AMB:
            if _hit(text, pattern):
                ambiguous.append({"class": "1", "why": why})
                break

    found = _class2(text)
    if found is not None:
        status, kind = found
        if status == "definite":
            classes.append(2)
            reasons.append(f"class 2: {kind}")
        else:
            ambiguous.append(
                {
                    "class": "2",
                    "why": f"{kind}, but the row also states a width, height, angle or other value",
                }
            )

    variant = _reasons(_C3, text)
    if variant:
        classes.append(3)
        reasons.append("class 3: " + "; ".join(dict.fromkeys(variant)))
    else:
        for pattern, why in _C3_AMB:
            if _hit(text, pattern):
                ambiguous.append({"class": "3", "why": why})
                break

    pointer = _pointer_hit(text)
    if pointer and not own_value(text) and not _AFTER_TEST.search(text):
        classes.append(4)
        reasons.append(f"class 4: {pointer}")
    elif pointer is None:
        for pattern, why in _C4_AMB:
            if _hit(text, pattern):
                ambiguous.append({"class": "4", "why": why})
                break

    return {"classes": classes, "ambiguous": ambiguous, "reasons": reasons}


def self_check() -> None:
    for text, expect in _CHECKS:
        got = tuple(tag_text(text)["classes"])
        if got != expect:
            raise SystemExit(f"rule check failed: {got} != {expect} for {text}")


def load_submission(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def tag_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tagged = []
    for row in rows:
        tag = tag_text(row["text"])
        source = row["source"]
        tagged.append(
            {
                "id": row["id"],
                "regulation": source["regulation"],
                "paragraph": source.get("paragraph"),
                "page": source.get("page"),
                "classes": tag["classes"],
                "ambiguous": tag["ambiguous"],
                "reasons": tag["reasons"],
                "text": row["text"],
            }
        )
    return tagged


def _counts(tagged: list[dict[str, Any]]) -> dict[str, int]:
    counts = {str(n): 0 for n in (1, 2, 3, 4)}
    any_class = 0
    ambiguous = 0
    for row in tagged:
        if row["classes"]:
            any_class += 1
        for n in row["classes"]:
            counts[str(n)] += 1
        if row["ambiguous"]:
            ambiguous += 1
    counts["any"] = any_class
    counts["ambiguous_rows"] = ambiguous
    counts["rows"] = len(tagged)
    return counts


def cmd_tag() -> int:
    self_check()
    data = load_submission(VOTES7)
    tagged = tag_rows(data["requirements"])
    payload = {
        "source": "out/rear-lamp-swing-A-votes7.json",
        "method": "text rules, no model call",
        "spend_usd": 0,
        "tagged_at": stamp(),
        "counts": _counts(tagged),
        "rows": tagged,
    }
    TAGS.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(payload["counts"], indent=2))
    print(f"wrote {TAGS}")
    return 0


def _key(row: dict[str, Any], paragraph_key: Any) -> tuple[str, str | None]:
    return row["source"]["regulation"], paragraph_key(row["source"].get("paragraph"))


def _f2(matched: int, rows: int) -> float:
    return 5 * matched / (760 + rows)


def _match_stats(rows: list[dict[str, Any]], expected: list[dict[str, Any]]) -> dict[str, Any]:
    from eval import judge
    from eval.score import paragraph_key

    gold = {_key(row, paragraph_key) for row in expected}
    ours: dict[tuple[str, str | None], int] = {}
    for row in rows:
        k = _key(row, paragraph_key)
        ours[k] = ours.get(k, 0) + 1
    pairs = judge.match(rows, expected)
    matched_sub = {i for i, _, _ in pairs}
    matched_exp = {j for _, j, _ in pairs}
    inside = [i for i, row in enumerate(rows) if _key(row, paragraph_key) in gold]
    missed = [j for j in range(len(expected)) if j not in matched_exp]
    on_cited = sum(1 for j in missed if _key(expected[j], paragraph_key) in ours)
    off_cited = len(missed) - on_cited
    matched = len(pairs)
    n = len(rows)
    n_inside = len(inside)
    base = _f2(matched, n)
    drop_outside = _f2(len(matched_sub & set(inside)), n_inside)
    recover = _f2(matched + on_cited, n)
    cite = _f2(matched + off_cited, n + off_cited)
    lifts = {
        "drop rows outside gold paragraphs": drop_outside - base,
        "recover gold rows missed on a cited paragraph": recover - base,
        "cite gold paragraphs the file skips": cite - base,
    }
    cause = max(lifts, key=lifts.get)
    return {
        "rows": n,
        "matched": matched,
        "f2": base,
        "outside_gold_paragraphs": n - n_inside,
        "matched_ids": [rows[i]["id"] for i in sorted(matched_sub)],
        "on_cited_misses": on_cited,
        "off_cited_misses": off_cited,
        "lifts": lifts,
        "why_f2_is_not_1": cause,
    }


def _run(cmd: list[str], cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    text = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        text += f"\nexit {proc.returncode}\n"
    return text.strip()


def _official(path: Path) -> str:
    rel = str(path)
    chunks = [
        _run(["uv", "run", "python", str(ROOT / "tools" / "validate.py"), rel], BRAIN),
        _run(["uv", "run", "python", str(ROOT / "tools" / "score_local.py"), rel], BRAIN),
        _run(["uv", "run", "python", "-m", "eval.score", rel], BRAIN),
        _run(["uv", "run", "python", "-m", "eval.errors", rel], BRAIN),
    ]
    return "\n\n".join(chunks)


def _write_cut(
    source: dict[str, Any],
    tagged: list[dict[str, Any]],
    drop: set[int],
    path: Path,
) -> list[dict[str, Any]]:
    keep = []
    for row, tag in zip(source["requirements"], tagged, strict=True):
        if not (set(tag["classes"]) & drop):
            keep.append(row)
    out = dict(source)
    out["requirements"] = keep
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    return keep


def _deletion(before: dict[str, Any], kept_ids: set[str]) -> dict[str, int]:
    deleted_matched = [i for i in before["matched_ids"] if i not in kept_ids]
    deleted = before["rows"] - len(kept_ids)
    return {
        "deleted": deleted,
        "matched_deleted": len(deleted_matched),
        "unmatched_deleted": deleted - len(deleted_matched),
    }


def _cut_record(
    name: str,
    path: Path,
    drop: set[int],
    before: dict[str, Any],
    kept: list[dict[str, Any]],
    expected: list[dict[str, Any]],
) -> dict[str, Any]:
    after = _match_stats(kept, expected)
    deletion = _deletion(before, {row["id"] for row in kept})
    log = path.with_suffix(".log")
    official = _official(path)
    when = stamp()
    log.write_text(
        f"{when}\nfile {path.name}\ndrop classes {sorted(drop)}\n"
        f"rows {after['rows']} matched {after['matched']} F2 {after['f2']:.3f}\n"
        f"matched_deleted {deletion['matched_deleted']} "
        f"unmatched_deleted {deletion['unmatched_deleted']}\n\n{official}\n"
    )
    record = {
        "name": name,
        "file": str(path.relative_to(ROOT)),
        "drop": sorted(drop),
        "rows": after["rows"],
        "matched": after["matched"],
        "f2": round(after["f2"], 3),
        **deletion,
        "outside_gold_paragraphs": after["outside_gold_paragraphs"],
        "on_cited_misses": after["on_cited_misses"],
        "off_cited_misses": after["off_cited_misses"],
        "lifts": {k: round(v, 3) for k, v in after["lifts"].items()},
        "why_f2_is_not_1": after["why_f2_is_not_1"],
        "log": str(log.relative_to(ROOT)),
    }
    print(
        f"{name}: rows {record['rows']} matched {record['matched']} F2 {record['f2']:.3f} "
        f"matched_deleted {record['matched_deleted']} "
        f"unmatched_deleted {record['unmatched_deleted']}"
    )
    return record


CUTS: tuple[tuple[str, set[int]], ...] = (
    ("drop1", {1}),
    ("drop12", {1, 2}),
    ("drop123", {1, 2, 3}),
    ("drop1234", {1, 2, 3, 4}),
)


def cmd_sweep() -> int:
    self_check()
    if not TAGS.is_file():
        raise SystemExit(f"missing {TAGS}; run tag first")
    tags = json.loads(TAGS.read_text())["rows"]
    source = load_submission(VOTES7)
    expected = load_submission(EXPECTED)["requirements"]
    if len(tags) != len(source["requirements"]):
        raise SystemExit("tag file does not match votes7 row count")
    before = _match_stats(source["requirements"], expected)
    print(
        f"baseline: rows {before['rows']} matched {before['matched']} "
        f"F2 {before['f2']:.3f} outside {before['outside_gold_paragraphs']}"
    )
    by_class: dict[str, dict[str, int]] = {}
    from eval.score import paragraph_key

    gold_keys = {
        (row["source"]["regulation"], paragraph_key(row["source"].get("paragraph")))
        for row in expected
    }
    matched = set(before["matched_ids"])
    for n in (1, 2, 3, 4):
        by_class[str(n)] = {"outside": 0, "matched": 0, "other_unmatched": 0}
    any_outside = 0
    any_matched = 0
    for row, tag in zip(source["requirements"], tags, strict=True):
        key = (row["source"]["regulation"], paragraph_key(row["source"].get("paragraph")))
        outside = key not in gold_keys
        hit = row["id"] in matched
        if tag["classes"] and outside:
            any_outside += 1
        if tag["classes"] and hit:
            any_matched += 1
        for n in tag["classes"]:
            slot = by_class[str(n)]
            if outside:
                slot["outside"] += 1
            elif hit:
                slot["matched"] += 1
            else:
                slot["other_unmatched"] += 1
    records = []
    for name, drop in CUTS:
        path = OUT / f"rear-lamp-swing-J-{name}.json"
        kept = _write_cut(source, tags, drop, path)
        records.append(_cut_record(name, path, drop, before, kept, expected))
    eligible = [r for r in records if r["matched"] >= 151]
    winner = None
    if eligible:
        winner = max(eligible, key=lambda r: (r["f2"], -r["rows"], -len(r["drop"])))["name"]
    payload = {
        "scored_at": stamp(),
        "spend_usd": 0,
        "baseline": {
            "rows": before["rows"],
            "matched": before["matched"],
            "f2": round(before["f2"], 3),
            "outside_gold_paragraphs": before["outside_gold_paragraphs"],
            "lifts": {k: round(v, 3) for k, v in before["lifts"].items()},
            "why_f2_is_not_1": before["why_f2_is_not_1"],
        },
        "of_outside_rows_classes_catch": any_outside,
        "of_matches_classes_destroy": any_matched,
        "by_class": by_class,
        "cuts": records,
        "winner": winner,
        "winner_rule": "best F2 among cuts that still match at least 151",
    }
    SWEEP.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    print(f"outside caught {any_outside} matches destroyed {any_matched} winner {winner}")
    print(f"wrote {SWEEP}")
    return 0


def _spread(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    if len(rows) <= n:
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)]


def cmd_samples() -> int:
    """Write 15 deleted rows and 10 unmatched kept rows from the winning cut."""
    self_check()
    sweep = json.loads(SWEEP.read_text())
    winner = sweep.get("winner")
    adopted = winner is not None
    if not winner:
        winner = max(sweep["cuts"], key=lambda r: (r["f2"], -r["rows"]))["name"]
    tags = {row["id"]: row for row in json.loads(TAGS.read_text())["rows"]}
    source = load_submission(VOTES7)
    expected = load_submission(EXPECTED)["requirements"]
    drop = dict(CUTS)[winner]
    before = _match_stats(source["requirements"], expected)
    matched = set(before["matched_ids"])
    deleted = []
    kept_unmatched = []
    for row in source["requirements"]:
        tag = tags[row["id"]]
        gone = bool(set(tag["classes"]) & drop)
        item = {
            "id": row["id"],
            "regulation": row["source"]["regulation"],
            "paragraph": row["source"].get("paragraph"),
            "classes": tag["classes"],
            "reasons": tag["reasons"],
            "ambiguous": tag["ambiguous"],
            "matched_before": row["id"] in matched,
            "text": row["text"],
        }
        if gone:
            deleted.append(item)
        elif row["id"] not in matched:
            kept_unmatched.append(item)
    deleted_sorted = sorted(deleted, key=lambda r: (not r["matched_before"], r["id"]))
    chosen_deleted = deleted_sorted[:15]
    chosen_kept = _spread(kept_unmatched, 10)
    path = OUT / "experiments" / "J-read.json"
    path.write_text(
        json.dumps(
            {
                "read_at": stamp(),
                "winner": winner,
                "adopted": adopted,
                "deleted_shown": chosen_deleted,
                "kept_unmatched_shown": chosen_kept,
                "deleted_total": len(deleted),
                "kept_unmatched_total": len(kept_unmatched),
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"deleted {len(deleted)} kept unmatched {len(kept_unmatched)} wrote {path}")
    return 0


def cmd_sunday() -> int:
    """Apply the same text rules to single runs, which did not pass through a vote."""
    self_check()
    expected = load_submission(EXPECTED)["requirements"]
    bases = [
        ("fable", OUT / "rear-lamp-fable.json"),
        ("main", OUT / "rear-lamp-main-a39acab.json"),
        ("sonnet", OUT / "rear-lamp-swing-H-sonnet-w85.json"),
    ]
    records = []
    for label, path in bases:
        if not path.is_file():
            print(f"missing {path}")
            continue
        source = load_submission(path)
        tagged = tag_rows(source["requirements"])
        before = _match_stats(source["requirements"], expected)
        print(
            f"{label} baseline: rows {before['rows']} matched {before['matched']} "
            f"F2 {before['f2']:.3f}"
        )
        for name, drop in CUTS:
            out = OUT / f"rear-lamp-swing-J-{label}-{name}.json"
            kept = _write_cut(source, tagged, drop, out)
            record = _cut_record(f"{label}-{name}", out, drop, before, kept, expected)
            record["base"] = label
            record["base_rows"] = before["rows"]
            record["base_matched"] = before["matched"]
            record["base_f2"] = round(before["f2"], 3)
            records.append(record)
    path = OUT / "experiments" / "J-sunday.json"
    path.write_text(
        json.dumps({"scored_at": stamp(), "spend_usd": 0, "cuts": records}, indent=1) + "\n"
    )
    print(f"wrote {path}")
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "tag"
    if cmd == "tag":
        return cmd_tag()
    if cmd == "sweep":
        return cmd_sweep()
    if cmd == "samples":
        return cmd_samples()
    if cmd == "sunday":
        return cmd_sunday()
    raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
