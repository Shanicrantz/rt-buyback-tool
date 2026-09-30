#!/usr/bin/env python3
"""Pick this week's reprice scope (2026-09-30): carry-forward forced items + high-value + recent + stale rotation.

Context: v6.7 (09-26) was a full refresh run on request; the 09-28 scheduled run screened 96 entries without the
research fan-out and accepted a single change (Oppo Find X8 Pro 16/512, 'estimated'). Its other 95 entries were
NOT freshly verified, so the 09-21 cohort (now 9 days old) is the natural target this week."""
import json, collections
from datetime import date
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-09-30'
T=date(2026,9,30)
FRESH={'2026-09-26','2026-09-28'}   # researched 2-4 days ago — drift is noise, do not re-burn research
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
def age_days(ld):
    try: return (T-date(*map(int,ld.split('-')))).days
    except: return None

FORCE_REASON={}
# (a) SUCCESSOR HOLD RELEASED. iPhone 18 Pro / Galaxy S26 FE on sale in India since 09-18 (12 days). All ten
#     outgoing-gen entries were last calibrated 09-21 (2TB: 09-16) — the 09-26 run skipped them as fresh — so none
#     has yet been priced on a full post-launch fortnight of observed resale. Rises are allowed again, +8% cap.
for k in ph:
    if k.startswith(('iphone_17_pro_','samsung_s25_fe_')):
        FORCE_REASON[k]='successor hold released: 12 days of post-launch resale'
# (b) CALCIFIED 0.80 anchors, round 3. FRESH does not exempt (lesson 2026-09-26). This week's scan found resale at
#     EXACTLY 80% of new on phones 47-469 days old: the Pixel 11 family (research returned the convention at 45
#     days on 09-26, against round new prices 90,000 / 105,000 / 150,000), Realme 16x (49 d), Moto G Max (47 d,
#     new 28,000 round), Vivo Y400 8/256 (469 d, new 24,000 round).
#     Excluded: redmi_note_15_5g_8_256 (Opus-verified OLX datapoint that lands on 0.80), samsung_s25_ultra_256
#     (0.80 is an artifact of the 09-21 storage-inversion repair), realme_15t_5g_8_256 (verify+refute 09-26 set
#     18,500 from research; 0.804 is a coincidence of that figure).
CALC_EXCLUDE={'redmi_note_15_5g_8_256','samsung_s25_ultra_256','realme_15t_5g_8_256'}
for k,e in ph.items():
    if e.get('rt_buyback_a1_override') or k in CALC_EXCLUDE: continue
    rs=e.get('resale_target_a1'); nn=e.get('net_new_inr'); ad=age_days(e.get('launch_date',''))
    if rs and nn and ad and ad>45 and abs(rs/nn-0.80)<0.01:
        FORCE_REASON[k]='calcified 0.80 placeholder (round 3)'
# The Pixel 11 family shares one research lookup; its siblings sit at 0.80-0.82 of the same round prices.
for k,e in ph.items():
    rs=e.get('resale_target_a1'); nn=e.get('net_new_inr')
    if k.startswith('google_pixel_11') and rs and nn and 0.78<=rs/nn<=0.86:
        FORCE_REASON.setdefault(k,'calcified 0.80 placeholder (round 3)')
# (c) 'estimated' entries that already trade used (>30 d): the Fold8/Flip8 ladder-capped trims, Vivo Y31t, the
#     Oppo A6s repair pair (the 09-28 run could not settle them), the 09-28 Find X8 Pro single-ask estimate.
for k,e in ph.items():
    ad=age_days(e.get('launch_date',''))
    if e.get('calibration_status')=='estimated' and e.get('calibration_date') in FRESH|{'2026-09-21'} and ad and ad>30:
        FORCE_REASON.setdefault(k,'estimated, used market exists')
# (d) 09-28 flag: one merchant shows Z Flip 7 256 at Rs55,000 — possible overvaluation at A1 52,775.
FORCE_REASON.setdefault('samsung_z_flip_7_256','09-28 flag: possible overvaluation')

cands=[]
for k,e in ph.items():
    if e.get('rt_buyback_a1_override'): continue      # Shane's hand-set rates: never auto-touch
    a1=cur_a1(e)
    if not a1: continue
    age=months(e.get('launch_date',''))
    ad=age_days(e.get('launch_date',''))
    if ad is not None and ad<30 and k not in FORCE_REASON: continue   # no used market yet: nothing to research
    recent = age is not None and age<=24
    forced = k in FORCE_REASON
    if not forced:
        if not (e.get('tier') in ('S','A') or recent): continue
        if e.get('discontinued'): continue
    cands.append({'key':k,'name':e.get('display_name'),'tier':e.get('tier'),'a1':a1,'forced':forced,
                  'why':FORCE_REASON.get(k,''),'age':age,'cal':e.get('calibration_date',''),'ld':e.get('launch_date','')})

byval=sorted(cands,key=lambda c:-c['a1'])
forced=[c for c in byval if c['forced']]
sel=set(c['key'] for c in forced)
top=[c for c in byval if c['key'] not in sel and c['cal'] not in FRESH][:26]
sel|=set(c['key'] for c in top)
stale=sorted([c for c in byval if c['key'] not in sel and c['cal'] not in FRESH],
             key=lambda c:(c['cal'], -c['a1']))[:12]
sel|=set(c['key'] for c in stale)
recent_new=sorted([c for c in byval if c['key'] not in sel and c['cal'] not in FRESH
                   and c['age'] is not None and c['age']<=9], key=lambda c:-c['a1'])[:max(0,96-len(sel))]
sel|=set(c['key'] for c in recent_new)

chosen=[c for c in byval if c['key'] in sel]
print(f'candidates {len(cands)} -> chosen {len(chosen)}  (forced {len(forced)}, top-value {len(top)}, stale {len(stale)}, recent {len(recent_new)})')
print('forced reasons:',collections.Counter(c['why'] for c in forced))
print('tiers:',collections.Counter(c['tier'] for c in chosen))
print('cal dates:',collections.Counter(c['cal'] for c in chosen))
keys=[c['key'] for c in chosen]
batches=[keys[i:i+8] for i in range(0,len(keys),8)]
json.dump(batches,open(f'{DIR}/_ov_batches.json','w'),indent=1)
json.dump(chosen,open(f'{DIR}/_scope_{TODAY}.json','w'),indent=1,default=str)
print('batches:',len(batches),'sizes',[len(b) for b in batches])
for c in chosen: print(f"  {c['a1']:>8,.0f}  {c['tier']}  {(c['name'] or '')[:44]:44s} cal={c['cal']} {c['why']}")
