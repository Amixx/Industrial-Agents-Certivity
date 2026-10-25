"""Rebuilds heldout-cut2.json: heldout-silver-r10r148.json without R48 section 6 and R148 section 5 and annexes.

    python3 repro/heldout-cut2/build.py repro/heldout-r10r148/heldout-silver-r10r148.json out.json
"""
import json
import sys

src, dst = sys.argv[1:3]
d = json.load(open(src))


def dead(s):
    p = s["paragraph"]
    return (s["regulation"] == "UN R48" and p.startswith("6.")) or (
        s["regulation"] == "UN R148" and (p.startswith("5.") or p.startswith("Annex"))
    )


d["requirements"] = [dict(r, id=f"R-{i + 1:04d}") for i, r in enumerate(r for r in d["requirements"] if not dead(r["source"]))]
json.dump(d, open(dst, "w"), indent=1, ensure_ascii=False)
print(len(d["requirements"]))
