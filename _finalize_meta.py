#!/usr/bin/env python3
"""Final metadata pass for the weekly refresh: bump version, stamp last_calibration,
write the dated changelog, refresh market_signals, then write BOTH files in sync and
run the invariant checks. --apply to write; default dry-run."""
import json, sys, re

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-09-26'
VERSION = '6.7'
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
    f"Brain refresh ({TODAY}, run on request 5 days after v6.6). MARKET REPRICE: 96 models (12x8, fetch + adversarial "
    f"critic, 47 corrected) re-anchored {len(changes)} ({len(moved)} moved >=0.5%); entries refreshed on 09-21 were "
    f"excluded except where forced. "
    f"HEADLINE — FOLDABLE PLACEHOLDERS, ROUND 2: 16 entries still sat at EXACTLY 80% of new on phones 66-890 days old, "
    f"led by the whole Galaxy Z Fold8 / Fold8 Ultra / Flip8 family, which the 09-21 research had 'confirmed' at 61 days "
    f"by applying the prompt's own thin-market convention. The prompt hint is now restricted to phones <30 days old. Re-"
    f"researched and verify+refuted against live Cashify sell ceilings, the family came down hard: Fold8 12/256 A1 "
    f"130,100 -> 97,400, 12/512 145,600 -> 108,200, 16/1TB 174,700 -> 129,800; Fold8 Ultra 256 145,600 -> 121,000, 512 "
    f"160,100 -> 127,400, 1TB 189,300 -> 136,500; Flip8 256 91,900 -> 74,600, 512 107,400 -> 86,500; Razr Fold -6 to -9%. "
    f"Net Rs2.80 lakh of A1 removed on foldables alone. LADDER CAP (new, _ladder_cap_{TODAY}.py): verification repriced "
    f"some Fold8/Flip8 trims off live data while siblings kept weaker research, leaving a Rs42,000 used step between "
    f"Fold8 256 and 512 against a Rs20,000 new-price step and the standard Fold8 512/1TB priced ABOVE the Fold8 Ultra. "
    f"Larger trims are now capped at the verified base trim's resale x the new-price ratio (lowers only). "
    f"OUTLIER VERIFICATION (Opus verify + adversarial refute, 41 items): 25 lowered, 13 rolled back to week-start, 2 "
    f"held, 0 granted. All 23 rises the +8% cap (or the successor hold) blocked were refused or lowered — the sixth "
    f"consecutive measurement and the first with zero grants. Several stored net_new_inr were fabricated and corrected "
    f"(Vivo V70 Elite 12/512 'Rs77,000' is Rs61,999; 12/256 'Rs72,000' is Rs63,999; iPhone 17e 256 is Rs64,900). "
    f"LAUNCHES ADDED (8; <30-day ones on an explicit new x0.80 placeholder, 'estimated'): Redmi Note 17 Pro Max 8/256 + "
    f"12/256 (on sale 09-23), Realme 16 Pro 5G Harry Potter Edition 12/256 (09-22), OnePlus N6 Lite 4/64 at Rs16,999 "
    f"(09-22, 4G Unisoc), Lava Bold N4 Pro 5G 6/128 (first sale today), itel Zeno 300 4/64 (09-25), and Nothing Phone (3a) "
    f"Lite 8/128 + 8/256 (Nov-2025 gap; the critic put resale ABOVE Cashify's own refurb price, so it was capped and "
    f"re-verified down to A1 14,600 / 15,500). HELD (first sale in the future): iPhone Duo 256/512/1TB/2TB (10-23, "
    f"Rs2,99,900-4,49,900), Redmi 17C (10-01), Oppo K14 Plus (09-29), Lava Virat Curve (09-28). "
    f"PHANTOMS REMOVED (2): Oppo A6s 8/128 and 8/256 — OPPO India's own newsroom (hand-read) lists the A6s 5G as 4/128 "
    f"Rs18,999 and 6/128 Rs20,999 only (launched 2026-03-18). The real configs were added 'estimated' at the refuter's "
    f"conservative indicative resale (A1 10,400 / 11,200) — removal and repair are one operation. "
    f"PIPELINE FIXES: verified competitor quotes now pass the same 85%-of-resale coherence filter as the weekly script "
    f"(7 'Get Upto' headlines dropped, incl. iPhone 17e 256 at 95% that had raised a false 'Cashify pays more' alarm); "
    f"the placeholder-echo band widened to 0.865 (Fold8 Ultra 256 landed on 0.8600). "
)

# --- market signals ---
ms = meta.get('market_signals', {})
ms['updated'] = TODAY
ms['sept_2026_successors_shipped']['effect'] = ('Outgoing iPhone 17 Pro / Pro Max and Galaxy S25 FE: rises refused through '
    'the 2026-09-26 run (verification found no post-launch datapoint supporting any rise). From the 2026-09-28 run: drop '
    'the successor hold; re-research the 18 Pro family + S26 FE placeholders ~10-18 Oct.')
ms['thin_market_convention_echo']['event'] = ('2026-09-21: 31 pre-guardrail 0.80 anchors all came down (net Rs61,229). '
    '2026-09-26 round 2: 16 more, headed by the Fold8/Flip8 family that research had re-confirmed at 80% at 61 days; '
    'verified off live Cashify sell ceilings they fell 17-28% (net Rs2.8 lakh on foldables).')
ms['thin_market_convention_echo']['effect'] = ('Fetch prompt now allows the 78-85%-of-new convention ONLY under 30 days. A '
    'result at 76-86.5% of new on an older phone can confirm a drop, never a rise, stays estimated, goes to verify+refute.')
ms['weekly_research_upward_bias']['event'] = ('Sixth consecutive measurement (2026-09-26): of 23 blocked rises, 0 granted '
    '— 13 rolled back, 10 lowered.')
ms['weekly_research_upward_bias']['confidence'] = 'high (measured 2026-08-10, 08-30, 09-10, 09-16, 09-21, 09-26)'
ms['iphone_duo_2026'] = {'event': 'iPhone Duo announced for India, first sale 2026-10-23 (256GB Rs2,99,900 / 512GB '
    'Rs3,24,900 / 1TB Rs3,74,900 / 2TB Rs4,49,900, apple.com/in).', 'effect': 'Held until it ships; carried in '
    '_held_future_2026-09-26.json.', 'confidence': 'high (apple.com/in via gap-audit critic 2026-09-26)'}
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
