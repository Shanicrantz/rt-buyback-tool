#!/usr/bin/env python3
"""Read-only public market research. Does not change prices or contact sellers.

Collects exact-variant public retailer evidence, with resumable, hashed snapshots.
Only reviewed observations may be installed by _apply_market_observations.py.
"""
import argparse, concurrent.futures, gzip, hashlib, html, json, re, threading, uuid
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlencode, urlparse, parse_qs
import requests

ROOT = Path(__file__).resolve().parent
WORK = ROOT / '_weekly_refresh/2026-10-04-v6.19-all-running'
AS_OF = datetime.now(ZoneInfo('Asia/Kolkata')).date()
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
    def text(self):
        if self.tag in ('script','style'): return ''
        return ' '.join(x if isinstance(x,str) else x.text() for x in self.children).strip()
    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c,Node): yield from c.walk()

class DOM(HTMLParser):
    def __init__(self, raw):
        super().__init__(); self.root=Node(); self.stack=[self.root]; self.feed(raw)
    def handle_starttag(self,t,a):
        n=Node(t,a); self.stack[-1].children.append(n)
        if t not in VOID: self.stack.append(n)
    def handle_startendtag(self,t,a): self.handle_starttag(t,a); self.handle_endtag(t)
    def handle_endtag(self,t):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==t: self.stack=self.stack[:i]; break
    def handle_data(self,d): self.stack[-1].children.append(d)

def stamp(): return datetime.now(timezone.utc).isoformat(timespec='milliseconds')
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
    tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def family(name):
    return re.sub(r'\s*\(?\d+\s*(?:GB)?\s*/\s*\d+\s*(?:GB|TB)\)?.*$|\s+\d+\s*(?:GB|TB).*$', '',name,flags=re.I).strip()
def norm(name):
    s=name.lower().replace('motorola','moto').replace('xiaomi redmi','redmi').replace('apple ','').replace('+',' plus ')
    s=re.sub(r'\bmoto\s+moto\b','moto',s)
    # S25 base India listings append the chipset as marketing text. Restrict
    # this alias to that exact model; never merge FE/Plus or Exynos variants.
    s=re.sub(r'^samsung galaxy s25(?: 5g)? snapdragon$', 'samsung galaxy s25', s.strip())
    # 4G and 5G remain distinct. Limited aliases are handled explicitly below.
    return re.sub('[^a-z0-9]','',s)
def ram_storage(name):
    m=re.search(r'(\d+)\s*(?:GB)?\s*(?:RAM\s*)?/\s*(\d+)\s*(GB|TB)',name,re.I)
    if m:return int(m[1]),int(m[2])*(1024 if m[3].upper()=='TB' else 1)
    m=re.search(r'(\d+)\s*(GB|TB)',name,re.I)
    return None,(int(m[1])*(1024 if m[2].upper()=='TB' else 1) if m else None)
def identity(title):
    # Retail title, e.g. model (colour, 256 GB) (12 GB RAM).
    ram=re.search(r'(\d+)\s*GB\s*RAM',title,re.I)
    store=re.search(r',\s*(\d+)\s*(GB|TB)\)',title,re.I)
    fam=re.split(r'\([^)]*,\s*\d+\s*(?:GB|TB)\)',title,flags=re.I)[0].strip()
    return norm(fam),int(ram[1]) if ram else None,int(store[1])*(1024 if store[2].upper()=='TB' else 1) if store else None
def family_match(a,b):
    if a==b:return True
    # Retailers commonly append 5G to a model without a network suffix in DB.
    # Never bridge an explicitly named 4G model.
    return '4g' not in a+b and a.removesuffix('5g')==b.removesuffix('5g')

def resale_retail_allowance(entry):
    """Business estimate for retailer warranty/service, not device depreciation.

    Today's exact-model retail ask already reflects the model generation. Never
    deduct launch age again; the quote engine handles the customer's actual age.
    """
    return .15 if entry.get('tier') in ('C','D') or entry.get('is_foldable') or re.search(r'fold|flip|razr|magic v|find n|oneplus open',entry.get('display_name',''),re.I) else .10

