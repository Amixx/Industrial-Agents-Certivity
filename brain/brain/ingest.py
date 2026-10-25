"""Regulation PDFs -> paragraph records (label, page, text, parents), one JSONL file per version.

    uv run python -m brain.ingest            # all versions in regulations/index.json
    uv run python -m brain.ingest --role base --only "UN R148"

The Certivity PDFs have a clean text layer, a header line "UN R148, version 1.6.0 | page 10 of 48"
on every page, and paragraph labels at the left margin ("5.5.7. Colour:"). Annexes restart the
numbering, so their labels get a prefix in the style of the expected answers: "Annex 3 1.2",
"Annex 6 Part 4 3".

Three passes over the lines of a PDF:
  1. scope headings (Annex N, Part N, Appendix N), accepted only in sequence;
  2. inside each scope, the longest chain of label lines whose numbers follow each other, so a
     table cell or a wrapped reference that starts a line with "5.1." cannot derail the numbering;
  3. paragraphs: each chosen label opens one, every other line is appended to the open one.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .models import Paragraph, Role
from .paths import CORPUS, INDEX, PDFS

HEADER = re.compile(r"^.+, version [\w.]+ \| page (\d+) of (\d+)\s*$")
PREAMBLE_END = re.compile(r"^Role in the hackathon:")
LABEL_DOT = re.compile(r"^(\d{1,2}(?:\.\d{1,3})*)\.(?:\s+(\S.*))?$")
LABEL_NODOT = re.compile(r"^(\d{1,2}(?:\.\d{1,3})+)\s+([A-Z(\"“].*)$")
ANNEX = re.compile(r"^Annex\s+(\d{1,2})([A-Z]?)(?:\s*[-–]\s*Appendix\s+(\d+))?(?:\s+(\S.*))?$")
APPENDIX = re.compile(r"^Appendix\s+(\d{1,2})(?:\s*[:.]\s*|\s+)([A-Z].*)?$")
NORMATIVE = re.compile(
    r"^(?:[IVX]+|[A-Z])\.\s+Text of the (?:global technical )?Regulation\b", re.I
)
PART = re.compile(r"^Part\s+(\d{1,2}|[A-H])\s*[-–:]\s*(\S.*)?$")
CONTINUES = re.compile(
    r"(paragraphs?|para\.|and|or|to|of|in|with|see|under|Annex|Regulation|Regulations?\s+Nos?\.|-)$",
    re.IGNORECASE,
)
MODAL = re.compile(r"\b(shall|must|may)\b")
MAX_GAP = 5
LOOKBACK = 400  # label candidates considered as predecessors in the chain search


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    prev: str  # the line before, for "wrapped reference" checks


@dataclass(frozen=True)
class Scope:
    """An annex / part / appendix heading line: everything after it until the next one."""

    index: int  # line index of the heading; -1 for the main body
    prefix: str | None  # "Annex 6 Part 4"; None for the main body
    title: str | None
    depth: int  # 0 annex or main-body appendix, 1 part, 2 appendix inside an annex


def _components(number: str) -> tuple[int, ...]:
    return tuple(int(c) for c in number.split("."))


def follows(new: tuple[int, ...], cur: tuple[int, ...] | None) -> bool:
    """Whether `new` can be the next paragraph number after `cur` in the same numbering scope."""
    if cur is None:
        return new[0] <= MAX_GAP and all(c <= 2 for c in new[1:])
    if new[: len(cur)] == cur and len(new) > len(cur):  # child, maybe skipping empty levels
        return all(1 <= c <= 2 for c in new[len(cur) :])
    for depth in range(min(len(cur), len(new))):
        if cur[depth] < new[depth] <= cur[depth] + MAX_GAP and new[:depth] == cur[:depth]:
            return all(c <= 2 for c in new[depth + 1 :])
        if new[depth] != cur[depth]:
            break
    return False


def _heading(rest: str | None) -> str | None:
    if not rest or len(rest) > 90 or MODAL.search(rest):
        return None
    return rest if rest.endswith(":") or not rest.endswith(".") else None


# --- pass 1: scopes ----------------------------------------------------------------------------


def _scopes(lines: list[Line]) -> list[Scope]:
    scopes = [Scope(-1, None, None, 0)]
    annex_num, annex = 0, None
    part_seq, part = 0, None
    appendix_num = 0
    for i, line in enumerate(lines):
        if CONTINUES.search(line.prev):
            continue
        if NORMATIVE.match(line.text) and annex_num == 0:
            # A GTR: the statement of rationale before this line is numbered on its own.
            scopes[0] = Scope(-1, "Rationale", None, 0)
            scopes.append(Scope(i, None, line.text, 0))
            continue
        if m := ANNEX.match(line.text):
            num, suffix, appendix, rest = int(m[1]), m[2], m[3], m[4]
            if rest and not (rest[0].isupper() or rest.startswith("(")):
                continue
            same = annex_num > 0 and num == annex_num
            if annex_num == 0 and num != 1:
                continue
            if not ((same and (appendix or suffix)) or annex_num < num <= annex_num + 2):
                continue
            annex_num, annex = num, f"Annex {num}{suffix}"
            part_seq, part = 0, None
            appendix_num = int(appendix) if appendix else 0
            prefix = f"{annex} Appendix {appendix}" if appendix else annex
            scopes.append(Scope(i, prefix, rest, 2 if appendix else 0))
        elif annex and (m := PART.match(line.text)):
            token = m[1]
            seq = int(token) if token.isdigit() else ord(token) - ord("A") + 1
            if seq != part_seq + 1:
                continue
            part_seq, part, appendix_num = seq, f"Part {token}", 0
            scopes.append(Scope(i, f"{annex} {part}", m[2], 1))
        elif m := APPENDIX.match(line.text):
            num = int(m[1])
            if num != appendix_num + 1:
                continue
            appendix_num = num
            parent = " ".join(p for p in (annex, part) if p)
            prefix = f"{parent} Appendix {num}" if parent else f"Appendix {num}"
            scopes.append(Scope(i, prefix, m[2], 2 if annex else 0))
    return scopes


# --- pass 2: label chains ----------------------------------------------------------------------


def _label(line: Line) -> tuple[str, str | None] | None:
    m = LABEL_DOT.match(line.text) or LABEL_NODOT.match(line.text)
    if not m or (m[2] and m[2][0].islower()) or CONTINUES.search(line.prev):
        return None
    return m[1], m[2]


def _chain(candidates: list[tuple[int, tuple[int, ...]]]) -> set[int]:
    """Line indices of the longest chain of candidates whose numbers follow each other."""
    n = len(candidates)
    best = [0] * n
    back = [-1] * n
    for i, (_, num) in enumerate(candidates):
        best[i] = 1 if follows(num, None) else 0
        for j in range(max(0, i - LOOKBACK), i):
            if best[j] and best[j] + 1 > best[i] and follows(num, candidates[j][1]):
                best[i], back[i] = best[j] + 1, j
    if not n or max(best) == 0:
        return set()
    i = max(range(n), key=lambda k: (best[k], k))
    chosen = set()
    while i >= 0:
        chosen.add(candidates[i][0])
        i = back[i]
    return chosen


# --- pass 3: paragraphs ------------------------------------------------------------------------


@dataclass
class _Open:
    id: str
    parent: str | None
    path: list[str]
    label: str
    number: str
    annex: str | None
    page: int
    heading: str | None
    lines: list[str] = field(default_factory=list)
    breaks: list[int] = field(default_factory=list)
    last_page: int = 0
    length: int = 0

    def add(self, line: str, page: int) -> None:
        if self.lines and page != self.last_page:
            self.breaks.append(self.length + 1)
        joiner = (
            "" if not self.lines or (self.lines[-1].endswith("-") and line[:1].islower()) else " "
        )
        self.lines.append(joiner + line)
        self.length += len(joiner) + len(line)
        self.last_page = page


def parse_lines(lines: list[Line], regulation: str, version: str, role: Role) -> list[Paragraph]:
    scopes = _scopes(lines)
    heads = {s.index: s for s in scopes if s.index >= 0}
    bounds = [s.index for s in scopes] + [len(lines)]
    starts: dict[int, tuple[str, str | None]] = {}
    for k in range(len(scopes)):
        candidates = []
        for i in range(bounds[k] + 1, bounds[k + 1]):
            if found := _label(lines[i]):
                candidates.append((i, _components(found[0])))
                starts[i] = found
        chosen = _chain(candidates)
        for i, _ in candidates:
            if i not in chosen:
                del starts[i]

    out: list[Paragraph] = []
    ids: dict[str, int] = {}
    paths: dict[str, list[str]] = {}
    scope_ids: dict[str, str] = {}
    heading_ids: list[tuple[int, str]] = []  # (depth, id) of the annex / part / appendix headings
    prefix: str | None = scopes[0].prefix
    current: _Open | None = None

    def close() -> None:
        nonlocal current
        if current is not None:
            out.append(
                Paragraph(
                    id=current.id,
                    regulation=regulation,
                    version=version,
                    role=role,
                    label=current.label,
                    number=current.number,
                    annex=current.annex,
                    page=current.page,
                    page_end=current.last_page,
                    heading=current.heading,
                    text="".join(current.lines),
                    page_breaks=current.breaks,
                    parent=current.parent,
                    path=current.path,
                )
            )
        current = None

    def start(label: str, number: str, page: int, rest: str | None) -> _Open:
        close()
        base = f"{regulation}|{version}|{label}"
        n = ids.get(base, 0)
        ids[base] = n + 1
        pid = base if n == 0 else f"{base}~{n + 1}"
        parent = None
        if number:
            comps = number.split(".")
            for k in range(len(comps) - 1, 0, -1):
                if (anc := ".".join(comps[:k])) in scope_ids:
                    parent = scope_ids[anc]
                    break
            scope_ids[number] = pid
        if parent is None and heading_ids:
            parent = heading_ids[-1][1]
        paths[pid] = paths[parent] + [parent] if parent else []
        opened = _Open(
            pid, parent, paths[pid], label, number, prefix, page, _heading(rest), last_page=page
        )
        if rest:
            opened.add(rest, page)
        return opened

    for i, line in enumerate(lines):
        if i in heads:
            scope = heads[i]
            prefix = scope.prefix
            scope_ids = {}
            heading_ids = [h for h in heading_ids if h[0] < scope.depth]
            if prefix is None:  # back to un-prefixed numbering (GTR normative text)
                close()
                current = start("preamble", "", line.page, scope.title)
                continue
            current = start(prefix, "", line.page, scope.title)
            heading_ids.append((scope.depth, current.id))
        elif i in starts:
            number, rest = starts[i]
            current = start(f"{prefix} {number}" if prefix else number, number, line.page, rest)
        else:
            if current is None:
                current = start("preamble", "", line.page, None)
            current.add(line.text, line.page)
    close()
    return out


def read_lines(pdf: Path) -> list[Line]:
    out: list[Line] = []
    prev = ""
    for page, text in _raw_lines(pdf):
        out.append(Line(page, text, prev))
        prev = text
    return out


def _raw_lines(pdf: Path) -> Iterator[tuple[int, str]]:
    import pymupdf

    doc = pymupdf.open(pdf)
    in_preamble = True
    for index, page in enumerate(doc, start=1):  # type: ignore[arg-type,var-annotated]
        for raw in page.get_text().splitlines():
            line = " ".join(raw.split())
            if not line:
                continue
            if header := HEADER.match(line):
                if int(header[1]) != index:
                    raise ValueError(f"{pdf.name}: header says page {header[1]} on page {index}")
                continue
            if in_preamble and index == 1:
                in_preamble = not PREAMBLE_END.match(line)
                continue
            if "�" in line:
                raise ValueError(f"{pdf.name}: replacement character on page {index}")
            yield index, line


def parse_pdf(pdf: Path, regulation: str, version: str, role: Role) -> list[Paragraph]:
    return parse_lines(read_lines(pdf), regulation, version, role)


# --- corpus files ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    regulation: str
    version: str
    role: Role
    pdf: Path
    title: str


def sources(index_path: Path = INDEX, pdf_dir: Path = PDFS) -> list[Source]:
    out = []
    for entry in json.loads(index_path.read_text()):
        slug = "_".join(entry["regulation"].replace("/", " ").split())
        for version in entry["versions"]:
            for file in version["files"]:
                pdf = pdf_dir / slug / version["role"] / file["name"]
                out.append(
                    Source(
                        entry["regulation"],
                        version["version_label"],
                        version["role"],
                        pdf,
                        entry["title"],
                    )
                )
    return out


def corpus_path(regulation: str, role: Role, corpus_dir: Path = CORPUS) -> Path:
    return corpus_dir / f"{'_'.join(regulation.split())}_{role}.jsonl"


def write(paragraphs: Iterable[Paragraph], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for p in paragraphs:
            f.write(p.model_dump_json() + "\n")


def load(regulation: str, role: Role = "base", corpus_dir: Path = CORPUS) -> list[Paragraph]:
    path = corpus_path(regulation, role, corpus_dir)
    return [Paragraph.model_validate_json(line) for line in path.read_text().splitlines()]


def load_all(role: Role = "base", corpus_dir: Path = CORPUS) -> dict[str, list[Paragraph]]:
    return {
        s.regulation: load(s.regulation, role, corpus_dir)
        for s in sources()
        if s.role == role and corpus_path(s.regulation, role, corpus_dir).exists()
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Parse the regulation PDFs into paragraph JSONL.")
    ap.add_argument("--role", choices=["base", "latest"])
    ap.add_argument("--only", nargs="*", help="regulations, e.g. 'UN R148'")
    args = ap.parse_args(argv)
    for s in sources():
        if (args.role and s.role != args.role) or (args.only and s.regulation not in args.only):
            continue
        if not s.pdf.exists():
            print(f"missing  {s.pdf}")
            continue
        paragraphs = parse_pdf(s.pdf, s.regulation, s.version, s.role)
        write(paragraphs, corpus_path(s.regulation, s.role))
        print(f"{len(paragraphs):5d}  {s.regulation} {s.role} {s.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
