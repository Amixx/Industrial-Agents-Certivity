"""Lane E of task 07: rows that are the regulation's own sentence, completed, never reworded.

    BRAIN_LLM= PYTHONPATH=. uv run python swing/e_verbatim.py candidates          # E1
    BRAIN_LLM=anthropic PYTHONPATH=. uv run python swing/e_verbatim.py run <variant> [model]
    BRAIN_LLM= PYTHONPATH=. uv run python swing/e_verbatim.py read <file> [n]     # E4

Selection is held fixed: the paragraphs cited by `out/rear-lamp-fable.json`. Each paragraph is
cut into sentences by `brain.obligations.sentences`. A model (Sonnet 5.5 on the API, cached;
`claude -p` was not logged in for lane agents) writes each row as a list of segments: `source`
segments must be verbatim substrings of the paragraph, `context` segments verbatim substrings of
the parent clause or heading path, and `added` segments are the few free words that name the
subject or join two clauses. The script checks every segment against the source text, so a
reworded sentence cannot slip through. Variants: v1 (base prompt), v2 (v1 plus EXTRA_V2),
v3 (base prompt plus EXTRA_V3, which replaces v2's list rule).
"""

from __future__ import annotations

import difflib
import json
import os
import re
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import median
from typing import Any

import anthropic.resources.beta.messages as M

from brain import llm
from brain.graph import Graph, build
from brain.ingest import load_all
from brain.models import Paragraph
from brain.obligations import sentences
from brain.rewrite import _heading_path, _parent_text
from eval import judge
from eval.score import fbeta

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
SOURCE = OUT / "rear-lamp-fable.json"
EXP = ROOT / "cases" / "dev-rear-lamp" / "expected.json"
CANDIDATES = OUT / "experiments" / "E-candidates.json"
BATCH = 8
WORKERS = 4
DEFAULT_MODEL = "claude-sonnet-5-5"
PRICE = {"claude-sonnet-5-5": (2, 10, 0.2), "claude-opus-5-5": (4, 20, 0.2)}
_usage: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])  # calls, in, out, cache read
_lock = threading.Lock()
_create = M.Messages.create


def _counted(self: Any, **kw: Any) -> Any:
    r = _create(self, **kw)
    u = r.usage
    with _lock:
        a = _usage[kw["model"]]
        a[0] += 1
        a[1] += u.input_tokens + (u.cache_creation_input_tokens or 0)
        a[2] += u.output_tokens
        a[3] += u.cache_read_input_tokens or 0
    return r


M.Messages.create = _counted  # type: ignore[method-assign]


def spend() -> float:
    total = 0.0
    for m, (c, i, o, cr) in _usage.items():
        pi, po, pc = PRICE.get(m, (10, 50, 1))
        cost = (i * pi + o * po + cr * pc) / 1e6
        total += cost
        print(f"[cost] {m}: {c} new calls, {i:,} in / {o:,} out / {cr:,} cache read; ${cost:.2f}")
    print(f"[cost] total new spend ${total:.2f}")
    return total


