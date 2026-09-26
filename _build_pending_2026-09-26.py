#!/usr/bin/env python3
"""Collect this week's outliers for the find->adversarial-refute verification pass (2026-09-26).
Writes _pending/items.json + _pending/batches.json (batches of 6)."""
import json, os
from datetime import date
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-09-26'
T=date(2026,9,26)
db=json.load(open(f'{DIR}/phone_db.json'))
ph={k:v for k,v in db.items() if k!='_meta'}
ref=json.load(open(f'{DIR}/_brain_refresh_{TODAY}.json'))
start=json.load(open(f'{DIR}/phone_db.backup-{TODAY}.json'))
CALCIFIED={c['key'] for c in json.load(open(f'{DIR}/_scope_{TODAY}.json')) if 'calcified' in (c.get('why') or '')}
def age(ld):
    try: return (T-date(*map(int,ld.split('-')))).days
    except Exception: return None

items=[]; seen=set()
def base(k,e,kind,**kw):
    if k in seen: return
    seen.add(k)
    it={'key':k,'kind':kind,'name':e.get('display_name'),'tier':e.get('tier'),
        'launch_date':e.get('launch_date'),'net_new_inr':e.get('net_new_inr'),
        'placeholder_anchor':((start.get(k) or {}).get('calibration_status')=='estimated') or k in CALCIFIED}
    it.update(kw); items.append(it)

# 1) rises the +8% cap blocked
for b in ref.get('blocked_rises',[]):
    e=ph.get(b['key'])
    if e is None: continue
    base(b['key'],e,'rise',db_resale_anchor=e.get('resale_target_a1'),cur_a1=b['cur'],
         wanted_a1=b['wanted'],granted_a1=b['granted'],pct_wanted=round(b['pct_wanted']),
         research_resale=b.get('resale'),research_buyback=b.get('buyback'),research_conf=b.get('conf'))
# 2) rises refused by the successor-shipped hold (S25 FE, iPhone 17 Pro Max 2TB) — a live "Cashify pays more"
#    alarm sits on the S25 FE 128, so settle them on post-09-18 evidence instead of carrying the hold blind.
for b in ref.get('successor_refused',[]):
    e=ph.get(b['key'])
    if e is None: continue
    base(b['key'],e,'rise',db_resale_anchor=e.get('resale_target_a1'),cur_a1=b['cur'],wanted_a1=b['wanted'],
         granted_a1=b['cur'],pct_wanted=round((b['wanted']-b['cur'])/b['cur']*100),research_resale=b.get('resale'),
         research_buyback=b.get('buyback'),research_conf=b.get('conf'),
         context='Rise REFUSED by the successor-shipped hold (iPhone 18 Pro Max on sale in India since 2026-09-18). Last week verification refused a rise here on two Mumbai ASKS. This week research cites 7 exact-2TB OLX asks (Rs1,59,950-1,79,000, Sep 12-19, straddling the launch). Grant ONLY on post-09-18 exact-variant datapoints discounted to sold.')
# 3) big drops (>=12% down, or floored by the week cap)
for c in ref.get('changes',[]):
    if c['pct']<=-12 or 'week-cap-down' in c.get('capped_by',''):
        e=ph.get(c['key'])
        if e is None: continue
        base(c['key'],e,'drop',db_resale_anchor=e.get('resale_target_a1'),cur_a1=c['cur'],
             new_a1=c['new_a1'],pct=round(c['pct']),research_resale=c.get('resale'),
             research_buyback=c.get('buyback'),research_conf=c.get('conf'),capped_by=c.get('capped_by'))
# 4) unresolved non-existence claims
for k,nm,note in ref.get('nonexistent',[]):
    e=ph.get(k)
    if e is None or k=='vivo_y31t_5g_6_256': continue   # critic quoted 'does not exist' while CONFIRMING it real (added + verified 2026-09-21)
    base(k,e,'existence',cur_a1=None,claim=note[:300])
# 5) scoped models with no usable research at all (critic dropped the key entirely)

# 6) CALCIFIED PLACEHOLDER ECHOES: research came back at 76-86% of new — the thin-market convention again.
for k in ref.get('calcified_echo',[]):
    e=ph.get(k)
    if e is None: continue
    base(k,e,'placeholder_resale',db_resale_anchor=e.get('resale_target_a1'),stored_new=e.get('net_new_inr'),
         age_days=age(e.get('launch_date','')),launch=e.get('launch_date'),
         context='Originally priced at EXACTLY 80% of an unverified new price and never researched; this week the research agents returned the same ~80% convention instead of datapoints. Find REAL used datapoints (OLX sold-adjusted, local dealer listings, Cashify refurb as the upper bound). If after a genuine search none exist, say so and give your honest conservative figure.')
# 7) this week's gap-add whose critic put resale ABOVE Cashify's refurb ceiling (capped on add)
for k in ('nothing_phone_3a_lite_8_128','nothing_phone_3a_lite_8_256'):
    e=ph.get(k)
    if e: base(k,e,'recheck',db_resale_anchor=e.get('resale_target_a1'),cur_a1=round(e['resale_target_a1']/(1+e['target_margin'])),
                context='Just added (India launch 2025-11-27 at Rs20,999/22,999, hiked since). The gap-audit critic set mint resale ABOVE Cashify\'s own warrantied refurb Fair price (Rs17,899 / Rs18,999), which the pricing method forbids for a 10-month-old phone; the add was capped at that ceiling. Find real local resale for this exact variant (OLX sold-adjusted, ORUphones, dealers).')
# 8) sibling repair behind the Oppo A6s phantoms
NEWMODEL=[
 {'key':'oppo_a6s_5g_4_128','name':'Oppo A6s 5G 4/128GB','tier':'C','launch_date':'2026-03-18',
  'context':'Real India config behind two phantom 8GB entries. OPPO India newsroom: A6s 5G launched 2026-03-18 at 4GB+128GB Rs18,999 (6GB+128GB Rs20,999). Confirm, and price its real used resale (~6 months old).'},
 {'key':'oppo_a6s_5g_6_128','name':'Oppo A6s 5G 6/128GB','tier':'C','launch_date':'2026-03-18',
  'context':'As above for the 6GB+128GB (Rs20,999 at launch).'},
]
for nm in NEWMODEL:
    if nm['key'] in ph or nm['key'] in seen: continue
    seen.add(nm['key'])
    items.append({'key':nm['key'],'kind':'newmodel','name':nm['name'],'tier':nm['tier'],'launch_date':nm['launch_date'],
                  'net_new_inr':None,'placeholder_anchor':True,'context':nm['context']})

from collections import Counter
print(f'pending items: {len(items)}', dict(Counter(i["kind"] for i in items)))
batches=[items[i:i+6] for i in range(0,len(items),6)]
os.makedirs(f'{DIR}/_pending',exist_ok=True)
json.dump(items,open(f'{DIR}/_pending/items.json','w'),ensure_ascii=False,indent=1)
json.dump(batches,open(f'{DIR}/_pending/batches.json','w'),ensure_ascii=False,indent=1)
print(f'batches: {len(batches)} sizes {[len(b) for b in batches]}')
for i in items: print(f"  [{i['kind']:18s}] {i['key']}")
