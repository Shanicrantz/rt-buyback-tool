"""v6.35 weekly new-price refresh (recovered from v6.32): assemble observations from this run's evidence and build the candidate.
Sources (all fetched today into ./research, each re-parsed from its hashed snapshot before use):
  Flipkart exact product pages, Reliance Digital sitemap products, category-specific nonphone offers,
  and a re-fetch of every previously saved exact new-price URL.
Resale is NOT re-researched in this run: no resale reference is added, refreshed or withdrawn.
"""
import sys, gzip, hashlib, json, re
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path('/Users/shane/Documents/Claude/Projects/rt buyback tool');W=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(W))
import _market_refresh_runner as m
import _research_reliance_prices as reliance
import _research_nonphone_prices as nonphone
from _apply_market_observations import build,validate
from variant_guard import network_conflict
m.WORK=W
read=lambda f:json.loads((W/f).read_text())
db=read('baseline/phone_db.json')
assert db==json.loads((ROOT/'phone_db.json').read_text()),'production DB moved since baseline: reconcile first'
assert (W/'baseline/index.html').read_bytes()==(ROOT/'index.html').read_bytes(),'production HTML moved since baseline'
scope=read('scope.json')
new={r['key']:r for r in read('new-results.json')};rel={r['key']:r for r in read('reliance-results.json')}
np={r['key']:r for r in read('nonphone-results.json')};saved={r['key']:r['result'] for r in read('saved-new-rechecks.json')}
ram_holds=read('ram-identity-holds.json')
searches={}
for s in read('search-results.json'):searches.setdefault(s['family'],[]).append(s)
catalogue_meta=read('research/'+hashlib.sha256(b'https://www.reliancedigital.in/sitemap.xml').hexdigest()[:24]+'.json')
now=datetime.now(timezone.utc)
def check(meta,outcome):
    return {k:v for k,v in dict(source_url=meta.get('final_url',meta['source_url']),observed_at=meta['observed_at'],outcome=outcome,http_status=meta.get('http_status'),evidence_file=meta.get('snapshot'),sha256=meta.get('sha256')).items() if v is not None}
def verify_new(ref,row):
    raw=gzip.decompress((W/'research'/ref['evidence_file']).read_bytes());assert hashlib.sha256(raw).hexdigest()==ref['sha256']
    meta=dict(http_status=200,observed_at=ref['observed_at'],final_url=ref['source_url'],source_url=ref['source_url'],snapshot=ref['evidence_file'],sha256=ref['sha256'])
    parsed=nonphone.parse(raw.decode(),meta,row,ref['retailer']) if row['category']!='phone' else (reliance.parse if ref.get('retailer')=='Reliance Digital' else m.parse_new)(raw.decode(),meta,row)
    assert parsed['status']=='verified' and parsed['reference']['amount_inr']==ref['amount_inr'],row['key']
    validate(ref,db[row['key']],True,now);return ref
CURVE=[[0,.85],[3,.80],[6,.75],[12,.65],[18,.58],[24,.50],[36,.38],[48,.28],[60,.20],[84,.10],[120,.05],[240,.03]]
def dep(mo):
    for i in range(1,len(CURVE)):
        (e,y1),(s0,y0)=CURVE[i],CURVE[i-1]
        if mo<=e:return y0+(y1-y0)*(mo-s0)/(e-s0)
    return CURVE[-1][1]
def markup_signal(entry,ref):
    """A 2+ year-old model listed above RT's own known new price (or far above what it re-sells for) is most
    likely third-party old stock. Used as the saved new price it would inflate actual-age quotes, so hold it."""
    if not ref or not entry.get('launch_date'):return None
    y,mo=map(int,entry['launch_date'][:7].split('-'));age=(now.year-y)*12+now.month-mo
    if age<24:return None
    p=ref['amount_inr'];nn=entry.get('net_new_inr')
    res=entry.get('market_resale_observed') or (entry.get('last_known_resale_price') or {}).get('amount_inr') or entry.get('resale_target_a1')
    why=[]
    if nn and p>1.10*nn:why.append(f'{p/nn:.2f}x RT known new price Rs{nn}')
    if res and p*dep(age)>1.5*res:why.append(f'actual-age quote Rs{round(p*dep(age))} would be {p*dep(age)/res:.2f}x saved resale Rs{res}')
    return f'Held: {age}-month-old model listed at Rs{p} ('+'; '.join(why)+'). Likely third-party old-stock listing; enter today\'s price at the counter.' if why else None
markup_holds=[]
def resale_fresh(entry):
    """A carried-over resale estimate counts as 'estimated' only inside the engine's 10-day market window
    (fixed 2026-11-14: v6.32's carry-over kept 'estimated' on references that had already expired)."""
    r=entry.get('current_resale_price')
    if not r or not r.get('observed_at'):return False
    age=(now-datetime.fromisoformat(r['observed_at'].replace('Z','+00:00'))).total_seconds()
    return 0<=age<=10*86400
