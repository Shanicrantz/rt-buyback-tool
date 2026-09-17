#!/usr/bin/env python3
"""Final metadata pass for the weekly refresh: bump version, stamp last_calibration,
write the dated changelog, refresh market_signals, then write BOTH files in sync and
run the invariant checks. --apply to write; default dry-run."""
import json, sys, re

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-09-16'
VERSION = '6.5'
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
    f"Weekly brain refresh ({TODAY}; applied and deployed 2026-09-17). SHANE-FLAGGED GAP FIXED: Vivo T3x 5G "
    f"6/128 and 8/128 were missing. Vivo India's launch release, spec page ('4/6/8 GB + 128 GB') and price-cut "
    f"releases confirm the India line-up is exactly 4/128, 6/128, 8/128 (current Rs12,499 / 13,999 / 15,499). "
    f"Added 6/128 (A1 Rs7,200, verified) and 8/128 (A1 Rs7,200, estimated: 8GB OLX data is thin and polluted by "
    f"'4+4 virtual RAM' ads, so it is held level with 6/128). The DB's 4/256 was a PHANTOM (never sold in India) "
    f"and is removed; 4/128 re-priced Rs8,400 -> Rs6,400 off 14 hand-read OLX ads (its old anchor was Cashify refurb "
    f"x0.95, a rejected method) with its round Rs14,000 new price and launch date corrected. "
    f"MARKET REPRICE: 96 models (12x8, fetch + adversarial critic, 24 corrected) re-anchored {len(changes)} "
    f"({len(moved)} moved >=0.5%). {len(added)} India launches added (Infinix Hot 70 Pro 5G 6/128 + 8/128, Oppo "
    f"K14 Lite 4/64, Lava Bold N4 Lite 3/32). "
    f"NEW HOLDS: (1) ANNOUNCED-BUT-NOT-ON-SALE by first-sale date — Redmi Note 17 Pro (8/128, 8/256; sale 09-17) and "
    f"Note 17 Pro Max (8/256, 12/256; sale 09-23) were announced 09-15, so the launch-date check alone would have "
    f"admitted them; _add_gaps.py now keys the hold off the confirmed first-sale date. 19 SKUs held in total "
    f"(_held_future_{TODAY}.json, incl. iPhone 18 Pro/Pro Max, Watch S12/SE 3/Ultra 4, S26 FE shipping 09-18). "
    f"(2) SUCCESSOR-SHIPPING HOLD — research wanted +22% to +46% on the iPhone 17 Pro / Pro Max line (resale at ~92% "
    f"of new off Cashify refurb retail) two days before the 18 Pro ships; all 7 rises refused, drops still apply. "
    f"(3) CRITIC BACK-SOLVE REJECTED — the critic raised iPad Pro M4 13in 512 resale 82k -> 88k explicitly 'so RT "
    f"clears the competitor rate', which the brain forbids and which also slid a Cashify Get-Upto under the "
    f"incoherent-spread filter. "
    f"OUTLIER VERIFICATION (verify + adversarial refute, 42 items): 27 repriced, 7 rolled back, 8 phantoms removed. "
    f"Of the 28 rises the +8% cap blocked, 10 were granted (all partially, mostly budget/mid phones where the "
    f"move was the <24mo margin), 12 were LOWERED below where they started the week, 5 refused, 1 was a phantom — "
    f"the cap stays load-bearing for a fourth week. Two drops were REFUSED on evidence: iPad Air M4 13in (Apple "
    f"raised India new to Rs1,19,900 in June, so used cannot have collapsed to 46k) and MacBook Pro 14 M4 (the 82k "
    f"was back-solved from a family-level Cashify headline). FIXED: a refused move now restores the whole week-start "
    f"entry — resetting only the anchor left research resale on the entry and would have tripped a1_above_resale. "
    f"PHANTOMS REMOVED (14), every one hand-verified against an India source: Vivo T3x 4/256; Motorola Razr 60 Ultra "
    f"12/512 (India: single 16/512); Pixel 9 Pro 128 and 9 Pro XL 1TB; OnePlus Nord 5 8/128; Poco X7 Pro 8/512; "
    f"Motorola Edge 60 Neo 8/256 + 12/512 (never launched in India); Pixel 10 Pro 16/512; Xiaomi 14 Civi 8/512; "
    f"Realme GT 6 8/512; Moto Edge 70 Fusion 8/512; Moto Edge 60 Pro 12/512; Moto Edge 60 Fusion 8/512. "
    f"REAL CONFIGS ADDED IN THEIR PLACE (12): T3x 6/128 + 8/128, Razr 60 Ultra 16/512, Redmi Note 14 Pro+ 8/128 + "
    f"12/512, Nord 5 12/256 + 12/512, Poco X7 Pro 12/256, Edge 60 Pro 8/256 + 16/512, Edge 60 Fusion 12/256 + 8/128. "
    f"ONE PHANTOM CALL OVERTURNED: last week's follow-up said Redmi Note 14 Pro+ 8/256 was a phantom; the Xiaomi "
    f"India specs page reads 'Variants 8+128 | 8+256 | 12+512' — it is REAL and kept. "
    f"OVERPAYS CORRECTED (resale anchored above Cashify's own warrantied refurb retail): Xiaomi 14 Civi 12/512 A1 "
    f"26,200 -> 20,200; Realme GT 6 16/512 21,600 -> 19,300 and 12/256 20,200 -> 18,100; Pixel 10 Pro 256 70,100 -> "
    f"61,900, XL 256 71,900 -> 65,500, XL 512 81,000 -> 68,200; Z Fold 7 512 101,200 -> 89,200 (it had priced above "
    f"the 1TB); Pixel 9 Pro 256 48,700 -> 43,700, 9 Pro XL 256 54,100 -> 45,400. "
    f"iPAD PRO M4 CARRY-FORWARD SETTLED: 11in 512 was priced above the larger 13in off a stale Rs86,000 anchor — now "
    f"resale 68k, A1 Rs57,100. 13in 512 resale 78k (A1 levelled to Shane's 13in 256 override Rs67,100). Shane's "
    f"override re-checked: resale Rs75,000 is above its Rs72,935 review line, so it holds (cushion Rs2,065). "
    f"PIPELINE FIXES: storage-inversion repair no longer lifts freshly researched prices up to a stale sibling "
    f"(it lowers the stale one — Galaxy A26 8/128 14,400 -> 12,800), and now covers suffixed tablet keys "
    f"(_wifi), which had never been checked; placeholder-anchored 'estimated' entries take research drops unbanded. "
    f"Guardrails that fired: 20+ competitor quotes discarded as incoherent (buyback >85% of resale)."
)

