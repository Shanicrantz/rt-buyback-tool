'use strict';
// Exercise the shipped pure engine, not a duplicate implementation or a mocked price.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(process.argv[2] || __dirname+'/index.html','utf8');
function slice(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0 && b>a,'Engine marker absent');return html.slice(a,b);}
const context=vm.createContext({Date,URL,Intl});
vm.runInContext(slice('const TIER_FACTOR','// ============ UI STATE')+'\n'+slice('const FOLDABLE_OOW_RISK','// ============ RENDER QUOTE')+'\nglobalThis.api={computeA1,fullQuote,computeFinal,resolveValuation,currentNewPrice,depFraction,partCost,damagePartsFor,cashifyEconomicLimit,AGE_VALUE_POLICY,AGE_RANGES};',context);
const api=context.api,db=JSON.parse(html.match(/^const DB = (\{[^\r\n]*\});[ \t]*$/m)[1]);
const today=new Date('2026-10-02T13:30:00Z'),key='example_phone_8_128';
const condition={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const entry={display_name:'Example Phone 8/128GB',tier:'B',net_new_inr:999999,resale_target_a1:77700,target_margin:.298,rt_buyback_a1_override:50000,rt_buyback_a1_warranty:70000,warranty_premium:.8};
const input={newPrice:20000,newPriceConfirmed:true,priceConfirmedAt:today.toISOString(),ageMode:'months',ageMonths:12};
const clone=x=>JSON.parse(JSON.stringify(x));
const savedPrice={kind:'retail_cash_price',amount_inr:20000,available:true,observed_at:today.toISOString(),source_url:'https://shop.example.com/phone-8-128',variant_name:entry.display_name,model_key:key};
function quote(e=entry,i=input,c=condition,extra={}){const q=api.fullQuote(e,c.under_warranty,c.under_warranty?.9:0,i,today);return {...api.computeFinal(e,q,{modelKey:key,condition:c,today,...extra}),quote:q};}
function assessed(c=condition,age=12,amount=15001){return {kind:'assessed_quote',provider:'Cashify',model_key:key,amount_inr:amount,observed_at:today.toISOString(),source_url:'https://www.cashify.in/sell-old-mobile-phone/used-example-phone-8-gb-128-gb',condition:clone(c),device_age_months:age};}
const checks=[],failures=[];let modelChecks=0,conditionChecks=0;
function test(name,fn){try{fn();checks.push(name);}catch(error){failures.push({name,message:error.message});}}
function invalid(i,e=entry){const q=api.fullQuote(e,false,0,i,today);assert.equal(q.valid,false);assert.equal(q.a1,0);return q;}

test('policy anchors and linear interpolation use actual unit months',()=>{
 for(const [months,value] of [[0,85000],[3,80000],[6,75000],[12,65000],[18,58000],[24,50000],[36,38000],[48,28000],[60,20000],[84,10000],[120,5000],[240,3000]])
  assert.equal(api.computeA1(entry,today,{...input,newPrice:100000,ageMonths:months})[0],value,'age '+months);
 assert.ok(Math.abs(api.depFraction(1.5)-.825)<1e-10);
 assert.equal(api.computeA1(entry,today,{...input,newPrice:40000,ageMonths:1.5})[0],33000);
});
test('original purchase date controls age; launch date cannot change it',()=>{
 const i={...input,ageMode:'date',purchaseDate:'2025-10-02'},v=api.resolveValuation(entry,i,today);
 assert.ok(Math.abs(v.months-365/(365.25/12))<.01);
 assert.equal(api.computeA1({...entry,launch_date:'2000-01-01'},today,i)[0],api.computeA1({...entry,launch_date:'2026-09-01'},today,i)[0]);
 assert.equal(api.resolveValuation(entry,{...i,purchaseDate:'2026-10-02'},today).months,0);
});
test('approximate ranges use their upper endpoint and disclose it',()=>{
 api.AGE_RANGES.forEach(([label,upper],ageRange)=>{const v=api.resolveValuation(entry,{...input,ageMode:'range',ageRange},today);assert.equal(v.months,upper);assert.match(v.ageLabel,new RegExp(String(upper)));});
 for(const ageRange of [-1,12,NaN,1.5,'2',null])invalid({...input,ageMode:'range',ageRange});
});
test('blank, negative, over-age, nonfinite and malformed dates do not produce a quote',()=>{
 for(const ageMonths of [undefined,null,'',-1,241,NaN,Infinity,'12'])invalid({...input,ageMonths});
 for(const purchaseDate of ['',undefined,'2026-02-30','2026-10-03','2025-10-02T00:00:00Z','invalid','1990-01-01'])invalid({...input,ageMode:'date',purchaseDate});
 invalid({...input,ageMode:'unexpected'});
});
test('session new price must be a finite positive amount explicitly confirmed today IST',()=>{
 for(const newPrice of [undefined,null,'',0,-1,NaN,Infinity,'20000',2000001])invalid({...input,newPrice});
 for(const extra of [{newPriceConfirmed:false},{newPriceConfirmed:undefined},{priceConfirmedAt:'2026-10-01T18:29:59Z'},{priceConfirmedAt:'2026-10-02T13:30:01Z'},{priceConfirmedAt:'invalid'}])invalid({...input,...extra});
 assert.equal(api.resolveValuation(entry,{...input,priceConfirmedAt:'2026-10-01T19:00:00Z'},today).price,20000);
});
test('fresh saved price can substitute for counter input, historical net_new cannot',()=>{
 const i={ageMode:'months',ageMonths:12};
 invalid(i,entry);
 const e={...entry,current_new_price:savedPrice},q=api.fullQuote(e,false,0,i,today);
 assert.equal(q.valid,true);assert.equal(q.a1,13000);assert.equal(q.debug.priceSource,savedPrice.source_url);
 assert.equal(api.resolveValuation(e,{...input,newPrice:30000},today).price,30000);
 invalid({...input,newPrice:0},e); // An invalid entered override must not silently fall back.
});
test('saved new-price schema enforces date, stock, cash kind, URL and exact variant',()=>{
 const i={ageMode:'months',ageMonths:12};
 for(const patch of [{kind:'launch_mrp'},{amount_inr:0},{amount_inr:Infinity},{available:false},{available:undefined},{observed_at:'2026-09-25T13:29:59Z'},{observed_at:'2026-10-02T13:30:01Z'},{observed_at:'2026-02-30'},{source_url:'http://shop.example.com/phone'},{source_url:'https://user:pass@shop.example.com/phone'},{variant_name:'Example Phone 8/256GB'},{variant_name:undefined}])
  invalid(i,{...entry,current_new_price:{...savedPrice,...patch}});
 assert.equal(api.resolveValuation({...entry,current_new_price:{...savedPrice,observed_at:'2026-09-25T13:30:00Z'}},i,today).price,20000);
});
test('old override, resale, refurb, launch, tier premium and margin never control A1',()=>{
 const expected=quote().final;
 for(const patch of [{rt_buyback_a1_override:900000},{rt_buyback_a1_warranty:900000},{resale_target_a1:900000,target_margin:.01},{cashify_exchange:900000,rt_premium_over_cashify:1},{refurb_retail_anchor_excellent:900000,market_factor:1},{launch_date:'1999-01-01',net_new_inr:1},{tier:'S',warranty_premium:9}])assert.equal(quote({...entry,...patch}).final,expected);
});
test('every catalogue entry accepts the same explicit current-price/age calculation',()=>{
 for(const [model,e] of Object.entries(db))if(model!=='_meta'){
  for(const ageMonths of [0,6,12,24,60,120,240]){
   const value=api.computeA1(e,today,{...input,newPrice:100000,ageMonths})[0];
   const expected=Math.floor((100000*api.depFraction(ageMonths)*(e.international?.9:1)+1e-7)/100)*100;
   assert.equal(value,expected,model+' age '+ageMonths);modelChecks++;
  }
 }
 assert.equal(modelChecks,(Object.keys(db).length-1)*7);
});
test('increasing age or lowering current new price cannot increase the base quote',()=>{
 let last=Infinity;
 for(let age=0;age<=240;age+=.25){const n=quote(entry,{...input,ageMonths:age}).final;assert.ok(n<=last,'age '+age);last=n;}
 let previous=0;
 for(const newPrice of [1,99,101,999,5001,20000,53123,100000,2000000]){const n=quote(entry,{...input,newPrice}).final;assert.ok(n>=previous);previous=n;}
});
test('rounding cannot put a newborn offer above 85 percent of current new price',()=>{
 for(const newPrice of [101,199,999,1001,5001,53123]){
  const r=quote(entry,{...input,newPrice,ageMonths:0});assert.ok(r.final<=newPrice*.85,{newPrice,final:r.final});assert.equal(r.final%100,0);
 }
});
test('all grade, kit and battery combinations stay nonnegative and monotonic',()=>{
 for(const type of [{},{category:'laptop'},{category:'watch'},{category:'audio'},{is_foldable:true}]){
  const e={...entry,...type};
  for(const battery_band of [0,1,2,3])for(const mask of [0,1,2,3,4,5,6,7]){
   let previous=Infinity;
   for(const grade of ['A1','A2','B','C','D']){
    const c={...condition,grade,battery_band,kit:{box:!!(mask&1),bill:!!(mask&2),charger:!!(mask&4)}},r=quote(e,input,c);
    assert.ok(Number.isFinite(r.final)&&r.final>=0&&r.final<=previous);previous=r.final;conditionChecks++;
    if(battery_band>0)assert.ok(r.final<=quote(e,input,{...c,battery_band:battery_band-1}).final);
    for(const bit of [1,2,4])if(!(mask&bit))assert.ok(r.final<=quote(e,input,{...c,kit:{box:!!((mask|bit)&1),bill:!!((mask|bit)&2),charger:!!((mask|bit)&4)}}).final);
   }
  }
 }
});
test('damage estimates use resolved current price rather than historical price or anchor',()=>{
 const c={...condition,damages:['display']},r=quote(entry,input,c);
 assert.equal(r.dmgTotal,3600);assert.equal(r.final,9400);
 assert.equal(quote({...entry,net_new_inr:1,resale_target_a1:1},input,c).final,r.final);
 assert.equal(quote(entry,{...input,newPrice:40000},c).dmgTotal,7200);
});
test('battery fault never raises offer and uses only the larger of health loss or repair',()=>{
 for(const battery_band of [0,1,2,3]){
  const c={...condition,battery_band},plain=quote(entry,input,c),repair=quote(entry,input,{...c,damages:['battery']});
  const expected=Math.floor((13000-Math.max(13000*[0,.05,.10,.20][battery_band],1000))/100)*100;
  assert.ok(repair.final<=plain.final,'Adding battery fault at band '+battery_band+' raised '+plain.final+' to '+repair.final);
  assert.equal(repair.final,expected,'Deduct max health/repair once at band '+battery_band);
 }
});
test('all damages clamp at zero; adding any fault cannot increase offer',()=>{
 for(const category of ['phone','laptop','watch','audio']){
  const e={...entry,category},parts=Object.keys(api.damagePartsFor(e));
  for(const part of parts)for(const battery_band of [0,3]){
   const c={...condition,battery_band};assert.ok(quote(e,input,{...c,damages:[part]}).final<=quote(e,input,c).final,category+' '+part);
  }
  const r=quote(e,input,{...condition,grade:'D',battery_band:3,damages:parts});assert.equal(r.final,0);
 }
});
test('approved warranty premium changes final offer; legacy direct warranty amounts stay ignored',()=>{
 const c={...condition,under_warranty:true,warranty_band:0};assert.equal(quote(entry,input,c).final,14500);assert.equal(quote().final,13000);
 const fold={...entry,is_foldable:true};assert.ok(quote(fold,input,c).final>=quote(fold).final);
});
test('missing valuation cannot be rescued by legacy or same-age assessed Cashify quote',()=>{
 const e={...entry,market_resale_estimate:30000,calibration_date:'2026-10-02',cashify_quotes:[assessed()]};
 for(const i of [{}, {...input,ageMonths:undefined},{...input,newPriceConfirmed:false}]){
  const r=quote(e,i);assert.equal(r.quote.valid,false);assert.equal(r.final,0);assert.equal(r.cashify.status,'needs_inputs');assert.equal(r.cashify.meets,false);
 }
});
test('unknown or different Cashify age cannot override the formula, even if context omits valuation',()=>{
 for(const age of [undefined,null,'12',11,13]){
  const e={...entry,market_resale_estimate:30000,calibration_date:'2026-10-02',cashify_quotes:[assessed(condition,age)]};
  if(age===undefined)delete e.cashify_quotes[0].device_age_months;
  const r=quote(e);assert.equal(r.final,13000);assert.equal(r.cashify.status,'different_age');assert.equal(r.cashify.meets,false);
 }
});
test('same-age exact assessed policy adds 2 percent minimum100 after deductions and ignores old manual rate',()=>{
 const e={...entry,market_resale_estimate:30000,calibration_date:'2026-10-02',cashify_quotes:[assessed(condition,12,13001)]};
 const r=quote(e);assert.equal(r.final,13300);assert.equal(r.cashify.target,13300);assert.equal(r.cashify.status,'applied');assert.equal(r.cashify.cap,13800); // 18000 resale ceiling / 1.298 markup
 const low={...entry,target_margin:0,market_resale_estimate:3000,calibration_date:'2026-10-02',cashify_quotes:[assessed(condition,12,1000)]};
 const l=quote(low,{...input,newPrice:1500});assert.equal(l.final,1100);assert.equal(l.cashify.target,1100);
 const different=quote(e,input,{...condition,grade:'B'});assert.equal(different.cashify.status,'different_condition');assert.equal(different.final,10400);
});
test('Cashify cap uses current new price, exact condition and honest cap conflict',()=>{
 const e={...entry,market_resale_estimate:30000,calibration_date:'2026-10-02',cashify_quotes:[assessed(condition,12,19000)]};
 const r=quote(e);assert.equal(r.cashify.cap,13800);assert.equal(r.cashify.status,'cap_blocked');assert.equal(r.final,13000);assert.equal(r.cashify.meets,false);
 const stale=quote({...e,calibration_date:'2026-09-01'});assert.equal(stale.cashify.status,'stale_market');assert.equal(stale.final,13000);
 const intl=quote({...e,international:true});assert.equal(intl.cashify.status,'international');assert.ok(intl.final<13000);
});
test('Cashify economic battery cap is monotonic when a repair is selected',()=>{
 const e={...entry,market_resale_estimate:30000,calibration_date:'2026-10-02'},valuation=api.resolveValuation(e,input,today);
 const c={...condition,battery_band:3};
 const plain=api.cashifyEconomicLimit(e,c,today,valuation),repair=api.cashifyEconomicLimit(e,{...c,damages:['battery']},today,valuation);
 assert.ok(repair.limit<=plain.limit,'Battery fault raised cap from '+plain.limit+' to '+repair.limit);
 assert.equal(repair.limit,11000);
});

const result={passed:failures.length===0,checks:checks.length,total_groups:checks.length+failures.length,all_model_age_calculations:modelChecks,condition_calculations:conditionChecks,failures};
console.log(JSON.stringify(result,null,2));
if(failures.length)process.exit(1);
