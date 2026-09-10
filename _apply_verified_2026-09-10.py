#!/usr/bin/env python3
"""Apply the outlier verification (_pending/verified_*.json) ON TOP of the weekly brain refresh.

Runs after _apply_brain_weekly.py --apply. Four verdict classes from the refuter:
  grant  -> the capped +8% rise was too small; re-anchor on the verified resale
  refuse -> the rise is unsupported; roll the model back to where it started the week
  lower  -> the defensible number is BELOW what is live; apply it
  remove -> hard evidence the variant does not exist in India
  hold   -> nothing established; leave whatever the weekly refresh produced

Asymmetry is deliberate and matches the weekly script: a DOWNWARD move needs no
confidence bar (underpaying costs one deal), an UPWARD move needs triangulated
evidence at medium/high confidence (overpaying costs money on every unit). Every
grant is still bounded by the same hard ceilings — resale x0.92, new x0.85 — and by
+-20% measured from where the model started the week, so one verification round can
never outrun a week of real drift.

--apply writes both files; default is dry-run.
"""
import json, glob, sys

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-09-10'
APPLY = '--apply' in sys.argv
RESALE_CAP, NEW_CAP, BAND = 0.92, 0.85, 0.20

def r100(n): return int(round(n / 100.0)) * 100

# HAND-VERIFICATION OVERRIDE (2026-09-10). The refuter's 'remove' verdicts were re-checked by
# hand against India-specific sources before any deletion, per the standing rule that a phantom
# is never deleted on an agent's say-so. Four were confirmed and are removed; one was WRONG:
#   realme_15_5g_12_512 — refuter claimed realme.com/in has no 12/512. GSMArena's India-specific
#   page (gsmarena.com/realme_15_5g-14018.php) lists Internal as "128GB 8GB RAM, 256GB 8GB RAM,
#   256GB 12GB RAM, 512GB 12GB RAM" — the variant is REAL. Deleting a real variant costs RT a
#   counter-quote on every walk-in, so positive evidence wins and the entry stays.
KEEP_VERIFIED_REAL = {'realme_15_5g_12_512'}

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
        y, mo = map(int, ld.split('-')[:2]); return (2026 - y) * 12 + (9 - mo)
    except Exception:
        return None

def margin_for(e):
    a = months(e.get('launch_date', ''))
    b = '<24mo' if (a is None or a < 24) else '24-36mo' if a < 36 else '36-54mo' if a < 54 else '54mo+'
    m = MA[b]
    if e.get('tier') in ('C', 'D'):
        m = max(m, TIER_DEF.get(e.get('tier'), 0.25))
    return round(m, 3)

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

items = {i['key']: i for i in json.load(open(f'{DIR}/_pending/items.json'))}
ver = {}
for f in sorted(glob.glob(f'{DIR}/_pending/verified_*.json')):
    for it in json.load(open(f)).get('items', []):
        ver[it['key']] = it

applied, refused, removed, held, notes = [], [], [], [], []

