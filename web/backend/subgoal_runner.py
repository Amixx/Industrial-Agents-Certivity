"""Runs the sub-goal diff (`brain.subgoal`) for the web backend, inside the brain's own environment.

    brain/.venv/bin/python web/backend/subgoal_runner.py identify PDF
    brain/.venv/bin/python web/backend/subgoal_runner.py diff REQUEST OUT

`identify` prints {"regulation", "version"} as read from the PDF's first page (either may be
null). `diff` reads REQUEST ({"old_pdf", "new_pdf", "regulation", "to_version", "requirements"})
and writes OUT: the requirement changes of `brain.subgoal`, the paragraph diff of the regulation
as hunks, and the counts the app shows. No model, no network.

A hunk is one changed paragraph of the new version (or a deleted one of the old): its units in
order, each unchanged, amended (with word segments), new or deleted. Paragraphs whose units are
all unchanged are left out, renumbered ones are only counted.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pymupdf
from brain.ingest import parse_pdf
from brain.subgoal import Link, Op, Span, align, bare, diff_parsed, kind, units

FIRST_PAGE = re.compile(r"\bUN (R\d+|GTR \d+)(?:, version (\d+\.\d+\.\d+))?")


def identify(pdf: Path) -> dict[str, str | None]:
    with pymupdf.open(pdf) as doc:
        text = doc[0].get_text() if len(doc) else ""
    m = FIRST_PAGE.search(text)
    return {"regulation": f"UN {m[1]}" if m else None, "version": m[2] if m else None}


def segments(old: str, new: str, ops: tuple[Op, ...]) -> list[list[str]]:
    """[kind, text] runs of an amended unit, kind "same", "del" or "ins", from its substantive
    word ops. Edits that only change punctuation or spelling keep the old words."""
    words = old.split()
    out: list[list[str]] = []

    def push(k: str, text: str) -> None:
        if not text:
            return
        if out and out[-1][0] == k:
            out[-1][1] += " " + text
        else:
            out.append([k, text])

    i = 0
    for tag, before, after, at in sorted(ops, key=lambda o: o[3]):
        push("same", " ".join(words[i:at]))
        i = at
        if tag in ("replace", "delete"):
            n = len(before.split())
            push("del", " ".join(words[i : i + n]))
            i += n
        if tag in ("replace", "insert"):
            push("ins", after)
    push("same", " ".join(words[i:]))
    return out


def ancestors(label: str) -> list[str]:
    """The label and its parents: "Annex 3 2.1" gives itself, "Annex 3 2", "Annex 3"."""
    m = re.match(r"^((?:Annex \d+(?: Part \d+)?|Appendix \d+)\s*)?(.*)$", label)
    prefix, number = (m[1] or "", m[2]) if m else ("", label)
    parts = number.split(".") if number else []
    out = [f"{prefix}{'.'.join(parts[:k])}" for k in range(len(parts), 0, -1)]
    return out + ([prefix.strip()] if prefix else [])


def hunks(links: list[Link], headings: dict[str, str]) -> tuple[list[dict[str, Any]], int]:
    """The changed paragraphs, in new-document order, and the count of renumbered ones."""
    by_new: dict[str, list[Link]] = defaultdict(list)
    by_old: dict[str, list[Link]] = defaultdict(list)
    for link in links:
        if link.new:
            by_new[link.new.label].append(link)
        if link.old:
            by_old[link.old.label].append(link)

    # A deleted unit goes to the paragraph the rest of its old paragraph went to.
    home: dict[str, str] = {}
    for label, group in by_old.items():
        went = Counter(link.new.label for link in group if link.new)
        if went:
            home[label] = went.most_common(1)[0][0]
    deleted_into: dict[str, list[Link]] = defaultdict(list)
    orphans: dict[str, list[Link]] = defaultdict(list)
    for link in links:
        if link.old and not link.new:
            target = home.get(link.old.label)
            (deleted_into[target] if target else orphans[link.old.label]).append(link)

    out: list[dict[str, Any]] = []
    renumbered = 0
    order = sorted(by_new, key=lambda label: min(link.new.index for link in by_new[label]))  # type: ignore[union-attr]
    for label in order:
        group = sorted(by_new[label], key=lambda link: link.new.index)  # type: ignore[union-attr]
        gone = deleted_into.get(label, [])
        kinds = Counter(kind(link) for link in group + gone)
        olds = Counter(link.old.label for link in group if link.old)
        old_label = olds.most_common(1)[0][0] if olds else None
        if set(kinds) == {"unchanged"}:
            renumbered += old_label is not None and old_label != label
            continue
        rows = [_row(link) for link in group]
        # Each deleted unit after the last row that comes before it in the old version.
        for link in sorted(gone, key=lambda link: link.old.index):  # type: ignore[union-attr]
            assert link.old
            at = max(
                (
                    k + 1
                    for k, r in enumerate(rows)
                    if r["_old"] is not None and r["_old"] < link.old.index
                ),
                default=0,
            )
            rows.insert(at, _row(link))
        if not olds:
            status = "new"
        elif old_label != label:
            status = "moved and amended"
        else:
            status = "amended"
        old_page = next((link.old.page for link in group + gone if link.old), None)
        heading = headings.get(label, "")
        found = _hunk(label, old_label, group[0].new, old_page, status, rows, heading)  # type: ignore[arg-type]
        if found:
            out.append(found)
    for label, gone in orphans.items():
        rows = [_row(link) for link in sorted(gone, key=lambda link: link.old.index)]  # type: ignore[union-attr]
        first = gone[0].old
        assert first
        heading = headings.get(f"old:{label}", "")
        found = _hunk(label, label, first, first.page, "deleted", rows, heading)
        if found:
            out.append(found)
    return out, renumbered


def _row(link: Link) -> dict[str, Any]:
    k = kind(link)
    old_index = link.old.index if link.old else None
    if k == "amended":
        assert link.old and link.new
        return {
            "kind": k,
            "segments": segments(link.old.text, link.new.text, link.ops),
            "_old": old_index,
        }
    if k == "new":
        assert link.new
        return {"kind": k, "segments": [["ins", link.new.text]], "_old": None}
    if k == "deleted":
        assert link.old
        return {"kind": k, "segments": [["del", link.old.text]], "_old": old_index}
    assert link.new
    return {"kind": k, "segments": [["same", link.new.text]], "_old": old_index}


def _key(text: str) -> tuple[str, ...]:
    return tuple(bare(text))


def _cancel_moves(rows: list[dict[str, Any]]) -> None:
    """Words deleted in one unit of a paragraph and inserted in another only moved, as a table
    header repeated after a page break does: the deletion stays as plain text, the insertion
    goes."""
    deleted = Counter(_key(t) for r in rows for k, t in r["segments"] if k == "del")
    inserted = Counter(_key(t) for r in rows for k, t in r["segments"] if k == "ins")
    moved = deleted & inserted
    if not moved:
        return
    drop, keep = Counter(moved), Counter(moved)
    for r in rows:
        segs = []
        for k, t in r["segments"]:
            if k == "ins" and drop[_key(t)] > 0:
                drop[_key(t)] -= 1
                continue
            if k == "del" and keep[_key(t)] > 0:
                keep[_key(t)] -= 1
                k = "same"
            if segs and segs[-1][0] == k:
                segs[-1] = [k, f"{segs[-1][1]} {t}"]
            else:
                segs.append([k, t])
        r["segments"] = segs
        if r["kind"] in ("amended", "new", "deleted") and all(k == "same" for k, _ in segs):
            r["kind"] = "unchanged"


def _hunk(
    label: str,
    old_label: str | None,
    first: Span,
    old_page: int | None,
    status: str,
    rows: list[dict[str, Any]],
    heading: str,
) -> dict[str, Any] | None:
    for r in rows:
        r.pop("_old")
    _cancel_moves(rows)
    rows = [r for r in rows if r["segments"]]
    if all(r["kind"] == "unchanged" for r in rows):
        return None

    def words(k: str) -> int:
        return sum(len(t.split()) for r in rows for sk, t in r["segments"] if sk == k)

    return {
        "id": f"old:{label}" if status == "deleted" else label,
        "label": label,
        "old_label": old_label,
        "page": first.page,
        "old_page": old_page,
        "status": status,
        "heading": heading,
        "rows": rows,
        "added_words": words("ins"),
        "removed_words": words("del"),
    }


def diff(request: dict[str, Any]) -> dict[str, Any]:
    regulation, to_version = request["regulation"], request["to_version"]
    requirements = request["requirements"]
    clock = time.perf_counter
    t0 = clock()
    old = parse_pdf(Path(request["old_pdf"]), regulation, request["from_version"], "base")
    new = parse_pdf(Path(request["new_pdf"]), regulation, to_version, "latest")
    t1 = clock()
    links = align(old, new)
    t2 = clock()
    changes = (
        diff_parsed(old, new, links, requirements, regulation, to_version) if requirements else []
    )
    for c in changes:
        c.pop("new_units", None)
    t3 = clock()

    headings = {p.label: p.heading or "" for p in new} | {
        f"old:{p.label}": p.heading or "" for p in old
    }
    found, renumbered = hunks(links, headings)
    cited = {r["source"]["paragraph"]: r["id"] for r in requirements}
    citing: dict[str, list[str]] = defaultdict(list)
    for r in requirements:
        citing[r["source"]["paragraph"]].append(r["id"])
    for h in found:
        ids: list[str] = []
        for label in {
            *ancestors(h["label"]),
            *(ancestors(h["old_label"]) if h["old_label"] else []),
        }:
            ids += citing.get(label, [])
        h["cited_by"] = sorted(set(ids))

    old_units = [link for link in links if link.old]
    unchanged = sum(1 for link in old_units if kind(link) == "unchanged")
    statuses = Counter(h["status"] for h in found)
    changed_cited = {
        h["old_label"] for h in found if h["old_label"] in cited and h["status"] != "new"
    }
    return {
        "changes": changes,
        "hunks": found,
        "stats": {
            "old_paragraphs": len(old),
            "new_paragraphs": len(new),
            "old_units": len(old_units),
            "new_units": len(units(new)),
            "unchanged_share": unchanged / len(old_units) if old_units else 0.0,
            "amended": statuses["amended"] + statuses["moved and amended"],
            "new": statuses["new"],
            "deleted": statuses["deleted"],
            "renumbered": renumbered,
            "requirements": len(requirements),
            "cited_paragraphs": len(cited),
            "changed_cited_paragraphs": len(changed_cited),
            "seconds": {"parse": t1 - t0, "align": t2 - t1, "map": t3 - t2},
        },
    }


def main() -> int:
    command, *args = sys.argv[1:]
    if command == "identify":
        print(json.dumps(identify(Path(args[0]))))
    elif command == "diff":
        Path(args[1]).write_text(json.dumps(diff(json.loads(Path(args[0]).read_text()))))
    else:
        print(f"unknown command {command}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
