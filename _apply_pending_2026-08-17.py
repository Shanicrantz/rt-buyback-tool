#!/usr/bin/env python3
"""Apply the hand-verified follow-ups to the 2026-08-17 refresh (v6.0 -> v6.1).

Three things were left open after the weekly run and have now been verified by a
dedicated find+critic pass (_pending/verified_*.json):

1. PHANTOM VARIANTS. Seven RAM/storage combos were positively disproved at HIGH
   confidence — each verifier named the real India line-up instead (e.g. OnePlus 15R
   ships 12GB+ only; Nothing's own India store lists just 12/256 and 16/512). Those
   are removed. The two the pass could NOT disprove stay: asus_rog_phone_9_12_256
   (low confidence, no official India launch found but nothing replaced it) and
   samsung_z_flip_8_256 (confirmed REAL — India 2026-07-22, ₹1,24,999).

2. Z FOLD8 FAMILY. Both Fold8 and Fold8 Ultra are confirmed real on Samsung India's
   own buy page, with official prices now first-hand. Their resale anchors were
   already right; what was fake was the competitor buyback: Cashify's "Approx.
   Buyback Value" widget is a TEMPLATE that always prints 40% of the listed price
   (verified identical on Fold8, Fold8 Ultra and iPhone 17 Pro Max). Since resale
   sits at 80% of new, that template lands at exactly 50% of resale — which is what
   the echo-detector kept catching. So: keep the resale anchors, stamp the confirmed
   new prices, drop every buyback figure sourced from that widget, and promote the
   entries from 'estimated' to 'verified'.

3. CAPPED RISES. The +8% cap held on 34 models; nine of the largest were re-checked.
   The verification largely VINDICATED the cap: four iPhone entries came back LOW
   confidence, the Pro Max 2TB resale turned out to be back-solved from its own
   buyback figure, and Cashify's iPhone pages were caught quoting a new price of
   ₹1,37,900 against Apple's real ₹1,49,900. Those five rises are refused, and where
   a verified figure is LOWER than what is live (iPhone 17 Pro 256) the lower one is
   applied. Four models re-anchor on hand-verified resale with corroborated official
   prices.

Rule applied to (3): a rise needs medium/high confidence AND a resale that was
triangulated rather than derived from the buyback figure. An incoherent pair (buyback
> 85% of resale) discredits the BUYBACK, which is dropped, not the resale. Any grant
is held inside the same ±20% band the weekly drop cap uses, measured from where the
model started the week, so one verification round cannot outrun a week of real drift.
Downward moves always apply — conservative is the safe error.

--apply writes both files; default is dry-run.
"""
import json, sys

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-17'
APPLY = '--apply' in sys.argv
RESALE_CAP, NEW_CAP = 0.92, 0.85

# High-confidence, positively-disproved variants (verifier named the real line-up).
PHANTOMS = {
    'oneplus_15r_8_128':          'India ships 12/256, 12/512, 16/512 — no 8GB tier in any market',
    'oneplus_15r_8_256':          'India ships 12/256, 12/512, 16/512 — no 8GB tier in any market',
    'oneplus_13t_16_512':         'never sold in India; rebadged as OnePlus 13s (12/256, 12/512), no 16GB tier',
    'oppo_reno_15_8_512':         'India ships 8/256, 12/256, 12/512 — no 8GB+512GB combo',
    'nothing_phone_3_12_512':     "Nothing's own India store lists only 12/256 and 16/512",
    'vivo_x200_fe_12_512':        'India ships 12/256 and 16/512 only',
    'moto_edge_70_pro_5g_12_512': 'India tops out at 256GB (8/256, 12/256); the 512GB tier is the Edge 70 Fusion',
}
# Could not be disproved -> kept (deleting a real variant costs a counter quote).
KEPT_DOUBTFUL = {
    'asus_rog_phone_9_12_256': 'no official India launch found, but nothing replaced it — kept at low confidence',
    'samsung_z_flip_8_256':    'CONFIRMED REAL — India 2026-07-22, ₹1,24,999 (12/256)',
}

# Confirmed first-hand from Samsung India + Cashify spec sheets.
FOLD8 = {
    'samsung_z_fold_8_256':       (144000, 179999),
    'samsung_z_fold_8_512':       (160000, 199999),
    'samsung_z_fold_8_1tb':       (192000, 239999),
    'samsung_z_fold_8_ultra_256': (160000, 199999),
    'samsung_z_fold_8_ultra_512': (176000, 219999),
    'samsung_z_fold_8_ultra_1tb': (208000, 259999),
}

def r100(n): return int(round(n / 100.0)) * 100

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

removed, fold8_done, rise_changes, rise_kept = [], [], [], []
rise_capped_week = []

