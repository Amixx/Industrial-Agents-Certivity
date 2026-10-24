"""Diff two versions of a UN Regulation paragraph by paragraph and map the
changes onto an assessment's requirements.

    uv run --with pymupdf python scripts/diff_regulation.py \
        --regulation "UN R148" --assessment cases/dev-rear-lamp/expected.json --out out.json

    uv run --with pymupdf python scripts/diff_regulation.py \
        --old-pdf subgoal/dev/old.pdf --new-pdf subgoal/dev/new.pdf \
        --requirements subgoal/dev/requirements_old.json --out out.json
"""

import argparse
import difflib
import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent

LABEL = re.compile(r"^(\d+(?:\.\d+)*)\.(?:\s+|(?=[A-Z]))(.*)$|^(\d+(?:\.\d+)+)\s+([A-Z(].*)$")
ANNEX = re.compile(r"^Annex\s+(\d+[A-Z]?)(?:\s*[-–]\s*Appendix\s+(\d+))?\b")
# A line starting with "4.2. " right after one of these words is a cross-reference, not a paragraph.
REFERENCE_WORDS = {"paragraph", "paragraphs", "para.", "and", "or", "to", "of", "in", "see", "with", "under", "by", "Annex"}
SENTENCE_END = re.compile(r"(?<=[.;:])\s+(?=[A-Z(])")
MIN_BODY_SIZE = 9
HEADING_SIZE = 12
EXPONENT_BASE = re.compile(r"(\d|\b(?:m|cm|mm|km|m/s|s|cd|lx|W|V|Hz))$")


def norm(text):
    return " ".join(text.split())


def bare(text):
    """Lower-case words without punctuation, with editorial variants ("70%", "6 seconds", "µ") spelled one way."""
    text = text.replace("%", " per cent ").replace("\u00b5", "\u03bc")
    text = re.sub(r"(\d)\s*(?:seconds?|sec)\b", r"\1 s", text)
    return re.sub(r"[^\w]+", " ", text).lower().split()


def page_lines(page):
    """Yield (text, is_heading) for each line of body text.

    Lines set in small type (page header, footnotes) are dropped. Within a line, small lowered text is a
    subscript and kept, small raised text after a number or unit is an exponent, and any other small raised
    text is a footnote marker and dropped.
    """
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = line["spans"]
            if not spans or spans[0]["size"] < MIN_BODY_SIZE:
                continue
            baseline = spans[0]["origin"][1]
            text = ""
            for span in spans:
                raised = span["origin"][1] < baseline - 0.5
                if span["size"] >= MIN_BODY_SIZE or not raised:
                    text += span["text"]
                elif EXPONENT_BASE.search(text):
                    text += "^" + span["text"].strip()
            text = text.strip()
            if text:
                yield text, spans[0]["size"] >= HEADING_SIZE and spans[0]["flags"] & 16


def parse_pdf(path):
    """Return {label: {"label", "page", "text"}} in document order."""
    paragraphs = {}
    current = None
    title_line = False
    annex = ""
    prev = ""
    for page_no, page in enumerate(pymupdf.open(path), start=1):
        for line, is_heading in page_lines(page):
            annex_match = ANNEX.match(line)
            if annex_match and is_heading:
                number, appendix = annex_match.groups()
                annex = f"Annex {number} " + (f"Appendix {appendix} " if appendix else "")
                current = None
                prev = line
                continue
            label_match = LABEL.match(line)
            prev_word = prev.split()[-1] if prev else ""
            if label_match and prev_word not in REFERENCE_WORDS:
                label = annex + (label_match.group(1) or label_match.group(3))
                body = label_match.group(2) or label_match.group(4)
                if label in paragraphs:
                    current = paragraphs[label]
                    current["text"] += " " + body
                else:
                    current = paragraphs[label] = {"label": label, "page": page_no, "text": body}
                title_line = len(body.split()) < 10 and not body.endswith((".", ":", ";"))
            elif current is not None:
                # A short label line followed by a capitalised line is the paragraph's title.
                separator = "\n" if title_line and line[0].isupper() else " "
                current["text"] += separator + line
                title_line = False
            prev = line
    for p in paragraphs.values():
        p["text"] = "\n".join(norm(part) for part in p["text"].replace("\u00ad", "").split("\n"))
    return paragraphs


