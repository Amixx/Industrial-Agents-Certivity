"""The 0.783 chain end to end on one case, with a model per stage and cost and time per stage.

    cd brain && uv run --frozen python ../repro/speed/chain.py OUT_DIR CASE_DIR [stage=model ...]

Stages: profile, select_regs, relevance, rewrite, keep (the pipeline, through BRAIN_LLM=claude-cli),
sections (p_section, one call per section) and merge (MERGE/SPLIT of list paragraphs). Every stage
runs on claude-opus-5-5 unless named; `codex:<model>` (for example codex:gpt-6-luna) sends a
stage's calls through `codex exec` on the ChatGPT subscription instead of claude -p. The chain is the one `repro/run.sh` and
`repro/consolidate/` rebuild: pipeline with Jev at relative cut 0.20 and p_keep recorded, the
section cut p_keep * sqrt(p_section) >= 0.3535 with the pointer, umbrella and approval-mark rules,
verbatim text for unshared quotes, then the merge, the shared-quote collapse and the exact-duplicate
drop. Answers come from the cache in brain/data/cache, the section and merge answers from CLI_CACHE
when it is set; CACHE_ONLY=1 stops at a miss. With Opus on sections, a section whose paragraphs all
have a score in repro/p_section.json (the 0.783 run's) takes those scores instead of a call.
BRAIN_CLAUDE_CLI_WORKERS caps concurrent claude -p processes (default 10). STOP_AFTER_SELECT=1 stops
after paragraph selection and writes selected.json (paragraph id -> blended score) instead.

OUT_DIR gets final.json, pipeline.json, p_section.json and stats.json: per stage the calls, cache
hits, the cost claude -p reported for the live calls, the cost of every call when it was first
made (cold), and the seconds from its first call to its last.
"""

# ruff: noqa: E501

import collections
import copy
import inspect
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.update(
    BRAIN_LLM="claude-cli",
    BRAIN_CLAUDE_CLI_STRONG="claude-opus-5-5",
    BRAIN_CLAUDE_CLI_BULK="claude-opus-5-5",
    BRAIN_JEV="1",
)
os.environ.setdefault("TYPESAFE_API_KEY", "cache-only")
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, os.getcwd())

import numpy as np  # noqa: E402

from brain import claude_cli, codex_cli, ingest, jev, keep, llm, pipeline, relevance  # noqa: E402
from brain import graph as G  # noqa: E402
from eval.score import paragraph_key  # noqa: E402

OPUS = "claude-opus-5-5"
out_dir, case = Path(sys.argv[1]), Path(sys.argv[2])
MODELS = dict(a.split("=", 1) for a in sys.argv[3:])
CACHE_ONLY = os.environ.get("CACHE_ONLY") == "1"
CLI_CACHE = Path(os.environ["CLI_CACHE"]) if os.environ.get("CLI_CACHE") else None
out_dir.mkdir(parents=True, exist_ok=True)

lock = threading.Lock()
stats: dict = collections.defaultdict(
    lambda: {
        "model": OPUS,
        "calls": 0,
        "hits": 0,
        "live_usd": 0.0,
        "cold_usd": 0.0,
        "first": None,
        "last": None,
    }
)
_stage = threading.local()


def _note(stage: str, model: str, hit: bool, cost: float | None, start: float) -> None:
    with lock:
        s = stats[stage]
        s["model"] = model
        s["calls"] += 1
        s["hits"] += hit
        s["cold_usd"] += cost or 0.0
        if not hit:
            s["live_usd"] += cost or 0.0
        s["first"] = start if s["first"] is None else min(s["first"], start)
        s["last"] = max(s["last"] or 0.0, time.monotonic())


