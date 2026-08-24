#!/usr/bin/env python3
"""Add this week's gap-audit finds — but only the ones the price-check pass cleared.

The gap audit's own prices were not trustworthy this week (a Tecno Pova at ₹49,999,
an iQOO Z11 at ₹34,999 — 2-3x their series' real India band, almost certainly MRPs).
So the finder supplies identity (name / launch / variant) and the price-check refuter
(_gaps/checked_*.json) supplies the money: only add_to_db=true entries are written, and
they are priced by the brain, A1 = resale/(1+margin_by_age) capped at new x 0.85.

--apply writes both files; default is dry-run.
"""
import json, glob, re, sys
from collections import Counter

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-24'
APPLY = '--apply' in sys.argv
KNOWN = {'iphone','apple','samsung','vivo','iqoo','realme','oppo','redmi','xiaomi','poco','oneplus',
         'google','moto','nothing','cmf','honor','asus','infinix','tecno','lava','itel','micromax',
         'nokia','hmd','ipad'}

# --- TIE-BREAK PANEL 2026-08-24 -------------------------------------------------
# Three independent lenses (brand India store / major retailer / India tech press) were
# run on the three families whose proposed prices looked 2-3x their series' historical
# band. All nine agents agreed the prices are REAL, with verbatim source quotes and
# matching variant ladders — 2026 India budget pricing has simply moved up hard
# (iQOO Z10 Rs21,999 -> Z11 Rs34,999; Pova 7 Pro Rs19,999 -> Pova 8 Pro Rs49,999;
# Poco M7 Rs10,499 -> M8x Rs20,999). The band heuristic was wrong, not the research.
# The price-check pass had rejected the Z11 6/128 on band grounds while clearing its
# MORE expensive siblings — internally inconsistent — so the panel result restores it.
PANEL_OVERRIDE = {
    'iqoo_z11_5g_6_128': {'add_to_db': True, 'new_final_inr': 34999, 'resale_final_inr': 28000,
                          'tier_final': 'B', 'launch_final': '2026-08-20',
                          'price_provenance': 'official_brand_india', 'confidence': 'high',
                          'note': 'TIE-BREAK PANEL 3/3: shop.iqoo.com/in lists 6GB+128GB at Rs34,999 '
                                  '(MRP Rs49,999); Digit/91mobiles/TelecomTalk publish the same four-variant '
                                  'table. Band test that rejected it was the wrong test.'},
}

def r100(n): return int(round(n / 100.0)) * 100

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
MA = meta['margin_by_age']
TIER_DEF = meta['default_margins_by_tier']
existing = set(k for k in db if k != '_meta')
def sig(nm): return re.sub(r'[^a-z0-9]', '', (nm or '').lower())
exsig = set(sig(db[k].get('display_name', '')) for k in existing)

def months(ld):
    try:
        y, mo = map(int, ld.split('-')[:2]); return (2026 - y) * 12 + (8 - mo)
    except Exception: return None

def margin_for(ld, tier):
    a = months(ld or '')
    b = '<24mo' if (a is None or a < 24) else '24-36mo' if a < 36 else '36-54mo' if a < 54 else '54mo+'
    m = MA[b]
    if tier in ('C', 'D'): m = max(m, TIER_DEF.get(tier, 0.25))
    return round(m, 3)

# --- tier normalisation ---------------------------------------------------------
# The finder assigns tier per a rubric, but it drifts: this week it put the iQOO Z11 and
# the Tecno Pova 8 Pro in tier B while every existing iQOO Z (14/14) and Tecno Pova (14 C,
# 8 D) in the DB sits at C, and it put the OnePlus 15R at A while the 13R and 12R are both
# B. Tier is not cosmetic — it sets the margin FLOOR for C/D, so a drifting tier silently
# changed what RT pays (the Pova 8 Pro's two variants came out with 0.25 and 0.099 margins
# for the same phone). Where the DB already holds the same series, its own tier wins.
import collections
# The R-line has no DB entry to inherit from yet, but the precedent is unambiguous:
# OnePlus 12R and 13R are both tier B. (Tier is inert for A/B here since target_margin
# is always written explicitly — it matters for which models the weekly scope prioritises.)
TIER_OVERRIDE = {'oneplus_15r_12_256': 'B', 'oneplus_15r_12_512': 'B'}

def series_tier(key):
    if key in TIER_OVERRIDE: return TIER_OVERRIDE[key], 'oneplus_12r/13r precedent', 2
    toks = key.split('_')
    for n in (3, 2):
        pref = '_'.join(toks[:n])
        tiers = [e.get('tier') for k, e in db.items()
                 if k != '_meta' and k.startswith(pref) and e.get('tier')]
        if len(tiers) >= 2:
            return collections.Counter(tiers).most_common(1)[0][0], pref, len(tiers)
    return None, None, 0