def sentences(text):
    return [s for part in text.split("\n") for s in SENTENCE_END.split(part) if s]


def body(text):
    """The paragraph without its title line."""
    return text.split("\n", 1)[-1]


def word_ops(old, new):
    """Word-level differences as (tag, old_phrase, new_phrase, old_word_index)."""
    a, b = old.split(), new.split()
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            ops.append((tag, " ".join(a[i1:i2]), " ".join(b[j1:j2]), i1))
    return ops


def describe(ops):
    parts = []
    for tag, old, new, _ in ops:
        if tag == "replace":
            parts.append(f"'{old}' became '{new}'")
        elif tag == "insert":
            parts.append(f"'{new}' was added")
        else:
            parts.append(f"'{old}' was removed")
    return "; ".join(parts)


def substantive(old, new):
    return bare(old) != bare(new)


def apply_ops(req_text, old_para, ops):
    """Apply the paragraph's wording changes to the requirement text where the changed phrase occurs in it."""
    words = old_para.split()
    text = req_text
    applied = 0
    for tag, old, new, i in ops:
        if tag in ("replace", "delete") and old in text:
            text = text.replace(old, new, 1)
            applied += 1
        elif tag == "insert":
            for k in (4, 3, 2):
                anchor = " ".join(words[max(0, i - k):i])
                if i >= k and anchor in text:
                    text = text.replace(anchor, anchor + " " + new, 1)
                    applied += 1
                    break
    return norm(text), applied


def similarity(a, b):
    return difflib.SequenceMatcher(None, bare(a), bare(b), autojunk=False).ratio()


def spans(text, max_words):
    """Runs of consecutive sentences, up to about twice the length of what they are matched against."""
    parts = sentences(body(text))
    for i in range(len(parts)):
        for j in range(i + 1, len(parts) + 1):
            span = " ".join(parts[i:j])
            yield span
            if len(span.split()) > 2 * max_words + 10:
                break


def best_span(target, paragraphs):
    """The (score, label, span) in `paragraphs` that best matches `target`; earlier paragraphs win near-ties."""
    best = (0.0, None, None)
    size = len(target.split())
    for p in paragraphs:
        for span in spans(p["text"], size):
            score = similarity(target, span)
            if score > best[0] + 0.05:
                best = (score, p["label"], span)
    return best


def contains(text, phrase):
    return " ".join(bare(phrase)) in " ".join(bare(text))


def shall_sentences(text):
    """Obligation sentences, leaving out figure and table captions, whose text runs into the cell contents."""
    return [s for s in sentences(text) if re.search(r"\bshall\b", s) and not re.match(r"(Figure|Table)\s+\d", s)]


def short(text, n=100):
    return text if len(text) <= n else text[:n].rstrip() + "…"


def diff_paragraphs(old, new):
    changed = [l for l in old if l in new and old[l]["text"] != new[l]["text"]]
    removed = [l for l in old if l not in new]
    added = [l for l in new if l not in old]
    return changed, added, removed


def map_requirement(req, regulation, to_version, old, new, moved_into):
    """The change to one requirement whose paragraph was changed or removed, or None if its provision is intact."""
    label = req["source"]["paragraph"]
    _, _, old_span = best_span(req["text"], [old[label]])
    candidates = ([new[label]] if label in new else []) + moved_into
    if any(contains(p["text"], old_span) for p in candidates):
        return None
    score, new_label, new_span = best_span(old_span, candidates)
    if score < 0.5:
        verb = "was amended" if label in new else "was deleted"
        return {
            "requirementId": req["id"], "change": "removed", "oldText": req["text"], "newText": None,
            "reason": f"Paragraph {label} of {regulation} {verb} in version {to_version}; "
                      f"the provision '{short(req['text'])}' no longer appears.",
            "source": {"page": new[label]["page"], "paragraph": label} if label in new else None,
        }
    ops = [op for op in word_ops(old_span, new_span) if substantive(op[1], op[2])]
    if not ops:
        return None
    patched, applied = apply_ops(req["text"], old_span, ops)
    formerly = f" (formerly {label})" if new_label != label else ""
    return {
        "requirementId": req["id"], "change": "modified", "oldText": req["text"],
        "newText": patched if applied == len(ops) else new_span,
        "reason": f"Paragraph {new_label}{formerly} of {regulation} was amended in version {to_version}: {describe(ops)}.",
        "source": {"page": new[new_label]["page"], "paragraph": new_label},
        "_span": new_span,
    }


