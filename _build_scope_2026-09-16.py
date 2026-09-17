#!/usr/bin/env python3
"""Pick this week's reprice scope: carry-forward forced items + high-value + recent + stale rotation."""
import json, collections
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-09-16'
FRESH={'2026-09-10'}          # refreshed 6 days ago — drift is noise, do not re-burn research
# Suspected phantoms go to the existence pass, not to repricing (pricing a phantom is wasted research).
PHANTOM_CHECK={'moto_razr_60_ultra_12_512','redmi_note_14_pro_plus_5g_8_256','google_pixel_9_pro_128'}
# Carry-forward from _phantom_followup_2026-09-10.json: incoherent / hand-set anchors that must be researched.
FORCE={'ipad_pro_m4_11_512_wifi','ipad_pro_m4_13_512_wifi'}
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
        y,mo=map(int,ld.split('-')[:2]); return (2026-y)*12+(9-mo)
    except: return None

cands=[]
for k,e in ph.items():
    if e.get('rt_buyback_a1_override'): continue      # Shane's hand-set rates: never auto-touch
    if k in PHANTOM_CHECK: continue
    a1=cur_a1(e)
    if not a1: continue
    age=months(e.get('launch_date',''))
    recent = age is not None and age<=24
    forced = k in FORCE or (e.get('calibration_status')=='estimated' and e.get('calibration_date') in FRESH)
    if not forced:
        if not (e.get('tier') in ('S','A') or recent): continue
        if e.get('discontinued'): continue
    cands.append({'key':k,'name':e.get('display_name'),'tier':e.get('tier'),'a1':a1,'forced':forced,
                  'age':age,'cal':e.get('calibration_date',''),'ld':e.get('launch_date','')})

byval=sorted(cands,key=lambda c:-c['a1'])
# 0) forced carry-forward: 09-10 placeholder-resale adds (estimated) + incoherent iPad anchors
forced=[c for c in byval if c['forced']]
sel=set(c['key'] for c in forced)
# 1) top value-at-risk, excluding what was refreshed 6 days ago
top=[c for c in byval if c['key'] not in sel and c['cal'] not in FRESH][:36]
sel|=set(c['key'] for c in top)
# 2) stale rotation: highest-value entries carrying the oldest calibration
stale=sorted([c for c in byval if c['key'] not in sel and c['cal'] not in FRESH],
             key=lambda c:(c['cal'], -c['a1']))[:32]
sel|=set(c['key'] for c in stale)
# 3) recent launches (<=9 months) not yet covered
recent_new=sorted([c for c in byval if c['key'] not in sel and c['cal'] not in FRESH
                   and c['age'] is not None and c['age']<=9], key=lambda c:-c['a1'])[:96-len(sel)]
sel|=set(c['key'] for c in recent_new)

chosen=[c for c in byval if c['key'] in sel]
print(f'candidates {len(cands)} -> chosen {len(chosen)}  (forced {len(forced)}, top-value {len(top)}, stale {len(stale)}, recent {len(recent_new)})')
print('tiers:',collections.Counter(c['tier'] for c in chosen))
print('cal dates:',collections.Counter(c['cal'] for c in chosen))
keys=[c['key'] for c in chosen]
batches=[keys[i:i+8] for i in range(0,len(keys),8)]
json.dump(batches,open(f'{DIR}/_ov_batches.json','w'),indent=1)
json.dump(chosen,open(f'{DIR}/_scope_{TODAY}.json','w'),indent=1,default=str)
print('batches:',len(batches),'sizes',[len(b) for b in batches])
for c in chosen: print(f"  {c['a1']:>8,.0f}  {c['tier']}  {(c['name'] or '')[:44]:44s} cal={c['cal']} {'FORCED' if c['forced'] else ''}")
