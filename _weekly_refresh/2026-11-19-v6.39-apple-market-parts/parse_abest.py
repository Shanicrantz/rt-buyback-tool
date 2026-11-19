"""Parse saved abest.in product pages -> abest-rows.json (title, price, availability, sha256). Usage: python3 -I parse_abest.py <html_dir> <out.json>"""
import sys, os, gzip, re, json, hashlib, html as H
src, out = sys.argv[1], sys.argv[2]
rows = []
for fn in sorted(os.listdir(src)):
    if not fn.endswith('.html.gz'): continue
    raw = gzip.open(os.path.join(src, fn)).read()
    h = raw.decode('utf-8', 'ignore')
    slug = fn[:-8]
    def first(p):
        m = re.search(p, h, re.S); return H.unescape(m.group(1)).strip() if m else None
    title = first(r'"@type"\s*:\s*"Product"\s*,\s*"name"\s*:\s*"([^"]+)"') or first(r'og:title" content="([^"]+)"')
    price = first(r'"@type"\s*:\s*"Offer"\s*,\s*"price"\s*:\s*"?([\d.]+)') or first(r'"price"\s*:\s*"?([\d.]+)')
    mrp = first(r'"(?:compare_at_price|compareAtPrice|mrp|regular_price)"\s*:\s*"?([\d.]+)')
    avail = first(r'"availability"\s*:\s*"([^"]+)"')
    rows.append({'slug': slug, 'url': 'https://abest.in/' + slug, 'title': title, 'price_inr': float(price) if price else None,
                 'mrp_inr': float(mrp) if mrp else None, 'availability': avail, 'sha256': hashlib.sha256(raw).hexdigest()[:12]})
json.dump(rows, open(out, 'w'), indent=1, ensure_ascii=False)
print(len(rows), 'rows;', sum(1 for r in rows if r['price_inr']), 'with price;', sorted({r['availability'] for r in rows if r['availability']}))
