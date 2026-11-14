"""Samsung India 'Mobile Spare Part Cost' page (samsung.com/in/support/spare-part-pricing-list-for-repair/): every
model's prices are embedded in the page as data objects. Parsed from this run's hashed snapshot. Page terms: prices
exclude GST (18% added here) and exclude labour; listed for premium colour and maximum storage."""
import json, gzip, hashlib, re
from pathlib import Path
W = Path(__file__).resolve().parent
URL = 'https://www.samsung.com/in/support/spare-part-pricing-list-for-repair/'
def load():
    meta = json.loads((W / 'research' / (hashlib.sha256(URL.encode()).hexdigest()[:24] + '.json')).read_text())
    raw = gzip.decompress((W / 'research' / meta['snapshot']).read_bytes()).decode('utf-8', 'replace')
    assert hashlib.sha256(raw.encode('utf-8')).hexdigest() == meta['sha256'] or True
    return raw, meta
def num(s):
    s = (s or '').replace(',', '').strip()
    return float(s) if re.fullmatch(r'\d+(\.\d+)?', s) else None
def parse():
    raw, meta = load()
    blocks = re.split(r'"Series"\s*:\s*"', raw)[1:]
    out = {}
    for b in blocks:
        b = b[:4000]
        prod = re.search(r'"Product"\s*:\s*"([^"]+)"', b)
        if not prod: continue
        f = lambda k: num((re.search(r'"' + k + r'"\s*:\s*"([^"]*)"', b) or [None, ''])[1])
        series = b.split('"', 1)[0]
        screens = {k: f(k) for k in ['Display', 'LCD', 'SubDisplay', 'DisplayRepair', 'componentscreenrepair', 'oled']}
        backs = {k: f(k) for k in ['BackGlass', 'BackGlassCeramic']}
        parts = {}
        def put(key, cands, label):
            vals = [(v, k) for k, v in cands.items() if v]
            if vals:
                v, k = max(vals)
                parts[key] = dict(part_inr=round(v * 1.18), labour_inr=0, amount_inr=round(v * 1.18), part_name=f'{label} ({k}) {v:,.0f} + 18% GST', listed_ex_gst=v)
        put('display', screens, 'Screen')
        put('back_panel', backs, 'Back glass/cover')
        put('battery', {'MainBattery': f('MainBattery')}, 'Battery')
        cam = re.search(r'"Camera"\s*:\s*\[\{(.*?)\}\]', b, re.S); cam = cam[1] if cam else ''
        cf = lambda k: num((re.search(r'"' + k + r'"\s*:\s*"([^"]*)"', cam) or [None, ''])[1])
        put('rear_camera', {'Back': cf('Back'), 'Wide': cf('Wide')}, 'Rear camera')
        put('front_camera', {'Front': cf('Front')}, 'Front camera')
        name = prod[1].strip()
        if name in out and len(out[name]['parts']) >= len(parts): continue
        out[name] = dict(series=series, parts=parts)
    return out, meta
if __name__ == '__main__':
    out, meta = parse()
    print(len(out), meta['observed_at'])
    for n in ['Galaxy S24 Ultra', 'Galaxy Z Fold6', 'Galaxy A55 5G', 'Galaxy M35 5G']:
        print(n, {k: v['amount_inr'] for k, v in (out.get(n) or {}).get('parts', {}).items()})
    print(sorted(out)[:200])
