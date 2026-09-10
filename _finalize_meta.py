#!/usr/bin/env python3
"""Final metadata pass for the weekly refresh: bump version, stamp last_calibration,
write the dated changelog, refresh market_signals, then write BOTH files in sync and
run the invariant checks. --apply to write; default dry-run."""
import json, sys, re

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-09-10'
VERSION = '6.4'
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
    f"(12x8 batches, fetch + adversarial critic; the critic corrected 29 prices) re-anchored "
    f"{len(changes)} of them ({len(moved)} moved >=0.5%). A1 = resale/(1+margin_by_age), caps "
    f"resale x0.92 / new x0.85, week move -20%/+8% asymmetric. {len(added)} India launches added. "
    f"OUTLIER VERIFICATION (Opus, verify + adversarial refute over 46 items in 10 batches: 29 "
    f"capped rises, 7 collapses, 1 existence claim, 3 missing prices, 6 placeholder resales): "
    f"34 repriced, 3 rolled back to week-start, 4 removed. "
    f"HEADLINE — of the 29 rises the +8% cap had blocked, exactly ONE survived independent "
    f"re-research (Vivo V70 FE 8/128, +Rs600). 23 were LOWERED and 3 rolled back outright. That "
    f"is the third consecutive week in which essentially no capped rise proved genuine; the "
    f"asymmetric cap is not a safety margin, it is load-bearing. "
    f"NEW GUARDRAIL 1 — ANNOUNCED-BUT-NOT-SHIPPING HOLD. The gap audit proposed 15 models whose "
    f"India launch_date is still in the FUTURE (2026-09-18): iPhone 18 Pro and 18 Pro Max (8 "
    f"storage SKUs), Apple Watch Series 12 / SE 3 / Ultra 4 (5), Samsung Galaxy S26 FE (2). Their "
    f"official India prices are genuinely verified against apple.com/in, but a phone that has not "
    f"shipped has NO used market: nobody can walk into RT with a used unit, and the critics "
    f"themselves recorded resale as a 'new x0.80 placeholder'. Adding them would plant a "
    f"fabricated anchor that next week's refresh would treat as a real prior. All 15 are held, "
    f"with their verified new prices carried forward in _held_future_2026-09-10.json so the next "
    f"run need not re-research them. The DB has never contained a future-dated entry and still "
    f"does not. Precedent: the Lava Virat V1 Pro was held on the same grounds and added once it "
    f"shipped. "
    f"NEW GUARDRAIL 2 — PLACEHOLDER-RESALE DETECTION. 18 of this week's 20 gap-adds came back "
    f"with resale at EXACTLY 80% of new. That is the gap-audit prompt's own fallback for a phone "
    f"too new to have a used market — legitimate on a six-day-old launch, an unresearched guess "
    f"on anything older. All 18 are now recorded as 'estimated' rather than 'verified', and the 6 "
    f"old enough to actually trade used were routed straight into the verification pass. Every "
    f"one of the 6 came back LOWER: Xiaomi 17T 12/512 Rs51,000->Rs38,200, 17T 12/256 "
    f"Rs47,300->Rs35,000, Tecno Pova Curve 2 8/256 Rs21,800->Rs15,600, 8/128 Rs20,500->Rs14,400, "
    f"Tecno POP X 6/128 Rs11,400->Rs7,700, 4/128 Rs9,800->Rs6,900. The 80% fallback overpays by "
    f"25-30% on a phone with a real used market. "
    f"PHANTOM VARIANTS REMOVED (4) — each re-verified BY HAND against an India-specific source "
    f"before deletion, never on an agent's say-so: Google Pixel 9 Pro 512GB (India received the "
    f"9 Pro in a SINGLE 256GB trim at Rs1,09,999; 128/512/1TB are international-only), Infinix "
    f"Zero Flip 8/256 (India shipped the sole 8/512 config at Rs49,999), Redmi Note 14 Pro+ 8/512 "
    f"(India ships 8/128 at Rs30,999 and 12/512 at Rs35,999 — 512GB pairs only with 12GB), "
    f"Motorola Razr 60 Ultra 12/256 (India launched a single 16/512 trim at Rs99,999). "
    f"ONE REMOVAL OVERRULED. The refuter also called realme_15_5g_12_512 a phantom on the grounds "
    f"that realme.com/in does not list it. GSMArena's India-specific page lists Internal as "
    f"'128GB 8GB RAM, 256GB 8GB RAM, 256GB 12GB RAM, 512GB 12GB RAM' — the variant is REAL and the "
    f"entry was KEPT. Deleting a real variant costs RT a counter-quote on every walk-in, so "
    f"positive evidence beats an absence argument. This is why removals are hand-checked. "
    f"FOLLOW-UPS RECORDED, NOT ACTED ON (_phantom_followup_2026-09-10.json): hand-checking the 4 "
    f"removals exposed 3 further suspected phantoms that research had NOT flagged — Razr 60 Ultra "
    f"12/512 (both DB trims carry 12GB RAM; India ships only 16/512), Redmi Note 14 Pro+ 8/256 "
    f"(both DB trims are phantoms), Pixel 9 Pro 128GB — plus the real configs missing behind them "
    f"(Razr 60 Ultra 16/512; Note 14 Pro+ 8/128 and 12/512). They are recorded rather than removed "
    f"or invented, because removal needs hand evidence and an add needs researched resale. "
    f"MEASURED, NOT ASSUMED: the round-number net_new_inr signature was re-scanned DB-wide — 233 "
    f"entries carry a round-thousand new price but 0 of them currently BIND an A1, so no research "
    f"was spent on them. The 512GB/1TB-with-wrong-RAM phantom scan returned only 2 hits, both "
    f"Galaxy Z Fold8 12/512 configs that are genuinely real. Last week's cleanup holds. "
    f"Guardrails that fired during the refresh: 13 competitor quotes discarded as incoherent "
    f"(buyback >85% of resale) and 2 as the Cashify 40%-of-listed-price widget template."
)