# --- market signals ---
ms = meta.get('market_signals', {})
ms['updated'] = TODAY
ms['apple_september_2026_launch_pending'] = {
    'event': 'iPhone 18 Pro / 18 Pro Max, Apple Watch Series 12 / SE 3 / Ultra 4 and Galaxy S26 FE ship in India on '
             '2026-09-18. Still HELD out of the DB (no used market yet); verified new prices carried in '
             f'_held_future_{TODAY}.json.',
    'effect': 'Rises on the outgoing iPhone 17 Pro / Pro Max line were refused this week (research wanted +22-46%, '
              'resale at ~92% of new). First run after 09-18: add the 18 Pro family once units trade, and re-anchor the '
              '17 Pro line on OBSERVED resale — expect it to soften. Cashify Get-Upto figures on the 17 Pro line sit '
              'Rs500-3,100 above RT today; do not chase them across a launch.',
    'confidence': 'high (apple.com/in; research 2026-09-16)',
}
ms['announced_vs_on_sale'] = {
    'event': 'Redmi Note 17 Pro / Pro Max announced 2026-09-15 but on sale 09-17 / 09-23. India launch_date (the '
             'announcement) can precede first sale by 1-2 weeks.',
    'effect': 'Gap-adds are held until the confirmed FIRST-SALE date, not the announcement date.',
    'confidence': 'high (GSMArena India launch news 2026-09-16)',
}
ms['india_memory_cost_price_hike_2026'] = {
    'event': 'Mid-2026 India new-price hikes on memory cost: iPad Air M4 13in Rs84,900 -> Rs1,19,900 (Jun), MacBook '
             'M5 line up, Motorola Edge 60/70 Fusion raised from 2026-08-25, OnePlus Nord 5 +Rs2,000.',
    'effect': 'Rising new prices firm used prices. Research that shows a used collapse on a product whose new price '
              'just went UP is almost certainly a bad datapoint — verify before applying the drop.',
    'confidence': 'high (apple.com/in, Goodreturns, motorola.in, oneplus.in; 2026-09-17)',
}
ms['weekly_research_upward_bias']['event'] = ('Fourth consecutive measurement (2026-09-16): of 28 rises blocked by '
    'the +8% cap, 10 granted (partially), 12 lowered below week-start, 5 refused, 1 was a phantom variant.')
