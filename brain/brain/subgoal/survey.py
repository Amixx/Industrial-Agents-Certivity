"""The sub-goal diff on every base and latest pair in the corpus, and on synthetic edits.

    uv run python -m brain.subgoal.survey              # one row per regulation with both versions
    uv run python -m brain.subgoal.survey --synthetic  # the six synthetic edits per regulation
    uv run python -m brain.subgoal.survey --main-goal "UN R148" "UN R10" "UN R48"

The survey counts units by link kind: amended, new, deleted, and moved (unchanged text under a
new label). The synthetic pairs take a parsed regulation and apply one edit whose answer is known.
--main-goal runs the whole diff from base to latest PDF with the main goal's deterministic rows
(../out/rear-lamp-deterministic.json) as the old requirements, and prints every change, to read.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter

from brain.ingest import CORPUS, load
from brain.models import Paragraph
from brain.paths import INDEX, PDFS, ROOT
from brain.subgoal import align, bare, diff_assessment, kind, sentences, units

Expected = set[tuple[str, str]]
NUMBER = re.compile(r"(?<![\w.])\d+(?![\w])")  # a free-standing number, not a footnote marker


def _unique(paragraphs: list[Paragraph]) -> list[int]:
    """Indexes of main-body paragraphs with two or more units, each unit's text unique."""
    seen = Counter(tuple(bare(u.text)) for u in units(paragraphs))
    return [
        k
        for k, p in enumerate(paragraphs)
        if not p.annex
        and len(sentences(p.text)) >= 2
        and all(seen[tuple(bare(s))] == 1 for s in sentences(p.text))
        and len(bare(p.text)) >= 12
    ]


def _relabel(p: Paragraph, label: str) -> Paragraph:
    return p.model_copy(update={"label": label, "number": label, "id": f"{p.id}~{label}"})


def synthetic_pairs(
    paragraphs: list[Paragraph],
) -> list[tuple[str, list[Paragraph], list[Paragraph], Expected]]:
    """(name, old, new, expected (old label or "", kind) of every non-unchanged link)."""
    old = list(paragraphs)
    picks = _unique(old)
    a, b = picks[len(picks) // 3], picks[2 * len(picks) // 3]
    pairs: list[tuple[str, list[Paragraph], list[Paragraph], Expected]] = []

    target = old[a].label
    renumbered = [
        _relabel(p, "9" + p.label) if p.label == target or p.label.startswith(target + ".") else p
        for p in old
    ]
    pairs.append(("renumber", old, renumbered, set()))

    inserted = old[a].model_copy(
        update={
            "label": old[a].label + ".99",
            "id": old[a].id + ".99",
            "heading": None,
            "text": "The test device shall withstand a static load of 777 N for 9 s.",
        }
    )
    pairs.append(("insert", old, old[: a + 1] + [inserted] + old[a + 1 :], {("", "new")}))

    pairs.append(("delete", old, old[:b] + old[b + 1 :], {(old[b].label, "deleted")}))

    numbered = list(old)
    k = next(k for k in picks if NUMBER.search(old[k].text[len(old[k].heading or "") :]))
    text = old[k].text
    m = NUMBER.search(text[len(old[k].heading or "") :])
    assert m is not None
    start = len(old[k].heading or "") + m.start()
    end = len(old[k].heading or "") + m.end()
    numbered[k] = old[k].model_copy(
        update={"text": text[:start] + str(int(m.group()) + 1) + text[end:]}
    )
    pairs.append(("number", old, numbered, {(old[k].label, "amended")}))

    parts = sentences(old[b].text)
    head = old[b].model_copy(update={"text": parts[0]})
    tail = old[b].model_copy(
        update={
            "label": old[b].label + ".98",
            "id": old[b].id + ".98",
            "heading": None,
            "text": " ".join(parts[1:]),
        }
    )
    pairs.append(("split", old, old[:b] + [head, tail] + old[b + 1 :], set()))

    spaced = [p.model_copy(update={"text": p.text.replace(" ", "  \n ")}) for p in old]
    pairs.append(("whitespace", old, spaced, set()))
    return pairs


def pairs_in_corpus() -> list[str]:
    """Regulations with both a base and a latest version parsed."""
    out = []
    for entry in json.loads(INDEX.read_text()):
        regulation = entry["regulation"]
        stem = regulation.replace(" ", "_")
        if all((CORPUS / f"{stem}_{role}.jsonl").exists() for role in ("base", "latest")):
            out.append(regulation)
    return out


def survey() -> None:
    print("| Regulation | Paragraphs old / new | Amended | New | Deleted | Moved | Seconds |")
    print("|---|---|---|---|---|---|---|")
    for regulation in pairs_in_corpus():
        old, new = load(regulation, "base"), load(regulation, "latest")
        start = time.monotonic()
        links = align(old, new)
        seconds = time.monotonic() - start
        counts = Counter(kind(link) for link in links)
        moved = sum(
            1
            for link in links
            if kind(link) == "unchanged"
            and link.old
            and link.new
            and link.old.label != link.new.label
        )
        print(
            f"| {regulation} | {len(old)} / {len(new)} | {counts['amended']} | {counts['new']} | "
            f"{counts['deleted']} | {moved} | {seconds:.1f} |"
        )


def synthetic() -> None:
    for regulation in pairs_in_corpus():
        for name, old, new, expected in synthetic_pairs(load(regulation, "base")):
            found = {
                (link.old.label if link.old else "", kind(link))
                for link in align(old, new)
                if kind(link) != "unchanged"
            }
            print(f"{regulation:10} {name:10} {'ok' if found == expected else f'got {found}'}")


def main_goal(regulations: list[str]) -> None:
    rows = json.loads((ROOT / "out" / "rear-lamp-deterministic.json").read_text())["requirements"]
    for regulation in regulations:
        mine = [r for r in rows if r["source"]["regulation"] == regulation]
        requirements = [
            {"id": f"R-{k + 1:03d}", "text": r["text"], "source": r["source"]}
            for k, r in enumerate(mine)
        ]
        stem = regulation.replace(" ", "_")
        old_pdf = next((PDFS / stem / "base").glob("*.pdf"))
        new_pdf = next((PDFS / stem / "latest").glob("*.pdf"))
        start = time.monotonic()
        changes = diff_assessment(old_pdf, new_pdf, requirements)
        counts = Counter(c["change"] for c in changes)
        seconds = time.monotonic() - start
        print(f"== {regulation}: {len(requirements)} requirements, {dict(counts)}, {seconds:.1f} s")
        for c in changes:
            print(f"  {c['change']:8} {c.get('requirement_id') or '':6} {c['reason'][:230]}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--synthetic", action="store_true", help="run the six synthetic edits instead")
    ap.add_argument("--main-goal", nargs="+", metavar="REGULATION", help="diff with main-goal rows")
    args = ap.parse_args(argv)
    if args.main_goal:
        main_goal(args.main_goal)
    elif args.synthetic:
        synthetic()
    else:
        survey()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
