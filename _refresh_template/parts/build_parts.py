"""v6.37: attach OFFICIAL brand India spare-part prices to catalogue entries as `part_prices`.

Sources (all fetched 14 Nov 2026, each model with its own timestamp):
  OnePlus  service.oneplus.com/in/spare-parts-price   part price incl. 18% GST + listed labour fee (saved responses)
  OPPO     support.oppo.com/in/spare-parts-price      part price incl. 18% GST + listed labour fee (saved responses)
  vivo     vivo.com/in/support/accessory              MRP incl. all taxes; labour not listed (saved responses)
  Samsung  samsung.com/in/support/spare-part-pricing-list-for-repair/  ex-GST -> +18% GST; labour excluded (saved page)
  realme   realme.com/in/support/spare-parts-price    GST included; service charge extra (read in the browser)
  Xiaomi   mi.com/in/support/spare-part-prices/       read in the browser (device name checked on each page)
Matching: exact model name first, then 5G/4G-insensitive only when unique on both sides; the catalogue never gets a
price from a different network/RAM edition. Unmatched brand models and catalogue families are listed, not guessed.
Damage keys without an official part keep the existing tier-percentage estimate. International rows untouched.
"""
import json, re, sys, hashlib, collections, unicodedata
from pathlib import Path
W = Path(__file__).resolve().parent; ROOT = W.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(W))
import _market_refresh_runner as m
from parts_common import parse_oppo_platform, read_gz_json
import parse_samsung

BRAND_KEYS = {'OnePlus': ('oneplus',), 'OPPO': ('oppo',), 'vivo': ('vivo',), 'Samsung': ('samsung',), 'realme': ('realme',), 'Xiaomi': ('redmi', 'poco', 'xiaomi'), 'Apple': ('iphone',)}
STRIP = r'^(samsung|oppo|vivo|realme|xiaomi|oneplus)\s+'
# Brand page name -> catalogue family, only where the catalogue spells the SAME phone differently (checked 14 Nov).
ALIASES = {('realme', 'realme 10 4G'): ['Realme 10'], ('realme', 'realme NARZO 80 Lite'): ['Realme Narzo 80 Lite 4G'],
           ('realme', 'realme GT Master Edition'): ['Realme GT Master'], ('realme', 'realme 9 5G speed edition'): ['Realme 9 5G Speed'],
           ('realme', 'realme narzo 50i（IN）'): ['Realme Narzo 50i'], ('Xiaomi', 'Redmi 12'): ['Redmi 12 4G'],
           ('Xiaomi', 'POCO M4 Pro'): ['Poco M4 Pro 4G', 'Poco M4 Pro (4G)']}

def key(name, loose):
    s = unicodedata.normalize('NFKC', name).lower().replace('genshin impact edition', '')
    s = re.sub(r'\(?\b\d+\s*g?b?\s*\+\s*\d+\s*g?b?\)?', ' ', s)   # vivo per-config entries: "X60 (12+256)", "V23 5G 256G+12G"
    s = s.replace('+', ' plus ')
    s = re.sub(STRIP, '', s.strip())
    s = re.sub(r'\b\d+\s*gb\b', ' ', s)                      # Samsung page names carry RAM ("Galaxy A23 8GB")
    if loose: s = re.sub(r'\b(5g|4g)\b', ' ', s)
    return re.sub(r'[^a-z0-9]', '', s)

def money(v):
    v = str(v or '').replace('₹', '').replace(',', '').replace('INR', '').strip()
    try: return float(v)
    except ValueError: return None

def by_label(items, rules):
    """items: [(label, price)], rules: {damage_key: (include_regex, exclude_regex|None)} -> max price per key."""
    out = {}
    for k, (inc, exc) in rules.items():
        cands = [(p, l) for l, p in items if p and re.search(inc, l, re.I) and not (exc and re.search(exc, l, re.I))]
        if cands:
            p, l = max(cands)
            out[k] = dict(part_inr=round(p), labour_inr=0, amount_inr=round(p), part_name=l)
    return out

COMMON = {
    'display': (r'screen|display|lcd|oled', r'protector|guard|film|glass only'),
    'back_panel': (r'back ?cover|battery cover|back ?glass|backcover|rear cover|back panel', None),
    'battery': (r'^battery$|^battery\b(?!.*cover)', r'cover'),
    'rear_camera': (r'rear (main )?camera|camera[- ]?rear|camera.*(main|wide angle)|^camera wide|back camera|camer wide', r'front|macro|depth|ultra ?wide|telephoto|tele\b'),
    'front_camera': (r'front', None),
    'charging_port': (r'sub[- ]?board|usb port|charging port|pcb-sb', r'cable'),
    'speaker': (r'speaker', None),
}

