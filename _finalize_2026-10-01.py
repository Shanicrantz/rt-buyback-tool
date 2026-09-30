#!/usr/bin/env python3
"""Finalize v6.10 (2026-10-01): version, changelog, market signal, invariants, both files in sync.
Invariants are computed on the REAL engine (computeA1 from index.html via _engine_quote.cjs). --apply writes."""
import json, re, sys, subprocess
from _intl_rule import engine_a1

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY, VERSION = '2026-10-01', '6.10'
APPLY = '--apply' in sys.argv
db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
fix = json.load(open(f'{DIR}/_intl_fix_{TODAY}.json'))

meta['version'] = VERSION
meta['last_calibration'] = TODAY
meta['v6_10_changelog'] = (
    "INTERNATIONAL-VARIANT POLICY (Shane, 2026-10-01) on top of v6.9. The 2026-09-30 gap audit (finder + adversarial "
    "critic) showed 12 rows carry RAM/storage configs never sold in India (OnePlus 11 8/256 + 8/512, 11R 8/256, 12 12/512, "
    "13 12/512, 13R 8/256, Nord 3 8/256, Nord CE 3 8/256, Poco M7 5G 4/128, Vivo Y39 5G 4/128 + 6/128, Oppo Reno 14 "
    "8/512). Shane's call: do not delete — imported units walk in. They stay quotable, relabelled '(International)', "
    "flagged international/intl_sibling/intl_discount, priced A1 = min(0.90 x A1 of the nearest India config, prior A1) "
    "so the relabel never raised a quote (_intl_rule.py). Their extrapolated India new price / competitor quote / resale "
    "moved to _pre_intl_* fields. ADDED the 12 real India configs behind them (critic-verified 2026-09-30: OnePlus 11 "
    "16/256, 11R 16/256, 12 16/512, 13 16/512, 13R 12/256 + 16/512, Nord 3 16/256, Nord CE 3 12/256, Poco M7 5G 8/128, "
    "Vivo Y39 5G 8/128, Oppo Reno 14 12/256 + 12/512). LADDER: two stale India rows priced above a freshly verified "
    "superior config were lowered to it (Nord 3 8/128 14,100 -> 13,300; Poco M7 5G 6/128 6,200 -> 6,000); three new trims "
    "capped at the verified base trim x launch-price ratio (Reno 14 12/256 25,400 -> 18,600, 12/512 27,700 -> 20,100, "
    "OnePlus 13 16/512 40,100 -> 39,900). FLAG: critics call the whole Reno 14 family under-priced (8/256 resale 19,500 vs "
    "Cashify max 23,010 and OLX ~27-28k) — re-research the three India trims together next run. 25 quotes changed, "
    "none raised except the 12 new rows; every other entry is byte-identical to v6.9.")
ms = meta.setdefault('market_signals', {})
ms['updated'] = TODAY
ms['international_variants_policy'] = {
    'event': "2026-10-01: Shane decided configs never sold in India are kept as '(International)' rows, not deleted.",
    'effect': ("A1 = min(0.90 x A1(intl_sibling), prior A1); no research on these rows (no India market to observe). "
               "Weekly finalize re-derives them from the India sibling via _intl_rule.recompute_international()."),
    'confidence': 'policy (Shane)'}

ph = {k: v for k, v in db.items() if k != '_meta'}
A1 = engine_a1(db, TODAY)
problems = {'a1_above_new': [], 'zero_or_broken': [], 'resale_le_buyback': [], 'a1_above_resale': [],
            'storage_inversion': [], 'intl_above_sibling': [], 'dup_display_name': []}
for k, e in ph.items():
    a = A1[k]
    if not a or a <= 0: problems['zero_or_broken'].append(k); continue
    nn = e.get('net_new_inr')
    if isinstance(nn, (int, float)) and nn > 0 and a >= nn: problems['a1_above_new'].append((k, a, nn))
    bm, obs = e.get('buyback_market'), e.get('market_resale_observed')
    rs = obs or e.get('resale_target_a1')
    if bm and rs and bm >= rs: problems['resale_le_buyback'].append((k, bm, rs))
    if isinstance(obs, (int, float)) and obs > 0 and a > obs * 0.92 + 100: problems['a1_above_resale'].append((k, a, obs))
    if e.get('international'):
        s = e.get('intl_sibling')
        if not s in ph or a > A1[s] * 0.9 + 100: problems['intl_above_sibling'].append((k, a, s, A1.get(s)))
RANK = {'64': 1, '128': 2, '256': 3, '512': 4, '1tb': 5, '2tb': 6}
fams = {}
for k in ph:
    m = re.match(r'^(.*?)_(\d+|1tb|2tb)(_[a-z]+)?$', k)
    if m and m.group(2) in RANK: fams.setdefault(m.group(1) + (m.group(3) or ''), []).append((RANK[m.group(2)], k))
for fam, items in fams.items():
    items.sort()
    for i in range(1, len(items)):
        # an International row vs an India row is a cross-market price difference (the 10% policy discount), not an
        # inversion — only same-market ladders are checked
        if bool(ph[items[i][1]].get('international')) != bool(ph[items[i - 1][1]].get('international')): continue
        if A1[items[i][1]] < A1[items[i - 1][1]] - 100:
            problems['storage_inversion'].append((items[i][1], A1[items[i][1]], items[i - 1][1], A1[items[i - 1][1]]))
names = {}
for k, e in ph.items(): names.setdefault(e.get('display_name'), []).append(k)
problems['dup_display_name'] = [(n, ks) for n, ks in names.items() if len(ks) > 1]

print('=' * 72); print(f'FINALIZE v{VERSION} {TODAY}  phones={len(ph)}'); print('=' * 72)
for n, items in problems.items():
    print(f'  {n:20s}: {len(items)}')
    for it in items[:6]: print(f'      {it}')
# compare against v6.9's own baseline counts so pre-existing issues are not blamed on this change
base = json.load(open(f'{DIR}/phone_db.backup-{TODAY}.json'))
BA = engine_a1(base, TODAY)
pre_inv = sum(1 for fam, items in fams.items() for i in range(1, len(items))
              if items[i][1] in BA and items[i - 1][1] in BA and BA[items[i][1]] < BA[items[i - 1][1]] - 100)
print(f'  (storage inversions already present in v6.9 over the same families: {pre_inv})')
if not APPLY:
    print('\n(dry-run)'); sys.exit(0)
out = {'_meta': meta}; out.update(ph)
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
c = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
L = open(f'{DIR}/index.html').read().split('\n'); n = 0
for i, ln in enumerate(L):
    if ln.lstrip().startswith('const DB = {'): L[i] = ln[:len(ln) - len(ln.lstrip())] + c; n += 1
assert n == 1
open(f'{DIR}/index.html', 'w').write('\n'.join(L))
h = open(f'{DIR}/index.html', encoding='utf-8').read(); i = h.find('const DB = {')
inline = json.loads(h[i + len('const DB = '):h.find('\n', i)].rstrip().rstrip(';'))
same = json.dumps(inline, sort_keys=True) == json.dumps(json.load(open(f'{DIR}/phone_db.json')), sort_keys=True)
print(f'\nAPPLIED v{VERSION}. files in sync: {same}')
sys.exit(0 if same else 1)
