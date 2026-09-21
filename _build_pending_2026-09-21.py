#!/usr/bin/env python3
"""Collect this week's outliers for the find->adversarial-refute verification pass (2026-09-21).
Writes _pending/items.json + _pending/batches.json (batches of 6)."""
import json, os
from datetime import date
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-09-21'
T=date(2026,9,21)
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
         context='Rise REFUSED by the successor-shipped hold: its successor (iPhone 18 Pro / Galaxy S26 FE) went on sale in India 2026-09-18. Grant ONLY on used-resale datapoints dated after 09-18 for this exact variant; a pre-launch figure or Cashify refurb retail does not count. The research resale for the S25 FE 128 was back-solved from a Cashify quote (buyback / 0.80), which is not a resale observation.')
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
# 5) scoped models with no usable research at all (critic dropped the key entirely)
for k in ('redmi_note_14_pro_plus_5g_8_128',):
    e=ph.get(k)
    if e: base(k,e,'missing',db_resale_anchor=e.get('resale_target_a1'))
# 6) CALCIFIED PLACEHOLDER ECHOES: research came back at 76-86% of new — the thin-market convention again.
for k in ref.get('calcified_echo',[]):
    e=ph.get(k)
    if e is None: continue
    base(k,e,'placeholder_resale',db_resale_anchor=e.get('resale_target_a1'),stored_new=e.get('net_new_inr'),
         age_days=age(e.get('launch_date','')),launch=e.get('launch_date'),
         context='Originally priced at EXACTLY 80% of an unverified new price and never researched; this week the research agents returned the same ~80% convention instead of datapoints. Find REAL used datapoints (OLX sold-adjusted, local dealer listings, Cashify refurb as the upper bound). If after a genuine search none exist, say so and give your honest conservative figure.')
# 7) this week's gap-adds whose resale is a flat ratio on a model with a real used market (>90 days)
for k in ('apple_watch_se3_40','apple_watch_se3_44'):
    e=ph.get(k)
    if e: base(k,e,'placeholder_resale',db_resale_anchor=e.get('resale_target_a1'),stored_new=e.get('net_new_inr'),
                age_days=age(e.get('launch_date','')),launch=e.get('launch_date'),
                context='Just added. Apple Watch SE 3 launched in India Sept 2025; resale was set as a flat new x0.60 age-estimate with no listing read. Also confirm the official current India price for this exact size (the 44mm Rs33,900 has never been re-derived; Cashify showed Rs28,900 at launch).')
# 8) carry-forward rechecks
RECHECK={
 'ipad_pro_m5_11_256_wifi':'Research this week put the 11-inch iPad Pro M5 256GB Wi-Fi at resale Rs1,15,000 off an apple.com/in fetch of Rs1,39,900 — ABOVE the 13-inch 256GB sibling (verified resale Rs1,08,000 on 08-30; launch Rs1,29,900), while the same week the 13-inch fetch returned Rs1,99,900, which its critic rejected as a rendering error. Settle the CURRENT official India prices of BOTH sizes (256GB Wi-Fi) and give real used resale for EXACTLY the 11-inch. The 11-inch cannot out-resell the 13-inch.',
 'apple_watch_s12_46':'Just added (on sale 2026-09-18). Its official India price Rs62,900 has never been independently re-derived (Apple buy-flow is JS). The 42mm is Rs56,900; Series 10 was Rs46,900 / Rs49,900 for 42/46mm (+Rs3,000). Confirm the real 46mm GPS price. Resale is a <30-day placeholder (new x0.80) — fine unless you find real listings.',
}
for k,ctx in RECHECK.items():
    e=ph.get(k)
    if e is None or k in seen: continue
    m=e.get('target_margin') or 0.099
    base(k,e,'recheck',db_resale_anchor=e.get('resale_target_a1'),cur_a1=round(e['resale_target_a1']/(1+m)),context=ctx)
# 9) MODELS MISSING FROM THE DB (sibling/series gaps exposed this week) — researched for ADD
NEWMODEL=[
 {'key':'apple_watch_s11_42','name':'Apple Watch Series 11 42mm GPS','tier':'S','launch_date':'2025-09-19',
  'context':'Gap exposed this week: the DB has Series 10 and now Series 12, but no Series 11 (Sept 2025, same event as SE 3 / Ultra 3). Confirm India sale, official India price at launch and today, and real used resale for the 42mm GPS.'},
 {'key':'apple_watch_s11_46','name':'Apple Watch Series 11 46mm GPS','tier':'S','launch_date':'2025-09-19',
  'context':'As above for the 46mm GPS.'},
 {'key':'apple_watch_ultra_3_49','name':'Apple Watch Ultra 3 49mm GPS+Cell','tier':'S','launch_date':'2025-09-19',
  'context':'Gap: DB has Ultra 2 and now Ultra 4, no Ultra 3 (Sept 2025). Confirm India sale, official India price, real used resale.'},
 {'key':'realme_p3_ultra_5g_12_256','name':'Realme P3 Ultra 5G 12/256GB','tier':'B','launch_date':'2025-03-19',
  'context':'Sibling repair: this week the critic found Cashify\'s variant table lists the P3 Ultra India line-up as 8/128 (Rs26,999), 8/256 (Rs27,999), 12/256 (Rs29,999) — the DB holds 8/256 and a suspected phantom 8/512. Confirm 12/256 on realme India and price its real used resale.'},
 {'key':'realme_p3_ultra_5g_8_128','name':'Realme P3 Ultra 5G 8/128GB','tier':'B','launch_date':'2025-03-19',
  'context':'Sibling repair, as above: confirm the 8/128 India SKU and price its real used resale.'},
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
