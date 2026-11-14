#!/usr/bin/env python3
"""Release gate for a weekly new-price refresh. Exit 1 (do not deploy) unless every check passes.
Writes release-check.json in the run folder."""
import json, re, sys
from pathlib import Path
ROOT=Path('/Users/shane/Documents/Claude/Projects/rt buyback tool');W=Path(__file__).resolve().parent
read=lambda f:json.loads((W/f).read_text())
run=read('run.json');checks={};notes=[]
def check(name,ok,detail=''):
    checks[name]={'ok':bool(ok),'detail':detail}
PAT=re.compile(r'^const DB = (\{[^\r\n]*\});[ \t]*$',re.M)
cand_html=(W/'candidate/index.html').read_text();cand_raw=(W/'candidate/phone_db.json').read_text()
m=PAT.search(cand_html);cand=json.loads(cand_raw);base=read('baseline/phone_db.json')
check('candidate pair identical',m and m[1]==cand_raw)
check('version',cand['_meta']['version']==run['version'],cand['_meta']['version'])
check('html outside DB line unchanged',PAT.sub('',cand_html)==PAT.sub('',(W/'baseline/index.html').read_text()))
check('same catalogue keys',sorted(cand)==sorted(base),f"{len(cand)-1} records")
check('production unchanged since baseline',(ROOT/'phone_db.json').read_bytes()==(W/'baseline/phone_db.json').read_bytes() and (ROOT/'index.html').read_bytes()==(W/'baseline/index.html').read_bytes())
t=(W/'tests.log').read_text();check('all JS suites pass',re.search(r'SUITES (\d+) FAILED 0$',t,re.M) and int(re.search(r'SUITES (\d+)',t)[1])>=11,t.strip().splitlines()[-1])
cov=read('coverage-validation.json');check('full-catalogue coverage',cov.get('results_complete') is True)
s=cand['_meta']['last_scoped_market_refresh'];check('verified new prices >= 450 (sources not blocked)',s['new_prices_verified']>=450,f"{s['new_prices_verified']} verified / {s['scope_count']}")
res=json.loads((W/'resolve.log').read_text()[(W/'resolve.log').read_text().index('{'):]) if '{' in (W/'resolve.log').read_text() else {}
check('no numeric inversions',res.get('numeric_inversions')==0,str(res.get('numeric_inversions')))
qc=read('quote-comparison.json')['rows']
changed=[r for r in qc if r['old_quick_estimate'] is not None and r['old_quick_estimate']!=r['new_quick_estimate']]
rises=[r for r in changed if r['new_quick_estimate'] is not None and r['new_quick_estimate']>r['old_quick_estimate']*1.08]
lost=[r for r in changed if r['new_quick_estimate'] is None]
check('no-age quote changes <= 40',len(changed)<=40,f"{len(changed)} changed")
check('no no-age quote rises above 8%',not rises,'; '.join(f"{r['model']} {r['old_quick_estimate']}->{r['new_quick_estimate']}" for r in rises[:10]))
check('no model lost its no-age quote',not lost,'; '.join(r['model'] for r in lost[:10]))
blocked=lambda db:sum(1 for k,e in db.items() if k!='_meta' and (e.get('quote_safety') or {}).get('requires_counter_review'))
check('no new counter blocks',blocked(cand)<=blocked(base),f"{blocked(base)} -> {blocked(cand)}")
ok=all(c['ok'] for c in checks.values())
out={'ok':ok,'version':run['version'],'checks':checks,'no_age_changes':[{k:r[k] for k in ('model','old_quick_estimate','new_quick_estimate')} for r in changed]}
(W/'release-check.json').write_text(json.dumps(out,indent=1)+'\n')
for k,c in checks.items():print(('PASS ' if c['ok'] else 'FAIL ')+k+(' | '+c['detail'] if c['detail'] else ''))
print('RELEASE CHECK','OK' if ok else 'FAILED - do not deploy')
sys.exit(0 if ok else 1)
