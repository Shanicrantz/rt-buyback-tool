#!/usr/bin/env python3
"""Apply the 2026-09-16 carry-forward research (_pending/cf_final_*.json, verify + adversarial refute),
after HAND verification of every removal against an India-specific source.

  * Vivo T3x 5G — Shane flagged 6/128 + 8/128 missing. India line-up is 4/128, 6/128, 8/128 only.
  * Phantom follow-ups from 2026-09-10 — removed only with positive India line-up evidence, and each
    removal is paired with adding the real config it was standing in for.
  * Pixel 9 Pro / 9 Pro XL, Redmi Note 14 Pro+, Razr 60 Ultra — resale re-priced from hand-read OLX pulls.

Same economics as the weekly script: A1 = resale/(1+margin), margin_by_age with the tier default as a
floor for C/D, capped at resale x0.92 and new x0.85. Rises need triangulated medium/high evidence;
drops apply in full. --apply writes both files; default dry-run.
"""
import json, sys
DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-09-16'
APPLY = '--apply' in sys.argv
def r100(n): return int(round(n / 100.0)) * 100

db = json.load(open(f'{DIR}/phone_db.json')); meta = db['_meta']
ph = {k: v for k, v in db.items() if k != '_meta'}
MA, TIER_DEF = meta['margin_by_age'], meta['default_margins_by_tier']

def months(ld):
    try: y, mo = map(int, ld.split('-')[:2]); return (2026 - y) * 12 + (9 - mo)
    except Exception: return None
def margin_for(tier, ld):
    a = months(ld); b = '<24mo' if (a is None or a < 24) else '24-36mo' if a < 36 else '36-54mo' if a < 54 else '54mo+'
    m = MA[b]
    if tier in ('C', 'D'): m = max(m, TIER_DEF.get(tier, 0.25))
    return round(m, 3)
def a1_of(e):
    mg = e.get('target_margin');  mg = TIER_DEF.get(e.get('tier'), 0.22) if mg is None else mg
    if e.get('rt_buyback_a1_override'): return e['rt_buyback_a1_override']
    if e.get('resale_target_a1'): return e['resale_target_a1'] / (1 + mg)
    r = e.get('refurb_retail_anchor_excellent')
    if not r and e.get('refurb_retail_anchor_fair'): r = e['refurb_retail_anchor_fair'] * meta.get('fair_to_excellent_multiplier', 1.18)
    if r: return r * e.get('market_factor', meta.get('default_market_factor', 0.88)) / (1 + mg)
    return None
def price(resale, new, m):
    a1 = min(resale / (1 + m), resale * 0.92)
    if new: a1 = min(a1, new * 0.85)
    return r100(a1)

# ---- REMOVALS: each hand-verified 2026-09-17 against an India-specific source (not an agent's say-so) ----
REMOVE = {
    'vivo_t3x_5g_4_256': "Vivo India newsroom price release lists only 4/128 Rs12,499, 6/128 Rs13,999, 8/128 Rs15,499; Vivo India spec page '4/6/8 GB + 128 GB'. No 256GB ever sold in India.",
    'moto_razr_60_ultra_12_512': "Business Standard 2025-05-13: India launched a SINGLE 16GB/512GB variant at Rs99,999; Motorola India store catalogue carries one storage option '16GB/512GB'.",
    'google_pixel_9_pro_128': "GSMArena India pre-order news + Gadgets360 India: Pixel 9 Pro sold in India as a single 16GB/256GB at Rs1,09,999; 128GB is a global SKU.",
    'google_pixel_9_pro_xl_16_1tb': "GSMArena India launch table + Gadgets360/Smartprix India: Pixel 9 Pro XL India variants are 16/256 (Rs1,24,999) and 16/512 (Rs1,39,999) only; Cashify 1TB sell page 404.",
}
# ---- ADDS: the real configs (Shane-flagged T3x gap + the configs the phantoms stood in for) ----
ADD = [
    # key, display, tier, launch, new (current official India price), resale, triangulated&conf>=medium
    ('vivo_t3x_5g_6_128', 'Vivo T3x 5G 6/128GB', 'C', '2024-04-17', 13999, 9000, True,
     'OLX India 129-ad pull hand-classified: clean 6/128 n=22, median ask 9,500 -> ~8,550 sold; boxed clean ~9,000'),
    ('vivo_t3x_5g_8_128', 'Vivo T3x 5G 8/128GB', 'C', '2024-04-17', 15499, 9000, False,
     'OLX 8/128 thin (n=7) and polluted by 4+4 virtual-RAM ads; median ask 9,000 -> held level with 6/128, not scaled by the new-price gap'),
    ('moto_razr_60_ultra_16_512', 'Motorola Razr 60 Ultra 16/512GB', 'S', '2025-05-13', 99999, 50000, True,
     'All 15 OLX India ads read 2026-09-16, ask -10% to sold, A1-adjusted median Rs50,000; Cashify Get-Upto 45,740 is a ceiling (91% of resale), not stored'),
    ('redmi_note_14_pro_plus_5g_8_128', 'Redmi Note 14 Pro+ 5G 8/128GB', 'B', '2024-12-09', 28999, 18000, False,
     'OLX India API pull hand-classified (damaged/near-new/relists excluded); Xiaomi India store Rs28,999'),
    ('redmi_note_14_pro_plus_5g_12_512', 'Redmi Note 14 Pro+ 5G 12/512GB', 'B', '2024-12-09', 33999, 22500, False,
     'OLX 12/512 clean n=22 hand-classified; Xiaomi India store Rs33,999; Cashify Get-Upto 20,790 is a ceiling (92% of resale), not stored'),
]
# ---- RE-PRICE existing real keys: key -> (resale, new, triangulated&conf>=medium, launch_date fix or None, method) ----
REPRICE = {
    'vivo_t3x_5g_4_128': (8000, 12499, True, '2024-04-17', 'OLX clean 4/128 n=14 hand-classified, median ask 8,500 -> ~8,000 boxed; old anchor was Cashify refurb x0.95 (rejected method)'),
    'redmi_note_14_pro_plus_5g_8_256': (20500, 30999, False, None, "REAL (Xiaomi India specs 'Variants 8+128 | 8+256 | 12+512'; store Rs30,999) — 2026-09-10 phantom note was WRONG. OLX hand-classified resale 20,500"),
    'google_pixel_9_pro_256': (52000, 109999, True, None, 'OLX API pull: 9 Pro 16/256 clean n=13, median ask 59,000 -> ~53,100 sold; dealer asks lower; round new Rs1,05,000 corrected'),
    'google_pixel_9_pro_xl_16_256': (54000, 124999, True, None, 'OLX API pull: XL 16/256 clean n=33, median ask 60,000 -> 54,000 sold'),
    'google_pixel_9_pro_xl_16_512': (58000, 139999, False, None, 'OLX XL 16/512 thin (n~7); priced as 256GB resale + conservative storage premium'),
}

