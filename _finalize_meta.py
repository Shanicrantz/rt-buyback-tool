#!/usr/bin/env python3
"""Final metadata pass for the weekly refresh: bump version, stamp last_calibration,
write the dated changelog, refresh market_signals, then write BOTH files in sync and
run the invariant checks. --apply to write; default dry-run."""
import json, sys, re

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-10'
VERSION = '5.9'
APPLY = '--apply' in sys.argv

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
ph = {k: v for k, v in db.items() if k != '_meta'}

try:
    refresh = json.load(open(f'{DIR}/_brain_refresh_{TODAY}.json'))
except FileNotFoundError:
    refresh = {'changes': [], 'lose_to_market': [], 'nonexistent': []}
changes = refresh.get('changes', [])
moved = [c for c in changes if abs(c['pct']) >= 0.5]
added = json.load(open(f'{DIR}/_added_{TODAY}.json')) if __import__('os').path.exists(f'{DIR}/_added_{TODAY}.json') else []

meta['version'] = VERSION
meta['last_calibration'] = TODAY
meta['pricing_brain'] = ("A1 buyback = resale ÷ (1+margin_by_age), capped at resale×0.92 & new×0.85. "
                         "margin auto-calibrated by phone age from Shane overrides vs REAL resale "
                         "(recent ~10%, oldest ~30%); tier default acts as a floor for C/D so cheap "
                         "phones keep a sane absolute buffer. buyback_market shown as competitiveness "
                         "reference. Refreshed weekly from live resale + buyback research.")
meta[f'v{VERSION.replace(".", "_")}_changelog'] = (
    f"Weekly brain refresh ({TODAY}): re-anchored {len(changes)} high-value models "
    f"({len(moved)} moved ≥0.5%) from live India resale + buyback-market research, batched 12×8 and "
    f"adversarially critic-verified. Scope = top value-at-risk S/A-tier + recent launches, weighted to "
    f"models previously priced from pre-launch leaks (Galaxy Z Fold8/Flip8 family, Razr Fold, 2026 "
    f"flagships); deep budget/long-tail left on existing values 5 days after the 2026-08-05 full refresh. "
    f"A1 = resale÷(1+margin_by_age), caps resale×0.92 / new×0.85, single-week move capped ±20%. "
    f"Gap-audit added {len(added)} verified India launches; a phantom 'Galaxy F70 Pro' (3 variants) was "
    f"rejected by the critic. Motorola Razr Fold was falsely flagged non-existent by a low-confidence "
    f"critic and independently RE-VERIFIED as real (India 2026-05-13, ₹1,49,999 / ₹1,59,999) — kept.")

# --- market signals: the Jul-22 Unpacked has happened; the pre-launch haircut rule is spent ---
meta['market_signals'] = {
    'updated': TODAY,
    'resolved': {
        'samsung_z_fold_8__z_flip_8': {
            'event': 'Galaxy Z Fold8 / Fold8 Ultra / Flip8 LAUNCHED in India 2026-07-22. '
                     'Official India pricing confirmed: Fold8 ₹1,79,999, Fold8 Ultra ₹1,99,999, '
                     'Flip8 ₹1,24,999 (12/256).',
            'effect': 'The "successor imminent" pre-launch haircut on Fold7/Flip7 is now SPENT — the '
                      'successor has shipped, so outgoing-gen anchors are re-based on observed post-launch '
                      'resale rather than an anticipatory trim.',
            'confidence': 'high (samsung.com/in product pages + Flipkart live listings, re-verified 2026-08-10)',
        },
        'motorola_razr_fold': {
            'event': 'Motorola first book-style foldable, India 2026-05-13. 12/256 ₹1,49,999, '
                     '16/512 ₹1,59,999, FIFA Edition 16/512 ₹1,69,999.',
            'effect': 'Both DB variants confirmed REAL and correctly priced. Do not treat as phantom.',
            'confidence': 'high (GSMArena India launch report + multiple India outlets, 2026-08-10)',
        },
    },
    'rule': ('When a successor flagship is confirmed <~4 weeks out, trim outgoing-gen resale anchors 5-10%; '
             'once it actually launches, drop the anticipatory trim and re-anchor on observed resale. '
             'Festival-sale (Prime Day/BBD) lows are a TEMPORARY NET_NEW floor: cap buyback below them, but '
             'revert the anchor to trend after the sale unless it is a confirmed permanent price cut.'),
}

