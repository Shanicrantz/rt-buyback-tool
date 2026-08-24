#!/usr/bin/env python3
"""Apply the round-number-anchor audit (_pending/rp_verified_*.json).

These entries were created by earlier gap audits that recorded estimated, suspiciously
round new prices (new=40,000 / resale=32,000 = exactly 80%) instead of researched ones.
The audit re-sourced each. Rules:
  lower -> always applied (an anchor that is too high makes RT overpay every unit)
  raise -> only with real provenance at medium/high confidence, capped at +20%
  keep/hold -> untouched
net_new_inr is rewritten only when the audit sourced a real India price, because that
figure is the new x 0.85 ceiling and a fake one silently raises what RT will pay.

--apply writes both files; default is dry-run.
"""
import json, glob, sys

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-24'
APPLY = '--apply' in sys.argv
RESALE_CAP, NEW_CAP, RISE_CAP = 0.92, 0.85, 0.20
GOOD_PROV = {'official_brand_india', 'major_retailer', 'marketplace_used', 'press_coverage'}

def r100(n): return int(round(n / 100.0)) * 100

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
ph = {k: v for k, v in db.items() if k != '_meta'}
TIER_DEF = meta['default_margins_by_tier']
MA = meta['margin_by_age']

def margin_of(e):
    m = e.get('target_margin')
    return m if m is not None else TIER_DEF.get(e.get('tier'), 0.22)

def months(ld):
    try:
        y, mo = map(int, ld.split('-')[:2]); return (2026 - y) * 12 + (8 - mo)
    except Exception: return None

def margin_for(e):
    a = months(e.get('launch_date', ''))
    b = '<24mo' if (a is None or a < 24) else '24-36mo' if a < 36 else '36-54mo' if a < 54 else '54mo+'
    m = MA[b]
    if e.get('tier') in ('C', 'D'): m = max(m, TIER_DEF.get(e.get('tier'), 0.25))
    return round(m, 3)

def a1_of(e):
    if e.get('rt_buyback_a1_override'): return e['rt_buyback_a1_override']
    if e.get('resale_target_a1'): return e['resale_target_a1'] / (1 + margin_of(e))
    return None

ver = {}
for f in sorted(glob.glob(f'{DIR}/_pending/rp_verified_*.json')):
    for it in json.load(open(f)).get('items', []):
        ver[it['key']] = it

# Idempotence guard. Batch 12 of the audit landed after the first apply, so this script has to
# run twice. The rise cap is a limit on a SINGLE move — re-computing an already-applied key from
# its new (already-raised) value would stack a second +20% on top of the first. Keys this audit
# has already moved are therefore skipped outright on a re-run.
# Ground truth is the DB, not the outcome file: a dry run overwrites the outcome file, so it
# cannot be trusted to say what was actually written. Every entry this audit has already moved
# carries an "ANCHOR AUDIT <today>" live_source stamp.
already = {k for k, e in ph.items()
           if (e.get('live_source') or '').startswith(f'ANCHOR AUDIT {TODAY}')}

