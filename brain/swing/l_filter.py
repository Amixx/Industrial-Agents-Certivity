"""Lane L of task 08: four-class skip filter. Text rules only, no model calls.

The classes are the shared brief in ``brain/docs/todo/08-complex.md``. Gold rows and the
local judge are not inputs. ``sweep`` uses them afterwards to report what a cut did.

    BRAIN_LLM= PYTHONPATH=. uv run python swing/l_filter.py tag SUBMISSION -o TAGS.json
    BRAIN_LLM= PYTHONPATH=. uv run python swing/l_filter.py cut SUBMISSION --drop 1,2 -o OUT.json
    BRAIN_LLM= PYTHONPATH=. uv run python swing/l_filter.py sweep SUBMISSION
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = ROOT / "cases" / "dev-rear-lamp" / "expected.json"

# A pass criterion states the result of a test. Those rows stay, even when the
# same sentence names the test. Class 1 is the step: prepare, immerse, spray,
# wipe, or measure.
_PASS = re.compile(
    r"\bshall not\b|"
    r"\bno water shall\b|"
    r"\bshall prevent\b|"
    r"\bshall comply with\b|"
    r"\bshall meet\b|"
    r"\bshall be below\b|"
    r"\bnot less than\b|"
    r"\bnot exceed\b|"
    r"\bequal to or greater\b|"
    r"\bnot show any\b|"
    r"\bnot be considered to have passed\b|"
    r"\bshall be at least\b|"
    r"\bremain constant at\b|"
    r"\blimit\b.{0,40}\bshall\b",
    re.I,
)

_PROCEDURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("immerse", re.compile(r"\bimmers?e[ds]?\b|\bimmersion test\b", re.I)),
    ("spray", re.compile(r"water spray|saline mist|salt spray", re.I)),
    ("wipe", re.compile(r"\bwiped?\b|cotton cloth", re.I)),
    (
        "prepare",
        re.compile(
            r"sample shall be allowed|allowed to dry|stripped of all removable|"
            r"shall be kept for \d+|be subjected (?:successively )?to|"
            r"state of charge \(SOC\)|shall be in charging mode during|"
            r"tested at rated current|current shall be set to",
            re.I,
        ),
    ),
    (
        "test-step",
        re.compile(
            r"test shall last|test shall be repeated|shall be repeated after turning|"
            r"lightly shaken|shall be inspected visually|"
            r"correction factor .{0,40}shall be applied|"
            r"shall be applied to the supply lines|"
            r"frequency step size",
            re.I,
        ),
    ),
    (
        "measure",
        re.compile(
            r"shall be measured by the method|shall be measured according to|"
            r"shall be measured as described|"
            r"measurements of the .{0,80}shall be (?:made|repeated)|"
            r"all measurements .{0,80}shall be made|"
            r"shall be measured with the light source continuously|"
            r"measurement results .{0,40}shall be added together|"
            r"shall be measured inside the field|"
            r"illuminated by CIE|"
            r"direction of observation shall be shifted|"
            r"shall be placed in the position|shall be rotated about|may be rotated about|"
            r"shall be verified|should be verified",
            re.I,
        ),
    ),
)

# Widths, heights and angles stay. A count ("two in number") is not one of those.
_KEPT_DIMENSION = re.compile(
    r"°|º|\bdegrees?\b|\bmm\b|above the ground|geometric visibility",
    re.I,
)

_VARIANT = re.compile(
    r"LED substitute|"
    r"fail-safe|"
    r"optional (?:stop )?lamps?|"
    r"optional devices|"
    r"two optional|"
    r"electronic light source control gear|"
    r"variable luminous intensity|"
    r"variable intensity control|"
    r"secondary operating mode|"
    r"interdependent lamp|"
    r"Unique Identifier|"
    r"reciprocally incorporated|"
    r"not marked \"TOP\"|"
    r"marked \"TOP\"|"
    r"apparent surface of the lamp is hidden|"
    r"more than 50 per cent hidden|"
    r"special power supply|"
    r"does not include an electronic oscillator|"
    r"are not switched, contain no switches|"
    r"light source module|"
    r"non-replaceable light source|"
    r"mounting height|"
    r"exclusively in a pair|"
    r"verified only up to an angle|"
    r"grouped, combined|"
    r"movable component|"
    r"single approval mark",
    re.I,
)

_LEAD = re.compile(
    r"^(?:If |Where |When |In the case |In case |For a |For the two optional )",
    re.I,
)

# "The normal rules still apply" is not a variant the sentence exists only to cover.
_UMBRELLA = re.compile(
    r"all requirements regarding|"
    r"requirements regarding colour|"
    r"requirements of the lamp shall be fulfilled|"
    r"photometric and colorimetric requirements of the lamp shall be fulfilled|"
    r"in compliance with the technical provisions|"
    r"geometric visibility requirements shall be fulfilled",
    re.I,
)

# The demand itself has to be the reference. "Shall meet the requirements" with no
# table, paragraph, section or annex is a requirement of its own, not a pointer.
_POINTER = re.compile(
    r"shall conform to|"
    r"shall comply with (?:paragraph|paragraphs|section|sections|annex)|"
    r"shall meet the requirements in Table|"
    r"shall meet the requirements contained in sections?|"
    r"requirements set forth in (?:Annex|paragraph|section)|"
    r"requirements as specified in paragraphs?|"
    r"shall be in accordance with paragraph|"
    r"deemed to comply with|"
    r"shall be equal to the number indicated|"
    r"be type approved according to the corresponding|"
    r"only if the conditions specified in paragraphs|"
    r"as specified in Table \d|"
    r"provisions of paragraphs [\d.]+ and [\d.]+ shall not apply",
    re.I,
)

_OWN_VALUE = re.compile(
    r"°|º|\bmm\b|\bcd\b|\bdB\b|\bkHz\b|\bMHz\b|"
    r"\b\d+(?:[.,]\d+)?\s*(?:V|volt|per cent|%|min\b|minute|hour)|"
    r"\b(?:at least|not less than|not more than|shall not exceed|equal to or greater)\s+\d|"
    r"\b(?:red|amber|white)\b",
    re.I,
)


def procedure(text: str) -> str | None:
    if _PASS.search(text):
        return None
    for name, pattern in _PROCEDURES:
        if pattern.search(text):
            return name
    return None


def installation(text: str) -> str | None:
    """Orientation, count, bare presence, or at the rear. Widths, heights and angles stay."""
    if _KEPT_DIMENSION.search(text):
        return None
    if re.search(r"oriented rearwards|oriented towards the rear|oriented forwards", text, re.I):
        return "orientation"
    if re.search(r"\bshall be present\b|\bshall be mandatory\b", text, re.I):
        return "presence"
    if re.search(r"\bin number\b|the number of .{0,40}shall be\b", text, re.I):
        return "count"
    if re.search(r"\bshall be equal to the number indicated\b", text, re.I):
        return "count"
    if re.search(r"\b(?:one|two|three|four)\b.{0,80}\bshall be fitted\b", text, re.I):
        if re.search(r"in such a way|with light sources|symmetrically", text, re.I):
            return None
        return "count"
    if re.search(r"\bshall be fitted on\b", text, re.I):
        if re.search(r"in such a way|with light sources|symmetrically", text, re.I):
            return None
        return "presence"
    if re.search(
        r"positioned at the rear of the vehicle|shall be at the rear of the vehicle",
        text,
        re.I,
    ):
        return "at-the-rear"
    return None


def _stripped(text: str) -> str:
    return re.sub(r"^If not otherwise specified,\s*", "", text, flags=re.I)


def variant(text: str) -> str | None:
    """The sentence exists only to cover equipment it introduces as optional, alternative or absent.

    A requirement on the base lamp, with the variant named only in an exception, stays.
    """
    if re.match(r"Except where the rear lamp has non-replaceable", text, re.I):
        if re.search(r"LED substitute", text, re.I):
            return "led-substitute"
        return None

    parts = re.split(r"\bexcept\b", text, maxsplit=1, flags=re.I)
    before = parts[0]
    if len(parts) == 2 and _VARIANT.search(parts[1]) and not _VARIANT.search(before):
        return None
    if _UMBRELLA.search(text):
        return None

    if re.search(r"only for use on a vehicle fitted with a tell-tale", text, re.I):
        return "only-with-tell-tale"
    if re.match(r"An electronic light source control gear", text, re.I):
        return "control-gear"
    if re.search(r"special power supply", text, re.I):
        return "special-supply"
    if re.search(r"\bTOP\b", text) and re.search(
        r"shall bear the word|not marked|marked \"TOP\"", text
    ):
        return "top-mark"
    if re.search(r"shall not apply", text, re.I) and _VARIANT.search(text):
        return "variant-exemption"
    if re.search(r"single approval mark", text, re.I) and re.search(
        r"grouped, combined", text, re.I
    ):
        return "grouped-mark"

    stripped = _stripped(text)
    if _LEAD.search(stripped) and _VARIANT.search(before if before.strip() else stripped):
        match = _VARIANT.search(stripped)
        label = match.group(0).lower() if match else "variant"
        return f"variant:{label}"
    if re.search(r"\boptional (?:stop )?lamps?\b|\btwo optional\b", before, re.I):
        return "optional-fitment"
    return None


def pointer(text: str) -> str | None:
    """The only demand is a table, paragraph or section, and the row states no value of its own."""
    if _OWN_VALUE.search(text):
        return None
    if _POINTER.search(text):
        return "pointer"
    return None


def classify(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    if reason := procedure(text):
        found.append((1, reason))
    if reason := installation(text):
        found.append((2, reason))
    if reason := variant(text):
        found.append((3, reason))
    if reason := pointer(text):
        found.append((4, reason))
    return found


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def tag_rows(submission: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for req in submission["requirements"]:
        found = classify(req["text"])
        source = req["source"]
        rows.append(
            {
                "id": req["id"],
                "classes": [number for number, _ in found],
                "why": [reason for _, reason in found],
                "regulation": source.get("regulation"),
                "paragraph": source.get("paragraph"),
                "text": req["text"],
            }
        )
    return rows


def parse_drop(spec: str) -> set[int]:
    text = spec.strip().lower()
    if text in {"all", "1,2,3,4", "1234"}:
        return {1, 2, 3, 4}
    if text in {"1+2+3", "123"}:
        return {1, 2, 3}
    if text in {"1+2", "12"}:
        return {1, 2}
    numbers = {int(part) for part in re.split(r"[^0-9]+", text) if part}
    unknown = numbers - {1, 2, 3, 4}
    if not numbers or unknown:
        raise SystemExit(f"drop set must be classes 1 to 4, got {spec!r}")
    return numbers


def cut(submission: dict[str, Any], drop: set[int]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return a copy of the submission without rows in `drop`, and the deleted tag rows."""
    kept: list[dict[str, Any]] = []
    deleted: list[dict[str, Any]] = []
    for req in submission["requirements"]:
        found = classify(req["text"])
        classes = {number for number, _ in found}
        if classes & drop:
            source = req["source"]
            deleted.append(
                {
                    "id": req["id"],
                    "classes": sorted(classes),
                    "why": [reason for _, reason in found],
                    "regulation": source.get("regulation"),
                    "paragraph": source.get("paragraph"),
                    "text": req["text"],
                }
            )
        else:
            kept.append(req)
    out = dict(submission)
    out["requirements"] = kept
    return out, deleted


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")