SYSTEM = """You turn paragraphs of UN Regulations into engineering requirements for a product,
without rewording the regulation. Each requirement is the regulation's own sentence, completed
so that it stands alone. You never paraphrase, reorder or shorten a sentence's own words.

You write each requirement as a list of segments, joined in order with spaces:
- {"kind": "source", "text": ...}: text copied character for character from the paragraph's
  `text`. Normally one whole sentence from `sentences`.
- {"kind": "context", "text": ...}: text copied character for character from `parent_text`
  or `heading_path`, used to carry the parent's condition ("After each impact test made in
  accordance with ...,") into a child that completes the parent's clause, or to say what a
  sentence is about when only the heading says it.
- {"kind": "added", "text": ...}: at most eight free words, only to name the subject or join
  segments: "The rear position lamp", "The reversing lamp shall be", ", except that",
  "When". The subject comes from the heading path or the product, in the regulation's own
  terms.

Per sentence, decide one of:
1. Drop it: it states no obligation (definitions, scope notes, statements of purpose,
   administrative steps of the approval authority, permissions with no constraint, notes,
   footnotes, table captions and table cells).
2. Keep it as is: one source segment with the whole sentence, when it already names its
   subject and its condition.
3. Complete it: add the subject where the sentence has a pronoun ("It", "They", "Such lamps")
   or no subject (telegraphic "In height: not less than 250 mm ..."), and carry the condition
   from the parent clause when the paragraph completes it. Replace a leading pronoun by
   starting the source segment after the pronoun and putting the subject in an added segment
   before it. For a telegraphic sentence, put "The <subject> shall be" in an added segment and
   the source segment from the first word after the colon.

Rules:
- Segments may interleave: source, added, source. Use that to name the device where the
  sentence names none: "The colour of light emitted" + added "by the rear position lamp" +
  source "shall be red." (the device from the heading path, never a vaguer word). Use it to
  keep what the paragraph's heading says when the sentence leaves it out: source "... shall meet
  the requirements in Table 9" + added "for" + context "<the heading's words>".
- Every requirement names its subject and keeps every condition that governs it ("When tested
  in accordance with ...", "In the case of ...", "If ..."). Never drop a condition.
- One requirement per sentence that carries an obligation. Do not merge two obligation
  sentences, except that a "However, ..." sentence joins the sentence it restricts: source
  segment, added ", except that", source segment starting after "However,".
- Split a sentence only where the source has a list or a table with its own values: each
  lettered or numbered item that states its own limit becomes its own requirement, made of the
  list's lead-in (source segment) plus the item (source segment). Do not split two limits that
  share one sentence without a list.
- A sentence that points to a table ("shall meet the requirements in Table 7") is one
  requirement; do not copy table cells.
- Keep a permission as a permission; never turn "may" into "shall". Keep "may" sentences only
  when they carry a constraint (a limit, a condition, "only if").
- Ignore footnote markers glued to words; copy them as they are rather than editing a segment.
- Return an empty list for a paragraph with no obligation.

Example (UN R127 5.1.2, heading path: Specifications > Legform test to bumper):
text: "Upper legform to bumper When tested in accordance with Annex 5, paragraph 2. (upper
legform to bumper), the instantaneous sum of the impact forces with respect to time shall not
exceed 7.5 kN and the bending moment on the test impactor shall not exceed 510 Nm. The upper
legform impactor shall be certified pursuant to Annex 6, paragraph 2."
-> [{"kind": "source", "text": "When tested in accordance with Annex 5, paragraph 2. (upper
legform to bumper), the instantaneous sum of the impact forces with respect to time shall not
exceed 7.5 kN and the bending moment on the test impactor shall not exceed 510 Nm."}]
-> [{"kind": "source", "text": "The upper legform impactor shall be certified pursuant to
Annex 6, paragraph 2."}]

Example (UN R42 6.1.4, parent_text: "After each impact test made in accordance with the
conditions and procedure specified in annex 3 to this Regulation, the vehicle shall meet the
following requirements:"):
text: "The vehicle's exhaust system shall not suffer any damage or displacement which would
prevent its normal function."
-> [{"kind": "context", "text": "After each impact test made in accordance with the conditions
and procedure specified in annex 3 to this Regulation,"}, {"kind": "source", "text": "The
vehicle's exhaust system shall not suffer any damage or displacement which would prevent its
normal function."}]

Example (UN R42 6.2, heading path: Requirements > Protective devices):
text: "They shall be so designed that the vehicle can be towed without damage."
-> [{"kind": "added", "text": "The protective devices"}, {"kind": "source", "text": "shall be
so designed that the vehicle can be towed without damage."}]"""

