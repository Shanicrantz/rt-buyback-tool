"""v6.39 Apple market part prices: India market ORIGINAL-grade part + fitting replaces the Apple service estimate.

Shane, 2026-11-19: "parts ke rates apple ki jagah market ke laga do"; quality = Original / OG (pulled or new original
part, not copy/soft-OLED/aftermarket); price = with fitting (part + fitting).

Rule, per iPhone model and part (display, battery, back_panel, rear_camera — the parts Apple's page listed):
  1. Each seller's in-stock listings explicitly graded original ("Original", "100% Original", "Set Removed Original",
     "Pulled Original", "Genuine") for exactly that model; one quote per seller = that seller's highest such listing.
     Copy / OLED / GX / DD / HQ / Foxconn / "OEM grade" / ungraded listings are left out. Out-of-stock listings are left out.
  2. Each part quote + fitting = an all-in market rate. Fitting: display Rs500 and back glass Rs2,000 as listed by
     iFonewala (Gaffar Market); battery and rear camera Rs500 (not listed by any source; same as the display fitting).
     iFonewala's back-glass laser repair price (all-in, per series) is used as listed.
  3. Market rate = median of the all-in rates, rounded up to Rs100.
  4. If no original-grade quote exists, or the market rate is not below Apple's own out-of-warranty price, the
     Apple record stays (Apple's service is then the cheaper genuine route).
Usage: python3 -I build_market.py   (reads research/*, baseline/phone_db.json; writes market-parts.json, market-quotes.json)
"""
import json, re, math, statistics, sys
from pathlib import Path
W = Path(__file__).resolve().parent
R = W / 'research'
PARTS = ('display', 'battery', 'back_panel', 'rear_camera')
FITTING = {'display': 500, 'back_panel': 2000, 'battery': 500, 'rear_camera': 500}
FITTING_BASIS = {'display': 'Rs500 fitting as listed by iFonewala, Gaffar Market (display pages)',
                 'back_panel': 'Rs2,000 fitting as listed by iFonewala, Gaffar Market (back housing page)',
                 'battery': 'Rs500 fitting (assumed = listed display fitting; no source lists battery fitting)',
                 'rear_camera': 'Rs500 fitting (assumed = listed display fitting; no source lists camera fitting)'}
PART_NAME = {'display': 'Display combo (original)', 'battery': 'Battery (original)', 'back_panel': 'Back glass (original)',
             'rear_camera': 'Main rear camera (original)'}

def fetch_times(log):
    t = {}
    if log.exists():
        for ln in log.read_text().splitlines():
            ts, code, url = ln.split(' ', 2)
            if code == '200': t[url.strip()] = ts
    return t

def norm_model(title):
    """Return the one canonical iPhone model named in a title, or None if none / more than one."""
    s = ' ' + re.sub(r'[^a-z0-9]+', ' ', title.lower()) + ' '
    s = re.sub(r' iphone se ?2 2020 | iphone se2 | iphone se 2020 | iphone se 2nd gen\w* ', ' iphone se2020 ', s)
    s = re.sub(r' iphone se ?3 | iphone se 2022 | iphone se 3rd gen\w* ', ' iphone se2022 ', s)
    s = re.sub(r' iphone 17 air | iphone air ', ' iphone air ', s)
    s = re.sub(r' (\d\d) e ', r' \1e ', s)
    s = re.sub(r' promax ', ' pro max ', s)
    found = set()
    for m in re.finditer(r' iphone (se2020|se2022|air|duo|\d\d?e|\d\d?)((?: pro max| pro| plus| mini)?) ', s):
        base, suf = m.group(1), m.group(2).strip()
        if base == 'se2020': name = 'iPhone SE (2020)'
        elif base == 'se2022': name = 'iPhone SE (2022)'
        elif base == 'air': name = 'iPhone Air'
        elif base == 'duo': name = 'iPhone Duo'
        else: name = 'iPhone ' + base + ((' ' + {'pro max': 'Pro Max', 'pro': 'Pro', 'plus': 'Plus', 'mini': 'mini'}[suf]) if suf else '')
        found.add(name)
    # shared-model titles ("12/12 Pro", "12 and 12 Pro") name a second model without the word iPhone
    if re.search(r' iphone \d\d? (?:pro max |pro |plus |mini )?(?:and )?\d\d? (?:pro|plus|mini)? ', s): return None
    return found.pop() if len(found) == 1 else None

def part_of(title):
    t = title.lower()
    if re.search(r'adhesive|sticker|protector|programmer|housing|big hole', t): return None
    if re.search(r'back glass|glass back|back battery cover|battery back cover|back rear glass', t): return 'back_panel'
    if 'battery' in t: return None if re.search(r'connector|flex|board', t) else 'battery'
    if re.search(r'back camera|rear camera|main camera', t): return None if re.search(r'lens|camera glass|flex', t) else 'rear_camera'
    if re.search(r'display|lcd|screen|combo', t):  # "LCD with Flex" / "with Sensor Flex" are full display assemblies
        return None if re.search(r'front glass|outer glass|frame|chassis|backlight|digitizer for|^touch screen for', t) else 'display'
    return None

