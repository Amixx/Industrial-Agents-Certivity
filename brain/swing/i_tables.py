"""Lane I: one row per value line of a collapsed EMC table, added to the 7-vote file.

    BRAIN_LLM= PYTHONPATH=. uv run python swing/i_tables.py

No model calls. Value lines are parsed from the UN R10 corpus text. A new row is dropped
when its token Jaccard against a votes7 row on the same paragraph is 0.6 or above and the
two rows cite the same value numbers. Different numbers are a different requirement, the
same rule lane A uses when it refuses to cluster them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from eval import judge

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "brain" / "data" / "corpus" / "UN_R10_base.jsonl"
VOTES = ROOT / "out" / "rear-lamp-swing-A-votes7.json"
SUBMISSION = ROOT / "out" / "rear-lamp-swing-I-tables.json"
LOG = ROOT / "out" / "rear-lamp-swing-I-tables.log"
LINES = ROOT / "out" / "experiments" / "I-lines.json"

_VALUE = re.compile(r"\d+(?:[.,]\d+)*")
_RANGE = re.compile(r"Not applicable|LUF to \d+(?:,\d+)? MHz|\d+(?:,\d+)? to \d+(?:,\d+)? MHz")
_LEVEL = re.compile(r"Not applicable|\d+(?:,\d+)? (?:V/m|mA)")
_PULSE = re.compile(
    r"(?<![0-9a-z])(1|2a|2b|3a|3b) "
    r"([+-]\d+) V ([+-]\d+) V "
    r"(\d+ pulses|1 h) "
    r"(III|II|I) (III|II|I)"
)
METHODS = ("Stripline", "TEM cell", "BCI", "ALSE", "Reverberation chamber")
SIM_DROP = 0.6


def value_numbers(text: str) -> frozenset[str]:
    """Numbers that are values, not paragraph references. Copied from lane A's rule."""
    return frozenset(n for n in _VALUE.findall(text) if n.count(".") < 2)


def jaccard(a: str, b: str) -> float:
    ta, tb = judge.tokens(a), judge.tokens(b)
    return len(ta & tb) / max(1, len(ta | tb))


def paragraph(label: str) -> dict[str, Any]:
    for line in CORPUS.read_text().splitlines():
        row = json.loads(line)
        if row["label"] == label:
            return row
    raise SystemExit(f"corpus has no paragraph {label}")


def _chunk_after(text: str, label: str, stop: str | None) -> str:
    start = text.index(label) + len(label)
    rest = text[start:]
    if stop and stop in rest:
        rest = rest.split(stop, 1)[0]
    return rest


def _take(pattern: re.Pattern[str], text: str, n: int, what: str) -> list[str]:
    found = pattern.findall(text)
    if len(found) < n:
        raise SystemExit(f"expected {n} {what} in {text!r}, found {found}")
    return found[:n]


def table_2_lines(text: str, table: str) -> list[dict[str, str]]:
    """Numeric cells of Table 2a or 2b. 'Not applicable' is not a value line."""
    below_ranges = _take(
        _RANGE, _chunk_after(text, "Frequency range below 2 GHz", "Test level"), 5, "ranges"
    )
    below_levels = _take(
        _LEVEL, _chunk_after(text, "Test level below 2 GHz", "Frequency range"), 5, "levels"
    )
    above_ranges = _take(
        _RANGE, _chunk_after(text, "Frequency range above 2 GHz", "Test level"), 5, "ranges"
    )
    above_levels = _take(_LEVEL, _chunk_after(text, "Test level above 2 GHz", None), 5, "levels")
    band = {
        "2a": "the test level in over 90 per cent of the 20 to 6,000 MHz frequency band",
        "2b": "the minimum test level over the whole 20 to 6,000 MHz frequency band",
    }[table]
    lines = []
    for where, ranges, levels in (
        ("below 2 GHz", below_ranges, below_levels),
        ("above 2 GHz", above_ranges, above_levels),
    ):
        for method, rng, level in zip(METHODS, ranges, levels, strict=True):
            if level == "Not applicable" or rng == "Not applicable":
                continue
            lines.append(
                {
                    "paragraph": "6.8.2.1",
                    "quote": f"Table {table} {method} {where} {rng} {level}",
                    "text": (
                        f"The immunity of an ESA to electromagnetic radiation by the {method} "
                        f"method shall be tested at a level of {level} in the {rng} frequency "
                        f"range, {band} (Table {table})."
                    ),
                }
            )
    return lines


