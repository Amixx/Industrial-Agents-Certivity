"""Measure the graphs against a golden answer: stats, golden-set connectivity, and the expansion test.

    python3 scripts/reggraph/measure.py [--case cases/dev-rear-lamp/expected.json]

Reads data/reggraph/*.json (run build.py first), prints Markdown tables and writes data/reggraph/metrics.json.
"""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRAPHS = ROOT / "data" / "reggraph"
SEEDS = 20
FOUND_FRACTIONS = (0.5, 0.25)
TOP_REFERENCED = 5


def load(regulation):
    return json.loads((GRAPHS / f"{regulation.replace(' ', '_')}.json").read_text())


class Graph:
    """Nodes and typed adjacency over the regulations of one case, with document order for the baselines."""

    def __init__(self, graphs):
        self.nodes = []
        self.page = {}
        self.adj = defaultdict(lambda: defaultdict(set))
        for g in graphs:
            ids = [f"{g['regulation']}|{n['label']}" for n in g["nodes"]]
            self.nodes += ids
            for i, (node_id, n) in enumerate(zip(ids, g["nodes"])):
                self.page[node_id] = n["page"]
                if i:
                    self.adj["next"][ids[i - 1]].add(node_id)
                    self.adj["prev"][node_id].add(ids[i - 1])
        by_page = defaultdict(set)
        for node_id in self.nodes:
            by_page[(node_id.split("|")[0], self.page[node_id])].add(node_id)
        for node_id in self.nodes:
            self.adj["page"][node_id] = by_page[(node_id.split("|")[0], self.page[node_id])] - {node_id}
        known = set(self.nodes)
        for g in graphs:
            for e in g["edges"]:
                s, t = e["source"], e["target"]
                if s not in known or t not in known:
                    continue
                kind = {"parent": "up", "ref": "ref_out", "xref": "ref_out"}.get(e["type"])
                if kind is None:
                    continue
                self.adj[kind][s].add(t)
                self.adj[{"up": "down", "ref_out": "ref_in"}[kind]][t].add(s)
        for node_id in self.nodes:
            for parent in self.adj["up"][node_id]:
                self.adj["sibling"][node_id] |= self.adj["down"][parent] - {node_id}

    def step(self, frontier, kinds):
        out = set()
        for node_id in frontier:
            for kind in kinds:
                out |= self.adj[kind][node_id]
        return out

    def expand(self, seeds, kinds, hops=1):
        reached, frontier = set(seeds), set(seeds)
        for _ in range(hops):
            frontier = self.step(frontier, kinds) - reached
            reached |= frontier
        return reached


STRATEGIES = {
    "parent": (("up",), 1),
    "children": (("down",), 1),
    "parent + children": (("up", "down"), 1),
    "siblings": (("sibling",), 1),
    "ref out": (("ref_out",), 1),
    "ref in": (("ref_in",), 1),
    "ref both": (("ref_out", "ref_in"), 1),
    "parent + ref out": (("up", "ref_out"), 1),
    "parent + children + ref both": (("up", "down", "ref_out", "ref_in"), 1),
    "parent + children + ref both, 2 hops": (("up", "down", "ref_out", "ref_in"), 2),
    "siblings + ref both": (("sibling", "ref_out", "ref_in"), 1),
    "baseline: next/previous paragraph": (("next", "prev"), 1),
    "baseline: 2 paragraphs either side": (("next", "prev"), 2),
    "baseline: same page": (("page",), 1),
    "baseline: 8 paragraphs either side": (("next", "prev"), 8),
}

CONNECTIVITY = {
    "parent/child": ("up", "down"),
    "sibling": ("sibling",),
    "ref (either direction)": ("ref_out", "ref_in"),
    "parent/child + ref": ("up", "down", "ref_out", "ref_in"),
    "baseline: document order": ("next", "prev"),
}


def golden(case):
    reqs = json.loads(Path(case).read_text())["requirements"]
    return {f"{r['source']['regulation']}|{r['source']['paragraph']}" for r in reqs}, reqs


def stats_table(graphs):
    rows = []
    for g in graphs:
        in_degree = Counter(e["target"] for e in g["edges"] if e["type"] == "ref")
        top = ", ".join(f"{t.split('|')[1]} ({c})" for t, c in in_degree.most_common(TOP_REFERENCED))
        rows.append(
            {
                "regulation": g["regulation"],
                "nodes": len(g["nodes"]),
                **{k: sum(1 for e in g["edges"] if e["type"] == k) for k in ("parent", "ref", "xref", "supersedes")},
                "refs_found": sum(g["references"].get(k, 0) for k in ("ref_exact", "ref_ancestor", "ref_none")),
                "resolved_exact": g["ref_resolution_exact"],
                "resolved_any": g["ref_resolution_any"],
                "top_referenced": top,
            }
        )
    return rows


