#!/usr/bin/env python3
"""Weekly refresh 2026-07-20: apply live rate updates + new launches, enforce guardrails, write both files.

Policy (per scheduled-task spec):
  - rt_buyback_a1_override: NEVER auto-changed. Divergences >10% -> _review_overrides.json.
  - live update: write to the entry's EXISTING anchor field only; sanity band 0.45x-1.7x; anti-overpay ceilings.
  - no_live_data: leave value AND calibration_date untouched (scoped refresh -- do not claim freshness we lack,
    and 14 days of drift is noise; matches v4.9/v5.0 precedent of no mass rewrite).
  - additions: new India launches, resale_target_a1 anchored, resale <= 0.90 x new price.
  - storage monotonicity + sibling-premium cap enforced after merge.
"""
import json, glob, os, re, sys
from datetime import date

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY = '2026-07-20'
LAST_CAL = '2026-07-06'
NEW_VERSION = '5.4'

DEFAULT_MARGIN = {'S': 0.18, 'A': 0.20, 'B': 0.22, 'C': 0.25, 'D': 0.30}
RT_PREMIUM = {'S': 0.08, 'A': 0.10, 'B': 0.12, 'C': 0.14, 'D': 0.16}
DEFAULT_MARKET_FACTOR = 0.88

def round100(n):
    return int(round(n / 100.0)) * 100

ANCHOR_PRIORITY = ['rt_buyback_a1_override', 'cashify_exchange', 'resale_target_a1',
                   'refurb_retail_anchor_excellent', 'net_new_inr']

def primary_anchor(e):
    for f in ANCHOR_PRIORITY:
        if f in e:
            return f
    return None

def compute_a1(e):
    """Mirror of computeA1 in index.html (modes 1-4)."""
    tier = e.get('tier')
    margin = e.get('target_margin', DEFAULT_MARGIN.get(tier, 0.22))
    if e.get('rt_buyback_a1_override'):
        return round100(e['rt_buyback_a1_override'])
    if e.get('cashify_exchange'):
        prem = e.get('rt_premium_over_cashify', RT_PREMIUM.get(tier, 0.08))
        return round100(e['cashify_exchange'] * (1 + prem))
    if e.get('resale_target_a1'):
        return round100(e['resale_target_a1'] / (1 + margin))
    refurb = e.get('refurb_retail_anchor_excellent')
    if not refurb and e.get('refurb_retail_anchor_fair'):
        refurb = e['refurb_retail_anchor_fair'] * 1.18
    if refurb:
        mf = e.get('market_factor', DEFAULT_MARKET_FACTOR)
        return round100(refurb * mf / (1 + margin))
    return 0

# ---------------- load ----------------
db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
phones = {k: v for k, v in db.items() if k != '_meta'}
orig_overrides = {k: v['rt_buyback_a1_override'] for k, v in phones.items()
                  if 'rt_buyback_a1_override' in v}

upd = {}
files = sorted(glob.glob(f'{DIR}/_updates_20/batch_*.json'))
parse_errors = []
for fp in files:
    try:
        obj = json.load(open(fp))
        for u in obj.get('updates', []):
            if 'key' in u:
                upd[u['key']] = u
    except Exception as ex:
        parse_errors.append((os.path.basename(fp), str(ex)))

additions = []
if os.path.exists(f'{DIR}/_additions_20.json'):
    additions = json.load(open(f'{DIR}/_additions_20.json'))

stats = dict(live_applied=0, live_capped=0, live_rejected=0, untouched_no_data=0,
             overrides_protected=0, overrides_flagged=0, added=0, add_skipped=0,
             storage_fixed=0)
override_reviews = []
big_changes = []
rejected = []
capped_list = []
add_skips = []

