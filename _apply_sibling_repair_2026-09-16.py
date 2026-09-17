#!/usr/bin/env python3
"""Apply the 2026-09-16 sibling-repair research (_pending/sr_final_*.json, verify + adversarial refute).

Removing a phantom leaves a hole where a REAL variant belongs, so this pass (a) removes the two further
phantoms the outlier refuters exposed — each hand-verified against an India source first — (b) adds the
real configs the removed phantoms were standing in for, and (c) re-prices siblings the refuters flagged
as overpays (resale anchored above Cashify's own warrantied refurb retail) or stale.

Economics identical to the weekly scripts: A1 = resale/(1+margin_by_age), C/D tier floor, capped at
resale x0.92 and new x0.85. Drops apply in full; rises need triangulated medium/high evidence and are
banded at +20%. A round-thousand net_new_inr is the known fabrication signature and is replaced by the
sourced launch price; any other stored new price (Shane's) is kept. --apply writes both files.
"""
import json, glob, sys, re
DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-09-16'
APPLY = '--apply' in sys.argv
def r100(n): return int(round(n / 100.0)) * 100

# Hand-verified 2026-09-17 (Smartprix / motorola.in catalogue / India launch coverage), not on an agent's say-so.
HAND_VERIFIED_PHANTOMS = {
    'moto_edge_60_pro_12_512': 'India Edge 60 Pro = 8/256 Rs29,999, 12/256 Rs33,999, 16/512 Rs37,999 (Smartprix, motorola.in catalogue); 512GB ships only with 16GB.',
    'moto_edge_60_fusion_8_512': 'India Edge 60 Fusion = 8/128, 8/256, 12/256 (motorola.in catalogue; GSMArena/Business Standard launch lists 8/256 + 12/256); no 512GB at any RAM.',
}
FAMILY_TIER = {'oneplus_nord_5': 'B', 'poco_x7_pro_5g': 'B', 'moto_edge_60_pro': 'B', 'moto_edge_60_fusion': 'B'}

db = json.load(open(f'{DIR}/phone_db.json')); meta = db['_meta']
ph = {k: v for k, v in db.items() if k != '_meta'}
MA, TIER_DEF = meta['margin_by_age'], meta['default_margins_by_tier']
def months(ld):
    try: y, mo = map(int, ld.split('-')[:2]); return (2026 - y) * 12 + (9 - mo)
    except Exception: return None
def margin_for(tier, ld):
    a = months(ld); b = '<24mo' if (a is None or a < 24) else '24-36mo' if a < 36 else '36-54mo' if a < 54 else '54mo+'
    m = MA[b]
    if tier in ('C', 'D'): m = max(m, TIER_DEF.get(tier, 0.25))
    return round(m, 3)
def a1_of(e):
    mg = e.get('target_margin'); mg = TIER_DEF.get(e.get('tier'), 0.22) if mg is None else mg
    if e.get('rt_buyback_a1_override'): return e['rt_buyback_a1_override']
    if e.get('resale_target_a1'): return e['resale_target_a1'] / (1 + mg)
    r = e.get('refurb_retail_anchor_excellent')
    if not r and e.get('refurb_retail_anchor_fair'): r = e['refurb_retail_anchor_fair'] * meta.get('fair_to_excellent_multiplier', 1.18)
    if r: return r * e.get('market_factor', meta.get('default_market_factor', 0.88)) / (1 + mg)
    return None
def ceilinged(rs, new, m):
    a1 = min(rs / (1 + m), rs * 0.92)
    if isinstance(new, (int, float)) and new > 0: a1 = min(a1, new * 0.85)
    return a1
def pick_new(stored, sourced):
    if isinstance(stored, (int, float)) and stored > 0 and stored % 1000 != 0: return stored   # Shane's / sourced — keep
    return int(sourced) if isinstance(sourced, (int, float)) and sourced > 0 else stored