def original_grade(title):
    t = title.lower()
    if re.search(r'copy|oled display for apple|gx |gx-|\bdd\b|\bhq\b|tft|incell|soft oled|foxconn|oem grade|compatible|high quality li', t): return False
    return bool(re.search(r'original|genuine|set removed|pulled', t))

def seller_rows():
    out = []
    for seller, f, log in [('abest.in', 'abest/abest-rows.json', 'abest/fetch.log'),
                           ('touchlcdbaba.com', 'touchlcdbaba/touchlcdbaba-rows.json', 'touchlcdbaba/fetch.log'),
                           ('appleproductsfix.com', 'appleproductsfix/appleproductsfix-rows.json', 'appleproductsfix/fetch.log')]:
        times = fetch_times(R / log)
        for r in json.loads((R / f).read_text()):
            title = r.get('title') or ''
            inst = 'outofstock' not in str(r.get('availability', '')).lower().replace('_', '').replace(' ', '')
            out.append({'seller': seller, 'title': title, 'url': r['url'], 'price_inr': r.get('price_inr'), 'in_stock': inst,
                        'model': norm_model(title), 'part': part_of(title), 'original': original_grade(title),
                        'kind': 'part', 'observed_at': times.get(r['url']) or times.get(r['url'].rstrip('/')), 'sha256': r.get('sha256')})
    for q in json.loads((R / 'ifonewala/ifonewala-quotes.json').read_text())['quotes']:
        out.append({'seller': 'ifonewala.com', 'title': q['title'], 'url': q['url'], 'price_inr': q['price_inr'], 'in_stock': True,
                    'model': q['model'], 'part': q['part'], 'original': True, 'kind': q['kind'], 'observed_at': q['observed_at'], 'sha256': q['sha256']})
    return out

def plain_glass(title):
    t = title.lower(); return not re.search(r'flash|wireless|nfc|camera lens|module', t)

def build(apple_models):
    rows = seller_rows()
    usable = [r for r in rows if r['model'] and r['part'] in PARTS and r['original'] and r['in_stock'] and r['price_inr']]
    quotes, result = {}, {}
    for m in apple_models:
        for p in PARTS:
            cand = [r for r in usable if r['model'] == m and r['part'] == p]
            if p == 'back_panel':  # glass-only listing preferred over glass + flash/wireless-charging module, per seller
                for s in {r['seller'] for r in cand}:
                    mine = [r for r in cand if r['seller'] == s]
                    if any(plain_glass(r['title']) for r in mine): cand = [r for r in cand if r['seller'] != s or plain_glass(r['title'])]
            per_seller = {}
            for r in cand:
                key = (r['seller'], r['kind'])
                if key not in per_seller or r['price_inr'] > per_seller[key]['price_inr']: per_seller[key] = r
            qs = sorted(per_seller.values(), key=lambda r: (r['seller'], r['kind']))
            for r in qs: r['all_in_inr'] = int(r['price_inr']) + (FITTING[p] if r['kind'] == 'part' else 0)
            quotes[f'{m}|{p}'] = qs
            if qs:
                med = statistics.median([r['all_in_inr'] for r in qs])
                result[(m, p)] = {'amount': int(math.ceil(med / 100) * 100), 'quotes': qs}
    return rows, usable, quotes, result

if __name__ == '__main__':
    base = json.loads((W / 'baseline/phone_db.json').read_text())
    apple = {}
    for k, e in base.items():
        if k == '_meta' or not e.get('part_prices'): continue
        for dk, r in e['part_prices'].items():
            if r.get('brand') == 'Apple': apple.setdefault(r['brand_model'], {})[dk] = r['amount_inr']
    rows, usable, quotes, result = build(sorted(apple))
    table = []
    for m in sorted(apple):
        for p in PARTS:
            if p not in apple[m]: continue
            a = apple[m][p]; r = result.get((m, p))
            mk = r['amount'] if r else None
            use = bool(r) and mk < a
            table.append({'model': m, 'part': p, 'apple_inr': a, 'market_inr': mk, 'use_market': use,
                          'reason': 'market median below Apple' if use else ('no original-grade market quote' if not r else 'market not below Apple: Apple kept'),
                          'quotes': [{k: q[k] for k in ('seller', 'title', 'url', 'price_inr', 'all_in_inr', 'kind', 'observed_at', 'sha256')} for q in (r['quotes'] if r else [])]})
    (W / 'market-quotes.json').write_text(json.dumps({'all_rows': rows}, indent=1, ensure_ascii=False))
    (W / 'market-parts.json').write_text(json.dumps(table, indent=1, ensure_ascii=False))
    unmatched = sorted({(r['seller'], r['title']) for r in rows if r['original'] and r['part'] in PARTS and not r['model']})
    print(json.dumps({'rows': len(rows), 'usable': len(usable), 'apple_parts': len(table), 'use_market': sum(t['use_market'] for t in table),
                      'kept_apple': [(t['model'], t['part'], t['reason']) for t in table if not t['use_market']], 'unmatched_original_titles': unmatched[:40]}, indent=1, ensure_ascii=False))
