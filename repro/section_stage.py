"""Stage uploads: the section cut (p_keep * sqrt(p_section) >= 0.3535) plus the pointer, umbrella and approval-mark rules.

    stage.py <out.json> <source.json> [--pkeep <source.pkeep.json>]

Without --pkeep the source is taken as already cut and only the rule is applied."""
import json, re, sys
from pathlib import Path
import numpy as np
from eval.score import paragraph_key
B = Path.home() / 'Personal/bench-out'
POINTER = re.compile(r"^[^.;]{0,90}?:?\s*see\s+(?:paragraph|table|annex|figure)s?\b[^;]{0,40}\.?$", re.I)
UMBRELLA = re.compile(r"(?:shall\s+(?:conform|comply)\s+(?:to|with)\s+the\s+requirements\s+(?:set\s+forth|specified|contained)\s+in\s+(?:paragraphs?|sections?)|the\s+requirements\s+contained\s+in\s+sections?\s+[\d.]+.{0,80}?\s+shall\s+apply|shall\s+be\s+so\s+manufactured\s+as\s+to\s+conform\s+to\s+the\s+type\s+approved)", re.I)
# Items that spell out the approval mark itself, which the approval authority assigns.
MARK = re.compile(r"circle\s+(?:surrounding|containing)\s+the\s+letter|number\s+of\s+this\s+regulation,?\s+followed\s+by\s+the\s+letter|approval\s+marking\s+shall\s+consist\s+of|symbols\s+identifying\s+the", re.I)
def hit(r):
    q = r['quote'].strip()
    return bool(POINTER.match(q)) or bool(UMBRELLA.search(q)) or bool(MARK.search(q))
out, src = sys.argv[1], sys.argv[2]
sub = json.load(open(src))
rows = sub['requirements']
keep = np.array([not hit(r) for r in rows])
if '--pkeep' in sys.argv:
    pk = np.array(json.load(open(sys.argv[sys.argv.index('--pkeep') + 1])))
    ps = json.load(open(Path(__file__).parent / 'p_section.json'))
    sec = np.array([ps.get(f"{r['source']['regulation']}|{paragraph_key(r['source']['paragraph'])}", 1.0) for r in rows])
    keep &= pk * np.sqrt(sec) >= 0.3535  # keeps p_keep 0.5 with p_section 0.5 (0.35355)
sub['requirements'] = [r for r, k in zip(rows, keep) if k]
sub['team_id'] = 'team-06'
json.dump(sub, open(out, 'w'), indent=1, ensure_ascii=False)
print(f"{out}: {len(sub['requirements'])} of {len(rows)} rows")
