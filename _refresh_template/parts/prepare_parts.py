"""Official part-price stage (template parts/; from v6.37): live DB + official part_prices -> candidate. run.json gives version and caches."""
import json, re, sys, shutil
from pathlib import Path
W = Path(__file__).resolve().parent; ROOT = W.parents[1]; sys.path.insert(0, str(W))
from build_parts import build
RUN = json.loads((W / 'run.json').read_text())
base = json.loads((W / 'baseline/phone_db.json').read_text())
assert base == json.loads((ROOT / 'phone_db.json').read_text()) and base['_meta']['version'] == RUN['previous_version'], 'production DB moved since baseline'
out, rep = build(base)
brands = ', '.join(f'{b} {n}' for b, n in rep['by_brand'].items())
out['_meta']['version'] = RUN['version']
out['_meta']['part_price_policy'] = ('Damage deductions use the brand\'s own India out-of-warranty spare-part price for the exact model (part_prices, with source and date) '
    'when the brand lists that part: OnePlus/OPPO part incl. GST + listed labour; vivo MRP incl. taxes; Samsung ex-GST price + 18% GST; realme/Xiaomi as listed incl. GST. '
    'Labour is included only where the brand lists it. Parts the brand does not list keep the tier-percentage estimate. Rounded up to Rs100.')
out['_meta']['v' + RUN['version'].replace('.', '_') + '_changelog'] = (RUN['date_label'] + f": official brand India spare-part prices for {rep['variants_priced']} catalogue variants ({brands} models read from the brands' own price pages); "
    'damage deductions now use them where listed, tier-percentage estimate elsewhere. Quotes without damage unchanged.')
compact = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
(W / 'candidate').mkdir(exist_ok=True); (W / 'candidate/phone_db.json').write_text(compact)
html = (W / 'baseline/index.html').read_text()
assert 'function officialPartPrice' in html
html, n = re.subn(r'^const DB = (\{[^\r\n]*\});[ \t]*$', lambda _: 'const DB = ' + compact + ';', html, flags=re.M); assert n == 1
(W / 'candidate/index.html').write_text(html)
sw = (ROOT / 'sw.js').read_text(); assert RUN['old_cache'] in sw, 'sw.js cache name moved since the run was made'
(W / 'candidate/sw.js').write_text(sw.replace(RUN['old_cache'], RUN['new_cache']))
for f in ['manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png']: shutil.copy2(ROOT / f, W / 'candidate' / f)
for t in ROOT.glob('test_*.cjs'): shutil.copy2(t, W / 'candidate' / t.name)
shutil.copy2(ROOT / '_resolve_quote_safety.cjs', W / 'candidate/_resolve_quote_safety.cjs')
if not (W / 'candidate/_test_fixtures').exists(): shutil.copytree(ROOT / '_test_fixtures', W / 'candidate/_test_fixtures')
if not (W / 'candidate/_weekly_refresh').exists(): (W / 'candidate/_weekly_refresh').symlink_to(ROOT / '_weekly_refresh', target_is_directory=True)
print(json.dumps({k: v for k, v in rep.items() if k not in ('unmatched_brand', 'unmatched_catalogue_families')}, default=str))
