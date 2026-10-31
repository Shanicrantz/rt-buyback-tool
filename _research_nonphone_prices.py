"""Category-aware public price checks; ambiguous catalogue variants stay pending."""
import argparse, concurrent.futures, json, re
from pathlib import Path
from urllib.parse import urlencode,urljoin,urlparse,parse_qs
import _market_refresh_runner as m

def clean(s):
    s=s.lower().replace('+',' plus ').replace('wi-fi','wifi').replace('wi fi','wifi').replace('bluetooth','bt').replace('usb-c','usbc').replace('usb c','usbc')
    s=re.sub(r'(\d+)\s*(?:st|nd|rd|th)\s*(?:gen(?:eration)?)',r'\1gen',s)
    s=re.sub(r'\bgen(?:eration)?\s*(\d+)',r'\1gen',s)
    s=re.sub(r'\b(\d+)\s*mm\b',r'\1mm',s)
    s=re.sub(r'\ba17\s*pro\b','a17pro',s)
    s=s.replace('active noise cancellation','anc').replace('noise cancelling','anc')
    return re.sub(r'[^a-z0-9.]+',' ',s).strip()

def identity_problem(row,title,description=''):
    name=row['display_name'];cat=row['category'];t=clean(title);body=clean(title+' '+description)
    if re.search(r'case for|cover for|folio|sleeve|keyboard|screen protector|strap|protector|charging cable|stand for',t):return 'accessory listing'
    if re.search(r'premium tws|\(smartwatch\)|\(tws\)',name,re.I):return 'catalogue family lacks an exact purchasable model'
    core=m.family(name);core=re.sub(r'\bWiFi\b|GPS(?:\+Cell)?|\bBT\b|\bLTE\b','',core,flags=re.I)
    core=re.sub(r'\b\d+mm\b|\d+(?:\.\d+)?\s*"','',core,flags=re.I)
    core=clean(core).replace('apple ','')
    if 'ipad' in core and 'a16' in core:core=re.sub(r'\b11gen\b','',core)
    if 'ipad mini' in core and 'a17pro' in core:core=core.replace('mini 7','mini')
    if 'watch se 2' in core and 'watch se' in t and '2gen' in t:t=t.replace('2gen','2')
    # Names without a year in the title require the exact generation/chip below.
    expected_year=re.search(r'\b20\d{2}\b',core)
    if cat=='laptop':core=re.sub(r'\b20\d{2}\b','',core)
    required=core.split()
    if not all(re.search(r'(?<![a-z0-9])'+re.escape(word)+r'(?![a-z0-9])',t) for word in required):return 'model/generation identity mismatch'
    # A seller title mentioning a supported device is not that device (e.g.
    # third-party accessories). Require the actual brand/family at the start.
    branded=re.sub(r'^apple\s+(?:20\d{2}\s+)?','',t)
    if not branded.startswith(required[0]+' ') and branded!=required[0]:return 'different product brand'
    for qualifier in ['pro','plus','ultra','fe','se','lite','max','mini','air','go','classic','nord','active']:
        if qualifier in t.split() and qualifier not in required:return 'different model suffix '+qualifier
    if cat!='laptop':
        identity_words=[w for w in required if w not in ('anc','usbc') and not re.fullmatch(r'20\d{2}',w)]
        # Ignore a descriptive "in ear" insertion, never a model generation.
        model_text=t.replace(' in ear ',' ')
        pattern=r'(?<![a-z0-9])'+r'\s+'.join(map(re.escape,identity_words))+r'(?![a-z0-9])'
        match=re.search(pattern,model_text)
        if not match:return 'non-contiguous model identity / extra generation'
        tail=model_text[match.end():].strip().split()
        if tail and re.fullmatch(r'\d{1,2}|[a-z]',tail[0]) and (len(tail)<2 or tail[1] not in ('gb','tb','mm','inch','inches','cm','core')):return 'additional model generation/letter'
    if cat in ('tablet','laptop') and re.search(r'\b(?:4g|5g|lte|cellular)\b',t) and not re.search(r'\b(?:4g|5g|lte|cellular)\b',clean(name)):return 'unexpected cellular variant'
    if cat=='audio':
        if ('anc' in required)!=('anc' in t.split()):return 'ANC option mismatch'
        if 'usbc' in required and 'usbc' not in t:return 'connector not confirmed'
        return None
    if cat=='watch':
        mm=re.search(r'(\d+)mm',name,re.I)
        if mm and mm[1]+'mm' not in t:return 'case size not confirmed'
        cellular=bool(re.search(r'cell|lte',t))
        if bool(re.search(r'Cell|LTE',name,re.I))!=cellular:return 'watch connectivity mismatch'
        if 'GPS' in name and 'gps' not in t:return 'GPS not confirmed'
        return None
    # RAM/storage can be in schema description when the title omits specs.
    ram=row['ram'];storage=row['storage']
    capacities=[int(x)*(1024 if unit=='tb' else 1) for x,unit in re.findall(r'(\d+)\s*(gb|tb)\b',body)]
    if storage is None or storage not in capacities:return 'storage not confirmed'
    if ram is not None:
        pairs=re.findall(r'(\d+)\s*gb\s*(?:ram|unified memory|memory)|(?:ram|memory)\s*(\d+)\s*gb',body)
        confirmed={int(a or b) for a,b in pairs}
        compact=bool(re.search(r'\b'+str(ram)+r'\s*gb\s*'+str(storage)+r'\s*gb\b',body))
        if ram not in confirmed and not compact:return 'RAM not confirmed'
    if re.search(r'wifi',clean(name)) and (not re.search(r'\bwifi\b',t) or re.search(r'cellular|\blte\b|\b5g\b',t)):return 'tablet WiFi-only not confirmed'
    size=re.search(r'(\d+(?:\.\d+)?)\s*"',name)
    if size:
        allowed={float(size[1])}
        if cat=='laptop':allowed.add({13:13.6,14:14.2,15:15.3,16:16.2}.get(float(size[1]),float(size[1])))
        sizes={float(x) for x in re.findall(r'(\d+(?:\.\d+)?)\s*(?:inch|inches|\")',title.lower())}
        if not allowed&sizes:return 'display size not confirmed'
    return None

