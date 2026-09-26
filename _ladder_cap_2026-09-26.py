#!/usr/bin/env python3
"""Post-verification coherence pass (2026-09-26), applied after _apply_verified_2026-09-26.py.

1) PROPORTIONAL STORAGE-LADDER CAP. Verify+refute re-priced some Fold8/Flip8 trims off live Cashify ceilings while
   their siblings kept this week's weaker research. That left Fold8 12/256 at resale Rs1,07,000 and Fold8 12/512 at
   Rs1,49,000 — a Rs42,000 used step against a Rs20,000 new-price step — and pushed the standard Fold8 512/1TB above
   the Fold8 ULTRA 512/1TB. Used storage premiums compress; they never exceed the new-price step. So each larger trim's
   resale is capped at base_resale x (new_k / new_base), anchored on the family's verified base trim. Lowers only.
2) SIBLING REPAIR for the two Oppo A6s phantoms removed this week (8/128, 8/256; OPPO India newsroom lists 4/128 and
   6/128 only). The refuter confirmed both real configs but held them on thin resale. Removal and repair are one
   operation, so they are added 'estimated' at the refuter's own conservative indicative resale."""
import json, sys
DIR='/Users/shane/Documents/Claude/Projects/rt buyback tool'; TODAY='2026-09-26'; APPLY='--apply' in sys.argv
db=json.load(open(f'{DIR}/phone_db.json')); meta=db['_meta']; ph={k:v for k,v in db.items() if k!='_meta'}
def r100(n): return int(round(n/100.0))*100
def a1(e): return e['resale_target_a1']/(1+e['target_margin'])
FAMS={'samsung_z_fold_8_':['256','512','1tb'],'samsung_z_fold_8_ultra_':['256','512','1tb'],'samsung_z_flip_8_':['256','512']}
out=[]
for pre,ladder in FAMS.items():
    base=ph[pre+ladder[0]]; bres=base.get('market_resale_observed') or base['resale_target_a1']; bnew=base['net_new_inr']
    for st in ladder[1:]:
        k=pre+st; e=ph.get(k)
        if not e or not e.get('net_new_inr'): continue
        cap=r100(bres*e['net_new_inr']/bnew)
        obs=e.get('market_resale_observed') or e['resale_target_a1']
        cur=a1(e); new_a1=min(cur, cap/(1+e['target_margin']), cap*0.92)
        if obs>cap or new_a1<cur-50:
            out.append((k,round(cur),r100(new_a1),obs,cap))
            e['market_resale_observed']=min(obs,cap)
            e['resale_target_a1']=r100(r100(new_a1)*(1+e['target_margin']))
            e['calibration_status']='estimated'; e['calibration_date']=TODAY
            e['live_source']=(f"LADDER-CAP {TODAY}: resale capped at base {pre+ladder[0]} Rs{bres:,} x new-price ratio "
                              f"= Rs{cap:,} -> A1 Rs{r100(new_a1):,}")[:180]
print('LADDER CAP:'); [print(f'  {k:32s} A1 {c:>8,} -> {n:>8,}  (resale {o:,} capped to {cp:,})') for k,c,n,o,cp in out]
REPAIR=[('oppo_a6s_5g_4_128','Oppo A6s 5G 4/128GB',13000,18999),('oppo_a6s_5g_6_128','Oppo A6s 5G 6/128GB',14000,20999)]
for k,nm,rs,nn in REPAIR:
    if k in ph: continue
    m=0.25   # tier C floor (<24mo)
    ph[k]={'display_name':nm,'tier':'C','launch_date':'2026-03-18','resale_target_a1':r100(rs),'target_margin':m,
           'net_new_inr':nn,'market_resale_observed':rs,'calibration_status':'estimated','calibration_date':TODAY,
           'live_source':f"SIBLING-REPAIR {TODAY}: real India config (OPPO India newsroom) behind removed 8GB phantoms; refuter's conservative indicative resale Rs{rs:,} -> A1 Rs{r100(rs/(1+m)):,}. Re-research."[:180]}
    print(f'  ADDED {k}: A1 {r100(rs/(1+m)):,} (resale {rs:,}, new {nn:,})')
if APPLY:
    o={'_meta':meta}; o.update(ph)
    json.dump(o,open(f'{DIR}/phone_db.json','w'),ensure_ascii=False,indent=2)
    c='const DB = '+json.dumps(o,ensure_ascii=False,separators=(',',':'))+';'
    L=open(f'{DIR}/index.html').read().split('\n'); n=0
    for i,ln in enumerate(L):
        if ln.lstrip().startswith('const DB = {'): L[i]=ln[:len(ln)-len(ln.lstrip())]+c; n+=1
    assert n==1; open(f'{DIR}/index.html','w').write('\n'.join(L)); print('APPLIED')
json.dump({'ladder_cap':out,'repair':[r[0] for r in REPAIR]},open(f'{DIR}/_ladder_cap_{TODAY}.json','w'),indent=1)