# v2: fixes for what v1 lost against Fable (telegraphic labels, demonstratives, lists inside a
# sentence, conditions stated once at the paragraph start, imperatives, qualifying sentences).
EXTRA_V2 = """

Additional rules (they override the rules above where they differ):
- Telegraphic sentence "Horizontal angle: 45° inwards and 80° outwards": never copy the label
  and its colon into the requirement. Write added "The horizontal angle of the rear position
  lamp shall be" + source "45° inwards and 80° outwards", using the label's words and the
  device from the heading path. Same for "In height: ..." -> "The <device> shall be" + source.
  A heading like "Electrical connections: In accordance with paragraph 5.11." becomes added
  "The electrical connections of the <device> shall be" + source "in accordance with ...".
- A demonstrative or pronoun subject that points back ("This sequential number", "It",
  "They", "Such lamps") is replaced by the full noun phrase it refers to, copied as a source
  segment from the earlier sentence ("The four to six-digit sequential number, being part of
  the approval number prescribed in paragraph 3.2.3.2.,") followed by the rest of the sentence.
- A condition stated once for the whole paragraph or its parent ("If not otherwise agreed
  between ...", "If not otherwise specified:", "In the case of ...", "In case of
  retro-reflectors" in the heading path) is repeated in every requirement it governs, copied
  as a source or context segment.
- A list inside one sentence ("shall be such that (a) ...; and (b) ...; and (c) ...", "the
  following conditions: (a) ... (b) ...") becomes one requirement per item: the lead-in up to
  the list (source segment, with its subject and condition) + the item without its marker
  (source segment, without the trailing "; and" or "; or"). Do not also write the whole list as
  one requirement.
- An imperative sentence ("Apply the starting profile according to ISO 16750-2 to the supply
  lines ...") becomes source "the starting profile according to ISO 16750-2" + added "shall be
  applied" + source "to the supply lines ...".
- A sentence that only qualifies the obligation before it (a tolerance "In each direction a
  tolerance of ±3° shall be allowed", an exception "However, ...") joins that requirement:
  source + added ", with" or ", except that" + source.
- Never keep a sentence whose subject is a document or the authority (the communication form,
  the Type Approval Authority, the technical service) unless it constrains the product."""

