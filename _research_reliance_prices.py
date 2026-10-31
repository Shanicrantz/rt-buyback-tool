"""Read-only exact-variant new-price checks from the public retailer sitemap."""
import argparse, concurrent.futures, gzip, json, re
from pathlib import Path
import _market_refresh_runner as m

def identity(title):
    title=title.replace('-', ' ')
    specs=list(re.finditer(r'(\d+)\s*(GB|TB)\b',title,re.I))
    ram=re.search(r'(\d+)\s*GB\s*RAM',title,re.I)
    stores=[x for x in specs if not re.match(r'\s*RAM',title[x.end():],re.I)]
    if not stores:return '',None,None
    store=stores[0]
    name=title[:min(x.start() for x in specs)].strip(' ,(')
    if name.lower().startswith('galaxy '):name='Samsung '+name
    return m.norm(name),int(ram[1]) if ram else None,int(store[1])*(1024 if store[2].upper()=='TB' else 1)

def parse(raw,meta,row):
    if row.get('category','phone')!='phone':return {'status':'unverified','reason':'category-specific identity check required','fetch':meta}
    products=[x for x in m.ld(raw) if x.get('@type')=='Product']
    if meta.get('http_status')!=200 or len(products)!=1:return {'status':'unverified','reason':'missing unique product / HTTP 200','fetch':meta}
    p=products[0];title=p.get('name','');f,ram,storage=identity(title);offer=p.get('offers',{})
    if ram is None:
        match=re.search(r'(\d+)\s*GB\s*RAM',p.get('description',''),re.I)
        if match:ram=int(match[1])
    if not m.family_match(m.norm(row['family']),f) or storage!=row['storage'] or row['ram'] is not None and ram!=row['ram']:
        return {'status':'unverified','reason':'exact variant mismatch','title':title,'detected':[f,ram,storage],'fetch':meta}
    if not isinstance(offer,dict) or not offer.get('availability','').endswith('/InStock'):
        return {'status':'unavailable','reason':'selected variant not in stock','title':title,'fetch':meta}
    if offer.get('priceCurrency')!='INR' or not offer.get('itemCondition','').endswith('/NewCondition') or re.search('refurbished|renewed|open box',title,re.I):
        return {'status':'unverified','reason':'not new INR cash listing','fetch':meta}
    amount=float(offer['price']);text=re.sub(r'\s+',' ',m.DOM(raw).root.text())
    displayed=[float(x.replace(',','')) for x in re.findall(r'₹\s*([\d,]+(?:\.\d+)?)',text)]
    if amount not in displayed or not 0<amount<=2000000:
        return {'status':'unverified','reason':'price not displayed','fetch':meta}
    if 'Free Shipping' not in text or re.search(r'(?:packaging|platform|handling)\s+(?:fee|charge)',text,re.I):
        return {'status':'unverified','reason':'shipping / mandatory fees need review','fetch':meta}
    ref=dict(kind='retail_cash_price',variant_name=row['display_name'],amount_inr=int(amount),selling_price_inr=int(amount),mandatory_fees_inr=0,observed_at=meta['observed_at'],source_url=meta['final_url'],available=True,market='India',condition='new',requires_exchange=False,requires_bank_offer=False,availability_scope='India public exact listing, Free Shipping displayed; Moradabad delivery/checkout not checked',evidence_file=meta['snapshot'],sha256=meta['sha256'],selected_title=title,selected_ram_gb=ram,selected_storage_gb=storage,retailer='Reliance Digital')
    return {'status':'verified','reference':ref,'fetch':meta}

def collect(work):
    m.WORK=work
    scope=json.loads((work/'scope.json').read_text())['models']
    urls=list(dict.fromkeys(u for r in json.loads((work/'reliance-sitemaps.json').read_text()) for u in r['urls']))
    index={}
    for u in urls:
        title=u.split('/product/')[-1].replace('-',' ')
        f,ram,storage=identity(title)
        if storage:index.setdefault((f.removesuffix('5g'),storage),[]).append((ram,u))
    def one(row):
        candidates=[u for ram,u in index.get((m.norm(row['family']).removesuffix('5g'),row['storage']),[]) if row['ram'] is None or ram==row['ram']]
        # Check every matching colour: no arbitrary three-seller cutoff.
        attempts=[]
        for u in candidates:
            raw,meta=m.fetch(u)
            if meta.get('snapshot'):raw=gzip.decompress((work/'research'/meta['snapshot']).read_bytes()).decode('utf8')
            attempts.append(parse(raw,meta,row))
        accepted=[x['reference'] for x in attempts if x['status']=='verified']
        return {'key':row['key'],'attempts':attempts,'reference':min(accepted,key=lambda x:x['amount_inr']) if accepted else None}
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for r in pool.map(one,scope):
            rows.append(r)
            if len(rows)%100==0:
                m.write(work/'reliance-results.json',rows)
                print('Reliance scope',len(rows),'/',len(scope),'accepted',sum(bool(x['reference']) for x in rows),flush=True)
    m.write(work/'reliance-results.json',rows)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();collect(a.work.resolve())
