#!/usr/bin/env python3
"""Pick this week's reprice scope: high-value + recent, half fresh-rotation."""
import json, datetime
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
db=json.load(open(f'{DIR}/phone_db.json')); meta=db['_meta']
ph={k:v for k,v in db.items() if k!='_meta'}
TIER_DEF=meta['default_margins_by_tier']
RT_PREMIUM={'S':0.06,'A':0.08,'B':0.10,'C':0.12,'D':0.14}
def cur_a1(e):
    tier=e.get('tier'); margin=e.get('target_margin')
    if margin is None: margin=TIER_DEF.get(tier,0.22)
    if e.get('rt_buyback_a1_override'): return e['rt_buyback_a1_override']
    if e.get('resale_target_a1'): return e['resale_target_a1']/(1+margin)
    if e.get('cashify_exchange'):
        return e['cashify_exchange']*(1+e.get('rt_premium_over_cashify',RT_PREMIUM.get(tier,0.08)))
    r=e.get('refurb_retail_anchor_excellent')
    if not r and e.get('refurb_retail_anchor_fair'): r=e['refurb_retail_anchor_fair']*meta.get('fair_to_excellent_multiplier',1.18)
    if r: return r*e.get('market_factor',meta.get('default_market_factor',0.88))/(1+margin)
    return None
def months(ld):
    try:
        y,mo=map(int,ld.split('-')[:2]); return (2026-y)*12+(8-mo)
    except: return None

cands=[]
for k,e in ph.items():
    if e.get('rt_buyback_a1_override'): continue           # Shane's hand-set rates: never auto-touch
    a1=cur_a1(e)
    if not a1: continue
    age=months(e.get('launch_date',''))
    recent = age is not None and age<=24
    if not (e.get('tier') in ('S','A') or recent): continue
    if e.get('discontinued'): continue
    cands.append({'key':k,'name':e.get('display_name'),'tier':e.get('tier'),'a1':a1,
                  'age':age,'cal':e.get('calibration_date',''),'ld':e.get('launch_date','')})

byval=sorted(cands,key=lambda c:-c['a1'])
TOP=48
top=[c for c in byval[:TOP]]
sel=set(c['key'] for c in top)
# rotation: highest-value candidates NOT refreshed last week, oldest calibration first
rot=[c for c in byval if c['key'] not in sel and c['cal']!='2026-08-10']
rot.sort(key=lambda c:(c['cal'], -c['a1']))
# interleave: take value-weighted stale ones — prefer high value among the stalest
stale=sorted([c for c in rot if c['cal'] in ('2026-06-25','2026-07-06','2026-07-03','2026-07-02','')],
             key=lambda c:-c['a1'])[:32]
sel |= set(c['key'] for c in stale)
recent_new=[c for c in byval if c['key'] not in sel and (c['age'] is not None and c['age']<=9)]
recent_new.sort(key=lambda c:-c['a1'])
extra=recent_new[:16]
sel |= set(c['key'] for c in extra)

chosen=[c for c in byval if c['key'] in sel]
print(f'candidates {len(cands)} -> chosen {len(chosen)}  (top-value {len(top)}, stale-rotation {len(stale)}, recent {len(extra)})')
import collections
print('tiers:',collections.Counter(c['tier'] for c in chosen))
print('cal dates:',collections.Counter(c['cal'] for c in chosen))
keys=[c['key'] for c in chosen]
batches=[keys[i:i+8] for i in range(0,len(keys),8)]
json.dump(batches,open(f'{DIR}/_ov_batches.json','w'),indent=1)
json.dump(chosen,open(f'{DIR}/_scope_2026-08-17.json','w'),indent=1,default=str)
print('batches:',len(batches),'sizes',[len(b) for b in batches])
for c in chosen[:12]: print(f"  {c['a1']:>8,.0f}  {c['tier']}  {c['name'][:44]:44s} cal={c['cal']}")