# ---------------- PART A: rate updates ----------------
for key, u in upd.items():
    entry = phones.get(key)
    if entry is None:
        continue
    anchor = primary_anchor(entry)

    if anchor == 'rt_buyback_a1_override':
        stats['overrides_protected'] += 1
        rv = u.get('override_review')
        if isinstance(rv, dict):
            try:
                cur = float(rv.get('current') or entry['rt_buyback_a1_override'])
                sug = float(rv.get('live_suggestion'))
                pct = (sug - cur) / cur * 100 if cur else 0
                if abs(pct) >= 10:
                    override_reviews.append({
                        'key': key, 'display': entry.get('display_name'),
                        'current': cur, 'live_suggestion': sug,
                        'pct_diff': round(pct, 1),
                        'source': (u.get('source') or '')[:300],
                        'flagged_on': TODAY,
                        'note': rv.get('note', ''),
                    })
                    stats['overrides_flagged'] += 1
            except Exception:
                pass
        continue

    if anchor is None or anchor == 'net_new_inr':
        continue

    old = entry.get(anchor)
    if not (u.get('status') == 'live' and u.get('new_value') is not None
            and u.get('anchor_field') == anchor):
        stats['untouched_no_data'] += 1
        continue

    nv = float(u['new_value'])
    conf = u.get('confidence', 'low')
    if nv <= 0:
        stats['untouched_no_data'] += 1
        continue

    eff, capped, reason, band_ok = nv, False, '', True
    if isinstance(old, (int, float)) and old > 0:
        ratio = nv / old
        if ratio < 0.45:
            band_ok, reason = False, f'out-of-band low {ratio:.2f}'
        elif ratio > 1.7:
            band_ok, reason = False, f'out-of-band high {ratio:.2f}'
        elif anchor == 'refurb_retail_anchor_excellent' and ratio > 1.15:
            # budget/discontinued cohort inflates upward (agents anchor to OLX ASKING prices)
            if conf == 'low':
                band_ok, reason = False, f'low-conf inflation {ratio:.2f}'
            else:
                cap = 1.40 if conf == 'high' else 1.25
                if ratio > cap:
                    eff, capped = old * cap, True
                    reason = f'capped {ratio:.2f}->{cap:.2f} ({conf})'

    ceiling = u.get('new_price_ceiling')
    if band_ok and isinstance(ceiling, (int, float)) and ceiling > 0:
        cap_ceiling = ceiling * (0.90 if anchor == 'resale_target_a1' else 1.0)
        if eff > cap_ceiling:
            eff, capped = cap_ceiling, True
            reason = (reason + '; ' if reason else '') + f'clamped to ceiling {int(ceiling)}'

    if not band_ok:
        rejected.append((key, reason, old, nv))
        stats['live_rejected'] += 1
        continue

    newv = round100(eff)
    if newv <= 0:
        stats['untouched_no_data'] += 1
        continue
    entry[anchor] = newv
    entry['calibration_status'] = 'verified'
    entry['calibration_date'] = TODAY
    if u.get('source'):
        entry['live_source'] = u['source'][:200]
    stats['live_applied'] += 1
    if capped:
        stats['live_capped'] += 1
        capped_list.append((key, anchor, old, newv, nv, reason))
    if isinstance(old, (int, float)) and old > 0:
        pct = (newv - old) / old * 100
        if abs(pct) >= 8:
            big_changes.append((key, anchor, old, newv, round(pct, 1)))

# ---------------- PART B: new launches ----------------
seen_names = {v.get('display_name', '').lower().strip() for v in phones.values()}
for a in additions:
    key = a['key']
    if key in phones:
        add_skips.append((key, 'key already exists'))
        stats['add_skipped'] += 1
        continue
    name = a.get('display_name', '').lower().strip()
    if name in seen_names:
        add_skips.append((key, f"duplicate display_name '{a.get('display_name')}'"))
        stats['add_skipped'] += 1
        continue
    resale = float(a['resale_target_a1'])
    newp = a.get('new_price_inr')
    if isinstance(newp, (int, float)) and newp > 0:
        if resale > 0.90 * newp:                       # anti-overpay
            resale = 0.90 * newp
    resale = round100(resale)
    if resale <= 0:
        add_skips.append((key, 'non-positive resale'))
        stats['add_skipped'] += 1
        continue
    e = {
        'display_name': a['display_name'],
        'tier': a['tier'],
        'discontinued': bool(a.get('discontinued', False)),
        'launch_date': a['launch_date'],
        'resale_target_a1': resale,
        'calibration_status': 'estimated',
        'calibration_date': TODAY,
        'live_source': a.get('live_source', '')[:200],
    }
    cat = a.get('category', 'phone')
    if cat and cat != 'phone':
        e['category'] = cat
    if isinstance(newp, (int, float)) and newp > 0:
        e['net_new_inr'] = int(newp)
    # final invariant: implied A1 must be < new price
    if isinstance(newp, (int, float)) and newp > 0 and compute_a1(e) >= newp:
        add_skips.append((key, 'implied A1 >= new price'))
        stats['add_skipped'] += 1
        continue
    phones[key] = e
    seen_names.add(name)
    stats['added'] += 1

