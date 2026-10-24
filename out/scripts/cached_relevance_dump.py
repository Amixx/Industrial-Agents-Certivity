"""Recover cached LLM relevance scores with every network path disabled (cache hits only)."""
import os, pickle, sys
from pathlib import Path
for k in ("OPENAI_API_KEY", "OPENAI_KEY", "ANTHROPIC_API_KEY", "BRAIN_LLM"):
    os.environ.pop(k, None)
from brain import llm
for k in ("OPENAI_API_KEY", "OPENAI_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(k, None)  # .env loaded at import
def _no_network(*a, **k):
    raise RuntimeError("cache miss (network disabled)")
llm._openai_compatible = _no_network
llm._anthropic = _no_network
PROV = sys.argv[1] if len(sys.argv) > 1 else "openai"
llm.provider = lambda: PROV

import numpy as np
from brain.decide import dataset, cross_validate
from brain.graph import build
from brain.ingest import load_all
from brain.paths import CASES
from brain.profile import build_profile
from brain import relevance

case = CASES / "dev-rear-lamp"
corpus = load_all("base")
ds = dataset(case, corpus)
oof = cross_validate(ds)
profile = build_profile((case / "spec.md").read_text(), case / "exploded_view.png")
print("profile:", profile.product, profile.functions)
regs = sorted({p.regulation for p in ds.paragraphs})
graph = build({r: corpus[r] for r in regs}, set(corpus))
numbered = [p for p in ds.paragraphs if p.number]
out = {"ids": [p.id for p in ds.paragraphs], "y": ds.y, "X": ds.X, "oof": oof}
for tier in ("strong", "bulk"):
    s = relevance.score(numbered, graph, profile, tier=tier)
    print(tier, "cached:", len(s), "of", len(numbered))
    out[tier] = s
pickle.dump(out, open(Path(__file__).parent / f"dev_{PROV}.pkl", "wb"))
