import sys, concurrent.futures
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import _market_refresh_runner as collector
collector.WORK=Path(__file__).resolve().parent
from _market_refresh_runner import *
scope=json.loads((WORK/'scope.json').read_text())['models'];families=json.loads((WORK/'resale-results.json').read_text());variants=[v for r in families for v in r['variants']]
def verify(row):
 candidates=[v for v in variants if family_match(norm(row['family']),norm(v['family'])) and row['storage']==v['storage'] and (row['ram'] is None or row['ram']==v['ram'])]
 candidates.sort(key=lambda v:v['amount_inr']);attempts=[];ref=None;seen=set()
 for v in candidates:
  if v['source_url'] in seen:continue
  seen.add(v['source_url']);raw,meta=fetch(v['source_url']);products=[p for p in ld(raw) if p.get('@type')=='Product'];attempt={'fetch':meta,'accepted':False}
  if meta.get('http_status')==200 and len(products)==1:
   p=products[0];props={a.get('propertyID'):a.get('value') for a in p.get('additionalProperty',[])};ram,storage=ram_storage(props.get('storage',''));of=p.get('offers',{});attempt.update(title=p['name'],properties={k:props.get(k) for k in ['storage','refurbishment-grade','warranty-months']},offer={k:of.get(k) for k in ['price','availability','itemCondition','priceCurrency']})
   if family_match(norm(row['family']),norm(p['name'].split(' - Refurbished')[0])) and storage==row['storage'] and (row['ram'] is None or row['ram']==ram) and props.get('refurbishment-grade')=='Superb' and of.get('priceCurrency')=='INR' and of.get('availability','').endswith('/InStock') and of.get('itemCondition','').endswith('/RefurbishedCondition'):
    attempt['accepted']=True
    ref=dict(v,amount_inr=float(of['price']),observed_at=meta['observed_at'],evidence_file=meta['snapshot'],sha256=meta['sha256'],exact_variant_verified=True,warranty_months=int(props.get('warranty-months') or 6))
  attempts.append(attempt)
  if ref or len(attempts)>=2:break
 return {'key':row['key'],'reference':ref,'attempts':attempts}
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for r in pool.map(verify,scope):
  rows.append(r)
write(WORK/'resale-verified.json',rows)
print('Exact Superb variants verified:',sum(bool(x['reference']) for x in rows),'of',sum(bool(x['attempts']) for x in rows))
