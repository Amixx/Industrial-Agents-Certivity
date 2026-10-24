"""Build the paragraph graph of every base PDF in the corpus.

    uv run --with pymupdf python scripts/reggraph/build.py            # all regulations
    uv run --with pymupdf python scripts/reggraph/build.py R148 R7    # a subset

Writes data/reggraph/<UN_Rnn>.json (nodes and edges; node ids are "<regulation>|<label>") and data/reggraph/index.json (per-regulation stats, the
cross-regulation adjacency and the supersedes edges).
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from edges import Resolver, node_edges, parent_label, supersedes_edges
from parse import parse_pdf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "reggraph"
# The committed graphs keep the opening of each paragraph's text only for the regulations the spike measures.
TEXT_REGULATIONS = {"UN R148", "UN R48", "UN R150", "UN R10", "UN R7"}
TEXT_CHARS = 300
EVIDENCE_CHARS = 80


def base_versions():
    """{regulation: (version, pdf path)} for every base version in the corpus index."""
    out = {}
    for entry in json.loads((ROOT / "regulations" / "index.json").read_text()):
        for version in entry["versions"]:
            if version["role"] == "base":
                slug = entry["regulation"].replace(" ", "_")
                out[entry["regulation"]] = (version["version_label"], ROOT / "regulations" / "pdf" / slug / "base" / version["files"][0]["name"])
    return out


def build(reg, version, path, regulations):
    nodes = parse_pdf(path)
    labels = {n["label"] for n in nodes}
    for n in nodes:
        n["parent"] = parent_label(n["label"], labels)
    resolver = Resolver(nodes)
    edges = [{"type": "parent", "source": f"{reg}|{n['label']}", "target": f"{reg}|{n['parent']}"} for n in nodes if n["parent"]]
    stats = Counter()
    for n in nodes:
        found, counts = node_edges(reg, n, resolver, regulations)
        stats.update(counts)
        edges += found
        edges += supersedes_edges(reg, n, regulations)
    for e in edges:
        if "evidence" in e:
            e["evidence"] = e["evidence"][:EVIDENCE_CHARS]
    refs = stats["ref_exact"] + stats["ref_ancestor"] + stats["ref_none"]
    summary = {
        "regulation": reg,
        "version": version,
        "nodes": len(nodes),
        "edges": dict(Counter(e["type"] for e in edges)),
        "references": dict(stats),
        "ref_resolution_exact": round(stats["ref_exact"] / refs, 3) if refs else None,
        "ref_resolution_any": round((stats["ref_exact"] + stats["ref_ancestor"]) / refs, 3) if refs else None,
    }
    graph = {
        **summary,
        "nodes": [
            {"label": n["label"], "page": n["page"]}
            | ({"text": n["text"][:TEXT_CHARS]} if reg in TEXT_REGULATIONS else {})
            for n in nodes
        ],
        "edges": edges,
    }
    return graph, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("only", nargs="*", help="regulation numbers such as R148, default all")
    args = parser.parse_args()
    versions = base_versions()
    wanted = [r for r in versions if not args.only or r.split()[-1] in args.only]
    OUT.mkdir(parents=True, exist_ok=True)
    summaries, cross, supersedes = [], Counter(), []
    for reg in wanted:
        version, path = versions[reg]
        graph, summary = build(reg, version, path, set(versions))
        (OUT / f"{reg.replace(' ', '_')}.json").write_text(json.dumps(graph, ensure_ascii=False, separators=(",", ":")))
        summaries.append(summary)
        for e in graph["edges"]:
            if e["type"] == "xref":
                cross[(reg, e["target"].split("|")[0])] += 1
            elif e["type"] == "supersedes":
                supersedes.append(e)
        print(f"{reg:12} {summary['nodes']:5} nodes  {summary['edges']}  resolved {summary['ref_resolution_exact']}")
    index = {
        "regulations": summaries,
        "xref": [{"source": s, "target": t, "count": c} for (s, t), c in sorted(cross.items())],
        "supersedes": supersedes,
    }
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
