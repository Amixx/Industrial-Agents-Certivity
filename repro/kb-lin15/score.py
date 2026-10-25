"""Paragraph P/R/F2 against the bumper silver labels (R42, R26, R127) for submission files, plus row counts."""
import json, csv, re, sys
L='/Users/imantsliepins/Personal/wt-ready/brain/data/bumper-labels/'
REGS=('UN R42','UN R26','UN R127')
def key(l): t=re.sub(r"[,;:()\[\]]"," ",l.casefold()); t=re.sub(r"(?<![0-9a-z])\.|\.(?![0-9a-z])"," ",t); return " ".join(t.split())
silver=set()
for f in ('labels-r42-r26.csv','labels-r127-gtr9.csv'):
    for r in csv.DictReader(open(L+f)):
        if r['cited']=='y' and r['regulation'] in REGS and not r['paragraph'].startswith('('): silver.add((r['regulation'],key(r['paragraph'])))
for f in sys.argv[1:]:
    rows=[r for r in json.load(open(f))['requirements'] if r['source']['regulation'] in REGS]
    kp={(r['source']['regulation'],key(r['source']['paragraph'])) for r in rows}; tp=len(kp&silver)
    P=tp/max(1,len(kp)); R=tp/len(silver); F=5*P*R/(4*P+R) if tp else 0
    print(f"{f.split('/')[-1]:40} rows {len(rows):4} paras {len(kp):4} hit {tp:3}/{len(silver)}  P {P:.2f} R {R:.2f} F2 {F:.3f}")
