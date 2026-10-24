"""Lane F, step 1 and the cheap part of step 2: pool the model-written dev files into row
clusters and compute the features that need no model call.

    PYTHONPATH=. uv run python swing/f_pool.py

Writes ../out/experiments/F-pool.json: one record per cluster (regulation, paragraph, page,
member rows with their source file, votes, features, label). Own clustering: rows of the same
(regulation, paragraph) join when their token Jaccard is 0.6 or more and they do not cite
different numbers. When lane A's `A-pool.json` exists, its clusters and medoid texts are used
instead.
The label `y` is the local judge's one-to-one assignment of the 190 gold rows to cluster texts,
credit going to the cluster with more votes on a tie; `y_any` is 1 when some gold row of the
regulation is at similarity 0.45 or more.
The Opus paragraph relevance comes from the shared cache; a cache miss raises instead of paying.
"""

from __future__ import annotations

import json
import os
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from brain import llm, relevance
from brain.graph import build
from brain.ingest import load_all
from brain.models import Paragraph, ProductProfile
from brain.paths import CASES
from eval import judge
from eval.score import paragraph_key

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
POOL_PATH = OUT / "experiments" / "F-pool.json"
A_POOL = OUT / "experiments" / "A-pool.json"

# Model-written dev files, best platform matched first: the representative of a cluster is the
# member from the earliest file in this list.
FILES = [
    "rear-lamp-kb-jev.json",
    "rear-lamp-fable.json",
    "dev-upload.json",
    "rear-lamp-opus.json",
    "rear-lamp-main-cli.json",
    "rear-lamp-kb-sol-rewrite.json",
    "rear-lamp-main-a39acab.json",
    "rear-lamp-sonnet.json",
    "rear-lamp-kb-jev-filter-v4.json",
    "rear-lamp-mix-examples-cut.json",
    "rear-lamp-mix.json",
    "rear-lamp-mix-examples.json",
    "rear-lamp-mix-noimage.json",
    "rear-lamp-mix-examples-cut-consolidated.json",
    "rear-lamp-qwen-split-rewrite.json",
]
SIM = 0.6
_NUM = re.compile(r"\d+(?:[.,]\d+)*")
_REF = re.compile(r"\b(?:paragraphs?|annex|appendix|table)\s+\d", re.I)
_MODAL = re.compile(r"\b(shall not|shall|must not|must|may|should)\b", re.I)


def _path(name: str) -> Path:
    return ROOT / "brain" / "out" / name if name == "dev-upload.json" else OUT / name


def _numbers(text: str) -> set[str]:
    return set(_NUM.findall(text))


def same_row(a: str, b: str) -> bool:
    na, nb = _numbers(a), _numbers(b)
    if na != nb and (na or nb) and not (na <= nb or nb <= na):
        return False
    return judge.similarity(a, b) >= SIM


def opus_relevance(profile: ProductProfile, regs: list[str]) -> dict[str, float]:
    """Raw LLM p_cited per paragraph id, as `main`'s pipeline asks it, from the cache only."""
    os.environ["BRAIN_LLM"] = "anthropic"

    def no_call(*_: Any, **__: Any) -> Any:
        raise RuntimeError("relevance cache miss: lane F does not pay for relevance")

    llm._anthropic = no_call  # type: ignore[assignment]
    corpus = load_all("base")
    sub = {r: corpus[r] for r in regs}
    graph = build(sub, set(corpus))
    paras = [
        p
        for r in regs
        for p in sub[r]
        if p.number and p.label != "preamble" and not p.label.startswith("Rationale")
    ]
    return relevance.score(paras, graph, profile)


def word_share(text: str, source: str) -> float:
    t = judge.tokens(text)
    return len(t & judge.tokens(source)) / max(1, len(t))


def position(quote: str, text: str) -> float:
    """Where the row's quote starts in its paragraph, 0 (start) to 1 (end); 0.5 if not found."""
    if not quote or not text:
        return 0.5
    i = text.find(quote[:60])
    return 0.5 if i < 0 else i / max(1, len(text))


