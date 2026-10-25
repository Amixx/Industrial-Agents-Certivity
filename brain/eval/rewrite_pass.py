"""Rewrite a fixed paragraph set with the current rewrite prompt and score it, so a rewrite change
is measured with paragraph selection held constant.

    uv run python -m eval.rewrite_pass ../out/rear-lamp-fable.json out/x.json            # dry run
    uv run python -m eval.rewrite_pass ../out/rear-lamp-fable.json out/x.json --provider local
    uv run python -m eval.rewrite_pass ../out/rear-lamp-fable.json out/x.json \
        --provider anthropic --approved

The paragraph set is every paragraph the source submission cites. The rewrite runs on the bulk
tier of the chosen provider (`BRAIN_MODEL_BULK` for Anthropic, `BRAIN_LOCAL_MODEL` for local).
The output is a valid dev submission with the source's team_id, ready to upload. Paid providers
need `--approved`, given only after the owner agreed to the cost the dry run prints.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", help="submission whose cited paragraphs are rewritten")
    ap.add_argument("out")
    ap.add_argument("--provider", choices=["local", "anthropic", "openai"])
    ap.add_argument("--approved", action="store_true", help="the owner approved the paid run")
    args = ap.parse_args(argv)
    if args.provider in ("anthropic", "openai") and not args.approved:
        ap.error("a paid provider needs --approved; run without --provider first for the size")
    from brain import llm, rewrite
    from brain.graph import build
    from brain.ingest import load_all
    from brain.paths import CASES
    from brain.verify import clean

    from . import judge
    from .score import fbeta

    source = json.loads(Path(args.source).read_text())
    rows = source["requirements"]
    product = source.get("profile", {}).get("product", "")
    corpus = load_all("base")
    regs = sorted({r["source"]["regulation"] for r in rows})
    graph = build({r: corpus[r] for r in regs}, set(corpus))
    by_label = {(p.regulation, p.label): p for r in regs for p in corpus[r]}
    keys = dict.fromkeys((r["source"]["regulation"], r["source"]["paragraph"]) for r in rows)
    paragraphs = [by_label[k] for k in keys if k in by_label]
    print(f"{len(paragraphs)} paragraphs ({len(keys) - len(paragraphs)} labels not in the corpus)")
    if not args.provider:
        tokens = sum(len(p.text[:4000]) + 400 for p in paragraphs) / 3.5
        batches = -(-len(paragraphs) // 12)
        print(
            f"dry run: about {tokens / 1e3:.0f}k paragraph tokens plus about 2k prompt tokens "
            f"per batch ({batches} cloud batches of 12); output is usually 0.5 to 1 times the "
            "input"
        )
        return 0
    llm.use(args.provider)
    if not llm.available():
        raise SystemExit("no provider configured")
    print(f"model {llm.model_for('bulk')}", file=sys.stderr)
    t0 = time.time()
    drafts = rewrite.with_llm(paragraphs, graph, product)
    kept, dropped = clean(drafts, graph.paragraphs)
    secs = time.time() - t0
    print(f"drafts {len(drafts)}, kept {len(kept)}, dropped {len(dropped)}, {secs:.0f}s")
    new = [
        {
            "id": f"R-{i:04d}",
            "text": d.text,
            "source": {
                "regulation": d.paragraph.regulation,
                "version": d.paragraph.version,
                "page": d.paragraph.page,
                "paragraph": d.paragraph.label,
            },
            "quote": d.quote[:1000],
        }
        for i, d in enumerate(kept, 1)
    ]
    out = {"team_id": source["team_id"], "case_id": source["case_id"], "requirements": new}
    Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    exp = json.loads((CASES / "dev-rear-lamp" / "expected.json").read_text())["requirements"]
    for name, rs in ((args.source, rows), (args.out, new)):
        m = len(judge.match(rs, exp))
        p, r = m / len(rs), m / len(exp)
        print(f"{name}: rows {len(rs)} matched {m} P {p:.3f} R {r:.3f} F2 {fbeta(p, r):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
