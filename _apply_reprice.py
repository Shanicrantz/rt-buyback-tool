#!/usr/bin/env python3
"""Reprice the 100 override models from critic-VERIFIED new + refurb prices.
Buyback A1 is now COMPUTED (not hand-set): resale_target_a1 = refurb_retail x RESALE_MULT,
engine A1 = resale_target / (1 + margin). New price stored as ceiling. Old override stashed
as _override_prev (reversible). Only touches the 100 override keys."""
import json, glob
DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-05'
DEFAULT_MARGIN = {'S':0.18,'A':0.2,'B':0.22,'C':0.25,'D':0.3}
RESALE_MULT = 0.95      # RT resells a used unit at ~95% of certified-refurb retail (tunable)
CEIL_FRAC = 0.92        # resale_target must stay <= 92% of current new price
def round100(n): return int(round(n/100.0))*100

db = json.load(open(f'{DIR}/phone_db.json'))
ver = {}
for f in sorted(glob.glob(f'{DIR}/_ov_updates/verified_*.json')):
    for m in json.load(open(f)).get('models', []):
        ver[m['key']] = m

def a1_from(entry):
    m = entry.get('target_margin', DEFAULT_MARGIN[entry['tier']])
    if 'rt_buyback_a1_override' in entry: return round100(entry['rt_buyback_a1_override'])
    if 'resale_target_a1' in entry: return round100(entry['resale_target_a1']/(1+m))
    if 'refurb_retail_anchor_excellent' in entry: return round100(entry['refurb_retail_anchor_excellent']*entry.get('market_factor',0.88)/(1+m))
    return 0

rows = []; stats = dict(repriced=0, kept_no_refurb=0, not_in_verified=0, clamped=0)
for key, entry in db.items():
    if key == '_meta' or 'rt_buyback_a1_override' not in entry:
        continue
    old_override = entry['rt_buyback_a1_override']
    old_a1 = round100(old_override)
    v = ver.get(key)
    if not v:
        stats['not_in_verified'] += 1
        rows.append((key, old_a1, None, 'NO VERIFIED DATA - kept override')); continue
    refurb = v.get('refurb_price_final'); new = v.get('new_price_final')
    if not isinstance(refurb,(int,float)) or refurb <= 0:
        stats['kept_no_refurb'] += 1
        rows.append((key, old_a1, None, 'no refurb price - kept override')); continue
    margin = entry.get('target_margin', DEFAULT_MARGIN[entry['tier']])
    resale = refurb * RESALE_MULT
    clamped = False
    if isinstance(new,(int,float)) and new > 0 and resale > CEIL_FRAC*new:
        resale = CEIL_FRAC*new; clamped = True; stats['clamped'] += 1
    resale = round100(resale)
    # switch off override -> computed resale-anchored
    entry['_override_prev'] = old_override
    del entry['rt_buyback_a1_override']
    entry['resale_target_a1'] = resale
    entry['refurb_retail_anchor_excellent'] = round100(refurb)   # reference anchor
    if isinstance(new,(int,float)) and new > 0: entry['net_new_inr'] = round100(new)
    entry['calibration_status'] = 'verified'
    entry['calibration_date'] = TODAY
    src = f"Repriced {TODAY} from verified refurb ₹{round100(refurb):,}"
    if new: src += f" / new ₹{round100(new):,}"
    src += f" (critic:{v.get('new_verdict','?')}/{v.get('refurb_verdict','?')}). resale=refurb×{RESALE_MULT}; A1=resale÷(1+{margin}). Was override ₹{old_override:,}."
    entry['live_source'] = src[:180]
    new_a1 = a1_from(entry)
    stats['repriced'] += 1
    rows.append((key, old_a1, new_a1, f"refurb {round100(refurb)}{' new '+str(round100(new)) if new else ' (disc)'}{' CLAMPED' if clamped else ''}"))

# meta
db['_meta']['version'] = '5.7'
db['_meta']['v5_7_changelog'] = (f"OVERRIDE -> COMPUTED repricing ({TODAY}): {stats['repriced']} of 100 hand-set override models "
    f"switched to a CALCULATED buyback derived from critic-verified NEW + REFURB prices (resale_target = refurb x {RESALE_MULT}, "
    f"A1 = resale/(1+margin); new price = ceiling). Adversarial critic re-verified every price to catch wrong new/refurb values. "
    f"Old override stashed as _override_prev (reversible). {stats['clamped']} clamped to <= {int(CEIL_FRAC*100)}% of new; "
    f"{stats['kept_no_refurb']+stats['not_in_verified']} kept on override (no verified refurb).")

out = {'_meta': db['_meta']}
for k, v in db.items():
    if k != '_meta': out[k] = v
json.dump(out, open(f'{DIR}/phone_db.json','w'), ensure_ascii=False, indent=2)
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',',':')) + ';'
lines = open(f'{DIR}/index.html').read().split('\n')
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'):
        lines[i] = ln[:len(ln)-len(ln.lstrip())] + compact
open(f'{DIR}/index.html','w').write('\n'.join(lines))

print('=== REPRICE SUMMARY ===')
for k,v in stats.items(): print(f'  {k}: {v}')
print(f'\nRESALE_MULT={RESALE_MULT} | tunable\n')
print(f'{"MODEL":34s} {"OLD A1":>8s} {"NEW A1":>8s} {"Δ%":>6s}  detail')
diffs=[]
for key, oa, na, det in rows:
    if na is None:
        print(f'{key:34s} {oa:>8d} {"—":>8s} {"—":>6s}  {det}')
    else:
        pct = (na-oa)/oa*100 if oa else 0; diffs.append(pct)
        print(f'{key:34s} {oa:>8d} {na:>8d} {pct:>+6.1f}  {det}')
if diffs:
    import statistics
    print(f'\nΔ across repriced: median {statistics.median(diffs):+.1f}% · mean {statistics.mean(diffs):+.1f}% · max +{max(diffs):.0f}% / {min(diffs):.0f}%')
