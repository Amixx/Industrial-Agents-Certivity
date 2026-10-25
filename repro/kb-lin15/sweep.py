"""kb lineage: section-cut sweep on its own p_keep and p_section, dev (est F2 from capacity, x165/167) and bumper silver paragraph F2."""
import json, csv, re, math, collections
K='/Users/imantsliepins/Personal/bench-out/kbbump/'; R='/Users/imantsliepins/Personal/wt-backup-0724/repro/'
L='/Users/imantsliepins/Personal/wt-ready/brain/data/bumper-labels/'
def key(l): t=re.sub(r"[,;:()\[\]]"," ",l.casefold()); t=re.sub(r"(?<![0-9a-z])\.|\.(?![0-9a-z])"," ",t); return " ".join(t.split())
REGS=('UN R42','UN R26','UN R127')
silver=set()
for f in ('labels-r42-r26.csv','labels-r127-gtr9.csv'):
    for r in csv.DictReader(open(L+f)):
        if r['cited']=='y' and r['regulation'] in REGS and not r['paragraph'].startswith('('): silver.add((r['regulation'],key(r['paragraph'])))
gold=json.load(open('/Users/imantsliepins/Personal/Industrial-Agents-Certivity/cases/dev-rear-lamp/expected.json'))['requirements']
G=collections.Counter((g['source']['regulation'],key(g['source']['paragraph'])) for g in gold)
def load(rows_f,pk_f,ps):
    rows=json.load(open(rows_f))['requirements']; pk=json.load(open(pk_f))
    return [((r['source']['regulation'],key(r['source']['paragraph'])),p,ps.get(f"{r['source']['regulation']}|{key(r['source']['paragraph'])}") or 1.0) for r,p in zip(rows,pk)]
dev=load(R+'out/j20f-all.json',R+'out/j20f-all.pkeep.json',json.load(open(R+'p_section.json')))
cases={n:load(K+n+'.json',K+n+'.pkeep.json',json.load(open(K+n+'.psec.json'))) for n in ('plain','sensfog')}
rules={'lin':lambda a,b:a*b,'sqrt':lambda a,b:a*math.sqrt(b)}
print('rule     t | dev rows off cap estF2 | plain rows F2 | sensfog rows F2')
for rn,fn in rules.items():
    for t in (0.0,0.10,0.15,0.20,0.25,0.30,0.3535,0.40):
        k=[x for x in dev if fn(x[1],x[2])>=t]; P=collections.Counter(x[0] for x in k)
        cap=sum(min(P[g],G[g]) for g in G); off=sum(v for g,v in P.items() if g not in G); est=5*165/167*cap/(760+len(k))
        s=f"{rn:5}{t:6.3f} | {len(k):4} {off:4} {cap:4} {est:.3f}"
        for n,rows in cases.items():
            kk=[x for x in rows if x[0][0] in REGS and fn(x[1],x[2])>=t]; kp={x[0] for x in kk}; tp=len(kp&silver)
            Pp=tp/max(1,len(kp)); Rr=tp/len(silver); s+=f" | {len(kk):4} {5*Pp*Rr/(4*Pp+Rr) if tp else 0:.3f}"
        print(s)
