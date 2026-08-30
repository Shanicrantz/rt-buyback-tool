#!/usr/bin/env python3
"""Correct net_new_inr values hand-verified against brand primary sources on 2026-08-30.

Found while hand-verifying the phantom removals: several SURVIVING entries carry the
round-number fabrication signature (net_new_inr ending in 000) or a price borrowed from a
different trim. net_new_inr is the new x0.85 ceiling, so a wrong one is a live overpay risk.

Asymmetric by design: when a correction LOWERS the ceiling below the live A1, A1 is pulled
down to it. When a correction RAISES the ceiling, A1 is left exactly where it is — a ceiling
going up is permission to pay more, never a reason to.

--apply writes both files; default is dry-run.
"""
import json, sys

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-30'
APPLY = '--apply' in sys.argv
NEW_CAP = 0.85

def r100(n): return int(round(n / 100.0)) * 100

# key -> (corrected official India new price, source)
FIXES = {
    'oppo_find_x9_12_256':          (74999, 'OPPO India newsroom: Find X9 12/256 Rs74,999, 16/512 Rs84,999'),
    'oppo_reno_13_8_256':           (39999, 'OPPO India newsroom: Reno13 5G 8/128 Rs37,999, 8/256 Rs39,999'),
    'vivo_v50_8_128':               (34999, 'vivo India line-up: 8/128 Rs34,999, 8/256 Rs36,999, 12/512 Rs40,999'),
    'vivo_v50_8_256':               (36999, 'vivo India line-up: 8/256 Rs36,999'),
    'realme_14_pro_plus_5g_8_256':  (31999, 'realme India launch: 8/128 Rs29,999, 8/256 Rs31,999, 12/256 Rs34,999'),
    'iqoo_neo_10_5g_8_256':         (37999, 'iQOO India: Neo 10 8/256 Rs37,999, 12/256 Rs42,999'),
    'iqoo_neo_10_5g_12_256':        (42999, 'iQOO India: Neo 10 12/256 Rs42,999 (DB had no ceiling at all)'),
}
# Deliberately NOT touched: nothing_phone_3a_pro_12_256 (sources split between Rs31,999 and
# Rs34,999 — both above the stored Rs29,999, so every candidate correction would only RAISE
# the ceiling on ambiguous evidence. Left alone; conservative is the safe error.)

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
ph = {k: v for k, v in db.items() if k != '_meta'}
TIER_DEF = meta['default_margins_by_tier']

def margin_of(e):
    m = e.get('target_margin')
    return m if m is not None else TIER_DEF.get(e.get('tier'), 0.22)

def a1_of(e):
    if e.get('rt_buyback_a1_override'): return e['rt_buyback_a1_override']
    if e.get('resale_target_a1'): return e['resale_target_a1'] / (1 + margin_of(e))
    if e.get('cashify_exchange'):
        return e['cashify_exchange'] * (1 + e.get('rt_premium_over_cashify', 0.08))
    r = e.get('refurb_retail_anchor_excellent')
    if not r and e.get('refurb_retail_anchor_fair'):
        r = e['refurb_retail_anchor_fair'] * meta.get('fair_to_excellent_multiplier', 1.18)
    if r: return r * e.get('market_factor', meta.get('default_market_factor', 0.88)) / (1 + margin_of(e))
    return None

rows, pulled = [], []
for key, (new, src) in FIXES.items():
    e = ph.get(key)
    if e is None:
        rows.append((key, None, new, None, None, 'NOT IN DB')); continue
    old = e.get('net_new_inr')
    a1 = a1_of(e)
    ceil = new * NEW_CAP
    action = 'ceiling raised — A1 held' if (old is None or new > old) else 'ceiling lowered'
    new_a1 = a1
    if a1 and a1 > ceil:
        new_a1 = r100(ceil)
        action += f' — A1 pulled to new x{NEW_CAP}'
        pulled.append((key, e.get('display_name'), round(a1), new_a1))
    rows.append((key, old, new, round(a1) if a1 else None,
                 round(new_a1) if new_a1 else None, action))
    if APPLY:
        e['net_new_inr'] = new
        if new_a1 and a1 and new_a1 < a1:
            e['resale_target_a1'] = r100(new_a1 * (1 + margin_of(e)))
            e['live_source'] = (f"CEILING FIX {TODAY}: official new Rs{new:,} ({src}) "
                                f"-> A1 capped at new x0.85 = Rs{new_a1:,}")[:180]
        else:
            e['live_source'] = (f"{e.get('live_source','')} | new price corrected {TODAY}: "
                                f"Rs{new:,} ({src})")[:180]

print('=' * 78)
print(f'NET_NEW_INR CEILING CORRECTIONS {TODAY}  ({"APPLY" if APPLY else "dry-run"})')
print('=' * 78)
for key, old, new, a1, new_a1, action in rows:
    o = f'{old:,}' if isinstance(old, int) else str(old)
    print(f'  {key:32s} new {o:>9s} -> {new:>7,}  A1 {a1 or 0:>7,} -> {new_a1 or 0:>7,}  [{action}]')
print(f'\nA1 pulled down by a corrected ceiling: {len(pulled)}')
for k, nm, before, after in pulled:
    print(f'    {nm}: {before:,} -> {after:,}')

if not APPLY:
    print('\n(dry-run — no files written)')
    sys.exit(0)

out = {'_meta': meta}
out.update(ph)
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
lines = open(f'{DIR}/index.html').read().split('\n')
n = 0
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'):
        lines[i] = ln[:len(ln) - len(ln.lstrip())] + compact; n += 1
assert n == 1, f'expected exactly 1 DB line, patched {n}'
open(f'{DIR}/index.html', 'w').write('\n'.join(lines))
print(f'\nAPPLIED: {len(FIXES)} ceilings corrected, {len(pulled)} A1 values pulled down.')