def codex(stage: str, model: str, system: str, content, schema: dict) -> dict:
    prompt = content if isinstance(content, str) else "\n\n".join(b["text"] for b in content)
    hit = codex_cli._cache_path(
        {
            "system": system,
            "prompt": prompt,
            "schema": schema,
            "model": model,
            "e": codex_cli.EFFORT,
        }
    ).exists()
    if not hit and CACHE_ONLY:
        raise SystemExit(f"cache miss in {stage}")
    start = time.monotonic()
    with llm._CLI_SLOTS:
        result = codex_cli.complete_json(system, prompt, schema, model)
    _note(stage, f"codex:{model}", hit, None, start)
    return result


# Pipeline stages: llm.complete_json picks the model with model_for(tier) in the calling thread.
_model_for = llm.model_for
llm.model_for = lambda tier: getattr(_stage, "model", None) or _model_for(tier)
_complete = llm.complete_json


def complete_json(system, content, schema, *, tier="bulk", effort="medium", max_tokens=16000):
    stage = next(
        name.removeprefix("brain.")
        for f in inspect.stack()[1:]
        if (name := f.frame.f_globals.get("__name__", "")).startswith("brain.")
        and name != "brain.llm"
    )
    model = MODELS.get(stage, OPUS)
    if model.startswith("codex:"):
        return codex(stage, model.removeprefix("codex:"), system, content, schema)
    _stage.model = model
    payload = {
        "provider": "claude-cli",
        "model": model,
        "system": system,
        "content": content,
        "schema": schema,
        "effort": effort,
    }
    path = llm._cache_path(payload)
    hit = path.exists()
    if not hit and CACHE_ONLY:
        raise SystemExit(f"cache miss in {stage}")
    start = time.monotonic()
    try:
        result = _complete(system, content, schema, tier=tier, effort=effort, max_tokens=max_tokens)
    finally:
        _stage.model = None
    meta = path.with_suffix(".usage.json")
    cost = json.loads(meta.read_text()).get("cost_usd") if meta.exists() else None
    _note(stage, model, hit, cost, start)
    return result


llm.complete_json = complete_json
if CACHE_ONLY:

    def _no_jev(*a, **kw):
        raise SystemExit("cache miss in jev")

    jev._post = _no_jev


def cli(stage: str, system: str, prompt: str, schema: dict) -> dict:
    """One claude -p call outside the pipeline, as select.py and merge_llm.py made them."""
    model = MODELS.get(stage, OPUS)
    if model.startswith("codex:"):
        return codex(stage, model.removeprefix("codex:"), system, prompt, schema)
    if CLI_CACHE is not None:
        claude_cli.CACHE = CLI_CACHE
    hit = claude_cli._cache_path(
        {"system": system, "prompt": prompt, "schema": schema, "model": model}
    ).exists()
    if not hit and CACHE_ONLY:
        raise SystemExit(f"cache miss in {stage}")
    got: dict = {}
    start = time.monotonic()

    def on_usage(u: dict, cost: float | None) -> None:
        got["cost"] = cost

    with llm._CLI_SLOTS:
        result = claude_cli.complete_json(system, prompt, schema, model, on_usage=on_usage)
    _note(stage, model, hit, got.get("cost"), start)
    return result


# 1. Pipeline: Jev at relative cut 0.20, requirement filter off, p_keep recorded.
relevance.RELATIVE_JEV = 0.20
keep.THRESHOLD = 0.0
p_keep: list[float] = []
_scores = keep.scores


def scores(drafts, product):
    s = _scores(drafts, product)
    p_keep.extend(s)
    return s


keep.scores = scores
if os.environ.get("STOP_AFTER_SELECT") == "1":
    _select = pipeline.select_paragraphs

    def select_paragraphs(*a, **kw):
        chosen, graph = _select(*a, **kw)
        (out_dir / "selected.json").write_text(json.dumps({p.id: s for p, s in chosen}))
        raise SystemExit(0)

    pipeline.select_paragraphs = select_paragraphs
t0 = time.monotonic()
spec = (case / "spec.md").read_text()
image = case / "exploded_view.png"
try:
    sub = pipeline.run(
        spec, image if image.exists() else None, case_id=case.name, team_id="team-06"
    )
