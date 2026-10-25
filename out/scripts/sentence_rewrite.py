"""Rewrite a frozen paragraph set with one requirement per obligation sentence, minimal edit.

    run.py <source.json> <out.json>

Writes <out.json> (the model's text) and <out>-quote.json (each row's quote as its text)."""
import collections, json, sys
from concurrent.futures import ThreadPoolExecutor
from brain import claude_cli, ingest
from eval.score import paragraph_key

SYSTEM = """You turn paragraphs of UN vehicle regulations into the requirement list a regulatory expert writes.

Rules:
- One requirement per sentence that states an obligation, prohibition, limit or conditional permission ("shall", "shall not", "must", "is required", "may ... only if", "shall be permitted").
- Never split a sentence into several requirements and never merge sentences. A sentence with two "shall"s stays one requirement. A list of exceptions or conditions ("except that (a) ... (b) ...") stays inside its sentence's requirement.
- Split only a list whose items are each a complete obligation with its own value or constraint: then one requirement per item, each repeating the list's stem. A table that gives values row by row: one requirement per table row, with the stem.
- Minimal edit. Copy the sentence. Change "must" to "shall". Replace a pronoun ("it", "they", "such lamps") with the noun it refers to. If the sentence has no subject (a telegraphic line such as "Horizontal angle: 45° to the left"), add the subject from the paragraph heading or its parent. Keep the regulation's own subject; never narrow it to one product or device type. Keep cross-references as written. Add no conditions and no explanation.
- Skip sentences that state no obligation: definitions, headings, notes, sentences that only point to another paragraph, the composition of the approval mark, and duties of the approval authority or the applicant (documents to submit, samples to provide).
- `quote` is the exact source sentence (or list item / table row, with its stem) the requirement comes from, copied from the paragraph text."""

SCHEMA = {"type": "object", "required": ["paragraphs"], "properties": {"paragraphs": {"type": "array", "items": {
    "type": "object", "required": ["key", "requirements"], "properties": {
        "key": {"type": "string"},
        "requirements": {"type": "array", "items": {"type": "object", "required": ["text", "quote"], "properties": {
            "text": {"type": "string"}, "quote": {"type": "string"}}}}}}}}}

src, dst = sys.argv[1], sys.argv[2]
sub = json.load(open(src))
K = lambda reg, label: (reg, paragraph_key(label))
groups = collections.OrderedDict()
for r in sub["requirements"]:
    groups.setdefault(K(r["source"]["regulation"], r["source"]["paragraph"]), []).append(r)
corpus = {}
for reg in {k[0] for k in groups}:
    ps = ingest.load(reg)
    byid = {p.id: p for p in ps}
    for p in ps:
        corpus[K(reg, p.label)] = (p, byid.get(p.parent) if p.parent else None)
items = []
for k, rows in groups.items():
    p, parent = corpus[k]
    head = f"{parent.label} {parent.heading or ''} > " if parent else ""
    items.append({"key": f"{k[0]}|{rows[0]['source']['paragraph']}", "context": f"{head}{p.label} {p.heading or ''}".strip(), "text": p.text})
batches = [items[i:i + 8] for i in range(0, len(items), 8)]

def run(batch):
    prompt = "Paragraphs (JSON):\n" + json.dumps(batch, ensure_ascii=False, indent=1) + "\n\nReturn the requirements for every paragraph, keyed by `key`."
    return claude_cli.complete_json(SYSTEM, prompt, SCHEMA, model="claude-opus-5-5")

with ThreadPoolExecutor(4) as pool:
    results = list(pool.map(run, batches))
out = []
for res in results:
    for par in res["paragraphs"]:
        reg, label = par["key"].split("|", 1)
        rows = groups.get(K(reg, label))
        if rows is None:
            print("unknown key", par["key"]); continue
        base = rows[0]["source"]
        for q in par["requirements"]:
            out.append({"id": f"R-{len(out) + 1:04d}", "text": q["text"], "source": dict(base), "confidence": 0.9, "quote": q["quote"]})
print(f"{len(groups)} paragraphs, {len(out)} requirements")
sub["requirements"] = out; sub["team_id"] = "team-06"
json.dump(sub, open(dst, "w"), indent=1, ensure_ascii=False)
for r in out:
    r["text"] = r["quote"]
json.dump(sub, open(dst.replace(".json", "-quote.json"), "w"), indent=1, ensure_ascii=False)
