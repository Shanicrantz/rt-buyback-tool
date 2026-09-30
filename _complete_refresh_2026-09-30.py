#!/usr/bin/env python3
"""Resume the saved September research without applying unsupported outliers.

Builds a reviewable candidate by default. --apply installs the validated pair.
Resale anchors remain research values; a movement requiring a synthetic anchor
is held for review. Existing manual rates and new-price ceilings are immutable.
"""
import copy
import hashlib
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TODAY = '2026-09-30'
WORK = ROOT / '_weekly_refresh' / TODAY
BASE = json.loads((ROOT / f'phone_db.backup-{TODAY}.json').read_text())
OLD_HTML = (ROOT / f'index.backup-{TODAY}.html').read_text()
QUOTES = json.loads((WORK / 'baseline_quotes.json').read_text())
DB = copy.deepcopy(BASE)
META = DB['_meta']
VERSION = '6.9'
scope = {x['key'] for x in json.loads((ROOT / f'_scope_{TODAY}.json').read_text())}
held, changes, additions, removals = [], {}, {}, []


def r100(n):
    return math.floor(n / 100 + .5) * 100


def margin(entry):
    try:
        launch = date.fromisoformat(entry['launch_date'])
        now = date.fromisoformat(TODAY)
        months = (now.year - launch.year) * 12 + now.month - launch.month
        months -= now.day < launch.day
    except (KeyError, ValueError):
        return None
    bucket = '<24mo' if months < 24 else '24-36mo' if months < 36 else '36-54mo' if months < 54 else '54mo+'
    value = META['margin_by_age'][bucket]
    # Preserve the established conservative risk buffer for budget phones.
    if entry.get('tier') in ('C', 'D'):
        value = max(value, META['default_margins_by_tier'][entry['tier']])
    return value


def quote(entry):
    return r100(entry['resale_target_a1'] / (1 + entry['target_margin']))


def hold(key, reason):
    held.append({'key': key, 'reason': reason})


def enrich(entry, review, resale):
    entry['resale_target_a1'] = resale
    entry['market_resale_estimate'] = resale
    entry.pop('market_resale_observed', None)
    entry['target_margin'] = margin(entry)
    entry['calibration_date'] = TODAY
    # Market asks, analogs, headline ceilings and retail bounds are estimates of
    # local resale even when the source pages and India variant are verified.
    entry['calibration_status'] = 'estimated'
    entry['market_resale_basis'] = review.get('basis') or 'Reviewed used-market estimate; not a confirmed completed local sale'
    entry['calibration_evidence'] = [{
        'checked_at': TODAY, 'confidence': review.get('confidence', 'low'),
        'basis': entry['market_resale_basis'], 'note': review.get('note', ''),
        'sources': review.get('sources', []),
    }]
    entry['live_source'] = f"BRAIN {TODAY}: reviewed resale estimate Rs{resale:,}; A1 Rs{quote(entry):,}; margin {entry['target_margin']}. Evidence retained."
    entry.pop('buyback_market', None)
    entry.pop('market_buyback_ceiling', None)
    market = review.get('buyback_market')
    ceiling = review.get('buyback_ceiling')
    # Only a verified condition-specific payout is a market offer. A public
    # 'Get Upto' headline remains useful, separately labelled as a ceiling.
    if isinstance(market, (int, float)) and market > 0:
        if review.get('buyback_basis') == 'condition-specific verified quote' and market < resale:
            entry['buyback_market'] = r100(market)
        else:
            ceiling = market
    if isinstance(ceiling, (int, float)) and ceiling > 0:
        entry['market_buyback_ceiling'] = r100(ceiling)
        entry['market_buyback_ceiling_basis'] = 'Public maximum headline; actual payout depends on condition and inspection'
    else:
        entry.pop('market_buyback_ceiling_basis', None)


reviews = []
for part in ('pricing_a', 'pricing_b'):
    reviews.extend(json.loads((WORK / f'{part}.json').read_text())['models'])