# ---------------- PART C: storage monotonicity + sibling premium ----------------
# Key convention (same as _fix_storage.py): base = key minus last token, last token = storage.
# RAM-differing variants land in separate bases -- conservative, and consistent with prior runs.
SRANK = {'32': 32, '64': 64, '128': 128, '256': 256, '512': 512, '1tb': 1024, '2tb': 2048}

def srank(k):
    return SRANK.get(k.split('_')[-1].lower(), 0)

def base_of(k):
    return '_'.join(k.split('_')[:-1])

def set_a1(e, target):
    """Set the entry's primary anchor so engine A1 == target. Returns field, or None for override."""
    t = e.get('tier')
    m = e.get('target_margin', DEFAULT_MARGIN.get(t, 0.22))
    mf = e.get('market_factor', DEFAULT_MARKET_FACTOR)
    if 'rt_buyback_a1_override' in e:
        return None
    if 'cashify_exchange' in e:
        p = e.get('rt_premium_over_cashify', RT_PREMIUM.get(t, 0.08))
        e['cashify_exchange'] = round100(target / (1 + p)); return 'cashify_exchange'
    if 'resale_target_a1' in e:
        e['resale_target_a1'] = round100(target * (1 + m)); return 'resale_target_a1'
    if 'refurb_retail_anchor_excellent' in e:
        e['refurb_retail_anchor_excellent'] = round100(target * (1 + m) / mf)
        return 'refurb_retail_anchor_excellent'
    return None

groups = {}
for k in phones:
    if srank(k) > 0:
        groups.setdefault(base_of(k), []).append(k)

storage_fixes = []
for g, ks in groups.items():
    var = sorted(ks, key=srank)
    if len(var) < 2:
        continue
    prev_k, prev_a1 = None, None
    for k in var:
        e = phones[k]
        cur = compute_a1(e)
        if prev_a1 is None or cur <= 0 or prev_a1 <= 0:
            prev_k, prev_a1 = k, cur
            continue
        if primary_anchor(e) == 'rt_buyback_a1_override':
            prev_k, prev_a1 = k, cur          # never touch Shane's rates
            continue
        target = None
        if cur < prev_a1:                      # inversion: bigger storage priced lower
            target = round100(prev_a1 * 1.08)
        elif cur > prev_a1 * 1.15:             # excessive premium over next-lower sibling
            target = round100(prev_a1 * 1.15)
        if target and target != cur:
            fld = set_a1(e, target)
            if fld:
                e['calibration_date'] = TODAY
                new_a1 = compute_a1(e)
                storage_fixes.append((k, fld, cur, new_a1, prev_k, prev_a1))
                stats['storage_fixed'] += 1
                cur = new_a1
        prev_k, prev_a1 = k, cur

# ---------------- PART D: invariants ----------------
problems = []
for k, e in phones.items():
    a1 = compute_a1(e)
    if a1 <= 0:
        problems.append((k, 'zero/broken A1'))
    nn = e.get('net_new_inr')
    if isinstance(nn, (int, float)) and nn > 0 and a1 >= nn:
        problems.append((k, f'A1 {a1} >= new price {nn}'))
    r = e.get('resale_target_a1')
    if isinstance(nn, (int, float)) and nn > 0 and isinstance(r, (int, float)) and r > 0.9001 * nn:
        problems.append((k, f'resale {r} > 0.90 x new {nn}'))

