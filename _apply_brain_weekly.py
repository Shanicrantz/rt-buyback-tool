#!/usr/bin/env python3
"""WEEKLY BRAIN REFRESH — re-anchors already-computed models to this week's verified market.

Unlike _apply_brain.py (the one-time override -> computed migration), this refreshes
resale_target_a1 in place from fresh research:

    A1 = resale / (1 + margin)      margin = margin_by_age(launch_date)
    A1 = min(A1, resale*0.92, new*0.85)
    A1 = clamp(A1, cur*0.80, cur*1.20)          # +-20% single-week move cap
    resale_target_a1 = A1 * (1+margin)          # back-solved so the engine reproduces A1

Margin policy: margin_by_age for tiers S/A/B (it was calibrated on exactly that cohort,
from Shane's own overrides). For C/D the tier default is used as a FLOOR, so cheap phones
keep a sane absolute risk buffer instead of a 10% one.

--apply writes both files; default is dry-run.
"""
import json, glob, sys, re
from collections import defaultdict

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-17'
APPLY = '--apply' in sys.argv
WEEK_CAP = 0.20      # max single-week DROP in A1 (market softening = safe direction)
INCREASE_CAP = 0.08  # max single-week RISE in A1 — deliberately tighter than the drop cap.
                     # Web research on this DB reliably anchors to OLX *asking* prices and pushes
                     # up; overpaying loses money while underpaying only loses a deal. A rise big
                     # enough to be blocked here is flagged for Shane instead of applied.
RESALE_CAP = 0.92    # never pay above 92% of resale (>=8% margin)
NEW_CAP = 0.85       # never pay above 85% of new price
SUSPECT_RATIO = 0.55 # buyback_market below this share of resale => resale is probably inflated

# --- manual verification, carried forward from 2026-08-10 (critic was wrong on 5 of 6) ---
# Critic said "DOES NOT EXIST" but the model is REAL and stays in the DB:
VERIFIED_REAL = {
    'moto_razr_fold_12_256', 'moto_razr_fold_16_512',      # India 2026-05-13, Rs1,49,999 / Rs1,59,999
    'moto_signature_12_256', 'moto_signature_16_512', 'moto_signature_16_1tb',  # India, Rs59,999/64,999/69,999
}
# Confirmed-phantom variants to REMOVE. iphone_17e_128 was removed on 2026-08-10; this week's
# "does not exist" claims start empty and are only added after I verify them by hand.
CONFIRMED_PHANTOM = set()
# Official India new prices confirmed first-hand today (used as the new*0.85 ceiling):
VERIFIED_NEW = {
    'moto_razr_fold_12_256': 149999, 'moto_razr_fold_16_512': 159999,
    'moto_signature_12_256': 59999, 'moto_signature_16_512': 64999, 'moto_signature_16_1tb': 69999,
    'samsung_z_fold_8_256': 179999, 'samsung_z_fold_8_ultra_256': 199999,
    'samsung_z_flip_8_256': 124999,
}

def r100(n): return int(round(n / 100.0)) * 100

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
ph = {k: v for k, v in db.items() if k != '_meta'}
MA = meta['margin_by_age']
TIER_DEF = meta['default_margins_by_tier']

def months(ld):
    try:
        y, mo = map(int, ld.split('-')[:2])
        return (2026 - y) * 12 + (8 - mo)
    except Exception:
        return None

def bucket(age):
    if age is None: return '24-36mo'
    return '<24mo' if age < 24 else '24-36mo' if age < 36 else '36-54mo' if age < 54 else '54mo+'

def margin_for(e):
    m = MA[bucket(months(e.get('launch_date', '')))]
    if e.get('tier') in ('C', 'D'):
        m = max(m, TIER_DEF.get(e.get('tier'), 0.25))
    return round(m, 3)

RT_PREMIUM = {'S': 0.06, 'A': 0.08, 'B': 0.10, 'C': 0.12, 'D': 0.14}

