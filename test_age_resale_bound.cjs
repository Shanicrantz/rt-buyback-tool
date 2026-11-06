'use strict';
// Regression (Shane, 2026-11-07): "price age aur warranty under warranty main difference hai".
// Without fresh or counter-confirmed resale, entering an actual age must never lift a quote above the
// no-age (saved-resale) quote for the same condition. Fresh/confirmed resale keeps the exact formula.
// usage: node test_age_resale_bound.cjs [index.html]
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(process.argv[2]||__dirname+'/index.html','utf8');
const ctx=vm.createContext({Date,URL,Intl});
vm.runInContext(html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'))+'\n'+html.slice(html.indexOf('const FOLDABLE_OOW_RISK'),html.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={counterQuote,computeFinal,WTY_LEFT};',ctx);
const api=ctx.api,db=JSON.parse(html.match(/^const DB = (\{[^\n]+\});$/m)[1]);
const base={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const conds=[base,...[0,1,2,3].map(b=>({...base,under_warranty:true,warranty_band:b})),{...base,grade:'B',kit:{box:false,bill:true,charger:true}}];
function quote(entry,input,c,today){const q=api.counterQuote(entry,c.under_warranty,c.under_warranty?api.WTY_LEFT[c.warranty_band].factor:0,input,today);return {q,...api.computeFinal(entry,q,{modelKey:'t',condition:c,today})};}
let checks=0,comparisons=0;const ok=(v,m)=>{assert.ok(v,m);checks++;};
{ // Synthetic: saved price 100,000, stale saved resale 30,000 at 22% markup -> gross 18.03%.
  const today=new Date('2026-11-07T08:00:00Z');
  const e={display_name:'Bound Phone 8/128GB',tier:'B',target_margin:.22,market_resale_estimate:30000,calibration_date:'2026-01-01',
    current_new_price:{kind:'retail_cash_price',variant_name:'Bound Phone 8/128GB',amount_inr:100000,selling_price_inr:100000,mandatory_fees_inr:0,observed_at:today.toISOString(),source_url:'https://example.com/p',available:true,market:'India',condition:'new',requires_exchange:false,requires_bank_offer:false}};
  const noAge=quote(e,{},base,today),age6=quote(e,{ageMode:'months',ageMonths:6},base,today);
  ok(age6.q.debug.savedResaleBound===true,'stale resale: age quote is bounded');
  ok(age6.final===noAge.final,'stale resale: 6-month quote equals the no-age quote, not 75,000');
  ok(age6.q.debug.ageFormulaRawA1===75000,'age formula value is kept for display');
  const old=quote(e,{ageMode:'months',ageMonths:60},base,today);
  ok(old.final<noAge.final&&old.q.debug.savedResaleBound===undefined,'an old unit keeps the lower age-formula value');
  const confirmed={ageMode:'months',ageMonths:6,resalePrice:30000,resaleConfirmed:true,resaleConfirmedAt:today.toISOString()};
  const c=quote(e,confirmed,base,today);ok(c.q.debug.savedResaleBound===undefined&&c.q.a1===75000&&!c.economics.problem,'counter-confirmed resale keeps the exact formula');
  const capped=quote({...e,quote_safety:{max_raw_a1:20000}},{ageMode:'months',ageMonths:6},base,today);ok(capped.q.debug.rawA1===20000,'conservative cap applies to the age quote too');
  const bare={...e};delete bare.market_resale_estimate;ok(quote(bare,{ageMode:'months',ageMonths:6},base,today).q.a1===75000,'no resale reference at all: age formula unchanged');
}
{ // Live catalogue: saved prices, every age band and warranty band.
  const today=new Date(Date.parse((db._meta.last_scoped_market_refresh?.checked_at)||Date.now())+3600e3);
  for(const [key,e] of Object.entries(db)){
    if(key==='_meta'||!e.current_new_price)continue;
    for(const c of conds){
      const noAge=quote(e,{},c,today);if(!noAge.valid)continue;
      for(const months of [0,3,6,12,24,48]){
        const r=quote(e,{ageMode:'months',ageMonths:months},c,today);if(!r.valid)continue;
        if(!r.economics.problem)continue; // fresh resale: exact formula + market limit
        assert.ok(r.final<=noAge.final,`${key} ${months}mo ${JSON.stringify([c.grade,c.warranty_band])}: age ${r.final} > no-age ${noAge.final}`);comparisons++;
      }
    }
  }
  ok(comparisons>1000,'catalogue comparisons ran');
  const x=db.vivo_x300_fe_12_256;
  if(x?.current_new_price)ok(quote(x,{ageMode:'months',ageMonths:6},base,today).final===quote(x,{},base,today).final,'Vivo X300 FE 12/256: 6-month quote equals no-age quote');
}
console.log(JSON.stringify({passed:true,checks,comparisons}));
