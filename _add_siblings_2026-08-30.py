#!/usr/bin/env python3
"""Add the REAL storage variants that this week's removed phantoms were standing in for.

Reads _gaps/repair_verified_*.json (research + adversarial refute). Only 'add' verdicts with
confirmed India existence are inserted. Priced with the brain exactly like any other entry:
    A1 = resale / (1 + margin_by_age)   capped at resale*0.92 and new*0.85
with the tier and margin inherited from the surviving siblings in the same family, so one
phone cannot end up with two different margins across its storage variants.

--apply writes both files; default is dry-run.
"""
import json, glob, re, sys
from collections import Counter

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-30'
APPLY = '--apply' in sys.argv
RESALE_CAP, NEW_CAP = 0.92, 0.85

def r100(n): return int(round(n / 100.0)) * 100

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
MA = meta['margin_by_age']
TIER_DEF = meta['default_margins_by_tier']
existing = set(k for k in db if k != '_meta')

def months(ld):
    try:
        y, mo = map(int, ld.split('-')[:2]); return (2026 - y) * 12 + (8 - mo)
    except Exception:
        return None

def margin_for(ld, tier):
    a = months(ld)
    b = '<24mo' if (a is None or a < 24) else '24-36mo' if a < 36 else '36-54mo' if a < 54 else '54mo+'
    m = MA[b]
    if tier in ('C', 'D'): m = max(m, TIER_DEF.get(tier, 0.25))
    return round(m, 3)

def family(k):
    m = re.match(r'^(.*?)_(\d+)_(\d+|1tb|2tb)$', k)
    return m.group(1) if m else None

# tier + launch_date inherited from surviving siblings of the same family
fam_tier, fam_ld = {}, {}
for k in existing:
    f = family(k)
    if not f: continue
    fam_tier.setdefault(f, Counter())[db[k].get('tier')] += 1
    if db[k].get('launch_date'): fam_ld.setdefault(f, db[k]['launch_date'])

# the research schema carries no display_name, so keep the canonical names alongside the keys
NAMES = {
    'oppo_find_x9_16_512':          'Oppo Find X9 16/512GB',
    'vivo_v50_12_512':              'Vivo V50 12/512GB',
    'oppo_reno_13_8_128':           'Oppo Reno 13 8/128GB',
    'realme_14_pro_plus_5g_12_512': 'Realme 14 Pro+ 5G 12/512GB',
    'realme_14_pro_plus_5g_8_128':  'Realme 14 Pro+ 5G 8/128GB',
    'realme_14_pro_plus_5g_12_256': 'Realme 14 Pro+ 5G 12/256GB',
}

ver = {}
for f in sorted(glob.glob(f'{DIR}/_gaps/repair_verified_*.json')):
    for it in json.load(open(f)).get('items', []):
        ver[it['key']] = it

added, skipped = [], []
for key, v in ver.items():
    if key in existing:
        skipped.append((key, 'already in DB')); continue
    if v.get('verdict') != 'add' or v.get('exists_in_india') != 'yes':
        skipped.append((key, f"verdict={v.get('verdict')} exists={v.get('exists_in_india')}")); continue
    rs = v.get('resale_inr'); new = v.get('official_new_inr')
    if not isinstance(rs, (int, float)) or rs <= 0:
        skipped.append((key, 'no usable resale')); continue
    # The refuter's `triangulated` flag gates RAISES elsewhere in the pipeline, because raising a
    # live price on weak evidence costs money on every unit. That reasoning does not transfer here:
    # these entries replace phantoms whose prices were FABRICATED, there is no live price to
    # protect, and the refuter already cut every figure 9-15% and rejected every buyback quote.
    # So weak provenance is recorded as calibration_status 'estimated' — which makes next week's
    # refresh re-research it — rather than leaving RT with no quote at all for a real phone.
    weak = not v.get('triangulated', True) or v.get('confidence') == 'low'

    fam = family(key)
    tier = (fam_tier.get(fam).most_common(1)[0][0] if fam_tier.get(fam) else None) or 'B'
    ld = v.get('launch_date') or fam_ld.get(fam) or ''
    m = margin_for(ld, tier)
    a1 = rs / (1 + m)
    cap = 'margin'
    if a1 > rs * RESALE_CAP: a1, cap = rs * RESALE_CAP, 'resale*0.92'
    if isinstance(new, (int, float)) and new > 0 and a1 > new * NEW_CAP:
        a1, cap = new * NEW_CAP, 'new*0.85'
    a1 = r100(a1)
    if a1 <= 0:
        skipped.append((key, 'computed A1 <= 0')); continue

    e = {'display_name': NAMES.get(key, key), 'tier': tier, 'launch_date': ld,
         'resale_target_a1': r100(a1 * (1 + m)), 'target_margin': m,
         'market_resale_observed': r100(rs)}
    if isinstance(new, (int, float)) and new > 0: e['net_new_inr'] = int(new)   # exact, never rounded
    bm = v.get('buyback_inr')
    if isinstance(bm, (int, float)) and bm > 0: e['buyback_market'] = r100(bm)
    e['calibration_status'] = 'estimated' if weak else 'verified'
    e['calibration_date'] = TODAY
    e['live_source'] = (f"SIBLING REPAIR {TODAY}: real variant replacing a removed phantom. "
                        f"resale Rs{r100(rs):,} -> A1 Rs{a1:,} = resale/(1+{m}) [{cap}]"
                        f"{' (resale extrapolated - re-research)' if weak else ''}")[:180]
    db[key] = e
    existing.add(key)
    added.append({'key': key, 'name': e['display_name'], 'tier': tier, 'launch': ld,
                  'a1': a1, 'resale': r100(rs), 'new': new, 'cap': cap,
                  'status': e['calibration_status']})

print('=' * 78)
print(f'SIBLING REPAIR {TODAY}  ({"APPLY" if APPLY else "dry-run"})')
print('=' * 78)
print(f'researched: {len(ver)} | ADDED: {len(added)} | skipped: {len(skipped)}')
for a in added:
    n = f"{a['new']:,}" if a['new'] else '?'
    print(f"  + {a['name'][:42]:42s} tier={a['tier']} A1 Rs{a['a1']:>7,}  resale {a['resale']:>7,}  new {n:>9s} [{a['cap']}] {a['status']}")
for k, r in skipped:
    print(f'  - {k}: {r}')

json.dump(added, open(f'{DIR}/_added_siblings_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)

if not APPLY:
    print('\n(dry-run — no files written)')
    sys.exit(0)

if added:
    out = {'_meta': meta}
    out.update({k: v for k, v in db.items() if k != '_meta'})
    json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
    compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
    lines = open(f'{DIR}/index.html').read().split('\n')
    n = 0
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith('const DB = {'):
            lines[i] = ln[:len(ln) - len(ln.lstrip())] + compact; n += 1
    assert n == 1, f'expected exactly 1 DB line, patched {n}'
    open(f'{DIR}/index.html', 'w').write('\n'.join(lines))
    print(f'\nAPPLIED: +{len(added)} sibling variants -> total {len([k for k in out if k != "_meta"])}')
else:
    print('\nNothing to add.')