def cur_a1(e):
    """A1 the live engine produces today — mirrors computeA1() in index.html exactly,
    including its priority order and its margin default."""
    tier = e.get('tier')
    margin = e.get('target_margin')
    if margin is None: margin = TIER_DEF.get(tier, 0.22)
    if e.get('rt_buyback_a1_override'): return e['rt_buyback_a1_override']
    if e.get('resale_target_a1'):
        return e['resale_target_a1'] / (1 + margin)
    if e.get('cashify_exchange'):
        prem = e.get('rt_premium_over_cashify', RT_PREMIUM.get(tier, 0.08))
        return e['cashify_exchange'] * (1 + prem)
    refurb = e.get('refurb_retail_anchor_excellent')
    if not refurb and e.get('refurb_retail_anchor_fair'):
        refurb = e['refurb_retail_anchor_fair'] * meta.get('fair_to_excellent_multiplier', 1.18)
    if refurb:
        mf = e.get('market_factor', meta.get('default_market_factor', 0.88))
        return refurb * mf / (1 + margin)
    return None

# ---- load critic-verified research ----
ver = {}
for f in glob.glob(f'{DIR}/_ov_updates/verified_*.json'):
    for m in json.load(open(f)).get('models', []):
        ver[m['key']] = m

nonexistent, changes, skipped, flags = [], [], [], []
held_estimate, blocked_rises = set(), []

for key, v in ver.items():
    e = ph.get(key)
    note = (v.get('note') or '')
    if e is None:
        skipped.append((key, 'not in DB')); continue
    if 'DOES NOT EXIST' in note.upper() and key not in VERIFIED_REAL:
        nonexistent.append((key, e.get('display_name'), note[:120])); continue

    rs = v.get('resale_final'); bm = v.get('buyback_final')
    if not isinstance(rs, (int, float)) or rs <= 0:
        skipped.append((key, 'no verified resale')); continue

    # Fabricated-research guard: several batches returned buyback at exactly 50% of resale with
    # resale exactly equal to the value already in the DB — i.e. the agent echoed the existing
    # estimate back instead of researching it. Treat that buyback as absent, not as evidence.
    echoed = (e.get('resale_target_a1') == r100(rs))
    if bm and abs(bm / rs - 0.50) < 0.005 and echoed:
        flags.append(('echoed-estimate', key, f'resale {r100(rs)} == existing anchor and buyback is exactly 50% — not real research'))
        bm = None
        held_estimate.add(key)

    # A competitor cannot pay ~90% of resale and still run a business. When the reported
    # buyback sits that close to resale, one of the two numbers is wrong, so the pair is
    # useless as a competitiveness signal — drop it rather than show Shane a false alarm.
    if bm and bm / rs > 0.85:
        flags.append(('incoherent-spread', key,
                      f'buyback {r100(bm)} is {bm/rs:.0%} of resale {r100(rs)} — not a real competitor quote, dropped'))
        bm = None

    cur = cur_a1(e)
    if not cur:
        skipped.append((key, 'no current A1')); continue

    # guardrail: resale must exceed what buyers pay
    if isinstance(bm, (int, float)) and bm > 0 and bm >= rs:
        skipped.append((key, f'resale {rs} <= buyback {bm} — incoherent, held')); continue

    # An inflated resale with a plausible buyback shows up as an implausibly wide spread.
    # Never let that combination RAISE what RT pays.
    suspect = bool(bm) and (bm / rs) < SUSPECT_RATIO

    m = margin_for(e)
    new = VERIFIED_NEW.get(key, e.get('net_new_inr'))
    a1 = rs / (1 + m)
    a1 = min(a1, rs * RESALE_CAP)
    capped_by = 'margin'
    if a1 == rs * RESALE_CAP: capped_by = 'resale*0.92'
    if isinstance(new, (int, float)) and new > 0 and a1 > new * NEW_CAP:
        a1 = new * NEW_CAP; capped_by = 'new*0.85'

    raw = a1
    lo, hi = cur * (1 - WEEK_CAP), cur * (1 + INCREASE_CAP)
    if a1 < lo:
        a1, capped_by = lo, 'week-cap-down'
    elif a1 > hi:
        blocked_rises.append({'key': key, 'name': e.get('display_name'), 'cur': r100(cur),
                              'wanted': r100(a1), 'granted': r100(hi),
                              'pct_wanted': (a1 - cur) / cur * 100, 'resale': r100(rs),
                              'buyback': r100(bm) if bm else None, 'conf': v.get('confidence')})
        a1, capped_by = hi, 'rise-cap+flagged'

    # The ±week caps only damp research NOISE — they must never override the two hard economic
    # ceilings. The -20% floor is applied after the caps above, so when research says resale
    # collapsed by more than 20% the floor can land ABOVE resale×0.92, i.e. RT would pay more
    # than it can re-sell for and lose money on every unit. Re-assert the ceilings last.
    hard = rs * RESALE_CAP
    if isinstance(new, (int, float)) and new > 0:
        hard = min(hard, new * NEW_CAP)
    if a1 > hard:
        a1, capped_by = hard, capped_by + '+hard-ceiling'

    if suspect and a1 > cur:
        a1, capped_by = cur, 'held: resale looks inflated vs buyback'
        flags.append(('inflated-resale-hold', key,
                      f'buyback {r100(bm)} is only {bm/rs:.0%} of resale {r100(rs)} — rise refused'))
    a1 = r100(a1)
    if a1 <= 0:
        skipped.append((key, 'computed A1 <= 0')); continue

    changes.append({
        'key': key, 'name': e.get('display_name'), 'tier': e.get('tier'),
        'cur': r100(cur), 'new_a1': a1, 'pct': (a1 - cur) / cur * 100,
        'resale': r100(rs), 'old_resale': e.get('resale_target_a1'),
        'buyback': r100(bm) if isinstance(bm, (int, float)) and bm else None,
        'margin': m, 'old_margin': e.get('target_margin'),
        'capped_by': capped_by, 'raw': r100(raw), 'conf': v.get('confidence'),
    })

