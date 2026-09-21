#!/usr/bin/env python3
"""Final metadata pass for the weekly refresh: bump version, stamp last_calibration,
write the dated changelog, refresh market_signals, then write BOTH files in sync and
run the invariant checks. --apply to write; default dry-run."""
import json, sys, re

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-09-21'
VERSION = '6.6'
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
    f"Weekly brain refresh ({TODAY}). MARKET REPRICE: 96 models (12x8, fetch + adversarial critic, 29 corrected) "
    f"re-anchored {len(changes)} ({len(moved)} moved >=0.5%). Scope was deliberately re-weighted this week: 58 of the "
    f"96 were forced carry-forwards. "
    f"SUCCESSOR SHIPPED 2026-09-18: iPhone 18 Pro / 18 Pro Max, Apple Watch Series 12 / Ultra 4 and Galaxy S26 FE went on "
    f"sale in India. The outgoing iPhone 17 Pro line was re-anchored on OBSERVED post-launch resale and softened as "
    f"predicted (17 Pro 256 A1 102,800 -> 94,600; 512 -> 101,900; 1TB -> 111,000; Pro Max 256 -> 104,600; 512 -> 112,800; "
    f"1TB -> 121,000; 2TB held at 121,900 after verification refused research's +11% on two Mumbai asking prices). "
    f"Rises on the outgoing generation (17 Pro, S25 FE) stay refused for one more week while the used market settles; "
    f"drops apply. The S25 FE's successor-held rises were instead settled by Opus verify+refute on post-09-18 datapoints "
    f"only: 128 A1 25,400 -> 27,800, 256 29,200 -> 30,500, 512 33,600 -> 32,800 (its July anticipatory trim was for the "
    f"wrong successor). "
    f"LAUNCHES ADDED (19, all first sold on/before today; <30-day ones on an explicit new x0.80 placeholder marked "
    f"'estimated'): iPhone 18 Pro 256/512/1TB/2TB and 18 Pro Max 256/512/1TB/2TB (apple.com/in), Apple Watch Series 12 "
    f"42/46mm and Ultra 4, Galaxy S26 FE 8/256 at Rs79,999 (India ships ONLY that config — the held 128GB was a phantom "
    f"and was rejected), Redmi Note 17 Pro 5G 8/128 + 8/256 (on sale 09-17), Vivo Y31t 5G 4/128, 6/128, 6/256 (on sale "
    f"offline 2026-08-21), and Apple Watch SE 3 40/44mm, which turned out to be a SEPT-2025 model the hold had "
    f"misfiled as a 2026 launch. STILL HELD (first sale in the future): Redmi Note 17 Pro Max (09-23), OnePlus N6 Lite "
    f"(09-22), Realme 16 Pro Harry Potter Edition (09-22), Lava Bold N4 Pro (09-26), Lava Virat Curve (09-28). "
    f"GAPS FILLED BY VERIFY+REFUTE (5): the SE 3 finding exposed that the DB had Series 10 and 12 but no Series 11 or "
    f"Ultra 3 — Apple Watch Series 11 42/46mm (A1 25,000 / 26,400) and Ultra 3 (A1 49,100) added on OLX/dealer "
    f"datapoints; Realme P3 Ultra 12/256 and 8/128 added as the real configs behind a removed phantom. "
    f"PHANTOM REMOVED (1): Realme P3 Ultra 8/512 — India line-up is 8/128, 8/256, 12/256 only, max 256GB (Mobigyaan / "
    f"Zee Biz launch coverage, hand-read; refuter concurred on realme.com/in). "
    f"HEADLINE — CALCIFIED PLACEHOLDERS: a DB-wide scan found 31 entries (mostly the 2026-08-07 gap audit, before the "
    f"placeholder guardrail existed) whose resale was EXACTLY 80% of a round, unverified new price yet stamped "
    f"'verified'. Asked to research them from scratch, the weekly agents mostly handed back the same ~80% 'thin market' "
    f"convention (24 of 31) — so those were held 'estimated', refused any rise, and sent to Opus verify+refute, which "
    f"read real OLX / ORUphones / Cashify datapoints. ALL 31 CAME DOWN: net Rs61,229 of A1 removed, led by OnePlus Pad 2 "
    f"12/256 30,800 -> 18,500 and 8/128 26,700 -> 16,800, iPhone 16e 128 34,600 -> 30,900 (its stored 'new' was a round "
    f"48,000; Apple India's is 59,900), Galaxy S24 256 31,500 -> 28,600, S24 Ultra 512 56,300 -> 53,800. Their round new "
    f"prices were replaced with brand-sourced ones (and 2026 hikes: Moto G37 Power 8/128 now Rs25,999, OnePlus N6x +Rs2,000). "
    f"OUTLIER VERIFICATION (Opus verify + adversarial refute, 53 items): 40 repriced, 4 rolled back, 1 removed, 5 added. "
    f"Of the 11 rises the +8% cap blocked, NONE survived at the capped level: 4 granted smaller (+5 to +7%), 4 LOWERED "
    f"below where they started the week, 3 refused — fifth consecutive week. "
    f"OTHER FINDINGS: research put the iPad Pro M5 11in above the 13in; verification confirmed Apple India's post-hike "
    f"prices (11in 256 Rs1,39,900, 13in 256 Rs1,99,900 — the 13in figure a critic had rejected as a rendering error is "
    f"real) and granted the 11in only resale 85k (A1 77,300); the higher new price was NOT allowed to loosen the stored "
    f"ceiling. S25 Ultra 256 research sat at Cashify refurb retail on a false 'still current generation' premise (the S26 "
    f"Ultra shipped months ago). "
    f"PIPELINE FIXES: (1) outlier 'refuse' on a non-rise item no longer restores week-start (it would have undone "
    f"this week's drops, e.g. Moto G37 Power 4/128 9,840 -> 10,240); (2) a refused rise now restores the week-start entry "
    f"even when A1 did not move, so refuted research never sits on an entry as 'verified'; (3) verification may lower "
    f"net_new_inr or replace a round-number one, but never loosens a trusted ceiling; (4) verify+refute can now ADD a "
    f"missing model on triangulated evidence. "
)

