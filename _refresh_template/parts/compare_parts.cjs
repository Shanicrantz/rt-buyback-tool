'use strict';
// Damage deduction per part, before (v6.36 tier %) vs after (official brand price), at each variant's current new price.
const fs=require('fs'),vm=require('vm'),W=__dirname;
function engine(file){const h=fs.readFileSync(file,'utf8'),ctx=vm.createContext({Date,URL,Intl});vm.runInContext(h.slice(h.indexOf('const TIER_FACTOR'),h.indexOf('// ============ UI STATE'))+'\n'+h.slice(h.indexOf('const FOLDABLE_OOW_RISK'),h.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={partCost,currentNewPrice};',ctx);return ctx.api;}
const A=engine(W+'/baseline/index.html'),B=engine(W+'/candidate/index.html'),today=new Date();
const old=JSON.parse(fs.readFileSync(W+'/baseline/phone_db.json','utf8')),db=JSON.parse(fs.readFileSync(W+'/candidate/phone_db.json','utf8'));
const rows=[];
for(const [k,e] of Object.entries(db)){if(k==='_meta'||!e.part_prices)continue;
 const np=B.currentNewPrice(e,today)?.amount_inr??null;
 for(const dk of Object.keys(e.part_prices)){const before=A.partCost(old[k],dk,np),after=B.partCost(e,dk,np);rows.push({key:k,model:e.display_name,part:dk,before,after,diff:after-before,brand:e.part_prices[dk].brand,new_price:np??e.net_new_inr??null});}}
const by=p=>{const r=rows.filter(x=>x.part===p);return {n:r.length,up:r.filter(x=>x.diff>0).length,down:r.filter(x=>x.diff<0).length,same:r.filter(x=>x.diff===0).length,median_ratio:(()=>{const s=r.map(x=>x.after/Math.max(1,x.before)).sort((a,b)=>a-b);return s.length?+s[Math.floor(s.length/2)].toFixed(2):null})()}};
const parts=[...new Set(rows.map(r=>r.part))];
fs.writeFileSync(W+'/deduction-changes.json',JSON.stringify(rows,null,1));
const halved=rows.filter(r=>r.part==='display'&&r.after<r.before*0.5);
console.log(JSON.stringify({rows:rows.length,by_part:Object.fromEntries(parts.map(p=>[p,by(p)])),display_below_half_of_old:halved.length},null,1));
for(const r of rows.filter(r=>r.part==='display'&&r.diff<0).sort((a,b)=>a.diff-b.diff).slice(0,12))console.log('DISPLAY DOWN',r.model.padEnd(34),r.before,'->',r.after,r.brand);
for(const r of rows.filter(r=>r.part==='display'&&r.diff>0).sort((a,b)=>b.diff-a.diff).slice(0,6))console.log('DISPLAY UP  ',r.model.padEnd(34),r.before,'->',r.after,r.brand);
