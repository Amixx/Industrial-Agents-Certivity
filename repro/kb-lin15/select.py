"""Section-level paragraph selection: Opus sees every cited paragraph of one section together and
gives each a probability that an expert's requirement list for the product cites it."""
import json, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from brain import claude_cli, graph as G, ingest
from eval.score import paragraph_key
B = Path.home() / 'Personal/bench-out'
SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
MODEL = 'claude-opus-5-5'
sub = json.load(open(SRC))
rows, profile = sub['requirements'], sub['profile']
regs = sorted({r['source']['regulation'] for r in rows})
corpus = {reg: ingest.load(reg) for reg in regs}
graph = G.build(corpus)
by_label = {(reg, paragraph_key(p.label)): p for reg, ps in corpus.items() for p in ps}
def section(reg, key, depth):
    if key.startswith('annex'):
        head, _, rest = key.partition(' ')
        num, _, tail = rest.partition(' ')
        return (reg, f"annex {num}")
    return (reg, '.'.join(key.split('.')[:depth]))
keys = set()
for r in rows:
    reg, key = r['source']['regulation'], paragraph_key(r['source']['paragraph'])
    if (reg, key) in by_label:
        keys.add((reg, key))
    else:
        print('no corpus paragraph for', reg, key, file=sys.stderr)
top = defaultdict(list)
for reg, key in keys:
    top[section(reg, key, 1)].append(key)
def order(key):
    return [int(x) if x.isdigit() else 0 for x in key.replace(' ', '.').split('.')]
cited = defaultdict(dict)
for (reg, sec), ks in top.items():
    if len(ks) <= 25:
        cited[(reg, sec)] = {k: by_label[(reg, k)] for k in ks}
        continue
    # Split a long section into its subsections, merging consecutive small ones up to 20.
    subs = defaultdict(list)
    for k in ks:
        subs[section(reg, k, 2)[1]].append(k)
    chunk, name = [], None
    for sub_name in sorted(subs, key=order):
        if chunk and len(chunk) + len(subs[sub_name]) > 20:
            cited[(reg, name)] = {k: by_label[(reg, k)] for k in chunk}
            chunk, name = [], None
        chunk += subs[sub_name]
        name = sub_name if name is None else name.split('-')[0] + '-' + sub_name
    cited[(reg, name)] = {k: by_label[(reg, k)] for k in chunk}
def heading_path(p):
    names = []
    for pid in p.path:
        q = graph.paragraphs.get(pid)
        if q is not None:
            names.append(f"{q.label} {q.heading or q.text[:60]}")
    return ' > '.join(names)
SYSTEM = """You are a type-approval engineer preparing the requirement list for one automotive
component. You see the paragraphs of one section of a UN Regulation that a first pass marked as
possibly relevant, together, in document order. For each paragraph give the probability that an
expert's final requirement list for this component cites it: the expert cites the paragraphs
whose requirements an engineer designing or testing this component has to meet, and leaves out
the rest of the section."""
SCHEMA = {"type": "object", "properties": {"paragraphs": {"type": "array", "items": {"type": "object",
    "properties": {"label": {"type": "string"}, "p": {"type": "number"}}, "required": ["label", "p"],
    "additionalProperties": False}}}, "required": ["paragraphs"], "additionalProperties": False}
product = json.dumps({k: profile[k] for k in ('product', 'vehicle_categories', 'functions', 'parts') if k in profile}, ensure_ascii=False)
def ask(item):
    (reg, sec), paras = item
    ps = sorted(paras.values(), key=lambda p: p.page)
    listing = '\n\n'.join(f"[{p.label}] {heading_path(p)}\n{p.text[:700]}" for p in ps)
    prompt = f"Component: {product}\n\nRegulation: {reg}, section {sec}\n\n{listing}\n\nGive a probability for each of the {len(ps)} paragraphs, by label."
    out = claude_cli.complete_json(SYSTEM, prompt, SCHEMA, MODEL)['paragraphs']
    got = {paragraph_key(d['label']): d['p'] for d in out}
    return {f"{reg}|{k}": got.get(k) for k in paras}
items = sorted(cited.items())
print(len(items), 'sections,', sum(len(v) for v in cited.values()), 'paragraphs', flush=True)
res = {}
with ThreadPoolExecutor(6) as pool:
    for d in pool.map(ask, items):
        res.update({k: v for k, v in d.items() if v is not None})
OUT.write_text(json.dumps(res, indent=0))
print('missing p:', sum(v is None for v in res.values()))
