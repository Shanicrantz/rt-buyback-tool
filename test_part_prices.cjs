'use strict';
// Official brand spare-part prices (v6.37): partCost uses part_prices when saved, else the tier-percentage estimate.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const ctx=vm.createContext({Date,URL,Intl});
vm.runInContext(html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'))+'\nglobalThis.api={partCost,officialPartPrice,DAMAGE_PARTS};',ctx);
const {partCost,officialPartPrice,DAMAGE_PARTS}=ctx.api;
const db=JSON.parse(html.match(/^const DB = (\{[^\n]+\});$/m)[1]);
let checks=0;const test=(n,f)=>{try{f();checks++}catch(e){e.message=n+': '+e.message;throw e}};
test('official price wins, rounded UP to Rs100',()=>{
 const e={tier:'A',part_prices:{display:{amount_inr:13294,brand:'OnePlus'}}};
 assert.equal(partCost(e,'display',50000),13300);
 assert.equal(partCost(e,'battery',50000),Math.round(50000*DAMAGE_PARTS.battery.pct.A/100)*100);
});
test('missing, zero or invalid official price falls back to the tier estimate',()=>{
 for(const bad of [undefined,{},{amount_inr:0},{amount_inr:-5},{amount_inr:'abc'}]){
  const e={tier:'B',part_prices:bad===undefined?undefined:{display:bad}};
  assert.equal(partCost(e,'display',20000),Math.round(20000*DAMAGE_PARTS.display.pct.B/100)*100);
  assert.equal(officialPartPrice(e,'display'),null);
 }
});
test('unknown damage key still costs nothing',()=>assert.equal(partCost({tier:'A',part_prices:{x:{amount_inr:500}}},'x',10000),0));
const priced=Object.entries(db).filter(([k,e])=>k!=='_meta'&&e.part_prices);
test('catalogue part prices carry brand, https source, date and a positive amount',()=>{
 assert.ok(priced.length>=500,'expected official part prices on the catalogue');
 for(const [k,e] of priced)for(const [dk,r] of Object.entries(e.part_prices)){
  assert.ok(DAMAGE_PARTS[dk],k+' unknown key '+dk);
  assert.ok(Number.isFinite(r.amount_inr)&&r.amount_inr>0,k+' '+dk);
  assert.ok(/^https:\/\//.test(r.source_url||''),k+' '+dk+' source');
  assert.ok(!Number.isNaN(Date.parse(r.observed_at)),k+' '+dk+' date');
  assert.ok(r.brand&&r.brand_model,k+' '+dk+' brand');
  assert.equal(r.amount_inr,(r.part_inr??r.amount_inr)+(r.labour_inr||0),k+' '+dk+' part+labour');
 }
});
test('international rows keep their derived pricing (no part prices attached)',()=>{
 for(const [k,e] of Object.entries(db))if(k!=='_meta'&&e.international)assert.equal(e.part_prices,undefined,k);
});
test('no part price above 1.5x the phone\'s own launch new price (unit / scraping sanity)',()=>{
 for(const [k,e] of priced){const np=e.current_new_price?.amount_inr||e.net_new_inr;if(!np)continue;
  for(const [dk,r] of Object.entries(e.part_prices))assert.ok(r.amount_inr<=np*1.5,k+' '+dk+' '+r.amount_inr+' vs new '+np);}
});
// v6.39: iPhone market rates (original-grade part + fitting) replace the Apple service estimate where cheaper.
const market=[];for(const [k,e] of priced)for(const [dk,r] of Object.entries(e.part_prices))if(r.market)market.push([k,dk,r]);
test('market part prices are iPhone-only, original grade, fitted, cheaper than Apple and sourced',()=>{
 assert.ok(market.length>=200,'expected iPhone market part prices');
 for(const [k,dk,r] of market){
  assert.equal(r.brand,'Market',k);assert.ok(/^iPhone /.test(r.brand_model),k+' '+r.brand_model);
  assert.equal(r.grade,'Original/OG',k);
  assert.equal(r.labour_inr,dk==='back_panel'?2000:500,k+' '+dk+' fitting');
  assert.ok(r.amount_inr%100===0,k+' '+dk+' rounded');
  if(r.apple_official_inr!==undefined)assert.ok(Number.isFinite(r.apple_official_inr)&&r.amount_inr<r.apple_official_inr,k+' '+dk+' not below Apple'); // v6.40 fills (no Apple price) carry none
  assert.ok(typeof r.sources==='string'&&/Rs\d/.test(r.sources),k+' '+dk+' sources');
 }
});
test('a model never mixes Apple and market prices for the same part across its storage variants',()=>{
 const seen={};for(const [k,e] of priced)for(const [dk,r] of Object.entries(e.part_prices)){if(r.brand!=='Apple'&&r.brand!=='Market')continue;
  const id=r.brand_model+'|'+dk;(seen[id]??=new Set()).add(r.brand+':'+r.amount_inr);}
 for(const [id,s] of Object.entries(seen))assert.equal(s.size,1,id+' '+[...s]);
});
test('policy text names the iPhone market rule',()=>assert.match(db._meta.part_price_policy,/market rate for an ORIGINAL-grade part/));
test('v6.40: every iPhone part a seller lists is priced; older iPhones and the extra parts are covered',()=>{
 const has=(k,dk)=>db[k]&&db[k].part_prices&&db[k].part_prices[dk]&&db[k].part_prices[dk].market;
 for(const [k,dk] of [['iphone_x_64','display'],['iphone_xr_64','battery'],['iphone_xs_max_256','rear_camera'],['iphone_11_pro_64','display'],['iphone_11_128','back_panel'],
   ['iphone_13_128','charging_port'],['iphone_15_pro_256','front_camera'],['iphone_16_pro_max_256','speaker'],['iphone_7_32','battery'],['iphone_se_2016_32','display']])assert.ok(has(k,dk),k+' '+dk);
 assert.ok(market.length>=700,'expected v6.39 + v6.40 market part prices');
});
console.log(JSON.stringify({passed:true,checks,priced:priced.length,market:market.length}));