def table_3_lines(text: str) -> list[dict[str, str]]:
    """Table 3a starting profile and Table 3b pulses, one line per supply system."""
    if "B D Starting profile" not in text:
        raise SystemExit("Table 3a letters B and D were not where the table puts them")
    start = re.search(
        r"Starting profile II II 10 pulses \(for ESA which shall be operational during engine "
        r"start phases\) C \(for other ESA\)",
        text,
    )
    if not start:
        raise SystemExit("Table 3a starting-profile line was not in the source")
    proviso = (
        "Starting profile is only applicable to ESAs that could be installed in vehicles with "
        "internal combustion engines which are started with a 12V/24V starter motor."
    )
    if proviso not in text:
        raise SystemExit("starting-profile proviso was not in the source")
    pulses = _PULSE.findall(text)
    if len(pulses) != 5:
        raise SystemExit(f"expected 5 pulses in Table 3b, found {pulses}")
    subject = "The immunity of an ESA to transient disturbances conducted along supply lines"
    lines = []
    for system in ("12 V", "24 V"):
        lines.append(
            {
                "paragraph": "6.9.1",
                "quote": start.group(0),
                "text": (
                    f"{subject} shall meet, for the starting profile on a {system} system, "
                    f"immunity test level II and 10 pulses, with functional status classification "
                    f"B for functions related to immunity related functions for an ESA which shall "
                    f"be operational during engine start phases and C for other ESA, and "
                    f"functional status classification D for functions not related to immunity "
                    f"related functions (Table 3a). {proviso}"
                ),
            }
        )
    for pulse, v12, v24, duration, related, unrelated in pulses:
        for system, volts in (("12 V", f"{v12} V"), ("24 V", f"{v24} V")):
            lines.append(
                {
                    "paragraph": "6.9.1",
                    "quote": f"{pulse} {v12} V {v24} V {duration} {related} {unrelated}",
                    "text": (
                        f"{subject} shall meet, for test pulse {pulse} on a {system} system, "
                        f"an immunity test level of {volts} and a test duration of {duration}, "
                        f"with functional status classification {related} for functions related "
                        f"to immunity related functions and {unrelated} for functions not related "
                        f"to immunity related functions (Table 3b)."
                    ),
                }
            )
    return lines


def table_1_lines(text: str) -> list[dict[str, str]]:
    found = re.search(
        r"Positive ([+-]\d+) V ([+-]\d+) V Negative ([+-]\d+) V ([+-]\d+) V",
        text,
    )
    if not found:
        raise SystemExit("Table 1 pulse amplitudes were not in the source")
    pos12, pos24, neg12, neg24 = found.groups()
    rows = [
        ("positive", "12 V", f"{pos12} V"),
        ("positive", "24 V", f"{pos24} V"),
        ("negative", "12 V", f"{neg12} V"),
        ("negative", "24 V", f"{neg24} V"),
    ]
    return [
        {
            "paragraph": "6.7.1",
            "quote": f"{polarity} {volts}",
            "text": (
                "When tested by the method(s) according to ISO 7637-2 as described in Annex 10 "
                f"(Table 1), the {polarity} pulse amplitude for vehicles with {system} systems "
                f"shall not exceed {volts}."
            ),
        }
        for polarity, system, volts in rows
    ]


def modulation_lines(text: str) -> list[dict[str, str]]:
    """The three Annex 9 3.1 clauses. votes7 already has them; the filter should drop these."""
    body = re.search(r"The test signal modulation shall be: (.+?) If not otherwise", text)
    if not body:
        raise SystemExit("Annex 9 3.1 modulation list was not in the source")
    parts = re.findall(r"\([abc]\) (.+?)(?:; and|;|\.)", body.group(1))
    if len(parts) != 3:
        raise SystemExit(f"expected 3 modulation clauses, found {parts}")
    return [
        {
            "paragraph": "Annex 9 3.1",
            "quote": part.strip(),
            "text": f"The test signal modulation shall be {part.strip().rstrip('.')}.",
        }
        for part in parts
    ]


def nearest(text: str, existing: list[str]) -> tuple[float, bool]:
    """Highest Jaccard, and whether that row also cites the same value numbers."""
    best, same = 0.0, False
    nums = value_numbers(text)
    for old in existing:
        sim = jaccard(text, old)
        if sim > best:
            best, same = sim, value_numbers(old) == nums
    return best, same