# v3 replaces EXTRA_V2. v2's "one requirement per list item" dropped the marking list and the
# small "may vary" list; v3 splits only items that are their own marking or limit, and it
# requires the device even when a property is already the grammatical subject.
EXTRA_V3 = """

Additional rules (they override the rules above where they differ):

Lists. When `sentences` is empty, or a sentence is only a marker such as "(a)" or "(i)",
ignore `sentences` and read `text`.
- Each lettered or numbered item that is its own marking or its own limit is its own
  requirement. Copy the condition that governs the list onto every item, then an added
  subject and verb taken from the list header, then the item's own words with the marker
  left off. Do not glue on "bear the following markings. (a) On the ...: (i)", and do not
  drop the items.
  Text: "In case replaceable light source module(s) is/are used, bear the following
  markings. (a) On the light source module(s): (i) The trade name or mark of the applicant;"
  -> [{"kind": "source", "text": "In case replaceable light source module(s) is/are used,"},
  {"kind": "added", "text": "the light source module(s) shall bear"},
  {"kind": "source", "text": "the trade name or mark of the applicant."}]
  The subject is copied from "(a) On the light source module(s)". Items under "(b) On the
  lamp:" use "the lamp shall bear" and the same opening condition.
- A short list that is one permission or one obligation, with a proviso that covers every
  item, stays one requirement. Copy the lead-in, every item and the closing proviso. Do not
  split it, and do not drop it because it says "may".
  "The photometric characteristics of any lamp may vary: (a) ...; (b) ...; or (c) ...;
  provided that any variation in the photometric characteristics is in compliance with the
  technical provisions for the lamp concerned." is one requirement.
- A paragraph whose obligation is "shall meet the requirements in Table N" is one
  requirement. Never copy table cells, even when `sentences` is empty.
- Lettered exceptions under one angle join that angle's requirement. They are not separate
  limits.

Telegraphic labels. Never leave the label or its colon in the requirement. Never write
"shall be In", "shall be Horizontal" or "shall have a Closed-circuit".
- "Horizontal angle: 45° inwards and 80° outwards." -> added "The horizontal angle of the"
  + context "<device, copied from the heading path>" + added "shall be" + source "45°
  inwards and 80° outwards." A later "However, ..." in that paragraph joins this requirement:
  added ", except that" + source starting after "However,".
- Heading "Electrical connections" and sentence "In accordance with paragraph 5.11." ->
  added "The electrical connections of the" + context "<device>" + added "shall be" + source
  "in accordance with paragraph 5.11." The source starts with a lowercase letter. Each added
  segment stays within eight words; the device is context, not added. The "However, if ..."
  sentence in that paragraph joins the same requirement.
- "Tell-tale. Closed-circuit tell-tale mandatory." -> added "The" + context "<device>" +
  added "shall have a mandatory" + source "closed-circuit tell-tale." Join "It shall be
  combined with ..." and "This requirement does not apply when ..." onto that same
  requirement. A later "However, a tell-tale indicating failure is mandatory ..." is its own
  requirement: it names a different tell-tale. Keep its words and add the device from the
  heading as context.
- A marking sentence with no modal is still an obligation. "On lamps which cannot be mounted
  on either side of the vehicle indiscriminately, a horizontal arrow showing in which
  position the lamp is to be mounted." -> source "On lamps which cannot be mounted on either
  side of the vehicle indiscriminately," + added "the lamp shall bear" + source "a horizontal
  arrow showing in which position the lamp is to be mounted."

The device. Insert it even when the sentence already has a grammatical subject, if that
subject is a property (colour of the light, intensity, an angle, a height, a number,
presence, a tell-tale, electrical connections) and the heading path names the device. Copy
the device's words from `heading_path` as a context segment. Do not invent a shorter name.
Heading path ending "Rear position lamps", text "Colour: The colour of light emitted shall
be red.":
[{"kind": "source", "text": "The colour of light emitted"}, {"kind": "added", "text": "by the"},
{"kind": "context", "text": "rear position lamps"}, {"kind": "source", "text": "shall be red."}]

Qualifying sentences join the requirement they restrict, and every word of both sentences
stays. Join with an added ", and". For a sentence that starts with "However,", join with
", except that" and a source segment that starts after "However,". A following sentence that
exempts someone ("are not subject", "does not apply", "This requirement does not apply")
joins the same way. Do not rewrite "In each direction a tolerance of ±3° shall be allowed"
as "with a tolerance of ±3° shall be allowed". Write the first sentence, then ", and", then
"in each direction a tolerance of ±3° shall be allowed."

Other:
- A condition stated once for the paragraph ("In case ...", "If not otherwise specified",
  "If not otherwise agreed between ...") opens every requirement it governs.
- A pronoun or demonstrative ("It", "They", "This sequential number", "Such lamps") is
  replaced by the noun phrase it refers to, copied as a source segment from the earlier
  sentence, then the rest of the sentence.
- An imperative ("Apply the starting profile according to the International Standard
  ISO 16750-2 to the supply lines ...") becomes that profile as a source segment, added
  "shall be applied", then the rest as a source segment. The next sentence that says who
  "is not subject" joins with ", except that".
- An added segment is at most eight words. A longer subject or condition is a source or
  context segment, not a paraphrase in added words.
- Keep a "may" sentence that carries a limit or a proviso."""

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "paragraphs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "requirements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "segments": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "kind": {
                                                "type": "string",
                                                "enum": ["source", "context", "added"],
                                            },
                                            "text": {"type": "string"},
                                        },
                                        "required": ["kind", "text"],
                                        "additionalProperties": False,
                                    },
                                }
                            },
                            "required": ["segments"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["id", "requirements"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["paragraphs"],
    "additionalProperties": False,
}

_WS = re.compile(r"\s+")
_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})
_WORD = re.compile(r"[a-z0-9]+(?:[.,]\d+)*")
_LOWER_FIRST = re.compile(
    r"^(The|A|An|Each|Every|All|Any|This|These|Such|No|Where|When|If|In|On|For|After|"
    r"Before|During|Provided|However|It|They|See|With|To|By|Of|From|At|Under|Over|And|Or|Not)\b"
)
_PROPER = re.compile(
    r"^(Table|Annex|Figure|Class|Zone|Paragraph|Regulation|Appendix|Part|ISO|UN|LED)\b"
)
_MARKER_SENT = re.compile(r"^\([A-Za-z0-9]+\)")
_AFTER = {"be", "a", "an", "the", "of"}


def norm(text: str) -> str:
    return _WS.sub(" ", text.translate(_QUOTES)).strip()