def connectivity(graph, gold):
    out = {}
    for name, kinds in CONNECTIVITY.items():
        one = sum(1 for n in gold if (graph.expand({n}, kinds, 1) - {n}) & gold)
        two = sum(1 for n in gold if (graph.expand({n}, kinds, 2) - {n}) & gold)
        out[name] = {"1 hop": one, "2 hops": two}
    return out


def expansion(graph, gold):
    gold = sorted(gold)
    out = {}
    for fraction in FOUND_FRACTIONS:
        rows = {}
        for name, (kinds, hops) in STRATEGIES.items():
            gained, pulled = [], []
            for seed in range(SEEDS):
                found = set(random.Random(seed).sample(gold, round(fraction * len(gold))))
                new = graph.expand(found, kinds, hops) - found
                gained.append(len(new & set(gold)))
                pulled.append(len(new - set(gold)))
            g, p = sum(gained) / SEEDS, sum(pulled) / SEEDS
            rows[name] = {
                "recall_before": round(fraction, 3),
                "recall_after": round(fraction + g / len(gold), 3),
                "golden_gained": round(g, 1),
                "non_golden_pulled": round(p, 1),
                "precision_of_pulled": round(g / (g + p), 3) if g + p else None,
            }
        out[str(fraction)] = rows
    return out


def cross_regulation(index, regulations):
    counts = {(x["source"], x["target"]): x["count"] for x in index["xref"]}
    return {s: {t: counts.get((s, t), 0) for t in regulations if t != s} for s in regulations}


def md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default=str(ROOT / "cases" / "dev-rear-lamp" / "expected.json"))
    args = parser.parse_args()
    gold, reqs = golden(args.case)
    regulations = sorted({r["source"]["regulation"] for r in reqs}, key=lambda r: int(r.split("R")[-1]))
    graphs = [load(r) for r in regulations]
    graph = Graph(graphs)
    missing = gold - set(graph.nodes)
    index = json.loads((GRAPHS / "index.json").read_text())
    shown = regulations + ["UN R7", "UN R6", "UN R23", "UN R3"]
    metrics = {
        "golden_paragraphs": len(gold),
        "golden_missing_from_graph": sorted(missing),
        "universe_nodes": len(graph.nodes),
        "stats": stats_table(graphs + [load("UN R7")]),
        "connectivity": connectivity(graph, gold),
        "expansion": expansion(graph, gold),
        "cross_regulation": cross_regulation(index, shown),
        "supersedes": [s for s in index["supersedes"] if s["source"] in shown or s["target"] in shown],
    }
    (GRAPHS / "metrics.json").write_text(json.dumps(metrics, indent=1))

    print(f"Golden paragraphs: {len(gold)} distinct, {len(missing)} missing from the graph; universe {len(graph.nodes)} nodes, base rate {len(gold) / len(graph.nodes):.3f}\n")
    s = metrics["stats"]
    print(md_table(list(s[0]), [list(r.values()) for r in s]), "\n")
    c = metrics["connectivity"]
    print(md_table(["edges", "1 hop", "2 hops"], [[k, f"{v['1 hop']} ({v['1 hop'] / len(gold):.0%})", f"{v['2 hops']} ({v['2 hops'] / len(gold):.0%})"] for k, v in c.items()]), "\n")
    for fraction, rows in metrics["expansion"].items():
        print(f"Found {float(fraction):.0%} of the golden paragraphs, {SEEDS} seeds:\n")
        print(md_table(["expansion", "recall after", "golden gained", "non-golden pulled", "precision of pulled"], [[k, v["recall_after"], v["golden_gained"], v["non_golden_pulled"], v["precision_of_pulled"]] for k, v in rows.items()]), "\n")
    x = metrics["cross_regulation"]
    print(md_table(["from \\ to"] + [t.split()[-1] for t in shown], [[s.split()[-1]] + [x[s].get(t, "") if s != t else "" for t in shown] for s in shown]), "\n")
    for e in metrics["supersedes"]:
        print(f"{e['source']} supersedes {e['target']} ({e['basis']}, {e['at']})")


if __name__ == "__main__":
    main()
