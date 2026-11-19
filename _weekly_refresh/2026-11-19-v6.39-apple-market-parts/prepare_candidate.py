"""v6.39 candidate: baseline DB + market-parts.json -> candidate/{phone_db.json,index.html,sw.js,...}. Usage: python3 -I prepare_candidate.py"""
import json, re, shutil, statistics
from pathlib import Path
W = Path(__file__).resolve().parent; ROOT = W.parents[1]
import importlib.util
spec = importlib.util.spec_from_file_location('bm', W / 'build_market.py'); bm = importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
VERSION, PREV = '6.39', '6.38'
OLD_CACHE, NEW_CACHE = 'rt-buyback-cache-v6-38-weekly-20261119', 'rt-buyback-cache-v6-39-apple-market-parts-20261119'
EVID = '_weekly_refresh/2026-11-19-v6.39-apple-market-parts/'

base = json.loads((W / 'baseline/phone_db.json').read_text())
assert base == json.loads((ROOT / 'phone_db.json').read_text()) and base['_meta']['version'] == PREV, 'production DB moved since baseline'
table = {(t['model'], t['part']): t for t in json.loads((W / 'market-parts.json').read_text())}

def seller_name(s): return s.split(' ')[0]
def record(t, apple_rec):
    p, amt, fit = t['part'], t['market_inr'], bm.FITTING[t['part']]
    qs = t['quotes']; med = statistics.median([q['all_in_inr'] for q in qs])
    near = min(qs, key=lambda q: (abs(q['all_in_inr'] - med), q['seller']))
    return {
        'part_inr': amt - fit, 'labour_inr': fit, 'amount_inr': amt,
        'part_name': bm.PART_NAME[p],
        'basis': f"India market rate: original-grade part, median of {len(qs)} seller price{'s' if len(qs) > 1 else ''}, + fitting Rs{fit:,} (Apple service estimate was Rs{apple_rec['amount_inr']:,})",
        'brand': 'Market', 'market': True, 'grade': 'Original/OG',
        'brand_model': t['model'], 'source_url': near['url'],
        'observed_at': max(q['observed_at'] for q in qs),
        'sources': ' · '.join(f"{seller_name(q['seller'])} Rs{int(q['price_inr']):,}{' all-in' if q['kind'] == 'all_in' else ''}" for q in qs),
        'fitting_basis': bm.FITTING_BASIS[p],
        'apple_official_inr': apple_rec['amount_inr'],
        'method': 'v6.39 market median (see _meta.part_price_policy); evidence ' + EVID,
    }

out = json.loads(json.dumps(base)); changed = kept = 0
for k, e in out.items():
    if k == '_meta' or not e.get('part_prices'): continue
    for dk, r in list(e['part_prices'].items()):
        if r.get('brand') != 'Apple': continue
        t = table[(r['brand_model'], dk)]
        if t['use_market']: e['part_prices'][dk] = record(t, r); changed += 1
        else: kept += 1
m = out['_meta']; m['version'] = VERSION
m['part_price_policy'] = ('Damage deductions use a saved per-model part price (part_prices, with source and date) when one exists, else the tier-percentage estimate. '
    'Android brands: the brand\'s own India out-of-warranty spare-part price for the exact model (OnePlus/OPPO part incl. GST + listed labour; vivo MRP incl. taxes; '
    'Samsung ex-GST price + 18% GST; realme/Xiaomi as listed incl. GST; labour only where the brand lists it). '
    'Apple iPhones (from v6.39, Shane 2026-11-19): India market rate for an ORIGINAL-grade part (pulled or new original, not copy/OLED) plus fitting = median of India sellers\' '
    'in-stock original-grade prices + fitting (display Rs500, back glass Rs2,000, battery/camera Rs500); Apple\'s own service estimate is kept where no original-grade market '
    'price exists or the market is not cheaper (Apple estimates: support.apple.com/en-in/iphone/repair, read 2026-11-14). Rounded up to Rs100.')
m['v6_39_changelog'] = (f'19 Nov 2026: Apple part prices replaced with India market rates (original-grade part + fitting) for {changed} iPhone part prices on '
    f'{sum(1 for k, e in out.items() if k != "_meta" and any(r.get("market") for r in (e.get("part_prices") or {}).values()))} catalogue variants '
    '(abest.in, touchlcdbaba.com, appleproductsfix.com, iFonewala Gaffar Market). Apple estimate kept for iPhone 17e, 18 Pro, 18 Pro Max, Duo, SE (2022) battery and '
    '17 Pro / 17 Pro Max battery (no original market part, or market dearer). No-damage quotes unchanged.')
compact = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
C = W / 'candidate'; C.mkdir(exist_ok=True); (C / 'phone_db.json').write_text(compact)

html = (W / 'baseline/index.html').read_text()
old_src = 'const src = official ? `${official.brand || "Brand"} India price ${String(official.observed_at || "").slice(0,10)}: part ${fmt(official.part_inr ?? official.amount_inr)}${official.labour_inr ? " + labour " + fmt(official.labour_inr) : ""}` : "Estimate: % of new price (no official part price saved)";'
new_src = ('const src = !official ? "Estimate: % of new price (no part price saved)" : official.market\n'
           '      ? `Market rate ${String(official.observed_at || "").slice(0,10)} (original part + fitting): part ${fmt(official.part_inr)} + fitting ${fmt(official.labour_inr || 0)} · ${official.sources || ""} · Apple service ${fmt(official.apple_official_inr || 0)}`\n'
           '      : `${official.brand || "Brand"} India price ${String(official.observed_at || "").slice(0,10)}: part ${fmt(official.part_inr ?? official.amount_inr)}${official.labour_inr ? " + labour " + fmt(official.labour_inr) : ""}`;')
assert html.count(old_src) == 1; html = html.replace(old_src, new_src)
old_cmt = "// Official brand India out-of-warranty price for this exact model's part (part + listed labour, GST included),\n// saved per model by the refresh with its source and date. Missing => the tier-percentage estimate below."
new_cmt = ("// Saved per-model part price with its source and date: the brand's India out-of-warranty price (Android brands), or for\n"
           "// iPhones the India market rate for an original-grade part + fitting (market:true, v6.39). Missing => the tier-percentage estimate below.")
assert html.count(old_cmt) == 1; html = html.replace(old_cmt, new_cmt)
html, n = re.subn(r'^const DB = (\{[^\r\n]*\});[ \t]*$', lambda _: 'const DB = ' + compact + ';', html, flags=re.M); assert n == 1
(C / 'index.html').write_text(html)
sw = (W / 'baseline/sw.js').read_text(); assert sw.count(OLD_CACHE) == 1; (C / 'sw.js').write_text(sw.replace(OLD_CACHE, NEW_CACHE))
for f in ['manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png', '_resolve_quote_safety.cjs']: shutil.copy2(ROOT / f, C / f)
for t in ROOT.glob('test_*.cjs'):
    if t.name != 'test_part_prices.cjs' or not (C / t.name).exists(): shutil.copy2(t, C / t.name)
if not (C / '_test_fixtures').exists(): shutil.copytree(ROOT / '_test_fixtures', C / '_test_fixtures')
if not (C / '_weekly_refresh').exists(): (C / '_weekly_refresh').symlink_to(ROOT / '_weekly_refresh', target_is_directory=True)
print(json.dumps({'version': VERSION, 'market_records': changed, 'apple_records_kept': kept, 'db_bytes': len(compact), 'baseline_db_bytes': len(json.dumps(base, ensure_ascii=False, separators=(',', ':')))}))