def words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def load() -> tuple[list[Paragraph], Graph, str, dict[str, Any]]:
    source = json.loads(SOURCE.read_text())
    rows = source["requirements"]
    corpus = load_all("base")
    regs = sorted({r["source"]["regulation"] for r in rows})
    graph = build({r: corpus[r] for r in regs}, set(corpus))
    by_label = {(p.regulation, p.label): p for r in regs for p in corpus[r]}
    keys = dict.fromkeys((r["source"]["regulation"], r["source"]["paragraph"]) for r in rows)
    paragraphs = [by_label[k] for k in keys if k in by_label]
    return paragraphs, graph, source.get("profile", {}).get("product", ""), source


def body(p: Paragraph) -> str:
    text = p.text
    if p.heading and text.startswith(p.heading):
        text = text[len(p.heading) :].strip()
    return text


def candidates(paragraphs: list[Paragraph], graph: Graph) -> list[dict[str, Any]]:
    return [
        {
            "id": p.id,
            "label": f"{p.regulation} {p.label}",
            "heading_path": _heading_path(p, graph),
            "parent_text": _parent_text(p, graph),
            "text": p.text[:4000],
            "sentences": [s for _, s in sentences(body(p)[:4000])],
        }
        for p in paragraphs
    ]


PROMPTS = {"v1": SYSTEM, "v2": SYSTEM + EXTRA_V2, "v3": SYSTEM + EXTRA_V3}


_CELL_START = re.compile(r"^(?:table\b|\([a-z]\)\))", re.IGNORECASE)


def _cell(sentence: str) -> bool:
    """A dumped table, not a real obligation sentence that happens to mention a table."""
    text = sentence.strip()
    if _CELL_START.match(text):
        return True
    if len(text) > 400 and "table" in text[:80].lower():
        return True
    digits = sum(ch.isdigit() for ch in text)
    return len(text) > 500 and digits > 30


def prompt_view(cand: dict[str, Any], variant: str) -> dict[str, Any]:
    """For v3, hide splitter fragments of a list, and hide dumped table cells."""
    if not variant.startswith("v3"):
        return cand
    out = dict(cand)
    sents: list[str] = list(out["sentences"])
    cells = [s for s in sents if _cell(s)]
    kept = [s for s in sents if s not in cells]
    markers = [s for s in kept if _MARKER_SENT.match(s.strip())]
    if len(markers) >= 2:
        out["sentences"] = []
        out["read"] = "text; the splitter broke this list"
    elif cells and kept:
        out["sentences"] = kept
        out["read"] = "table cells removed; cite the table, do not copy cells"
    elif cells:
        out["sentences"] = sents[:1]
        out["read"] = "table cells removed; cite the table, do not copy cells"
    return out


def ask(
    chunk: list[dict[str, Any]],
    product: str,
    model: str,
    system: str = SYSTEM,
    *,
    tail: str = "",
) -> dict[str, Any]:
    listing = "\n\n".join(json.dumps(c, ensure_ascii=False) for c in chunk)
    prompt = (
        f"Product: {product}\n\nParagraphs (JSON lines):\n\n{listing}\n\n"
        "Return the requirements for every paragraph id, as segments." + tail
    )
    os.environ["BRAIN_MODEL_BULK"] = model
    return llm.complete_json(system, prompt, SCHEMA, tier="bulk", max_tokens=32000)


def snap(segment: str, haystack: str) -> tuple[str, str]:
    """(text, status): the segment if it is verbatim in `haystack`, else the source span it was
    copied from when at least 90% of it matches ('snapped'), else the segment ('unverified')."""
    seg = norm(segment)
    if not seg or seg.lower() in haystack.lower():
        return seg, "verbatim"
    sm = difflib.SequenceMatcher(None, haystack, seg, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 4]
    if blocks and sum(b.size for b in blocks) >= 0.9 * len(seg):
        start, end = blocks[0].a, blocks[-1].a + blocks[-1].size
        if end - start <= 1.2 * len(seg):
            return haystack[start:end], "snapped"
    return seg, "unverified"


def _join(text: str, piece: str) -> str:
    """Lowercase a continuation, so 'shall be' + 'In accordance' does not keep the capital."""
    if not text or text.endswith((".", ":", "!", "?")) or _PROPER.match(piece):
        return piece
    prev = text.rstrip().rsplit(" ", 1)[-1].lower()
    if _LOWER_FIRST.match(piece) or (prev in _AFTER and re.match(r"^[A-Z][a-z]", piece)):
        return piece[0].lower() + piece[1:]
    return piece


