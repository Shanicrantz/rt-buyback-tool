"""New-launch gap check (from v6.36). Fill launch-specs.json first (it starts as []), one object per exact variant:
  {"key": "oppo_find_x10_12_256", "display_name": "Oppo Find X10 12/256GB", "tier": "A", "launch_price": 139999,
   "first_sale": "2026-10-29", "foldable": false, "launch_sources": ["https://...first-sale or launch page..."]}
Rules (REFRESH-POLICY + memory): India phones whose FIRST SALE is on/before today and after the last launch add; tier =
the tier the DB already uses for that series; launch_price is the official launch cash price (history only).
A variant is proposed only if an exact, in-stock, new INR cash listing is fetched today (Flipkart product page or
Reliance Digital product page; demo/open-box excluded). One Cashify family GET is recorded; no resale is accepted.
"""
import sys, json, re, concurrent.futures
from pathlib import Path
from datetime import date
sys.path.insert(0, '/Users/shane/Documents/Claude/Projects/rt buyback tool')
import _market_refresh_runner as m
import _research_reliance_prices as rel
W = Path(__file__).resolve().parent; m.WORK = W
read = lambda n: json.loads((W / n).read_text())
db = read('baseline/phone_db.json'); run = read('run.json'); specs = read('launch-specs.json')
today = date.fromisoformat(run['date'])
sitemaps = sorted((W.parent).glob('*/reliance-sitemaps.json'))
urls = list(dict.fromkeys(u for r in json.loads(sitemaps[-1].read_text()) for u in r['urls'])) if sitemaps else []
def receipt(f, note):
    return {k: v for k, v in dict(source_url=f.get('final_url', f['source_url']), observed_at=f['observed_at'], http_status=f.get('http_status'), evidence_file=f.get('snapshot'), sha256=f.get('sha256'), outcome=note).items() if v is not None}
def one(s):
    key, name = s['key'], s['display_name']
    assert key not in db, key + ' already in catalogue'
    assert date.fromisoformat(s['first_sale']) <= today, key + ': first sale is in the future - hold it'
    assert s['launch_price'] % 1000 != 0, key + ': round launch price is the fabrication signature - verify it'
    row = dict(key=key, display_name=name, family=m.family(name), ram=m.ram_storage(name)[0], storage=m.ram_storage(name)[1], tier=s['tier'], category='phone')
    checks, attempts = [], []
    srch = m.search_family(row['family']); checks.append(receipt(srch['fetch'], 'Primary retailer discovery; no search-card price accepted without exact product verification'))
    for c in sorted(srch['cards'], key=lambda c: (c['unavailable'], c['search_price'] or 1e9)):
        fam, ram, store = m.identity(c['title'])
        if not m.family_match(m.norm(row['family']), fam) or store != row['storage'] or ram != row['ram']: continue
        raw, f = m.fetch(c['source_url']); a = m.parse_new(raw, f, row) if f.get('http_status') == 200 else dict(status='unverified', reason='fetch failed', fetch=f)
        attempts.append(a)
        if a['status'] == 'verified': break
    for u in urls:
        fam, ram, store = rel.identity(u.split('/product/')[-1].replace('-', ' '))
        if not (m.family_match(m.norm(row['family']), fam) and ram == row['ram'] and store == row['storage']) or 'demo' in u.lower(): continue
        raw, f = m.fetch(u); a = rel.parse(raw, f, row)
        if a['status'] == 'verified' and re.search('demo|open box', a['reference']['selected_title'], re.I): a = dict(status='unverified', reason='demo unit', fetch=f)
        attempts.append(a)
    for a in attempts: checks.append(receipt(a['fetch'], a.get('reason', a['status'])))
    refs = [a['reference'] for a in attempts if a['status'] == 'verified']; ref = min(refs, key=lambda x: x['amount_inr']) if refs else None
    lsrc = []
    for u in s['launch_sources']:
        raw, f = m.fetch(u); lsrc.append(receipt(f, 'India launch / first-sale source'))
    slug = re.sub('[^a-z0-9]+', '-', row['family'].lower()).strip('-'); raw, cf = m.fetch('https://www.cashify.in/buy-refurbished-mobile-phones/renewed-' + slug)
    entry = dict(display_name=name, tier=s['tier'], launch_date=s['first_sale'], launch_date_verified=bool(ref), net_new_inr=s['launch_price'], net_new_price_basis='official_launch_period_history_only',
                 launch_sources=lsrc + ([receipt(dict(source_url=ref['source_url'], observed_at=ref['observed_at'], http_status=200, snapshot=ref['evidence_file'], sha256=ref['sha256']), 'Exact variant in stock as a new INR cash offer today: on sale in India')] if ref else []),
                 price_reference_pending='Enter actual device age and a confirmed current new cash price. Independent A1 resale is not verified; no saved automatic offer.',
                 notes=f"India sale confirmed by an in-stock exact new listing on {run['date']}. Launch-period list price is historical only. No bank/exchange discount used; no independent used resale proof.")
    if s.get('foldable'): entry['is_foldable'] = True
    obs = dict(key=key, new_price_status='verified' if ref else 'unverified', resale_status='unverified', current_new_price=ref, new_price_checks=checks,
               note=f"New India variant (first sale {s['first_sale']}). " + ('Current new cash price verified from exact available listing.' if ref else 'Current new cash offer pending.') + ' Individual source observation dates preserved; Moradabad checkout/delivery not verified. Independent exact A1 resale unavailable; actual unit age required.')
    return dict(key=key, entry=entry, observation=obs, attempts=[{k: v for k, v in a.items() if k != 'evidence_excerpt'} for a in attempts], resale_check=receipt(cf, 'Cashify refurbished family page checked once; no exact A1 resale accepted'))
rows = list(concurrent.futures.ThreadPoolExecutor(max_workers=2).map(one, specs))
held = [dict(key=r['key'], reason='no exact in-stock new listing today') for r in rows if r['observation']['new_price_status'] != 'verified']
m.write(W / 'launch-proposals.json', [r for r in rows if r['observation']['new_price_status'] == 'verified']); m.write(W / 'launch-held.json', held)
for r in rows:
    ref = r['observation']['current_new_price']
    print(r['key'], r['observation']['new_price_status'], ref and (ref['amount_inr'], ref.get('retailer') or ref['source_url'].split('/')[2]))
print('proposed', len(rows) - len(held), 'held', len(held))
