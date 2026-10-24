"""Check that every cited (regulation, page, paragraph) of an expected file exists in the corpus.

uv run python -m eval.gold_check [../cases/dev-rear-lamp/expected.json]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from brain.ingest import load
from brain.models import Paragraph
from brain.paths import CASES

from .score import paragraph_key


def missing(expected: dict, corpus: dict[str, list[Paragraph]]) -> list[tuple[str, str, int, list]]:
    """Gold citations whose paragraph label is not parsed on the cited page."""
    out, seen = [], set()
    for r in expected["requirements"]:
        s = r["source"]
        key = paragraph_key(re.sub(r"\s*Table.*$", "", s.get("paragraph") or ""))
        if (s["regulation"], key, s["page"]) in seen:
            continue
        seen.add((s["regulation"], key, s["page"]))
        hits = [p for p in corpus[s["regulation"]] if paragraph_key(p.label) == key]
        if not any(p.page == s["page"] for p in hits):
            out.append(
                (s["regulation"], s.get("paragraph"), s["page"], [(p.label, p.page) for p in hits])
            )
    return out


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]) if args else CASES / "dev-rear-lamp" / "expected.json"
    expected = json.loads(path.read_text())
    corpus = {r: load(r) for r in {x["source"]["regulation"] for x in expected["requirements"]}}
    miss = missing(expected, corpus)
    total = len(
        {
            (r["source"]["regulation"], r["source"].get("paragraph"), r["source"]["page"])
            for r in expected["requirements"]
        }
    )
    print(f"{total - len(miss)}/{total} cited paragraphs found on their page")
    for m in miss:
        print("  missing", m)
    return 1 if miss else 0


if __name__ == "__main__":
    raise SystemExit(main())
