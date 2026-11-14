import sys,json,gzip,hashlib,re,collections
from pathlib import Path
sys.path.insert(0,'/Users/shane/Documents/Claude/Projects/rt buyback tool')
import _market_refresh_runner as m
W=Path(__file__).resolve().parent
read=lambda n:json.loads((W/n).read_text())
rows=read('resale-verified.json');scope={r['key']:r for r in read('scope.json')['models']};products=[]
for family in read('resale-results.json'):
 for f in family['attempts']:
  if f.get('http_status')!=200:continue
  raw=gzip.decompress((W/'research'/f['snapshot']).read_bytes());assert hashlib.sha256(raw).hexdigest()==f['sha256']
  ps=[p for p in m.ld(raw.decode()) if p.get('@type')=='Product']
  if len(ps)!=1:continue
  p=ps[0];props={a.get('propertyID'):a.get('value') for a in p.get('additionalProperty',[])}
  ram,storage=m.ram_storage(props.get('storage',''));of=p.get('offers',{})
  if props.get('refurbishment-grade')!='Superb' or of.get('priceCurrency')!='INR' or not of.get('availability','').endswith('/InStock') or not of.get('itemCondition','').endswith('/RefurbishedCondition'):continue
  products.append((p,props,ram,storage,of,f))
added=[]
for r in rows:
 row=scope[r['key']]
 if row['category']!='phone':continue
 for p,props,ram,storage,of,f in products:
  if not m.family_match(m.norm(row['family']),m.norm(p['name'].split(' - Refurbished')[0])) or storage!=row['storage'] or row['ram'] is not None and ram!=row['ram']:continue
  ref=dict(family=row['family'],ram=ram,storage=storage,amount_inr=float(of['price']),grade='Superb',title=p['name'],source_url=f['final_url'],selected_offer_url=of.get('url'),family_source_url=f['final_url'],observed_at=f['observed_at'],evidence_file=f['snapshot'],sha256=f['sha256'],kind='refurb_retail_asking',available=True,exact_variant_verified=True,warranty_months=int(props.get('warranty-months') or 6),verification_method='Public page selected Product, exact storage/RAM/grade/stock; not ProductGroup sibling inference')
  if not r['reference'] or ref['amount_inr']<r['reference']['amount_inr']:
   r['reference']=ref;added.append(r['key'])
   r['attempts'].append(dict(fetch=f,accepted=True,title=p['name'],properties=props,offer=of,method=ref['verification_method']))
m.write(W/'resale-verified-before-family.json',read('resale-verified.json'))
m.write(W/'resale-verified.json',rows)
print(json.dumps(dict(verified=sum(bool(r['reference']) for r in rows),selected_product_fallback=added)))
