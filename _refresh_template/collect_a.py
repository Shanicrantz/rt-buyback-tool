"""Weekly new-price refresh, phase A (template; copied into each dated run folder by new_run.sh): re-check every domestic variant on the existing sources.
Read-only public GETs; writes only into this work folder. Order:
  1. baseline + scope   2. re-fetch every saved exact new-price URL   3. Flipkart search -> exact product pages
  4. Flipkart exact-variant gap searches -> second product pass   5. Reliance Digital sitemap + nonphone categories
"""
from pathlib import Path
import sys, json, re, concurrent.futures
ROOT=Path('/Users/shane/Documents/Claude/Projects/rt buyback tool');sys.path.insert(0,str(ROOT))
import _market_refresh_runner as m
import _research_reliance_prices as reliance
import _research_nonphone_prices as nonphone
W=Path(__file__).resolve().parent;m.WORK=W
step=sys.argv[1] if len(sys.argv)>1 else 'all'
if step in('all','init'):m.initialize()
db=json.loads((W/'baseline/phone_db.json').read_text());scope={r['key']:r for r in json.loads((W/'scope.json').read_text())['models']}
if step in('all','saved'):
    def one(key):
        old=db[key]['current_new_price'];row=scope[key];raw,meta=m.fetch(old['source_url'])
        parsed=nonphone.parse(raw,meta,row,old['retailer']) if row['category']!='phone' else (reliance.parse if old.get('retailer')=='Reliance Digital' else m.parse_new)(raw,meta,row)
        return {'key':key,'previous_amount_inr':old['amount_inr'],'result':parsed}
    keys=[k for k,e in db.items() if k in scope and e.get('current_new_price')];rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for r in pool.map(one,keys):
            rows.append(r)
            if len(rows)%100==0:m.write(W/'saved-new-rechecks.json',rows);print('Saved exact sources',len(rows),'/',len(keys),flush=True)
    m.write(W/'saved-new-rechecks.json',rows)
    print('Saved-source recheck:',len(rows),'verified',sum(r['result']['status']=='verified' for r in rows),flush=True)
if step in('all','flipkart'):
    m.collect_search();m.collect_new();m.collect_gaps();m.collect_new()
    nr=json.loads((W/'new-results.json').read_text());print('Flipkart verified',sum(r['new_price_status']=='verified' for r in nr),'/',len(nr),flush=True)
if step in('all','reliance'):
    raw,meta=m.fetch('https://www.reliancedigital.in/sitemap.xml')
    maps=[u for u in re.findall(r'<loc>(.*?)</loc>',raw) if '/products/' in u]
    def sitemap(url):
        raw,meta=m.fetch(url);return {'fetch':meta,'urls':re.findall(r'<loc>(.*?)</loc>',raw)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(sitemap,maps))
    m.write(W/'reliance-sitemaps.json',results)
    print('Reliance sitemaps:',len(results),'product URLs:',sum(len(r['urls']) for r in results),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for f in [pool.submit(reliance.collect,W),pool.submit(nonphone.collect,W)]:f.result()
    rr=json.loads((W/'reliance-results.json').read_text());print('Reliance verified',sum(bool(r['reference']) for r in rr),flush=True)
print('PHASE A step',step,'done',flush=True)
