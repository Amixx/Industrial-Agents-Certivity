"""consolidate-v2 arms from the consolidated file.
merge: Opus decides for every paragraph with 2+ rows whether an expert writes ONE requirement or SEVERAL; ONE becomes one verbatim row.
whole: a paragraph's single row becomes the whole paragraph text when the paragraph holds at most one shall/must and is short."""
import json, re, collections, copy, sys
from brain import claude_cli, ingest
O='/Users/imantsliepins/Personal/Industrial-Agents-Certivity/'
arm=sys.argv[1]; src=sys.argv[2] if len(sys.argv)>2 else O+'out/upload/consolidate.json'
up=json.load(open(src)); rows=up['requirements']
gold=json.load(open(O+'cases/dev-rear-lamp/expected.json'))['requirements']
key=lambda s:(s['regulation'],s['paragraph'].strip().rstrip('.').lower())
G=collections.Counter(key(g['source']) for g in gold)
by=collections.OrderedDict()
for r in rows: by.setdefault(key(r['source']),[]).append(r)
corpus={}
for reg in {k[0] for k in by}:
    for p in ingest.load(reg): corpus[(reg,p.label.strip().rstrip('.').lower())]=p
norm=lambda t:re.sub(r'\s+',' ',t).strip()
MOD=re.compile(r'\b(shall|must)\b',re.I)
out=[]; log=[]
if arm=='merge':
    cand=[k for k,rs in by.items() if len(rs)>=2 and k in corpus]
    SYSTEM="""You decide how a regulatory expert turns one regulation paragraph into requirements for a requirements list.
- ONE: the paragraph states a single obligation or permission. Its parts are cases, conditions, alternatives, exceptions, explanations or details of that one obligation. The expert writes one requirement: the whole paragraph.
- SEVERAL: the paragraph states separate obligations, each with its own subject, action or limit, that an engineer would check separately. The expert writes one requirement per obligation.
You also see the rows currently drafted from the paragraph. Answer for every paragraph."""
    SCHEMA={"type":"object","required":["paragraphs"],"properties":{"paragraphs":{"type":"array","items":{"type":"object","required":["key","decision"],"properties":{"key":{"type":"string"},"decision":{"type":"string","enum":["ONE","SEVERAL"]}}}}}}
    items=[{"key":f"{k[0]}|{k[1]}","paragraph":norm(corpus[k].text),"drafted_rows":[r['text'] for r in by[k]]} for k in cand]
    import os
    D='/Users/imantsliepins/Personal/bench-out/v2/merge-decisions.json'
    if os.path.exists(D): dec=json.load(open(D))
    else:
        res=claude_cli.complete_json(SYSTEM,"Paragraphs (JSON):\n"+json.dumps(items,ensure_ascii=False,indent=1),SCHEMA,model="claude-opus-5-5")
        dec={p["key"]:p["decision"] for p in res["paragraphs"]}
    json.dump(dec,open('/Users/imantsliepins/Personal/bench-out/v2/merge-decisions.json','w'),indent=1)
    for k,rs in by.items():
        if dec.get(f"{k[0]}|{k[1]}")=="ONE" and len(norm(corpus[k].text))<=2000:
            t=norm(corpus[k].text); out.append(dict(copy.deepcopy(rs[0]),text=t,quote=t))
        else: out+=[copy.deepcopy(r) for r in rs]
        if k in cand: log.append((k,dec.get(f"{k[0]}|{k[1]}"),len(rs),G.get(k,0)))
elif arm=='whole':
    for k,rs in by.items():
        if len(rs)==1 and k in corpus:
            w=norm(corpus[k].text); t=norm(rs[0]['text'])
            if t.rstrip('.')!=w.rstrip('.') and len(w)<=2000 and len(MOD.findall(w))<=1 and len(w)<=700:
                out.append(dict(copy.deepcopy(rs[0]),text=w,quote=w)); log.append((k,'WHOLE',1,G.get(k,0))); continue
        out+=[copy.deepcopy(r) for r in rs]
P=collections.Counter(key(r['source']) for r in out); P0=collections.Counter(key(r['source']) for r in rows)
cap=lambda P: sum(min(P[k],G[k]) for k in G)
print(arm,'rows',len(rows),'->',len(out),' capacity',cap(P0),'->',cap(P))
c=collections.Counter((d,g>0, 'gold1' if g==1 else 'gold>1' if g>1 else 'gold0') for _,d,n,g in log); print(c)
d={k:v for k,v in up.items() if k!='requirements'}; d['team_id']='team-06'
d['requirements']=[dict(r,id=f'R-{i+1:04d}') for i,r in enumerate(out)]
dst=sys.argv[3] if len(sys.argv)>3 else O+f'out/upload/v2-{arm}.json'
json.dump(d,open(dst,'w'),indent=1,ensure_ascii=False); print('wrote',dst)