def parse(raw,meta,row,retailer):
    products=[p for p in m.ld(raw) if p.get('@type')=='Product']
    if meta.get('http_status')!=200 or len(products)!=1:return dict(status='unverified',reason='No unique product / HTTP200',fetch=meta)
    p=products[0];title=p.get('name','');problem=identity_problem(row,title,p.get('description',''))
    if problem:return dict(status='unverified',reason=problem,title=title,fetch=meta)
    offer=p.get('offers',{})
    if not isinstance(offer,dict) or not offer.get('availability','').endswith('/InStock'):return dict(status='unavailable',reason='Exact listing out of stock',title=title,fetch=meta)
    if offer.get('priceCurrency')!='INR' or not offer.get('itemCondition','').endswith('/NewCondition'):return dict(status='unverified',reason='Not new INR offer',fetch=meta)
    text=re.sub(r'\s+',' ',m.DOM(raw).root.text());amount=float(offer['price'])
    displayed=[float(x.replace(',','')) for x in re.findall(r'₹\s*([\d,]+(?:\.\d+)?)',text)]
    if amount not in displayed or not 0<amount<=2000000:return dict(status='unverified',reason='Price not visibly confirmed',fetch=meta)
    fees=re.findall(r'\+\s*₹\s*([\d,]+)\s*(?:Protect Promise|Secured Packaging|Secure Packaging|Handling|Platform)[^₹]{0,25}?Fee',text,re.I);fees={int(x.replace(',','')) for x in fees}
    if len(fees)>1:return dict(status='unverified',reason='Multiple fees need manual review',fetch=meta)
    if retailer=='Reliance Digital' and ('Free Shipping' not in text or re.search(r'(?:packaging|platform|handling)\s+(?:fee|charge)',text,re.I)):return dict(status='unverified',reason='Shipping/fees unconfirmed',fetch=meta)
    fee=sum(fees)
    ref=dict(kind='retail_cash_price',variant_name=row['display_name'],amount_inr=int(amount+fee),selling_price_inr=int(amount),mandatory_fees_inr=fee,observed_at=meta['observed_at'],source_url=meta['final_url'],available=True,market='India',condition='new',requires_exchange=False,requires_bank_offer=False,evidence_file=meta['snapshot'],sha256=meta['sha256'],selected_title=title,retailer=retailer,identity_parser='nonphone-v1',availability_scope='Public exact-category offer; Moradabad checkout not verified')
    return dict(status='verified',reference=ref,fetch=meta)

