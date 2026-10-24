"""Gemini relevance on the dev paragraphs through brain's OpenAI-compatible `local` provider.

    PYTHONPATH=. uv run python gemini_relevance.py smoke     # one batch of 25
    PYTHONPATH=. uv run python gemini_relevance.py full      # every candidate paragraph

The key comes from GEMINI_API_KEY in brain/.env and is handed to the process as BRAIN_LOCAL_KEY.
"""

import os
import pickle
import sys
import time
from pathlib import Path

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
os.environ.update(
    BRAIN_LLM="local",
    BRAIN_LOCAL_URL="https://generativelanguage.googleapis.com/v1beta/openai/",
    BRAIN_LOCAL_MODEL=MODEL,
    BRAIN_LLM_TIMEOUT="300",
)
for k in ("OPENAI_API_KEY", "OPENAI_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(k, None)

from brain import llm, relevance  # noqa: E402  (loads brain/.env)

os.environ["BRAIN_LOCAL_KEY"] = os.environ["GEMINI_API_KEY"]
for k in ("OPENAI_API_KEY", "OPENAI_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(k, None)
assert llm.provider() == "local"

import numpy as np  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

from brain.decide import f2_at  # noqa: E402
from brain.graph import build  # noqa: E402
from brain.ingest import load_all  # noqa: E402
from brain.paths import CASES  # noqa: E402
from brain.profile import parse_spec  # noqa: E402

HERE = Path(__file__).parent
cached = pickle.load(open(HERE / "dev_openai.pkl", "rb"))  # ids, y, oof, strong (gpt-5.5)
corpus = load_all("base")
byid = {p.id: p for ps in corpus.values() for p in ps}
keep = [i for i, pid in enumerate(cached["ids"]) if byid[pid].number]
ids = [cached["ids"][i] for i in keep]
y, oof = cached["y"][keep], cached["oof"][keep]
paragraphs = [byid[i] for i in ids]
regs = sorted({p.regulation for p in paragraphs})
graph = build({r: corpus[r] for r in regs}, set(corpus))
profile = parse_spec((CASES / "dev-rear-lamp" / "spec.md").read_text())

mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
t0 = time.time()
if mode == "smoke":
    gold_first = sorted(range(len(ids)), key=lambda i: -y[i])[:5] + list(range(20))
    sample = [paragraphs[i] for i in dict.fromkeys(gold_first)][:25]
    scores = relevance.score(sample, graph, profile, batch=25, workers=1)
    print(f"{MODEL}: {len(scores)} of {len(sample)} scored in {time.time() - t0:.0f}s")
    for p in sample[:8]:
        print(f"   {p.regulation} {p.label:10s} gold={int(p.id in set(np.array(ids)[y == 1]))} "
              f"p={scores.get(p.id)}")
    raise SystemExit(0)

BATCH = int(os.environ.get("GEMINI_BATCH", "100"))
product = profile.model_dump_json(include={"product", "vehicle_categories", "functions", "parts", "electronics"})
chunks = [paragraphs[i : i + BATCH] for i in range(0, len(paragraphs), BATCH)]
scores = {}
for n, chunk in enumerate(chunks, 1):
    try:
        scores |= relevance._batch(chunk, graph, product, "strong")
        print(f"[{time.time() - t0:5.0f}s] batch {n}/{len(chunks)}: {len(scores)} scored", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[{time.time() - t0:5.0f}s] batch {n} failed: {e!r:.160}", file=sys.stderr, flush=True)
        if "429" in repr(e):
            print("quota reached; scoring what finished", file=sys.stderr)
            break
scored = [i for i, pid in enumerate(ids) if pid in scores]
ids = [ids[i] for i in scored]; y = y[scored]; oof = oof[scored]; paragraphs = [paragraphs[i] for i in scored]
regs = sorted({p.regulation for p in paragraphs})
print(f"{MODEL}: {len(scores)} of {len(paragraphs)} scored in {time.time() - t0:.0f}s")
g = np.array([scores.get(i, 0.0) for i in ids])
s = np.array([cached["strong"].get(i, 0.0) for i in ids])
pickle.dump({"ids": ids, "gemini": g}, open(HERE / f"dev_{MODEL}.pkl", "wb"))
for name, v in [
    ("decision model (out of fold)", oof),
    (f"{MODEL}", g),
    ("gpt-5.5 (cached)", s),
    (f"blend {MODEL} + decision model", np.array([relevance.blend(a, b) for a, b in zip(oof, g)])),
]:
    best = max((f2_at(v, y, t)[2], t) for t in np.arange(0.01, 0.95, 0.01))
    prec, rec, f2 = f2_at(v, y, best[1])
    print(f"{name:40s} AUC {roc_auc_score(y, v):.3f}  best F2 {f2:.3f} (P {prec:.2f} R {rec:.2f} "
          f"at {best[1]:.2f}, n={(v >= best[1]).sum()})")
for reg in regs:
    m = np.array([p.regulation == reg for p in paragraphs])
    print(f"   {reg:8s} gold {y[m].sum():3d}/{m.sum():4d}  AUC {MODEL} {roc_auc_score(y[m], g[m]):.3f}"
          f"  gpt-5.5 {roc_auc_score(y[m], s[m]):.3f}")
