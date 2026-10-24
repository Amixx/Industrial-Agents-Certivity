"""requirements*.tsv (regulation<TAB>paragraph<TAB>text) -> submission JSON with version and page from the corpus."""
import json, re, sys
from pathlib import Path
CORPUS = Path.home() / "Personal/Industrial-Agents-Certivity-select/brain/data/corpus"
folder, out = Path(sys.argv[1]), Path(sys.argv[2])
norm = lambda s: re.sub(r"[\s,]+", " ", s.strip().rstrip(".").lower())
paras = {}
rows, bad = [], []
for f in sorted(folder.glob("requirements*.tsv")):
    for n, line in enumerate(f.read_text().splitlines(), 1):
        if not line.strip(): continue
        parts = line.split("\t")
        if len(parts) != 3: bad.append(f"{f.name}:{n} not 3 columns"); continue
        reg, label, text = (p.strip() for p in parts)
        if reg not in paras:
            p = CORPUS / f"{reg.replace(' ', '_')}_base.jsonl"
            paras[reg] = {norm(d["label"]): d for d in map(json.loads, p.read_text().splitlines())} if p.exists() else {}
        d = paras[reg].get(norm(label))
        if not d: bad.append(f"{f.name}:{n} unknown paragraph {reg} {label}"); continue
        rows.append({"id": f"R-{len(rows)+1:04d}", "text": text, "source": {"regulation": reg, "version": d["version"], "page": d["page"], "paragraph": d["label"]}})
out.write_text(json.dumps({"team_id": "team-06", "case_id": "dev-rear-lamp", "requirements": rows}, indent=1, ensure_ascii=False))
print(f"{len(rows)} requirements, {len(bad)} problems"); print("\n".join(bad[:30]))
