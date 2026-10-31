'use strict';
// Economic regressions against the shipped engine and the previous saved release.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
function engine(text){const ctx=vm.createContext({Date,URL,Intl});vm.runInContext(text.slice(text.indexOf('const TIER_FACTOR'),text.indexOf('// ============ UI STATE'))+'\n'+text.slice(text.indexOf('const FOLDABLE_OOW_RISK'),text.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={fullQuote,computeFinal,cashifyEconomicLimit,resolveValuation,currentNewPrice,resaleEconomics,damagePartsFor,cashifyDate};',ctx);return ctx.api;}
const api=engine(html),today=new Date('2026-10-04T12:00:00Z');
const c={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const e={display_name:'Test 8/128GB',tier:'B',target_margin:.25,market_resale_estimate:30000,calibration_date:'2026-10-04'};
const i={newPrice:50000,newPriceConfirmed:true,priceConfirmedAt:today.toISOString(),ageMode:'months',ageMonths:12};
const quote=(entry=e,input=i,condition=c,extra={})=>api.computeFinal(entry,api.fullQuote(entry,condition.under_warranty,0,input,today),{modelKey:'test',condition,today,...extra});
let checks=0,calculations=0;function test(name,fn){try{fn();checks++;}catch(err){err.message=name+': '+err.message;throw err;}}
test('base offer respects fresh resale without any competitor quote',()=>{
 const q=quote();assert.equal(q.formulaFinal,32500);assert.equal(q.final,24000);assert.equal(q.marketCapped,true);assert.equal(q.economics.margin,.2);
 // 25% legacy markup means resale / 1.25, not 25% gross margin.
 assert.equal(quote({...e,margin_basis:'gross'}).final,22500);
 assert.equal(quote({...e,target_margin:0}).final,27600); // Existing 8% floor remains.
});
test('explicit per-deal costs reduce both formula and economic caps once',()=>{
 assert.equal(quote(e,{...i,sellingCosts:750}).final,23200);
 const noMarket={...e,calibration_date:'2026-08-01'};
 assert.equal(quote(noMarket,{...i,sellingCosts:750}).final,31700);
 assert.equal(quote(e,{...i,sellingCosts:50000}).final,0);
 for(const sellingCosts of [-1,'100',NaN,Infinity,2000001])assert.equal(quote(e,{...i,sellingCosts}).valid,false);
});
test('only final rounding loses less than100 from the continuous formula',()=>{
 const q=quote({...e,calibration_date:'2026-08-01'},{...i,newPrice:53123},{...c,grade:'A2',kit:{box:false,bill:true,charger:true},battery_band:1});
 const exact=53123*.65*.9*.97*.95;
 assert.equal(q.final,28600);assert.ok(exact-q.final>=0&&exact-q.final<100);
});
test('stale missing or cross-variant resale is disclosed, not quietly freshened',()=>{
 for(const patch of [{calibration_date:'2026-09-23'},{calibration_date:'2026-10-05'},{calibration_date:'bad'},{market_resale_estimate:null},{market_resale_derived_from_key:'sibling'}]){
  const q=quote({...e,...patch});assert.ok(q.economics.problem);assert.equal(q.final,32500);
 }
 assert.equal(quote({...e,calibration_date:'2026-09-24'}).final,24000);
});
test('today counter resale overrides stale data and requires explicit reconfirmation',()=>{
 const input={...i,resalePrice:20000,resaleConfirmed:true,resaleConfirmedAt:today.toISOString()};
 assert.equal(quote({...e,calibration_date:'2026-01-01'},input).final,16000);
 for(const patch of [{resaleConfirmed:false},{resaleConfirmedAt:'2026-10-03T12:00:00Z'},{resaleConfirmedAt:'2026-10-05T12:00:00Z'},{resalePrice:NaN},{resalePrice:-1},{resalePrice:'20000'}])assert.equal(quote(e,{...input,...patch}).valid,false);
});
test('malformed condition and corrupt margins fail closed without NaN or crashes',()=>{
 for(const patch of [{grade:'X'},{kit:{}},{battery_band:9},{under_warranty:true,warranty_band:99},{damages:['unknown']},{damages:['display','display']}]){const q=quote(e,i,{...c,...patch});assert.equal(q.valid,false);assert.equal(q.final,0);}
 for(const target_margin of [-1,1,NaN,Infinity,'0.25'])assert.equal(quote({...e,target_margin}).valid,false);
 assert.equal(quote({...e,margin_basis:'unknown'}).valid,false);
 assert.equal(api.cashifyDate('2026-10-03T24:00:00Z'),null);
 assert.ok(api.resolveValuation(e,i,new Date('bad')).problem);
});
test('assessed Cashify uplift cannot spend protected margin or selling costs',()=>{
 const assessed={provider:'Cashify',kind:'assessed_quote',model_key:'test',condition:c,device_age_months:12,amount_inr:24000,observed_at:today.toISOString(),confirmed:true};
 const q=quote(e,{...i,sellingCosts:750},c,{sessionQuote:assessed});assert.equal(q.final,23200);assert.equal(q.cashify.target,24500);assert.equal(q.cashify.status,'cap_blocked');
 const r=quote(e,{...i,ageMonths:36},c,{sessionQuote:{...assessed,device_age_months:36,amount_inr:21000}});assert.equal(r.final,21500);assert.ok(r.final<=r.economics.limit);
});
test('repair breakdown uses the limiting resale base when margin cap binds',()=>{
 const q=quote(e,i,{...c,battery_band:1,damages:['battery']});
 assert.equal(q.final,21500);assert.equal(q.batteryDeducted,1200);assert.equal(q.dmgTotal,1300);
 assert.equal(q.batteryDeducted+q.dmgTotal,2500);assert.equal(q.formulaAmounts.dmgTotal,875);
});
test('all categories, warranties, grades, battery/kit/damage combinations stay within caps',()=>{
 for(const category of ['phone','tablet','laptop','watch','audio','foldable']){
  const entry={...e,category,is_foldable:category==='foldable'};
  for(const grade of ['A1','A2','B','C','D'])for(const battery_band of [0,1,2,3])for(let mask=0;mask<8;mask++)for(const warranty_band of [null,0,1,2,3]){
   const condition={...c,grade,battery_band,kit:{box:!!(mask&1),bill:!!(mask&2),charger:!!(mask&4)},under_warranty:warranty_band!==null,warranty_band};
   const base=quote(entry,{...i,sellingCosts:325},condition);
   for(const damage of [null,...Object.keys(api.damagePartsFor(entry))]){
    const q=quote(entry,{...i,sellingCosts:325},{...condition,damages:damage?[damage]:[]});calculations++;
    assert.ok(q.valid&&Number.isFinite(q.final)&&q.final>=0&&q.final%100===0);
    assert.ok(q.final<=q.economics.limit);assert.ok(q.final<=base.final,'damage raises offer');
   }
  }
 }
});
test('all catalogue variants are finite across seven ages with confirmed scenario prices',()=>{
 const db=JSON.parse(fs.readFileSync(__dirname+'/phone_db.json','utf8'));
 for(const [key,entry] of Object.entries(db))if(key!=='_meta')for(const ageMonths of [0,6,12,24,60,120,240]){
  const q=quote(entry,{...i,ageMonths,newPrice:100000,resalePrice:60000,resaleConfirmed:true,resaleConfirmedAt:today.toISOString(),sellingCosts:500});calculations++;
  assert.ok(q.valid&&Number.isFinite(q.final)&&q.final>=0,key);assert.ok(q.final<=q.economics.limit,key);
 }
});
console.log(JSON.stringify({passed:true,checks,calculations}));