def paraphrase(text: str, existing: list[str]) -> bool:
    nums = value_numbers(text)
    for old in existing:
        if jaccard(text, old) >= SIM_DROP and value_numbers(old) == nums:
            return True
    return False


def candidates() -> list[dict[str, Any]]:
    by_label = {
        "6.7.1": table_1_lines,
        "6.8.2.1": None,
        "6.9.1": table_3_lines,
        "Annex 9 3.1": modulation_lines,
    }
    out: list[dict[str, Any]] = []
    for label, builder in by_label.items():
        src = paragraph(label)
        if label == "6.8.2.1":
            # The prose mentions both tables before the grids. Cut at the grid headings.
            grid_a = src["text"].index("Table 2a Test Level")
            grid_b = src["text"].index("Table 2b Minimum")
            made = table_2_lines(src["text"][grid_a:grid_b], "2a")
            made += table_2_lines(src["text"][grid_b:], "2b")
        else:
            assert builder is not None
            made = builder(src["text"])
        for row in made:
            for token in value_numbers(row["text"]):
                # "2" from "2a" and "Table 2a" is in the source as a digit. Every other value too.
                bare = token.replace(",", "")
                if token not in src["text"] and bare not in src["text"].replace(",", ""):
                    raise SystemExit(f"{label}: value {token} is not in the source text")
            row["page"] = src["page"]
            row["version"] = src["version"]
            out.append(row)
    return out


def build() -> None:
    votes = json.loads(VOTES.read_text())
    existing: dict[str, list[str]] = {}
    confidence: dict[str, float] = {}
    for req in votes["requirements"]:
        label = req["source"]["paragraph"]
        existing.setdefault(label, []).append(req["text"])
        confidence[label] = max(confidence.get(label, 0.0), float(req.get("confidence") or 0.0))

    records = []
    added = []
    for row in candidates():
        sim, same_numbers = nearest(row["text"], existing.get(row["paragraph"], []))
        drop = paraphrase(row["text"], existing.get(row["paragraph"], []))
        records.append(
            {
                **row,
                "nearest_jaccard": round(sim, 3),
                "same_numbers": same_numbers,
                "dropped": drop,
            }
        )
        if drop:
            continue
        added.append(
            {
                "text": row["text"],
                "source": {
                    "regulation": "UN R10",
                    "version": row["version"],
                    "page": row["page"],
                    "paragraph": row["paragraph"],
                },
                "confidence": round(confidence.get(row["paragraph"], 0.0), 3),
                "quote": row["quote"],
            }
        )

    requirements = list(votes["requirements"])
    start = len(requirements)
    for i, req in enumerate(added, start=start + 1):
        requirements.append({"id": f"R-{i:04d}", **req})
    submission = {
        "team_id": votes["team_id"],
        "case_id": votes["case_id"],
        "requirements": requirements,
    }
    SUBMISSION.write_text(json.dumps(submission, indent=1, ensure_ascii=False) + "\n")
    LINES.write_text(json.dumps(records, indent=1, ensure_ascii=False) + "\n")

    kept = [r for r in records if not r["dropped"]]
    dropped = [r for r in records if r["dropped"]]
    by_kept: dict[str, int] = {}
    by_drop: dict[str, int] = {}
    for r in kept:
        by_kept[r["paragraph"]] = by_kept.get(r["paragraph"], 0) + 1
    for r in dropped:
        by_drop[r["paragraph"]] = by_drop.get(r["paragraph"], 0) + 1
    lines = [
        "lane I table split. No model call. Spend $0.",
        f"votes7 rows {start}. Value lines parsed {len(records)}. Kept {len(kept)}. "
        f"Dropped as paraphrases {len(dropped)}. Union rows {len(requirements)}.",
        f"kept by paragraph: {by_kept}",
        f"dropped by paragraph: {by_drop}",
        "Drop rule: token Jaccard >= 0.6 and the same value numbers, against a votes7 row "
        "on the same paragraph.",
    ]
    for r in records:
        mark = "drop" if r["dropped"] else "keep"
        lines.append(f"  {mark} {r['paragraph']} j={r['nearest_jaccard']} {r['text']}")
    LOG.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:6]))


if __name__ == "__main__":
    build()
