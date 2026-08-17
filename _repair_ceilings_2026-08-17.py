#!/usr/bin/env python3
"""v6.1 cleanup: repair pre-existing breaches of the resale ceiling, and withdraw one grant.

(a) Six entries written by LAST week's run carry A1 above market_resale_observed*0.92 —
    they are casualties of the cap-ordering bug fixed today (the -20% week floor was applied
    after the hard caps, so it could land above resale). Today's fix prevents new ones but does
    not retroactively repair those already in the DB. Re-assert the ceiling on them; the normal
    week floor will keep walking them toward the full brain value on later runs.

(b) iPhone 17 Pro Max 1TB was the single iPhone rise granted this week. It now computes ABOVE
    its own 2TB sibling, whose rise was refused for circular evidence. Rather than raise the 2TB
    on evidence we rejected, withdraw the 1TB grant — the iPhone cluster as a whole failed
    verification, so leaving the whole line at last week's capped values is the coherent read.
"""
import json, sys
DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-17'
APPLY = '--apply' in sys.argv
def r100(n): return int(round(n / 100.0)) * 100

db = json.load(open(f'{DIR}/phone_db.json')); meta = db['_meta']
ph = {k: v for k, v in db.items() if k != '_meta'}
def mg(e):
    m = e.get('target_margin')
    return m if m is not None else meta['default_margins_by_tier'].get(e.get('tier'), 0.22)
def a1_of(e):
    if e.get('rt_buyback_a1_override'): return e['rt_buyback_a1_override']
    if e.get('resale_target_a1'): return e['resale_target_a1'] / (1 + mg(e))
    return None

fixed = []
for k, e in ph.items():
    v, ob = a1_of(e), e.get('market_resale_observed')
    if not v or not isinstance(ob, (int, float)) or ob <= 0: continue
    ceil = ob * 0.92
    nn = e.get('net_new_inr')
    if isinstance(nn, (int, float)) and nn > 0: ceil = min(ceil, nn * 0.85)
    if v > ceil + 100:
        new_a1 = r100(ceil)
        e['resale_target_a1'] = r100(new_a1 * (1 + mg(e)))
        e['live_source'] = (f"{(e.get('live_source') or '')[:110]} | CEILING REPAIR {TODAY}: "
                            f"A1 capped to resale x0.92 = ₹{new_a1:,}")[:180]
        fixed.append((k, e.get('display_name'), r100(v), new_a1, ob))

# withdraw the lone iPhone grant that inverted against its 2TB sibling
WITHDRAW = 'iphone_17_pro_max_1tb'
w = ph.get(WITHDRAW); wrow = None
if w:
    prev, m = 117100, mg(w)
    cur = r100(a1_of(w))
    if cur > prev:
        w['resale_target_a1'] = r100(prev * (1 + m))
        w['live_source'] = (f"{TODAY}: hand-verified resale ₹140,000, but the +8.8% grant was WITHDRAWN — "
                            f"it inverted against the 2TB sibling whose rise was refused for circular "
                            f"evidence. Held at the weekly capped A1 ₹{prev:,}.")[:180]
        wrow = (WITHDRAW, cur, prev)

print(f'--- CEILING REPAIRS ({len(fixed)}) ---')
for k, n, b, a, ob in fixed:
    print(f"    {(n or k)[:40]:40s} A1 {b:>8,} -> {a:>8,}  (observed resale {ob:,})")
print(f'\n--- GRANT WITHDRAWN ---\n    {wrow}')
if not APPLY:
    print('\n(dry-run)'); sys.exit(0)

out = {'_meta': meta}; out.update(ph)
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
lines = open(f'{DIR}/index.html').read().split('\n')
n = 0
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'):
        lines[i] = ln[:len(ln) - len(ln.lstrip())] + compact; n += 1
assert n == 1
open(f'{DIR}/index.html', 'w').write('\n'.join(lines))
print(f'\nAPPLIED: {len(fixed)} ceiling repairs, grant withdrawn.')
