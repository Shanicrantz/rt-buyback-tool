'use strict';
// v6.39: iPhone damage deduction per part, before (Apple service estimate) vs after (market original + fitting), through each engine.
const fs=require('fs'),vm=require('vm'),W=__dirname;
function engine(file){const h=fs.readFileSync(file,'utf8'),ctx=vm.createContext({Date,URL,Intl});vm.runInContext(h.slice(h.indexOf('const TIER_FACTOR'),h.indexOf('// ============ UI STATE'))+'\n'+h.slice(h.indexOf('const FOLDABLE_OOW_RISK'),h.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={partCost,currentNewPrice};',ctx);return ctx.api;}
const A=engine(W+'/baseline/index.html'),B=engine(W+'/candidate/index.html'),today=new Date();
const old=JSON.parse(fs.readFileSync(W+'/baseline/phone_db.json','utf8')),db=JSON.parse(fs.readFileSync(W+'/candidate/phone_db.json','utf8'));
const rows=[];let otherChanged=0;
for(const [k,e] of Object.entries(db)){if(k==='_meta'||!e.part_prices)continue;const np=B.currentNewPrice(e,today)?.amount_inr??null;
 for(const dk of Object.keys(e.part_prices)){const before=A.partCost(old[k],dk,np),after=B.partCost(e,dk,np);
  if(old[k].part_prices[dk].brand!=='Apple'){if(before!==after)otherChanged++;continue;}
  rows.push({key:k,model:e.display_name,part:dk,before,after,diff:after-before,now:e.part_prices[dk].brand,sources:e.part_prices[dk].sources||null});}}
fs.writeFileSync(W+'/deduction-changes.json',JSON.stringify(rows,null,1));
const by=p=>{const r=rows.filter(x=>x.part===p),m=r.filter(x=>x.now==='Market'),s=m.map(x=>x.after/x.before).sort((a,b)=>a-b);return {variants:r.length,market:m.length,apple_kept:r.length-m.length,lower:r.filter(x=>x.diff<0).length,higher:r.filter(x=>x.diff>0).length,median_new_over_old:s.length?+s[Math.floor(s.length/2)].toFixed(2):null}};
console.log(JSON.stringify({rows:rows.length,non_apple_rows_changed:otherChanged,by_part:Object.fromEntries(['display','battery','back_panel','rear_camera'].map(p=>[p,by(p)]))},null,1));
