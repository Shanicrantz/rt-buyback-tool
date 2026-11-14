"""Shared helpers for official brand spare-part prices (v6.37, 2026-11-14).

Damage keys follow DAMAGE_PARTS in index.html. A key gets an official price only when the brand's India page lists the
matching part; everything else keeps the existing tier-percentage estimate. Amount = regular out-of-warranty part price
(as listed, GST included) + the labour fee the brand lists for that part. Promotional/discounted prices are ignored.
"""
import json, re, gzip

def norm_model(name):
    s = name.lower().replace('+', ' plus ').replace('genshin impact edition', '')
    s = re.sub(r'\b(5g|4g)\b', ' ', s)
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def _amount(child):
    if (child.get('retailPriceCurrency') or 'INR') != 'INR':
        return None
    try:
        part = float(child.get('retailPrice') or 0)
        labour = float(child.get('laborCostAmount') or 0)
    except ValueError:
        return None
    if part <= 0:
        return None
    return dict(part_inr=round(part), labour_inr=round(labour), amount_inr=round(part + labour), part_name=(child.get('partName') or '').strip())

def parse_oppo_platform(payload):
    """OPPO / OnePlus India 'Repair Price' platform: getPartPriceNew response -> {damage_key: price}."""
    data = (payload or {}).get('data') or {}
    groups = {}
    for g in data.get('partPriceList') or []:
        for c in g.get('childList') or []:
            a = _amount(c)
            if a:
                groups.setdefault(g.get('groupCode'), []).append(a)
    out = {}
    def pick(key, items):
        if items:
            out[key] = max(items, key=lambda a: a['amount_inr'])  # foldables: inner/main part is the conservative one
    pick('display', groups.get('PHONE_SCREEN'))
    pick('back_panel', groups.get('PHONE_BATTERY_COVER'))
    pick('battery', groups.get('PHONE_BATTERY'))
    cams = groups.get('PHONE_CAMERA') or []
    rear_main = [a for a in cams if re.match(r'rear (main )?camera', a['part_name'], re.I)]
    pick('rear_camera', rear_main)
    pick('front_camera', [a for a in cams if re.search(r'front', a['part_name'], re.I)])
    return out, (data.get('serviceModelInfoVO') or {}).get('marketingModelName')

def read_gz_json(path):
    return json.loads(gzip.decompress(path.read_bytes()))