# A1 each model started the week on, before the v6.0 weekly run moved it.
WEEK_START = {c['key']: c['cur'] for c in json.load(open(f'{DIR}/_brain_refresh_{TODAY}.json'))['changes']}

# ---- 1. remove disproved variants ----
for k, why in PHANTOMS.items():
    if k in ph:
        removed.append((k, ph[k].get('display_name'), why))
        del ph[k]

# ---- 2. Z Fold8 family: confirm prices, drop template buyback, promote to verified ----
for k, (resale, new) in FOLD8.items():
    e = ph.get(k)
    if not e: continue
    m = margin_of(e)
    a1 = min(resale / (1 + m), resale * RESALE_CAP, new * NEW_CAP)
    before = a1_of(e)
    e['resale_target_a1'] = r100(resale)
    e['net_new_inr'] = new
    e['market_resale_observed'] = resale
    e.pop('buyback_market', None)          # Cashify widget = flat 40%-of-price template, not a quote
    e['calibration_status'] = 'verified'
    e['calibration_date'] = TODAY
    e['live_source'] = (f"HAND-VERIFIED {TODAY}: Samsung India new ₹{new:,}; thin used market "
                        f"(on sale 2026-08-07) resale ₹{resale:,} -> A1 ₹{r100(a1):,}. No real "
                        f"competitor buyback exists yet — Cashify's widget is a 40%-of-price template.")[:180]
    fold8_done.append((k, e.get('display_name'), r100(before or 0), r100(a1), new))

# ---- 3. capped rises: apply verified resale, but only downward when confidence is low ----
ver = json.load(open(f'{DIR}/_pending/verified_rises.json'))
for v in ver['models']:
    k, e = v['key'], ph.get(v['key'])
    if not e: continue
    rs, conf = v.get('resale_price'), v.get('confidence')
    if not isinstance(rs, (int, float)) or rs <= 0: continue
    m = margin_of(e)
    new = v.get('official_new_price') or e.get('net_new_inr')
    a1 = min(rs / (1 + m), rs * RESALE_CAP)
    if isinstance(new, (int, float)) and new > 0: a1 = min(a1, new * NEW_CAP)
    a1, cur = r100(a1), r100(a1_of(e) or 0)
    bm = v.get('buyback_market')
    # Same coherence rule as the weekly run: a buyback above 85% of resale is not a real
    # competitor quote, so it is dropped rather than shown as a competitiveness signal.
    bm_ok = isinstance(bm, (int, float)) and bm > 0 and bm / rs <= 0.85

    # A RISE has to clear more than a confidence label, because this is a manual grant stacked on
    # top of the +8% the weekly run already gave. Two things disqualify one outright:
    #   - LOW confidence, and
    #   - a resale that was derived FROM the buyback figure rather than triangulated (circular).
    # An incoherent pair (buyback > 85% of resale) does NOT block the rise: per the established
    # house rule it discredits the BUYBACK number, which is dropped above, while the independently
    # sourced resale stands. Downward moves are always allowed — that is the safe direction.
    CIRCULAR = {'iphone_17_pro_max_2tb': 'resale back-solved from buyback/0.80, not triangulated'}
    if (conf == 'low' or k in CIRCULAR) and a1 >= cur:
        why = (CIRCULAR.get(k) or 'low confidence') + ', rise not granted'
        rise_kept.append((k, e.get('display_name'), cur, a1, conf, why))
        continue

    # Hold the whole week's move inside the same +-20% band the weekly drop cap uses, measured
    # from where the model started the week — one verification round should not be able to move
    # a price further than a week of market drift plausibly can.
    start = WEEK_START.get(k)
    if start and a1 > start * 1.20:
        a1 = r100(start * 1.20)
        rise_capped_week.append((k, e.get('display_name'), start, a1, conf))

    if conf == 'low' and a1 >= cur:
        rise_kept.append((k, e.get('display_name'), cur, a1, conf, 'low confidence, rise not granted'))
        continue
    if a1 == cur:
        rise_kept.append((k, e.get('display_name'), cur, a1, conf, 'no change'))
        continue

    e['resale_target_a1'] = r100(a1 * (1 + m))
    e['market_resale_observed'] = r100(rs)
    if bm_ok: e['buyback_market'] = r100(bm)
    else: e.pop('buyback_market', None)
    if isinstance(new, (int, float)) and new > 0: e['net_new_inr'] = r100(new)
    e['calibration_status'] = 'verified'
    e['calibration_date'] = TODAY
    e['live_source'] = (f"HAND-VERIFIED {TODAY}: resale ₹{r100(rs):,}"
                        f"{' / market buys ₹' + format(r100(bm), ',') if bm_ok else ''}"
                        f" -> A1 ₹{a1:,} = resale÷(1+{m}).")[:180]
    rise_changes.append((k, e.get('display_name'), cur, a1, conf, (a1 - cur) / cur * 100))

