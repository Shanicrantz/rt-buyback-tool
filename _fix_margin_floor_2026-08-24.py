#!/usr/bin/env python3
"""Enforce the C/D margin FLOOR on entries that predate the rule.

margin_by_age was calibrated only on Shane's high-value override models, so the brain
applies it as-is for S/A/B but uses the tier default as a FLOOR for C/D — otherwise a
cheap phone gets a ~10% risk buffer in absolute rupees that does not cover the risk of
holding it. _apply_brain_weekly.py has always applied that floor; gap-added entries did
not, because _add_gaps.py called margin_for(launch_date) without it. Result: 130 C/D
entries carry margin 0.099 where policy says 0.25/0.30, i.e. RT overpays on each.

This is a pure re-application of the DB's own documented policy — no new research. The
A1 target moves DOWN only; resale_target_a1 is left untouched, since the engine derives
A1 = resale_target_a1/(1+margin) and the anchor itself was never wrong.

--apply writes both files; default is dry-run.
"""
import json, sys

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-24'
APPLY = '--apply' in sys.argv

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
ph = {k: v for k, v in db.items() if k != '_meta'}
TIER = meta['default_margins_by_tier']

fixed = []
for k, e in ph.items():
    t = e.get('tier'); m = e.get('target_margin')
    if t not in ('C', 'D') or not isinstance(m, (int, float)): continue
    floor = TIER[t]
    if m >= floor - 1e-9: continue
    # A1 comes from resale_target_a1 or, for the older discontinued entries, from the refurb
    # anchor. Either way raising the margin lowers A1 by the same ratio, so the anchor field
    # itself is never touched.
    anchor = e.get('resale_target_a1')
    if not anchor:
        r = e.get('refurb_retail_anchor_excellent')
        if not r and e.get('refurb_retail_anchor_fair'):
            r = e['refurb_retail_anchor_fair'] * meta.get('fair_to_excellent_multiplier', 1.18)
        if not r: continue
        anchor = r * e.get('market_factor', meta.get('default_market_factor', 0.88))
    before = anchor / (1 + m)
    after = anchor / (1 + floor)
    e['target_margin'] = floor
    src = e.get('live_source') or ''
    e['live_source'] = (src + f' | margin floored to tier {t} default {floor} on {TODAY}')[:180]
    fixed.append((before - after, k, e.get('display_name'), t, m, floor, round(before), round(after)))

fixed.sort(reverse=True)
print('=' * 78)
print(f'C/D MARGIN FLOOR {TODAY}  ({"APPLY" if APPLY else "dry-run"})')
print('=' * 78)
print(f'entries corrected: {len(fixed)} | total A1 overstatement removed: ₹{sum(f[0] for f in fixed):,.0f}')
for d, k, nm, t, m, fl, a, b in fixed[:20]:
    print(f'  -{d:>7,.0f}  {(nm or k)[:42]:42s} tier={t} m={m} -> {fl}   A1 {a:>7,} -> {b:>7,}')
if len(fixed) > 20: print(f'  ... and {len(fixed)-20} more')

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
print(f'\nAPPLIED: {len(fixed)} margins floored.')