def fetch(url):
    ident=hashlib.sha256(url.encode()).hexdigest()[:24]
    path=WORK/'research'/f'{ident}.json'
    if path.exists():
        meta=json.loads(path.read_text())
        same_day=datetime.fromisoformat(meta['observed_at']).astimezone(ZoneInfo('Asia/Kolkata')).date()==AS_OF
        if same_day and meta.get('http_status') in (200,404):
            cached=gzip.decompress((WORK/'research'/meta['snapshot']).read_bytes())
            if hashlib.sha256(cached).hexdigest()==meta['sha256']:
                return cached.decode(),meta
    meta={'source_url':url,'observed_at':stamp(),'method':'anonymous public HTTPS GET'}
    raw=''
    try:
        r=requests.get(url,timeout=18,headers={'User-Agent':'Mozilla/5.0'})
        raw=r.content.decode('utf-8',errors='replace');digest=hashlib.sha256(r.content).hexdigest()
        meta.update(http_status=r.status_code,final_url=r.url,sha256=digest,snapshot=ident+'-'+digest[:16]+'.html.gz')
        (WORK/'research'/meta['snapshot']).write_bytes(gzip.compress(r.content))
    except requests.RequestException as ex:meta['error']=str(ex)[:180]
    write(path,meta)
    return raw,meta

def ld(raw):
    out=[]
    for s in re.findall(r'<script[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>',raw,re.S|re.I):
        try:
            x=json.loads(s);out.extend(x if isinstance(x,list) else [x])
        except ValueError:pass
    return out

def catalogue_scope(db):
    """Every domestic catalogue variant, including old/discontinued/nonphones.

    International derived rows are accounted for separately; never copy an
    India new-price observation into another market as an independent price.
    """
    rows=[];derived=[]
    for key,entry in db.items():
        if key=='_meta':continue
        if entry.get('international'):
            derived.append({'key':key,'display_name':entry['display_name'],'status':'derived_international','note':'Review existing India-sibling derivation and regional rule; not an independent India cash-price observation.'})
            continue
        ram,storage=ram_storage(entry['display_name'])
        category=entry.get('category','phone')
        rows.append(dict(key=key,display_name=entry['display_name'],family=family(entry['display_name']),ram=ram,storage=storage,tier=entry['tier'],category=category,research_route='phone_collectors_then_primary_sources' if category=='phone' else 'category_specific_primary_sources',reasons=['full catalogue: no age, tier, popularity, discontinued or batch-count exclusion']))
    return {'policy':'all-catalogue-v1','definition':'Every domestic catalogue model and exact RAM/storage/size/connectivity variant, including old, discontinued, budget and nonphone entries. No fixed sample or launch-age filter. International derived records are separately accounted for and retain their existing regional derivation. Missing current stock or evidence remains pending, not freshly priced.','catalogue_count':len(db)-1,'models':rows,'derived_models':derived}

def validate_scope_coverage(payload, db):
    expected={r['key'] for r in catalogue_scope(db)['models']}
    rows=payload['models'];keys=[r['key'] for r in rows]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate model results')
    actual=set(keys)
    if actual!=expected:raise ValueError(f'Full catalogue coverage mismatch: {len(expected-actual)} missing, {len(actual-expected)} unexpected variants')
    for row in rows:
        if row.get('new_price_status') not in ('verified','unavailable','unverified'):raise ValueError('Missing per-variant current-new-price result: '+row['key'])
        if row['new_price_status']=='verified' and not row.get('current_new_price'):raise ValueError('Verified result lacks price evidence: '+row['key'])
        if row['new_price_status']!='verified' and not row.get('note'):raise ValueError('Pending result lacks reason: '+row['key'])
        if row['new_price_status']!='verified':
            checks=row.get('new_price_checks',[])
            if not checks or any(not c.get('observed_at') or not c.get('source_url','').startswith('https://') or not c.get('outcome') for c in checks):raise ValueError('Pending result lacks dated source checks: '+row['key'])
    return {'catalogue_count':len(db)-1,'researched_scope':len(expected),'derived_international':sum(bool(e.get('international')) for k,e in db.items() if k!='_meta'),'results_complete':True,'price_coverage':'partial' if any(r['new_price_status']!='verified' for r in rows) else 'verified'}