rows=[];identity_holds=[];moves=[]
for row in scope['models']:
    key=row['key'];entry=db[key];candidates=[];checks=[];statuses=[]
    for result in [new[key],rel[key]]:
        ref=result.get('current_new_price') or result.get('reference')
        if ref:candidates.append(verify_new(ref,row))
        for a in result['attempts']:checks.append(check(a['fetch'],a.get('reason',a['status'])));statuses.append(a['status'])
    if key in np:
        r=np[key];checks.append(check(r['search'],'Category-specific exact-model search; product offers reviewed separately'))
        if r['reference'] and key!='redmi_pad_se_4_128':candidates.append(verify_new(r['reference'],row))
        for a in r['attempts']:checks.append(check(a['fetch'],a.get('reason',a['status'])));statuses.append(a['status'])
    if key in saved:
        r=saved[key];checks.append(check(r['fetch'],'Previously saved exact listing re-checked: '+r.get('reason',r['status'])));statuses.append(r['status'])
        if r.get('reference'):candidates.append(verify_new(r['reference'],row))
    for query in [row['family'],row['family']+(f" {row['storage']} GB" if row['storage'] else '')+(f" {row['ram']} GB RAM" if row['ram'] else '')]:
        for s in searches.get(query,[]):checks.append(check(s['fetch'],'Primary retailer discovery checked; no search-card price accepted without exact product verification'))
    checks.append(check(catalogue_meta,'Second retailer full current product sitemap searched for exact variant'))
    checks=list({(c['source_url'],c['outcome']):c for c in checks}.values())
    rejected=[r for r in candidates if network_conflict(row,r,scope['models'])]
    for r in rejected:
        identity_holds.append(dict(key=key,source_url=r['source_url'],selected_title=r['selected_title'],kind='new',reason='Separate base and 5G catalogue families; optional network alias rejected'))
        checks.append(dict(source_url=r['source_url'],observed_at=r['observed_at'],outcome='Rejected cross-network alias: catalogue has separate base and 5G families',evidence_file=r['evidence_file'],sha256=r['sha256']))
    candidates=[r for r in candidates if r not in rejected]
    if key in ram_holds:candidates=[];statuses=['unverified']
    ref=min(candidates,key=lambda x:x['amount_inr']) if candidates else None
    if key=='redmi_pad_se_4_128':ref=None
    # Review-only (2026-11-06): holding these raised some actual-age quotes (fallback to saved resale), so the
    # listing is kept as in v6.30 and the signal is reported for Shane instead of changing the price.
    signal=markup_signal(entry,ref)
    if signal:markup_holds.append(dict(key=key,model=entry['display_name'],source_url=ref['source_url'],amount_inr=ref['amount_inr'],reason=signal.replace('Held: ','Review: ').replace("; enter today's price at the counter",'')))
    held=None
    if held:
        markup_holds.append(dict(key=key,model=entry['display_name'],source_url=ref['source_url'],amount_inr=ref['amount_inr'],reason=held))
        checks.append(dict(source_url=ref['source_url'],observed_at=ref['observed_at'],outcome=held,evidence_file=ref['evidence_file'],sha256=ref['sha256']))
        ref=None;statuses=['unverified']
    note='Current new cash price '+('verified from exact available listing' if ref else 'pending: no acceptable available exact new offer in checked sources')+'. Individual source observation dates preserved; Moradabad checkout/delivery not verified. Resale not re-checked in this new-price refresh; any prior dated resale reference is retained unchanged, subject to its existing freshness limit.'
    if key in ram_holds:note+=' '+ram_holds[key]['reason']
    if held:note+=' '+held
    rows.append(dict(key=key,new_price_status='verified' if ref else 'unavailable' if statuses and all(s=='unavailable' for s in statuses) else 'unverified',current_new_price=ref,resale_status=('estimated' if resale_fresh(entry) and (entry.get('market_refresh') or {}).get('resale_status')=='estimated' else 'unverified'),new_price_checks=checks,note=note))
    old=(entry.get('current_new_price') or {}).get('amount_inr')
    if old or ref:moves.append(dict(key=key,model=entry['display_name'],before=old,after=ref['amount_inr'] if ref else None,retailer=(ref or {}).get('retailer') or ((ref or {}).get('source_url','').split('/')[2] if ref else None)))
version=sys.argv[1] if len(sys.argv)>1 else '6.35'
payload=dict(checked_at=m.stamp(),release_version=version,scope_policy='all-catalogue-v1',scope_definition=scope['definition'],research_manifest=str(W/'scope.json'),models=rows,
  changelog='14 November weekly full-catalogue NEW-price refresh: every domestic variant re-checked on Flipkart exact product pages, the Reliance Digital product sitemap, category-specific nonphone offers and every previously saved exact listing. Lowest verified exact in-stock new cash offer kept per variant; 2+ year-old models listed above the RT known new price are reported for review (not held); pending where no acceptable current offer exists (mostly discontinued models). Resale evidence not re-researched or changed.')
m.write(W/'old-model-markup-review.json',markup_holds);m.write(W/'variant-identity-holds.json',identity_holds);m.write(W/'new-price-moves.json',moves)
m.write(W/'observations.json',payload);m.write(W/'coverage-validation.json',m.validate_scope_coverage(payload,db))
candidate=build(payload,db,now);(W/'candidate').mkdir(exist_ok=True)
compact=json.dumps(candidate,ensure_ascii=False,separators=(',',':'))
(W/'candidate/phone_db.json').write_text(compact)
html=(W/'baseline/index.html').read_text()
html,n=re.subn(r'^const DB = (\{[^\r\n]*\});[ \t]*$',lambda _: 'const DB = '+compact+';',html,flags=re.M);assert n==1
(W/'candidate/index.html').write_text(html)
s=candidate['_meta']['last_scoped_market_refresh']
both=[x for x in moves if x['before'] and x['after']]
print(json.dumps(dict(scope=s['scope_count'],verified=s['new_prices_verified'],pending=s['new_prices_pending'],gained=sum(1 for x in moves if x['after'] and not x['before']),lost=sum(1 for x in moves if x['before'] and not x['after']),
  changed=sum(1 for x in both if x['before']!=x['after']),identity_holds=len(identity_holds),markup_holds=len(markup_holds)),indent=1))
