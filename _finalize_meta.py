#!/usr/bin/env python3
"""Final metadata pass for the weekly refresh: bump version, stamp last_calibration,
write the dated changelog, refresh market_signals, then write BOTH files in sync and
run the invariant checks. --apply to write; default dry-run."""
import json, sys, re

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-30'
VERSION = '6.3'
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

# Real storage variants added to replace removed phantoms (written by _add_siblings_*.py).
# Removing a phantom leaves a hole where a REAL variant should sit, so the two go together:
# without the repair, RT loses a counter-quote on a phone that genuinely walks in.
try:
    _sib = json.load(open(f'{DIR}/_added_siblings_{TODAY}.json'))
except FileNotFoundError:
    _sib = []
if _sib:
    _names = ', '.join(f"{s['name']} (A1 Rs{s['a1']:,})" for s in _sib)
    SIBLING_NOTE = (f"SIBLING REPAIR: removing a phantom leaves a hole where a REAL variant belongs, "
                    f"so the {len(_sib)} real configs the phantoms were standing in for were researched "
                    f"(Opus, research + adversarial refute) and added: {_names}. ")
else:
    SIBLING_NOTE = ("SIBLING REPAIR: the real configs behind the removed phantoms were researched but "
                    "none cleared the evidence bar, so none were added — adding a second phantom to "
                    "replace the first is the worst available outcome. Carried to next week. ")

meta['version'] = VERSION
meta['last_calibration'] = TODAY
meta['pricing_brain'] = ("A1 buyback = resale ÷ (1+margin_by_age), capped at resale×0.92 & new×0.85. "
                         "margin auto-calibrated by phone age from Shane overrides vs REAL resale "
                         "(recent ~10%, oldest ~30%); tier default acts as a floor for C/D so cheap "
                         "phones keep a sane absolute buffer. buyback_market shown as competitiveness "
                         "reference. Refreshed weekly from live resale + buyback research.")
meta[f'v{VERSION.replace(".", "_")}_changelog'] = (
    f"Weekly brain refresh ({TODAY}). Live market research on 96 high-value/recent models "
    f"(12x8 batches, fetch + adversarial critic; the critic corrected 33 prices) re-anchored "
    f"{len(changes)} of them ({len(moved)} moved ≥0.5%). A1 = resale÷(1+margin_by_age), caps "
    f"resale×0.92 / new×0.85, week move -20%/+8% asymmetric. {len(added)} India launches added "
    f"(Realme P4s 5G x3, Tecno Spark Go 3 Pro x2, Lava Virat V1 Pro 5G, Infinix Note 60 Pro "
    f"Pininfarina Edition). The Lava Virat V1 Pro was correctly HELD BACK last week as announced-"
    f"but-not-on-sale and is now genuinely shipping — the hold worked as intended. "
    f"OUTLIER VERIFICATION (run on Opus this week, find + adversarial-refute over 26 items: 14 "
    f"capped rises, 5 collapses, 3 existence claims, 4 missing prices): 16 lowered, 2 rolled back "
    f"to week-start, 8 removed. NOTABLE — every single one of the 14 rises that the +8% cap had "
    f"blocked was then REFUSED or LOWERED by independent research; not one survived as a genuine "
    f"rise. The asymmetric cap is doing real work, and the systematic upward bias of the weekly "
    f"research is re-confirmed rather than assumed. "
    f"PHANTOM VARIANTS REMOVED (8) — each hand-verified against the brand's own India line-up "
    f"before deletion, never on an absence-of-listing argument: Oppo Find X9 12/512 (India ships "
    f"12/256 + 16/512 only), iQOO Neo 10 Pro 12/512 (no Neo 10 Pro sold in India at all), Nothing "
    f"Phone 3a Pro 12/512 (tops out at 12/256), Oppo Reno 13 8/512 (8/128 + 8/256 only; the 12/512 "
    f"belongs to the Reno13 Pro), Pixel 10 Pro 16/1TB (real global SKU, never sold in India), Poco "
    f"F7 Ultra 12/512 (512GB pairs only with 16GB), Vivo V50 8/512 (512GB pairs only with 12GB), "
    f"Realme 14 Pro+ 8/512 (512GB pairs only with 12GB). ALL EIGHT share one signature: a 512GB or "
    f"1TB tier paired with the WRONG RAM size. "
    f"ROOT-CAUSE FINDING: the phantom-variant bug and the round-number-price fabrication signature "
    f"are the SAME failure — a past gap audit invented a next-storage-tier variant and priced it "
    f"by extrapolation, which is why 5 of the 8 phantoms carried prices like Rs35,000 / Rs43,000 / "
    f"Rs90,000. Two follow-ups: (a) _add_gaps.py was rounding net_new_inr to the nearest Rs100, "
    f"manufacturing the very round-number signature the audit hunts for (Rs34,999 stored as "
    f"Rs35,000) — fixed, and this week's 7 new entries carry exact prices; (b) 7 surviving entries "
    f"had their net_new_inr corrected against brand primary sources, headlined by Oppo Find X9 "
    f"12/256 (stored Rs82,000, really Rs74,999) and both Vivo V50 trims (both stored Rs38,000, "
    f"really Rs34,999 / Rs36,999). No A1 was riding a corrected ceiling, so nothing RT pays moved; "
    f"ceilings that ROSE were applied without letting any A1 follow them up. "
    f"233 round-price entries remain DB-wide, but 0 of them currently bind an A1 — latent hygiene, "
    f"not a live pricing error, and many are merely Rs1 rounding artifacts of the bug just fixed. "
    f"{SIBLING_NOTE}"
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