def deletion_report(submission: dict[str, Any], deleted: list[dict[str, Any]]) -> dict[str, int]:
    """How the local judge and the gold paragraphs saw the deleted rows. Not used to drop them."""
    from eval import judge
    from eval.score import paragraph_key

    expected = load(EXPECTED)["requirements"]
    submitted = submission["requirements"]
    matched = {index for index, _, _ in judge.match(submitted, expected)}
    gold = {
        (row["source"]["regulation"], paragraph_key(row["source"].get("paragraph")))
        for row in expected
    }
    by_id = {row["id"]: index for index, row in enumerate(submitted)}
    deleted_matched = 0
    outside = 0
    inside_unmatched = 0
    for row in deleted:
        index = by_id[row["id"]]
        key = (
            submitted[index]["source"]["regulation"],
            paragraph_key(submitted[index]["source"].get("paragraph")),
        )
        if index in matched:
            deleted_matched += 1
        elif key not in gold:
            outside += 1
        else:
            inside_unmatched += 1
    return {
        "deleted": len(deleted),
        "deleted_matched": deleted_matched,
        "deleted_unmatched": len(deleted) - deleted_matched,
        "deleted_outside_gold_paragraphs": outside,
        "deleted_inside_gold_unmatched": inside_unmatched,
    }


