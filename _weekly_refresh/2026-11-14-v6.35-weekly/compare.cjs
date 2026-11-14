'use strict';
// No-age quick quote (A1, full kit, out of warranty) before vs after, for every scoped model.
// Header rebuilt 2026-11-14 (original v6.30 file was on the damaged 1TB drive); body as recovered.
const fs=require('fs'),vm=require('vm');
function engine(file){const h=fs.readFileSync(file,'utf8'),ctx=vm.createContext({Date,URL,Intl});vm.runInContext(h.slice(h.indexOf('const TIER_FACTOR'),h.indexOf('// ============ UI STATE'))+'\n'+h.slice(h.indexOf('const FOLDABLE_OOW_RISK'),h.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={counterQuote,computeFinal};',ctx);return ctx.api;}
const read=f=>JSON.parse(fs.readFileSync(__dirname+'/'+f,'utf8'));
const old=read('baseline/phone_db.json'),db=read('candidate/phone_db.json');
const before=engine(__dirname+'/baseline/index.html'),after=engine(__dirname+'/candidate/index.html'),today=new Date();
const condition={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
function amount(api,entry){if(!entry)return null;const q=api.counterQuote(entry,false,0,{},today);const result=api.computeFinal(entry,q,{modelKey:'comparison',condition,today});return result.valid?result.final:null;}
const rows=db._meta.last_scoped_market_refresh.scope.map(key=>({key,model:db[key].display_name,old_quick_estimate:amount(before,old[key]),new_quick_estimate:amount(after,db[key]),old_new_cash:old[key]?.current_new_price?.amount_inr??null,new_cash:db[key].current_new_price?.amount_inr??null,resale_estimate:db[key].current_resale_price?.amount_inr??null}));
fs.writeFileSync(__dirname+'/quote-comparison.json',JSON.stringify({at:today.toISOString(),condition,age:'unknown',rows},null,2)+'\n');
const changed=rows.filter(r=>r.old_quick_estimate!==null&&r.old_quick_estimate!==r.new_quick_estimate);
console.log(JSON.stringify({models:rows.length,changed:changed.length,largest:changed.sort((a,b)=>Math.abs(b.new_quick_estimate-b.old_quick_estimate)-Math.abs(a.new_quick_estimate-a.old_quick_estimate)).slice(0,25),added:rows.filter(r=>r.old_quick_estimate===null)},null,2));