def map_changes(regulation, to_version, old, new, requirements):
    changed, added, removed = diff_paragraphs(old, new)
    affected = {l for l in changed if substantive(old[l]["text"], new[l]["text"])} | set(removed)
    moved_into = [new[l] for l in added + changed]
    changes = []

    for req in requirements:
        if req["source"]["paragraph"] in affected:
            change = map_requirement(req, regulation, to_version, old, new, moved_into)
            if change:
                changes.append(change)

    used = [c.pop("_span") for c in changes if "_span" in c]
    # Sentences of changed or removed paragraphs may reappear under another label after renumbering.
    movable = {tuple(bare(s)) for l in changed + removed for s in sentences(old[l]["text"])}
    for label in added + changed:
        para = new[label]
        if label in old and not substantive(old[label]["text"], para["text"]):
            continue
        verb = "was amended in version" if label in old else "is new in version"
        for s in shall_sentences(body(para["text"])):
            if tuple(bare(s)) in movable or any(contains(span, s) for span in used):
                continue
            changes.append({
                "requirementId": None, "change": "added", "oldText": None, "newText": s,
                "reason": f"Paragraph {label} of {regulation} {verb} {to_version}: '{short(s)}'.",
                "source": {"page": para["page"], "paragraph": label},
            })

    stats = {"changed": len(changed), "added": len(added), "removed": len(removed)}
    return changes, stats


def regulation_pdfs(regulation, from_role, to_role):
    entry = next(e for e in json.loads((ROOT / "regulations/index.json").read_text()) if e["regulation"] == regulation)
    folder = ROOT / "regulations/pdf" / regulation.replace(" ", "_")
    versions = {v["role"]: v for v in entry["versions"]}

    def resolve(role):
        v = versions[role]
        return v["version_label"], folder / role / v["files"][0]["name"]

    return resolve(from_role), resolve(to_role)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regulation", action="append", help="e.g. 'UN R148'; repeatable")
    parser.add_argument("--assessment", help="assessment JSON with a 'requirements' list")
    parser.add_argument("--from-role", default="base")
    parser.add_argument("--to-role", default="latest")
    parser.add_argument("--old-pdf")
    parser.add_argument("--new-pdf")
    parser.add_argument("--requirements", help="JSON list of requirements")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if args.old_pdf:
        requirements = json.loads(Path(args.requirements).read_text())
        regulation = requirements[0]["source"]["regulation"]
        new_version = re.search(r"version (\S+?),?\s", pymupdf.open(args.new_pdf)[0].get_text()).group(1)
        changes, stats = map_changes(regulation, new_version, parse_pdf(args.old_pdf), parse_pdf(args.new_pdf), requirements)
        result = {"regulation": regulation, "toVersion": new_version, "stats": stats, "changes": changes}
    else:
        assessment = json.loads(Path(args.assessment).read_text())["requirements"]
        result = []
        for regulation in args.regulation:
            (from_version, old_pdf), (to_version, new_pdf) = regulation_pdfs(regulation, args.from_role, args.to_role)
            requirements = [r for r in assessment if r["source"]["regulation"] == regulation]
            changes, stats = map_changes(regulation, to_version, parse_pdf(old_pdf), parse_pdf(new_pdf), requirements)
            result.append({"regulation": regulation, "fromVersion": from_version, "toVersion": to_version,
                           "stats": stats, "changes": changes})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
