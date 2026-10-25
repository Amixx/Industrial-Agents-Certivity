"""heldout-cut20-light.json: the held-out API file without its R48, R148 and R10 rows under confidence 0.20."""
import json, sys
from pathlib import Path

src = Path(__file__).parents[1] / "heldout-api" / "heldout-api.json"
s = json.loads(src.read_text())
s["requirements"] = [
    r for r in s["requirements"]
    if not (r["source"]["regulation"] in ("UN R48", "UN R148", "UN R10") and r["confidence"] < 0.20)
]
Path(sys.argv[1] if len(sys.argv) > 1 else "heldout-cut20-light.rebuilt.json").write_text(
    json.dumps(s, indent=1, ensure_ascii=False)
)