except SystemExit:
    report = {
        n: {
            k: (round(v, 3) if isinstance(v, float) else v)
            for k, v in s.items()
            if k not in ("first", "last")
        }
        | {"span_s": round((s["last"] or 0) - (s["first"] or 0), 1)}
        for n, s in stats.items()
    }
    (out_dir / "stats.json").write_text(json.dumps({"models": MODELS, "stages": report}, indent=1))
    print(json.dumps(report.get("relevance", {})))
    raise
t_pipeline = time.monotonic() - t0
(out_dir / "pipeline.json").write_text(json.dumps(sub, indent=1, ensure_ascii=False))
rows, profile = sub["requirements"], sub["profile"]

# 2. p_section: every cited paragraph of one section together (bench-out/section/select.py).
regs = sorted({r["source"]["regulation"] for r in rows})
corpus = {reg: ingest.load(reg) for reg in regs}
graph = G.build(corpus)
by_label = {(reg, paragraph_key(p.label)): p for reg, ps in corpus.items() for p in ps}


def section(reg, key, depth):
    if key.startswith("annex"):
        _, _, rest = key.partition(" ")
        num, _, _ = rest.partition(" ")
        return (reg, f"annex {num}")
    return (reg, ".".join(key.split(".")[:depth]))


def order(key):
    return [int(x) if x.isdigit() else 0 for x in key.replace(" ", ".").split(".")]


keys = {
    (r["source"]["regulation"], paragraph_key(r["source"]["paragraph"]))
    for r in rows
    if (r["source"]["regulation"], paragraph_key(r["source"]["paragraph"])) in by_label
}
top = collections.defaultdict(list)
for reg, key in keys:
    top[section(reg, key, 1)].append(key)
cited: dict = collections.defaultdict(dict)
for (reg, sec), ks in top.items():
    if len(ks) <= 25:
        cited[(reg, sec)] = {k: by_label[(reg, k)] for k in ks}
        continue
    subs = collections.defaultdict(list)
    for k in ks:
        subs[section(reg, k, 2)[1]].append(k)
    chunk, name = [], None
    for sub_name in sorted(subs, key=order):
        if chunk and len(chunk) + len(subs[sub_name]) > 20:
            cited[(reg, name)] = {k: by_label[(reg, k)] for k in chunk}
            chunk, name = [], None
        chunk += subs[sub_name]
        name = sub_name if name is None else name.split("-")[0] + "-" + sub_name
    cited[(reg, name)] = {k: by_label[(reg, k)] for k in chunk}


def heading_path(p):
    names = []
    for pid in p.path:
        q = graph.paragraphs.get(pid)
        if q is not None:
            names.append(f"{q.label} {q.heading or q.text[:60]}")
    return " > ".join(names)


SECTION_SYSTEM = """You are a type-approval engineer preparing the requirement list for one automotive
component. You see the paragraphs of one section of a UN Regulation that a first pass marked as
possibly relevant, together, in document order. For each paragraph give the probability that an
expert's final requirement list for this component cites it: the expert cites the paragraphs
whose requirements an engineer designing or testing this component has to meet, and leaves out
the rest of the section."""
SECTION_SCHEMA = {"type": "object", "properties": {"paragraphs": {"type": "array", "items": {"type": "object",
    "properties": {"label": {"type": "string"}, "p": {"type": "number"}}, "required": ["label", "p"],
    "additionalProperties": False}}}, "required": ["paragraphs"], "additionalProperties": False}  # fmt: skip
product = json.dumps(
    {
        k: profile[k]
        for k in ("product", "vehicle_categories", "functions", "parts")
        if k in profile
    },
    ensure_ascii=False,
)


SAVED = json.loads((Path(__file__).parents[1] / "p_section.json").read_text())