log = []
for k, why in REMOVE.items():
    if k in ph: log.append(('REMOVE', k, ph[k].get('display_name'), why[:110]))
    elif APPLY: pass
for key, name, tier, ld, new, rs, tri, method in ADD:
    if key in ph: log.append(('SKIP-EXISTS', key, name, '')); continue
    m = margin_for(tier, ld); a1 = price(rs, new, m)
    e = {'display_name': name, 'tier': tier, 'launch_date': ld, 'discontinued': False,
         'net_new_inr': new, 'resale_target_a1': r100(a1 * (1 + m)), 'target_margin': m,
         'market_resale_observed': rs,
         'calibration_status': 'verified' if tri else 'estimated', 'calibration_date': TODAY,
         'live_source': f"CARRY-FORWARD {TODAY} (verify+refute, removals hand-checked): resale ₹{rs:,} -> A1 ₹{a1:,} = resale÷(1+{m}). {method}"[:180]}
    ph[key] = e
    log.append(('ADD', key, name, f'A1 ₹{a1:,} (resale {rs:,}, new {new:,}, m={m}, {e["calibration_status"]})'))
for key, (rs, new, tri, ld_fix, method) in REPRICE.items():
    e = ph.get(key)
    if e is None: log.append(('MISSING', key, '', '')); continue
    if ld_fix: e['launch_date'] = ld_fix
    cur = a1_of(e); m = margin_for(e.get('tier'), e.get('launch_date', ''))
    a1 = price(rs, new, m)
    if cur and a1 > cur and not tri:
        a1, note = r100(cur), 'rise refused (not triangulated) — held'
    else:
        note = 'repriced'
    e['resale_target_a1'] = r100(a1 * (1 + m)); e['target_margin'] = m
    e['net_new_inr'] = new; e['market_resale_observed'] = rs
    e.pop('buyback_market', None)          # no real sell-flow quote obtainable for any of these
    e['calibration_status'] = 'verified' if tri else 'estimated'; e['calibration_date'] = TODAY
    e['live_source'] = f"CARRY-FORWARD {TODAY}: resale ₹{rs:,} -> A1 ₹{a1:,} = resale÷(1+{m}) [{note}]. {method}"[:180]
    log.append(('REPRICE', key, e.get('display_name'), f"A1 {r100(cur) if cur else None} -> {a1:,} [{note}]"))

# iPad Pro M4 13" 256 — Shane's override is observation-only: record the fresh resale, never move the override.
ip = ph.get('ipad_pro_m4_13_256_wifi')
if ip:
    ip['market_resale_observed'] = 75000
    ip['override_last_review'] = (f"{TODAY}: independent resale Rs75,000 (band 74-80k, OLX dealer asks + Cashify/Cashkr) is above the "
                                  "Rs72,935 review line — override Rs67,100 holds; cushion only Rs2,065, re-check in 2-3 weeks.")
    log.append(('OBSERVE', 'ipad_pro_m4_13_256_wifi', ip.get('display_name'), 'resale 75,000 > review line 72,935 — override holds'))

for row in log: print(f'  {row[0]:12s} {row[1]:36s} {row[2] or "":34s} {row[3]}')
if not APPLY:
    print('\n(dry-run — no files written)'); sys.exit(0)
for k in REMOVE: ph.pop(k, None)
json.dump([{'key': k, 'reason': w} for k, w in REMOVE.items()], open(f'{DIR}/_removed_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)
json.dump([{'key': a[0], 'name': a[1], 'a1': price(a[5], a[4], margin_for(a[2], a[3]))} for a in ADD],
          open(f'{DIR}/_added_siblings_{TODAY}.json', 'w'), ensure_ascii=False, indent=1)
out = {'_meta': meta}; out.update(ph)
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
lines = open(f'{DIR}/index.html').read().split('\n'); n = 0
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'): lines[i] = ln[:len(ln) - len(ln.lstrip())] + compact; n += 1
assert n == 1, n
open(f'{DIR}/index.html', 'w').write('\n'.join(lines))
print(f'\nAPPLIED: -{len(REMOVE)} phantoms, +{len(ADD)} real configs, {len(REPRICE)} repriced. phones={len(ph)}')
