#!/usr/bin/env python3
"""Pick this week's reprice scope: carry-forward forced items + high-value + recent + stale rotation."""
import json, collections
from datetime import date
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-09-21'
T=date(2026,9,21)
FRESH={'2026-09-16'}          # refreshed 5 days ago — drift is noise, do not re-burn research
PHANTOM_CHECK=set()
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

# ---- FORCED carry-forward (2026-09-21) ----
FORCE_REASON={}
# (a) SUCCESSOR SHIPPED 2026-09-18: iPhone 18 Pro / Pro Max are on Indian shelves. The 09-16 run refused
#     all 17 Pro rises and asked the first run after 09-18 to re-anchor the whole line on OBSERVED resale.
for k in ph:
    if k.startswith('iphone_17_pro_'): FORCE_REASON[k]='successor-shipped: re-anchor 17 Pro line on observed resale'
# (b) Galaxy S26 FE shipped 2026-09-18 -> S25 FE is now the outgoing generation.
for k in ph:
    if k.startswith('samsung_s25_fe_'): FORCE_REASON[k]='successor-shipped: S26 FE on sale 09-18'
# (c) iPhone Air ladder is incoherent: 512 resale 83k vs 1TB 115k, and the stored new prices look
#     swapped/fabricated (512 = 174,900, 1TB = round 132,000). Research the exact variants.
for k in ('iphone_air_256','iphone_air_512','iphone_air_1tb'):
    if k in ph: FORCE_REASON[k]='incoherent ladder + suspect net_new_inr'
# (d) last week's 'estimated' entries old enough to have a real used market (>60 days) — sibling repairs
#     and carry-forward triangulations recorded as provisional.
for k,e in ph.items():
    ad=age_days(e.get('launch_date',''))
    if e.get('calibration_status')=='estimated' and e.get('calibration_date') in FRESH and ad and ad>60:
        FORCE_REASON[k]='09-16 estimated, used market exists'
# (e) Pixel 11 family: 40 days old, highest value-at-risk among last week's thin-market holds.
for k in ph:
    if k.startswith('google_pixel_11_') and not k.startswith('google_pixel_11_pro_fold'):
        FORCE_REASON.setdefault(k,'thin-market hold, 40 days old, high value')
# (f) CALCIFIED PLACEHOLDERS (found 2026-09-21): pre-guardrail gap-adds (mostly 2026-08-07) whose resale is
#     EXACTLY 80% of a round new price but which were stamped 'verified'. The 0.80 fallback is only valid
#     for a phone days old; these are 45-900 days old. Re-research from scratch.
for k,e in ph.items():
    if e.get('rt_buyback_a1_override'): continue
    rs=e.get('resale_target_a1'); nn=e.get('net_new_inr'); ad=age_days(e.get('launch_date',''))
    if rs and nn and ad and ad>45 and abs(rs/nn-0.80)<0.01 and (e.get('calibration_date') or '')<='2026-08-10':
        FORCE_REASON.setdefault(k,'calcified 0.80 placeholder (pre-guardrail add)')

cands=[]
for k,e in ph.items():
    if e.get('rt_buyback_a1_override'): continue      # Shane's hand-set rates: never auto-touch
    if k in PHANTOM_CHECK: continue
    a1=cur_a1(e)
    if not a1: continue
    age=months(e.get('launch_date',''))
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
