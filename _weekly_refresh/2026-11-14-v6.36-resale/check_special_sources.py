"""v6.36: re-open the two non-Cashify resale anchors (GudFast X60 Pro+, Mobirapid S25 256) with the same
plain public GET and the same acceptance checks as v6.26/v6.30. No catalogue writes."""
from pathlib import Path
import html, json, math, re, sys
sys.path.insert(0, '/Users/shane/Documents/Claude/Projects/rt buyback tool')
import _market_refresh_runner as m
W = Path(__file__).resolve().parent; m.WORK = W
db = json.loads((W / 'baseline/phone_db.json').read_text())
checks, refs = [], {}
for key, retailer in [('vivo_x60_pro_plus_12_256', 'GudFast'), ('samsung_s25_256', 'Mobirapid')]:
    old = db[key]['current_resale_price']
    raw, meta = m.fetch(old['source_url'])
    text = re.sub(r'\s+', ' ', m.DOM(raw).root.text()) if raw else ''
    checks.append(dict(key=key, fetch=meta, structured=m.ld(raw) if raw else [], text=text[:4000]))
    if meta.get('http_status') != 200:
        continue
    if retailer == 'GudFast':
        variants = []
        for s in re.findall(r'data-product_variations=["\'](.*?)["\']', raw):
            variants.extend(json.loads(html.unescape(s)))
        cands = [v for v in variants if v['attributes'].get('attribute_pa_condition') == 'superb'
                 and v['is_in_stock'] and v['is_purchasable'] and v['variation_is_active']]
        if not cands or '12 GB RAM | 256 GB ROM' not in text or 'Snapdragon 888' not in text or 'INDIA Free Shipping' not in text:
            continue
        v = min(cands, key=lambda v: v['display_price']); ask = v['display_price']
        ref = json.loads(json.dumps(old)); ref['evidence'][0].update(selected_variant_id=v['variation_id'], selected_attributes=v['attributes'])
    else:
        products = [p for p in m.ld(raw) if p.get('@type') == 'Product']
        if len(products) != 1:
            continue
        p = products[0]
        if p.get('name') != 'REFURBISHED Samsung Galaxy S25 256GB' or not p['offers'].get('availability', '').endswith('/InStock') or p['offers'].get('priceCurrency') != 'INR' or '+ 18% GST Excellent' not in text:
            continue
        ask = round(float(p['offers']['price']) * 1.18, 2); ref = json.loads(json.dumps(old))
    ref.update(amount_inr=math.floor(ask * (1 - ref['assumption_discount']) / 100) * 100, observed_at=meta['observed_at'])
    ref['evidence'][0].update(amount_inr=ask, observed_at=meta['observed_at'], evidence_file=meta['snapshot'], sha256=meta['sha256'])
    refs[key] = ref
m.write(W / 'special-source-checks.json', checks)
m.write(W / 'special-resale-references.json', refs)
print(json.dumps({'special_resale': {k: (r['evidence'][0]['amount_inr'], r['amount_inr']) for k, r in refs.items()},
                  'sources': [{'key': c['key'], 'url': c['fetch']['source_url'], 'http_status': c['fetch'].get('http_status')} for c in checks]}, indent=1))