def collect(work):
    m.WORK=work;rows=[r for r in json.loads((work/'scope.json').read_text())['models'] if r['category']!='phone']
    urls=list(dict.fromkeys(u for s in json.loads((work/'reliance-sitemaps.json').read_text()) for u in s['urls']))
    def one(row):
        u='https://www.flipkart.com/search?'+urlencode({'q':row['display_name']});raw,meta=m.fetch(u);attempts=[];cards=[]
        for node in m.DOM(raw).root.walk():
            if not node.attrs.get('data-id'):continue
            nodes=list(node.walk());imgs=[n for n in nodes if n.tag=='img' and n.attrs.get('alt')];links=[n.attrs['href'] for n in nodes if n.tag=='a' and '/p/' in n.attrs.get('href','')]
            if not imgs or not links:continue
            title=imgs[0].attrs['alt'];url=urljoin('https://www.flipkart.com',links[0]);pid=parse_qs(urlparse(url).query).get('pid',[''])[0];url=url.split('?')[0]+('?pid='+pid if pid else '')
            cards.append({'title':title,'url':url})
            if identity_problem(row,title,node.text()):continue
            html,receipt=m.fetch(url);attempts.append(parse(html,receipt,row,'Flipkart'))
        # A broad product-family candidate scan; exact validation happens on the page.
        family_tokens=clean(row['display_name']).split()[:3]
        if family_tokens and family_tokens[0]=='apple':family_tokens=family_tokens[1:]
        if family_tokens and family_tokens[0]=='ipad':
            # Retailers call the base 11th generation iPad simply "iPad A16".
            # Discover the family broadly; enforce generation/chip on the page.
            family_tokens=['ipad']+([family_tokens[1]] if len(family_tokens)>1 and family_tokens[1] in ('air','pro','mini') else [])
        candidates=[u for u in urls if all(word in clean(u.split('/product/')[-1]).split() for word in family_tokens)]
        for u in candidates:
            slug=u.split('/product/')[-1].replace('-',' ')
            # Keep only plausible generations before fetching; actual title specs are decisive.
            if row['category']=='laptop' and not re.search(r'\bm[1-9]\b',slug):continue
            raw,receipt=m.fetch(u);result=parse(raw,receipt,row,'Reliance Digital');attempts.append(result)
        accepted=[a['reference'] for a in attempts if a['status']=='verified']
        return {'key':row['key'],'search':meta,'search_cards':cards,'attempts':attempts,'reference':min(accepted,key=lambda x:x['amount_inr']) if accepted else None,'reason':'Exact category identity / available cash offer required; ambiguous or unavailable offers remain pending'}
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for row in pool.map(one,rows):
            results.append(row)
            if len(results)%10==0:m.write(work/'nonphone-results.json',results);print('Nonphones',len(results),'/',len(rows),'accepted',sum(bool(r['reference']) for r in results),flush=True)
    m.write(work/'nonphone-results.json',results)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();collect(a.work.resolve())
