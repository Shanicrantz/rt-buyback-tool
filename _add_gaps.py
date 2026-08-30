#!/usr/bin/env python3
"""Add critic-verified missing models to phone_db.json + inlined DB, priced via the BRAIN:
A1 = resale/(1+margin_by_age), capped at new*0.85. Merges finder (launch/tier/name) + critic (prices).
Dedupes vs existing keys + display names. --apply to write; default dry-run."""
import json, glob, re, sys, statistics
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-08-30'
APPLY='--apply' in sys.argv
def r100(n): return int(round(n/100.0))*100
KNOWN={'iphone','apple','samsung','vivo','iqoo','realme','oppo','redmi','xiaomi','poco','oneplus','google',
 'moto','nothing','cmf','honor','asus','infinix','tecno','lava','itel','micromax','nokia','hmd','ipad'}

db=json.load(open(f'{DIR}/phone_db.json'))
MA=db['_meta'].get('margin_by_age', {'<24mo':0.10,'24-36mo':0.19,'36-54mo':0.19,'54mo+':0.30})
TIER_DEF=db['_meta'].get('default_margins_by_tier', {'S':0.18,'A':0.20,'B':0.22,'C':0.25,'D':0.30})
existing=set(k for k in db if k!='_meta')
def sig(nm): return re.sub(r'[^a-z0-9]','',nm.lower())
exsig=set(sig(db[k].get('display_name','')) for k in existing)

def months(ld):
    try: y,mo,_=map(int,ld.split('-')); return (2026-y)*12+(8-mo)
    except: return None
def margin_for(ld, tier=None):
    # margin_by_age was calibrated on high-value models only, so the tier default is a FLOOR
    # for C/D — without it a cheap phone carries a ~10% buffer that does not cover the risk of
    # holding it. Omitting this here is what left 130 gap-added C/D entries under-margined
    # (found and repaired 2026-08-24); every other script in the pipeline applies the floor.
    a=months(ld)
    b='<24mo' if (a is None or a<24) else '24-36mo' if a<36 else '36-54mo' if a<54 else '54mo+'
    m=MA[b]
    if tier in ('C','D'): m=max(m, TIER_DEF.get(tier, 0.25))
    return round(m,3)

# merge finder (meta) + critic (verified prices) by key
find={}
for f in glob.glob(f'{DIR}/_gaps/find_*.json'):
    for m in json.load(open(f)).get('missing',[]): find[m['key']]=m
ver={}
for f in glob.glob(f'{DIR}/_gaps/verified_*.json'):
    for v in json.load(open(f)).get('verified',[]): ver[v['key']]=v

# Tier drift guardrail (2026-08-24): the finder's tier wanders vs what the DB already uses
# for the same series (iQOO Z11 got B against 14/14 existing C entries). Tier sets the C/D
# margin FLOOR, so drift silently changes margins. Normalise a new entry's tier to the
# majority tier of its series when the series has >=3 existing entries.
def series_sig(k):
    toks=k.split('_')
    while len(toks)>2 and re.fullmatch(r'\d+|1tb|2tb',toks[-1]): toks.pop()
    return re.sub(r'\d+','',('_'.join(toks)))
from collections import Counter
series_tiers={}
for k in existing:
    t=db[k].get('tier')
    if t: series_tiers.setdefault(series_sig(k),Counter())[t]+=1

added=[]; skipped=0; rejected=0; tier_fixed=[]
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
    tc=series_tiers.get(series_sig(key))
    if tc and sum(tc.values())>=3:
        maj,cnt=tc.most_common(1)[0]
        if cnt/sum(tc.values())>=0.7 and f.get('tier')!=maj:
            tier_fixed.append((key,f.get('tier'),maj,dict(tc))); f['tier']=maj
    ld=f.get('launch_date',''); m=margin_for(ld, f.get('tier'))
    a1=resale/(1+m)
    if isinstance(new,(int,float)) and new>0: a1=min(a1, new*0.85)
    a1=r100(a1)
    e={'display_name':f['display_name'],'tier':f['tier'],'launch_date':ld}
    if f.get('discontinued'): e['discontinued']=True
    e['resale_target_a1']=r100(resale); e['target_margin']=m
    if isinstance(new,(int,float)) and new>0: e['net_new_inr']=int(new)
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
if tier_fixed:
    print('\nTier normalised to series majority:')
    for k,frm,to,tc in tier_fixed: print(f'  {k}: {frm} -> {to}  (series has {tc})')
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
