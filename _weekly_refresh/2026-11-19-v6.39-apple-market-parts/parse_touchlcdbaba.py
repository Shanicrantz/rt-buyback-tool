"""Parse saved touchlcdbaba.com (S.S. Spare Parts) iPhone pages -> rows json. Usage: python3 -I parse_touchlcdbaba.py <html_dir> <urls.txt> <out.json>"""
import sys, os, gzip, re, json, hashlib, html as H
src, urlf, out = sys.argv[1:4]
urls = {u.strip().replace('https://www.touchlcdbaba.com/', '').replace('/', '_').removesuffix('.html'): u.strip() for u in open(urlf) if u.strip()}
rows = []
for fn in sorted(os.listdir(src)):
    if not fn.endswith('.html.gz'): continue
    raw = gzip.open(os.path.join(src, fn)).read(); h = raw.decode('utf-8', 'ignore'); slug = fn[:-8]
    def first(p):
        m = re.search(p, h, re.S); return H.unescape(m.group(1)).strip() if m else None
    title = first(r'<h1[^>]*>(.*?)</h1>')
    title = re.sub(r'<[^>]+>', '', title or '') or first(r'og:title" content="([^"]+)"')
    price = first(r'"@type":"Offer".{0,400}?"price":"?([\d.]+)') or first(r'"price":"?([\d.]+)')
    avail = first(r'"availability":"([^"]+)"')
    # the visible main price block (first ₹ amount after the H1)
    i = h.find('</h1>'); vis = re.search(r'&#8377;(?:</span>)?\s*([\d,]+\.\d\d)', h[i:i+6000]) if i > 0 else None
    rows.append({'slug': slug, 'url': urls.get(slug), 'title': title, 'price_inr': float(price) if price else None,
                 'visible_price_inr': float(vis.group(1).replace(',', '')) if vis else None,
                 'availability': avail, 'sha256': hashlib.sha256(raw).hexdigest()[:12]})
json.dump(rows, open(out, 'w'), indent=1, ensure_ascii=False)
print(len(rows), 'rows')
