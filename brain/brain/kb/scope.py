"""Scope statements per regulation, and the regulation's role read from its scope wording."""

from __future__ import annotations

import hashlib
import re
import sqlite3

PROV = "rule:scope"
_HEADING = re.compile(r"^\s*(?:application\s*/\s*)?(?:scope|purpose)\b", re.I)
_APPLIES = re.compile(
    r"\bThis\s+(?:UN\s+)?(?:Regulation|global\s+technical\s+regulation|gtr)\b"
    r"(?:\s*\([^)]*\))?[^.]{0,80}?\b(?:applies|shall\s+apply|is\s+applicable)\b",
    re.I,
)
_SENTENCE_END = re.compile(r"\.(?=\s+[A-Z\d]|\s*$)")
_FOOTNOTE = re.compile(
    r"(?:\s*\*?\s*\d{0,2}\s*/?\s*\*?\s*"
    r"(?:As defined in|Also called|As referred to in|As specified in)\b"
    r"|(?<=[.;:\s])\d{1,2}(?=[A-Z][a-z])"
    r"|(?<=[.;:]\s)[^.;]*?\bConsolidated Resolution\b).*$",
    re.S,
)
_URL = re.compile(r"\s*-?\s*(?:https?://|www\.)\S+")
_MARKERS = (
    re.compile(r"\s\*(?=\s)"),
    re.compile(r"\s\d{1,2}/(?=[\s.,;]|$)"),
    re.compile(r"(?<=[.;])\s\d{1,2}(?=\s+[A-Z][a-z])"),
    re.compile(r"(?<=[).;,])\d{1,2}(?=\s|$)"),
    re.compile(r"(?<=\b[LMNOT]\d)\s?\d(?=\s+(?:of|with|and|\*)\b)"),
    re.compile(r"(?<=\b[LMNOT]\d)\.\d(?=\s+[A-Z])"),
)
_BUDGET = 1500


def clean_text(text: str) -> str:
    """Scope text without footnotes, footnote markers or URLs. Each line is one node's text, so
    a footnote at the end of one node does not take the following nodes with it."""
    return re.sub(r"\s+", " ", " ".join(_clean_node(line) for line in text.splitlines())).strip()


def _clean_node(text: str) -> str:
    text = _FOOTNOTE.sub("", text)
    text = _URL.sub("", text)
    for marker in _MARKERS:
        text = marker.sub("", text)
    return re.sub(
        r"^\s*(?:application\s*/\s*)?(?:scope|purpose)(?:\s+and\s+purpose)?\s*",
        "",
        text,
        flags=re.I,
    )


def _sentence(text: str, start: int) -> str:
    end = _SENTENCE_END.search(text, start)
    return text[start : end.end() if end else len(text)]


def _candidates(rows: list[sqlite3.Row], is_gtr: bool) -> list[tuple[str | None, str, float, str]]:
    children: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        if row["parent_id"]:
            children.setdefault(row["parent_id"], []).append(row)
    regulation_text_from = next(
        (r["ord"] for r in rows if re.search(r"\bText of the Regulation\b", r["text"], re.I)), None
    )
    out: list[tuple[str | None, str, float, str]] = []
    for row in rows:
        if row["annex"] and row["label"] != "preamble":
            continue
        if row["label"].startswith("Rationale"):
            continue
        heading = row["heading"] or row["text"][:40]
        if row["label"] != "preamble" and _HEADING.match(heading):
            text = row["text"]
            for child in children.get(row["id"], []):
                if len(text) >= _BUDGET:
                    break
                text += "\n" + child["text"]
            in_part_b = regulation_text_from is not None and row["ord"] > regulation_text_from
            purpose = re.match(r"^\s*purpose\b", heading, re.I) is not None
            if is_gtr and in_part_b:
                rule, confidence = "gtr_part_b_scope", 0.95 if not purpose else 0.6
            else:
                rule, confidence = "scope_heading", 0.9 if not purpose else 0.6
            if not _APPLIES.search(text):
                confidence -= 0.2
            out.append((row["id"], text[:_BUDGET], confidence, rule))
            continue
        for match in _APPLIES.finditer(row["text"]):
            text = _sentence(row["text"], match.start())
            confidence = (
                0.85 if re.search(r"\bscope\s*$", row["text"][: match.start()], re.I) else 0.7
            )
            if row["label"] == "preamble" and confidence < 0.85:
                confidence = 0.5
            out.append((row["id"], text[:_BUDGET], confidence, "applies_sentence"))
    return out