def cmd_tag(args: argparse.Namespace) -> int:
    submission = load(Path(args.submission))
    rows = tag_rows(submission)
    counts = {str(number): 0 for number in (1, 2, 3, 4)}
    for row in rows:
        for number in row["classes"]:
            counts[str(number)] += 1
    payload = {
        "base": str(Path(args.submission)),
        "rows_in": len(rows),
        "tagged": sum(1 for row in rows if row["classes"]),
        "class_counts": counts,
        "rows": rows,
    }
    write_json(Path(args.output), payload)
    print(
        f"rows {len(rows)}, tagged {payload['tagged']}, "
        f"class1 {counts['1']}, class2 {counts['2']}, "
        f"class3 {counts['3']}, class4 {counts['4']}"
    )
    print(f"wrote {args.output}")
    return 0


def cmd_cut(args: argparse.Namespace) -> int:
    submission = load(Path(args.submission))
    drop = parse_drop(args.drop)
    filtered, deleted = cut(submission, drop)
    write_json(Path(args.output), filtered)
    print(
        f"drop {sorted(drop)}: kept {len(filtered['requirements'])}, "
        f"deleted {len(deleted)}, wrote {args.output}"
    )
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    from eval import judge
    from eval.score import fbeta

    submission = load(Path(args.submission))
    expected = load(EXPECTED)
    out_dir = Path(args.out_dir)
    sets = [("drop1", {1}), ("drop12", {1, 2}), ("drop123", {1, 2, 3}), ("drop1234", {1, 2, 3, 4})]
    summary: list[dict[str, Any]] = []
    for name, drop in sets:
        filtered, deleted = cut(submission, drop)
        path = out_dir / f"rear-lamp-swing-L-{name}.json"
        write_json(path, filtered)
        report = deletion_report(submission, deleted)
        # Same F2 as eval.score: 5 * matched / (4 * expected + submitted), via P and R.
        matched = len(judge.match(filtered["requirements"], expected["requirements"]))
        rows = len(filtered["requirements"])
        precision = matched / rows if rows else 0.0
        recall = matched / len(expected["requirements"])
        report.update(
            {
                "file": str(path.relative_to(ROOT)),
                "drop": sorted(drop),
                "rows": rows,
                "matched": matched,
                "f2": round(fbeta(precision, recall), 3),
            }
        )
        summary.append(report)
        log_path = path.with_suffix(".log")
        log_path.write_text(
            "\n".join(
                [
                    f"file: {path.name}",
                    f"base: {args.submission}",
                    f"drop classes: {sorted(drop)}",
                    f"rows: {rows}",
                    f"local matched: {matched}",
                    f"local F2: {report['f2']}",
                    f"deleted: {report['deleted']}",
                    f"deleted matched on the unfiltered file: {report['deleted_matched']}",
                    f"deleted unmatched: {report['deleted_unmatched']}",
                    "spend: $0",
                    "method: brain/swing/l_filter.py text rules, no API call",
                    "",
                ]
            )
        )
        print(
            f"{name}: rows {rows}, matched {matched}, F2 {report['f2']}, "
            f"deleted {report['deleted']} "
            f"(matched {report['deleted_matched']}, unmatched {report['deleted_unmatched']}, "
            f"outside gold paragraphs {report['deleted_outside_gold_paragraphs']})"
        )
    write_json(ROOT / "out" / "experiments" / "L-sweep.json", {"cuts": summary})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    tag = sub.add_parser("tag", help="write a class for every row")
    tag.add_argument("submission")
    tag.add_argument("-o", "--output", required=True)
    tag.set_defaults(func=cmd_tag)

    cut_parser = sub.add_parser("cut", help="write a submission with the named classes removed")
    cut_parser.add_argument("submission")
    cut_parser.add_argument("--drop", required=True, help="1 or 1,2 or 1,2,3 or 1,2,3,4")
    cut_parser.add_argument("-o", "--output", required=True)
    cut_parser.set_defaults(func=cmd_cut)

    sweep = sub.add_parser("sweep", help="write the four cuts and the deletion counts")
    sweep.add_argument("submission")
    sweep.add_argument("--out-dir", default=str(ROOT / "out"))
    sweep.set_defaults(func=cmd_sweep)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