def initialize():
    WORK.mkdir(exist_ok=True,parents=True);(WORK/'research').mkdir(exist_ok=True)
    db=json.loads((ROOT/'phone_db.json').read_text())
    if not (WORK/'baseline').exists():
        (WORK/'baseline').mkdir()
        for f in ['phone_db.json','index.html','sw.js','manifest.webmanifest','RT-BUYBACK-KNOWLEDGE-EXPORT.md']:
            (WORK/'baseline'/f).write_bytes((ROOT/f).read_bytes())
    document=catalogue_scope(db);scope=document['models']
    if (WORK/'scope.json').exists():
        saved=json.loads((WORK/'scope.json').read_text())
        if saved.get('policy')!=document['policy'] or saved['models']!=scope:raise ValueError('Existing scope differs. Use a fresh dated work folder; do not overwrite a prior refresh scope.')
    write(WORK/'scope.json',{'created_at':stamp(),**document})
    print('Scope:',len(scope),'variants;',len(document['derived_models']),'international derivations;',len(set(x['family'] for x in scope)),'family labels',flush=True)

def search_family(fam):
    url='https://www.flipkart.com/search?'+urlencode({'q':fam})
    raw,meta=fetch(url);cards=[]
    if meta.get('http_status')==200:
        dom=DOM(raw)
        for node in dom.root.walk():
            if not node.attrs.get('data-id','').startswith('MOB'):continue
            nodes=list(node.walk());imgs=[x for x in nodes if x.tag=='img' and x.attrs.get('alt')]
            links=[x.attrs['href'] for x in nodes if x.tag=='a' and '/p/' in x.attrs.get('href','')]
            if not imgs or not links:continue
            title=imgs[0].attrs['alt'];text=node.text()
            ram=re.search(r'(\d+)\s*GB\s*RAM',text,re.I)
            if ram and 'GB RAM' not in title:title+=f' ({ram[1]} GB RAM)'
            price=re.search(r'₹\s*([\d,]+)',text)
            u=urljoin('https://www.flipkart.com',links[0]);q=parse_qs(urlparse(u).query)
            u=u.split('?')[0]+'?pid='+q.get('pid',[''])[0]
            cards.append(dict(title=title,source_url=u,search_price=int(price[1].replace(',','')) if price else None,unavailable='Currently unavailable' in text,search_url=url))
    return {'family':fam,'fetch':meta,'cards':cards}

def collect_search():
    scope=json.loads((WORK/'scope.json').read_text())['models'];families=list(dict.fromkeys(x['family'] for x in scope))
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(search_family,families):
            rows.append(r)
            if len(rows)%40==0:print('New-price search',len(rows),'/',len(families),flush=True);write(WORK/'search-results.json',rows)
    write(WORK/'search-results.json',rows);print('New-price searches complete',len(rows),flush=True)

