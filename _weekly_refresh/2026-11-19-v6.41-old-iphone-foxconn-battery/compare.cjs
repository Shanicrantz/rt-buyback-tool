'use strict';
// v6.41: every damage deduction, baseline (v6.40) vs candidate, through each engine; also vs the pre-v6.40 tier-% estimate.
const fs=require('fs'),vm=require('vm'),W=__dirname;
function engine(file){const h=fs.readFileSync(file,'utf8'),ctx=vm.createContext({Date,URL,Intl});vm.runInContext(h.slice(h.indexOf('const TIER_FACTOR'),h.indexOf('// ============ UI STATE'))+'\n'+h.slice(h.indexOf('const FOLDABLE_OOW_RISK'),h.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={partCost,currentNewPrice,DAMAGE_PARTS};',ctx);return ctx.api;}
const A=engine(W+'/baseline/index.html'),B=engine(W+'/candidate/index.html'),P=engine(W+'/../2026-11-19-v6.40-iphone-market-parts/baseline/index.html'),today=new Date();
const old=JSON.parse(fs.readFileSync(W+'/baseline/phone_db.json','utf8')),db=JSON.parse(fs.readFileSync(W+'/candidate/phone_db.json','utf8'));
const pre=JSON.parse(fs.readFileSync(W+'/../2026-11-19-v6.40-iphone-market-parts/baseline/phone_db.json','utf8'));
const rows=[];let other=0;
for(const [k,e] of Object.entries(db)){if(k==='_meta')continue;const np=B.currentNewPrice(e,today)?.amount_inr??null;
 for(const dk of Object.keys(B.DAMAGE_PARTS)){const a=A.partCost(old[k],dk,np),b=B.partCost(e,dk,np);
  if(dk==='battery'&&e.part_prices?.battery?.grade==='Foxconn')rows.push({key:k,model:e.display_name,pct_estimate_v639:P.partCost(pre[k],dk,np),original_v640:a,foxconn_v641:b});
  else if(a!==b)other++;}}
fs.writeFileSync(W+'/deduction-changes.json',JSON.stringify(rows,null,1));
console.log(JSON.stringify({battery_rows:rows.length,other_deductions_changed:other,lower_than_v640:rows.filter(r=>r.foxconn_v641<r.original_v640).length,above_old_pct:rows.filter(r=>r.foxconn_v641>r.pct_estimate_v639).length}));
for(const m of ['iPhone 7 32GB','iPhone XS Max 64GB','iPhone XR 64GB','iPhone 11 Pro 64GB','iPhone 6 16GB'])for(const r of rows.filter(r=>r.model===m))console.log(m.padEnd(20),'% est',r.pct_estimate_v639,'| original',r.original_v640,'| Foxconn',r.foxconn_v641);