# ---- storage-inversion repair: within a family A1 must not fall as storage rises ----
RANK = {'64': 1, '128': 2, '256': 3, '512': 4, '1tb': 5, '2tb': 6}
def split_key(k):
    m = re.match(r'^(.*?)_(\d+|1tb|2tb)$', k)
    return (m.group(1), m.group(2)) if m and m.group(2) in RANK else (None, None)

byfam = defaultdict(list)
idx = {c['key']: c for c in changes}
for c in changes:
    fam, st = split_key(c['key'])
    if fam: byfam[fam].append((RANK[st], c))

inversions = 0
for fam, items in byfam.items():
    items.sort(key=lambda x: x[0])
    run = 0
    for _, c in items:
        if c['new_a1'] < run:
            newv = run
            ceil = min(c['cur'] * (1 + WEEK_CAP),
                       (c.get('resale') or 1e9) * RESALE_CAP)
            e = ph[c['key']]
            if e.get('net_new_inr'): ceil = min(ceil, e['net_new_inr'] * NEW_CAP)
            newv = min(newv, ceil)
            if newv > c['new_a1']:
                c['new_a1'] = r100(newv); c['capped_by'] += '+inv-fix'
                c['pct'] = (c['new_a1'] - c['cur']) / c['cur'] * 100
                inversions += 1
            else:
                flags.append(('storage-inversion-unfixable', c['key'],
                              f"{c['new_a1']} < {run} but capped"))
        run = max(run, c['new_a1'])

# ---- competitiveness: where Cashify pays more than RT ----
lose = [c for c in changes if c['buyback'] and c['buyback'] > c['new_a1']]

# ================= REPORT =================
moved = [c for c in changes if abs(c['pct']) >= 0.5]
print('=' * 78)
print(f'WEEKLY BRAIN REFRESH {TODAY}  (dry-run)' if not APPLY else f'WEEKLY BRAIN REFRESH {TODAY}  (APPLY)')
print('=' * 78)
print(f'verified models in: {len(ver)} | repriced: {len(changes)} | moved >=0.5%: {len(moved)} '
      f'| skipped: {len(skipped)} | inversions fixed: {inversions}')
print(f'margin_by_age={MA}  (C/D floored at tier default)')

if changes:
    ups = sorted([c for c in changes if c['pct'] > 0], key=lambda c: -c['pct'])
    dns = sorted([c for c in changes if c['pct'] < 0], key=lambda c: c['pct'])
    print(f'\n--- BIGGEST INCREASES ({len(ups)}) ---')
    for c in ups[:15]:
        print(f"  {c['pct']:+6.1f}%  {c['name'][:42]:42s} A1 {c['cur']:>7,} -> {c['new_a1']:>7,} "
              f"| resale {c['resale']:>7,} m={c['margin']} [{c['capped_by']}]")
    print(f'\n--- BIGGEST DECREASES ({len(dns)}) ---')
    for c in dns[:15]:
        print(f"  {c['pct']:+6.1f}%  {c['name'][:42]:42s} A1 {c['cur']:>7,} -> {c['new_a1']:>7,} "
              f"| resale {c['resale']:>7,} m={c['margin']} [{c['capped_by']}]")