# ================= INVARIANTS =================
def margin_of(e):
    m = e.get('target_margin')
    return m if m is not None else meta['default_margins_by_tier'].get(e.get('tier'), 0.22)

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

problems = {'a1_above_new': [], 'zero_or_broken': [], 'storage_inversion': [], 'resale_le_buyback': []}
for k, e in ph.items():
    a1 = a1_of(e)
    if a1 is None or a1 <= 0:
        if e.get('net_new_inr') and e.get('launch_date'): continue   # formula path, engine derives it
        problems['zero_or_broken'].append(k); continue
    nn = e.get('net_new_inr')
    if isinstance(nn, (int, float)) and nn > 0 and a1 >= nn: problems['a1_above_new'].append((k, round(a1), nn))
    # Compare the competitor's price against the OBSERVED market resale. resale_target_a1 is a
    # back-solved anchor (A1 x (1+margin)) that can sit below observed resale whenever a cap
    # bound A1, so it is not the right number for this check.
    bm = e.get('buyback_market')
    rs = e.get('market_resale_observed') or e.get('resale_target_a1')
    if bm and rs and bm >= rs: problems['resale_le_buyback'].append((k, bm, rs))

RANK = {'64': 1, '128': 2, '256': 3, '512': 4, '1tb': 5, '2tb': 6}
fams = {}
for k, e in ph.items():
    m = re.match(r'^(.*?)_(\d+|1tb|2tb)$', k)
    if m and m.group(2) in RANK:
        a1 = a1_of(e)
        if a1: fams.setdefault(m.group(1), []).append((RANK[m.group(2)], k, a1))
# Repair storage inversions: a higher-storage variant must never compute BELOW its smaller
# sibling. Level the bigger one UP to the sibling's A1 — the minimum conservative fix (never
# worth less, but we do not invent a premium either) — and never past its own new*0.85 ceiling.
inv_fixed = []
for fam, items in fams.items():
    items.sort()
    for i in range(1, len(items)):
        if items[i][2] < items[i-1][2] - 1:
            k, target = items[i][1], items[i-1][2]
            e = ph[k]
            nn = e.get('net_new_inr')
            if isinstance(nn, (int, float)) and nn > 0: target = min(target, nn * 0.85)
            if target <= items[i][2]:
                problems['storage_inversion'].append((k, round(items[i][2]), items[i-1][1], round(items[i-1][2])))
                continue
            mg = margin_of(e)
            if e.get('resale_target_a1'):
                e['resale_target_a1'] = int(round(target * (1 + mg) / 100)) * 100
            elif e.get('refurb_retail_anchor_excellent'):
                mf = e.get('market_factor', meta.get('default_market_factor', 0.88))
                e['refurb_retail_anchor_excellent'] = int(round(target * (1 + mg) / mf / 100)) * 100
            else:
                problems['storage_inversion'].append((k, round(items[i][2]), items[i-1][1], round(items[i-1][2])))
                continue
            inv_fixed.append((k, round(items[i][2]), round(a1_of(e))))
            items[i] = (items[i][0], k, a1_of(e))
if inv_fixed:
    print(f'  storage inversions repaired: {len(inv_fixed)}')
    for k, before, after in inv_fixed: print(f'      {k}: {before:,} -> {after:,}')

print('=' * 72)
print(f'FINALIZE v{VERSION}  {TODAY}   phones={len(ph)}')
print('=' * 72)
for name, items in problems.items():
    print(f'  {name:20s}: {len(items)}')
    for it in items[:8]: print(f'      {it}')

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

# verify the two copies really match
h = open(f'{DIR}/index.html', encoding='utf-8').read()
i = h.find('const DB = {')
inline = json.loads(h[i + len('const DB = '):h.find('\n', i)].rstrip().rstrip(';'))
disk = json.load(open(f'{DIR}/phone_db.json'))
same = json.dumps(inline, sort_keys=True) == json.dumps(disk, sort_keys=True)
print(f'\nAPPLIED v{VERSION}. files in sync: {same}')
if not same: sys.exit(1)
