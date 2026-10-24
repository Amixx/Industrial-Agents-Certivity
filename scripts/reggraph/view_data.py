"""Write the compact graph data the /dev/reggraph view loads: nodes in document order with golden flags, and edges.
The file is formatted with the frontend's Biome so `bun run lint` passes.

    python3 scripts/reggraph/view_data.py
"""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRAPHS = ROOT / "data" / "reggraph"
CASE = ROOT / "cases" / "dev-rear-lamp" / "expected.json"
TEXT_CHARS = 140
OUT = ROOT / "web" / "frontend" / "src" / "routes" / "dev" / "reggraph" / "graph.json"


def node(reg, n, index, parents, gold):
    """Text only for golden paragraphs and top-level sections, which the view labels."""
    node_id = f"{reg}|{n['label']}"
    parent = index.get(parents.get(node_id), -1)
    shown = node_id in gold or parent == -1
    return {"label": n["label"], "page": n["page"], "parent": parent, "gold": node_id in gold, "text": n["text"][:TEXT_CHARS] if shown else ""}


def main():
    reqs = json.loads(CASE.read_text())["requirements"]
    gold = {f"{r['source']['regulation']}|{r['source']['paragraph']}" for r in reqs}
    regulations = sorted({r["source"]["regulation"] for r in reqs}, key=lambda r: int(r.split("R")[-1]))
    out = []
    for reg in regulations:
        g = json.loads((GRAPHS / f"{reg.replace(' ', '_')}.json").read_text())
        index = {f"{reg}|{n['label']}": i for i, n in enumerate(g["nodes"])}
        parents = {e["source"]: e["target"] for e in g["edges"] if e["type"] == "parent"}
        out.append(
            {
                "regulation": reg,
                "version": g["version"],
                "nodes": [node(reg, n, index, parents, gold) for n in g["nodes"]],
                "refs": sorted(
                    {(index[e["source"]], index[e["target"]]) for e in g["edges"] if e["type"] == "ref" and e["target"] in index}
                ),
            }
        )
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    subprocess.run(["bunx", "biome", "format", "--write", str(OUT)], cwd=ROOT / "web" / "frontend", check=True, capture_output=True)


if __name__ == "__main__":
    main()
