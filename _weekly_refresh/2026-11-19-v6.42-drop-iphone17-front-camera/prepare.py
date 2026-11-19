"""v6.42: drop the iPhone 17 front-camera market rate (Shane, 2026-11-19: "Yes, drop it").

The only original-grade listing (appleproductsfix.com Rs21,500, read 2026-11-19) looked like an Apple-serialised part
(iPhone 17 Pro's plain part is Rs5,999), giving a Rs22,000 deduction. The record is removed, so the engine falls back to
the tier-% estimate. EXCLUDED is the reusable guard: a future market re-run must skip these (model, part) pairs.
Usage: python3 -I prepare.py   (baseline/ = live v6.41 files) -> candidate/
"""
import json, re, shutil
from pathlib import Path
W = Path(__file__).resolve().parent; ROOT = W.parents[1]
VERSION, PREV = '6.42', '6.41'
OLD_CACHE, NEW_CACHE = 'rt-buyback-cache-v6-41-foxconn-battery-20261119', 'rt-buyback-cache-v6-42-drop-17-front-cam-20261119'
EXCLUDED = [('iPhone 17', 'front_camera')]

base = json.loads((W / 'baseline/phone_db.json').read_text())
assert base == json.loads((ROOT / 'phone_db.json').read_text()) and base['_meta']['version'] == PREV, 'production DB moved since baseline'
out = json.loads(json.dumps(base)); removed = []
for k, e in out.items():
    if k == '_meta': continue
    for m, p in EXCLUDED:
        r = (e.get('part_prices') or {}).get(p)
        if r and r.get('market') and r.get('brand_model') == m:
            removed.append((k, p, r['amount_inr'])); del e['part_prices'][p]
assert len(removed) == 2, removed
meta = out['_meta']; meta['version'] = VERSION
meta['part_price_market_exclusions'] = [{'model': m, 'part': p, 'reason': 'single listing Rs21,500 looked Apple-serialised (17 Pro plain part Rs5,999); Shane 2026-11-19 "Yes, drop it": tier-% estimate'} for m, p in EXCLUDED]
meta['v6_42_changelog'] = '19 Nov 2026: iPhone 17 front-camera market rate (Rs22,000, one serialised-looking listing) dropped on 2 variants; that deduction is back on the tier-% estimate. Nothing else changed.'
compact = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
C = W / 'candidate'; C.mkdir(exist_ok=True); (C / 'phone_db.json').write_text(compact)
html = (W / 'baseline/index.html').read_text()
html, n = re.subn(r'^const DB = (\{[^\r\n]*\});[ \t]*$', lambda _: 'const DB = ' + compact + ';', html, flags=re.M); assert n == 1
(C / 'index.html').write_text(html)
sw = (W / 'baseline/sw.js').read_text(); assert sw.count(OLD_CACHE) == 1; (C / 'sw.js').write_text(sw.replace(OLD_CACHE, NEW_CACHE))
for f in ['manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png', '_resolve_quote_safety.cjs']: shutil.copy2(ROOT / f, C / f)
for t in ROOT.glob('test_*.cjs'):
    if t.name != 'test_part_prices.cjs' or not (C / t.name).exists(): shutil.copy2(t, C / t.name)
if not (C / '_test_fixtures').exists(): shutil.copytree(ROOT / '_test_fixtures', C / '_test_fixtures')
if not (C / '_weekly_refresh').exists(): (C / '_weekly_refresh').symlink_to(ROOT / '_weekly_refresh', target_is_directory=True)
print(json.dumps({'version': VERSION, 'removed': removed}))
