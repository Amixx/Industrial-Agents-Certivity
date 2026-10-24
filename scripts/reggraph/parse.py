"""Paragraph records from a base PDF: label, page where the label sits, and text stitched across page breaks.

Labels follow the expected answers' style: `6.19.7.3`, `Introduction`, `Annex 4`, `Annex 4 Part 1 1.2`, `Annex 1 Appendix 2 3`,
and table captions under their paragraph, `5.1.4.4.1. Table 3`.
"""

import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from diff_regulation import ANNEX, LABEL, REFERENCE_WORDS, norm, page_lines

PART = re.compile(r"^Part\s+(\d+[A-Z]?|[A-Z])\s*(?:[-–:]\s*\S|$)")
# A caption, not a cell that repeats a table number ("Table A2- 1 5∙10^-2").
TABLE = re.compile(r"^Table\s+([A-Z]?\d+(?:-\d+)?)(?:\s+[A-Za-z(]|$)")
# How far back a caption looks for the paragraph that announces it ("the parameters given in Table A6-1").
TABLE_LOOKBACK = 8


def table_parent(nodes, number):
    """The recent paragraph that names the table, else the paragraph the caption follows."""
    recent = [n for n in nodes[-TABLE_LOOKBACK:] if "table_of" not in n]
    for node in reversed(recent):
        if f"Table{number}" in re.sub(r"\s", "", node["text"]):
            return node["label"]
    return nodes[-1].get("table_of", nodes[-1]["label"])


def parse_pdf(path):
    """Return a list of {"label", "page", "text"} in document order."""
    nodes = {}
    current = None
    annex = ""
    annex_root = ""
    prev = ""

    def open_node(label, page_no, text):
        nonlocal current
        if label in nodes:
            current = nodes[label]
            current["text"] += " " + text
        else:
            current = nodes[label] = {"label": label, "page": page_no, "text": text}

    for page_no, page in enumerate(pymupdf.open(path), start=1):
        for line, is_heading in page_lines(page):
            annex_match = ANNEX.match(line)
            if annex_match and is_heading:
                number, appendix = annex_match.groups()
                annex_root = f"Annex {number}"
                annex = annex_root + (f" Appendix {appendix}" if appendix else "")
                open_node(annex, page_no, line)
                annex += " "
                prev = line
                continue
            part_match = PART.match(line) if annex_root else None
            if part_match:
                annex = f"{annex_root} Part {part_match.group(1)}"
                open_node(annex, page_no, line)
                annex += " "
                prev = line
                continue
            table_match = TABLE.match(line)
            if table_match and current is not None:
                parent = table_parent(list(nodes.values()), table_match.group(1))
                open_node(f"{parent}. Table {table_match.group(1)}", page_no, line)
                current["table_of"] = parent
                prev = line
                continue
            if current is None and line.startswith("Introduction"):
                open_node("Introduction", page_no, line)
                prev = line
                continue
            label_match = LABEL.match(line)
            prev_word = prev.split()[-1] if prev else ""
            if label_match and prev_word not in REFERENCE_WORDS:
                label = annex + (label_match.group(1) or label_match.group(3))
                open_node(label, page_no, label_match.group(2) or label_match.group(4))
            elif current is not None:
                current["text"] += " " + line
            prev = line
    for node in nodes.values():
        node.pop("table_of", None)
        node["text"] = norm(node["text"].replace("­", ""))
    return list(nodes.values())
