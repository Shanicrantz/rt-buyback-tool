#!/usr/bin/env python3
"""Collect this week's outliers for the find->adversarial-refute verification pass (2026-09-30).
Writes _pending/items.json + _pending/batches.json (batches of 6)."""
import json, os
from datetime import date
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-09-30'
T=date(2026,9,30)
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
    ctx=None
    if b['key'].startswith(('iphone_17_pro_','samsung_s25_fe_')):
        ctx=('Outgoing generation: iPhone 18 Pro / Galaxy S26 FE on sale in India since 2026-09-18 (12 days). The '
             'successor hold was released this week, so this rise reached verification for the first time. On 09-16/'
             '09-21/09-26 every rise research wanted here was refused on verification. Grant ONLY on exact-variant '
             'datapoints dated AFTER 09-18, discounted from asking to sold.')
    base(b['key'],e,'rise',db_resale_anchor=e.get('resale_target_a1'),cur_a1=b['cur'],
         wanted_a1=b['wanted'],granted_a1=b['granted'],pct_wanted=round(b['pct_wanted']),
         research_resale=b.get('resale'),research_buyback=b.get('buyback'),research_conf=b.get('conf'),
         **({'context':ctx} if ctx else {}))
# 2) rises refused by a successor-shipped hold (none this week — hold released 2026-09-30)
for b in ref.get('successor_refused',[]):
    e=ph.get(b['key'])
    if e is None: continue
    base(b['key'],e,'rise',db_resale_anchor=e.get('resale_target_a1'),cur_a1=b['cur'],wanted_a1=b['wanted'],
         granted_a1=b['cur'],pct_wanted=round((b['wanted']-b['cur'])/b['cur']*100),research_resale=b.get('resale'),
         research_buyback=b.get('buyback'),research_conf=b.get('conf'))
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
    if e is None: continue
    base(k,e,'existence',cur_a1=None,claim=note[:300])
# 5) scoped models with no usable research at all
for k,why in ref.get('skipped',[]):
    e=ph.get(k)
    if e is None or 'no verified resale' not in why: continue
    base(k,e,'missing',db_resale_anchor=e.get('resale_target_a1'),
         cur_a1=round(e['resale_target_a1']/(1+e['target_margin'])) if e.get('resale_target_a1') and e.get('target_margin') else None)
# 6) CALCIFIED PLACEHOLDER ECHOES: research came back at 76-86% of new — the thin-market convention again.
for k in ref.get('calcified_echo',[]):
    e=ph.get(k)
    if e is None: continue
    base(k,e,'placeholder_resale',db_resale_anchor=e.get('resale_target_a1'),stored_new=e.get('net_new_inr'),
         age_days=age(e.get('launch_date','')),launch=e.get('launch_date'),
         context='Priced at EXACTLY 80% of a (often round-number, unverified) new price; this week research again returned ~80% instead of datapoints. Find REAL used datapoints (OLX sold-adjusted, local dealer listings, Cashify refurb as the upper bound) and the OFFICIAL India new price per storage. If after a genuine search none exist, say so and give your honest conservative figure.')
# 7) PHANTOM-VARIANT SUSPECTS carried forward from the 2026-09-28 run. Each has the DB's #1 bug signature: a storage
#    tier paired with the wrong RAM while the real config is missing. Removal and repair are one operation, so each
#    suspect goes in as kind=existence and the config it probably stands in for as kind=newmodel.
SUSPECTS={
 'oneplus_15_12_512':('India listings and buyback selectors show 12/256 and 16/512 for the OnePlus 15; no 12/512 seen (2026-09-28). '
                      'The DB has no 16/512 entry at all — the classic phantom: big storage paired with the wrong RAM.'),
 'poco_m7_pro_5g_8_128':('Poco M7 Pro 5G India line-up needs confirming: the DB has 8/128 + 8/256 but no 6/128. If India sold 6/128 + '
                         '8/256 only, the 8/128 is a phantom standing in for the real 6/128.'),
 'realme_c75_5g_4_256':('Realme C75 5G India line-up needs confirming: the DB has 4/128, 4/256, 6/128 but no 4/64. A 256GB tier on the '
                        '4GB (lowest) RAM is the phantom signature.'),
 'redmi_note_15_se_5g_8_128':('Redmi Note 15 SE 5G India line-up needs confirming for the 8/128 (DB has 6/128, 8/128, 8/256). The 6/128 was '
                              'added on Shane\'s own flag 2026-07-06; the 8/128 was never sourced.'),
}
for k,ctx in SUSPECTS.items():
    e=ph.get(k)
    if e: base(k,e,'existence',cur_a1=round(e['resale_target_a1']/(1+e['target_margin'])) if e.get('resale_target_a1') else None,
               claim=ctx,context=ctx+' Settle it on the brand\'s own India store/newsroom or India launch coverage listing every '
               'India config. Absence from Cashify/OLX is NOT evidence.')
NEWMODEL=[
 {'key':'oneplus_15_16_512','name':'OnePlus 15 16/512GB','tier':'A','launch_date':'2025-11-13',
  'context':'Probable real India top config of the OnePlus 15 (the DB has 12/256 + a suspect 12/512). Confirm it sold in India, its official India price, and real mint-used resale from datapoints.'},
 {'key':'poco_m7_pro_5g_6_128','name':'Poco M7 Pro 5G 6/128GB','tier':'C','launch_date':'2024-12-17',
  'context':'Probable real India base config of the Poco M7 Pro 5G (missing from the DB; DB carries a suspect 8/128). Confirm and price real used resale.'},
 {'key':'realme_c75_5g_4_64','name':'Realme C75 5G 4/64GB','tier':'D','launch_date':'2025-05-02',
  'context':'Probable real India base config of the Realme C75 5G (missing from the DB; DB carries a suspect 4/256). Confirm India launch date, price and real used resale.'},
]
for nm in NEWMODEL:
    if nm['key'] in ph or nm['key'] in seen: continue
    seen.add(nm['key'])
    items.append({'key':nm['key'],'kind':'newmodel','name':nm['name'],'tier':nm['tier'],'launch_date':nm['launch_date'],
                  'net_new_inr':None,'placeholder_anchor':True,'context':nm['context']})
# 8) this week's gap-adds priced on the 0.80 placeholder although they are >30 days old (i.e. they trade used)
try:
    added=json.load(open(f'{DIR}/_added_{TODAY}.json'))
except FileNotFoundError:
    added=[]
for a in added:
    e=ph.get(a['key'])
    if not e: continue
    nn=e.get('net_new_inr'); rs=e.get('resale_target_a1'); ad=age(e.get('launch_date',''))
    if nn and rs and ad is not None and ad>30 and 0.76<=rs/nn<=0.865:
        base(a['key'],e,'placeholder_resale',db_resale_anchor=rs,stored_new=nn,age_days=ad,launch=e.get('launch_date'),
             context='Just gap-added with resale at ~80% of new although it has been on sale >30 days. Research the real used resale.')

from collections import Counter
print(f'pending items: {len(items)}', dict(Counter(i["kind"] for i in items)))
batches=[items[i:i+6] for i in range(0,len(items),6)]
os.makedirs(f'{DIR}/_pending',exist_ok=True)
json.dump(items,open(f'{DIR}/_pending/items.json','w'),ensure_ascii=False,indent=1)
json.dump(batches,open(f'{DIR}/_pending/batches.json','w'),ensure_ascii=False,indent=1)
print(f'batches: {len(batches)} sizes {[len(b) for b in batches]}')
for i in items: print(f"  [{i['kind']:18s}] {i['key']}")