def parse_new(raw,meta,row):
    if row.get('category','phone')!='phone':return {'status':'unverified','reason':'category-specific identity check required','fetch':meta}
    ps=[x for x in ld(raw) if x.get('@type')=='Product']
    if len(ps)!=1:return {'status':'unverified','reason':'missing unique product schema','fetch':meta}
    p=ps[0];of=p.get('offers',{});title=p.get('name','');fam,ram,storage=identity(title)
    # RAM often lives in the description/specifications rather than schema title.
    dom=DOM(raw);text=re.sub(r'\s+',' ',dom.root.text())
    if ram is None:
        m=re.search(r'(\d+)\s*GB\s*RAM',p.get('description',''),re.I) or re.search(r'RAM\s+(\d+)\s*GB',text,re.I)
        if m:ram=int(m[1])
    if not family_match(norm(row['family']),fam) or storage!=row['storage'] or (row['ram'] is not None and ram!=row['ram']):
        return {'status':'unverified','reason':'exact variant mismatch','title':title,'detected':[fam,ram,storage],'fetch':meta}
    if not str(of.get('availability','')).endswith('/InStock'):
        return {'status':'unavailable','reason':'selected variant out of stock','title':title,'fetch':meta}
    if of.get('priceCurrency')!='INR' or not str(of.get('itemCondition','')).endswith('/NewCondition'):
        return {'status':'unverified','reason':'not new INR offer','fetch':meta}
    amount=float(of['price']);fees=re.findall(r'\+\s*₹\s*([\d,]+)\s*(?:Protect Promise|Secured Packaging|Secure Packaging|Handling|Platform)[^₹]{0,25}?Fee',text,re.I)
    fees=list(set(int(x.replace(',','')) for x in fees))
    if len(fees)>1:return {'status':'unverified','reason':'multiple mandatory fee types need review','fetch':meta}
    fee=fees[0] if fees else 0
    if not re.search(r'₹\s*'+re.escape(f'{int(amount):,}')+r'\b',text) and str(int(amount)) not in text.replace(',',''):
        return {'status':'unverified','reason':'schema price absent from page','fetch':meta}
    ref=dict(kind='retail_cash_price',variant_name=row['display_name'],amount_inr=int(amount+fee),selling_price_inr=int(amount),mandatory_fees_inr=fee,observed_at=meta['observed_at'],source_url=meta['final_url'],available=True,market='India',condition='new',requires_exchange=False,requires_bank_offer=False,availability_scope='India public selected-variant listing; Moradabad pincode and checkout not checked',evidence_file=meta['snapshot'],sha256=meta['sha256'],selected_title=title,selected_ram_gb=ram,selected_storage_gb=storage)
    return {'status':'verified','reference':ref,'fetch':meta,'evidence_excerpt':text[max(0,text.find(title, len(title))):][:950]}

def collect_new():
    scope=json.loads((WORK/'scope.json').read_text())['models'];search=json.loads((WORK/'search-results.json').read_text());cards=[c for r in search for c in r['cards']]
    cached={r['key']:r for r in json.loads((WORK/'new-results.json').read_text())} if (WORK/'new-results.json').exists() else {}
    index={}
    for c in cards:
        f,ram,store=identity(c['title']);index.setdefault((f.removesuffix('5g'),store),[]).append((ram,c))
    def one(row):
        if cached.get(row['key'],{}).get('new_price_status') in ('verified','unavailable'):return cached[row['key']]
        matching=[c for ram,c in index.get((norm(row['family']).removesuffix('5g'),row['storage']),[]) if row['ram'] is None or ram==row['ram']]
        matching.sort(key=lambda c:(c['unavailable'],c['search_price'] or 1e9))
        seen=set();attempts=[]
        for c in matching:
            if c['source_url'] in seen:continue
            seen.add(c['source_url']);raw,meta=fetch(c['source_url'])
            result=parse_new(raw,meta,row) if meta.get('http_status')==200 else {'status':'unverified','reason':'fetch failed','fetch':meta}
            attempts.append(result)
            if result['status']=='verified':break
        accepted=next((r for r in attempts if r['status']=='verified'),None)
        return {'key':row['key'],'new_price_status':'verified' if accepted else 'unavailable' if attempts and all(r['status']=='unavailable' for r in attempts) else 'unverified','current_new_price':accepted['reference'] if accepted else None,'attempts':attempts,'search_checked':True}
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for r in pool.map(one,scope):
            rows.append(r)
            if len(rows)%75==0:print('Exact new variants',len(rows),'/',len(scope),'accepted',sum(x['new_price_status']=='verified' for x in rows),flush=True);write(WORK/'new-results.json',rows)
    write(WORK/'new-results.json',rows)

def collect_gaps():
    scope={r['key']:r for r in json.loads((WORK/'scope.json').read_text())['models']}
    before=json.loads((WORK/'new-results.json').read_text());rows=json.loads((WORK/'search-results.json').read_text())
    pending=[scope[r['key']] for r in before if r['new_price_status']=='unverified' and scope[r['key']]['storage'] is not None]
    queries=[r['family']+f" {r['storage']} GB"+(f" {r['ram']} GB RAM" if r['ram'] else '') for r in pending]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i,r in enumerate(pool.map(search_family,queries),1):
            rows.append(r)
            if i%50==0:print('Exact-variant gap searches',i,'/',len(queries),flush=True);write(WORK/'search-results.json',rows)
    write(WORK/'search-results.json',rows)

