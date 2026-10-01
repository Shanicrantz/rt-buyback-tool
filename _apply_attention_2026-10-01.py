#!/usr/bin/env python3
"""v6.11 (2026-10-01) — Shane's "needs attention" items, on top of v6.10.

 1) INTERNATIONAL policy for the three older non-India rows (Galaxy A57 8/128, Poco M7 Pro 8/128) and restoring
    OnePlus 15 12/512 (deleted by v6.9) as an International row — rule in _intl_rule.py.
 2) Lava Agni 3 5G 8/256GB was listed twice (lava_agni_3_8_256 + lava_agni_3_5g_8_256). Keep the family-consistent
    key, with the correct India new price (Rs24,999; Rs22,999 is the 8/128-with-charger SKU) and the LOWER of the two
    quotes; drop the stray duplicate.
 3) GAP BACKLOG: the critic-verified real India configs from the 2026-09-30 gap audit that v6.9 left out (launch-window
    only) — brain-priced exactly like _add_gaps.py (series-tier normalisation, C/D margin floor, resale x0.92 and
    new x0.85 caps, weak provenance -> 'estimated'). Held: future first sale, rejected, and the four Lava Play models
    (0.80 placeholders on 10-13-month-old phones; they are in this week's verify+refute pass).
 4) LADDER coherence inside every touched phone family, same market only: a dominated config (<= RAM and <= storage)
    must not quote above the config that dominates it. The dominated one is LOWERED to it — whichever is fresh or
    stale — so the repair can only ever lower a quote.
--apply writes both files; default is dry-run."""
import json, glob, re, sys
from collections import Counter
from datetime import date
from _intl_rule import r100, engine_a1, set_a1, recompute_international, INTL_DISCOUNT

DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY, RESEARCH_DATE = '2026-10-01', '2026-09-30'
APPLY = '--apply' in sys.argv
T = date(2026, 10, 1)
db = json.load(open(f'{DIR}/phone_db.json'))
meta = db['_meta']
MA, TIER_DEF = meta['margin_by_age'], meta['default_margins_by_tier']
PRE = engine_a1(db, TODAY)

def months(ld):
    y, mo, d = map(int, ld.split('-'))
    return (T.year - y) * 12 + (T.month - mo) - (1 if T.day < d else 0)

def margin_for(tier, ld):
    a = months(ld) if ld else None
    b = '<24mo' if (a is None or a < 24) else '24-36mo' if a < 36 else '36-54mo' if a < 54 else '54mo+'
    m = MA[b]
    if tier in ('C', 'D'): m = max(m, TIER_DEF.get(tier, 0.25))
    return round(m, 3)

log = {'intl': [], 'dup': [], 'added': [], 'held': [], 'ladder': []}

# ---------------- 1) International rows ----------------
old = json.load(open(f'{DIR}/phone_db.backup-2026-09-30.json'))          # v6.8: last version holding OnePlus 15 12/512
assert 'oneplus_15_12_512' not in db
db['oneplus_15_12_512'] = json.loads(json.dumps(old['oneplus_15_12_512']))
PRE['oneplus_15_12_512'] = engine_a1({'_meta': meta, 'x': db['oneplus_15_12_512']}, TODAY)['x']   # 47,300 as last quoted
INTL = {'samsung_a57_5g_8_128': 'samsung_a57_5g_8_256',   # India sold 8/256 + 12/256 only (Samsung India buy page, 91mobiles)
        'poco_m7_pro_5g_8_128': 'poco_m7_pro_5g_6_128',   # India sold 6/128 + 8/256 only (FoneArena launch 2024-12-17)
        'oneplus_15_12_512': 'oneplus_15_16_512'}         # India sold 12/256 + 16/512 only (oneplus.in, v6.9 review)
for k, sib in INTL.items():
    e = db[k]
    assert sib in db and not db[sib].get('international'), (k, sib)
    e['display_name'] = re.sub(r'\s*\(International\)$', '', e['display_name']) + ' (International)'
    e.update({'international': True, 'intl_sibling': sib, 'intl_discount': INTL_DISCOUNT, '_pre_intl_a1': PRE[k]})
    if e.get('target_margin') is None: e['target_margin'] = margin_for(e.get('tier'), e.get('launch_date'))

