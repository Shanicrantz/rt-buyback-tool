"""Parse saved appleproductsfix.com iPhone part pages -> rows json. Usage: python3 -I parse_appleproductsfix.py <html_dir> <out.json>"""
import sys, os, gzip, re, json, hashlib, html as H
src, out = sys.argv[1:3]
rows = []
for fn in sorted(os.listdir(src)):
    if not fn.endswith('.html.gz'): continue
    raw = gzip.open(os.path.join(src, fn)).read(); h = raw.decode('utf-8', 'ignore'); slug = fn[:-8]
    def meta(p):
        m = re.search(r'<meta property="' + re.escape(p) + r'" content="([^"]*)"', h); return H.unescape(m.group(1)).strip() if m else None
    price = meta('product:price:amount')
    url = (meta('og:url') or '').rstrip('?')
    rows.append({'slug': slug, 'url': url or 'https://www.appleproductsfix.com/product/' + slug, 'title': meta('og:title'),
                 'price_inr': float(price) if price else None, 'availability': meta('og:availability'),
                 'condition': meta('og:condition'), 'sha256': hashlib.sha256(raw).hexdigest()[:12]})
json.dump(rows, open(out, 'w'), indent=1, ensure_ascii=False)
print(len(rows), 'rows', sum(1 for r in rows if r['price_inr']), 'priced', sorted({r['availability'] for r in rows}, key=str))