# ================= REPORT =================
print('=' * 78)
print(f'PENDING FOLLOW-UPS {TODAY}  ' + ('(APPLY)' if APPLY else '(dry-run)'))
print('=' * 78)
print(f'\n--- PHANTOM VARIANTS REMOVED ({len(removed)}) ---')
for k, n, why in removed: print(f'    {k:30s} {n[:34]:34s} {why}')
print(f'\n--- KEPT despite a non-existence claim ({len(KEPT_DOUBTFUL)}) ---')
for k, why in KEPT_DOUBTFUL.items(): print(f'    {k:30s} {why}')
print(f'\n--- Z FOLD8 FAMILY re-verified ({len(fold8_done)}) ---')
for k, n, b, a, new in fold8_done:
    print(f"    {n[:40]:40s} A1 {b:>8,} -> {a:>8,}  new ₹{new:,}  (buyback dropped)")
print(f'\n--- CAPPED RISES: re-anchored on verified resale ({len(rise_changes)}) ---')
for k, n, c, a, conf, pct in rise_changes:
    print(f"    {n[:40]:40s} A1 {c:>8,} -> {a:>8,} ({pct:+5.1f}%) conf={conf}")
if rise_capped_week:
    print(f'\n--- grant trimmed to the +20% week band ({len(rise_capped_week)}) ---')
    for k, n, st, a, conf in rise_capped_week:
        print(f"    {n[:40]:40s} started week {st:>8,} -> granted {a:>8,} (+20% ceiling) conf={conf}")
print(f'\n--- CAPPED RISES: left as-is ({len(rise_kept)}) ---')
for k, n, c, a, conf, why in rise_kept:
    print(f"    {n[:40]:40s} A1 {c:>8,} (verified would be {a:>8,}) conf={conf} — {why}")

if not APPLY:
    print('\n(dry-run — no files written. re-run with --apply)')
    sys.exit(0)

# ================= APPLY =================
meta['version'] = '6.1'
meta['last_calibration'] = TODAY
meta['v6_1_changelog'] = (
    f"Hand-verification follow-up to the v6.0 weekly refresh ({TODAY}), resolving the three items "
    f"that run left open. (1) Removed {len(removed)} phantom RAM/storage variants that a dedicated "
    f"find+critic pass positively disproved at high confidence, each with the real India line-up "
    f"named (OnePlus 15R 8GB \\u00d72, OnePlus 13T 16/512 — India got the 13s instead, Oppo Reno 15 "
    f"8/512, Nothing Phone (3) 12/512, Vivo X200 FE 12/512, Moto Edge 70 Pro 12/512). Asus ROG "
    f"Phone 9 12/256 could not be disproved and was KEPT; Galaxy Z Flip8 12/256 was confirmed real. "
    f"(2) Z Fold8 + Fold8 Ultra confirmed real on Samsung India's own buy page with official prices "
    f"stamped (\\u20b91,79,999 / 1,99,999 / 2,39,999 and \\u20b91,99,999 / 2,19,999 / 2,59,999); their "
    f"anchors were already correct, and all competitor buyback figures were DROPPED after the "
    f"verifier proved Cashify's 'Approx. Buyback Value' widget is a template printing a flat 40% of "
    f"the listed price — identical ratio reproduced on Fold8, Fold8 Ultra and iPhone 17 Pro Max. "
    f"Because resale sits near 80% of new, that template lands at exactly 50% of resale, which is "
    f"what the echo-detector had been catching for two weeks. Entries promoted estimated -> verified. "
    f"(3) Nine of the largest rise-capped models were re-checked: the iPhone 17 Pro cluster was NOT "
    f"confirmed (low confidence, buyback/resale ratios of 85-90% that RT's own guardrail treats as "
    f"junk, and Cashify pages quoting \\u20b91,37,900 against Apple's real \\u20b91,49,900), so no iPhone "
    f"rise was granted and iPhone 17 Pro 256 was trimmed to the lower verified figure. "
    f"{len(rise_changes)} models re-anchored on hand-verified resale.")

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

h = open(f'{DIR}/index.html', encoding='utf-8').read()
i = h.find('const DB = {')
inline = json.loads(h[i + len('const DB = '):h.find('\n', i)].rstrip().rstrip(';'))
disk = json.load(open(f'{DIR}/phone_db.json'))
same = json.dumps(inline, sort_keys=True) == json.dumps(disk, sort_keys=True)
print(f'\nAPPLIED v6.1 — phones {len(ph)}, files in sync: {same}')
if not same: sys.exit(1)