log, removed, added = [], [], []
for f in sorted(glob.glob(f'{DIR}/_pending/sr_final_*.json')):
    r = json.load(open(f))
    for it in r['existing_keys']:
        k = it['key']; e = ph.get(k)
        if e is None: log.append(('MISSING-KEY', k, '')); continue
        if it['action'] == 'remove':
            if k in HAND_VERIFIED_PHANTOMS and it['exists_in_india'] == 'no':
                removed.append(k); log.append(('REMOVE', k, HAND_VERIFIED_PHANTOMS[k][:90]))
            else:
                log.append(('HOLD-REMOVE', k, 'not hand-verified — kept'))
            continue
        rs = it.get('resale_inr')
        if not isinstance(rs, (int, float)) or rs <= 0: log.append(('NO-RESALE', k, '')); continue
        cur = a1_of(e); m = margin_for(e.get('tier'), e.get('launch_date', ''))
        new = pick_new(e.get('net_new_inr'), it.get('official_new_inr'))
        a1 = ceilinged(rs, new, m); note = 'repriced'
        strong = it['triangulated'] and it['confidence'] in ('high', 'medium')
        if cur and a1 > cur:
            if not strong: a1, note = cur, 'rise refused (weak evidence) — held'
            elif a1 > cur * 1.20: a1, note = cur * 1.20, 'rise banded +20%'
        a1 = r100(a1)
        e['resale_target_a1'] = r100(a1 * (1 + m)); e['target_margin'] = m
        e['market_resale_observed'] = r100(rs)
        if new: e['net_new_inr'] = int(new)
        e.pop('refurb_retail_anchor_excellent', None) if e.get('refurb_retail_anchor_excellent') else None
        e.pop('buyback_market', None)          # refuters found only 'Get Upto' ceilings, never a real quote
        e['calibration_status'] = 'verified' if strong else 'estimated'; e['calibration_date'] = TODAY
        e['live_source'] = (f"SIBLING-REPAIR {TODAY} (verify+refute, OLX hand-classified): resale ₹{r100(rs):,} -> "
                            f"A1 ₹{a1:,} = resale÷(1+{m}) [{note}] conf={it['confidence']}")[:180]
        log.append(('REPRICE', k, f"A1 {r100(cur) if cur else None} -> {a1:,} [{note}] resale {r100(rs):,}"))
    for mc in r['missing_configs']:
        k = mc['key']
        if not mc.get('add'): log.append(('SKIP-ADD', k, 'add=false (not an India SKU)')); continue
        if k in ph: log.append(('EXISTS', k, '')); continue
        fam = re.sub(r'_\d+_\d+$', '', k); tier = FAMILY_TIER.get(fam)
        if not tier or not isinstance(mc.get('resale_inr'), (int, float)): log.append(('SKIP-ADD', k, 'no tier/resale')); continue
        ld = mc['india_launch_date']; m = margin_for(tier, ld); new = mc.get('official_new_inr'); rs = mc['resale_inr']
        a1 = r100(ceilinged(rs, new, m))
        strong = mc['triangulated'] and mc['confidence'] in ('high', 'medium')
        ph[k] = {'display_name': mc['display_name'], 'tier': tier, 'launch_date': ld, 'discontinued': False,
                 'net_new_inr': int(new) if new else None, 'resale_target_a1': r100(a1 * (1 + m)), 'target_margin': m,
                 'market_resale_observed': r100(rs),
                 'calibration_status': 'verified' if strong else 'estimated', 'calibration_date': TODAY,
                 'live_source': (f"SIBLING-REPAIR {TODAY}: real India config behind a removed phantom. resale ₹{r100(rs):,} "
                                 f"-> A1 ₹{a1:,} = resale÷(1+{m}) conf={mc['confidence']}")[:180]}
        if ph[k]['net_new_inr'] is None: del ph[k]['net_new_inr']
        added.append({'key': k, 'name': mc['display_name'], 'a1': a1})
        log.append(('ADD', k, f"{mc['display_name']} A1 ₹{a1:,} (resale {r100(rs):,}, new {new}, {ph[k]['calibration_status']})"))

for row in log: print(f'  {row[0]:12s} {row[1]:34s} {row[2]}')
if not APPLY: print('\n(dry-run — no files written)'); sys.exit(0)
for k in removed: ph.pop(k, None)
prev = []
try: prev = json.load(open(f'{DIR}/_removed_{TODAY}.json'))
except FileNotFoundError: pass
json.dump(prev + [{'key': k, 'reason': HAND_VERIFIED_PHANTOMS[k]} for k in removed], open(f'{DIR}/_removed_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)
prev = []
try: prev = json.load(open(f'{DIR}/_added_siblings_{TODAY}.json'))
except FileNotFoundError: pass
json.dump(prev + added, open(f'{DIR}/_added_siblings_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)
out = {'_meta': meta}; out.update(ph)
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
lines = open(f'{DIR}/index.html').read().split('\n'); n = 0
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'): lines[i] = ln[:len(ln) - len(ln.lstrip())] + compact; n += 1
assert n == 1, n
open(f'{DIR}/index.html', 'w').write('\n'.join(lines))
print(f'\nAPPLIED: -{len(removed)} phantoms, +{len(added)} real configs. phones={len(ph)}')
