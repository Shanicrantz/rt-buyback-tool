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
TODAY = '2026-09-21'
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
# HAND-CONFIRMED PHANTOMS (2026-09-21) — removed on positive India line-up evidence read by hand, whatever the
# refuter's verdict. realme_p3_ultra_5g_8_512: Mobigyaan / Zee Biz India launch coverage (2025-03-19) lists exactly
# three India SKUs — 8/128 Rs26,999, 8/256 Rs27,999, 12/256 Rs29,999 — and "up to 256 GB UFS 3.1 storage".
HAND_CONFIRMED_PHANTOM = {'realme_p3_ultra_5g_8_512':
    'India line-up is 8/128, 8/256, 12/256 only (max 256GB) — Mobigyaan + Zee Biz launch coverage, hand-read 2026-09-21'}

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
START = {k: v for k, v in json.load(open(f'{DIR}/phone_db.backup-{TODAY}.json')).items() if k != '_meta'}
ver = {}
for f in sorted(glob.glob(f'{DIR}/_pending/verified_*.json')):
    for it in json.load(open(f)).get('items', []):
        ver[it['key']] = it

applied, refused, removed, held, notes, added_new = [], [], [], [], [], []

for key, v in ver.items():
    e = ph.get(key)
    src = items.get(key, {})
    if e is None and src.get('kind') == 'newmodel':
        # ADD a model the DB was missing (2026-09-21). Same evidence bar as a raise — there is no live price
        # to protect, but a new entry must not be born on an invented number: positive India existence,
        # triangulated resale at medium/high confidence, and every hard ceiling applied.
        rs, conf = v.get('resale_final'), v.get('confidence')
        if not (v.get('verdict') == 'grant' and v.get('exists_final') == 'yes' and v.get('triangulated')
                and conf in ('high', 'medium') and isinstance(rs, (int, float)) and rs > 0):
            held.append((key, f"newmodel not added: verdict={v.get('verdict')} exists={v.get('exists_final')} "
                              f"tri={v.get('triangulated')} conf={conf}")); continue
        ne = {'display_name': src['name'], 'tier': src['tier'],
              'launch_date': v.get('launch_date_final') or src.get('launch_date')}
        m = margin_for(ne)
        nf = v.get('new_final')
        a1 = min(rs / (1 + m), rs * RESALE_CAP)
        if isinstance(nf, (int, float)) and nf > 0: a1 = min(a1, nf * NEW_CAP)
        a1 = r100(a1)
        ne['resale_target_a1'] = r100(a1 * (1 + m)); ne['target_margin'] = m
        if isinstance(nf, (int, float)) and nf > 0: ne['net_new_inr'] = int(nf)
        bf = v.get('buyback_final')
        if isinstance(bf, (int, float)) and 0 < bf <= rs * 0.85: ne['buyback_market'] = r100(bf)
        ne['market_resale_observed'] = r100(rs)
        ne['calibration_status'] = 'verified'; ne['calibration_date'] = TODAY
        ne['live_source'] = (f"ADDED {TODAY} (verify+refute): resale ₹{r100(rs):,} -> A1 ₹{a1:,} = resale÷(1+{m}) "
                             f"conf={conf}")[:180]
        ph[key] = ne
        added_new.append({'key': key, 'name': src['name'], 'a1': a1, 'resale': r100(rs), 'new': nf,
                          'launch': ne['launch_date'], 'note': (v.get('note') or '')[:140]})
        continue
    if e is None:
        held.append((key, 'not in DB')); continue
    live = a1_of(e)
    week_start = src.get('cur_a1') or live          # A1 before this week's refresh
    verdict = v.get('verdict')
    rs = v.get('resale_final')
    conf = v.get('confidence')
    triangulated = bool(v.get('triangulated'))
    kind = src.get('kind')

    if key in HAND_CONFIRMED_PHANTOM:
        removed.append((key, e.get('display_name'), HAND_CONFIRMED_PHANTOM[key])); continue
    if verdict == 'remove':
        if key in KEEP_VERIFIED_REAL:
            held.append((key, 'remove REFUSED — hand-verified REAL against India source, kept')); continue
        if v.get('exists_final') == 'no' and conf == 'high':
            removed.append((key, e.get('display_name'), (v.get('note') or '')[:140]))
        else:
            held.append((key, f"remove asked but exists={v.get('exists_final')} conf={conf} — kept"))
        continue

    # 'refuse' means "the rise this item was sent for is not supported". Only a kind=rise item was raised by this
    # week's refresh, so only there does refusing mean rolling back to week-start. On a drop / placeholder item the
    # refresh already moved the price DOWN, and restoring week-start would silently undo that drop (found
    # 2026-09-21: Moto G37 Power 4/128 would have gone back UP from 9,840 to 10,240). There, a refusal is a
    # 'lower' when the refuter's resale is below live and a no-op otherwise — the grant/lower path below
    # already refuses any upward move that is not triangulated.
    if verdict == 'refuse' and kind != 'rise':
        verdict = 'lower'
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
        # Roll back to where the model started the week by restoring the WHOLE week-start entry.
        # Resetting only resale_target_a1 (the old behaviour) left this week's research figures —
        # market_resale_observed, target_margin, live_source, calibration stamps — on the entry. For a
        # refused DROP that leaves A1 far above the recorded resale, which the a1_above_resale invariant
        # rightly flags as a loss-per-unit (hit iPad Air M4 13" and MacBook Pro M4 on 2026-09-16).
        start_e = START.get(key)
        # Restore even when A1 did not move (a hold already kept it): the refuted research resale/stamps must not
        # stay on the entry as if verified (2026-09-21: iPhone 17 Pro Max 2TB kept a refuted Rs1,49,000 resale).
        if live and start_e:
            restored = json.loads(json.dumps(start_e))
            bf_r = v.get('buyback_final')
            if not isinstance(bf_r, (int, float)) or bf_r <= 0:
                restored.pop('buyback_market', None)
            nf = v.get('new_final')
            if not restored.get('net_new_inr') and isinstance(nf, (int, float)) and nf > 0:
                restored['net_new_inr'] = int(nf)     # fill a missing ceiling only; never overwrite Shane's
            restored['last_verification'] = f"{TODAY}: {verdict} — research move refused, week-start entry restored"
            e.clear(); e.update(restored)
            refused.append({'key': key, 'name': e.get('display_name'), 'from': r100(live),
                            'to': r100(a1_of(e)), 'note': (v.get('note') or '')[:120]})
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
    _sn = e.get('net_new_inr')
    if (isinstance(_sn, (int, float)) and _sn > 0 and _sn % 1000 != 0
            and isinstance(new, (int, float)) and new > _sn):
        new = _sn        # never loosen a trusted stored ceiling (see net_new_inr guard below)
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
        if kind in ('placeholder_resale', 'roundprice') or src.get('placeholder_anchor'):
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
    # net_new_inr is the new x0.85 CEILING and Shane is the authority on it. Only let verification move it
    # when that is conservative or corrects a known fabrication (2026-09-21): a LOWER verified price tightens
    # the ceiling (always safe); a HIGHER one loosens it, so it is accepted only where the stored figure is
    # missing or a round-thousand fabrication signature.
    old_new = e.get('net_new_inr')
    if isinstance(new, (int, float)) and new > 0:
        if (not isinstance(old_new, (int, float)) or old_new <= 0 or new <= old_new
                or old_new % 1000 == 0):
            e['net_new_inr'] = int(new)
        else:
            notes.append((key, f'verified new {int(new)} above stored {old_new} — ceiling kept (not loosened)'))
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
if added_new:
    print('\n--- NEW MODELS ADDED ---')
    for a in added_new: print(f"  {a['name'][:40]:40s} A1 {a['a1']:>7,} resale {a['resale']:>7,} new {a['new']} launch {a['launch']}")
if notes:
    print('\n--- NOTES ---')
    for k, t in notes: print(f'  {k}: {t}')
if held:
    print(f'\n--- HELD ({len(held)}) ---')
    for k, r in held: print(f'  {k}: {r}')

json.dump({'today': TODAY, 'applied': applied, 'refused': refused,
           'added_new': added_new,
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