def collect_resale():
    scope=json.loads((WORK/'scope.json').read_text())['models'];families=list(dict.fromkeys(r['family'] for r in scope if r.get('category','phone')=='phone'))
    db=json.loads((WORK/'baseline/phone_db.json').read_text())
    known=set()
    for e in db.values():known.update(re.findall(r'https://www.cashify.in/buy-refurbished-mobile-phones/renewed-[a-z0-9-]+',json.dumps(e)))
    raw,_=fetch('https://www.cashify.in/buy-refurbished-mobile-phones')
    known.update('https://www.cashify.in'+x for x in re.findall(r'/buy-refurbished-mobile-phones/renewed-[a-z0-9-]+',raw))
    def one(fam):
        n=norm(fam);slug=re.sub('[^a-z0-9]+','-',fam.lower().replace('+',' plus ')).strip('-')
        if slug.startswith('iphone-'):slug='apple-'+slug
        if slug.startswith('moto-'):slug='motorola-'+slug[5:]
        urls=[u for u in known if family_match(norm(u.split('renewed-')[1].replace('-',' ')),n)]
        guesses=[slug,slug+'-5g' if not slug.endswith('5g') else slug[:-3]]
        urls+=['https://www.cashify.in/buy-refurbished-mobile-phones/renewed-'+s for s in guesses]
        attempts=[];variants=[]
        for u in dict.fromkeys(urls):
            raw,meta=fetch(u);attempts.append(meta)
            if meta.get('http_status')!=200:continue
            structured=ld(raw)
            groups=[g for g in structured if g.get('@type')=='ProductGroup' and family_match(norm(g.get('name','').split(' - Refurbished')[0]),n)]
            if not groups:continue
            # The selected product is omitted from hasVariant on these pages.
            # Add its independently labelled storage/grade offer as well.
            for product in structured:
                if product.get('@type')!='Product' or not family_match(norm(product.get('name','').split(' - Refurbished')[0]),n):continue
                props={p.get('propertyID'):p.get('value') for p in product.get('additionalProperty',[])}
                selected=dict(product,description=str(props.get('refurbishment-grade',''))+', '+str(props.get('storage','')))
                groups.append({'hasVariant':[selected]})
            for g in groups:
                for v in g.get('hasVariant',[]):
                    desc=v.get('description','');of=v.get('offers',{});ram,storage=ram_storage(desc)
                    if not re.search(r'\bSuperb\b',desc) or of.get('priceCurrency')!='INR' or not str(of.get('availability','')).endswith('/InStock'):continue
                    if not str(of.get('itemCondition','')).endswith('/RefurbishedCondition'):continue
                    variants.append(dict(family=fam,ram=ram,storage=storage,amount_inr=float(of['price']),grade='Superb',title=v['name'],source_url=of['url'],family_source_url=meta['final_url'],observed_at=meta['observed_at'],sha256=meta['sha256'],evidence_file=meta['snapshot'],kind='refurb_retail_asking',available=True))
            break
        return {'family':fam,'attempts':attempts,'variants':variants}
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for r in pool.map(one,families):
            rows.append(r)
            if len(rows)%40==0:print('Resale families',len(rows),'/',len(families),'with Superb stock',sum(bool(x['variants']) for x in rows),flush=True);write(WORK/'resale-results.json',rows)
    write(WORK/'resale-results.json',rows)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['init','search','new','resale','gaps','coverage']);ap.add_argument('--work',type=Path);ap.add_argument('--as-of',type=date.fromisoformat);ap.add_argument('--observations',type=Path);a=ap.parse_args()
    if a.as_of:AS_OF=a.as_of
    if a.work:WORK=a.work.resolve()
    if not a.work and AS_OF!=date(2026,10,4):ap.error('Provide a new dated --work folder for this refresh.')
    if a.stage=='coverage':
        if not a.observations:ap.error('coverage requires --observations')
        print(json.dumps(validate_scope_coverage(json.loads(a.observations.read_text()),json.loads((ROOT/'phone_db.json').read_text())),indent=2))
    else:{'init':initialize,'search':collect_search,'new':collect_new,'resale':collect_resale,'gaps':collect_gaps}[a.stage]()
