"""v6.41: older iPhones use a Foxconn-grade battery market rate (Shane, 2026-11-19: "Use Foxconn grade").

Scope: the 15 older models whose battery v6.40 priced at original grade (iPhone 6 / 6 Plus / 6s / 6s Plus / SE (2016) /
7 / 7 Plus / 8 / 8 Plus / X / XR / XS / XS Max / 11 Pro / 11 Pro Max). Every other part, and every other model's battery,
is unchanged (still original grade).
Rule: each seller's highest in-stock "Foxconn" battery listing for exactly that model + Rs500 fitting (assumed, as v6.39/40),
median over sellers, rounded up to Rs100. If a seller lists the model only out of stock, that listed price is used and
flagged (iPhone XS). abest.in "iPhone 5SE" is the trade name of the iPhone SE (2016) (5s-size SE, sold as "5SE").
Usage: python3 -I build_and_prepare.py   (baseline/ = live v6.40 files) -> foxconn-batteries.json, candidate/
"""
import json, re, math, statistics, shutil, importlib.util
from pathlib import Path
W = Path(__file__).resolve().parent; ROOT = W.parents[1]
spec = importlib.util.spec_from_file_location('bm', W.parent / '2026-11-19-v6.40-iphone-market-parts' / 'build_market.py')
bm = importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
VERSION, PREV = '6.41', '6.40'
OLD_CACHE, NEW_CACHE = 'rt-buyback-cache-v6-40-iphone-market-parts-20261119', 'rt-buyback-cache-v6-41-foxconn-battery-20261119'
EVID = '_weekly_refresh/2026-11-19-v6.41-old-iphone-foxconn-battery/'
TARGETS = ['iPhone 6', 'iPhone 6 Plus', 'iPhone 6s', 'iPhone 6s Plus', 'iPhone SE (2016)', 'iPhone 7', 'iPhone 7 Plus', 'iPhone 8', 'iPhone 8 Plus',
           'iPhone X', 'iPhone XR', 'iPhone XS', 'iPhone XS Max', 'iPhone 11 Pro', 'iPhone 11 Pro Max']
FIT = 500

def foxconn_rows():
    rows = [r for r in bm.seller_rows() if r['part'] == 'battery' and 'foxconn' in r['title'].lower()]
    times = bm.fetch_times(W / 'research/abest/fetch.log')
    fresh = json.loads((W / 'research/abest/abest-rows.json').read_text())
    for r in fresh:   # pages re-read for v6.41 replace the v6.39 copies
        rows = [x for x in rows if x['url'] != r['url']]
        model = 'iPhone SE (2016)' if '5se' in r['title'].lower() else bm.norm_model(r['title'])
        rows.append({'seller': 'abest.in', 'title': r['title'], 'url': r['url'], 'price_inr': r['price_inr'], 'model': model,
                     'in_stock': 'outofstock' not in (r['availability'] or '').lower(), 'observed_at': times.get(r['url']), 'sha256': r['sha256'],
                     'evidence_dir': str((W / 'research/abest').relative_to(W.parent))})
    return rows

def build():
    rows = foxconn_rows(); out = {}
    for m in TARGETS:
        cand = [r for r in rows if r['model'] == m and r['price_inr']]
        live = [r for r in cand if r['in_stock']]
        use, oos = (live, False) if live else (cand, True)
        per = {}
        for r in use:
            if r['seller'] not in per or r['price_inr'] > per[r['seller']]['price_inr']: per[r['seller']] = r
        qs = sorted(per.values(), key=lambda r: r['seller'])
        assert qs, 'no Foxconn quote for ' + m
        med = statistics.median([int(q['price_inr']) + FIT for q in qs])
        out[m] = {'amount': int(math.ceil(med / 100) * 100), 'out_of_stock_fallback': oos,
                  'quotes': [{k: q[k] for k in ('seller', 'title', 'url', 'price_inr', 'in_stock', 'observed_at', 'sha256', 'evidence_dir')} for q in qs]}
    return out