def assemble(segments: list[dict[str, str]], src: str, parent: str) -> tuple[str, str, dict]:
    text, quote, stats = "", [], {"verbatim": 0, "snapped": 0, "unverified": 0, "added": 0}
    for s in segments:
        kind, piece = s["kind"], s["text"]
        if kind == "added":
            piece = norm(piece)
            stats["added"] += len(words(piece))
        else:
            piece, status = snap(piece, src if kind == "source" else parent)
            stats[status] += 1
            if kind == "source":
                quote.append(piece)
        if not piece:
            continue
        piece = _join(text, piece)
        if piece.startswith((",", ";", ".")):
            text = text.rstrip().removesuffix(".") + piece
        else:
            text = f"{text} {piece}" if text else piece
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
        text = text.rstrip(" ;:,") + ("" if text.endswith(".") else ".")
    return text, " ".join(quote), stats


def share(text: str, reference: str) -> float:
    ref = set(words(reference))
    ws = words(text)
    return sum(w in ref for w in ws) / max(1, len(ws))


def run(variant: str, model: str) -> int:
    paragraphs, graph, product, source = load()
    cands = candidates(paragraphs, graph)
    by_id = {p.id: p for p in paragraphs}
    shown = [prompt_view(c, variant) for c in cands]
    chunks = [shown[i : i + BATCH] for i in range(0, len(shown), BATCH)]
    if llm.provider() != "anthropic":
        raise SystemExit("set BRAIN_LLM=anthropic (paid; approved cap $3 for lane E)")
    reshaped = sum(1 for c in shown if c.get("read"))
    print(f"{len(cands)} paragraphs in {len(chunks)} calls to {model}; {reshaped} reshaped")
    tail = ""
    if variant.startswith("v3"):
        tail = (
            " Where sentences is empty, read text. Where read says not to copy table cells, do not."
        )

    def safe(chunk: list[dict[str, Any]]) -> dict[str, Any]:
        try:
            return ask(chunk, product, model, PROMPTS[variant.split("-")[0]], tail=tail)
        except Exception as e:  # one failed call should not end the run; rerun picks it up
            print(f"call failed: {e!r:.200}", file=sys.stderr)
            return {"paragraphs": []}

    with ThreadPoolExecutor(WORKERS) as pool:
        answers = list(pool.map(safe, chunks))
    rows: list[dict[str, Any]] = []
    totals = {"verbatim": 0, "snapped": 0, "unverified": 0, "added": 0}
    answered: set[str] = set()
    seen: set[tuple[str, str]] = set()
    for answer in answers:
        for item in answer["paragraphs"]:
            p = by_id.get(item["id"])
            if p is None:
                continue
            answered.add(p.id)
            parent = norm(_parent_text(p, graph) + " " + _heading_path(p, graph))
            for r in item["requirements"]:
                text, quote, stats = assemble(r["segments"], norm(p.text), parent)
                if len(text) < 15 or (p.id, text) in seen:
                    continue
                seen.add((p.id, text))
                for k, v in stats.items():
                    totals[k] += v
                rows.append(
                    {
                        "id": f"R-{len(rows) + 1:04d}",
                        "text": text,
                        "source": {
                            "regulation": p.regulation,
                            "version": p.version,
                            "page": p.page,
                            "paragraph": p.label,
                        },
                        "quote": quote[:1000],
                        "share": round(share(text, p.text), 3),
                        "share_ctx": round(share(text, p.text + " " + parent), 3),
                        "added_words": stats["added"],
                    }
                )
    missing = [p.id for p in paragraphs if p.id not in answered]
    out = {"team_id": "team-06", "case_id": source["case_id"], "requirements": rows}
    path = OUT / f"rear-lamp-swing-E-{variant}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    exp = json.loads(EXP.read_text())["requirements"]
    m = len(judge.match(rows, exp))
    gm = len(judge.match(source["requirements"], exp))
    f2 = fbeta(m / max(1, len(rows)), m / len(exp))
    gold_share = gold_shares()
    print(f"wrote {path.relative_to(ROOT)}")
    print(f"paragraphs answered {len(answered)} of {len(paragraphs)}; missing {missing[:10]}")
    print(f"segments {totals}")
    if not rows:
        print("no rows")
        spend()
        return 1
    print(
        f"word share vs paragraph: median {median(r['share'] for r in rows):.3f}, "
        f"with parent: {median(r['share_ctx'] for r in rows):.3f}; gold {gold_share:.3f}"
    )
    print(f"rows with added words: {sum(r['added_words'] > 0 for r in rows)}")
    print(describe(rows))
    print(f"{path.name}: rows {len(rows)} matched {m} F2 {f2:.3f} (local lexical judge)")
    print(f"{SOURCE.name}: rows {len(source['requirements'])} matched {gm}")
    spend()
    return 0


