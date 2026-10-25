cd ~/Personal/Industrial-Agents-Certivity; python3 - <<'EOF'
import json,collections,copy
src=json.load(open('out/upload/thesis-merge-conditions.json')); rows=src['requirements']
key=lambda s:(s['regulation'],s['paragraph'].strip().rstrip('.').lower())
q=lambda r:(key(r['source']),(r.get('quote') or '').strip())
shared=collections.Counter(q(r) for r in rows); seen=set(); out=[]
for r in rows:
    if shared[q(r)]>1:
        if q(r) in seen: continue
        seen.add(q(r)); out.append(dict(copy.deepcopy(r),text=r['quote'].strip()))
    else: out.append(copy.deepcopy(r))
t=collections.Counter(r['text'] for r in out); dup=sum(c-1 for c in t.values() if c>1)
seen=set(); out2=[]
for r in out:
    if r['text'] in seen: continue
    seen.add(r['text']); out2.append(r)
src['requirements']=[dict(r,id=f'R-{i+1:04d}') for i,r in enumerate(out2)]; src['team_id']='team-06'
json.dump(src,open('out/upload/consolidate.json','w'),indent=1,ensure_ascii=False)
print('rows',len(rows),'-> shared-quote collapse',len(out),'-> exact-duplicate drop',len(out2))
EOF
date +%H:%M:%S