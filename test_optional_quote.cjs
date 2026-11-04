'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(__dirname+'/index.html','utf8'),db=JSON.parse(fs.readFileSync(__dirname+'/phone_db.json','utf8'));
const ctx=vm.createContext({Date,URL,Intl});
vm.runInContext(html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'))+'\n'+html.slice(html.indexOf('const FOLDABLE_OOW_RISK'),html.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={counterQuote,fullQuote,computeFinal,cashifyPolicyMessage};',ctx);
const api=ctx.api,today=new Date('2026-10-04T12:00:00Z');
const c={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const e={display_name:'Example 8/128GB',tier:'B',target_margin:.25,market_resale_estimate:30000,calibration_date:'2026-10-04',net_new_inr:50000};
const price={newPrice:50000,newPriceConfirmed:true,priceConfirmedAt:today.toISOString()};
function quote(entry=e,input={},condition=c,extra={}) {const q=api.counterQuote(entry,false,0,input,today);return {q,...api.computeFinal(entry,q,{modelKey:'example',condition,today,...extra})};}
let checks=0,catalogueChecks=0;function test(name,fn){try{fn();checks++;}catch(err){err.message=name+': '+err.message;throw err;}}
test('no entry required; unknown age and historical price remain unverified',()=>{
 const input={},r=quote(e,input);assert.ok(r.valid&&r.estimateOnly);assert.equal(r.final,24000);
 assert.equal(r.q.debug.months,null);assert.equal(r.q.debug.priceDate,null);assert.equal(r.q.debug.priceVerified,false);
 assert.equal(r.q.debug.ageLabel,'Age not supplied');assert.deepEqual(input,{});
 assert.equal(api.fullQuote(e,false,0,{},today).valid,false); // Strict engine is still strict.
});
test('blank date and range inputs do not create an assumed age',()=>{
 for(const input of [{ageMode:'date',purchaseDate:''},{ageMode:'range',ageRange:null},{ageMode:'months',ageMonths:null}]){
  const r=quote(e,input);assert.ok(r.valid&&r.estimateOnly);assert.equal(r.q.debug.months,null);assert.equal(r.final,24000);
 }
});
test('no new price available still permits a resale-based estimate without inventing a price',()=>{
 const r=quote({...e,net_new_inr:null});assert.equal(r.q.debug.price,null);assert.equal(r.final,24000);assert.ok(r.estimateOnly);
});
test('price only and age only remain estimates; both use original detailed formula',()=>{
 assert.ok(quote(e,price).estimateOnly);assert.equal(quote(e,price).q.debug.months,null);
 const age=quote(e,{ageMonths:36});assert.ok(age.estimateOnly);assert.equal(age.final,24000);assert.equal(age.q.debug.price,null); // Historical new price cannot drive depreciation.
 const full=quote(e,{...price,ageMonths:12});assert.equal(full.estimateOnly,false);assert.equal(full.final,24000);
 const strict=api.fullQuote(e,false,0,{...price,ageMonths:12},today);assert.equal(full.q.a1,strict.a1);
});
test('invalid supplied inputs never disappear into a plausible saved estimate',()=>{
 for(const input of [{newPrice:-1},{newPrice:NaN},{...price,newPriceConfirmed:false},{ageMonths:-1},{ageMonths:241},{ageMode:'date',purchaseDate:'2027-01-01'},{ageMode:'date',purchaseDate:'bad'},{ageMode:'range',ageRange:99},{ageMode:'bad'},{sellingCosts:-1},{resalePrice:30000}])assert.equal(quote(e,input).valid,false,JSON.stringify(input));
 for(const patch of [{target_margin:1},{margin_basis:'bad'}])assert.equal(quote({...e,...patch}).valid,false);
});
test('saved reference fallback and stale dates are never treated as current evidence',()=>{
 for(const field of ['market_resale_observed','market_resale_estimate','resale_target_a1','refurb_retail_anchor_excellent']){
  const r=quote({...e,market_resale_estimate:null,[field]:30000,calibration_date:'2026-01-01'});
  assert.equal(r.final,24000);assert.ok(r.estimateOnly);assert.equal(r.economics.problem,'stale_market');
 }
 assert.equal(quote({...e,market_resale_estimate:null,cashify_exchange:14000}).final,14000);
 assert.equal(quote({...e,market_resale_estimate:null}).valid,false);
});
test('unknown-age estimates never take an assessed Cashify uplift',()=>{
 const ref={kind:'assessed_quote',provider:'Cashify',model_key:'example',condition:c,device_age_months:null,amount_inr:27000,observed_at:today.toISOString(),confirmed:true};
 const r=quote(e,{},c,{sessionQuote:ref});assert.equal(r.final,24000);assert.equal(r.cashify.status,'estimate_only');assert.equal(r.cashify.uplift,0);assert.ok(api.cashifyPolicyMessage(r.cashify).includes('Quick estimate'));
});
test('condition, cost and fault deductions still apply exactly once',()=>{
 assert.equal(quote(e,{sellingCosts:500},{...c,grade:'B',kit:{box:false,bill:true,charger:true}}).final,18100);
 for(const battery_band of [0,1,2,3]){
  const plain=quote(e,{}, {...c,battery_band}),fault=quote(e,{}, {...c,battery_band,damages:['battery']});
  assert.ok(fault.final<=plain.final);assert.ok(fault.final>=0);
 }
});
test('saved catalogue models open an estimate; a model without evidence explicitly needs inputs',()=>{
 for(const [key,entry] of Object.entries(db))if(key!=='_meta'){
  const r=quote(entry);
  if(entry.price_reference_pending){
   const verifiedLaunch=entry.launch_date_verified===true && entry.net_new_price_basis==='official_launch_period_history_only' && entry.launch_sources?.length>0;
   assert.ok(entry.quote_safety?.requires_counter_review || key==='vivo_t2_5g_6_128' || verifiedLaunch,'Unexpected pending model '+key);assert.equal(r.valid,false);assert.equal(r.cashify.status,'needs_inputs');
   assert.match(r.q.debug.problem,/Saved estimate unavailable|Price review required/);catalogueChecks++;continue;
  }
  assert.ok(r.valid,key);assert.ok(Number.isFinite(r.final)&&r.final>=0&&r.final%100===0,key);
  assert.ok(r.estimateOnly,key);assert.equal(r.q.debug.months,null,key);catalogueChecks++;
 }
});
assert.doesNotMatch(html,/<input id="(?:new-price-confirm|resale-confirm)"/);
assert.match(html,/Refine quote/);assert.match(html,/ESTIMATED VALUE/);
console.log(JSON.stringify({passed:true,checks,catalogueChecks}));
