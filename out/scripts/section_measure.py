import json, collections
from pathlib import Path
from sklearn.metrics import roc_auc_score
from eval.score import paragraph_key, fbeta
B = Path.home() / 'Personal/bench-out'
exp = json.load(open(Path.home() / 'Personal/Industrial-Agents-Certivity/cases/dev-rear-lamp/expected.json'))['requirements']
rows = json.load(open(B / 'j20f-all.json'))['requirements']; pk = json.load(open(B / 'j20f-all.pkeep.json'))
ps = json.load(open(B / 'section/p_section.json'))
K = lambda r: (r['source']['regulation'], paragraph_key(r['source']['paragraph']))
gold = collections.Counter(K(e) for e in exp)
psec = [ps.get(f"{k[0]}|{k[1]}", 1.0) for k in map(K, rows)]
y = [K(r) in gold for r in rows]
print(f"AUC on rows  p_section {roc_auc_score(y, psec):.3f}  p_keep {roc_auc_score(y, pk):.3f}  product {roc_auc_score(y, [a*b for a,b in zip(psec,pk)]):.3f}")
paras = {}
for r, p in zip(rows, psec): paras[K(r)] = p
yp = [k in gold for k in paras]; print(f"AUC on paragraphs p_section {roc_auc_score(yp, list(paras.values())):.3f}")
CONV = 151 / 184
def show(name, keep):
    ks = [K(rows[i]) for i in keep]; on = sum(k in gold for k in ks)
    gp = {k for k in ks if k in gold}; reach = sum(gold[k] for k in gp); m = CONV * reach
    print(f"{name:34} rows {len(ks):4} on-gold {on:4} off {len(ks)-on:4} gold paras {len(gp):4} reachable {reach:4} est F2 {fbeta(m/len(ks), m/190):.3f}")
base = [i for i in range(len(rows)) if pk[i] >= 0.4]
show('filter 0.40 (uploaded)', base)
for t in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
    show(f'filter + p_section >= {t}', [i for i in base if psec[i] >= t])
for t in (0.1, 0.15, 0.2, 0.25, 0.3, 0.4):
    show(f'p_keep * p_section >= {t}', [i for i in range(len(rows)) if pk[i] * psec[i] >= t])
show('oracle: gold paragraphs only', [i for i in base if K(rows[i]) in gold])
