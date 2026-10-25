"""Compare paragraph selections (selected.json from chain.py STOP_AFTER_SELECT=1) with a reference
selection and with the dev gold paragraphs.

    python repro/speed/compare_selected.py REFERENCE.json VARIANT.json [...]
"""

import json
import sys
from pathlib import Path

GOLD = Path(__file__).parents[2] / "cases/dev-rear-lamp/expected.json"
gold = {
    (r["source"]["regulation"], r["source"]["paragraph"].strip().rstrip(".").lower())
    for r in json.loads(GOLD.read_text())["requirements"]
}


def key(pid: str) -> tuple[str, str]:
    reg, _, label = pid.split("|")
    return reg, label.strip().rstrip(".").lower()


ref = set(json.loads(Path(sys.argv[1]).read_text()))
for path in sys.argv[1:]:
    sel = set(json.loads(Path(path).read_text()))
    hits = {key(p) for p in sel} & gold
    print(
        f"{path}: {len(sel)} paragraphs, gold paragraphs {len(hits)}/{len(gold)}, "
        f"overlap with reference {len(sel & ref)} (+{len(sel - ref)} / -{len(ref - sel)})"
    )