def describe(rows: list[dict[str, Any]]) -> str:
    """Word-share distribution and how much of each row is added words (E3)."""
    shares = [float(r["share"]) for r in rows]
    adds = [int(r.get("added_words") or 0) for r in rows]

    def band(value: float) -> str:
        if value >= 0.999:
            return "1.00"
        if value >= 0.95:
            return "0.95-0.99"
        if value >= 0.90:
            return "0.90-0.94"
        if value >= 0.80:
            return "0.80-0.89"
        return "<0.80"

    share_b: dict[str, int] = defaultdict(int)
    for value in shares:
        share_b[band(value)] += 1
    add_b = {"0": 0, "1-8": 0, ">8": 0}
    for count in adds:
        add_b["0" if count == 0 else "1-8" if count <= 8 else ">8"] += 1
    ratios = []
    for row, count in zip(rows, adds, strict=True):
        n = len(words(row["text"]))
        ratios.append(count / n if n else 0.0)
    order = ("1.00", "0.95-0.99", "0.90-0.94", "0.80-0.89", "<0.80")
    share_txt = ", ".join(f"{name} {share_b[name]}" for name in order)
    return "\n".join(
        [
            f"rows {len(rows)} (Fable 332)",
            f"word share vs paragraph: median {median(shares):.3f}; {share_txt}",
            (
                f"added words: sum {sum(adds)}, rows with any {sum(c > 0 for c in adds)}, "
                f"over 8 {add_b['>8']}, max {max(adds) if adds else 0}; "
                f"median fraction of the row that is added words {median(ratios):.3f}"
            ),
            f"added buckets: 0 {add_b['0']}, 1-8 {add_b['1-8']}, >8 {add_b['>8']}",
        ]
    )


def gold_shares() -> float:
    corpus = load_all("base")
    by_label = {(p.regulation, p.label): p for ps in corpus.values() for p in ps}
    exp = json.loads(EXP.read_text())["requirements"]
    vals = [
        share(r["text"], by_label[k].text)
        for r in exp
        if (k := (r["source"]["regulation"], r["source"]["paragraph"])) in by_label
    ]
    return median(vals)


def read(path: str, n: int) -> int:
    import random

    rows = json.loads(Path(path).read_text())["requirements"]
    random.seed(7)
    for r in random.sample(rows, min(n, len(rows))):
        s = r["source"]
        tag = f"share {r.get('share')} +{r.get('added_words')}"
        print(f"[{s['regulation']} {s['paragraph']}] {tag}")
        print(f"  {r['text']}\n")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] == "candidates":
        paragraphs, graph, _, _ = load()
        cands = candidates(paragraphs, graph)
        CANDIDATES.write_text(json.dumps(cands, indent=1, ensure_ascii=False))
        n = sum(len(c["sentences"]) for c in cands)
        print(f"{len(cands)} paragraphs, {n} sentences -> {CANDIDATES.relative_to(ROOT)}")
        return 0
    if argv[0] == "run":
        model = argv[2] if len(argv) > 2 else DEFAULT_MODEL
        return run(argv[1], model)
    if argv[0] == "read":
        return read(argv[1], int(argv[2]) if len(argv) > 2 else 20)
    if argv[0] == "stats":
        gold = gold_shares()
        for path in argv[1:]:
            rows = json.loads(Path(path).read_text())["requirements"]
            print(f"== {path}")
            print(describe(rows))
            print(f"gold median word share {gold:.3f}")
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