changed_overrides = [k for k, v in orig_overrides.items()
                     if phones.get(k, {}).get('rt_buyback_a1_override') != v]

# ---------------- write ----------------
if '--dry-run' in sys.argv:
    print('DRY RUN — no files written')
else:
    meta['version'] = NEW_VERSION
    meta['last_calibration'] = TODAY
    changelog = ''
    if os.path.exists(f'{DIR}/_changelog_20.txt'):
        changelog = open(f'{DIR}/_changelog_20.txt').read().strip()
    meta[f"v{NEW_VERSION.replace('.', '_')}_changelog"] = changelog
    out = {'_meta': meta}
    out.update(phones)
    with open(f'{DIR}/phone_db.json', 'w') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    compact = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
    html_path = f'{DIR}/index.html'
    src = open(html_path).read()
    lines = src.split('\n')
    replaced = 0
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith('const DB = {'):
            indent = ln[:len(ln) - len(ln.lstrip())]
            lines[i] = indent + compact
            replaced += 1
    assert replaced == 1, f'expected exactly 1 DB line, replaced {replaced}'
    new_src = '\n'.join(lines)
    # app shell must be untouched apart from that one line
    assert len(src.split('\n')) == len(new_src.split('\n')), 'line count changed'
    with open(html_path, 'w') as fh:
        fh.write(new_src)
    print('index.html DB line replaced:', replaced)

    if override_reviews:
        prev = []
        if os.path.exists(f'{DIR}/_review_overrides.json'):
            try:
                prev = json.load(open(f'{DIR}/_review_overrides.json'))
            except Exception:
                prev = []
        json.dump(override_reviews, open(f'{DIR}/_review_overrides.json', 'w'),
                  ensure_ascii=False, indent=2)
        print(f'_review_overrides.json rewritten: {len(override_reviews)} entries (was {len(prev)})')

# ---------------- report ----------------
print('\n=== APPLY SUMMARY (2026-07-20) ===')
print('batch files:', len(files), '| keys with updates:', len(upd), '| additions proposed:', len(additions))
if parse_errors:
    print('PARSE ERRORS:', parse_errors[:10])
for k, v in stats.items():
    print(f'  {k}: {v}')
print('total phones:', len(phones))
print('overrides auto-changed (MUST be 0):', len(changed_overrides), changed_overrides[:5])
print('invariant problems (MUST be 0):', len(problems))
for p in problems[:15]:
    print('   !', p)

big_changes.sort(key=lambda x: -abs(x[4]))
print(f'\n--- Top 30 price changes (>=8%), {len(big_changes)} total ---')
for key, field, old, new, pct in big_changes[:30]:
    print(f'  {key:44s} {field:32s} {int(old):>7d} -> {int(new):>7d}  ({pct:+.1f}%)')

if capped_list:
    print(f'\n--- Capped by guardrail ({len(capped_list)}) ---')
    for key, f_, old, new, raw, reason in capped_list[:15]:
        print(f'  {key}: {old} -> {new} (raw {raw}) [{reason}]')

if rejected:
    print(f'\n--- Sanity-rejected ({len(rejected)}) ---')
    for key, reason, old, new in rejected[:15]:
        print(f'  {key}: {reason} (old {old} vs proposed {new})')

if storage_fixes:
    print(f'\n--- Storage-consistency fixes ({len(storage_fixes)}) ---')
    for k, f_, cur, new_a1, prev_k, prev_a1 in storage_fixes[:20]:
        print(f'  {k}: {f_} {cur}->{new_a1} (sibling {prev_k} A1 {prev_a1})')

if add_skips:
    print(f'\n--- Additions skipped ({len(add_skips)}) ---')
    for k, r in add_skips[:20]:
        print(f'  {k}: {r}')

print(f'\nOverride divergences flagged: {len(override_reviews)}')
for r in override_reviews[:15]:
    print(f"  {r['key']}: {int(r['current'])} vs live {int(r['live_suggestion'])} ({r['pct_diff']:+.1f}%)")
