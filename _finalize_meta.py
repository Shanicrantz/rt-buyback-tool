#!/usr/bin/env python3
"""Final metadata pass for the weekly refresh: bump version, stamp last_calibration,
write the dated changelog, refresh market_signals, then write BOTH files in sync and
run the invariant checks. --apply to write; default dry-run."""
import json, sys, re

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-24'
VERSION = '6.2'
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
    f"Weekly brain refresh ({TODAY}). Live market research on 96 high-value/recent models "
    f"(12x8 batches, fetch + adversarial critic, 29 prices corrected by the critic) re-anchored "
    f"{len(changes)} of them ({len(moved)} moved \u22650.5%). A1 = resale\u00f7(1+margin_by_age), caps "
    f"resale\u00d70.92 / new\u00d70.85, week move -20%/+8% asymmetric. "
    f"THREE VERIFICATION PASSES ran on top of the refresh this week, all find+adversarial-refute: "
    f"(1) OUTLIERS \u2014 51 items (33 rises the +8% cap had blocked, 8 collapses, 7 existence claims, "
    f"3 missing prices) were re-researched blind. 15 re-priced, 10 rises rolled back to where they "
    f"started the week (the refuter caught an iPhone 16 256GB quote that was really the 128GB price, "
    f"a Pixel 10a priced off its \u20b949,999 MRP sticker, and three stale net_new_inr ceilings), and 6 "
    f"phantom variants removed on positive line-up evidence: Samsung A57 8/512, Xiaomi 15 Ultra 1TB, "
    f"OnePlus Nord 6 8/128, OnePlus 13R 8/128, Vivo X200 Pro 12/512, Realme GT 7 8/512. A 7th "
    f"(iQOO 15R 12/256) rested on an absence-of-listing argument and was KEPT. "
    f"(2) ANCHOR AUDIT \u2014 47 entries created by earlier gap audits carried suspiciously round new "
    f"prices with resale at exactly 80% of them (a fabricated-estimate signature). The 38 with real "
    f"money at stake were re-sourced: 16 corrected, net \u20b948,200 of buyback removed, headlined by "
    f"Samsung F70 Pro and Infinix Note Edge (round \u20b925-29k \u2018prices\u2019 that were really \u20b919,999-23,999) "
    f"and three Realme 16 Pro variants that were under-anchored. The whole Pixel 11 family was "
    f"re-verified against store.google.com/in and Flipkart and CONFIRMED correct. "
    f"(3) GAP PRICE-CHECK + TIE-BREAK PANEL \u2014 the gap audit\u2019s own prices looked 2-3x their series\u2019 "
    f"historical band, so a 3-lens panel (brand India store / major retailer / India tech press) was "
    f"run on the disputed families. All 9 agents agreed the prices are REAL \u2014 2026 India budget "
    f"pricing has genuinely stepped up (iQOO Z10 \u20b921,999 \u2192 Z11 \u20b934,999; Tecno Pova 7 Pro \u20b919,999 \u2192 "
    f"Pova 8 Pro \u20b949,999; Poco M7 \u20b910,499 \u2192 M8x \u20b920,999). The band heuristic was wrong, not the "
    f"research. {len(added)} launches added (iQOO Z11 x4, Tecno Pova 8 Pro x2, Poco M8x x2, OnePlus 15R "
    f"x2); Lava Virat V1 Pro held back because it is announced but not yet on sale. New-entry tiers are "
    f"now normalised to whatever tier the DB already uses for that series \u2014 the finder had put the "
    f"iQOO Z11 and Tecno Pova 8 Pro in tier B against 14/14 and 22/22 existing C entries, which "
    f"silently changed the margin floor and gave one phone two different margins across its variants."
)

