'use strict';
// Focused executable checks of the browser's actual policy and final-offer math.
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const html = fs.readFileSync(process.argv[2] || __dirname + '/index.html','utf8');
const engine = html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'));
const finalEngine = html.slice(html.indexOf('const FOLDABLE_OOW_RISK'),html.indexOf('// ============ RENDER QUOTE'));
const context = vm.createContext({Date,URL,Intl});
vm.runInContext(engine + '\n' + finalEngine + '\nglobalThis.api={applyCashifyPolicy,computeFinal,cashifyConditionSignature,cashifyPolicyMessage};',context);
const api=context.api, today=new Date('2026-10-02T08:00:00Z');
const condition={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const entry={display_name:'Example Phone 8/128GB',tier:'B',market_resale_observed:20000,net_new_inr:30000,calibration_date:'2026-10-02'};
entry.current_new_price={kind:'retail_cash_price',variant_name:entry.display_name,amount_inr:30000,available:true,source_url:'https://shop.example/8-128',observed_at:today.toISOString()};
const ref={kind:'assessed_quote',provider:'Cashify',model_key:'example_8_128',amount_inr:5001,observed_at:today.toISOString(),condition,source_url:'https://www.cashify.in/sell-old-mobile-phone/used-example-phone-8-128'};
const clone=x=>JSON.parse(JSON.stringify(x));
function run(e=entry, existing=4000, r=ref, changes={}) {
 return api.applyCashifyPolicy({...e,cashify_quotes:[r]},existing,{modelKey:'example_8_128',condition,today,...changes});
}
let checks=0;
function test(name,fn){try{fn();checks++;}catch(err){err.message=name+': '+err.message;throw err;}}
test('exact 2% and ceil100 at minimum threshold',()=>{
 assert.equal(run().final,5200);
 assert.equal(run(entry,4000,{...ref,amount_inr:5000}).final,5100);
 assert.equal(run(entry,4000,{...ref,amount_inr:10010}).final,10300);
 assert.equal(run(entry,4000,{...ref,amount_inr:1100}).final,4000);
 assert.equal(run(entry,1000,{...ref,amount_inr:1100}).final,1200);
});
test('higher existing quote never reduced',()=>{
 const r=run(entry,15000);assert.equal(r.final,15000);assert.equal(r.status,'already_above');assert.equal(r.meets,true);
});
test('no legacy or headline evidence can uplift',()=>{
 for(const extra of [{cashify_exchange:10000},{buyback_market:10000},{market_buyback_ceiling:10000},{cashify_quotes:[{...ref,kind:'headline'}]}]){
  const r=api.applyCashifyPolicy({...entry,...extra},4000,{modelKey:'example_8_128',condition,today});
  assert.equal(r.final,4000);assert.equal(r.meets,false);
 }
});
test('invalid amount, provider, kind, URL rejected',()=>{
 for(const amount_inr of [0,-1,NaN,Infinity,'5001',null])assert.equal(run(entry,4000,{...ref,amount_inr}).final,4000);
 for(const field of [{provider:'Other'},{kind:'get_upto'},{source_url:'https://cashify.in.evil.test/sell-old-mobile-phone/a'},
  {source_url:'https://www.cashify.in/phone-price-in-india'},{source_url:'http://www.cashify.in/sell-old-mobile-phone/a'},
  {source_url:'https://user:secret@cashify.in/sell-old-mobile-phone/a'}])assert.equal(run(entry,4000,{...ref,...field}).matched,false);
});
test('current reference cannot cross model or any condition dimension',()=>{
 assert.equal(run(entry,4000,{...ref,model_key:'example_8_256'}).status,'different_model');
 const variants=[{grade:'B'},{kit:{...condition.kit,box:false}},{kit:{...condition.kit,bill:false}},
  {kit:{...condition.kit,charger:false}},{battery_band:1},{under_warranty:true,warranty_band:0},{damages:['display']}];
 for(const changed of variants)assert.equal(run(entry,4000,ref,{condition:{...condition,...changed}}).status,'different_condition');
 assert.equal(run(entry,4000,{...ref,condition:{grade:'A1'}}).status,'different_condition');
 const insured={...condition,under_warranty:true,warranty_band:0};
 assert.equal(run(entry,4000,{...ref,condition:insured},{condition:{...insured,warranty_band:1}}).status,'different_condition');
});
test('dates reject stale future invalid and expired quotes',()=>{
 for(const observed_at of ['2026-09-24T08:00:00Z','2026-10-03T08:00:00Z','invalid','2026-02-30','2026-10-02T09:00:00Z'])
  assert.equal(run(entry,4000,{...ref,observed_at}).matched,false);
 assert.equal(run(entry,4000,{...ref,observed_at:'2026-09-25T08:00:00Z'}).matched,true);
 assert.equal(run(entry,4000,{...ref,valid_until:'2026-10-01T23:59:59Z'}).status,'expired_quote');
});
test('no backsolved or stale market creates uplift',()=>{
 for(const patch of [{calibration_date:'2026-09-21'},{calibration_date:'2026-10-03'},{calibration_date:'2026-02-30'},
  {market_resale_observed:null,resale_target_a1:90000}]){
  const r=run({...entry,...patch});assert.equal(r.final,4000);assert.equal(r.meets,false);
 }
 assert.equal(run({...entry,calibration_date:'2026-09-22'}).final,5200);
 assert.equal(run({...entry,market_resale_observed:null,market_resale_estimate:20000}).final,5200);
});
test('cap conflict preserves current offer and discloses target and cap',()=>{
 const r=run({...entry,market_resale_observed:5500});
 assert.equal(r.status,'cap_blocked');assert.equal(r.target,5200);assert.equal(r.cap,4500);assert.equal(r.final,4000);assert.equal(r.meets,false);
 assert.match(api.cashifyPolicyMessage(r),/5,200/);assert.match(api.cashifyPolicyMessage(r),/4,500/);
 const n=run({...entry,current_new_price:{...entry.current_new_price,amount_inr:6000}});assert.equal(n.cap,4400);assert.equal(n.status,'cap_blocked');
});
test('existing offer above economic cap is preserved but requires review',()=>{
 const r=run(entry,19000);
 assert.equal(r.final,19000);assert.equal(r.cap,16300);assert.equal(r.target,5200);
 assert.equal(r.status,'existing_above_cap');assert.equal(r.meets,false);assert.equal(r.uplift,0);
 assert.match(api.cashifyPolicyMessage(r),/19,000/);assert.match(api.cashifyPolicyMessage(r),/16,300/);
});
test('manual and international policies preserved',()=>{
 for(const patch of [{rt_buyback_a1_override:4000},{international:true}])assert.equal(run({...entry,...patch}).final,4000);
 const c={...condition,under_warranty:true,warranty_band:0};
 assert.equal(run({...entry,rt_buyback_a1_warranty:8000},4000,{...ref,condition:c},{condition:c}).status,'manual_rate');
});
test('session quote must be explicitly confirmed for today IST',()=>{
 const opts={modelKey:'example_8_128',condition,today,sessionQuote:{...ref,source_url:undefined,confirmed:true}};
 assert.equal(api.applyCashifyPolicy(entry,4000,opts).final,5200);
 assert.equal(api.applyCashifyPolicy(entry,4000,{...opts,sessionQuote:{...opts.sessionQuote,confirmed:false}}).final,4000);
 assert.equal(api.applyCashifyPolicy(entry,4000,{...opts,sessionQuote:{...opts.sessionQuote,observed_at:'2026-10-01T17:00:00Z'}}).status,'stale_quote');
 assert.equal(api.applyCashifyPolicy(entry,4000,{...opts,sessionQuote:{...opts.sessionQuote,observed_at:'2026-10-01T19:00:00Z'}}).final,5200);
});
test('newest matching saved quote used; malformed records do not mask valid evidence',()=>{
 const r=api.applyCashifyPolicy({...entry,cashify_quotes:[null,{...ref,observed_at:'2026-10-01T08:00:00Z',amount_inr:10000},ref]},4000,{modelKey:'example_8_128',condition,today});
 assert.equal(r.cashify,5001);assert.equal(r.final,5200);
});
test('final-offer deductions happen before the premium; condition cap rounds down',()=>{
 const c={grade:'B',kit:{box:false,bill:true,charger:true},battery_band:1,under_warranty:false,warranty_band:null,damages:[]};
 const r=api.computeFinal({...entry,cashify_quotes:[{...ref,amount_inr:10000,condition:c}]},{a1:10000},{modelKey:'example_8_128',condition:c,today});
 assert.equal(r.originalFinal,7300);assert.equal(r.final,10200); // Grade/kit and final deductions now floor to INR100.
 assert.equal(r.cashify.cap,Math.floor((20000/1.22)*.8*.97*.95/100)*100);
});
test('foldable, damage, warranty and all grades remain nonnegative',()=>{
 for(const grade of ['A1','A2','B','C','D'])for(const under_warranty of [false,true])for(const damages of [[],['display','battery']]){
  const c={...condition,grade,under_warranty,warranty_band:under_warranty?0:null,damages,battery_band:3,kit:{box:false,bill:false,charger:false}};
  const e={...entry,display_name:'Galaxy Z Fold',cashify_quotes:[{...ref,condition:c,amount_inr:1000}]};
  const r=api.computeFinal(e,{a1:6000},{modelKey:'example_8_128',condition:c,today});
  assert.ok(Number.isFinite(r.final)&&r.final>=0);assert.ok(r.cashify.cap>=0);assert.ok(r.final>=r.originalFinal);
  if(r.cashify.meets)assert.ok(r.final>=r.cashify.target);
 }
});
test('pure calls need no DOM or UI globals',()=>assert.equal(run().final,5200));
// Exercise the shipped UI state, valuation handlers and render logic against a minimal document.
function createCounterUI(savedQuotes=[], entryPatch={}) {
 const elements=new Map(), groups=new Map(), timers=new Map();
 let nextTimerId=0;
 const setTimeout=(callback,delay)=>{const id=++nextTimerId;timers.set(id,{callback,delay});return id;};
 const clearTimeout=id=>timers.delete(id);
 function el(id){
  if(!elements.has(id)){
   const classes=new Set();
   elements.set(id,{id,focus(){document.activeElement=this;},value:'',checked:false,textContent:'',innerHTML:'',style:{},dataset:{},
    classList:{add(x){classes.add(x);},remove(x){classes.delete(x);},contains(x){return classes.has(x);}},
    addEventListener(event,fn){this[event]=fn;}});
  }
  return elements.get(id);
 }
 let customerMode=false;
 const document={body:{classList:{contains(){return customerMode;}}},getElementById:el,querySelectorAll(selector){return groups.get(selector)||[];}};
 for(const [selector,dataset] of Object.entries({'[data-grade]':{grade:'B'},'[data-kit]':{kit:'box'},'[data-batt]':{batt:'1'},'[data-dmg]':{dmg:'display'},'[data-wtyband]':{wtyband:'1'}})){
  const button=el(selector);button.dataset=dataset;groups.set(selector,[button]);
 }
 class FixedDate extends Date {constructor(...args){super(...(args.length?args:['2026-10-02T08:00:00Z']));}static now(){return today.getTime();}}
 const ui=vm.createContext({Date:FixedDate,URL,Intl,document,setTimeout,clearTimeout});
 const uiEntry={...entry,current_new_price:null,resale_target_a1:4400,target_margin:.1,cashify_quotes:savedQuotes,...entryPatch};
 const database=`const DB=${JSON.stringify({example_8_128:uiEntry,example_8_256:{...uiEntry,display_name:'Example Phone 8/256GB'}})};`;
 const state=html.slice(html.indexOf('// ============ UI STATE'),html.indexOf('// ============ HEADER / STATS'));
 const open=html.slice(html.indexOf('function openModel(key)'),html.indexOf('// ============ FINAL OFFER MATH'));
 const render=html.slice(html.indexOf('function renderQuote()'),html.indexOf('// ============ CUSTOMER MODE'));
 const quick=html.slice(html.indexOf('function quickA1('),html.indexOf('function runSearch()'));
 const share=html.slice(html.indexOf('function quoteText()'),html.indexOf('function saveRecent()'));
 vm.runInContext(engine+'\n'+database+'\n'+state+'\n'+finalEngine+'\n'+open+'\n'+render+'\n'+quick+'\n'+share+
  '\nfunction variantsOf(){return [];} function storageLabel(){return "";} openModel("example_8_128");',ui);
 const app={ui,el,groups,timers,mode(value){customerMode=value;},eval(code){return vm.runInContext(code,ui);},
  change(id,value){const field=el(id);if(typeof value==='boolean')field.checked=value;else field.value=String(value);field.onchange();this.flushTimers();},
  input(id,value){const field=el(id);field.value=String(value);document.activeElement=field;field.oninput();},
  flushTimers(){for(const [id,timer] of [...timers]){timers.delete(id);timer.callback();}},
  confirmValuation(price=10000,months=34){this.change('new-market-price',price);this.change('device-age-months',months);},
  estimate(){assert.equal(el('final-bar').classList.contains('show'),true);assert.equal(el('final-label').textContent,'ESTIMATED VALUE');assert.match(this.eval('quoteText()'),/ESTIMATED VALUE:/);assert.doesNotMatch(this.eval('quoteText()'),/FINAL OFFER:/);},
  pending(){assert.equal(el('final-bar').classList.contains('show'),false);assert.match(this.eval('quoteText()'),/^Quote pending:/);assert.doesNotMatch(this.eval('quoteText()'),/FINAL OFFER:/);}
 };
 return app;
}
const ageRef={...ref,device_age_months:34};
test('empty optional fields give an estimate; invalid explicit inputs still withhold the quote',()=>{
 const app=createCounterUI();app.estimate();
 assert.match(app.el('quote-output').innerHTML,/Old reference ₹30,000/);
 assert.match(app.el('quote-output').innerHTML,/Refine quote/);
 assert.equal(app.eval('_valuation.ageMonths'),null);assert.equal(app.eval('_valuation.newPrice'),'');
 assert.equal(app.eval('counterQuote(DB[_currentKey],false,0,_valuation).debug.months'),null);
 app.change('new-market-price',10000);app.estimate();
 app.change('device-age-months',34);assert.equal(app.el('final-value').textContent,'₹4,000');
 assert.match(app.eval('quoteText()'),/FINAL OFFER: ₹4,000/);
 app.change('device-age-months',-1);app.pending();
 app.change('device-age-months','');app.estimate();
 app.change('device-age-months',34);assert.equal(app.el('final-value').textContent,'₹4,000');
});
test('staff Apply/Reset and model/condition changes invalidate session evidence',()=>{
 const app=createCounterUI(),{el,groups}=app;app.confirmValuation();
 const applied=()=>{
  el('cashify-amount').value='5001';el('cashify-confirm').checked=true;el('cashify-apply').onclick();
  assert.equal(el('final-value').textContent,'₹5,200');
  assert.equal(app.eval('_cashifyQuote.device_age_months'),34);
 };
 app.mode(true);el('cashify-amount').value='5001';el('cashify-confirm').checked=true;el('cashify-apply').onclick();
 assert.equal(el('final-value').textContent,'₹4,000');assert.equal(app.eval('_cashifyQuote'),null);
 app.mode(false);applied();app.mode(true);el('cashify-clear').onclick();assert.equal(el('final-value').textContent,'₹5,200');
 app.mode(false);el('cashify-clear').onclick();assert.equal(el('final-value').textContent,'₹4,000');
 applied();const grade=groups.get('[data-grade]')[0];grade.click({currentTarget:grade});
 assert.equal(app.eval('_cashifyQuote'),null);assert.equal(el('final-value').textContent,'₹3,200');
 app.eval('_grade="A1";renderQuote();');assert.equal(el('final-value').textContent,'₹4,000');
 for(const selector of ['[data-kit]','[data-batt]','[data-dmg]']){
  applied();const button=groups.get(selector)[0];button.click({currentTarget:button});assert.equal(app.eval('_cashifyQuote'),null);
  app.eval('_kit={box:true,bill:true,charger:true};_battBand=0;_damages={};renderQuote();');
 }
 applied();el('wty-in').onclick();assert.equal(app.eval('_cashifyQuote'),null);
 app.eval('_underWarranty=false;renderQuote();');applied();app.change('device-age-months',35);
 assert.equal(app.eval('_cashifyQuote'),null);assert.equal(el('final-value').textContent,'₹3,900');
 app.change('device-age-months',34);applied();app.eval('openModel("example_8_256");');
 assert.equal(app.eval('_cashifyQuote'),null);assert.equal(app.eval('_valuation.newPrice'),'');assert.equal(app.eval('_valuation.ageMonths'),null);app.estimate();
 app.confirmValuation();assert.equal(el('final-value').textContent,'₹4,000');
 el('cashify-amount').value='5001';el('cashify-confirm').checked=false;el('cashify-apply').onclick();
 assert.equal(el('final-value').textContent,'₹4,000');assert.match(el('quote-output').innerHTML,/Actual same-condition assessed quote confirm/);
});
test('saved assessed quotes with unknown or different unit age cannot raise the formula offer',()=>{
 for(const saved of [ref,{...ageRef,device_age_months:33}]){
  const app=createCounterUI([saved]);app.confirmValuation();
  assert.equal(app.el('final-value').textContent,'₹4,000');
  assert.equal(app.eval('computeFinal(DB[_currentKey],fullQuote(DB[_currentKey],false,0,_valuation)).cashify.status'),'different_age');
  assert.match(app.el('quote-output').innerHTML,/actual age match/);
 }
});
test('saved exact-age quotes automatically match selected conditions after valuation inputs',()=>{
 const bRef={...ageRef,amount_inr:3501,condition:{...condition,grade:'B'}};
 const app=createCounterUI([ageRef,bRef]),{el}=app;app.estimate();app.confirmValuation();
 assert.equal(app.eval('_cashifyQuote'),null);assert.equal(el('final-value').textContent,'₹5,200');
 assert.equal(app.eval('quickA1(DB.example_8_128,"example_8_128")'),0); // Search cannot invent a unit age or use legacy new price.
 assert.match(el('quote-output').innerHTML,/data-grade="A1">\s*<span class="gname">A1<\/span>\s*<span class="price">₹5,200/);
 assert.match(el('quote-output').innerHTML,/data-grade="B">\s*<span class="gname">B<\/span>\s*<span class="price">₹3,700/);
 assert.match(el('quote-output').innerHTML,/<details id="cashify-override">/);
 assert.match(app.eval('quoteText()'),/FINAL OFFER: ₹5,200/);
 app.eval('_grade="B";renderQuote();');assert.equal(el('final-value').textContent,'₹3,700');
 assert.match(app.eval('quoteText()'),/FINAL OFFER: ₹3,700/);
 app.eval('_kit.box=false;renderQuote();');assert.equal(el('final-value').textContent,'₹3,100');
 app.eval('_kit.box=true;_grade="A1";renderQuote();');assert.equal(el('final-value').textContent,'₹5,200');
 app.change('device-age-months',35);assert.equal(el('final-value').textContent,'₹3,900');
 app.change('device-age-months',34);assert.equal(el('final-value').textContent,'₹5,200');
 app.eval('openModel("example_8_256");');app.estimate();app.confirmValuation();assert.equal(el('final-value').textContent,'₹4,000');
 app.eval('openModel("example_8_128");');app.estimate();app.confirmValuation();assert.equal(el('final-value').textContent,'₹5,200');
});
test('optional counter override resets to automatic matching exact-age saved evidence',()=>{
 const app=createCounterUI([ageRef]),{el}=app;app.confirmValuation();
 el('cashify-amount').value='6000';el('cashify-confirm').checked=true;el('cashify-apply').onclick();
 assert.equal(el('final-value').textContent,'₹6,200');assert.notEqual(app.eval('_cashifyQuote'),null);
 el('cashify-clear').onclick();assert.equal(app.eval('_cashifyQuote'),null);assert.equal(el('final-value').textContent,'₹5,200');
 app.eval('_battBand=1;renderQuote();');assert.equal(el('final-value').textContent,'₹3,800');
 app.eval('_battBand=0;renderQuote();');assert.equal(el('final-value').textContent,'₹5,200');
 el('cashify-amount').value='bad';el('cashify-confirm').checked=true;el('cashify-apply').onclick();
 assert.equal(el('final-value').textContent,'₹5,200');assert.match(el('quote-output').innerHTML,/Valid Cashify amount enter/);
});
test('typing a current price is sufficient confirmation and clears old Cashify evidence',()=>{
 const app=createCounterUI(),{el}=app;app.confirmValuation();
 el('cashify-amount').value='5001';el('cashify-confirm').checked=true;el('cashify-apply').onclick();
 app.change('new-market-price',20000);
 assert.equal(app.eval('_valuation.newPriceConfirmed'),true);assert.ok(app.eval('_valuation.priceConfirmedAt'));
 assert.equal(app.eval('_cashifyQuote'),null);assert.equal(el('final-value').textContent,'₹8,000');
 app.mode(true);app.change('new-market-price',50000);
 assert.equal(app.eval('_valuation.newPrice'),20000);assert.equal(el('final-value').textContent,'₹8,000');
});
test('typing clears stale Cashify evidence and debounces the updated quote',()=>{
 const app=createCounterUI(),{el}=app;app.confirmValuation();
 el('cashify-amount').value='5001';el('cashify-confirm').checked=true;el('cashify-apply').onclick();
 app.input('new-market-price',20000);
 assert.equal(app.eval('_valuation.newPrice'),20000);assert.equal(app.eval('_valuation.newPriceConfirmed'),true);
 assert.equal(app.eval('_cashifyQuote'),null);assert.equal(el('final-bar').classList.contains('show'),false);assert.equal(app.timers.size,1);
 app.input('new-market-price',15000);assert.equal(app.timers.size,1);
 assert.equal([...app.timers.values()][0].delay,250);app.flushTimers();
 assert.equal(el('final-value').textContent,'₹6,000');assert.equal(app.timers.size,0);assert.equal(app.eval('document.activeElement.id'),'new-market-price');
 app.input('device-age-months',35);app.flushTimers();assert.equal(el('final-value').textContent,'₹5,800');
 app.input('device-age-months',36);assert.equal(app.timers.size,1);
 app.eval('openModel("example_8_256");');assert.equal(app.timers.size,0);app.flushTimers();app.estimate();
 assert.equal(app.eval('_valuation.ageMonths'),null);assert.equal(app.eval('_valuation.newPrice'),'');
});
test('fresh price plus entered age gives a full quote; stale price stays an estimate',()=>{
 const current_new_price={kind:'retail_cash_price',variant_name:entry.display_name,amount_inr:10000,available:true,observed_at:today.toISOString(),source_url:'https://retailer.example/phone-8-128'};
 const app=createCounterUI([],{current_new_price});app.estimate();
 assert.equal(app.eval('quickA1(DB.example_8_128,"example_8_128")'),10000);
 app.change('device-age-months',34);assert.equal(app.el('final-value').textContent,'₹4,000');
 assert.equal(app.eval('_valuation.newPriceConfirmed'),false);
 assert.equal(app.eval('fullQuote(DB[_currentKey],false,0,_valuation).debug.priceSource'),current_new_price.source_url);
 for(const patch of [{observed_at:'2026-09-24T08:00:00Z'},{available:false}]){
  const invalid=createCounterUI([],{current_new_price:{...current_new_price,...patch}});invalid.change('device-age-months',34);invalid.estimate();
  assert.equal(invalid.eval('quickA1(DB.example_8_128,"example_8_128")'),0);
 }
});
test('counter resale and selling costs share one capped result across tiles and share text',()=>{
 const app=createCounterUI(),{el}=app;app.confirmValuation();
 app.change('resale-price',3000);assert.equal(el('final-value').textContent,'₹2,700');
 app.change('selling-costs',333);assert.equal(el('final-value').textContent,'₹2,300');
 assert.match(app.eval('quoteText()'),/FINAL OFFER: ₹2,300/);
 assert.match(el('quote-output').innerHTML,/data-grade="A1">\s*<span class="gname">A1<\/span>\s*<span class="price">₹2,300/);
 el('cashify-amount').value='5001';el('cashify-confirm').checked=true;el('cashify-apply').onclick();
 assert.equal(el('final-value').textContent,'₹2,300');assert.match(el('quote-output').innerHTML,/safe limit ₹2,300/);
 app.input('resale-price',4000);assert.equal(el('final-bar').classList.contains('show'),false);assert.equal(app.eval('_valuation.resaleConfirmed'),true);assert.equal(app.eval('_cashifyQuote'),null);
 app.flushTimers();assert.equal(el('final-value').textContent,'₹3,300');
 app.change('selling-costs',-1);app.pending();
 app.eval('openModel("example_8_256");');app.estimate();assert.equal(app.eval('_valuation.resalePrice'),undefined);assert.equal(app.eval('_valuation.sellingCosts'),undefined);
});
test('stale resale is disclosed in staff customer and shared quote outputs',()=>{
 const app=createCounterUI([],{calibration_date:'2026-08-01'});app.confirmValuation();
 assert.match(app.el('quote-output').innerHTML,/Resale Check Pending/);
 assert.match(app.eval('quoteText()'),/Estimate only — resale verification pending/);
 assert.match(app.el('final-detail').textContent,/resale check pending/);
});
test('optional panel stays collapsed until opened and resets for another device',()=>{
 const app=createCounterUI();app.estimate();
 assert.match(app.el('quote-output').innerHTML,/id="valuation-inputs" ><summary>Refine quote/);
 assert.doesNotMatch(app.el('quote-output').innerHTML,/<input id="(?:new-price-confirm|resale-confirm)"/);
 const panel=app.el('valuation-inputs');panel.open=true;panel.toggle();
 app.confirmValuation();assert.equal(app.eval('_refineOpen'),true);
 assert.match(app.el('quote-output').innerHTML,/id="valuation-inputs" open>/);
 app.change('new-market-price','');app.estimate();
 assert.equal(app.eval('_valuation.newPriceConfirmed'),false);assert.equal(app.eval('_valuation.priceConfirmedAt'),null);
 app.eval('openModel("example_8_256");');assert.equal(app.eval('_refineOpen'),false);app.estimate();
});
test('quick estimates cannot be raised by manually assessed Cashify quotes',()=>{
 const app=createCounterUI(),{el}=app;app.estimate();const initial=el('final-value').textContent;
 el('cashify-amount').value='99999';el('cashify-confirm').checked=true;el('cashify-apply').onclick();
 assert.equal(el('final-value').textContent,initial);assert.equal(app.eval('_cashifyQuote'),null);
 assert.match(el('quote-output').innerHTML,/optional current price aur actual age add/);
 app.estimate();
});
test('ordinary phone warranty toggle updates amount, band, comparison and shared quote',()=>{
 const app=createCounterUI(),{el}=app;app.confirmValuation();
 assert.equal(el('final-value').textContent,'₹4,000');
 el('wty-in').onclick();assert.equal(el('final-value').textContent,'₹4,400');
 assert.match(el('quote-output').innerHTML,/id="warranty-out-amount">₹4,000/);
 assert.match(el('quote-output').innerHTML,/id="warranty-in-amount">₹4,400/);
 assert.match(app.eval('quoteText()'),/Under warranty: 9–12mo left/);
 assert.match(app.eval('quoteText()'),/FINAL OFFER: ₹4,400/);
 app.eval('_wtyBand=3;renderQuote();');assert.equal(el('final-value').textContent,'₹4,000');
 assert.match(el('quote-output').innerHTML,/No extra payable amount/);
 el('wty-out').onclick();assert.equal(el('final-value').textContent,'₹4,000');
 app.eval('openModel("example_8_256");');assert.equal(app.eval('_underWarranty'),false);
});

// Compile all browser scripts, and inspect that sharing/printing use the same final engine result.
for(const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(match[1]);
assert.match(html,/function quoteText\(\)[\s\S]*?const fo = computeFinal\(entry, q\);[\s\S]*?fmt\(fo.final\)/);
assert.match(html,/"PURCHASE AMOUNT"\}: \$\{fmt\(fo.final\)\}/);
assert.match(html,/class="cond-box staff-only" id="cashify-panel"/);
console.log(JSON.stringify({passed:true,checks,javascript_syntax:true,shared_final_amount:true}));