def records():
    recs = []  # (brand, model, parts, provenance)
    for fn, brand in [('oneplus-raw.json', 'OnePlus'), ('oppo-raw.json', 'OPPO')]:
        p = W / fn
        if not p.exists(): continue
        for x in json.loads(p.read_text()):
            if x.get('http_status') != 200: continue
            parts, name = parse_oppo_platform(read_gz_json(W / 'research' / x['evidence_file']))
            for a in parts.values(): a.setdefault('basis', 'Brand India repair price: part (incl. 18% GST) + listed labour fee')
            recs.append((brand, (name or x['model']).strip(), parts, dict(source_url=x['source_url'], observed_at=x['observed_at'], evidence_file=x['evidence_file'], sha256=x['sha256'], method='saved brand-page price response')))
    p = W / 'vivo-raw.json'
    if p.exists():
        for x in json.loads(p.read_text()):
            if x.get('http_status') != 200: continue
            j = read_gz_json(W / 'research' / x['evidence_file'])
            lst = ((j.get('data') or {}).get('sparePartVO') or {}).get('sparePartsVoList') or []
            items = [(i.get('name', ''), money(i.get('price'))) for i in lst]
            parts = by_label(items, COMMON)
            for a in parts.values(): a['basis'] = 'Brand India MRP incl. all taxes; labour not listed'
            recs.append(('vivo', 'vivo ' + x['model'], parts, dict(source_url=x['source_url'], observed_at=x['observed_at'], evidence_file=x['evidence_file'], sha256=x['sha256'], method='saved brand-page price response')))
    sm, meta = parse_samsung.parse()
    for name, v in sm.items():
        if 'Tab' in name: continue
        parts = v['parts']
        for a in parts.values(): a['basis'] = 'Brand India part price ex-GST + 18% GST; labour excluded'
        recs.append(('Samsung', 'Samsung ' + name, parts, dict(source_url=parse_samsung.URL, observed_at=meta['observed_at'], evidence_file=meta['snapshot'], sha256=meta['sha256'], method='saved brand page (all models embedded)')))
    for fn, brand, basis in [('realme-browser.json', 'realme', 'Brand India price incl. GST; service charge extra'), ('xiaomi-browser.json', 'Xiaomi', 'Brand India price as listed; service charge not listed'), ('apple-browser.json', 'Apple', 'Apple India out-of-warranty service estimate ("may be subject to tax"); service fee included')]:
        p = W / fn
        if not p.exists(): continue
        LABEL = dict(display='Screen', back_panel='Back cover', battery='Battery', rear_camera='Rear main camera', front_camera='Front camera', charging_port='Sub-board / USB port', speaker='Speaker')
        for name, v in json.loads(p.read_text()).items():
            if 'values' in v:   # compact browser export: mapped regular prices per damage key + fingerprint of the full list read
                parts = {dk: dict(part_inr=int(val), labour_inr=0, amount_inr=int(val), part_name=LABEL[dk]) for dk, val in v['values'].items() if val}
                for a in parts.values(): a['basis'] = basis
                recs.append((brand, name, parts, dict(source_url=v['source_url'], observed_at=v['observed_at'], sha256=v.get('fingerprint'), method='read from the brand page in the browser (regular, not offer, price); list fingerprint = sha256 prefix of the full part list read')))
                continue
            items = [(l, money(pr)) for l, pr in v['items']]
            parts = by_label(items, COMMON)
            for a in parts.values(): a['basis'] = basis
            text = json.dumps(v['items'], ensure_ascii=False)
            recs.append((brand, name, parts, dict(source_url=v['source_url'], observed_at=v['observed_at'], sha256=hashlib.sha256(text.encode()).hexdigest(), method='read from the brand page in the browser; listed items saved in ' + fn)))
    return recs

def build(db):
    recs = records()
    fam = collections.defaultdict(list)
    for k, e in db.items():
        if k == '_meta' or e.get('international') or e.get('category', 'phone') != 'phone': continue
        fam[(k.split('_')[0], m.family(e['display_name']))].append(k)
    unmatched_brand, assign, loose_wait = [], collections.defaultdict(list), []
    for rec in recs:
        brand, model, parts, prov = rec
        if not parts: unmatched_brand.append(dict(brand=brand, model=model, reason='no mappable parts')); continue
        cand = [(p, f) for (p, f) in fam if p in BRAND_KEYS[brand]]
        exact = [c for c in cand if key(c[1], False) == key(model, False)] or [c for c in cand if c[1] in ALIASES.get((brand, model), [])]
        if exact:
            for c in exact: assign[c].append(rec)
        else: loose_wait.append((rec, cand))
    for rec, cand in loose_wait:
        loose = [c for c in cand if key(c[1], True) == key(rec[1], True)]
        if len({key(c[1], False) for c in loose}) == 1 and not any(assign.get(c) for c in loose):
            for c in loose: assign[c].append(rec)
        else: unmatched_brand.append(dict(brand=rec[0], model=rec[1], reason='no catalogue family' if not loose else 'ambiguous 4G/5G or duplicate family'))
    matched, used = [], set(assign)
    for c, rs in assign.items():
        merged = {}
        for brand, model, parts, prov in rs:
            for dk, a in parts.items():
                if dk not in merged or a['amount_inr'] > merged[dk]['amount_inr']:
                    merged[dk] = dict(a, brand=brand, brand_model=model, **prov)
        for k in fam[c]: matched.append((k, merged))
    out = json.loads(json.dumps(db)); changed = 0
    for k, ref in matched:
        if out[k].get('part_prices') != ref: changed += 1
        out[k]['part_prices'] = ref
    unmatched_db = sorted(f for (p, f) in fam if any(p in v for v in BRAND_KEYS.values()) and (p, f) not in used)
    return out, dict(records=len(recs), variants_priced=len(matched), changed=changed, unmatched_brand=unmatched_brand, unmatched_catalogue_families=unmatched_db,
                     by_brand=collections.Counter(r[0] for r in recs), keys=collections.Counter(dk for _, ref in matched for dk in ref))

if __name__ == '__main__':
    db = json.loads((W / 'baseline/phone_db.json').read_text())
    out, rep = build(db)
    (W / 'parts-match-report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: v for k, v in rep.items() if k not in ('unmatched_brand', 'unmatched_catalogue_families')}, default=str))
    print('unmatched brand models', len(rep['unmatched_brand']), '| unmatched catalogue families', len(rep['unmatched_catalogue_families']))