# --- market signals: the Jul-22 Unpacked has happened; the pre-launch haircut rule is spent ---
meta['market_signals'] = {
    'updated': TODAY,
    'resolved': {
        'samsung_z_fold_8__z_flip_8': {
            'event': 'Galaxy Z Fold8 / Fold8 Ultra / Flip8 LAUNCHED in India 2026-07-22. '
                     'Official India pricing confirmed: Fold8 \u20b91,79,999, Fold8 Ultra \u20b91,99,999, '
                     'Flip8 \u20b91,24,999 (12/256).',
            'effect': 'The "successor imminent" pre-launch haircut on Fold7/Flip7 is now SPENT.',
            'confidence': 'high (samsung.com/in + Flipkart, re-verified 2026-08-24)',
        },
        'google_pixel_11_family': {
            'event': 'Pixel 11 / 11 Pro / 11 Pro XL / 11 Pro Fold on sale in India since 2026-08-12. '
                     'Prices re-verified 2026-08-24 on store.google.com/in and Flipkart: Pixel 11 256GB '
                     '\u20b989,999 / 512GB \u20b91,04,999; 11 Pro 256GB \u20b91,19,999 / 512GB \u20b91,34,999; 11 Pro XL '
                     '256GB \u20b91,34,999 / 512GB \u20b91,49,999; 11 Pro Fold 16/512 \u20b91,86,999.',
            'effect': 'The family entered the DB on estimated round numbers; those estimates proved '
                      'accurate to within \u20b91 and the anchors are now first-hand verified.',
            'confidence': 'high (store.google.com/in + Flipkart, 2026-08-24)',
        },
    },
    'india_2026_price_step_up': {
        'event': 'Budget/mid India launch prices stepped up hard through 2026: iQOO Z10 \u20b921,999 \u2192 Z11 '
                 '\u20b934,999 (+59%); Tecno Pova 7 Pro \u20b919,999 \u2192 Pova 8 Pro \u20b949,999 (+150%); Poco M7 5G '
                 '\u20b910,499 \u2192 M8x \u20b920,999 (+100%).',
        'effect': 'A "this price is 2-3x its predecessor, so it must be an MRP" heuristic now produces '
                  'FALSE rejections. Confirmed by a 3-lens panel on 2026-08-24 (9/9 agreement). Verify '
                  'an out-of-band price against the brand India store before rejecting it.',
        'confidence': 'high (brand India stores + Flipkart + India tech press, 2026-08-24)',
    },
    'cashify_buyback_widget_is_fake': {
        'event': 'The "Approx. Buyback Value" on Cashify price pages is a template printing 40% of the '
                 'listed price \u2014 identical on Fold8, Fold8 Ultra and iPhone 17 Pro Max.',
        'effect': 'Never store it as buyback_market. The weekly script now drops any buyback landing on '
                  'exactly 40% of the known new price, alongside the existing 50%-of-resale echo check.',
        'confidence': 'high (verified by hand 2026-08-17)',
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
# sibling. Preferred fix is to level the bigger one UP to the sibling's A1 (never worth less,
# but we do not invent a premium either), bounded by its OWN ceilings — new*0.85 and, when this
# week's research observed a real resale for it, market_resale_observed*0.92.
#
# That upward fix is only valid when the smaller sibling's number is trustworthy. In a weekly
# refresh the common case is the opposite: the big variant was just researched DOWN while the
# small one still carries a stale anchor from an earlier calibration. Levelling up there would
# propagate the stale figure onto fresh research and can push A1 above observed resale — a
# guaranteed loss per unit. So when the raise is blocked (or does not fully clear the
# inversion), resolve it by pulling the SMALLER sibling DOWN to the bigger one's A1 instead.
# Both directions are conservative; RT never ends up paying more than the market supports.
# Shane's hand-set rt_buyback_a1_override entries are never touched in either direction.
def set_a1(e, target):
    """Write `target` A1 onto an entry via whichever anchor field the engine reads. False if none."""
    mg = margin_of(e)
    if e.get('resale_target_a1'):
        e['resale_target_a1'] = int(round(target * (1 + mg) / 100)) * 100
    elif e.get('refurb_retail_anchor_excellent'):
        mf = e.get('market_factor', meta.get('default_market_factor', 0.88))
        e['refurb_retail_anchor_excellent'] = int(round(target * (1 + mg) / mf / 100)) * 100
    else:
        return False
    return True

def ceiling_for(e):
    c = float('inf')
    nn = e.get('net_new_inr')
    if isinstance(nn, (int, float)) and nn > 0: c = min(c, nn * 0.85)
    ob = e.get('market_resale_observed')
    if isinstance(ob, (int, float)) and ob > 0: c = min(c, ob * 0.92)
    return c

inv_fixed, inv_lowered = [], []
for fam, items in fams.items():
    items.sort()
    for i in range(1, len(items)):
        if items[i][2] >= items[i-1][2] - 1: continue
        big_k, big_a1 = items[i][1], items[i][2]
        small_k, small_a1 = items[i-1][1], items[i-1][2]
        big, small = ph[big_k], ph[small_k]

        # 1) try raising the bigger variant, bounded by its own ceilings
        target = min(small_a1, ceiling_for(big))
        if target > big_a1 and not big.get('rt_buyback_a1_override') and set_a1(big, target):
            inv_fixed.append((big_k, round(big_a1), round(a1_of(big))))
            items[i] = (items[i][0], big_k, a1_of(big))
            big_a1 = items[i][2]

        # 2) still inverted -> pull the smaller sibling down to the bigger's A1
        if big_a1 < small_a1 - 1:
            if small.get('rt_buyback_a1_override') or not set_a1(small, big_a1):
                problems['storage_inversion'].append((big_k, round(big_a1), small_k, round(small_a1)))
                continue
            inv_lowered.append((small_k, round(small_a1), round(a1_of(small))))
            items[i-1] = (items[i-1][0], small_k, a1_of(small))
if inv_fixed:
    print(f'  storage inversions — bigger variant raised: {len(inv_fixed)}')
    for k, before, after in inv_fixed: print(f'      {k}: {before:,} -> {after:,}')
if inv_lowered:
    print(f'  storage inversions — stale smaller variant lowered: {len(inv_lowered)}')
    for k, before, after in inv_lowered: print(f'      {k}: {before:,} -> {after:,}')

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
