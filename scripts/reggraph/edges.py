"""Typed edges between paragraph records: `parent`, `ref`, `xref` and `supersedes`, each with its evidence span."""

import re

NUM = r"\d+(?:\.\d+)*\.?"
NUM_LIST = rf"{NUM}(?:\s*(?:,|and|or|to|-|–)\s*{NUM})*"
ANNEX_ID = r"\d+[A-Z]?"
REG_ID = r"\d+H?"

PARAGRAPHS = re.compile(rf"\b(?:sub-?)?(?:paragraphs?|paras?\.)\s+({NUM_LIST})", re.IGNORECASE)
# What follows a paragraph number and says which document part it is in.
QUALIFIER = re.compile(
    rf"""^\s*,?\s*(?:of|in|to)\s+(?:
        (?P<this>this\s+Regulation|the\s+Regulation)
      | Part\s+(?P<part>\w+)\s+(?:of|to)\s+Annex\s+(?P<part_annex>{ANNEX_ID})
      | Appendix\s+(?P<app>\d+)\s+(?:of|to)\s+Annex\s+(?P<app_annex>{ANNEX_ID})
      | Annex\s+(?P<annex>{ANNEX_ID})
      | (?:the\s+)?(?:\d+\s+series\s+of\s+amendments\s+to\s+)?(?:UN\s+)?Regulation\s+No\.?\s*(?P<reg>{REG_ID})
    )""",
    re.VERBOSE | re.IGNORECASE,
)
# "Annex 5, paragraph 2" names the annex first.
ANNEX_BEFORE = re.compile(rf"Annex\s+({ANNEX_ID})\s*,\s*$")
PART_OF_ANNEX = re.compile(rf"\bPart\s+(\w+)\s+(?:of|to)\s+Annex\s+({ANNEX_ID})\b")
APPENDIX_OF_ANNEX = re.compile(rf"\bAppendix\s+(\d+)\s+(?:of|to)\s+Annex\s+({ANNEX_ID})\b")
ANNEXES = re.compile(rf"\bAnnex(?:es)?\s+({ANNEX_ID}(?:\s*(?:,|and|or|to)\s*{ANNEX_ID})*)\b")
REGULATIONS = re.compile(
    rf"\b(?:UN\s+)?Regulations?\s+Nos?\.?\s*({REG_ID}(?:\s*(?:,|and|or)\s*(?:No\.?\s*)?{REG_ID})*)\b"
)
GTR = re.compile(r"\b(?:UN\s+)?(?:GTR|Global\s+Technical\s+Regulation)\s+No\.?\s*(\d+)\b")
# A transitional provision that stops new approvals once another regulation is in force.
CEASE = re.compile(r"\bcease\s+to\s+grant\b", re.IGNORECASE)
IN_FORCE = re.compile(rf"entry\s+into\s+force\s+of\s+(?:the\s+)?(?:UN\s+)?Regulation\s+No\.?\s*({REG_ID})\b")
# An introduction that merges older regulations into this one.
COMBINES = re.compile(
    rf"combines\s+the\s+provisions\s+of\s+(?:the\s+)?(?:individual\s+)?(?:UN\s+)?Regulations\s+Nos\.?\s*({REG_ID}(?:\s*(?:,|and)\s*{REG_ID})*)"
)
EVIDENCE_CHARS = 60


def evidence(text, start, end):
    return text[max(0, start - EVIDENCE_CHARS) : end + EVIDENCE_CHARS].strip()


def split_list(items):
    """'6.1 to 6.3, 6.5 and 7' as [('6.1', '6.3'), ('6.5', None), ('7', None)]."""
    out = []
    tokens = re.findall(rf"{NUM}|\bto\b|[-–]", items)
    i = 0
    while i < len(tokens):
        start = tokens[i].rstrip(".")
        if i + 2 < len(tokens) and tokens[i + 1] in ("to", "-", "–"):
            out.append((start, tokens[i + 2].rstrip(".")))
            i += 3
        else:
            if tokens[i] not in ("to", "-", "–"):
                out.append((start, None))
            i += 1
    return out