# ---------------- 2) Lava Agni 3 duplicate ----------------
keep, drop = 'lava_agni_3_5g_8_256', 'lava_agni_3_8_256'
assert db[keep]['display_name'] == db[drop]['display_name']
low = min(PRE[keep], PRE[drop])
db[keep]['net_new_inr'] = 24999          # India 8/256 (with charger) launch price; 22,999 is the 8/128-with-charger SKU
set_a1(db[keep], low)
db[keep]['calibration_status'] = 'estimated'
db[keep]['calibration_date'] = TODAY
db[keep]['live_source'] = (f"MERGED {TODAY}: duplicate {drop} removed; kept the lower quote ₹{low:,} "
                           f"(was ₹{PRE[keep]:,} here, ₹{PRE[drop]:,} there) and India new ₹24,999. Re-research.")[:180]
db[keep]['_merged_duplicate'] = {'key': drop, 'entry': db.pop(drop)}
log['dup'].append((keep, PRE[keep], low, drop, PRE[drop]))

KEYRE = re.compile(r'^(.*)_(\d+)_(\d+|1tb|2tb)(_[a-z0-9]+)?$')

# ---------------- 3) gap backlog ----------------
find, ver = {}, {}
for f in glob.glob(f'{DIR}/_gaps/find_*.json'):
    for m in json.load(open(f)).get('missing', []): find[m['key']] = m
for f in glob.glob(f'{DIR}/_gaps/verified_*.json'):
    for v in json.load(open(f)).get('verified', []): ver[v['key']] = v
IN_VERIFICATION = {'lava_play_max_5g_6_128', 'lava_play_max_5g_8_128', 'lava_play_ultra_5g_6_128', 'lava_play_ultra_5g_8_128'}
def sig(nm): return re.sub(r'[^a-z0-9]', '', (nm or '').lower())
exsig = {sig(e.get('display_name')) for k, e in db.items() if k != '_meta'}
def series_sig(k):
    toks = k.split('_')
    while len(toks) > 2 and re.fullmatch(r'\d+|1tb|2tb|wifi|5g|lte', toks[-1]): toks.pop()
    return re.sub(r'\d+', '', '_'.join(toks))
series_tiers = {}
for k, e in db.items():
    if k != '_meta' and e.get('tier'): series_tiers.setdefault(series_sig(k), Counter())[e['tier']] += 1

