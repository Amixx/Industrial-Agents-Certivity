"""Rewrite given rows as standalone sentences in the regulation's own words, one text per row.

    run.py <rows.json> <out.json>
"""
import collections, json, sys
from concurrent.futures import ThreadPoolExecutor
from brain import claude_cli, ingest
from eval.score import paragraph_key

SYSTEM = """You fix requirement rows taken from UN vehicle regulations. Each row was cut from a list item, table row or clause, so on its own it is not a complete requirement. Rewrite each row as ONE standalone requirement sentence, as a regulatory expert would write it.

Rules:
- Use the regulation's own words. Copy the item's wording, values, units and cross-references exactly.
- Take the subject, the verb ("shall", "shall bear", "shall be such that") and any condition ("where the device has a variable intensity control", "for vehicles of category N") from the lead-in sentence, the paragraph heading or the table's caption and column headers.
- Keep the regulation's own subject ("lamps", "the device", "the vehicle"). Never replace it with the name of one product.
- A table row: state every column's value together with what that column means, e.g. a row "B  0.8 cd  40 cd" under the columns "Category | Minimum | Maximum" of a table of luminous intensity becomes "For category B, the luminous intensity shall be not less than 0.8 cd and not more than 40 cd, as specified in Table X."
- State only what this row covers. Don't merge in other items and don't add explanation.
- If the row is already a complete requirement sentence, return it unchanged.
- Return exactly one text per row id."""

SCHEMA = {"type": "object", "required": ["rows"], "properties": {"rows": {"type": "array", "items": {
    "type": "object", "required": ["id", "text"], "properties": {"id": {"type": "string"}, "text": {"type": "string"}}}}}}

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
    head = f"{parent.label} {parent.heading or ''}: {(parent.text or '')[:600]}\n> " if parent else ""
    items.append({"paragraph": f"{k[0]} {p.label} {p.heading or ''}".strip(), "context": head.strip(), "text": p.text,
                  "rows": [{"id": r["id"], "row": r["text"]} for r in rows]})
batches = [items[i:i + 6] for i in range(0, len(items), 6)]

def run(batch):
    prompt = "Paragraphs with their rows (JSON):\n" + json.dumps(batch, ensure_ascii=False, indent=1) + "\n\nReturn one standalone text for every row id."
    return claude_cli.complete_json(SYSTEM, prompt, SCHEMA, model="claude-opus-5-5")

with ThreadPoolExecutor(4) as pool:
    results = list(pool.map(run, batches))
new = {x["id"]: x["text"] for res in results for x in res["rows"]}
missing = [r["id"] for r in sub["requirements"] if r["id"] not in new]
print(f"{len(groups)} paragraphs, {len(new)} texts, missing {missing}")
for r in sub["requirements"]:
    r["text"] = new.get(r["id"], r["text"])
sub["team_id"] = "team-06"
json.dump(sub, open(dst, "w"), indent=1, ensure_ascii=False)