# --- market signals ---
ms = meta.get('market_signals', {})
ms['updated'] = TODAY
ms.pop('apple_september_2026_launch_pending', None)
ms['sept_2026_successors_shipped'] = {
    'event': 'iPhone 18 Pro / 18 Pro Max, Apple Watch Series 12 / Ultra 4 and Galaxy S26 FE on sale in India 2026-09-18 '
             '(S26 FE: single 8/256 config, Rs79,999). Added 2026-09-21 on new x0.80 placeholders, marked estimated.',
    'effect': 'Outgoing iPhone 17 Pro / Pro Max and Galaxy S25 FE: rises refused through the 2026-09-21 run (drops apply); '
              'observed resale softened 3-8% on the 17 Pro line in the first 3 days. From the 2026-09-28 run: drop the '
              'successor hold, and re-research the 18 Pro family + S26 FE once they are ~30 days old (placeholders).',
    'confidence': 'high (apple.com/in, samsung India coverage; research + verification 2026-09-21)',
}
ms['india_memory_cost_price_hike_2026']['event'] = (
    'Mid-2026 India new-price hikes on memory cost: iPad Air M4 13in Rs84,900 -> Rs1,19,900 (Jun); iPad Pro M5 11in 256 '
    'Rs99,900 -> Rs1,39,900 and 13in 256 Rs1,29,900 -> Rs1,99,900 (apple.com/in, read 2026-09-21); Apple Watch SE 3 40mm '
    'Rs25,900 -> Rs29,900; Moto G37 Power 8/128 Rs18,999 -> Rs25,999 (Flipkart); OnePlus N6x +Rs2,000; Motorola Edge '
    '60/70 Fusion raised from 2026-08-25; OnePlus Nord 5 +Rs2,000.')
ms['india_memory_cost_price_hike_2026']['confidence'] = 'high (apple.com/in, Flipkart, Goodreturns, motorola.in, oneplus.in; 2026-09-21)'
ms['thin_market_convention_echo'] = {
    'event': '2026-09-21: 31 pre-guardrail gap-adds carried resale = EXACTLY 80% of a round new price but were stamped '
             'verified. Re-research returned the same ~80% "thin market" convention on 24 of them (phones 1.5-17 months '
             'old). Real OLX/ORU datapoints brought ALL 31 down (net Rs61,229 of A1).',
    'effect': 'A resale at 76-86% of new on a phone older than ~45 days is a convention, not an observation: it may '
              'confirm a drop but never a rise, stays estimated, and goes to verify+refute. The weekly fetch prompt\'s '
              '"<3 months = 78-85% of new" hint is the source — it must not be applied past ~30 days.',
    'confidence': 'high (measured 2026-09-21)',
}
ms['weekly_research_upward_bias']['event'] = ('Fifth consecutive measurement (2026-09-21): of 11 rises blocked by '
    'the +8% cap, 0 survived at the capped level — 4 granted smaller, 4 lowered below week-start, 3 refused.')
ms['weekly_research_upward_bias']['confidence'] = 'high (measured 2026-08-10, 08-30, 09-10, 09-16, 09-21)'
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