new_keys = []
for k, v in sorted(ver.items()):
    f = find.get(k)
    why = None
    if k in db: why = 'already in DB'
    elif not f: why = 'no finder record'
    elif not v.get('real_india_launch') or v.get('verdict') == 'rejected': why = 'rejected by critic'
    elif k in IN_VERIFICATION: why = 'in verify+refute (0.80 placeholder on an old phone)'
    elif max(f.get('launch_date') or '', f.get('first_sale_date') or '') > TODAY: why = f"future first sale {f.get('launch_date')}"
    elif sig(f['display_name']) in exsig: why = 'display name already in DB'
    elif not isinstance(v.get('resale_price_final'), (int, float)) or v['resale_price_final'] <= 0: why = 'no verified resale'
    if why:
        if why != 'already in DB': log['held'].append((k, why))
        continue
    rs, nn, bm = v['resale_price_final'], v.get('new_price_final'), v.get('buyback_market_final')
    tier = f['tier']
    # tier = the tier this exact phone family already carries in the DB (it sets the C/D margin floor, so one phone must
    # not get two margins across its storage variants); a brand-new family keeps the critic-checked finder tier
    fam_rows = [x for x in db if x != '_meta' and KEYRE.match(x) and KEYRE.match(x).group(1) == KEYRE.match(k).group(1)] if KEYRE.match(k) else []
    ft = Counter(db[x].get('tier') for x in fam_rows if db[x].get('tier'))
    if ft: tier = ft.most_common(1)[0][0]
    ld = f['launch_date']
    m = margin_for(tier, ld)
    a1 = min(rs / (1 + m), rs * 0.92)
    if isinstance(nn, (int, float)) and nn > 0: a1 = min(a1, nn * 0.85)
    note = (v.get('note') or '').upper()
    placeholder = isinstance(nn, (int, float)) and nn > 0 and abs(rs / nn - 0.80) < 0.01
    estimated = placeholder or any(t in note for t in ('ESTIMATED', 'LOW CONFIDENCE', 'ANALOG', 'RE-RESEARCH'))
    e = {'display_name': f['display_name'], 'tier': tier, 'launch_date': ld, 'target_margin': m,
         'market_resale_observed': r100(rs)}
    if f.get('discontinued'): e['discontinued'] = True
    a1 = set_a1(e, int(a1) // 100 * 100)
    if isinstance(nn, (int, float)) and nn > 0: e['net_new_inr'] = int(nn)
    if isinstance(bm, (int, float)) and 0 < bm <= rs * 0.85: e['buyback_market'] = r100(bm)
    e['calibration_status'] = 'estimated' if estimated else 'verified'
    e['calibration_date'] = RESEARCH_DATE
    e['live_source'] = (f"Added {TODAY} (gap-audit+critic {RESEARCH_DATE}). resale ₹{r100(rs):,}"
                        f"{' / new ₹' + format(int(nn), ',') if nn else ''} -> A1 ₹{a1:,} = resale÷(1+{m})")[:180]
    db[k] = e
    exsig.add(sig(e['display_name']))
    new_keys.append(k)
    log['added'].append((k, e['display_name'], tier, ld, a1, r100(rs), nn, e['calibration_status'],
                         'ROUNDNEW' if isinstance(nn, (int, float)) and nn % 1000 == 0 else ''))

# ---------------- 4) ladder coherence (same market, lowers only) ----------------
def parse(k):
    m = KEYRE.match(k)
    if not m: return None
    st = {'1tb': 1024, '2tb': 2048}.get(m.group(3), None) or int(m.group(3))
    return (m.group(1), m.group(4) or ''), int(m.group(2)), st
touched = {parse(k)[0] for k in new_keys + list(INTL) + [keep] if parse(k)}
cur = engine_a1(db, TODAY)
changed = True
while changed:
    changed = False
    for fam in touched:
        rows = [k for k in db if k != '_meta' and parse(k) and parse(k)[0] == fam
                and not db[k].get('rt_buyback_a1_override')]
        for intl in (False, True):
            grp = [k for k in rows if bool(db[k].get('international')) == intl]
            for small in grp:
                for big in grp:
                    if small == big: continue
                    _, rs_, ss = parse(small); _, rb, sb = parse(big)
                    if rb >= rs_ and sb >= ss and cur[small] > cur[big] + 100:
                        if intl: continue                     # international rows follow their sibling via _intl_rule
                        es, eb = db[small], db[big]
                        for x in (es, eb):
                            if x.get('target_margin') is None: x['target_margin'] = margin_for(x.get('tier'), x.get('launch_date'))
                        fresh = lambda k_: k_ in new_keys or (db[k_].get('calibration_date') or '') >= '2026-09-26'
                        was_s, was_b = cur[small], cur[big]
                        # 1) the bigger config is never worth less: level a STALE bigger one UP to its fresh/equal smaller
                        #    sibling, bounded by its own ceilings (the rule _finalize_meta.py applies every week). Never when the
                        #    bigger one is the fresh research and the smaller one the stale anchor.
                        if not eb.get('rt_buyback_a1_override') and not (fresh(big) and not fresh(small)):
                            ceil = float('inf')
                            if isinstance(eb.get('net_new_inr'), (int, float)) and eb['net_new_inr'] > 0: ceil = eb['net_new_inr'] * 0.85
                            if isinstance(eb.get('market_resale_observed'), (int, float)) and eb['market_resale_observed'] > 0:
                                ceil = min(ceil, eb['market_resale_observed'] * 0.92)
                            tgt = int(min(was_s, ceil)) // 100 * 100
                            if tgt > was_b:
                                set_a1(eb, tgt)
                                eb['calibration_status'] = 'estimated'
                                eb['live_source'] = (f"LADDER {TODAY}: levelled up from ₹{was_b:,} to the {es['display_name']} "
                                                     f"quote ₹{tgt:,} (a bigger config is never worth less); re-research")[:180]
                                cur = engine_a1(db, TODAY)
                                log['ladder'].append((big, was_b, cur[big], small, 'raised stale bigger'))
                                changed = True
                        # 2) still inverted -> pull the smaller config down to the bigger one's quote
                        if cur[small] > cur[big] + 100 and not es.get('rt_buyback_a1_override'):
                            set_a1(es, cur[big])
                            es['calibration_status'] = 'estimated'
                            es['live_source'] = (f"LADDER {TODAY}: ₹{was_s:,} sat above {eb['display_name']} ₹{cur[big]:,}; "
                                                 f"lowered to it")[:180]
                            cur = engine_a1(db, TODAY)
                            log['ladder'].append((small, was_s, cur[small], big, 'lowered smaller'))
                            changed = True

# ---------------- 5) International rows re-derived (incl. the three new ones) ----------------
res = recompute_international(db, TODAY, TODAY)
for k in list(INTL):
    for kk, o, n, sa in res:
        if kk == k: log['intl'].append((k, PRE[k], n, INTL[k], sa))
POST = engine_a1(db, TODAY)

# ---------------- report ----------------
print('=' * 78); print(f'v6.11 ATTENTION ITEMS {TODAY} ({"APPLY" if APPLY else "dry-run"})'); print('=' * 78)
print('\n1) INTERNATIONAL:')
for k, o, n, s, sa in log['intl']: print(f'  {db[k]["display_name"][:46]:46s} A1 {o:>7,} -> {n:>7,}  (0.9 x {s} {sa:,})')
print('\n2) DUPLICATE MERGED:')
for kp, a, b, dr, c in log['dup']: print(f'  kept {kp} ({a:,} -> {b:,}); removed {dr} ({c:,})')
print(f'\n3) BACKLOG ADDED ({len(log["added"])}):  by brand {dict(Counter(k.split("_")[0] for k, *_ in log["added"]))}')
st = Counter(x[7] for x in log['added']); print(f'   status: {dict(st)}')
for k, nm, t, ld, a1, rs, nn, s, fl in log['added']:
    print(f'  {nm[:40]:40s} T{t} {ld} A1 ₹{POST[k]:>7,} resale ₹{rs:>7,} new {nn} [{s}] {fl}')
print(f'\n   HELD ({len(log["held"])}):')
for k, w in log['held']: print(f'  {k}: {w}')
print(f'\n4) LADDER REPAIRS ({len(log["ladder"])}):')
for s_, o, n, b, kind in log['ladder']: print(f'  {s_} [{kind}]: {o:,} -> {n:,}  (vs {b})')
moved = {k: (PRE.get(k), POST.get(k)) for k in set(PRE) | set(POST) if PRE.get(k) != POST.get(k)}
expected = set(new_keys) | set(INTL) | {keep, drop} | {x[0] for x in log['ladder']}
unexpected = sorted(k for k in moved if k not in expected)
print(f'\nQUOTES CHANGED vs v6.10: {len(moved)}; unexpected movers: {unexpected or "none"}')
assert not unexpected
if not APPLY:
    print('\n(dry-run — no files written)'); sys.exit(0)
out = {'_meta': meta}; out.update({k: v for k, v in db.items() if k != '_meta'})
json.dump(out, open(f'{DIR}/phone_db.json', 'w'), ensure_ascii=False, indent=2)
c = 'const DB = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
L = open(f'{DIR}/index.html').read().split('\n'); n = 0
for i, ln in enumerate(L):
    if ln.lstrip().startswith('const DB = {'): L[i] = ln[:len(ln) - len(ln.lstrip())] + c; n += 1
assert n == 1, n
open(f'{DIR}/index.html', 'w').write('\n'.join(L))
json.dump({**log, 'quotes': {k: {'v6.10': a, 'v6.11': b} for k, (a, b) in moved.items()}},
          open(f'{DIR}/_attention_{TODAY}.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(f'\nAPPLIED: {len(log["added"])} added, {len(INTL)} International, 1 duplicate merged, {len(log["ladder"])} ladder fixes.')