assert len(reviews) == len(scope) == 96
assert {x['key'] for x in reviews} == scope
assert len({x['key'] for x in reviews}) == 96
for item in reviews:
    key = item['key']
    old = BASE[key]
    if old.get('rt_buyback_a1_override'):
        hold(key, 'Manual override protected')
        continue
    if item.get('decision') not in ('accept', 'correct'):
        hold(key, item.get('note') or 'Independent review did not support a change')
        continue
    resale = item.get('resale')
    if not isinstance(resale, (int, float)) or resale <= 0 or margin(old) is None:
        hold(key, 'Missing usable resale or age')
        continue
    entry = copy.deepcopy(old)
    enrich(entry, item, r100(resale))
    before, after = QUOTES[key], quote(entry)
    hard = min(entry['resale_target_a1'] * .92, (entry.get('net_new_inr') or float('inf')) * .85)
    if not .8 * before <= after <= 1.2 * before:
        hold(key, f'Weekly 20% guard: proposed A1 {before} -> {after}; prior entry retained')
        continue
    if after > before * 1.08:
        hold(key, f'Conservative rise guard: proposed A1 {before} -> {after} exceeds 8%; prior entry retained')
        continue
    if after > before and item.get('confidence') == 'low':
        hold(key, 'Low-confidence increase refused')
        continue
    if after > hard:
        hold(key, 'Would exceed the hard resale/new ceiling; prior entry retained')
        continue
    DB[key] = entry
    changes[key] = {'key': key, 'name': entry['display_name'], 'old_a1': before, 'new_a1': after,
                    'old_resale': old.get('market_resale_observed', old.get('resale_target_a1')),
                    'new_resale': entry['resale_target_a1'], 'pct': round((after / before - 1) * 100, 2)}

launch = json.loads((WORK / 'launch_review.json').read_text())
repair_from = {x.get('replacement_key'): x['key'] for x in launch.get('removals', []) if x.get('replacement_key')}
for item in launch.get('new_models', []):
    key = item['key']
    if key in DB:
        continue
    if max(item.get('launch_date', ''), item.get('first_sale_date', '')) > TODAY:
        hold(key, 'First sale is in the future')
        continue
    if not item.get('sources') or not item.get('net_new_inr') or not item.get('resale_target_a1'):
        hold(key, 'New variant lacks official price or usable resale evidence')
        continue
    entry = copy.deepcopy(BASE[repair_from[key]]) if key in repair_from else {}
    entry.update({k: item[k] for k in ('display_name', 'tier', 'launch_date', 'net_new_inr')})
    if key in repair_from:
        original = BASE[repair_from[key]]
        assert entry['net_new_inr'] == original['net_new_inr'], 'Repair must retain the authoritative new ceiling'
        assert item['resale_target_a1'] == original['resale_target_a1'], 'Identity repair must not invent a new resale'
    if item.get('category'):
        entry['category'] = item['category']
    if margin(entry) is None:
        hold(key, 'New variant has no valid launch date')
        continue
    enrich(entry, item, r100(item['resale_target_a1']))
    a1 = quote(entry)
    if a1 > min(entry['resale_target_a1'] * .92, entry['net_new_inr'] * .85):
        hold(key, 'New variant exceeds hard ceiling')
        continue
    # Do not create duplicate configurations under cosmetic key/name variants.
    signature = lambda n: re.sub(r'[^a-z0-9]', '', n.lower().replace('+', 'plus'))
    if signature(entry['display_name']) in {signature(v.get('display_name', '')) for k, v in DB.items() if k != '_meta'}:
        hold(key, 'Display-name duplicate')
        continue
    DB[key] = entry
    additions[key] = {'key': key, 'name': entry['display_name'], 'new_a1': a1,
                      'resale': entry['resale_target_a1'], 'launch_date': entry['launch_date']}

for item in launch.get('removals', []):
    key = item['key']
    replacement = item.get('replacement_key')
    if key not in DB or DB[key].get('rt_buyback_a1_override') or not item.get('sources'):
        continue
    if replacement and replacement not in DB:
        hold(key, 'Removal deferred until its real replacement is available')
        continue
    removals.append(item)
    del DB[key]
    changes.pop(key, None)

# Never raise a newly researched variant to a stale sibling. Defer only the
# conflicting change/addition; leave deep-tail and hand-set values intact.
ranks = {'32': 0, '64': 1, '128': 2, '256': 3, '512': 4, '1024': 5, '1tb': 5, '2048': 6, '2tb': 6}
for _ in range(100):
    families = {}
    for key, entry in DB.items():
        m = re.match(r'^(.*?)_(\d+|1tb|2tb)(_[a-z]+)?$', key)
        if m and m[2] in ranks:
            a1 = quote(entry) if key in changes or key in additions else QUOTES[key]
            families.setdefault(m[1] + (m[3] or ''), []).append((ranks[m[2]], key, a1))
    conflicts = []
    for rows in families.values():
        rows.sort()
        for small, big in zip(rows, rows[1:]):
            if big[2] < small[2] - 100:
                conflicts.append((small[1], big[1]))
    # Include tablet screen-size ladders as well as storage ladders.
    for key in DB:
        if key.startswith('ipad_') and '_11_' in key:
            big = key.replace('_11_', '_13_')
            if big in DB:
                qa = quote(DB[key]) if key in changes or key in additions else QUOTES[key]
                qb = quote(DB[big]) if big in changes or big in additions else QUOTES[big]
                if qb < qa - 100:
                    conflicts.append((key, big))
    if not conflicts:
        break
    progressed = False
    for small, big in conflicts:
        for key in (small, big):
            if key in additions:
                del additions[key], DB[key]
            elif key in changes:
                del changes[key]
                DB[key] = copy.deepcopy(BASE[key])
            else:
                continue
            hold(key, f'Storage/size ladder conflict with {small} / {big}; deferred rather than inventing a sibling price')
            progressed = True
    if not progressed:
        raise RuntimeError(f'Unresolved pre-existing ladder conflict: {conflicts}')
