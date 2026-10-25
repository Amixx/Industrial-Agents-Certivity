"""Merge a paragraph's list-item rows into one verbatim row only where the items are cases or conditions of one obligation."""
import json, re, collections, copy
from brain import claude_cli, ingest
R='/Users/imantsliepins/Personal/wt-backup-0724/repro/'; O='/Users/imantsliepins/Personal/Industrial-Agents-Certivity/out/upload/'
up=json.load(open(R+'uploaded-0724.json')); rows=up['requirements']
gold=json.load(open('/Users/imantsliepins/Personal/Industrial-Agents-Certivity/cases/dev-rear-lamp/expected.json'))['requirements']
key=lambda s:(s['regulation'],s['paragraph'].strip().rstrip('.').lower())
G=collections.Counter(key(g['source']) for g in gold)
ITEM=re.compile(r'^\s*\(?([a-z]|[ivx]{1,4}|\d{1,2})\)\s')
MODAL=re.compile(r'\b(shall|must|may|is required|are required)\b', re.I)
by=collections.OrderedDict()
for r in rows: by.setdefault(key(r['source']),[]).append(r)
corpus={}
for reg in {k[0] for k in by}:
    for p in ingest.load(reg): corpus[(reg, p.label.strip().rstrip('.').lower())]=p
cand=[k for k,rs in by.items() if len(rs)>=2 and k in corpus and any(ITEM.match(r['text']) and not MODAL.search(r['text']) for r in rs)]
SYSTEM="""You decide how a regulatory expert turns a paragraph containing a list into requirements.
- MERGE: the list items are cases, conditions, alternatives or circumstances under which ONE obligation or permission applies (e.g. "lamps with: (a) X; (b) Y shall bear ...", "the intensity may vary: (a) when ...; (b) when ..."). The expert writes one requirement for the whole paragraph.
- SPLIT: each list item is a separate thing that must be done, borne, met or provided, with its own content or value (e.g. "shall bear: (i) the trade name; (ii) the code; (iii) the voltage", or items each with its own limit). The expert writes one requirement per item.
Answer for every paragraph."""
SCHEMA={"type":"object","required":["paragraphs"],"properties":{"paragraphs":{"type":"array","items":{"type":"object","required":["key","decision"],"properties":{"key":{"type":"string"},"decision":{"type":"string","enum":["MERGE","SPLIT"]}}}}}}
items=[{"key":f"{k[0]}|{k[1]}","text":corpus[k].text} for k in cand]
res=claude_cli.complete_json(SYSTEM,"Paragraphs (JSON):\n"+json.dumps(items,ensure_ascii=False,indent=1),SCHEMA,model="claude-opus-5-5")
dec={p["key"]:p["decision"] for p in res["paragraphs"]}
out=[]; log=[]
for k,rs in by.items():
    if dec.get(f"{k[0]}|{k[1]}")=="MERGE":
        text=re.sub(r'\s+',' ',corpus[k].text).strip(); out.append(dict(copy.deepcopy(rs[0]),text=text,quote=text))
    else: out+=[copy.deepcopy(r) for r in rs]
    if k in cand: log.append((k[0]+' '+k[1],dec.get(f"{k[0]}|{k[1]}"),len(rs),G.get(k,0)))
P=collections.Counter(key(r['source']) for r in out); P0=collections.Counter(key(r['source']) for r in rows)
cap=lambda P: sum(min(P[k],G[k]) for k in G)
print('rows',len(rows),'->',len(out),' count ceiling',cap(P0),'->',cap(P))
for l in log: print(' ',l)
d={k:v for k,v in up.items() if k!='requirements'}; d['team_id']='team-06'
d['requirements']=[dict(r,id=f'R-{i+1:04d}') for i,r in enumerate(out)]
json.dump(d,open(O+'thesis-merge-conditions.json','w'),indent=1,ensure_ascii=False)
