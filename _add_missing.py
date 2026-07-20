#!/usr/bin/env python3
"""Insert missing models found by the gap-audit workflow into phone_db.json + index.html.
Validates: dedupe vs existing keys + normalized display names, anti-overpay (resale<=0.90*new,
implied A1 < new), sane values. Writes both files, bumps meta."""
import json, glob, re, sys
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'
TODAY='2026-06-25'
DEFAULT_MARGIN={'S':0.18,'A':0.2,'B':0.22,'C':0.25,'D':0.3}
def round100(n): return int(round(n/100.0))*100
KNOWN_BRANDS={'iphone','apple','samsung','vivo','iqoo','realme','oppo','redmi','xiaomi','poco','oneplus',
 'google','moto','nothing','cmf','honor','asus','infinix','tecno','lava','itel','micromax','nokia',
 'ipad','macbook','lenovo','airpods','boat','noise','fire'}

d=json.load(open(f'{DIR}/phone_db.json'))
existing=set(k for k in d if k!='_meta')
# normalized display+storage signature of existing, to catch dup models under diff keys
def norm(s): return re.sub(r'[^a-z0-9]','',s.lower())
def sig(name):
    return norm(name)
existing_sig=set()
for k,v in d.items():
    if k=='_meta': continue
    existing_sig.add(sig(v.get('display_name','')))

# load proposals
props={}
files=sorted(glob.glob(f'{DIR}/_gaps/unit_*.json'))
errs=[]
for fp in files:
    try:
        o=json.load(open(fp))
        for m in o.get('missing',[]):
            k=m.get('key')
            if not k: continue
            # keep highest-confidence if dup across units
            if k in props:
                rank={'high':3,'medium':2,'low':1}
                if rank.get(m.get('confidence','low'),1)<=rank.get(props[k].get('confidence','low'),1): continue
            props[k]=m
    except Exception as e:
        errs.append((fp,str(e)))

added=[]; skipped_existing=0; skipped_dup_name=0; rejected=[]
from collections import Counter
by_brand=Counter()
for k,m in props.items():
    brand=k.split('_')[0]
    if brand not in KNOWN_BRANDS:
        rejected.append((k,'unknown brand prefix')); continue
    if k in existing:
        skipped_existing+=1; continue
    if sig(m['display_name']) in existing_sig:
        skipped_dup_name+=1; continue
    av=m.get('anchor_value'); fld=m.get('anchor_field'); tier=m.get('tier')
    if not isinstance(av,(int,float)) or av<=0:
        rejected.append((k,'bad anchor_value')); continue
    new_price=m.get('new_price'); margin=m.get('target_margin') or DEFAULT_MARGIN.get(tier,0.22)
    # anti-overpay
    if fld=='resale_target_a1' and isinstance(new_price,(int,float)) and new_price>0:
        if av>0.90*new_price: av=round100(0.90*new_price)
    # implied A1
    if fld=='resale_target_a1': impliedA1=av/(1+margin)
    elif fld=='refurb_retail_anchor_excellent': impliedA1=av*(m.get('market_factor') or 0.88)/(1+margin)
    elif fld=='cashify_exchange': impliedA1=av*1.10
    else: impliedA1=av
    if isinstance(new_price,(int,float)) and new_price>0 and impliedA1>=new_price:
        rejected.append((k,f'A1 {int(impliedA1)} >= new {int(new_price)}')); continue
    # build entry
    e={'display_name':m['display_name'],'tier':tier,'launch_date':m['launch_date']}
    if m.get('discontinued'): e['discontinued']=True
    e[fld]=round100(av)
    if m.get('target_margin'): e['target_margin']=m['target_margin']
    if fld=='refurb_retail_anchor_excellent' and m.get('market_factor'): e['market_factor']=m['market_factor']
    e['calibration_status']=m.get('calibration_status','estimated')
    e['calibration_date']=TODAY
    if m.get('source'): e['live_source']=m['source'][:160]
    d[k]=e; existing.add(k); existing_sig.add(sig(m['display_name']))
    added.append((k,m['display_name'],m['launch_date'],fld,round100(av))); by_brand[brand]+=1

# meta
ph=[k for k in d if k!='_meta']
d['_meta']['version']='4.7'
d['_meta']['v4_7_changelog']=(f"Completeness gap-audit ({TODAY}). 24 brand/series agents audited the full India lineup 2014-2026 vs the DB; "
 f"added {len(added)} missing model-variants (incl. May-Jun 2026 new launches). Anti-overpay enforced (resale<=90% of new, A1<new); "
 f"{skipped_existing} already-present + {skipped_dup_name} duplicate-name proposals skipped; {len(rejected)} rejected (bad/overpay). "
 f"Total phones now {len(ph)}.")

json.dump(d,open(f'{DIR}/phone_db.json','w'),ensure_ascii=False,indent=2)
compact='const DB = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';'
lines=open(f'{DIR}/index.html').read().split('\n')
rep=0
for i,ln in enumerate(lines):
    if ln.lstrip().startswith('const DB = {'): lines[i]=ln[:len(ln)-len(ln.lstrip())]+compact; rep+=1
open(f'{DIR}/index.html','w').write('\n'.join(lines))

print('=== ADD MISSING SUMMARY ===')
print('Proposal files:',len(files),'| unique proposed keys:',len(props))
if errs: print('PARSE ERRORS:',errs[:5])
print('ADDED:',len(added),'| skipped existing:',skipped_existing,'| skipped dup-name:',skipped_dup_name,'| rejected:',len(rejected))
print('index.html replaced:',rep,'| total phones now:',len(ph))
print('\nAdded by brand:')
for b,c in by_brand.most_common(): print(f'  {b}: {c}')
print('\n--- Newest additions (by launch_date) ---')
for k,nm,ld,fld,av in sorted(added,key=lambda x:x[2],reverse=True)[:40]:
    print(f'  {ld}  {nm:42s} [{fld}={av}]')
if rejected:
    print(f'\n--- Rejected ({len(rejected)}) ---')
    for k,r in rejected[:20]: print(f'  {k}: {r}')