def annex_scopes(label):
    """Prefixes a bare paragraph number in this node may be relative to, nearest first: 'Annex 4 Part 1 1.2' gives
    ['Annex 4 Part 1 ', 'Annex 4 ', '']."""
    m = re.match(r"^(Annex \S+)( (?:Part|Appendix) \S+)?", label)
    if not m:
        return [""]
    scopes = [m.group(0) + " ", m.group(1) + " ", ""]
    return list(dict.fromkeys(scopes))


def parent_label(label, labels):
    """Nearest existing ancestor of a label, or None for a top-level node."""
    if ". Table " in label:
        return label.split(". Table ")[0]
    m = re.match(r"^(Annex \S+)(?: (Part|Appendix) (\S+))?(?: (\d+(?:\.\d+)*))?$", label)
    if m:
        annex, kind, part, num = m.groups()
        scope = f"{annex} {kind} {part}" if kind else annex
        if num:
            parts = num.split(".")
            for k in range(len(parts) - 1, 0, -1):
                candidate = f"{scope} {'.'.join(parts[:k])}"
                if candidate in labels:
                    return candidate
            return scope if scope in labels else (annex if annex in labels else None)
        if kind:
            return annex if annex in labels else None
        return None
    parts = label.split(".")
    for k in range(len(parts) - 1, 0, -1):
        candidate = ".".join(parts[:k])
        if candidate in labels:
            return candidate
    return None


class Resolver:
    """Resolves paragraph numbers to labels in one regulation, expanding ranges in document order."""

    def __init__(self, nodes):
        self.order = {n["label"]: i for i, n in enumerate(nodes)}
        self.labels = list(self.order)

    def exact(self, label):
        return label if label in self.order else None

    def ancestor(self, label):
        parts = label.split(" ")
        num = parts[-1].split(".")
        prefix = " ".join(parts[:-1])
        for k in range(len(num) - 1, 0, -1):
            candidate = (prefix + " " if prefix else "") + ".".join(num[:k])
            if candidate in self.order:
                return candidate
        return prefix if prefix in self.order else None

    def resolve(self, number, scopes):
        """(label, how) with how in exact, ancestor, none; tries each scope prefix in turn."""
        for scope in scopes:
            hit = self.exact(scope + number)
            if hit:
                return hit, "exact"
        for scope in scopes:
            hit = self.ancestor(scope + number)
            if hit:
                return hit, "ancestor"
        return None, "none"

    def span(self, start, end):
        a, b = self.order[start], self.order[end]
        if b < a or b - a > 200:
            return [start, end]
        return self.labels[a : b + 1]


