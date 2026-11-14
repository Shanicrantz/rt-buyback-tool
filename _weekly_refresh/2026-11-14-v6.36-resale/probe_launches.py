"""v6.36 new-launch gap check (pattern of v6.30 probe_launches.py). India phones whose first sale fell after the
last launch add and that are missing from the catalogue. Adds only variants with an exact, in-stock, new INR cash
listing fetched today (Flipkart product page or Reliance Digital product page); demo/open-box units excluded.
Launch-period price is history only. No resale is invented: one Cashify family GET is recorded, nothing accepted."""
import sys, json, re, hashlib, concurrent.futures
from pathlib import Path
sys.path.insert(0, '/Users/shane/Documents/Claude/Projects/rt buyback tool')
import _market_refresh_runner as m
import _research_reliance_prices as rel
W = Path(__file__).resolve().parent; m.WORK = W
read = lambda n: json.loads((W / n).read_text())
db = read('baseline/phone_db.json')
# key, display name, tier (normalised to the DB series), launch-period cash price, first India sale, foldable,
# family search, official/launch source, required text on that source
SPECS = [
 ('oppo_find_x10_12_256', 'Oppo Find X10 12/256GB', 'A', 139999, '2026-10-29', False),
 ('oppo_find_x10_12_512', 'Oppo Find X10 12/512GB', 'A', 169999, '2026-10-29', False),
 ('oppo_find_x10_pro_max_12_512', 'Oppo Find X10 Pro Max 12/512GB', 'A', 199999, '2026-10-29', False),
 ('infinix_gt_50_pro_12_256', 'Infinix GT 50 Pro 12/256GB', 'C', 69999, '2026-10-30', False),
]
LAUNCH_SOURCES = {
 'oppo': ['https://www.oppo.com/in/store/events/termsconditionsforfindx10serieslivestreamgiveaway', 'https://techenclave.com/news/items/oppo-launches-find-x10-phones-in-india-from-1-39-999-alongside-pad-mini-and-enco-x4'],
 'infinix': ['https://www.gsmarena.com/the_infinix_gt_50_pro_goes_official_in_india-news-75224.php'],
}
urls = list(dict.fromkeys(u for r in json.loads((W.parent / '2026-11-14-v6.35-weekly/reliance-sitemaps.json').read_text()) for u in r['urls']))
def receipt(f, note):
    return {k: v for k, v in dict(source_url=f.get('final_url', f['source_url']), observed_at=f['observed_at'], http_status=f.get('http_status'), evidence_file=f.get('snapshot'), sha256=f.get('sha256'), outcome=note).items() if v is not None}
launch_checks = {}
for brand, us in LAUNCH_SOURCES.items():
    launch_checks[brand] = []
    for u in us:
        raw, f = m.fetch(u); text = re.sub(r'\s+', ' ', m.DOM(raw).root.text()) if raw else ''
        launch_checks[brand].append(dict(fetch=f, text=text[:6000]))
def one(spec):
    key, name, tier, price, day, fold = spec
    assert key not in db, key
    row = dict(key=key, display_name=name, family=m.family(name), ram=m.ram_storage(name)[0], storage=m.ram_storage(name)[1], tier=tier, category='phone')
    checks, attempts = [], []
    s = m.search_family(row['family']); checks.append(receipt(s['fetch'], 'Primary retailer discovery; no search-card price accepted without exact product verification'))
    for c in sorted(s['cards'], key=lambda c: (c['unavailable'], c['search_price'] or 1e9)):
        fam, ram, store = m.identity(c['title'])
        if not m.family_match(m.norm(row['family']), fam) or store != row['storage'] or ram != row['ram']: continue
        raw, f = m.fetch(c['source_url']); a = m.parse_new(raw, f, row) if f.get('http_status') == 200 else dict(status='unverified', reason='fetch failed', fetch=f)
        attempts.append(a)
        if a['status'] == 'verified': break
    for u in urls:
        fam, ram, store = rel.identity(u.split('/product/')[-1].replace('-', ' '))
        if not (m.family_match(m.norm(row['family']), fam) and ram == row['ram'] and store == row['storage']): continue
        if 'demo' in u.lower():
            checks.append(dict(source_url=u, observed_at=m.stamp(), outcome='Demo-unit listing excluded: not a new retail unit')); continue
        raw, f = m.fetch(u); a = rel.parse(raw, f, row)
        if a['status'] == 'verified' and re.search('demo', a['reference']['selected_title'], re.I): a = dict(status='unverified', reason='demo unit', fetch=f)
        attempts.append(a)
    for a in attempts: checks.append(receipt(a['fetch'], a.get('reason', a['status'])))
    refs = [a['reference'] for a in attempts if a['status'] == 'verified']; ref = min(refs, key=lambda x: x['amount_inr']) if refs else None
    brand = 'oppo' if key.startswith('oppo') else 'infinix'
    lsrc = [receipt(c['fetch'], 'India launch / first-sale source') for c in launch_checks[brand]]
    slug = re.sub('[^a-z0-9]+', '-', row['family'].lower()).strip('-'); raw, f = m.fetch('https://www.cashify.in/buy-refurbished-mobile-phones/renewed-' + slug)
    entry = dict(display_name=name, tier=tier, launch_date=day, launch_date_verified=bool(ref), net_new_inr=price, net_new_price_basis='official_launch_period_history_only',
                 launch_sources=lsrc + ([receipt(dict(source_url=ref['source_url'], observed_at=ref['observed_at'], http_status=200, snapshot=ref['evidence_file'], sha256=ref['sha256']), 'Exact variant in stock as a new INR cash offer today: on sale in India')] if ref else []),
                 price_reference_pending='Enter actual device age and a confirmed current new cash price. Independent A1 resale is not verified; no saved automatic offer.',
                 notes='India sale confirmed by an in-stock exact new listing on 14 Nov 2026. Launch-period list price is historical only. No bank/exchange discount used; no independent used resale proof.')
    if fold: entry['is_foldable'] = True
    obs = dict(key=key, new_price_status='verified' if ref else 'unverified', resale_status='unverified', current_new_price=ref, new_price_checks=checks,
               note='New India variant (first sale ' + day + '). ' + ('Current new cash price verified from exact available listing.' if ref else 'Current new cash offer pending.') + ' Individual source observation dates preserved; Moradabad checkout/delivery not verified. Independent exact A1 resale unavailable; actual unit age required.')
    return dict(key=key, entry=entry, observation=obs, attempts=[{k: v for k, v in a.items() if k != 'evidence_excerpt'} for a in attempts], resale_check=receipt(f, 'Cashify refurbished family page checked once; no exact A1 resale accepted'))
rows = list(concurrent.futures.ThreadPoolExecutor(max_workers=2).map(one, SPECS))
m.write(W / 'launch-proposals.json', rows); m.write(W / 'launch-source-checks.json', launch_checks)
for r in rows:
    ref = r['observation']['current_new_price']
    print(r['key'], r['observation']['new_price_status'], ref and (ref['amount_inr'], ref.get('retailer') or ref['source_url'].split('/')[2], ref['selected_title']), [a.get('reason', a['status']) for a in r['attempts']])
for b, cs in launch_checks.items():
    for c in cs: print(b, c['fetch'].get('http_status'), c['text'][:300])