if __name__ == '__main__':
    res = build()
    base = json.loads((W / 'baseline/phone_db.json').read_text())
    assert base == json.loads((ROOT / 'phone_db.json').read_text()) and base['_meta']['version'] == PREV, 'production DB moved since baseline'
    out = json.loads(json.dumps(base)); changed = []
    for k, e in out.items():
        if k == '_meta' or not k.startswith('iphone'): continue
        m = bm.db_model(e['display_name']); r = (e.get('part_prices') or {}).get('battery')
        if m not in res or not r: continue
        assert r.get('market') and r.get('grade') == 'Original/OG', k
        x = res[m]; q = x['quotes']
        e['part_prices']['battery'] = {
            'part_inr': x['amount'] - FIT, 'labour_inr': FIT, 'amount_inr': x['amount'], 'part_name': 'Battery (Foxconn)',
            'basis': f"India market rate: Foxconn-grade battery (Shane 2026-11-19 for older iPhones), median of {len(q)} seller price{'s' if len(q) > 1 else ''}, + fitting Rs{FIT}"
                     + (' (seller lists it out of stock)' if x['out_of_stock_fallback'] else '') + f" (original-grade market rate was Rs{r['amount_inr']:,})",
            'brand': 'Market', 'market': True, 'grade': 'Foxconn', 'brand_model': m, 'source_url': q[0]['url'],
            'observed_at': max(z['observed_at'] for z in q),
            'sources': ' · '.join(f"{z['seller']} Rs{int(z['price_inr']):,}{'' if z['in_stock'] else ' (out of stock)'}" for z in q),
            'fitting_basis': bm.FITTING_BASIS['battery'], 'original_grade_inr': r['amount_inr'],
            'method': 'v6.41 Foxconn battery market median (see _meta.part_price_policy); evidence ' + EVID}
        changed.append((k, r['amount_inr'], x['amount']))
    meta = out['_meta']; meta['version'] = VERSION
    meta['part_price_policy'] += (' Batteries on older iPhones (6 / 6 Plus / 6s / 6s Plus / SE 2016 / 7 / 7 Plus / 8 / 8 Plus / X / XR / XS / XS Max / 11 Pro / 11 Pro Max) '
        'use the Foxconn-grade battery market rate + Rs500 fitting instead (v6.41, Shane 2026-11-19: "Use Foxconn grade").')
    meta['v6_41_changelog'] = (f'19 Nov 2026: battery deduction on {len(changed)} variants of {len(res)} older iPhones (6 -> XS Max, SE 2016, 11 Pro / Pro Max) now uses the '
        'Foxconn-grade market rate (abest.in) + Rs500 fitting instead of the original-grade rate. Other parts and newer models unchanged.')
    compact = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    C = W / 'candidate'; C.mkdir(exist_ok=True); (C / 'phone_db.json').write_text(compact)
    html = (W / 'baseline/index.html').read_text()
    a = '`Market rate ${String(official.observed_at || "").slice(0,10)} (original part + fitting): part ${fmt(official.part_inr)}'
    b = '`Market rate ${String(official.observed_at || "").slice(0,10)} (${official.grade === "Foxconn" ? "Foxconn" : "original"} part + fitting): part ${fmt(official.part_inr)}'
    assert html.count(a) == 1; html = html.replace(a, b)
    html, n = re.subn(r'^const DB = (\{[^\r\n]*\});[ \t]*$', lambda _: 'const DB = ' + compact + ';', html, flags=re.M); assert n == 1
    (C / 'index.html').write_text(html)
    sw = (W / 'baseline/sw.js').read_text(); assert sw.count(OLD_CACHE) == 1; (C / 'sw.js').write_text(sw.replace(OLD_CACHE, NEW_CACHE))
    for f in ['manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png', '_resolve_quote_safety.cjs']: shutil.copy2(ROOT / f, C / f)
    for t in ROOT.glob('test_*.cjs'):
        if t.name != 'test_part_prices.cjs' or not (C / t.name).exists(): shutil.copy2(t, C / t.name)
    if not (C / '_test_fixtures').exists(): shutil.copytree(ROOT / '_test_fixtures', C / '_test_fixtures')
    if not (C / '_weekly_refresh').exists(): (C / '_weekly_refresh').symlink_to(ROOT / '_weekly_refresh', target_is_directory=True)
    (W / 'foxconn-batteries.json').write_text(json.dumps({'models': res, 'variants': changed}, indent=1, ensure_ascii=False))
    for m, x in res.items(): print(f"{m:18} Rs{x['amount']:>5}{'  OOS fallback' if x['out_of_stock_fallback'] else ''}  " + ' | '.join(f"{q['seller']} {int(q['price_inr'])}" for q in x['quotes']))
    print(json.dumps({'version': VERSION, 'variants_changed': len(changed), 'db_bytes': len(compact)}))
