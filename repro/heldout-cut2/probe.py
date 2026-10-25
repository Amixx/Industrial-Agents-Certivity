"""Writes a probe file: the rows of the best held-out file whose regulation (and optional paragraph prefix) matches.

    python3 ~/Personal/bench-out/probe.py <src.json> <dst.json> "UN R48" ["UN R148|5.", ...]
"""
import json
import sys

src, dst, *sel = sys.argv[1:]
d = json.load(open(src))


def keep(r):
    s = r["source"]
    for x in sel:
        reg, _, pre = x.partition("|")
        if s["regulation"] == reg and s["paragraph"].startswith(pre):
            return True
    return False


d["requirements"] = [r for r in d["requirements"] if keep(r)]
json.dump(d, open(dst, "w"), indent=1, ensure_ascii=False)
print(dst, len(d["requirements"]), "rows", d["team_id"])
