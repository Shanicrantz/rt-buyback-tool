#!/usr/bin/env python3
"""v6.10 (2026-10-01) — INTERNATIONAL-VARIANT POLICY + the real India siblings behind 12 non-India rows.

Shane's decision (2026-10-01): the 12 DB rows whose RAM/storage config was never sold in India are NOT deleted.
International units do walk in, so each stays quotable, relabelled '(International)' and priced 10% below the nearest
India configuration of the same phone (rule + rationale in _intl_rule.py; the min() there means the relabel never
raises a quote). india_sibling = the India config with the same storage (closest RAM, tie -> lower RAM); if India
never sold that storage, the top India config below it.

The India siblings come from the 2026-09-30 gap audit (finder + adversarial critic: brand India store / FoneArena
launch coverage + OLX/ORU/Cashify datapoints), priced by the brain: A1 = resale / (1 + margin_by_age), C/D floored at
the tier default, capped at resale x0.92 and new x0.85.

Ladder coherence: adding a freshly researched India config can expose a STALE sibling priced above it (Poco M7 5G
6/128 at A1 6,200 from the 2026-06-25 calibration vs the verified 8/128 at 6,000). Per the guardrail, the stale
dominated config is pulled DOWN to the fresh one's A1 — never the fresh one up. --apply writes both files."""
import json, glob, re, sys
from datetime import date
from _intl_rule import r100, engine_a1, set_a1, recompute_international, INTL_DISCOUNT

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-10-01'
RESEARCH_DATE = '2026-09-30'
APPLY = '--apply' in sys.argv
T = date(2026, 10, 1)

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
MA = meta['margin_by_age']
TIER_DEF = meta['default_margins_by_tier']
PRE = engine_a1(db, TODAY)          # every quote as the live engine computes it before this change

def months(ld):
    y, mo, d = map(int, ld.split('-'))
    return (T.year - y) * 12 + (T.month - mo) - (1 if T.day < d else 0)

def margin_for(tier, ld):
    a = months(ld) if ld else None
    b = '<24mo' if (a is None or a < 24) else '24-36mo' if a < 36 else '36-54mo' if a < 54 else '54mo+'
    m = MA[b]
    if tier in ('C', 'D'): m = max(m, TIER_DEF.get(tier, 0.25))
    return round(m, 3)

def cfg(k, fam):
    ram, st = k[len(fam) + 1:].split('_')
    return int(ram), int(st)

# ---------------- 1) the real India configs (critic-verified 2026-09-30) ----------------
INDIA_ADDS = ['oneplus_11_16_256', 'oneplus_11r_16_256', 'oneplus_12_16_512', 'oneplus_13_16_512',
              'oneplus_13r_12_256', 'oneplus_13r_16_512', 'oneplus_nord_3_16_256', 'oneplus_nord_ce_3_12_256',
              'poco_m7_5g_8_128', 'vivo_y39_5g_8_128', 'oppo_reno_14_12_256', 'oppo_reno_14_12_512']
find, ver = {}, {}
for f in glob.glob(f'{DIR}/_gaps/find_*.json'):
    for m in json.load(open(f)).get('missing', []): find[m['key']] = m
for f in glob.glob(f'{DIR}/_gaps/verified_*.json'):
    for v in json.load(open(f)).get('verified', []): ver[v['key']] = v

