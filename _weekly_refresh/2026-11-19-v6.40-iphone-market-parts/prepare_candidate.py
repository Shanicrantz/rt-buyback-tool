"""v6.40 candidate: baseline (v6.39) + market-parts.json -> candidate/. Fills only iPhone parts with no saved part price.
Usage: python3 -I prepare_candidate.py"""
import json, re, shutil, statistics, importlib.util
from pathlib import Path
W = Path(__file__).resolve().parent; ROOT = W.parents[1]
spec = importlib.util.spec_from_file_location('bm', W / 'build_market.py'); bm = importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
VERSION, PREV = '6.40', '6.39'
OLD_CACHE, NEW_CACHE = 'rt-buyback-cache-v6-39-apple-market-parts-20261119', 'rt-buyback-cache-v6-40-iphone-market-parts-20261119'
EVID = '_weekly_refresh/2026-11-19-v6.40-iphone-market-parts/'

base = json.loads((W / 'baseline/phone_db.json').read_text())
assert base == json.loads((ROOT / 'phone_db.json').read_text()) and base['_meta']['version'] == PREV, 'production DB moved since baseline'
table = {(t['model'], t['part']): t for t in json.loads((W / 'market-parts.json').read_text())}

def record(t):
    p, amt, fit = t['part'], t['market_inr'], bm.FITTING[t['part']]
    qs = t['quotes']; med = statistics.median([q['all_in_inr'] for q in qs])
    near = min(qs, key=lambda q: (abs(q['all_in_inr'] - med), q['seller']))
    return {
        'part_inr': amt - fit, 'labour_inr': fit, 'amount_inr': amt, 'part_name': bm.PART_NAME[p],
        'basis': f"India market rate: original-grade part, median of {len(qs)} seller price{'s' if len(qs) > 1 else ''}, + fitting Rs{fit:,} (replaces the tier-% estimate)",
        'brand': 'Market', 'market': True, 'grade': 'Original/OG', 'brand_model': t['model'], 'source_url': near['url'],
        'observed_at': max(q['observed_at'] for q in qs),
        'sources': ' · '.join(f"{q['seller'].split(' ')[0]} Rs{int(q['price_inr']):,}{' all-in' if q['kind'] == 'all_in' else ''}" for q in qs),
        'fitting_basis': bm.FITTING_BASIS[p],
        'method': 'v6.40 market median (see _meta.part_price_policy); evidence ' + EVID,
    }

out = json.loads(json.dumps(base)); added = 0; variants = set(); models = set()
for k, e in out.items():
    if k == '_meta' or not k.startswith('iphone') or e.get('international') or e.get('category', 'phone') != 'phone': continue
    m = bm.db_model(e['display_name'])
    for p in bm.PARTS:
        if p in (e.get('part_prices') or {}): continue
        t = table.get((m, p))
        if t and t['use_market']:
            e.setdefault('part_prices', {})[p] = record(t); added += 1; variants.add(k); models.add(m)
meta = out['_meta']; meta['version'] = VERSION
old_pol = base['_meta']['part_price_policy']
anchor = "Apple iPhones (from v6.39, Shane 2026-11-19): India market rate for an ORIGINAL-grade part (pulled or new original, not copy/OLED) plus fitting = median of India sellers' in-stock original-grade prices + fitting (display Rs500, back glass Rs2,000, battery/camera Rs500); "
assert old_pol.count(anchor) == 1
meta['part_price_policy'] = old_pol.replace(anchor,
    "Apple iPhones (from v6.39/v6.40, Shane 2026-11-19): India market rate for an ORIGINAL-grade part (pulled or new original, not copy/OLED) plus fitting = median of India sellers' "
    "in-stock original-grade prices + fitting (display Rs500, back glass / back cover Rs2,000, battery, cameras, charging port and speaker Rs500), for every iPhone part a seller lists "
    "(v6.40 added older iPhones and front camera / charging port / speaker); ")
meta['v6_40_changelog'] = (f'19 Nov 2026: India market rates (original-grade part + fitting) added for {added} iPhone part prices that still used the tier-% estimate, on '
    f'{len(variants)} variants of {len(models)} models: older iPhones (6 -> XS Max, SE 2016, 11 Pro / Pro Max; back glass and rear camera on 11 and SE 2020) and front camera, '
    'charging port and speaker on iPhone 11 -> 17 Pro Max / Air. Parts with no original-grade market listing keep the tier-% estimate. v6.39 prices unchanged.')
compact = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
C = W / 'candidate'; C.mkdir(exist_ok=True); (C / 'phone_db.json').write_text(compact)

html = (W / 'baseline/index.html').read_text()
old_src = ' · Apple service ${fmt(official.apple_official_inr || 0)}`'
new_src = '${official.apple_official_inr ? " · Apple service " + fmt(official.apple_official_inr) : ""}`'
assert html.count(old_src) == 1; html = html.replace(old_src, new_src)
html, n = re.subn(r'^const DB = (\{[^\r\n]*\});[ \t]*$', lambda _: 'const DB = ' + compact + ';', html, flags=re.M); assert n == 1
(C / 'index.html').write_text(html)
sw = (W / 'baseline/sw.js').read_text(); assert sw.count(OLD_CACHE) == 1; (C / 'sw.js').write_text(sw.replace(OLD_CACHE, NEW_CACHE))
for f in ['manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png', '_resolve_quote_safety.cjs']: shutil.copy2(ROOT / f, C / f)
for t in ROOT.glob('test_*.cjs'):
    if t.name != 'test_part_prices.cjs' or not (C / t.name).exists(): shutil.copy2(t, C / t.name)
if not (C / '_test_fixtures').exists(): shutil.copytree(ROOT / '_test_fixtures', C / '_test_fixtures')
if not (C / '_weekly_refresh').exists(): (C / '_weekly_refresh').symlink_to(ROOT / '_weekly_refresh', target_is_directory=True)
print(json.dumps({'version': VERSION, 'added': added, 'variants': len(variants), 'models': len(models), 'db_bytes': len(compact)}))
