'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(process.argv[2]||__dirname+'/index.html','utf8');
const ctx=vm.createContext({Date,URL,Intl});
vm.runInContext(html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'))+'\n'+html.slice(html.indexOf('const FOLDABLE_OOW_RISK'),html.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={counterQuote,fullQuote,computeFinal};',ctx);
const a=ctx.api,now=new Date('2026-10-31T12:00:00Z');
const condition={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const e={display_name:'Test phone 8/128GB',tier:'B',target_margin:.25,market_resale_estimate:30000,calibration_date:'2026-10-30'};
const complete={newPrice:50000,newPriceConfirmed:true,priceConfirmedAt:now.toISOString(),resalePrice:30000,resaleConfirmed:true,resaleConfirmedAt:now.toISOString(),ageMonths:12};
function quote(entry,input={},c=condition,today=now){const q=a.counterQuote(entry,c.under_warranty,0,input,today);return {q,...a.computeFinal(entry,q,{modelKey:'test',condition:c,today})};}
let checks=0;function test(name,f){try{f();checks++;}catch(e){e.message=name+': '+e.message;throw e;}}
test('operational cap lowers offer without rewriting market evidence',()=>{
 const limited={...e,quote_safety:{max_raw_a1:22000}},snapshot=JSON.stringify(limited);
 assert.equal(quote(e).final,24000);const r=quote(limited);assert.equal(r.final,22000);assert.equal(r.q.debug.resaleReference,30000);assert.equal(r.q.debug.quoteSafetyApplied,true);assert.match(r.q.debug.basis,/conservative offer limit/);assert.equal(JSON.stringify(limited),snapshot);
 assert.equal(quote(limited,{sellingCosts:500}).final,21500);
});
test('invalid cap is a configuration error not an unlimited offer',()=>{for(const cap of [0,-1,NaN,Infinity,'22000'])assert.equal(quote({...e,quote_safety:{max_raw_a1:cap}}).valid,false);});
test('verified exact-age formula is unchanged',()=>{
 const limited={...e,quote_safety:{max_raw_a1:10000}};
 assert.equal(quote(limited,complete).final,quote(e,complete).final);
 assert.equal(quote(limited,complete).q.debug.quickEstimate,undefined);
});
test('pending gate rejects every incomplete or stale confirmation',()=>{
 const held={...e,quote_safety:{requires_counter_review:true,max_raw_a1:10000},current_new_price:{kind:'retail_cash_price',variant_name:e.display_name,amount_inr:50000,available:true,observed_at:now.toISOString(),source_url:'https://example.com/test',condition:'new',market:'India'}};
 const missing=[{}, {ageMonths:12}, {...complete,resalePrice:undefined}, {...complete,newPrice:undefined}, {...complete,ageMonths:undefined}, {...complete,resaleConfirmed:false}, {...complete,newPriceConfirmed:false}, {...complete,resaleConfirmedAt:'2026-10-30T12:00:00Z'}, {...complete,priceConfirmedAt:'2026-10-30T12:00:00Z'}, {...complete,ageMonths:-1}];
 for(const input of missing){const r=quote(held,input);assert.equal(r.valid,false,JSON.stringify(input));assert.match(r.q.debug.problem,/Price review required/);}
 const r=quote(held,complete);assert.equal(r.valid,true);assert.equal(r.final,quote(e,complete).final);
});
test('caps persist after source expiry and do not cause competitor uplift',()=>{
 const limited={...e,quote_safety:{max_raw_a1:22000}};
 const r=quote(limited,{},condition,new Date('2027-01-01T12:00:00Z'));assert.equal(r.final,22000);assert.equal(r.cashify.status,'estimate_only');assert.equal(r.cashify.uplift,0);
});
test('foldable risk and condition costs apply once to capped raw offer',()=>{
 const fold={...e,display_name:'Samsung Galaxy Z Fold 4 256GB',is_foldable:true};
 const b=quote(fold),same={...fold,quote_safety:{max_raw_a1:b.q.debug.rawA1}};
 assert.equal(quote(same).final,b.final);
 for(const grade of ['A1','A2','B','C'])for(const battery_band of [0,2]){
  const c={...condition,grade,battery_band};assert.equal(quote(same,{sellingCosts:500},c).final,quote(fold,{sellingCosts:500},c).final);
 }
});
const db=JSON.parse(html.match(/^const DB = (\{[^\n]+\});$/m)[1]);
test('all marked catalogue variants enforce the declared safety behavior',()=>{
 for(const [key,v]of Object.entries(db))if(v.quote_safety){
  const r=quote(v);
  if(v.quote_safety.requires_counter_review){assert.equal(r.valid,false,key);assert.equal(typeof v.price_reference_pending,'string');assert.equal(quote(v,complete).valid,true,key);}
  else {assert.equal(r.valid,true,key);assert.ok(r.q.debug.rawA1<=v.quote_safety.max_raw_a1+1e-8,key);}
 }
});
console.log(JSON.stringify({passed:true,checks}));