else:
    raise RuntimeError('Ladder review did not converge')

# A deferred replacement restores its paired original variant as well.
for item in removals[:]:
    if item.get('replacement_key') and item['replacement_key'] not in DB:
        DB[item['key']] = copy.deepcopy(BASE[item['key']])
        removals.remove(item)
        hold(item['key'], 'Replacement deferred by ladder check; original retained pending review')

moved = [x for x in changes.values() if x['old_a1'] != x['new_a1']]
META['version'] = VERSION
META['last_calibration'] = TODAY
META[f'v{VERSION.replace(".", "_")}_changelog'] = (
    f'Weekly brain refresh {TODAY}, resumed from saved 12 fetch+critic batches (96 entries). '
    f'Independent source review accepted {len(changes)} refreshed entries; {len(moved)} A1 quotes moved. '
    f'Added {len(additions)} shipping India configurations and removed {len(removals)} positively verified phantom configurations. '
    'Only the existing 96-entry rotation was researched; this was not a full-catalogue calibration. '
    'Resale anchors retain reviewed market estimates, age margins and existing C/D risk floors; public maximum buyback headlines '
    'are stored separately from actual condition-specific offers. Asking-price/analog estimates remain estimated. '
    'Unsupported increases, movements outside 20%, hard-ceiling conflicts and storage inversions are deferred with prior entries intact. '
    'Existing manual rates and net_new_inr are unchanged. Includes the unpublished 28-Sep Oppo Find X8 Pro correction. '
    'See _weekly_refresh/2026-09-30/REPORT.md and decisions.json for coverage, evidence and held items.'
)
META.setdefault('market_signals', {})['refresh_2026_09_30'] = {
    'scoped': 96, 'accepted': len(changes), 'quotes_moved': len(moved),
    'new_configs': len(additions), 'removed_phantoms': len(removals),
    'confidence': 'Conservative source-reviewed estimates; not completed local sale confirmations',
}
compact = json.dumps(DB, ensure_ascii=False, separators=(',', ':'))
html, count = re.subn(r'(?m)^(\s*)const DB = \{[^\r\n]*\};[ \t]*$', lambda m: m[1] + 'const DB = ' + compact + ';', OLD_HTML)
assert count == 1
assert json.loads(re.search(r'const DB = (\{[^\r\n]*\});', html)[1]) == DB
candidate = WORK / 'candidate'
candidate.mkdir(parents=True, exist_ok=True)
(candidate / 'phone_db.json').write_text(json.dumps(DB, ensure_ascii=False, indent=2) + '\n')
(candidate / 'index.html').write_text(html)
decisions = {'date': TODAY, 'version': VERSION, 'reviewed': 96, 'refreshed': list(changes.values()),
             'moved': moved, 'added': list(additions.values()), 'removed': removals, 'held': held,
             'held_launches': launch.get('held', []), 'total_entries': len(DB) - 1}
(WORK / 'decisions.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: len(v) if isinstance(v, list) else v for k, v in decisions.items()}))
if '--apply' in sys.argv:
    validation = json.loads((WORK / 'validation.json').read_text())
    assert validation['passed'], 'Candidate validation must pass first'
    for name in ('phone_db.json', 'index.html'):
        assert hashlib.sha256((candidate / name).read_bytes()).hexdigest() == validation['hashes'][name]
        assert (ROOT / name).read_bytes() == (ROOT / (f'phone_db.backup-{TODAY}.json' if name == 'phone_db.json' else f'index.backup-{TODAY}.html')).read_bytes(), 'Live local pair changed concurrently'
    for name in ('phone_db.json', 'index.html'):
        (ROOT / name).write_bytes((candidate / name).read_bytes())
    print('Installed validated candidate pair.')
