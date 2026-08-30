#!/usr/bin/env python3
"""Collect this week's outliers for the find->adversarial-refute verification pass:
capped rises, big drops, existence claims, missing resale, and round-price gap-adds.
Writes _pending/items.json + _pending/batches.json (batches of 5)."""
import json, os
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-08-30'
db=json.load(open(f'{DIR}/phone_db.json'))
ph={k:v for k,v in db.items() if k!='_meta'}
ref=json.load(open(f'{DIR}/_brain_refresh_{TODAY}.json'))

items=[]; seen=set()
def base(k,e,kind,**kw):
    if k in seen: return
    seen.add(k)
    it={'key':k,'kind':kind,'name':e.get('display_name'),'tier':e.get('tier'),
        'launch_date':e.get('launch_date'),'net_new_inr':e.get('net_new_inr')}
    it.update(kw); items.append(it)

# 1) rises the +8% cap blocked
for b in ref.get('blocked_rises',[]):
    e=ph.get(b['key'])
    if e is None: continue
    base(b['key'],e,'rise',db_resale_anchor=e.get('resale_target_a1'),cur_a1=b['cur'],
         wanted_a1=b['wanted'],granted_a1=b['granted'],pct_wanted=round(b['pct_wanted']),
         research_resale=b.get('resale'),research_buyback=b.get('buyback'),research_conf=b.get('conf'))

# 2) big drops (>=12% down, or floored by the week cap)
for c in ref.get('changes',[]):
    if c['pct']<=-12 or 'week-cap-down' in c.get('capped_by',''):
        e=ph.get(c['key'])
        if e is None: continue
        base(c['key'],e,'drop',db_resale_anchor=e.get('resale_target_a1'),cur_a1=c['cur'],
             new_a1=c['new_a1'],pct=round(c['pct']),research_resale=c.get('resale'),
             research_buyback=c.get('buyback'),research_conf=c.get('conf'),capped_by=c.get('capped_by'))

# 3) unresolved non-existence claims
for k,nm,note in ref.get('nonexistent',[]):
    e=ph.get(k)
    if e is None: continue
    base(k,e,'existence',cur_a1=None,claim=note[:140])

# 4) scoped models where research found no resale at all
for k,reason in ref.get('skipped',[]):
    if reason=='no verified resale':
        e=ph.get(k)
        if e is None: continue
        base(k,e,'missing',db_resale_anchor=e.get('resale_target_a1'))

# 5) round-price fabrication signature on this week's gap-adds
added_f=f'{DIR}/_added_{TODAY}.json'
if os.path.exists(added_f):
    for a in json.load(open(added_f)):
        e=ph.get(a['key'])
        if e is None: continue
        nn=e.get('net_new_inr')
        if isinstance(nn,(int,float)) and nn>0 and nn%1000==0:
            base(a['key'],e,'roundprice',db_resale_anchor=e.get('resale_target_a1'),
                 stored_new=nn,stored_resale=e.get('resale_target_a1'))

from collections import Counter
print(f'pending items: {len(items)}', dict(Counter(i["kind"] for i in items)))
batches=[items[i:i+5] for i in range(0,len(items),5)]
os.makedirs(f'{DIR}/_pending',exist_ok=True)
json.dump(items,open(f'{DIR}/_pending/items.json','w'),ensure_ascii=False,indent=1)
json.dump(batches,open(f'{DIR}/_pending/batches.json','w'),ensure_ascii=False,indent=1)
print(f'batches: {len(batches)} sizes {[len(b) for b in batches]}')
for i in items: print(f"  [{i['kind']:10s}] {i['key']}")