# --- market signals ---
meta['market_signals'] = {
    'updated': TODAY,
    'apple_september_2026_launch_pending': {
        'event': 'iPhone 18 Pro / 18 Pro Max, Apple Watch Series 12 / SE 3 / Ultra 4 announced with '
                 'official India pricing on apple.com/in; pre-orders open 12-Sep, SHIPPING 18-Sep-2026. '
                 'iPhone 18 Pro Rs1,64,900 (256GB) to Rs3,14,900 (2TB); 18 Pro Max Rs1,79,900 to '
                 'Rs3,29,900. Samsung Galaxy S26 FE also India-bound, price not yet published.',
        'effect': 'HELD OUT of the DB until units actually ship — an unshipped phone has no used '
                  'market and any resale figure for it is invented. Verified new prices are parked in '
                  '_held_future_2026-09-10.json for the first post-launch run. Separately, expect the '
                  'iPhone 17 / 17 Pro line to soften once the 18 is on shelves; re-anchor on observed '
                  'resale rather than pre-emptively trimming.',
        'confidence': 'high (apple.com/in, fetched 2026-09-10)',
    },
    'weekly_research_upward_bias': {
        'event': 'Third consecutive weekly measurement: of the 29 rises blocked by the +8% cap this '
                 'week, 1 survived independent re-research, 23 were lowered and 3 rolled back.',
        'effect': 'Keep the asymmetric cap. Drops apply in full to -20%; rises are capped at +8% and '
                  'must clear triangulated medium/high confidence before any grant.',
        'confidence': 'high (measured 2026-08-10, 2026-08-30, 2026-09-10)',
    },
    'gap_audit_80pct_resale_fallback': {
        'event': "The gap-audit prompt tells the finder to use resale ~= new x0.80 for a phone with no "
                 "used market yet. Agents apply it to older phones too: 18 of 20 adds came back at "
                 "exactly 0.80, and all 6 that were old enough to trade used verified 25-30% LOWER.",
        'effect': 'Any add landing on exactly 80% of new is recorded as calibration_status=estimated, '
                  'and those older than 90 days are force-routed into the verification pass.',
        'confidence': 'high (measured 2026-09-10)',
    },
    'india_2026_price_step_up': {
        'event': 'Budget/mid India launch prices stepped up hard through 2026: iQOO Z10 Rs21,999 -> Z11 '
                 'Rs34,999 (+59%); Tecno Pova 7 Pro Rs19,999 -> Pova 8 Pro Rs49,999 (+150%); Poco M7 5G '
                 'Rs10,499 -> M8x Rs20,999 (+100%).',
        'effect': 'A "this price is 2-3x its predecessor, so it must be an MRP" heuristic produces '
                  'FALSE rejections. Verify an out-of-band price against the brand India store before '
                  'rejecting it.',
        'confidence': 'high (brand India stores + Flipkart + India tech press, 2026-08-24)',
    },
    'cashify_buyback_widget_is_fake': {
        'event': 'The "Approx. Buyback Value" on Cashify price pages is a template printing 40% of the '
                 'listed price - identical on Fold8, Fold8 Ultra and iPhone 17 Pro Max.',
        'effect': 'Never store it as buyback_market. The weekly script drops any buyback landing on '
                  'exactly 40% of the known new price, alongside the 50%-of-resale echo check. It fired '
                  'twice this week (Tab S10 Ultra, Z Fold6 512GB).',
        'confidence': 'high (verified by hand 2026-08-17)',
    },
    'rule': ('When a successor flagship is confirmed <~4 weeks out, trim outgoing-gen resale anchors 5-10%; '
             'once it actually launches, drop the anticipatory trim and re-anchor on observed resale. '
             'Festival-sale (Prime Day/BBD) lows are a TEMPORARY NET_NEW floor: cap buyback below them, but '
             'revert the anchor to trend after the sale unless it is a confirmed permanent price cut. '
             'NEVER add a model whose India launch_date is still in the future.'),
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