for key, v in ver.items():
    e = ph.get(key)
    src = items.get(key, {})
    if e is None:
        held.append((key, 'not in DB')); continue
    live = a1_of(e)
    week_start = src.get('cur_a1') or live          # A1 before this week's refresh
    verdict = v.get('verdict')
    rs = v.get('resale_final')
    conf = v.get('confidence')
    triangulated = bool(v.get('triangulated'))
    kind = src.get('kind')

    if verdict == 'remove':
        if key in KEEP_VERIFIED_REAL:
            held.append((key, 'remove REFUSED — hand-verified REAL against India source, kept')); continue
        if v.get('exists_final') == 'no' and conf == 'high':
            removed.append((key, e.get('display_name'), (v.get('note') or '')[:140]))
        else:
            held.append((key, f"remove asked but exists={v.get('exists_final')} conf={conf} — kept"))
        continue

    if verdict == 'refuse' or (verdict == 'hold' and kind == 'rise'):
        # A refuted rise usually means the RESEARCH INPUTS were contaminated, and the competitor
        # buyback is often the contaminated half (a "Get Upto" headline, or the 40%-of-listed
        # Cashify widget). The grant/lower path already drops a buyback the refuter would not
        # stake — this path used to return early and leave the weekly figure sitting on the
        # entry, which then surfaced as a false "Cashify pays more than RT" alarm. Drop it here
        # too, on every path where the refuter came back with no real quote. (Bug found
        # 2026-09-10 on Vivo X Fold5 and iPad Pro M4 13".)
        bf_r = v.get('buyback_final')
        if not isinstance(bf_r, (int, float)) or bf_r <= 0:
            if e.pop('buyback_market', None) is not None:
                notes.append((key, 'dropped stale buyback_market — refuter found no real quote'))
        # roll back to where the model started the week
        target = week_start
        if live and target and abs(target - live) > 1:
            m = margin_of(e)
            e['resale_target_a1'] = r100(target * (1 + m))
            refused.append({'key': key, 'name': e.get('display_name'), 'from': r100(live),
                            'to': r100(target), 'note': (v.get('note') or '')[:120]})
        else:
            held.append((key, 'refuse: already at week-start'))
        continue

    if verdict == 'hold' or not isinstance(rs, (int, float)) or rs <= 0:
        bf_h = v.get('buyback_final')
        if not isinstance(bf_h, (int, float)) or bf_h <= 0:
            if e.pop('buyback_market', None) is not None:
                notes.append((key, 'dropped stale buyback_market — refuter found no real quote'))
        held.append((key, f'{verdict}: no usable resale')); continue

    # grant / lower -> recompute A1 from the verified resale
    m = margin_for(e)
    new = v.get('new_final') or e.get('net_new_inr')
    a1 = rs / (1 + m)
    cap = 'margin'
    if a1 > rs * RESALE_CAP: a1, cap = rs * RESALE_CAP, 'resale*0.92'
    if isinstance(new, (int, float)) and new > 0 and a1 > new * NEW_CAP:
        a1, cap = new * NEW_CAP, 'new*0.85'

    going_up = live is not None and a1 > live
    if going_up:
        if not (triangulated and conf in ('high', 'medium')):
            held.append((key, f'raise refused: triangulated={triangulated} conf={conf}')); continue
        ceiling = week_start * (1 + BAND)
        if a1 > ceiling: a1, cap = ceiling, cap + '+band+20%'
    else:
        # The -20% band protects an ESTABLISHED price from being outrun by one verification
        # round. An entry added minutes ago on a placeholder anchor (resale set to a flat 80%
        # of new, or a fabricated round price) has no such history to protect — its "week
        # start" IS the fabrication. Banding those would lock in most of the invented number,
        # so downward corrections on them apply in full.
        if kind in ('placeholder_resale', 'roundprice'):
            cap = cap + '+unbanded-new-entry'
        else:
            floor = week_start * (1 - BAND)
            if a1 < floor: a1, cap = floor, cap + '+band-20%'
        # the band must never push A1 back above what the phone re-sells for
        hard = rs * RESALE_CAP
        if isinstance(new, (int, float)) and new > 0: hard = min(hard, new * NEW_CAP)
        if a1 > hard: a1, cap = hard, cap + '+hard-ceiling'

    a1 = r100(a1)
    if a1 <= 0:
        held.append((key, 'computed A1 <= 0')); continue
    if live and abs(a1 - live) < 100:
        held.append((key, 'no material change')); continue

    e['resale_target_a1'] = r100(a1 * (1 + m))
    e['target_margin'] = m
    e['market_resale_observed'] = r100(rs)
    bf = v.get('buyback_final')
    if isinstance(bf, (int, float)) and bf > 0: e['buyback_market'] = r100(bf)
    else: e.pop('buyback_market', None)
    if isinstance(new, (int, float)) and new > 0: e['net_new_inr'] = int(new)
    e['calibration_status'] = 'verified'
    e['calibration_date'] = TODAY
    e['live_source'] = (f"VERIFIED {TODAY} ({verdict}): resale ₹{r100(rs):,} -> A1 ₹{a1:,} "
                        f"= resale÷(1+{m}) [{cap}] conf={conf}")[:180]
    applied.append({'key': key, 'name': e.get('display_name'), 'kind': kind, 'verdict': verdict,
                    'from': r100(live) if live else None, 'to': a1, 'resale': r100(rs),
                    'cap': cap, 'conf': conf, 'note': (v.get('note') or '')[:140]})

print('=' * 78)
print(f'OUTLIER VERIFICATION {TODAY}  ({"APPLY" if APPLY else "dry-run"})')
print('=' * 78)
print(f'verified items: {len(ver)} | repriced: {len(applied)} | rolled back: {len(refused)} '
      f'| remove-recommended: {len(removed)} | held: {len(held)}')

if applied:
    print('\n--- REPRICED ---')
    for a in sorted(applied, key=lambda a: (a['to'] - (a['from'] or 0))):
        d = a['to'] - (a['from'] or 0)
        print(f"  {d:+8,}  {(a['name'] or '')[:40]:40s} {a['from'] or 0:>7,} -> {a['to']:>7,} "
              f"[{a['verdict']}/{a['kind']}] resale {a['resale']:>7,} {a['cap']} conf={a['conf']}")
if refused:
    print('\n--- RISES ROLLED BACK TO WEEK-START ---')
    for a in refused:
        print(f"  {(a['name'] or '')[:40]:40s} {a['from']:>7,} -> {a['to']:>7,}   {a['note']}")
if removed:
    print('\n--- REMOVE RECOMMENDED (hard evidence, high confidence) ---')
    for k, nm, note in removed: print(f'  {k} ({nm}): {note}')
if held:
    print(f'\n--- HELD ({len(held)}) ---')
    for k, r in held: print(f'  {k}: {r}')

json.dump({'today': TODAY, 'applied': applied, 'refused': refused,
           'remove_recommended': [{'key': k, 'name': n, 'note': t} for k, n, t in removed],
           'held': [{'key': k, 'reason': r} for k, r in held]},
          open(f'{DIR}/_pending/outcome_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)

if not APPLY:
    print('\n(dry-run — no files written)')
    sys.exit(0)

for k, nm, note in removed:
    ph.pop(k, None)
    print(f'  REMOVED {k} ({nm})')

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
print(f'\nAPPLIED: {len(applied)} repriced, {len(refused)} rolled back, {len(removed)} removed.')
