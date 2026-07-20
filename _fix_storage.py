#!/usr/bin/env python3
"""Fix storage-variant overpay anomalies: remove phantom variants, and re-derive
stale (no_live_data) higher-storage variants from their live lower sibling + modest
storage premium. Live variants (with valid ceilings) are trusted and untouched.
Writes both phone_db.json and the inlined DB in index.html."""
import json
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-06-25'
DEFAULT_MARGIN={'S':0.18,'A':0.2,'B':0.22,'C':0.25,'D':0.3}; RT_PREM={'S':0.08,'A':0.10,'B':0.12,'C':0.14,'D':0.16}
def round100(n): return int(round(n/100.0))*100
def a1(e):
    t=e['tier']; m=e.get('target_margin',DEFAULT_MARGIN[t])
    if 'rt_buyback_a1_override' in e: return round100(e['rt_buyback_a1_override'])
    if 'cashify_exchange' in e: return round100(e['cashify_exchange']*(1+e.get('rt_premium_over_cashify',RT_PREM.get(t,.08))))
    if 'resale_target_a1' in e: return round100(e['resale_target_a1']/(1+m))
    if 'refurb_retail_anchor_excellent' in e: return round100(e['refurb_retail_anchor_excellent']*e.get('market_factor',0.88)/(1+m))
    return 0
def set_a1(e,target):
    """Set the entry's primary anchor field so engine A1 == target. Returns field name or None (override)."""
    t=e['tier']; m=e.get('target_margin',DEFAULT_MARGIN[t]); mf=e.get('market_factor',0.88)
    if 'rt_buyback_a1_override' in e:
        e['rt_buyback_a1_override']=round100(target); return 'rt_buyback_a1_override'
    if 'cashify_exchange' in e:
        p=e.get('rt_premium_over_cashify',RT_PREM.get(t,.08)); e['cashify_exchange']=round100(target/(1+p)); return 'cashify_exchange'
    if 'resale_target_a1' in e:
        e['resale_target_a1']=round100(target*(1+m)); return 'resale_target_a1'
    if 'refurb_retail_anchor_excellent' in e:
        e['refurb_retail_anchor_excellent']=round100(target*(1+m)/mf); return 'refurb_retail_anchor_excellent'
    return None
def srank(k): return {'32':32,'64':64,'128':128,'256':256,'512':512,'1tb':1024,'2tb':2048}.get(k.split('_')[-1].lower(),0)
def base(k): return '_'.join(k.split('_')[:-1])

d=json.load(open(f'{DIR}/phone_db.json'))
audit=json.load(open(f'{DIR}/_rate_refresh_audit_2026-06-25.json'))['updates']

# 1) remove confirmed phantom variants (non-existent storage tiers)
PHANTOM=['iphone_11_512','iphone_12_pro_1tb','iphone_12_pro_max_1tb']
removed=[]
for k in PHANTOM:
    if k in d:
        removed.append((k,d[k].get('display_name'),a1(d[k]))); del d[k]

def is_live(k):
    return audit.get(k,{}).get('status')=='live'

from collections import defaultdict
groups=defaultdict(list)
for k in d:
    if k!='_meta': groups[base(k)].append(k)

TIER=1.08   # clean per-storage-tier premium for derived variants
fixed=[]
for g,ks in groups.items():
    var=sorted([k for k in ks if srank(k)>0], key=srank)
    if len(var)<2: continue
    prev=None
    for k in var:
        cur=a1(d[k]); e=d[k]
        if prev is None: prev=cur; continue
        target=None
        if cur>prev*1.15 and not is_live(k):        # excess premium on a stale variant -> overpay
            target=round100(prev*TIER)
        elif cur<prev*0.97 and not is_live(k):      # inversion on a stale variant
            target=round100(prev*1.05)
        if target and target!=cur:
            old_a1=cur; fld=set_a1(e,target); newa=a1(e)
            e['calibration_date']=TODAY
            e['live_source']=f'derived from {srank(prev) if False else "lower-storage sibling"} +{int((TIER-1)*100)}% storage premium (no live data for this variant)'
            if e.get('calibration_status')=='verified': e['calibration_status']='estimated'
            fixed.append((k,old_a1,newa,fld)); cur=newa
        prev=cur

# write phone_db.json
with open(f'{DIR}/phone_db.json','w') as fh:
    json.dump(d,fh,ensure_ascii=False,indent=2)
# write inlined DB in index.html
compact='const DB = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';'
lines=open(f'{DIR}/index.html').read().split('\n')
rep=0
for i,ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'):
        lines[i]=ln[:len(ln)-len(ln.lstrip())]+compact; rep+=1
open(f'{DIR}/index.html','w').write('\n'.join(lines))

print('=== STORAGE FIX ===')
print('Phantom variants removed:',len(removed))
for k,nm,v in removed: print(f'  - {k} ({nm})  was A1 ₹{v}')
print(f'\nStale variants re-priced (no overpay): {len(fixed)}')
for k,o,n,fld in sorted(fixed,key=lambda x:-(x[1]-x[2])):
    print(f'  {k:34s} A1 ₹{o:<6d} -> ₹{n:<6d}  [{fld}]')
print(f'\nindex.html DB replaced: {rep} | total phones now: {len([k for k in d if k!="_meta"])}')
