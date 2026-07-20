#!/usr/bin/env python3
"""Apply workflow rate updates to phone_db.json + inlined DB in index.html.
Policy:
  - live update: set the entry's existing anchor field to new_value (sanity-banded), mark verified, restamp date.
  - rt_buyback_a1_override: NEVER auto-overwrite (Shane's hand-set). Restamp date; collect divergence flags.
  - no_live_data / missing: depreciation + date refresh fallback (age-based ~11-day decay on static anchors; formula entries just restamped).
  - both files kept byte-identical in DB content.
"""
import json, glob, os, re, sys
from datetime import date

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-06-25'
LAST_CAL = '2026-06-14'

def round100(n):
    return int(round(n / 100.0)) * 100

# ---- age-based 11-day decay (gap between 2026-06-14 and 2026-06-25 ~= 11 days = 11/30 month) ----
GAP = 11.0 / 30.0
def months_since(launch_iso):
    try:
        y, m, d = map(int, launch_iso.split('-'))
        return (2026 - y) * 12 + (6 - m) + (25 - d) / 30.0
    except Exception:
        return None

def monthly_decay(months):
    if months is None: return 0.010
    if months < 12: return 0.030
    if months < 24: return 0.020
    if months < 36: return 0.015
    return 0.010

def decay_factor(launch_iso):
    return 1.0 - monthly_decay(months_since(launch_iso)) * GAP

ANCHOR_PRIORITY = ['rt_buyback_a1_override', 'cashify_exchange', 'resale_target_a1', 'refurb_retail_anchor_excellent', 'net_new_inr']
def primary_anchor(entry):
    for f in ANCHOR_PRIORITY:
        if f in entry:
            return f
    return None

# ---- load DB ----
db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
phones = {k: v for k, v in db.items() if k != '_meta'}

# ---- load updates ----
upd = {}
files = sorted(glob.glob(f'{DIR}/_updates/batch_*.json'))
parse_errors = []
for fp in files:
    try:
        obj = json.load(open(fp))
        for u in obj.get('updates', []):
            if 'key' in u:
                upd[u['key']] = u
    except Exception as e:
        parse_errors.append((os.path.basename(fp), str(e)))

stats = dict(live_applied=0, live_capped=0, live_rejected=0, depreciated=0, formula_restamped=0,
             overrides_protected=0, overrides_flagged=0, missing_update=0, no_anchor=0)
override_reviews = []
big_changes = []   # (key, field, old, new, pct)
rejected = []      # (key, reason, old, new)
capped_list = []   # (key, field, old, capped_new, raw_proposed, reason)

for key, entry in phones.items():
    u = upd.get(key)
    anchor = primary_anchor(entry)

    # --- OVERRIDE entries: never auto-change ---
    if anchor == 'rt_buyback_a1_override':
        entry['calibration_date'] = TODAY
        stats['overrides_protected'] += 1
        if u and isinstance(u.get('override_review'), dict):
            rv = u['override_review']
            try:
                cur = float(rv.get('current') or entry['rt_buyback_a1_override'])
                sug = float(rv.get('live_suggestion'))
                pct = (sug - cur) / cur * 100 if cur else 0
                if abs(pct) >= 10:
                    override_reviews.append({'key': key, 'display': entry.get('display_name'),
                                             'current': cur, 'live_suggestion': sug,
                                             'pct_diff': round(pct, 1), 'source': u.get('source', '')})
                    stats['overrides_flagged'] += 1
            except Exception:
                pass
        continue

    if anchor is None:
        stats['no_anchor'] += 1
        entry['calibration_date'] = TODAY
        continue

    # --- formula-only entries auto-age via launch_date; just restamp ---
    if anchor == 'net_new_inr' and not (u and u.get('status') == 'live' and u.get('anchor_field') == 'net_new_inr' and u.get('new_value')):
        entry['calibration_date'] = TODAY
        stats['formula_restamped'] += 1
        continue

    old = entry.get(anchor)

    # --- LIVE update path ---
    if u and u.get('status') == 'live' and u.get('new_value') is not None:
        field = u.get('anchor_field')
        nv = u.get('new_value')
        conf = u.get('confidence', 'low')
        # must target the SAME field the entry uses (else fall through to depreciation)
        if field == anchor and isinstance(nv, (int, float)) and nv > 0:
            ceiling = u.get('new_price_ceiling')
            band_ok = True
            reason = ''
            eff = float(nv)           # effective value after caps
            capped = False
            if isinstance(old, (int, float)) and old > 0:
                ratio = nv / old
                if ratio < 0.45:
                    band_ok = False; reason = f'out-of-band low {ratio:.2f}'
                elif field == 'refurb_retail_anchor_excellent' and ratio > 1.15:
                    # budget/discontinued cohort had systematic upward bias (OLX-asking anchoring).
                    # Confidence-gated cap prevents over-paying; conservative is the safe error.
                    if conf == 'low':
                        band_ok = False; reason = f'low-conf inflation {ratio:.2f} -> depreciation'
                    else:
                        cap = 1.40 if conf == 'high' else 1.25   # high / medium
                        if ratio > cap:
                            eff = old * cap; capped = True
                            reason = f'capped {ratio:.2f}->{eff/old:.2f} ({conf})'
                elif ratio > 1.7:
                    band_ok = False; reason = f'out-of-band high {ratio:.2f}'
            if band_ok and isinstance(ceiling, (int, float)) and ceiling > 0:
                # resale_target_a1 must sit BELOW new price (>=10%); refurb anchor may equal its retail ceiling
                cap_ceiling = ceiling * (0.90 if field == 'resale_target_a1' else 1.0)
                if eff > cap_ceiling:
                    eff = cap_ceiling; capped = True
                    reason = (reason + '; ' if reason else '') + f'clamped to {int(cap_ceiling)} (ceiling {ceiling})'
            if band_ok:
                newv = round100(eff)
                entry[anchor] = newv
                entry['calibration_status'] = 'verified'
                entry['calibration_date'] = TODAY
                if u.get('source'):
                    entry['live_source'] = u.get('source', '')[:160]
                stats['live_applied'] += 1
                if capped:
                    stats['live_capped'] += 1
                    capped_list.append((key, anchor, old, newv, u.get('new_value'), reason))
                if isinstance(old, (int, float)) and old > 0:
                    pct = (newv - old) / old * 100
                    if abs(pct) >= 8:
                        big_changes.append((key, anchor, old, newv, round(pct, 1)))
                continue
            else:
                rejected.append((key, reason, old, nv))
                stats['live_rejected'] += 1
                # fall through to depreciation fallback

    # --- DEPRECIATION + date refresh fallback ---
    if u is None:
        stats['missing_update'] += 1
    if isinstance(old, (int, float)) and old > 0:
        f = decay_factor(entry.get('launch_date'))
        entry[anchor] = round100(old * f)
    entry['calibration_date'] = TODAY
    stats['depreciated'] += 1