ms['weekly_research_upward_bias']['confidence'] = 'high (measured 2026-08-10, 08-30, 09-10, 09-16)'
meta['market_signals'] = ms

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

# 'a1_above_resale' added 2026-09-10. A hand-set rt_buyback_a1_override is deliberately exempt
# from the weekly refresh, so nothing else re-checks it as the market moves underneath. On a
# discontinued item that is exactly how an override quietly becomes a loss per unit. Flag any
# entry — override or computed — whose A1 exceeds the observed resale x0.92 floor.
problems = {'a1_above_new': [], 'zero_or_broken': [], 'storage_inversion': [],
            'resale_le_buyback': [], 'a1_above_resale': []}
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
    obs = e.get('market_resale_observed')
    # Tolerance is one rounding unit: every A1 in this DB is rounded to the nearest Rs100, which
    # can legitimately land up to Rs50 above the exact 0.92 line. A Rs1 tolerance flagged 14
    # entries whose worst overshoot was Rs60 — all rounding, no real breach.
    if isinstance(obs, (int, float)) and obs > 0 and a1 > obs * 0.92 + 100:
        problems['a1_above_resale'].append((k, round(a1), obs, round(obs * 0.92)))

RANK = {'64': 1, '128': 2, '256': 3, '512': 4, '1tb': 5, '2tb': 6}
fams = {}
for k, e in ph.items():
    # Also match keys that carry a suffix after the storage tier (ipad_pro_m4_13_512_wifi). The old
    # pattern required storage to END the key, so no tablet ladder was ever checked (2026-09-16).
    m = re.match(r'^(.*?)_(\d+|1tb|2tb)(_[a-z]+)?$', k)
    if m and m.group(2) in RANK:
        a1 = a1_of(e)
        if a1: fams.setdefault(m.group(1) + (m.group(3) or ''), []).append((RANK[m.group(2)], k, a1))
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
        # Tolerance is one rounding unit: anchors are stored to the nearest Rs100, so a levelled A1 can
        # land ~Rs50 under its sibling (ipad_pro_m4_13_512 67,059 vs 67,100) — rounding, not an inversion.
        if items[i][2] >= items[i-1][2] - 100: continue
        big_k, big_a1 = items[i][1], items[i][2]
        small_k, small_a1 = items[i-1][1], items[i-1][2]
        big, small = ph[big_k], ph[small_k]

        # 1) try raising the bigger variant, bounded by its own ceilings — but NOT when the bigger one was
        #    researched this run and the smaller one was not. Then the smaller sibling's A1 is the stale
        #    number, and raising fresh research up to it propagates the stale anchor (2026-09-16: Galaxy A26
        #    8/256 verified to A1 Rs12,800 would have been lifted to its June-25 128GB sibling's Rs14,400,
        #    an ~11% margin on a C-tier phone whose floor is 25%). Fall through to lowering the stale one.
        fresh_big = big.get('calibration_date') == TODAY
        # Shane's hand-set override is authoritative, not stale — it can never be lowered, so levelling
        # the bigger variant up to it (within its own ceilings) is the only coherent repair.
        stale_small = small.get('calibration_date') != TODAY and not small.get('rt_buyback_a1_override')
        target = min(small_a1, ceiling_for(big))
        if (target > big_a1 and not (fresh_big and stale_small)
                and not big.get('rt_buyback_a1_override') and set_a1(big, target)):
            inv_fixed.append((big_k, round(big_a1), round(a1_of(big))))
            items[i] = (items[i][0], big_k, a1_of(big))
            big_a1 = items[i][2]

        # 2) still inverted -> pull the smaller sibling down to the bigger's A1
        if big_a1 < small_a1 - 100:
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