def node_edges(reg, node, resolver, regulations):
    """ref and xref edges found in one paragraph's text, plus counts of what did not resolve."""
    text = node["text"]
    label = node["label"]
    edges = []
    stats = {"ref_exact": 0, "ref_ancestor": 0, "ref_none": 0, "xref": 0, "xref_unknown": 0, "self": 0}
    consumed = []

    def add(kind, target, start, end, **extra):
        edges.append({"type": kind, "source": f"{reg}|{label}", "target": target, "evidence": evidence(text, start, end), **extra})

    def add_ref(number, scopes, start, end, ext_reg=None):
        if ext_reg:
            add("xref", f"{ext_reg}|{number}" if number else ext_reg, start, end, paragraph=number)
            return
        hit, how = resolver.resolve(number, scopes)
        stats[f"ref_{how}"] += 1
        if hit and hit != label:
            add("ref", f"{reg}|{hit}", start, end, resolution=how)

    for m in PARAGRAPHS.finditer(text):
        tail = text[m.end() : m.end() + 120]
        q = QUALIFIER.match(tail)
        before = ANNEX_BEFORE.search(text[max(0, m.start() - 20) : m.start()])
        end = m.end() + (q.end() if q else 0)
        consumed.append((m.start(), end))
        ext_reg = None
        if q and q.group("reg"):
            ext = f"UN R{q.group('reg')}"
            if ext == reg:
                scopes = [""]
                stats["self"] += 1
            else:
                ext_reg = ext
                stats["xref" if ext in regulations else "xref_unknown"] += 1
        if q and q.group("this"):
            scopes = [""]
        elif q and q.group("part"):
            scopes = [f"Annex {q.group('part_annex')} Part {q.group('part')} "]
        elif q and q.group("app"):
            scopes = [f"Annex {q.group('app_annex')} Appendix {q.group('app')} "]
        elif q and q.group("annex"):
            scopes = [f"Annex {q.group('annex')} "]
        elif before:
            scopes = [f"Annex {before.group(1)} "]
        elif not ext_reg:
            scopes = annex_scopes(label)
        for start, stop in split_list(m.group(1)):
            if ext_reg:
                for number in (start, stop):
                    if number:
                        add_ref(number, [], m.start(), end, ext_reg=ext_reg)
                continue
            if stop:
                a, how_a = resolver.resolve(start, scopes)
                b, how_b = resolver.resolve(stop, scopes)
                if a and b and how_a == how_b == "exact":
                    stats["ref_exact"] += 2
                    for target in resolver.span(a, b):
                        if target != label:
                            add("ref", f"{reg}|{target}", m.start(), end, resolution="range")
                    continue
                add_ref(start, scopes, m.start(), end)
                add_ref(stop, scopes, m.start(), end)
            else:
                add_ref(start, scopes, m.start(), end)

    def free(m):
        return not any(a <= m.start() < b for a, b in consumed)

    for pattern, fmt in ((PART_OF_ANNEX, "Annex {1} Part {0}"), (APPENDIX_OF_ANNEX, "Annex {1} Appendix {0}")):
        for m in pattern.finditer(text):
            if free(m):
                consumed.append((m.start(), m.end()))
                add_ref(fmt.format(*m.groups()), [""], m.start(), m.end())
    for m in ANNEXES.finditer(text):
        if not free(m):
            continue
        tail = text[m.end() : m.end() + 40]
        ext = re.match(rf"^\s*(?:to|of)\s+(?:the\s+)?(?:UN\s+)?Regulation\s+No\.?\s*({REG_ID})", tail)
        for start, stop in split_list(m.group(1)):
            for number in (start, stop):
                if not number:
                    continue
                if ext and f"UN R{ext.group(1)}" != reg:
                    add_ref(f"Annex {number}", [], m.start(), m.end(), ext_reg=f"UN R{ext.group(1)}")
                else:
                    add_ref(f"Annex {number}", [""], m.start(), m.end())

    for m in REGULATIONS.finditer(text):
        if not free(m):
            continue
        for target in (f"UN R{n}" for n in re.findall(REG_ID, m.group(1))):
            if target == reg:
                stats["self"] += 1
                continue
            stats["xref" if target in regulations else "xref_unknown"] += 1
            add("xref", target, m.start(), m.end(), paragraph=None)
    for m in GTR.finditer(text):
        target = f"UN GTR {m.group(1)}"
        stats["xref" if target in regulations else "xref_unknown"] += 1
        add("xref", target, m.start(), m.end(), paragraph=None)
    return edges, stats


def supersedes_edges(reg, node, regulations):
    """`supersedes` edges (newer regulation -> older one) stated in a transitional provision of the older
    regulation, or in the introduction of the newer one."""
    text = node["text"]
    out = []
    if CEASE.search(text):
        for m in IN_FORCE.finditer(text):
            newer = f"UN R{m.group(1)}"
            if newer != reg:
                out.append({"type": "supersedes", "source": newer, "target": reg, "basis": "transitional", "at": f"{reg}|{node['label']}", "evidence": evidence(text, m.start(), m.end())})
    for m in COMBINES.finditer(text):
        for older in (f"UN R{n}" for n in re.findall(REG_ID, m.group(1))):
            out.append({"type": "supersedes", "source": reg, "target": older, "basis": "consolidates", "in_corpus": older in regulations, "at": f"{reg}|{node['label']}", "evidence": evidence(text, m.start(), m.end())})
    return out