# ---- update meta ----
meta['version'] = '4.5'
meta['last_calibration'] = TODAY
n_live = stats['live_applied']; n_dep = stats['depreciated']
meta['v4_5_changelog'] = (
    f"Full-DB live rate refresh ({TODAY}). All 1566 phones attempted via live India web research "
    f"(Cashify exchange/refurb + Amazon/Flipkart). {n_live} anchors live-updated & marked 'verified'; "
    f"{n_dep} fell back to age-based depreciation + date refresh (no reliable live data, mostly long-tail/budget). "
    f"{stats['formula_restamped']} formula entries restamped (auto-age via launch_date). "
    f"{stats['overrides_protected']} Shane-set rt_buyback_a1_override rates PROTECTED (unchanged); "
    f"{stats['overrides_flagged']} flagged for review (>10% live divergence, see _review_overrides.json). "
    f"{stats['live_rejected']} live values rejected by sanity band (out-of-band/above-ceiling) -> depreciation fallback. "
    f"Prior baseline: v4.4 ({LAST_CAL})."
)

# ---- write phone_db.json ----
out = {'_meta': meta}
out.update(phones)
with open(f'{DIR}/phone_db.json', 'w') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)

# ---- write inlined DB in index.html (single line replace) ----
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
html_path = f'{DIR}/index.html'
lines = open(html_path).read().split('\n')
replaced = 0
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'):
        indent = ln[:len(ln) - len(ln.lstrip())]
        lines[i] = indent + compact
        replaced += 1
with open(html_path, 'w') as fh:
    fh.write('\n'.join(lines))

# ---- review + summary outputs ----
json.dump(override_reviews, open(f'{DIR}/_review_overrides.json', 'w'), ensure_ascii=False, indent=2)

big_changes.sort(key=lambda x: -abs(x[4]))
print('=== APPLY SUMMARY ===')
print('Update files loaded:', len(files), '| keys with updates:', len(upd))
if parse_errors:
    print('PARSE ERRORS:', parse_errors[:10])
for k, v in stats.items():
    print(f'  {k}: {v}')
print('index.html DB line replaced:', replaced)
print('total phones written:', len(phones))
print('\n--- Top 25 live price changes (>=8%) ---')
for key, field, old, new, pct in big_changes[:25]:
    print(f'  {key:42s} {field:30s} {int(old):>7d} -> {int(new):>7d}  ({pct:+.1f}%)')
print(f'\nTotal anchors changed >=8%: {len(big_changes)}')
print(f'Live values capped (budget anti-inflation / ceiling): {len(capped_list)}')
print(f'Override divergences flagged (>=10%): {len(override_reviews)}  -> _review_overrides.json')
if rejected:
    print(f'\n--- Sanity-rejected live values ({len(rejected)}) ---')
    for key, reason, old, new in rejected[:15]:
        print(f'  {key}: {reason} (old {old} vs proposed {new})')
