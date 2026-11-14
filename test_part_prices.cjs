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
console.log(JSON.stringify({passed:true,checks,priced:priced.length}));
