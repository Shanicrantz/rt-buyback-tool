"""v6.40 iPhone market part prices, second pass: fill every iPhone part that still used the tier-% estimate.

Shane, 2026-11-19 (after v6.39): "Yes, add those" — older iPhones without Apple prices (6 -> XS Max, SE 2016, 11 Pro / Pro Max,
plus back glass / rear camera on 11 and SE 2020/2022) and front camera, charging port and speaker on all iPhones.
Same rule as v6.39 (Original / OG grade, with fitting):
  1. Each seller's in-stock listings explicitly graded original ("Original", "100% Original", "Set Removed Original",
     "Pulled Original", "Genuine") for exactly that model; one quote per seller = that seller's highest such listing.
     Copy / OLED / GX / DD / HQ / Foxconn / "OEM grade" / ungraded / shared-model listings are left out; out-of-stock too.
     Back panel: a glass/back-cover listing is preferred over one bundling the flash / wireless-charging module, and a
     full body housing is used only when the seller lists no back cover (aluminium-back models).
     Speaker ("Speaker / mic bad"): the seller's highest plain ear speaker / loudspeaker (sensor-flex assemblies only if
     nothing plain is listed). Front camera: plain original part over an Apple-serialised "Support Repair Assistant" part.
     Charging port: the port flex, never the wireless / NFC / power-volume flex.
  2. Part + fitting = all-in rate: display Rs500, back panel Rs2,000 (iFonewala listed); battery, cameras, charging port
     and speaker Rs500 (assumed = listed display fitting). iFonewala's all-in laser back-glass series price counts as listed.
  3. Market rate = median of the all-in rates, rounded up to Rs100.
  4. Only parts with no saved price are filled (v6.39 market records and kept Apple records are left as they are).
Usage: python3 -I build_market.py   (reads ../2026-11-19-v6.39-apple-market-parts/research + research/, baseline/phone_db.json)
"""
import json, re, math, statistics
from pathlib import Path
W = Path(__file__).resolve().parent
R39 = W.parent / '2026-11-19-v6.39-apple-market-parts' / 'research'
R40 = W / 'research'
PARTS = ('display', 'battery', 'back_panel', 'rear_camera', 'front_camera', 'charging_port', 'speaker')
FITTING = {'display': 500, 'back_panel': 2000, 'battery': 500, 'rear_camera': 500, 'front_camera': 500, 'charging_port': 500, 'speaker': 500}
_ASSUMED = 'Rs500 fitting (assumed = listed display fitting; no source lists fitting for this part)'
FITTING_BASIS = {'display': 'Rs500 fitting as listed by iFonewala, Gaffar Market (display pages)',
                 'back_panel': 'Rs2,000 fitting as listed by iFonewala, Gaffar Market (back housing page)',
                 'battery': _ASSUMED, 'rear_camera': _ASSUMED, 'front_camera': _ASSUMED, 'charging_port': _ASSUMED, 'speaker': _ASSUMED}
PART_NAME = {'display': 'Display combo (original)', 'battery': 'Battery (original)', 'back_panel': 'Back glass / back cover (original)',
             'rear_camera': 'Main rear camera (original)', 'front_camera': 'Front camera (original)',
             'charging_port': 'Charging port flex (original)', 'speaker': 'Ear speaker / loudspeaker (original)'}

def fetch_times(log):
    t = {}
    if log.exists():
        for ln in log.read_text().splitlines():
            ts, code, url = ln.split(' ', 2)
            if code == '200': t[url.strip()] = ts
    return t

SUFFIX = {'pro max': 'Pro Max', 'pro': 'Pro', 'plus': 'Plus', 'mini': 'mini'}
BASE = {'se2016': 'iPhone SE (2016)', 'se2020': 'iPhone SE (2020)', 'se2022': 'iPhone SE (2022)', 'air': 'iPhone Air', 'duo': 'iPhone Duo',
        'xs max': 'iPhone XS Max', 'xs': 'iPhone XS', 'xr': 'iPhone XR', 'x': 'iPhone X'}