def build_pool() -> dict[str, Any]:
    base = json.loads((OUT / "rear-lamp-main-a39acab.json").read_text())
    profile = ProductProfile(**base["profile"])
    regs = [c["regulation"] for c in base["regulations"] if c["selected"]]
    rel = opus_relevance(profile, regs)
    corpus = load_all("base")
    by_key: dict[tuple[str, str], Paragraph] = {}
    for r in regs:
        for p in corpus[r]:
            by_key.setdefault((r, paragraph_key(p.label) or ""), p)

    clusters = clusters_from_a() if A_POOL.exists() else clusters_own()
    para_files: dict[tuple[str, str], set[str]] = defaultdict(set)
    rows_per_file: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for key, cs in clusters.items():
        for c in cs:
            for m in c["members"]:
                para_files[key].add(m["file"])
                rows_per_file[key][m["file"]] += 1

    out: list[dict[str, Any]] = []
    for (reg, pkey), cs in clusters.items():
        p = by_key.get((reg, pkey))
        ptext = p.text if p else ""
        n_para = len(para_files[(reg, pkey)])
        med_rows = statistics.median(rows_per_file[(reg, pkey)].values())
        ranked = sorted(cs, key=lambda c: -c["votes"])
        for rank, c in enumerate(ranked):
            rep = c["rep"]
            text = rep["text"]
            votes = c["votes"]
            modal = _MODAL.search(text)
            out.append(
                {
                    "regulation": reg,
                    "paragraph": p.label if p else pkey,
                    "pkey": pkey,
                    "page": c["page"],
                    "version": p.version if p else "",
                    "text": text,
                    "quote": rep["quote"],
                    "members": c["members"],
                    "f": {
                        "votes": votes,
                        "vote_share": votes / len(FILES),
                        "row_share": votes / max(1, n_para),
                        "para_votes": n_para / len(FILES),
                        "para_rows": float(med_rows),
                        "vote_rank": rank,
                        "llm_p": rel.get(p.id, 0.0) if p else 0.0,
                        "word_share": word_share(text, ptext),
                        "quote_share": word_share(rep["quote"], ptext) if rep["quote"] else 0.0,
                        "n_tokens": len(judge.tokens(text)),
                        "n_numbers": len(_numbers(text)),
                        "cites_other": int(bool(_REF.search(text))),
                        "shall_not": int(bool(modal) and "not" in modal.group(1).lower()),
                        "may": int(bool(modal) and modal.group(1).lower() in ("may", "should")),
                        "no_modal": int(not modal),
                        "position": position(rep["quote"], ptext),
                        "depth": pkey.count(".") + 1,
                        "annex": int(pkey.startswith("annex")),
                    },
                }
            )
    label(out)
    source = "A-pool.json (medoid text, 14 voters)" if A_POOL.exists() else f"own, Jaccard {SIM}"
    return {"files": FILES, "clusters_from": source, "clusters": out}


Clusters = dict[tuple[str, str], list[dict[str, Any]]]


def clusters_from_a() -> Clusters:
    """Lane A's clusters (average linkage at Jaccard 0.5, medoid text), with each member's quote
    read back from its file."""
    a = json.loads(A_POOL.read_text())
    reqs: dict[str, list[dict[str, Any]]] = {}
    out: Clusters = defaultdict(list)
    for c in a["clusters"]:
        members = []
        for m in c["members"]:
            path = ROOT / m["file"]
            if m["file"] not in reqs:
                reqs[m["file"]] = json.loads(path.read_text())["requirements"]
            row = reqs[m["file"]][m["id_index"]]
            members.append({"file": path.name, "text": m["text"], "quote": row.get("quote") or ""})
        rep = next((m for m in members if m["text"] == c["medoid"]), members[0])
        key = (c["regulation"], c["paragraph_key"])
        out[key].append({"page": c["page"], "members": members, "rep": rep, "votes": c["votes"]})
    return out


def clusters_own() -> Clusters:
    """Greedy clusters: a row joins the first cluster whose first member it matches."""
    out: Clusters = defaultdict(list)
    for name in FILES:
        for r in json.loads(_path(name).read_text())["requirements"]:
            s = r["source"]
            key = (s["regulation"], paragraph_key(s.get("paragraph")) or "")
            member = {"file": name, "text": r["text"], "quote": r.get("quote") or ""}
            for c in out[key]:
                if same_row(c["rep"]["text"], r["text"]):
                    c["members"].append(member)
                    c["votes"] = len({m["file"] for m in c["members"]})
                    break
            else:
                out[key].append({"page": s["page"], "members": [member], "rep": member, "votes": 1})
    return out


def label(pool: list[dict[str, Any]]) -> None:
    gold = json.loads((CASES / "dev-rear-lamp" / "expected.json").read_text())["requirements"]
    for c in pool:
        c["y"], c["y_any"] = 0, 0
    for reg in {g["source"]["regulation"] for g in gold}:
        ci = [i for i, c in enumerate(pool) if c["regulation"] == reg]
        gi = [g for g in gold if g["source"]["regulation"] == reg]
        m = np.array([[judge.similarity(pool[i]["text"], g["text"]) for g in gi] for i in ci])
        ok = m >= 0.45
        for a, i in enumerate(ci):
            pool[i]["y_any"] = int(ok[a].any())
        # Count first, then credit the cluster more runs wrote, then similarity: a near-copy
        # with fewer votes gets no credit for a gold row the stronger cluster already matches.
        votes = np.array([pool[i]["f"]["votes"] for i in ci], dtype=float)[:, None]
        rows, cols = linear_sum_assignment(-np.where(ok, 1.0 + votes / 100 + m / 1000, 0.0))
        for r, c in zip(rows, cols, strict=True):
            if ok[r, c]:
                pool[ci[r]]["y"] = 1


def main() -> int:
    pool = build_pool()
    cs = pool["clusters"]
    POOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    POOL_PATH.write_text(json.dumps(pool, ensure_ascii=False))
    print(
        f"{len(cs)} clusters, {sum(c['y'] for c in cs)} gold rows assigned, "
        f"{sum(c['y_any'] for c in cs)} clusters matchable"
    )
    for v in (1, 3, 5, 8, 10, 12):
        k = [c for c in cs if c["f"]["votes"] >= v]
        print(f"votes >= {v}: {len(k)} clusters, {sum(c['y'] for c in k)} assigned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
