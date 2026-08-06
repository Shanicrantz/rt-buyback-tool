#!/usr/bin/env python3
"""Apply the SCOPED hot-set refresh (449 models) to phone_db.json + inlined DB in index.html.
Only keys present in _updates are touched. Everything else is left byte-identical.
Guardrails: overrides never overwritten (flag divergences), anti-overpay, sanity bands,
refurb-cohort confidence-capped, resale <= 0.90*ceiling. no_live_data hot models left untouched."""
import json, glob, re
DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-08-05'
DEFAULT_MARGIN = {'S':0.18,'A':0.2,'B':0.22,'C':0.25,'D':0.3}
def round100(n): return int(round(n/100.0))*100
ANCHOR_PRIORITY = ['rt_buyback_a1_override','cashify_exchange','resale_target_a1','refurb_retail_anchor_excellent','net_new_inr']
def primary_anchor(e):
    for f in ANCHOR_PRIORITY:
        if f in e: return f
    return None

db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
upd = {}
for fp in sorted(glob.glob(f'{DIR}/_updates/batch_*.json')):
    for u in json.load(open(fp)).get('updates', []):
        if 'key' in u: upd[u['key']] = u

stats = dict(live_applied=0, live_capped=0, live_rejected=0, no_live_left=0,
             overrides_protected=0, overrides_flagged=0, not_in_db=0)
override_reviews = []; big_changes = []; rejected = []

for key, u in upd.items():
    if key not in db:
        stats['not_in_db'] += 1; continue
    entry = db[key]
    anchor = primary_anchor(entry)
    status = u.get('status'); conf = u.get('confidence','low')

    # --- OVERRIDE: never auto-change; flag divergences; restamp only if live-checked ---
    if anchor == 'rt_buyback_a1_override':
        stats['overrides_protected'] += 1
        if status == 'live':
            entry['calibration_date'] = TODAY
        rv = u.get('override_review')
        if isinstance(rv, dict):
            try:
                cur = float(rv.get('current') or entry['rt_buyback_a1_override'])
                sug = float(rv.get('live_suggestion'))
                pct = (sug-cur)/cur*100 if cur else 0
                if abs(pct) >= 10:
                    override_reviews.append({'key':key,'display':entry.get('display_name'),
                        'current':cur,'live_suggestion':sug,'pct_diff':round(pct,1),'source':u.get('source','')})
                    stats['overrides_flagged'] += 1
            except Exception: pass
        continue

    # --- no_live_data hot model: leave entirely untouched (honest) ---
    if status != 'live' or u.get('new_value') is None:
        stats['no_live_left'] += 1; continue

    field = u.get('anchor_field'); nv = u.get('new_value')
    if field != anchor or not isinstance(nv,(int,float)) or nv <= 0:
        stats['no_live_left'] += 1; continue
    old = entry.get(anchor)
    ceiling = u.get('new_price_ceiling')
    eff = float(nv); capped = False; reason = ''; ok = True
    if isinstance(old,(int,float)) and old > 0:
        ratio = nv/old
        if ratio < 0.45:
            ok = False; reason = f'out-of-band low {ratio:.2f}'
        elif anchor == 'refurb_retail_anchor_excellent' and ratio > 1.15:
            if conf == 'low':
                ok = False; reason = f'low-conf inflation {ratio:.2f}'
            else:
                cap = 1.40 if conf == 'high' else 1.25
                if ratio > cap: eff = old*cap; capped = True; reason = f'capped {ratio:.2f}->{cap}'
        elif ratio > 1.7:
            ok = False; reason = f'out-of-band high {ratio:.2f}'
    if ok and isinstance(ceiling,(int,float)) and ceiling > 0:
        cap_ceiling = ceiling*(0.90 if anchor == 'resale_target_a1' else 1.0)
        if eff > cap_ceiling: eff = cap_ceiling; capped = True; reason = (reason+'; ' if reason else '')+f'clamp<=ceiling'
    if not ok:
        rejected.append((key, reason, old, nv)); stats['live_rejected'] += 1
        continue
    newv = round100(eff)
    entry[anchor] = newv
    entry['calibration_status'] = 'verified'
    entry['calibration_date'] = TODAY
    if u.get('source'): entry['live_source'] = u['source'][:160]
    stats['live_applied'] += 1
    if capped: stats['live_capped'] += 1
    if isinstance(old,(int,float)) and old > 0:
        pct = (newv-old)/old*100
        if abs(pct) >= 8: big_changes.append((key, anchor, old, newv, round(pct,1)))

# meta bump (last_calibration -> today: the customer-facing hot models are fresh)
meta['version'] = '5.5'
meta['last_calibration'] = TODAY
meta['v5_5_changelog'] = (f"Hot-set live rate refresh ({TODAY}): 449 high-traffic models (all iPhones + 2023+ "
    f"S/A flagships & premium) live-checked vs Cashify/Amazon/Flipkart. {stats['live_applied']} anchors updated "
    f"(verified); {stats['overrides_protected']} Shane overrides protected ({stats['overrides_flagged']} flagged >10% divergence); "
    f"{stats['live_rejected']} rejected by sanity band; {stats['no_live_left']} no-live-data left unchanged. "
    f"Budget/long-tail (~1777) untouched — on weekly scheduler.")

out = {'_meta': meta}
for k, v in db.items():
    if k != '_meta': out[k] = v
with open(f'{DIR}/phone_db.json','w') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',',':')) + ';'
lines = open(f'{DIR}/index.html').read().split('\n'); rep = 0
for i, ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'):
        lines[i] = ln[:len(ln)-len(ln.lstrip())] + compact; rep += 1
open(f'{DIR}/index.html','w').write('\n'.join(lines))
json.dump(override_reviews, open(f'{DIR}/_review_overrides.json','w'), ensure_ascii=False, indent=2)

big_changes.sort(key=lambda x:-abs(x[4]))
print('=== SCOPED APPLY SUMMARY ===')
for k,v in stats.items(): print(f'  {k}: {v}')
print('index.html DB line replaced:', rep, '| total phones:', len([k for k in out if k!='_meta']))
print(f'\nTop 20 live changes (>=8%):')
for key,f,o,n,pct in big_changes[:20]:
    print(f'  {key:34s} {int(o):>7d} -> {int(n):>7d}  ({pct:+.1f}%)')
print(f'Total changed >=8%: {len(big_changes)} | override flags: {len(override_reviews)} | rejected: {len(rejected)}')
if rejected:
    for k,r,o,n in rejected[:10]: print(f'  REJECT {k}: {r} ({o}->{n})')