def norm_model(title):
    """Return the one canonical iPhone model named in a title, or None if none / more than one."""
    s = ' ' + re.sub(r'[^a-z0-9+]+', ' ', title.lower()) + ' '
    s = re.sub(r'(\d)\s*\+', r'\1 plus ', s)                       # "7+" -> "7 plus"
    s = re.sub(r' iphone (\d)g ', r' iphone \1 ', s)                  # abest "7G" / "8G" / "6G"
    s = re.sub(r' iphone se ?2 2020 | iphone se2 | iphone se 2020 | iphone se 2nd gen\w* ', ' iphone se2020 ', s)
    s = re.sub(r' iphone se ?3 | iphone se 2022 | iphone se 3rd gen\w* ', ' iphone se2022 ', s)
    s = re.sub(r' iphone se 2016 | iphone se 1st gen\w* ', ' iphone se2016 ', s)
    s = re.sub(r' iphone 17 air | iphone air ', ' iphone air ', s)
    s = re.sub(r' (\d\d) e ', r' \1e ', s)
    s = re.sub(r' promax ', ' pro max ', s)
    s = re.sub(r' +', ' ', s)
    found = set()
    for m in re.finditer(r' iphone (se2016|se2020|se2022|air|duo|xs max|xs|xr|x|\d\d?e|\d\d?s?)((?: pro max| pro| plus| mini)?)(?= )', s):
        base, suf = m.group(1), m.group(2).strip()
        name = BASE.get(base) or ('iPhone ' + base + ((' ' + SUFFIX[suf]) if suf else ''))
        if base in BASE and suf: name = None
        found.add(name)
    if re.search(r' iphone \d\d? (?:pro max |pro |plus |mini )?(?:and )?\d\d? (?:pro|plus|mini)? ', s): return None   # "12/12 Pro"
    if re.search(r' iphone (?:x|xs|xr|8|7) (?:to|and) ', s): return None                                       # "XS to 15 Pro"
    found.discard(None)
    return found.pop() if len(found) == 1 else None

def db_model(display_name):
    n = re.sub(r'\s+\d+\s?(GB|TB)$', '', display_name).strip()
    return re.sub(r'^iPhone (\d)S\b', r'iPhone \1s', n)

def part_of(title):
    """(part, back_rank) — back_rank: 0 plain back glass/cover, 1 glass with modules, 2 full housing."""
    t = title.lower()
    if re.search(r'adhesive|sticker|protector|programmer|big hole|\bcase\b|tempered', t): return None, None
    if re.search(r'back glass|glass back|back battery cover|battery back cover|back rear glass', t):
        return 'back_panel', (1 if re.search(r'flash|wireless|nfc|camera lens|module', t) else 0)
    if re.search(r'lens|camera glass|wireless charging coil|\bic\b|holder|bracket only', t): return None, None
    if re.search(r'full body housing|full housing|body housing', t): return 'back_panel', 2
    if 'housing' in t: return None, None
    if 'battery' in t: return (None if re.search(r'connector|flex|board', t) else 'battery'), None
    if re.search(r'front camera|selfie camera', t): return 'front_camera', (1 if 'repair assistant' in t else 0)
    if re.search(r'back camera|rear camera|main camera', t): return (None if 'flex' in t else 'rear_camera'), None
    if re.search(r'charging port|charging flex|charging connector|dock', t): return (None if re.search(r'wireless|nfc|power|volume', t) else 'charging_port'), None
    if re.search(r'ear ?speaker|earpiece|loud ?speaker|ringer|buzzer|speaker flex', t): return 'speaker', (1 if re.search(r'sensor|proximity|face id', t) else 0)
    if re.search(r'display|lcd|screen|combo', t):
        return (None if re.search(r'front glass|outer glass|frame|chassis|backlight|digitizer for|^touch screen for', t) else 'display'), None
    return None, None

def original_grade(title):
    t = title.lower()
    if re.search(r'copy|oled display for apple|gx |gx-|\bdd\b|\bhq\b|tft|incell|soft oled|foxconn|oem grade|compatible|high quality li|\btw\b', t): return False
    return bool(re.search(r'original|genuine|set removed|pulled', t))

