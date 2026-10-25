"""Add one row per uncovered obligation in long body paragraphs that carry several numeric limits.
    split_repair.py <in.json> <out.json>
A paragraph qualifies when it is outside an annex, is at least 600 characters, states 3+ numeric
limits and already has 2+ rows. Opus splits it into verbatim quotes, one per obligation or limit;
quotes no existing row of the paragraph covers become new rows."""
import copy, json, re, sys
from collections import OrderedDict
from brain import claude_cli, ingest
LIMIT = re.compile(r'\d[\d,.]*\s*(?:mm|cm|m\b|°|%|V\b|MHz|Hz|cd\b|km/h)')
norm = lambda s: re.sub(r'\s+', ' ', s).strip()
key = lambda s: (s['regulation'], s['paragraph'].strip().rstrip('.').lower())
SYSTEM = """You split one paragraph of a vehicle regulation into the separate requirements a regulatory expert would list for type approval.
One item per distinct obligation, numeric limit, angle, range or test condition that a product must meet. A list of alternatives or conditions under one obligation stays one item.
Each item is an exact, contiguous quote from the paragraph (copy the words verbatim), long enough to state the obligation on its own."""
SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {"type": "string"}}}}
src = json.load(open(sys.argv[1])); rows = src['requirements']
by = OrderedDict()
for r in rows: by.setdefault(key(r['source']), []).append(r)
corpus = {}
for reg in {k[0] for k in by}:
    for p in ingest.load(reg): corpus[(reg, p.label.strip().rstrip('.').lower())] = p
def covered(item, rs):
    a = set(re.findall(r'\w+', item.lower()))
    for r in rs:
        t = norm(r.get('quote') or '') + ' ' + norm(r['text'])
        if norm(item) in t: return True
        b = set(re.findall(r'\w+', t.lower()))
        if a and len(a & b) / len(a) >= 0.8: return True
    return False
out = []
for k, rs in by.items():
    out += rs
    p = corpus.get(k)
    if p is None or p.annex or len(p.text) < 600 or len(LIMIT.findall(p.text)) < 3 or len(rs) < 2: continue
    text = norm(p.text)
    items = claude_cli.complete_json(SYSTEM, f"Paragraph {k[0]} {p.label}:\n{text}", SCHEMA, model='claude-opus-5-5')['items']
    items = [norm(i) for i in items if norm(i) and norm(i) in text]
    new = [i for i in items if not covered(i, rs)]
    print(k[0], p.label, 'rows', len(rs), 'items', len(items), 'added', len(new))
    for i in new: out.append(dict(copy.deepcopy(rs[0]), text=i, quote=i))
src['requirements'] = [dict(r, id=f'R-{n+1:04d}') for n, r in enumerate(out)]; src['team_id'] = 'team-06'
json.dump(src, open(sys.argv[2], 'w'), indent=1, ensure_ascii=False)
print('rows', len(rows), '->', len(out))
