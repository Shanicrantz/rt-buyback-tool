#!/usr/bin/env python3
"""Finalize v6.11 (2026-10-01): International rows re-derived, version + changelog, invariants on the REAL engine
(incl. the cross-RAM ladder check the older same-RAM check missed — Galaxy A57 12/256 < 8/256 sat unseen), and both
files written in sync. --apply writes."""
import json, re, sys, os
from _intl_rule import engine_a1, recompute_international

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY, VERSION = '2026-10-01', '6.11'
APPLY = '--apply' in sys.argv
db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
att = json.load(open(f'{DIR}/_attention_{TODAY}.json'))
out_v = json.load(open(f'{DIR}/_pending/outcome_{TODAY}.json')) if os.path.exists(f'{DIR}/_pending/outcome_{TODAY}.json') else {}
V610 = engine_a1(json.load(open(f'{DIR}/phone_db.backup-{TODAY}-v610.json')), TODAY)

intl_moves = recompute_international(db, TODAY, TODAY)
A1 = engine_a1(db, TODAY)
ph = {k: v for k, v in db.items() if k != '_meta'}

def fmt_moves(rows):
    return ', '.join(f"{ph[k]['display_name']} {format(V610[k], ',') if k in V610 else 'restored'} -> {A1[k]:,}" for k in rows if k in ph)
reno = [k for k in ('oppo_reno_14_8_256', 'oppo_reno_14_12_256', 'oppo_reno_14_12_512', 'oppo_reno_14_8_512')]
lava = [a['key'] for a in out_v.get('added_new', [])]
held_v = [h['key'] for h in out_v.get('held', [])]
st = {}
for x in att['added']: st[x[7]] = st.get(x[7], 0) + 1
meta['version'] = VERSION
meta['last_calibration'] = TODAY
meta['v6_11_changelog'] = (
    f"Shane's 'needs attention' items on top of v6.10 (2026-10-01). "
    f"(1) INTERNATIONAL policy extended to the three older non-India rows: {fmt_moves([x[0] for x in att['intl']])} "
    f"(OnePlus 15 12/512 restored from v6.8 — v6.9 had deleted it). "
    f"(2) DUPLICATE: Lava Agni 3 5G 8/256GB was listed twice; kept lava_agni_3_5g_8_256 with India new Rs24,999 and the "
    f"lower quote, removed lava_agni_3_8_256. "
    f"(3) GAP BACKLOG: {len(att['added'])} critic-verified real India configs from the 2026-09-30 gap audit added "
    f"({st.get('verified', 0)} verified, {st.get('estimated', 0)} estimated -> re-researched next run); held: future first "
    f"sale (iPhone Duo, Oppo K14 Plus, HMD Vibe 2 Pro, Vivo V80 / S2 FE, Redmi 17C unpriced), critic-rejected phantoms "
    f"(itel A100C 4/64, OnePlus Pad Lite LTE 8/256). "
    f"(4) LADDER: {len(att['ladder'])} same-phone repairs — stale bigger configs levelled UP to fresh smaller research within "
    f"their ceilings, stale smaller configs lowered: " + '; '.join(f"{x[0]} {x[1]:,} -> {x[2]:,}" for x in att['ladder']) + ". "
    f"(5) VERIFY+REFUTE (Opus) on the Oppo Reno 14 family and four Lava Play models (0.80 placeholders): "
    f"{fmt_moves(reno)}; Lava Play added: {', '.join(lava) if lava else 'none'}; held: {', '.join(held_v) if held_v else 'none'}. "
    f"FLAGS: Galaxy A57 12/256 capped by its own observed resale Rs34,000 while critics call it under-priced — re-research "
    f"the A57 family; iQOO Z11x 8/128 + 8/256 levelled to the verified 6/128 — re-research. Every other entry is identical to v6.10.")
ms = meta.setdefault('market_signals', {})
ms['updated'] = TODAY

problems = {'a1_above_new': [], 'zero_or_broken': [], 'resale_le_buyback': [], 'a1_above_resale': [],
            'storage_inversion': [], 'ram_storage_dominance': [], 'intl_above_sibling': [], 'dup_display_name': []}
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
        if s not in ph or a > A1[s] * 0.9 + 100: problems['intl_above_sibling'].append((k, a, s, A1.get(s)))
RANK = {'64': 1, '128': 2, '256': 3, '512': 4, '1tb': 5, '2tb': 6}
fams = {}
for k in ph:
    m = re.match(r'^(.*?)_(\d+|1tb|2tb)(_[a-z]+)?$', k)
    if m and m.group(2) in RANK: fams.setdefault(m.group(1) + (m.group(3) or ''), []).append((RANK[m.group(2)], k))
for fam, items in fams.items():
    items.sort()
    for i in range(1, len(items)):
        if bool(ph[items[i][1]].get('international')) != bool(ph[items[i - 1][1]].get('international')): continue
        if A1[items[i][1]] < A1[items[i - 1][1]] - 100:
            problems['storage_inversion'].append((items[i][1], A1[items[i][1]], items[i - 1][1], A1[items[i - 1][1]]))
# cross-RAM dominance, same market: <= RAM and <= storage must not quote above
KEYRE = re.compile(r'^(.*)_(\d+)_(\d+|1tb|2tb)(_[a-z0-9]+)?$')
groups = {}
for k in ph:
    m = KEYRE.match(k)
    # count a key only when its display name confirms the RAM/storage reading (iphone_6_16 is a model number, not 6GB RAM)
    dn = re.sub(r'\s|gb', '', (ph[k].get('display_name') or '').lower())
    if m and not ph[k].get('rt_buyback_a1_override') and f"{m.group(2)}/{m.group(3)}" in dn:
        st_ = {'1tb': 1024, '2tb': 2048}.get(m.group(3)) or int(m.group(3))
        groups.setdefault((m.group(1), m.group(4) or '', bool(ph[k].get('international'))), []).append((int(m.group(2)), st_, k))
pre_dom = 0
BASE = V610
for g, rows in groups.items():
    for r1, s1, a in rows:
        for r2, s2, b in rows:
            if a != b and r2 >= r1 and s2 >= s1:
                if A1[a] > A1[b] + 100: problems['ram_storage_dominance'].append((a, A1[a], b, A1[b]))
                if a in BASE and b in BASE and BASE[a] > BASE[b] + 100: pre_dom += 1
names = {}
for k, e in ph.items(): names.setdefault(e.get('display_name'), []).append(k)
problems['dup_display_name'] = [(n, ks) for n, ks in names.items() if len(ks) > 1]

print('=' * 72); print(f'FINALIZE v{VERSION} {TODAY}  phones={len(ph)}  (intl rows re-derived: {len(intl_moves)})'); print('=' * 72)
for n, items in problems.items():
    print(f'  {n:22s}: {len(items)}')
    for it in items[:8]: print(f'      {it}')
print(f'  (cross-RAM dominance breaches already present in v6.10, DB-wide: {pre_dom})')
print('\nCHANGELOG:', meta['v6_11_changelog'][:1500])
if not APPLY:
    print('\n(dry-run)'); sys.exit(0)
# carry the pre-existing cross-RAM breaches forward for the next run's verify+refute (which side is wrong needs research)
json.dump([{'smaller': a, 'smaller_a1': aa, 'bigger': b, 'bigger_a1': bb,
            'smaller_cal': ph[a].get('calibration_date'), 'bigger_cal': ph[b].get('calibration_date')}
           for a, aa, b, bb in problems['ram_storage_dominance']],
          open(f'{DIR}/_carryforward_ram_dominance_{TODAY}.json', 'w'), indent=1)
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