def seller_rows():
    out, seen = [], set()
    srcs = [('appleproductsfix.com', R40 / 'appleproductsfix'), ('abest.in', R39 / 'abest'), ('touchlcdbaba.com', R39 / 'touchlcdbaba'), ('appleproductsfix.com', R39 / 'appleproductsfix')]
    files = {'abest.in': 'abest-rows.json', 'touchlcdbaba.com': 'touchlcdbaba-rows.json', 'appleproductsfix.com': 'appleproductsfix-rows.json'}
    for seller, d in srcs:
        times = fetch_times(d / 'fetch.log')
        for r in json.loads((d / files[seller]).read_text()):
            if r['url'] in seen: continue
            seen.add(r['url'])
            title = r.get('title') or ''
            inst = 'outofstock' not in str(r.get('availability', '')).lower().replace('_', '').replace(' ', '')
            part, rank = part_of(title)
            out.append({'seller': seller, 'title': title, 'url': r['url'], 'price_inr': r.get('price_inr'), 'in_stock': inst,
                        'model': norm_model(title), 'part': part, 'back_rank': rank, 'original': original_grade(title),
                        'kind': 'part', 'observed_at': times.get(r['url']), 'sha256': r.get('sha256'), 'evidence_dir': str(d.relative_to(W.parent))})
    for q in json.loads((R39 / 'ifonewala/ifonewala-quotes.json').read_text())['quotes']:
        out.append({'seller': 'ifonewala.com', 'title': q['title'], 'url': q['url'], 'price_inr': q['price_inr'], 'in_stock': True,
                    'model': q['model'], 'part': q['part'], 'back_rank': 0 if q['part'] == 'back_panel' else None, 'original': True,
                    'kind': q['kind'], 'observed_at': q['observed_at'], 'sha256': q['sha256'], 'evidence_dir': '2026-11-19-v6.39-apple-market-parts/research/ifonewala'})
    return out

def build(models):
    rows = seller_rows()
    usable = [r for r in rows if r['model'] and r['part'] in PARTS and r['original'] and r['in_stock'] and r['price_inr']]
    result = {}
    for m in models:
        for p in PARTS:
            cand = [r for r in usable if r['model'] == m and r['part'] == p]
            if p in ('back_panel', 'speaker', 'front_camera'):
                # per seller, the plain part first: back cover > glass with modules > full housing; plain speaker > speaker +
                # sensor flex; plain front camera > "Support Repair Assistant" (Apple-serialised) front camera
                best = {}
                for r in cand: best[r['seller']] = min(best.get(r['seller'], 9), r['back_rank'] or 0)
                cand = [r for r in cand if (r['back_rank'] or 0) == best[r['seller']]]
            per_seller = {}
            for r in cand:
                key = (r['seller'], r['kind'])
                if key not in per_seller or r['price_inr'] > per_seller[key]['price_inr']: per_seller[key] = r
            qs = sorted(per_seller.values(), key=lambda r: (r['seller'], r['kind']))
            for r in qs: r['all_in_inr'] = int(r['price_inr']) + (FITTING[p] if r['kind'] == 'part' else 0)
            if qs:
                med = statistics.median([r['all_in_inr'] for r in qs])
                result[(m, p)] = {'amount': int(math.ceil(med / 100) * 100), 'quotes': qs}
    return rows, usable, result

if __name__ == '__main__':
    base = json.loads((W / 'baseline/phone_db.json').read_text())
    need = {}
    for k, e in base.items():
        if k == '_meta' or not k.startswith('iphone') or e.get('international') or e.get('category', 'phone') != 'phone': continue
        m = db_model(e['display_name'])
        for p in PARTS:
            if p not in (e.get('part_prices') or {}): need.setdefault(m, set()).add(p)
    rows, usable, result = build(sorted(need))
    table = []
    for m in sorted(need):
        for p in PARTS:
            if p not in need[m]: continue
            r = result.get((m, p))
            table.append({'model': m, 'part': p, 'market_inr': r['amount'] if r else None, 'use_market': bool(r),
                          'reason': 'market median' if r else 'no original-grade market quote: tier-% estimate kept',
                          'quotes': [{k: q[k] for k in ('seller', 'title', 'url', 'price_inr', 'all_in_inr', 'kind', 'observed_at', 'sha256', 'evidence_dir')} for q in (r['quotes'] if r else [])]})
    (W / 'market-quotes.json').write_text(json.dumps({'all_rows': rows}, indent=1, ensure_ascii=False))
    (W / 'market-parts.json').write_text(json.dumps(table, indent=1, ensure_ascii=False))
    unmatched = sorted({(r['seller'], r['title']) for r in rows if r['original'] and r['part'] in PARTS and not r['model']})
    print(json.dumps({'rows': len(rows), 'usable': len(usable), 'missing_parts': len(table), 'filled': sum(t['use_market'] for t in table),
                      'unmatched_original_titles': unmatched}, indent=1, ensure_ascii=False))