changes, held = [], []
for key, v in ver.items():
    if key in already:
        held.append((key, 'already applied earlier in this run — not re-stacked')); continue
    e = ph.get(key)
    if e is None: held.append((key, 'not in DB')); continue
    act = v.get('action'); rs = v.get('resale_final_inr'); new = v.get('new_final_inr')
    conf = v.get('confidence'); prov = v.get('provenance')
    live = a1_of(e)
    if live is None: held.append((key, 'no computable A1')); continue
    if act in ('keep', 'hold') or not isinstance(rs, (int, float)) or rs <= 0:
        held.append((key, f'{act}: nothing applied')); continue

    m = margin_for(e)
    ceil_new = new if isinstance(new, (int, float)) and new > 0 and prov in GOOD_PROV else e.get('net_new_inr')
    a1 = rs / (1 + m)
    cap = 'margin'
    if a1 > rs * RESALE_CAP: a1, cap = rs * RESALE_CAP, 'resale*0.92'
    if isinstance(ceil_new, (int, float)) and ceil_new > 0 and a1 > ceil_new * NEW_CAP:
        a1, cap = ceil_new * NEW_CAP, 'new*0.85'

    if a1 > live:
        if not (conf in ('high', 'medium') and prov in GOOD_PROV):
            held.append((key, f'raise refused: conf={conf} prov={prov}')); continue
        if a1 > live * (1 + RISE_CAP): a1, cap = live * (1 + RISE_CAP), cap + '+rise-cap'
    a1 = r100(a1)
    if abs(a1 - live) < 100: held.append((key, 'no material change')); continue

    old_new = e.get('net_new_inr')
    e['resale_target_a1'] = r100(a1 * (1 + m))
    e['target_margin'] = m
    e['market_resale_observed'] = r100(rs)
    if isinstance(new, (int, float)) and new > 0 and prov in GOOD_PROV: e['net_new_inr'] = int(new)
    bf = v.get('buyback_final_inr')
    if isinstance(bf, (int, float)) and bf > 0: e['buyback_market'] = r100(bf)
    else: e.pop('buyback_market', None)
    e['calibration_status'] = 'verified' if conf in ('high', 'medium') else 'estimated'
    e['calibration_date'] = TODAY
    e['live_source'] = (f"ANCHOR AUDIT {TODAY} ({act}): resale ₹{r100(rs):,}"
                        f"{f' / new ₹{int(new):,}' if isinstance(new,(int,float)) and new else ''}"
                        f" -> A1 ₹{a1:,} = resale÷(1+{m}) [{cap}] {prov}/{conf}")[:180]
    changes.append({'key': key, 'name': e.get('display_name'), 'action': act,
                    'from': r100(live), 'to': a1, 'resale': r100(rs),
                    'old_new': old_new, 'new': e.get('net_new_inr'), 'cap': cap,
                    'conf': conf, 'prov': prov, 'note': (v.get('note') or '')[:130]})

print('=' * 78)
print(f'ROUND-NUMBER ANCHOR AUDIT {TODAY}  ({"APPLY" if APPLY else "dry-run"})')
print('=' * 78)
print(f'audited: {len(ver)} | changed: {len(changes)} | held: {len(held)}')
tot = sum(c['to'] - c['from'] for c in changes)
print(f'net A1 movement across changed entries: {tot:+,}')
for c in sorted(changes, key=lambda c: c['to'] - c['from']):
    print(f"  {c['to']-c['from']:+8,}  {(c['name'] or '')[:40]:40s} {c['from']:>7,} -> {c['to']:>7,} "
          f"| new {c['old_new']} -> {c['new']} | resale {c['resale']:>7,} [{c['cap']}] {c['prov']}/{c['conf']}")
if held:
    print(f'\n--- HELD ({len(held)}) ---')
    for k, r in held: print(f'  {k}: {r}')

prev_changes = []
try:
    prev_changes = json.load(open(f'{DIR}/_pending/roundprice_outcome_{TODAY}.json')).get('changes', [])
except FileNotFoundError:
    pass
if APPLY:
    json.dump({'today': TODAY, 'changes': prev_changes + changes,
               'held': [{'key': k, 'reason': r} for k, r in held]},
              open(f'{DIR}/_pending/roundprice_outcome_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)

if not APPLY:
    print('\n(dry-run — no files written)'); sys.exit(0)

out = {'_meta': meta}; out.update(ph)
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
lines = open(f'{DIR}/index.html').read().split('\n')
n = 0
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'):
        lines[i] = ln[:len(ln) - len(ln.lstrip())] + compact; n += 1
assert n == 1, f'expected exactly 1 DB line, patched {n}'
open(f'{DIR}/index.html', 'w').write('\n'.join(lines))
print(f'\nAPPLIED: {len(changes)} anchors corrected.')
