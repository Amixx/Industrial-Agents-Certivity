#!/usr/bin/env python3
"""Score your pipeline's outputs on every synthetic case (plus the dev case) in one table.

    python synthetic/score_all.py outputs/

Expects one file per case in the folder, named <case_id>.json (for example outputs/synth-a01-stop-tail-lamp.json
and outputs/dev-rear-lamp.json). Cases without an output file are listed as missing.
Regulation and page level only, like tools/score_local.py, which this reuses.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from score_local import score  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    out_dir = Path(argv[0])
    cases = {"dev-rear-lamp": ROOT / "cases" / "dev-rear-lamp" / "expected.json"}
    for folder in sorted((ROOT / "synthetic" / "cases").iterdir()):
        if (folder / "expected.json").is_file():
            cases[folder.name] = folder / "expected.json"

    print(f"{'case':<36}{'reg P':>7}{'reg R':>7}{'page P':>8}{'page R':>8}{'page F1':>9}")
    f1s = []
    for case_id, expected_path in cases.items():
        sub_path = out_dir / f"{case_id}.json"
        if not sub_path.is_file():
            print(f"{case_id:<36}   missing {sub_path}")
            continue
        result = score(json.loads(sub_path.read_text(encoding="utf-8")),
                       json.loads(expected_path.read_text(encoding="utf-8")))
        g, p = result["regulation_level"], result["page_level"]
        f1s.append(p["f1"])
        print(f"{case_id:<36}{g['precision']:>7.2f}{g['recall']:>7.2f}{p['precision']:>8.2f}{p['recall']:>8.2f}{p['f1']:>9.2f}")
    if f1s:
        print(f"\nmean page F1 over {len(f1s)} case(s): {sum(f1s) / len(f1s):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