_OBJECT = re.compile(r"\b(?:applies|shall\s+apply)\s+to\b:?(.{0,160})", re.I | re.S)
_VEHICLE = re.compile(r"\bvehicles?\b", re.I)
_DEVICE = re.compile(
    r"\b(?:lamps?|devices?|reflectors?|markings?|light sources|systems?|tyres|glazing|equipment|"
    r"modules?|immobili[sz]ers?|indicators?|projectors?)\b",
    re.I,
)


def _role(scope: str, title: str, regulation: str) -> tuple[str, str]:
    if regulation.startswith("UN GTR"):
        return "gtr", "regulation is a global technical regulation"
    if re.search(r"electromagnetic compatibility", f"{title} {scope}", re.I):
        return "emc", "scope names electromagnetic compatibility"
    if re.search(r"\bwith regard to the installation of\b", scope, re.I) or re.match(
        r"installation of\b", title, re.I
    ):
        return "installation", "scope covers the installation of devices"
    if re.search(r"\blight sources?\b", title, re.I):
        return "light_source", "title names light sources"
    target = _OBJECT.search(scope)
    if target is None:
        return "device_approval", "no scope wording; default"
    vehicle, device = _VEHICLE.search(target[1]), _DEVICE.search(target[1])
    if vehicle and (device is None or vehicle.start() < device.start()):
        return "vehicle_approval", "scope applies to vehicles"
    if device:
        return "device_approval", f"scope applies to {device[0].casefold()}"
    return "device_approval", "scope names neither vehicles nor devices; default"


def load(conn: sqlite3.Connection) -> int:
    """Replace the scope candidates, mark the best one per regulation and set `role_doc`."""
    conn.execute("DELETE FROM scope_candidate")
    cur = conn.cursor()
    cur.row_factory = sqlite3.Row
    total = 0
    regulations = conn.execute("SELECT id, title FROM regulation ORDER BY id").fetchall()
    for regulation, title in regulations:
        rows = cur.execute(
            "SELECT id, label, annex, parent_id, ord, heading, text FROM node "
            "WHERE regulation=? ORDER BY ord",
            (regulation,),
        ).fetchall()
        found = _candidates(rows, regulation.startswith("UN GTR"))
        seen: set[tuple[str | None, str]] = set()
        unique = []
        for node_id, raw, confidence, rule in found:
            if (node_id, raw) not in seen:
                seen.add((node_id, raw))
                unique.append((node_id, raw, confidence, rule))
        best = min(range(len(unique)), key=lambda i: (-unique[i][2], i)) if unique else None
        for i, (node_id, raw, confidence, rule) in enumerate(unique):
            key = hashlib.sha256(f"scope:{node_id}:{rule}:{raw}".encode()).hexdigest()
            conn.execute(
                "INSERT INTO scope_candidate VALUES (?,?,?,?,?,?,?,?)",
                (key, regulation, node_id, rule, confidence, raw, clean_text(raw), int(i == best)),
            )
        total += len(unique)
        scope_text = clean_text(unique[best][1]) if best is not None else ""
        role, reason = _role(scope_text, title, regulation)
        provenance = f"{PROV}:{regulation}"
        conn.execute(
            "INSERT OR REPLACE INTO provenance VALUES (?,?,?,?,?)",
            (provenance, "rule", None, None, f"role_doc {role}: {reason}"),
        )
        conn.execute(
            "UPDATE regulation SET role_doc=?, provenance_id=? WHERE id=?",
            (role, provenance, regulation),
        )
    return total