def ask(item):
    (reg, sec), paras = item
    saved = {f"{reg}|{k}": SAVED.get(f"{reg}|{k}") for k in paras}
    if MODELS.get("sections", OPUS) == OPUS and None not in saved.values():
        with lock:
            stats["sections"]["calls"] += 1
            stats["sections"]["hits"] += 1
        return saved
    ps = sorted(paras.values(), key=lambda p: p.page)
    listing = "\n\n".join(f"[{p.label}] {heading_path(p)}\n{p.text[:700]}" for p in ps)
    prompt = (
        f"Component: {product}\n\nRegulation: {reg}, section {sec}\n\n{listing}\n\n"
        f"Give a probability for each of the {len(ps)} paragraphs, by label."
    )
    out = cli("sections", SECTION_SYSTEM, prompt, SECTION_SCHEMA)["paragraphs"]
    got = {paragraph_key(d["label"]): d["p"] for d in out}
    return {f"{reg}|{k}": got.get(k) for k in paras}


t0 = time.monotonic()
p_section: dict = {}
with ThreadPoolExecutor(6) as pool:
    for d in pool.map(ask, sorted(cited.items())):
        p_section.update(d)
t_sections = time.monotonic() - t0
(out_dir / "p_section.json").write_text(json.dumps(p_section, indent=0))

# 3. Section cut and rules (repro/section_stage.py), then verbatim --all (repro/verbatim.py).
POINTER = re.compile(
    r"^[^.;]{0,90}?:?\s*see\s+(?:paragraph|table|annex|figure)s?\b[^;]{0,40}\.?$", re.I
)
UMBRELLA = re.compile(
    r"(?:shall\s+(?:conform|comply)\s+(?:to|with)\s+the\s+requirements\s+(?:set\s+forth|specified|contained)\s+in\s+(?:paragraphs?|sections?)|the\s+requirements\s+contained\s+in\s+sections?\s+[\d.]+.{0,80}?\s+shall\s+apply|shall\s+be\s+so\s+manufactured\s+as\s+to\s+conform\s+to\s+the\s+type\s+approved)",
    re.I,
)
MARK = re.compile(r"circle\s+(?:surrounding|containing)\s+the\s+letter|number\s+of\s+this\s+regulation,?\s+followed\s+by\s+the\s+letter|approval\s+marking\s+shall\s+consist\s+of|symbols\s+identifying\s+the", re.I)  # fmt: skip


def hit(r):
    q = r["quote"].strip()
    return bool(POINTER.match(q)) or bool(UMBRELLA.search(q)) or bool(MARK.search(q))


sec = np.array([
    p_section.get(f"{r['source']['regulation']}|{paragraph_key(r['source']['paragraph'])}") or 1.0
    for r in rows
])  # fmt: skip
mask = np.array([not hit(r) for r in rows]) & (np.array(p_keep) * np.sqrt(sec) >= 0.3535)
rows = [copy.deepcopy(r) for r, k in zip(rows, mask, strict=True) if k]
def quote_key(r):
    return (r["source"]["regulation"], r["source"].get("paragraph", ""), r["quote"].strip())


shared = collections.Counter(quote_key(r) for r in rows)
for r in rows:
    q = r["quote"].strip()
    if shared[quote_key(r)] == 1 and len(q) >= 20:
        r["text"] = q[:2000]

# 4. Merge (repro/consolidate/merge_llm.py), shared-quote collapse and exact-duplicate drop
# (repro/consolidate/build_consolidate.sh).
key = lambda s: (s["regulation"], s["paragraph"].strip().rstrip(".").lower())  # noqa: E731
ITEM = re.compile(r"^\s*\(?([a-z]|[ivx]{1,4}|\d{1,2})\)\s")
MODAL = re.compile(r"\b(shall|must|may|is required|are required)\b", re.I)
by: dict = collections.OrderedDict()
for r in rows:
    by.setdefault(key(r["source"]), []).append(r)
labels = {}
for reg in {k[0] for k in by}:
    for p in ingest.load(reg):
        labels[(reg, p.label.strip().rstrip(".").lower())] = p
