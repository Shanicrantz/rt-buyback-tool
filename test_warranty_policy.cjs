'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(process.argv[2]||__dirname+'/index.html','utf8');
function engine(text){const ctx=vm.createContext({Date,URL,Intl});vm.runInContext(text.slice(text.indexOf('const TIER_FACTOR'),text.indexOf('// ============ UI STATE'))+'\n'+text.slice(text.indexOf('const FOLDABLE_OOW_RISK'),text.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={counterQuote,fullQuote,computeFinal,conditionAmounts,resaleEconomics,WTY_LEFT};',ctx);return ctx.api;}
const api=engine(html),baseline=engine(fs.readFileSync(__dirname+'/_test_fixtures/warranty_engine_v620.js.txt','utf8'));
const today=new Date('2026-10-05T08:00:00Z');
const c={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const e={display_name:'Example Phone 8/128GB',tier:'B',target_margin:.25,market_resale_estimate:30000,calibration_date:'2026-10-05'};
const input={newPrice:50000,newPriceConfirmed:true,priceConfirmedAt:today.toISOString(),ageMonths:12};
function quote(entry=e,i=input,condition=c,engine=api){const q=engine.counterQuote(entry,condition.under_warranty,condition.under_warranty?api.WTY_LEFT[condition.warranty_band].factor:0,i,today);return engine.computeFinal(entry,q,{modelKey:'example',condition,today});}
const under=band=>({...c,under_warranty:true,warranty_band:band});
let checks=0,comparisons=0;const cases=[];
function test(name,fn){fn();checks++;cases.push(name);}
test('ordinary phones get the old 13 percent scaled premium without requiring age entry',()=>{
 const out=quote(e,{});assert.equal(out.final,24000);
 const expected=[26800,26000,25200,24400];
 for(let b=0;b<4;b++){const r=quote(e,{},under(b));assert.equal(r.final,expected[b]);assert.ok(r.final>out.final);assert.equal(r.economics.resale,30000);}
});
test('strict actual-age formula applies premium once before deductions',()=>{
 // No resale reference at all: the actual-age formula is the only basis and stays unbounded.
 const noMarket={...e,calibration_date:'2026-01-01'};delete noMarket.market_resale_estimate;
 assert.equal(quote(noMarket).final,32500);
 assert.equal(quote(noMarket,input,under(0)).final,36300);
 assert.equal(quote(noMarket,input,{...under(0),grade:'B',kit:{box:false,bill:true,charger:true}}).final,28100);
});
test('stale saved resale bounds the actual-age quote; warranty premium still applies once',()=>{
 // Shane 2026-11-07: an entered age must not lift the quote above the saved-resale quote.
 const stale={...e,calibration_date:'2026-01-01'};
 const r=quote(stale);assert.equal(r.final,24000);assert.equal(r.economics.problem,'stale_market');
 const noAge=quote(stale,{newPrice:50000,newPriceConfirmed:true,priceConfirmedAt:today.toISOString()});assert.equal(r.final,noAge.final);
 assert.equal(quote(stale,input,under(0)).final,26800);
 assert.equal(quote(stale,input,under(0)).final,quote(stale,{newPrice:50000,newPriceConfirmed:true,priceConfirmedAt:today.toISOString()},under(0)).final);
 const confirmed={...input,resalePrice:30000,resaleConfirmed:true,resaleConfirmedAt:today.toISOString()};
 const q=api.counterQuote(stale,false,0,confirmed,today);assert.equal(q.debug.savedResaleBound,undefined);assert.equal(q.a1,32500);
 assert.equal(quote(stale,confirmed).final,24000);
});
test('warranty uses only margin headroom above 8 percent; never invents resale',()=>{
 const narrow={...e,target_margin:.099};
 const r=quote(narrow,{},under(0));assert.equal(r.final,27600);assert.equal(r.economics.resale,30000);assert.equal(r.economics.margin,.08);
 assert.ok(r.final>=quote(narrow,{}).final);assert.ok(r.final<=30000*.92);
 const full=quote({...e,margin_basis:'gross',target_margin:.25},{},under(0));assert.equal(full.final,25100);
});
test('new price caps warranty even when resale is stale or missing',()=>{
 for(const ageMonths of [0,1,3]){
  const r=quote({...e,calibration_date:'2026-01-01'},{...input,newPrice:10000,ageMonths},under(0));
  assert.ok(r.final<=8500);assert.equal(r.newPriceLimit,8500);
 }
 // No resale reference, so only the new-price ceiling can bind (a saved resale would bound it lower).
 const noResale={...e,calibration_date:'2026-01-01'};delete noResale.market_resale_estimate;
 const newborn=quote(noResale,{...input,ageMonths:0},under(0));assert.equal(newborn.final,42500);assert.ok(newborn.marketCapped);
});
test('damage battery and costs are not waived or double-counted under warranty',()=>{
 const noMarket={...e,calibration_date:'2026-01-01'};
 const plain=quote(noMarket,input,under(0));
 const damaged=quote(noMarket,input,{...under(0),damages:['display']});assert.equal(plain.final-damaged.final,9000);
 assert.equal(quote(noMarket,{...input,sellingCosts:500},under(0)).final,plain.final-500);
 for(const battery_band of [0,1,2,3]){
  const condition={...under(0),battery_band};
  assert.ok(quote(noMarket,input,{...condition,damages:['battery']}).final<=quote(noMarket,input,condition).final);
 }
});
test('stale resale stays an estimate and still limits the warranty allowance',()=>{
 const stale={...e,target_margin:.099,market_resale_estimate:39500,calibration_date:'2026-01-01'};
 const r=quote(stale,{},under(0));assert.equal(r.final,36300);assert.equal(r.referenceLimit,36300);assert.ok(r.estimateOnly);assert.equal(r.economics.problem,'stale_market');
 assert.equal(r.cashify.status,'estimate_only');
});
test('legacy direct warranty amounts cannot bypass premium or current limits',()=>{
 const r=quote({...e,rt_buyback_a1_warranty:999999,warranty_premium:99},{},under(0));assert.equal(r.final,26800);
});
test('all catalogue out-of-warranty offers remain unchanged; warranty amounts are monotonic within limits',()=>{
 const db=JSON.parse(html.match(/^const DB = (\{[^\n]+\});$/m)[1]);
 for(const [key,entry] of Object.entries(db))if(key!=='_meta'){
  for(const i of [{},{...input,newPrice:100000,ageMonths:12}]){
   if(entry.quote_safety?.requires_counter_review){assert.equal(quote(entry,i).valid,false,key);for(const band of [3,2,1,0])assert.equal(quote(entry,i,under(band)).valid,false,key);continue;}
   const out=quote(entry,i),old=quote(entry,i,c,baseline);
   if(entry.quote_safety && !Object.keys(i).length)assert.ok(out.final<=old.final,key+' safety limit raised offer');
   // 2026-11-07: without fresh resale an actual-age quote is bounded by the saved-resale quote; it may only fall.
   else if(Object.keys(i).length){assert.ok(out.final<=old.final,key+' age quote raised');assert.ok(out.final<=quote(entry,{newPrice:i.newPrice,newPriceConfirmed:true,priceConfirmedAt:i.priceConfirmedAt}).final||!quote(entry,{newPrice:i.newPrice,newPriceConfirmed:true,priceConfirmedAt:i.priceConfirmedAt}).valid,key+' age quote above no-age quote');}
   else assert.equal(out.final,old.final,key+' out changed');
   if(entry.price_reference_pending && !Object.keys(i).length){
    const verifiedLaunch=entry.launch_date_verified===true && entry.net_new_price_basis==='official_launch_period_history_only' && entry.launch_sources?.length>0;
    assert.ok(key==='vivo_t2_5g_6_128' || verifiedLaunch,'Unexpected pending model '+key);assert.equal(out.valid,false);
    for(const band of [3,2,1,0])assert.equal(quote(entry,i,under(band)).valid,false,'Warranty cannot manufacture a missing base price');
    continue;
   }
   let previous=out.final;
   for(const band of [3,2,1,0]){
    const r=quote(entry,i,under(band));assert.ok(r.valid&&Number.isFinite(r.final)&&r.final>=previous,key+' warranty nonmonotonic');
    if(!r.economics.problem)assert.ok(r.final<=r.economics.limit&&r.economics.margin>=.08-1e-9,key+' margin');
    if(r.newPriceLimit!==null)assert.ok(r.final<=r.newPriceLimit,key+' new ceiling');
    previous=r.final;comparisons++;
   }
  }
 }
});
assert.match(html,/id="warranty-out-amount"/);assert.match(html,/id="warranty-in-amount"/);assert.match(html,/id="warranty-difference"/);
console.log(JSON.stringify({passed:true,checks,comparisons,cases}));
