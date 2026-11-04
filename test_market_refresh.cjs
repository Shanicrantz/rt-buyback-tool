'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const db=JSON.parse(fs.readFileSync(__dirname+'/phone_db.json','utf8'));
const ctx=vm.createContext({Date,URL,Intl});
vm.runInContext(html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'))+'\n'+html.slice(html.indexOf('const FOLDABLE_OOW_RISK'),html.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={currentNewPrice,currentResalePrice,counterQuote,fullQuote,computeFinal,resaleEconomics};',ctx);
const a=ctx.api,now=new Date('2026-10-04T23:00:00Z');
const condition={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const entry={display_name:'Example 256GB',tier:'S',target_margin:.25,net_new_inr:100000,market_resale_observed:90000,calibration_date:'2026-10-04',
 current_new_price:{kind:'retail_cash_price',variant_name:'Example 256GB',amount_inr:50000,available:true,market:'India',condition:'new',requires_exchange:false,requires_bank_offer:false,observed_at:'2026-10-04T12:00:00Z',source_url:'https://retailer.example/device-256'},
 current_resale_price:{kind:'local_resale_estimate',variant_name:'Example 256GB',amount_inr:60000,market:'India',grade:'A1',method:'10% below exact refurb retail; sold price unverified',observed_at:'2026-10-04T12:00:00Z',source_url:'https://retailer.example/used-256'}};
function q(e=entry,input={},extra={}){const quote=a.counterQuote(e,false,0,input,now);return {quote,...a.computeFinal(e,quote,{modelKey:'test',today:now,condition,...extra})};}
let checks=0;function test(name,fn){try{fn();checks++;}catch(e){e.message=name+': '+e.message;throw e;}}
test('fresh new price limits resale BEFORE margin, including optional blank-age path',()=>{
 const r=q();assert.equal(r.economics.resale,45000);assert.equal(r.final,36000);assert.ok(r.economics.newPriceCapped);assert.equal(r.quote.debug.months,null);assert.ok(r.estimateOnly);
 assert.equal(q(entry,{ageMonths:0}).final,36000);assert.equal(q(entry,{ageMonths:0,sellingCosts:500}).final,35500);
});
test('new price drop immediately lowers both detailed and quick offers',()=>{
 const cheap={...entry,current_new_price:{...entry.current_new_price,amount_inr:30000}};
 assert.equal(q(cheap).final,21600);assert.equal(q(cheap,{ageMonths:0}).final,21600);
});
test('current researched resale takes priority over every old anchor',()=>{
 const low={...entry,current_resale_price:{...entry.current_resale_price,amount_inr:20000}};
 assert.equal(q(low).final,16000);assert.equal(q(low,{ageMonths:0}).final,16000);
});
test('historical new price does not silently cap or depreciate fresh resale',()=>{
 const e={...entry,current_new_price:null,net_new_inr:1000};
 assert.equal(q(e).quote.debug.price,null);assert.equal(q(e,{ageMonths:36}).final,48000);
});
test('global calibration does not freshen stale or wrong-variant structured observations',()=>{
 for(const patch of [{observed_at:'2026-08-01T00:00:00Z'},{variant_name:'Example 512GB'},{market:'International'},{kind:'refurb_retail_asking'},{source_url:'http://unsafe.example'},{observed_at:'2026-10-05T00:00:00Z'}]){
  const e={...entry,current_resale_price:{...entry.current_resale_price,...patch}};
  assert.equal(a.currentResalePrice(e,now),null);assert.equal(a.resaleEconomics(e,now).problem,'stale_market');
 }
});
test('conditional offers, used prices and incorrect regions cannot become new cash prices',()=>{
 for(const patch of [{requires_exchange:true},{requires_bank_offer:true},{condition:'refurbished'},{available:false},{market:'International'},{variant_name:'Example 512GB'},{observed_at:'2026-09-01T00:00:00Z'}])assert.equal(a.currentNewPrice({...entry,current_new_price:{...entry.current_new_price,...patch}},now),null);
});
test('pending refresh cannot re-label old calibration as fresh resale',()=>{
 const e={...entry,current_resale_price:null,market_refresh:{resale_status:'unverified'}};
 assert.equal(a.resaleEconomics(e,now).problem,'missing_market');
 assert.ok(q(e).estimateOnly);
 assert.equal(a.resaleEconomics(e,now,{resalePrice:30000,resaleDate:now.toISOString()}).resale,30000);
});
test('unavailable listing preserves last known estimate without fresh evidence',()=>{
 const e={...entry,current_new_price:null,current_resale_price:null,last_known_resale_price:entry.current_resale_price,market_refresh:{resale_status:'unverified'}};
 assert.equal(q(e).final,48000);assert.ok(q(e).estimateOnly);
 assert.equal(a.currentResalePrice(e,now),null);assert.equal(a.resaleEconomics(e,now).problem,'missing_market');
 assert.match(q(e).quote.debug.basis,/Saved \/ unverified/);
});
test('inferred resale never authorizes a final quote or assessed-competitor uplift',()=>{
 const assessed={kind:'assessed_quote',provider:'Cashify',model_key:'test',condition,device_age_months:36,amount_inr:22000,observed_at:now.toISOString(),confirmed:true};
 const r=q(entry,{ageMonths:36},{sessionQuote:assessed});assert.ok(r.estimateOnly);assert.equal(r.final,19000);assert.equal(r.cashify.status,'estimated_market');
 const confirmed=q(entry,{ageMonths:36,resalePrice:40000,resaleConfirmed:true,resaleConfirmedAt:now.toISOString()},{sessionQuote:assessed});assert.equal(confirmed.estimateOnly,false);assert.equal(confirmed.final,22500);
});
test('scoped market evidence is exact, fees included, partial coverage honest',()=>{
 const meta=db._meta.last_scoped_market_refresh;assert.equal(meta.new_prices_verified,meta.scope.filter(k=>db[k].market_refresh.new_price_status==='verified').length);assert.equal(meta.resale_estimated,meta.scope.filter(k=>db[k].market_refresh.resale_status==='estimated').length);assert.equal(meta.resale_observed,0);assert.equal(meta.status,'partial');
 // Catalogue observations have their own refresh timestamp; scenario fixtures
 // above deliberately retain their fixed clock for stale/future-price tests.
 const catalogueNow=new Date(Math.max(Date.parse(meta.checked_at),Date.parse(db._meta.last_targeted_market_refresh?.checked_at || meta.checked_at)));
 for(const key of meta.scope){const e=db[key],n=a.currentNewPrice(e,catalogueNow),r=a.currentResalePrice(e,catalogueNow);
  if(e.market_refresh.new_price_status==='verified'){assert.ok(n,key);assert.equal(n.amount_inr,n.selling_price_inr+n.mandatory_fees_inr);}
  else assert.equal(n,null,key);
  if(e.market_refresh.resale_status==='estimated'){assert.ok(r,key);assert.equal(r.kind,'local_resale_estimate');assert.ok(r.amount_inr<r.evidence[0].amount_inr);}
  const quote=a.counterQuote(e,false,0,{},catalogueNow);
  const result=a.computeFinal(e,quote,{modelKey:key,today:catalogueNow,condition});
  if(e.quote_safety?.requires_counter_review){assert.equal(quote.valid,false,key);assert.equal(result.valid,false,key);assert.match(quote.debug.problem,/Price review required/);continue;}
  if(e.price_reference_pending){
   const verifiedLaunch=e.launch_date_verified===true && e.net_new_price_basis==='official_launch_period_history_only' && e.launch_sources?.length>0;
   assert.ok(key==='vivo_t2_5g_6_128' || verifiedLaunch,'Unexpected pending model '+key);assert.equal(r,null);assert.equal(quote.valid,false);assert.equal(result.valid,false);
   assert.match(quote.debug.problem,/Saved estimate unavailable/);
   if(verifiedLaunch && n){
    const aged=a.counterQuote(e,false,0,{ageMonths:12},catalogueNow);
    const priced=a.computeFinal(e,aged,{modelKey:key,today:catalogueNow,condition});
    assert.equal(priced.valid,true,key);assert.equal(priced.estimateOnly,true,key);
    assert.equal(aged.debug.price,n.amount_inr,key);assert.equal(aged.debug.months,12,key);
    assert.ok(priced.final>0 && priced.final<n.amount_inr,key);
   }
   if(key==='vivo_t2_5g_6_128'){
   const entered=a.counterQuote(e,false,0,{newPrice:16000,newPriceConfirmed:true,priceConfirmedAt:catalogueNow.toISOString(),ageMonths:24},catalogueNow);
   const value=a.computeFinal(e,entered,{modelKey:key,today:catalogueNow,condition});assert.equal(value.valid,true);assert.equal(value.final,8000);assert.equal(value.estimateOnly,true);
   if(n){
    const ageOnly=a.counterQuote(e,false,0,{ageMonths:24},catalogueNow);
    const automatic=a.computeFinal(e,ageOnly,{modelKey:key,today:catalogueNow,condition});
    assert.equal(automatic.valid,true);assert.equal(automatic.final,Math.floor(n.amount_inr*.5/100)*100);
    assert.equal(automatic.estimateOnly,true);assert.equal(ageOnly.debug.price,n.amount_inr);
    assert.equal(ageOnly.debug.months,24);
   }
   }
  }else {assert.ok(result.valid&&Number.isFinite(result.final),key);assert.ok(result.estimateOnly,key);}
 }
});
test('standalone and inline DB agree; only scoped records changed',()=>{
 const embedded=[...html.matchAll(/^const DB = (\{[^\r\n]*\});[ \t]*$/gm)];assert.equal(embedded.length,1);assert.deepEqual(JSON.parse(embedded[0][1]),db);
 const before=JSON.parse(fs.readFileSync(__dirname+'/_test_fixtures/market_baseline_20261004.json','utf8'));
 const scoped=new Set(db._meta.last_scoped_market_refresh.scope);
 for(const key of Object.keys(before))if(key!=='_meta'&&!scoped.has(key)){
  if(key==='vivo_t2_5g_8_256')assert.equal(db[key],undefined,'Official India model has 128GB only');
  else assert.deepEqual(db[key],before[key],key);
 }
 for(const key of scoped){
  if(before[key]){assert.equal(db[key].net_new_inr,before[key].net_new_inr);assert.equal(db[key].calibration_date,before[key].calibration_date);}
  else if(key==='vivo_t2_5g_6_128'){assert.equal(db[key].catalogue_source_url,'https://www.vivo.com/in/products/param/t2-5g');assert.equal(db[key].display_name,'Vivo T2 5G 6/128GB');}
  else if(['iphone_duo_256','iphone_duo_512','iphone_duo_1tb','iphone_duo_2tb'].includes(key)){
   const expected={iphone_duo_256:['iPhone Duo 256GB',299900],iphone_duo_512:['iPhone Duo 512GB',324900],iphone_duo_1tb:['iPhone Duo 1TB',374900],iphone_duo_2tb:['iPhone Duo 2TB',449900]}[key];
   assert.equal(db[key].display_name,expected[0]);assert.equal(db[key].net_new_inr,expected[1]);assert.equal(db[key].launch_date,'2026-10-23');assert.equal(db[key].is_foldable,true);
   assert.equal(db[key].launch_sources[0].source_url,'https://www.apple.com/in/newsroom/2026/09/apple-unveils-iphone-duo/');assert.equal(typeof db[key].price_reference_pending,'string');assert.equal(db[key].resale_target_a1,undefined);
   // A later refresh may verify current stock; the launch list price stays historical.
   assert.equal(db[key].net_new_price_basis,'official_launch_period_history_only');
  }
  else if(/^vivo_(v80|s2_fe|x_fold6)_/.test(key)){
   const expected={vivo_v80_8_128:['Vivo V80 8/128GB',62999,'2026-10-13'],vivo_v80_8_256:['Vivo V80 8/256GB',69999,'2026-10-13'],vivo_v80_8_512:['Vivo V80 8/512GB',79999,'2026-10-13'],vivo_x_fold6_12_512:['Vivo X Fold6 12/512GB',219999,'2026-10-13'],vivo_s2_fe_6_128:['Vivo S2 FE 6/128GB',38999,'2026-10-20'],vivo_s2_fe_8_128:['Vivo S2 FE 8/128GB',42999,'2026-10-20']}[key];
   assert.ok(expected,key);assert.deepEqual([db[key].display_name,db[key].net_new_inr,db[key].launch_date],expected);
   assert.equal(db[key].launch_date_verified,true);assert.equal(db[key].net_new_price_basis,'official_launch_period_history_only');
   assert.ok(db[key].launch_sources[0].source_url.startsWith('https://vivonewsroom.in/press-release/'));
   assert.equal(Boolean(db[key].is_foldable),key==='vivo_x_fold6_12_512');
   assert.equal(db[key].resale_target_a1,undefined);assert.equal(typeof db[key].price_reference_pending,'string');
  }
  else {assert.equal(key,'vivo_x60_pro_plus_12_256');assert.equal(db[key].catalogue_source_url,'https://shop.vivo.com/in/product/10126');assert.equal(db[key].display_name,'Vivo X60 Pro+ 12/256GB');}
 }
});
console.log(JSON.stringify({passed:true,checks}));
