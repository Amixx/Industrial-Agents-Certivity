"""Build the 0.701 fragquote upload from the 0.724 rebuild: rows whose quote is a fragment
(verbatim.py's fragment rule) take the quote, every other row keeps the rewrite.

    python repro/fragquote.py repro/out/j20f-all.json ... -> see run.sh; uses repro/out/cut2-mark.json"""
import json, re, sys, collections
from pathlib import Path
H = Path(__file__).parent
sub = json.load(open(H / 'out/cut2-mark.json')); rows = sub['requirements']
key = lambda r: (r['source']['regulation'], r['source'].get('paragraph', ''), r['quote'].strip())
shared = collections.Counter(key(r) for r in rows)
def fragment(q):
    if re.match(r"^(\(|[a-z]|-|–|or\b|and\b)", q) or re.search(r"[;:]\s*(and|or)?$", q): return True
    w = q.split(); return sum(bool(re.search(r"\d", x)) for x in w) > 0.4 * len(w)
for r in rows:
    q = r['quote'].strip()
    if shared[key(r)] == 1 and len(q) >= 20 and fragment(q): r['text'] = q[:2000]
sub['team_id'] = 'team-06'
json.dump(sub, open(H / 'out/fragquote.json', 'w'), indent=1, ensure_ascii=False)
s = lambda rs: [{k: r[k] for k in ('text', 'source', 'quote')} for r in rs]
print('identical to the uploaded file' if s(rows) == s(json.load(open(H / 'uploaded-0701-fragquote.json'))['requirements']) else 'DIFFERS')