added = []
for k in INDIA_ADDS:
    assert k not in db, f'{k} already in DB'
    f, v = find[k], ver[k]
    assert v.get('real_india_launch') and v.get('verdict') != 'rejected', k
    rs, nn, bm = v.get('resale_price_final'), v.get('new_price_final'), v.get('buyback_market_final')
    fam = re.sub(r'_\d+_\d+$', '', k)
    sib_t = [db[x]['tier'] for x in db if x != '_meta' and re.fullmatch(re.escape(fam) + r'_\d+_\d+', x)]
    tier = max(set(sib_t), key=sib_t.count) if sib_t else f['tier']      # series tier sets the C/D margin floor
    ld = f['launch_date']
    m = margin_for(tier, ld)
    a1 = min(rs / (1 + m), rs * 0.92)
    if isinstance(nn, (int, float)) and nn > 0: a1 = min(a1, nn * 0.85)
    note = (v.get('note') or '').upper()
    estimated = any(t in note for t in ('ESTIMATED', 'LOW CONFIDENCE', 'ANALOG', 'RE-RESEARCH'))
    e = {'display_name': f['display_name'], 'tier': tier, 'launch_date': ld, 'target_margin': m,
         'market_resale_observed': r100(rs)}
    a1 = set_a1(e, int(a1) // 100 * 100)                                 # floor to the Rs100 grid: never round up
    if isinstance(nn, (int, float)) and nn > 0: e['net_new_inr'] = int(nn)
    if isinstance(bm, (int, float)) and 0 < bm <= rs * 0.85: e['buyback_market'] = r100(bm)
    e['calibration_status'] = 'estimated' if estimated else 'verified'
    e['calibration_date'] = RESEARCH_DATE
    e['live_source'] = (f"Added {TODAY} (gap-audit+critic {RESEARCH_DATE}): real India config. resale ₹{r100(rs):,}"
                        f"{' / new ₹' + format(int(nn), ',') if nn else ''} -> A1 ₹{a1:,} = resale÷(1+{m})")[:180]
    db[k] = e
    added.append((k, e['display_name'], tier, ld, a1, r100(rs), nn, e['calibration_status']))

# ---------------- 2) the 12 non-India configs -> '(International)' ----------------
INTL = {  # row -> nearest India config
    'oneplus_11_8_256': 'oneplus_11_16_256',
    'oneplus_11_8_512': 'oneplus_11_16_256',          # India topped out at 256GB
    'oneplus_11r_8_256': 'oneplus_11r_16_256',
    'oneplus_12_12_512': 'oneplus_12_16_512',
    'oneplus_13_12_512': 'oneplus_13_16_512',
    'oneplus_13r_8_256': 'oneplus_13r_12_256',
    'oneplus_nord_3_8_256': 'oneplus_nord_3_16_256',
    'oneplus_nord_ce_3_8_256': 'oneplus_nord_ce_3_12_256',
    'poco_m7_5g_4_128': 'poco_m7_5g_6_128',
    'vivo_y39_5g_4_128': 'vivo_y39_5g_8_128',
    'vivo_y39_5g_6_128': 'vivo_y39_5g_8_128',
    'oppo_reno_14_8_512': 'oppo_reno_14_12_512',
}
for k, sib in INTL.items():
    e = db[k]
    e['display_name'] = re.sub(r'\s*\(International\)$', '', e['display_name']) + ' (International)'
    e['international'] = True
    e['intl_sibling'] = sib
    e['intl_discount'] = INTL_DISCOUNT
    if e.get('target_margin') is None:
        e['target_margin'] = margin_for(e.get('tier'), e.get('launch_date'))

# ---------------- 3) ladder coherence among INDIA rows of the touched families ----------------
fams = sorted({re.sub(r'_\d+_\d+$', '', k) for k in list(INTL) + INDIA_ADDS})
lowered = []
cur = engine_a1(db, TODAY)
for fam in fams:
    rows = [x for x in db if x != '_meta' and re.fullmatch(re.escape(fam) + r'_\d+_\d+', x) and not db[x].get('international')]
    for small in rows:
        for big in rows:
            if small == big: continue
            (rs_, ss), (rb, sb) = cfg(small, fam), cfg(big, fam)
            if rb >= rs_ and sb >= ss and cur[small] > cur[big] + 100:     # a dominated config priced above its superior
                if db[small].get('calibration_date') in (RESEARCH_DATE, TODAY) or db[small].get('rt_buyback_a1_override'):
                    print(f'  !! ladder conflict left for review: {small} {cur[small]} > {big} {cur[big]}'); continue
                if db[small].get('target_margin') is None:
                    db[small]['target_margin'] = margin_for(db[small].get('tier'), db[small].get('launch_date'))
                old = cur[small]
                new = set_a1(db[small], cur[big])
                db[small]['calibration_status'] = 'estimated'
                db[small]['calibration_date'] = TODAY
                db[small]['live_source'] = (f"LADDER {TODAY}: stale A1 ₹{old:,} sat above the verified {db[big]['display_name']} "
                                            f"₹{cur[big]:,}; lowered to it")[:180]
                lowered.append((small, old, new, big))
                cur[small] = new

# ---------------- 3b) proportional ladder cap on the new trims (lowers only; rule of 2026-09-26) ----------------
# Research priced the new trims off their own datapoints while the verified base trim kept an earlier, more
# conservative calibration. A used storage/RAM premium compresses and never exceeds the new-price step, so each new
# trim's resale is capped at base_resale x (new_trim / new_base), using India LAUNCH prices for both.
LADDER_CAP = [  # (new trim, verified base trim, launch new of trim, launch new of base)
    ('oneplus_13_16_512', 'oneplus_13_12_256', 76999, 69999),
    ('oppo_reno_14_12_256', 'oppo_reno_14_8_256', 39999, 37999),   # Reno 14 India launch 2025-07: 37,999 / 39,999 / 42,999
    ('oppo_reno_14_12_512', 'oppo_reno_14_8_256', 42999, 37999),
]
capped = []
cur = engine_a1(db, TODAY)
for k, base, nk, nb in LADDER_CAP:
    b = db[base]
    bres = b.get('market_resale_observed') or b['resale_target_a1']
    cap_res = r100(bres * nk / nb)
    e = db[k]
    lim = min(cap_res / (1 + e['target_margin']), cap_res * 0.92)
    if cur[k] > lim:
        old = cur[k]
        new = set_a1(e, int(lim) // 100 * 100)
        e['market_resale_observed'] = min(e['market_resale_observed'], cap_res)
        e['calibration_status'] = 'estimated'
        e['live_source'] = (f"Added {TODAY} (gap-audit+critic {RESEARCH_DATE}); LADDER-CAP: resale capped at {b['display_name']} "
                            f"₹{bres:,} x {nk:,}/{nb:,} = ₹{cap_res:,} -> A1 ₹{new:,} (research wanted ₹{old:,})")[:180]
        capped.append((k, old, new, base, cap_res))

# ---------------- 4) price the international rows (min rule, see _intl_rule.py) ----------------
# PRE holds each row's quote before this change: the rule may lower it, never raise it.
changes = []
for k in INTL:
    db[k]['_pre_intl_a1'] = PRE[k]
res = recompute_international(db, TODAY, TODAY)
cm = {}
for k, old, new, sa in res:
    tgt = min(r100(sa * (1 - INTL_DISCOUNT)), PRE[k]) if PRE[k] > 0 else r100(sa * (1 - INTL_DISCOUNT))
    if new != tgt:
        new = set_a1(db[k], tgt)
    cm[k] = (PRE[k], new, sa)
# A config never sold in India has no India new price, competitor quote or resale of its own — those fields were
# extrapolated when the row was invented. Keep them as provenance, off the pricing path (the resale anchor now wins).
for k in INTL:
    e = db[k]
    for fld in ('net_new_inr', 'buyback_market', 'market_resale_observed', 'cashify_exchange',
                'refurb_retail_anchor_excellent', 'refurb_retail_anchor_fair'):
        if fld in e: e[f'_pre_intl_{fld}'] = e.pop(fld)
    e['calibration_status'] = 'estimated'
    e['calibration_date'] = TODAY
POST = engine_a1(db, TODAY)

# ---------------- report ----------------
print('=' * 78); print(f'v6.10 INTERNATIONAL FIX {TODAY} ({"APPLY" if APPLY else "dry-run"})'); print('=' * 78)
print(f'\nINDIA CONFIGS ADDED ({len(added)}):')
for k, nm, t, ld, a1, rs, nn, st in added:
    print(f'  {nm[:30]:30s} T{t} {ld}  A1 ₹{POST[k]:>7,}  resale ₹{rs:>7,}  new {nn}  [{st}]')
print(f'\nSTALE INDIA ROWS LOWERED FOR LADDER COHERENCE ({len(lowered)}):')
for s, o, n, b in lowered: print(f'  {s}: {o:,} -> {n:,}  (<= {b})')
print(f'\nNEW TRIMS LADDER-CAPPED TO THE VERIFIED BASE ({len(capped)}):')
for k, o, n, b, cr in capped: print(f'  {k}: A1 {o:,} -> {n:,}  (resale cap {cr:,} from {b})')
print(f'\nINTERNATIONAL ({len(INTL)}):')
for k in INTL:
    o, n, sa = cm[k]
    print(f'  {db[k]["display_name"][:46]:46s} A1 {o:>7,} -> {POST[k]:>7,}   (0.9 x {INTL[k]} {sa:,} = {r100(sa*0.9):,})')
print('\nFAMILY VIEW (engine A1 after; I = International):')
for fam in fams:
    rows = [x for x in db if x != '_meta' and re.fullmatch(re.escape(fam) + r'_\d+_\d+', x)]
    rows.sort(key=lambda x: (bool(db[x].get('international')), cfg(x, fam)))
    print('  ' + fam + ': ' + ' | '.join(f"{x[len(fam) + 1:]}{'(I)' if db[x].get('international') else ''}={POST[x]:,}" for x in rows))
moved = {k: (PRE.get(k), POST[k]) for k in POST if PRE.get(k) != POST[k]}
print(f'\nQUOTES CHANGED vs v6.9: {len(moved)} (expected {len(added)} new + {len(INTL)} intl + {len(lowered)} ladder)')
unexpected = [k for k in moved if k not in INDIA_ADDS and k not in INTL and k not in {l[0] for l in lowered}]
print('  unexpected movers:', unexpected or 'none')
assert not unexpected

if not APPLY:
    print('\n(dry-run — no files written)'); sys.exit(0)
out = {'_meta': meta}; out.update({k: v for k, v in db.items() if k != '_meta'})
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
c = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
L = open(f'{DIR}/index.html').read().split('\n'); n = 0
for i, ln in enumerate(L):
    if ln.lstrip().startswith('const DB = {'): L[i] = ln[:len(ln) - len(ln.lstrip())] + c; n += 1
assert n == 1, n
open(f'{DIR}/index.html', 'w').write('\n'.join(L))
json.dump({'added': added, 'international': INTL, 'lowered': lowered, 'ladder_capped': capped,
           'quotes': {k: {'v6.9': PRE.get(k), 'v6.10': POST[k]} for k in moved}},
          open(f'{DIR}/_intl_fix_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)
print(f'\nAPPLIED: +{len(added)} India configs, {len(INTL)} International, {len(lowered)} ladder fixes.')