cand = [
    k for k, rs in by.items()
    if len(rs) >= 2 and k in labels and any(ITEM.match(r["text"]) and not MODAL.search(r["text"]) for r in rs)
]  # fmt: skip
MERGE_SYSTEM = """You decide how a regulatory expert turns a paragraph containing a list into requirements.
- MERGE: the list items are cases, conditions, alternatives or circumstances under which ONE obligation or permission applies (e.g. "lamps with: (a) X; (b) Y shall bear ...", "the intensity may vary: (a) when ...; (b) when ..."). The expert writes one requirement for the whole paragraph.
- SPLIT: each list item is a separate thing that must be done, borne, met or provided, with its own content or value (e.g. "shall bear: (i) the trade name; (ii) the code; (iii) the voltage", or items each with its own limit). The expert writes one requirement per item.
Answer for every paragraph."""
MERGE_SCHEMA = {"type":"object","required":["paragraphs"],"properties":{"paragraphs":{"type":"array","items":{"type":"object","required":["key","decision"],"properties":{"key":{"type":"string"},"decision":{"type":"string","enum":["MERGE","SPLIT"]}}}}}}  # fmt: skip
t0 = time.monotonic()
items = [{"key": f"{k[0]}|{k[1]}", "text": labels[k].text} for k in cand]
dec = {}
if items:
    res = cli(
        "merge",
        MERGE_SYSTEM,
        "Paragraphs (JSON):\n" + json.dumps(items, ensure_ascii=False, indent=1),
        MERGE_SCHEMA,
    )
    dec = {p["key"]: p["decision"] for p in res["paragraphs"]}
t_merge = time.monotonic() - t0
merged = []
for k, rs in by.items():
    if dec.get(f"{k[0]}|{k[1]}") == "MERGE":
        text = re.sub(r"\s+", " ", labels[k].text).strip()
        merged.append(dict(copy.deepcopy(rs[0]), text=text, quote=text))
    else:
        merged += [copy.deepcopy(r) for r in rs]
q = lambda r: (key(r["source"]), (r.get("quote") or "").strip())  # noqa: E731
shared = collections.Counter(q(r) for r in merged)
seen, out = set(), []
for r in merged:
    if shared[q(r)] > 1:
        if q(r) in seen:
            continue
        seen.add(q(r))
        out.append(dict(r, text=r["quote"].strip()))
    else:
        out.append(r)
seen, final = set(), []
for r in out:
    if r["text"] in seen:
        continue
    seen.add(r["text"])
    final.append(r)
sub["requirements"] = [dict(r, id=f"R-{i + 1:04d}") for i, r in enumerate(final)]
sub["team_id"] = "team-06"
(out_dir / "final.json").write_text(json.dumps(sub, indent=1, ensure_ascii=False))

report = {
    name: {
        **{k: v for k, v in s.items() if k not in ("first", "last")},
        "live_usd": round(s["live_usd"], 3),
        "cold_usd": round(s["cold_usd"], 3),
        "span_s": round((s["last"] or s["first"]) - s["first"], 1) if s["first"] else 0.0,
    }
    for name, s in stats.items()
}
summary = {
    "models": MODELS,
    "workers": llm.CLI_WORKERS,
    "rows": len(final),
    "seconds": {
        "pipeline": round(t_pipeline, 1),
        "sections": round(t_sections, 1),
        "merge": round(t_merge, 1),
    },
    "live_usd": round(sum(s["live_usd"] for s in stats.values()), 3),
    "cold_usd": round(sum(s["cold_usd"] for s in stats.values()), 3),
    "stages": report,
}
(out_dir / "stats.json").write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "stages"}))
for name, s in report.items():
    print(
        f"  {name:12} {s['model']:18} calls {s['calls']:4} hits {s['hits']:4} "
        f"live ${s['live_usd']:.2f} cold ${s['cold_usd']:.2f} span {s['span_s']}s"
    )