find = {}
for f in sorted(glob.glob(f'{DIR}/_gaps/find_*.json')):
    for m in json.load(open(f)).get('missing', []): find[m['key']] = m
checked = {}
for f in sorted(glob.glob(f'{DIR}/_gaps/checked_*.json')):
    for v in json.load(open(f)).get('items', []): checked[v['key']] = v
for k, ov in PANEL_OVERRIDE.items():
    checked.setdefault(k, {}).update(ov)

added, rejected, dup, retiered = [], [], [], []
bybrand = Counter()
for key, v in checked.items():
    f = find.get(key, {})
    name = f.get('display_name') or key
    if not v.get('add_to_db'):
        rejected.append((key, name, (v.get('note') or '')[:150])); continue
    if key in existing or sig(name) in exsig:
        dup.append((key, name)); continue
    if key.split('_')[0] not in KNOWN:
        rejected.append((key, name, 'unknown brand prefix')); continue
    resale = v.get('resale_final_inr'); new = v.get('new_final_inr')
    if not isinstance(resale, (int, float)) or resale <= 0:
        rejected.append((key, name, 'no defensible resale')); continue
    tier = v.get('tier_final') or f.get('tier') or 'C'
    st, spref, sn = series_tier(key)
    if st and st != tier:
        retiered.append((key, tier, st, spref, sn))
        tier = st
    ld = v.get('launch_final') or f.get('launch_date') or ''
    m = margin_for(ld, tier)
    a1 = resale / (1 + m)
    cap = 'margin'
    if a1 > resale * 0.92: a1, cap = resale * 0.92, 'resale*0.92'
    if isinstance(new, (int, float)) and new > 0 and a1 > new * 0.85:
        a1, cap = new * 0.85, 'new*0.85'
    a1 = r100(a1)
    e = {'display_name': name, 'tier': tier, 'launch_date': ld,
         'resale_target_a1': r100(a1 * (1 + m)), 'target_margin': m,
         'market_resale_observed': r100(resale)}
    if isinstance(new, (int, float)) and new > 0: e['net_new_inr'] = int(new)
    bm = v.get('buyback_final_inr') if 'buyback_final_inr' in v else None
    if isinstance(bm, (int, float)) and bm > 0: e['buyback_market'] = r100(bm)
    e['calibration_status'] = 'verified' if v.get('confidence') in ('high', 'medium') else 'estimated'
    e['calibration_date'] = TODAY
    e['live_source'] = (f"Added {TODAY} (gap-audit + price-check). resale ₹{r100(resale):,}"
                        f"{f' / new ₹{int(new):,}' if isinstance(new,(int,float)) and new else ''}"
                        f" -> A1 ₹{a1:,} = resale÷(1+{m}) [{cap}] {v.get('price_provenance')}/{v.get('confidence')}")[:180]
    db[key] = e; existing.add(key); exsig.add(sig(name))
    added.append({'key': key, 'name': name, 'launch': ld, 'tier': tier, 'a1': a1,
                  'resale': r100(resale), 'new': e.get('net_new_inr'),
                  'prov': v.get('price_provenance'), 'conf': v.get('confidence')})
    bybrand[key.split('_')[0]] += 1

json.dump(added, open(f'{DIR}/_added_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)
print('=== ADD GAPS (price-checked) ===')
print(f'price-checked: {len(checked)} | ADDED: {len(added)} | rejected: {len(rejected)} | dup: {len(dup)}')
print('by brand:', dict(bybrand.most_common()))
for a in sorted(added, key=lambda a: a['launch'], reverse=True):
    print(f"  {a['launch']}  {a['name'][:40]:40s} tier={a['tier']} A1 ₹{a['a1']:,} "
          f"(resale {a['resale']:,}, new {a['new']}) {a['prov']}/{a['conf']}")
if retiered:
    print('\n--- TIER NORMALISED TO THE DB SERIES ---')
    for k, was, now, pref, n in retiered:
        print(f'  {k}: {was} -> {now}  (matches {n} existing {pref}* entries)')
if rejected:
    print('\n--- NOT ADDED ---')
    for k, nm, note in rejected: print(f'  {k} ({nm}): {note}')
if dup:
    print('\n--- ALREADY PRESENT ---')
    for k, nm in dup: print(f'  {k} ({nm})')

if APPLY and added:
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
    print(f"\nAPPLIED: +{len(added)} models -> total {len([k for k in out if k != '_meta'])}")
elif not APPLY:
    print('\n(dry-run — re-run with --apply to write)')
