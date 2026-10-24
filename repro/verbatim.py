"""Replace each requirement's text with its quote, the source sentence, when that quote belongs to
that row only and is not a fragment. Fragments keep the rewrite: list items ("(b) ..."), clauses
starting in lower case or with a dash, quotes ending in ";" or ":", and table cells (mostly numbers).

    python out/scripts/verbatim.py <in.json> <out.json> [--all]   # --all: every unshared quote
"""
import collections, json, re, sys

src, dst = sys.argv[1], sys.argv[2]
sub = json.load(open(src))
rows = sub["requirements"]
key = lambda r: (r["source"]["regulation"], r["source"].get("paragraph", ""), r["quote"].strip())
shared = collections.Counter(key(r) for r in rows)
def fragment(q: str) -> bool:
    if re.match(r"^(\(|[a-z]|-|–|or\b|and\b)", q) or re.search(r"[;:]\s*(and|or)?$", q):
        return True
    words = q.split()
    return sum(bool(re.search(r"\d", w)) for w in words) > 0.4 * len(words)

n = 0
for r in rows:
    q = r["quote"].strip()
    if shared[key(r)] == 1 and len(q) >= 20 and ("--all" in sys.argv or not fragment(q)):
        r["text"] = q[:2000]
        n += 1
sub["team_id"] = "team-06"
json.dump(sub, open(dst, "w"), indent=1, ensure_ascii=False)
print(f"{dst}: {n} of {len(rows)} rows verbatim")
