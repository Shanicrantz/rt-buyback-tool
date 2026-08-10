#!/usr/bin/env python3
"""Add critic-verified missing models to phone_db.json + inlined DB, priced via the BRAIN:
A1 = resale/(1+margin_by_age), capped at new*0.85. Merges finder (launch/tier/name) + critic (prices).
Dedupes vs existing keys + display names. --apply to write; default dry-run."""
import json, glob, re, sys, statistics
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-08-10'
APPLY='--apply' in sys.argv
def r100(n): return int(round(n/100.0))*100
KNOWN={'iphone','apple','samsung','vivo','iqoo','realme','oppo','redmi','xiaomi','poco','oneplus','google',
 'moto','nothing','cmf','honor','asus','infinix','tecno','lava','itel','micromax','nokia','hmd','ipad'}

db=json.load(open(f'{DIR}/phone_db.json'))
MA=db['_meta'].get('margin_by_age', {'<24mo':0.10,'24-36mo':0.19,'36-54mo':0.19,'54mo+':0.30})
existing=set(k for k in db if k!='_meta')
def sig(nm): return re.sub(r'[^a-z0-9]','',nm.lower())
exsig=set(sig(db[k].get('display_name','')) for k in existing)

def months(ld):
    try: y,mo,_=map(int,ld.split('-')); return (2026-y)*12+(8-mo)
    except: return None
def margin_for(ld):
    a=months(ld)
    b='<24mo' if (a is None or a<24) else '24-36mo' if a<36 else '36-54mo' if a<54 else '54mo+'
    return MA[b]

# merge finder (meta) + critic (verified prices) by key
find={}
for f in glob.glob(f'{DIR}/_gaps/find_*.json'):
    for m in json.load(open(f)).get('missing',[]): find[m['key']]=m
ver={}
for f in glob.glob(f'{DIR}/_gaps/verified_*.json'):
    for v in json.load(open(f)).get('verified',[]): ver[v['key']]=v

added=[]; skipped=0; rejected=0
from collections import Counter
bybrand=Counter()
for key,v in ver.items():
    if not v.get('real_india_launch') or v.get('verdict')=='rejected': rejected+=1; continue
    if key in existing: skipped+=1; continue
    f=find.get(key)
    if not f: continue
    if sig(f['display_name']) in exsig: skipped+=1; continue
    brand=key.split('_')[0]
    if brand not in KNOWN: rejected+=1; continue
    resale=v.get('resale_price_final'); new=v.get('new_price_final'); bm=v.get('buyback_market_final')
    if not isinstance(resale,(int,float)) or resale<=0: rejected+=1; continue
    ld=f.get('launch_date',''); m=margin_for(ld)
    a1=resale/(1+m)
    if isinstance(new,(int,float)) and new>0: a1=min(a1, new*0.85)
    a1=r100(a1)
    e={'display_name':f['display_name'],'tier':f['tier'],'launch_date':ld}
    if f.get('discontinued'): e['discontinued']=True
    e['resale_target_a1']=r100(resale); e['target_margin']=m
    if isinstance(new,(int,float)) and new>0: e['net_new_inr']=r100(new)
    if isinstance(bm,(int,float)) and bm>0: e['buyback_market']=r100(bm)
    e['calibration_status']='verified'; e['calibration_date']=TODAY
    e['live_source']=f"Added {TODAY} (gap-audit+critic). resale ₹{r100(resale):,}{'/new ₹'+format(r100(new),',') if new else ''}{'/buy ₹'+format(r100(bm),',') if bm else ''}. A1=resale÷(1+{m})."[:180]
    db[key]=e; existing.add(key); exsig.add(sig(f['display_name']))
    added.append((key,f['display_name'],ld,a1,r100(resale))); bybrand[brand]+=1

# (version + changelog are set once by _finalize_meta.py after both brain-refresh and gap-add)

json.dump([{'key':k,'name':nm,'launch':ld,'a1':a1,'resale':rs} for k,nm,ld,a1,rs in added],
          open(f'{DIR}/_added_{TODAY}.json','w'), ensure_ascii=False, indent=1)
print('=== ADD GAPS ===')
print(f'proposed(verified files): {len(ver)} | ADDED: {len(added)} | skipped dup: {skipped} | rejected: {rejected}')
print('by brand:', dict(bybrand.most_common()))
print('\nNewest added (by launch_date):')
for k,nm,ld,a1,rs in sorted(added,key=lambda x:x[2],reverse=True)[:30]:
    print(f'  {ld}  {nm:42s} A1 ₹{a1:,} (resale {rs})')

if APPLY and added:
    out={'_meta':db['_meta']}; out.update({k:v for k,v in db.items() if k!='_meta'})
    json.dump(out,open(f'{DIR}/phone_db.json','w'),ensure_ascii=False,indent=2)
    c='const DB = '+json.dumps(out,ensure_ascii=False,separators=(',',':'))+';'
    L=open(f'{DIR}/index.html').read().split('\n')
    for i,ln in enumerate(L):
        if ln.lstrip().startswith('const DB = {'): L[i]=ln[:len(ln)-len(ln.lstrip())]+c
    open(f'{DIR}/index.html','w').write('\n'.join(L))
    print(f'\nAPPLIED: +{len(added)} models -> total {len([k for k in out if k!="_meta"])}, v5.8')
elif not APPLY:
    print('\n(dry-run — re-run with --apply to write)')