if blocked_rises:
    print(f'\n--- RISES CAPPED AT +{INCREASE_CAP:.0%} ({len(blocked_rises)}) — research wanted more; review before granting ---')
    for b in sorted(blocked_rises, key=lambda b: -b['pct_wanted'])[:20]:
        print(f"    {b['name'][:40]:40s} {b['cur']:>7,} -> granted {b['granted']:>7,} "
              f"(research wanted {b['wanted']:>7,}, {b['pct_wanted']:+.0f}%) conf={b['conf']}")

if held_estimate:
    print(f'\n--- ECHOED-ESTIMATE, LEFT AS estimated ({len(held_estimate)}) ---')
    for k in sorted(held_estimate): print(f'    {k}')

print(f'\n--- EXISTENCE CHECKS ---')
print(f'    critic flagged non-existent, I verified REAL and kept: {sorted(VERIFIED_REAL)}')
print(f'    confirmed phantom, REMOVING: {sorted(CONFIRMED_PHANTOM & set(ph))}')
unresolved = [x for x in nonexistent if x[0] not in CONFIRMED_PHANTOM]
if unresolved:
    print(f'    still-unresolved non-existence claims ({len(unresolved)}) — NOT auto-removed:')
    for k, n, note in unresolved: print(f'      {k} ({n}): {note}')

if lose:
    print(f'\n!!! CASHIFY PAYS MORE THAN RT ({len(lose)}) — you would lose these walk-ins:')
    for c in sorted(lose, key=lambda c: c['buyback'] - c['new_a1'], reverse=True)[:25]:
        print(f"    {c['name'][:44]:44s} RT {c['new_a1']:>7,} vs market {c['buyback']:>7,} "
              f"(+{c['buyback']-c['new_a1']:,})")

if flags:
    print(f'\n--- FLAGS ({len(flags)}) ---')
    for t, k, d in flags[:20]: print(f'    [{t}] {k}: {d}')

if skipped:
    print(f'\n--- SKIPPED ({len(skipped)}) ---')
    for k, r in skipped[:20]: print(f'    {k}: {r}')

json.dump({'today': TODAY, 'changes': changes, 'nonexistent': nonexistent,
           'lose_to_market': lose, 'skipped': skipped, 'flags': flags,
           'blocked_rises': blocked_rises, 'held_estimate': sorted(held_estimate),
           'verified_real_kept': sorted(VERIFIED_REAL),
           'removed_phantom': sorted(CONFIRMED_PHANTOM & set(ph))},
          open(f'{DIR}/_brain_refresh_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)

if not APPLY:
    print('\n(dry-run — no files written. re-run with --apply)')
    sys.exit(0)

# ================= APPLY =================
for key in sorted(CONFIRMED_PHANTOM & set(ph)):
    print(f'  REMOVED phantom variant: {key} ({ph[key].get("display_name")})')
    del ph[key]

for c in changes:
    e = ph.get(c['key'])
    if e is None: continue
    m = c['margin']
    e['resale_target_a1'] = r100(c['new_a1'] * (1 + m))   # engine: A1 = resale/(1+m)
    e['target_margin'] = m
    if c['buyback']: e['buyback_market'] = c['buyback']
    else: e.pop('buyback_market', None)   # drop stale/fabricated competitor figures
    if c['key'] in VERIFIED_NEW: e['net_new_inr'] = VERIFIED_NEW[c['key']]
    e['market_resale_observed'] = c['resale']
    e['calibration_status'] = 'estimated' if c['key'] in held_estimate else 'verified'
    e['calibration_date'] = TODAY
    e['live_source'] = (f"BRAIN {TODAY}: resale ₹{c['resale']:,}"
                        f"{' / market buys ₹' + format(c['buyback'], ',') if c['buyback'] else ''}"
                        f" -> A1 ₹{c['new_a1']:,} = resale÷(1+{m}) [{c['capped_by']}]")[:180]
    # NOTE: any refurb_retail_anchor_excellent / cashify_exchange on this entry is left in
    # place as provenance. resale_target_a1 outranks both in computeA1(), so they are inert.

out = {'_meta': meta}
out.update(ph)
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
lines = open(f'{DIR}/index.html').read().split('\n')
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'):
        lines[i] = ln[:len(ln) - len(ln.lstrip())] + compact
open(f'{DIR}/index.html', 'w').write('\n'.join(lines))
print(f'\nAPPLIED: {len(changes)} models repriced, {inversions} storage inversions fixed.')
