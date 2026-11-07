'use strict';
// Regression (Shane, 2026-11-07): age vs no-age quotes must agree, AND age must still move the price.
// Without fresh or counter-confirmed resale, an actual-age quote is bounded by the no-age saved quote
// scaled by depFraction(unit age)/depFraction(model age), at most +25%, and never above new price x age %.
// Fresh/confirmed resale keeps the exact formula.
// usage: node test_age_resale_bound.cjs [index.html]
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(process.argv[2]||__dirname+'/index.html','utf8');
const ctx=vm.createContext({Date,URL,Intl});
vm.runInContext(html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'))+'\n'+html.slice(html.indexOf('const FOLDABLE_OOW_RISK'),html.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={counterQuote,computeFinal,WTY_LEFT,depFraction,modelAgeMonths,AGE_BOUND_MAX_UPLIFT};',ctx);
const api=ctx.api,db=JSON.parse(html.match(/^const DB = (\{[^\n]+\});$/m)[1]);
const base={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const conds=[base,...[0,1,2,3].map(b=>({...base,under_warranty:true,warranty_band:b})),{...base,grade:'B',kit:{box:false,bill:true,charger:true}}];
function quote(entry,input,c,today){const q=api.counterQuote(entry,c.under_warranty,c.under_warranty?api.WTY_LEFT[c.warranty_band].factor:0,input,today);return {q,...api.computeFinal(entry,q,{modelKey:'t',condition:c,today})};}
const age=m=>({ageMode:'months',ageMonths:m});
let checks=0,comparisons=0;const ok=(v,m)=>{assert.ok(v,m);checks++;};
{ // Synthetic: launched 6 months ago, saved new 100,000, stale saved resale 30,000 at 22% markup.
  const today=new Date('2026-11-07T08:00:00Z');
  const e={display_name:'Bound Phone 8/128GB',tier:'B',target_margin:.22,market_resale_estimate:30000,calibration_date:'2026-01-01',launch_date:'2026-05-06',
    current_new_price:{kind:'retail_cash_price',variant_name:'Bound Phone 8/128GB',amount_inr:100000,selling_price_inr:100000,mandatory_fees_inr:0,observed_at:today.toISOString(),source_url:'https://example.com/p',available:true,market:'India',condition:'new',requires_exchange:false,requires_bank_offer:false}};
  ok(api.modelAgeMonths(e,today)===6,'model age from launch date');
  const noAge=quote(e,{},base,today).final;
  ok(quote(e,age(6),base,today).final===noAge,'unit as old as the model = no-age quote');
  const q1=quote(e,age(1),base,today).final,q12=quote(e,age(12),base,today).final;
  ok(q1>noAge&&q1<=Math.ceil(noAge*api.AGE_BOUND_MAX_UPLIFT/100)*100,'younger unit is worth more, at most +25%');
  ok(q12<noAge,'older unit is worth less');
  ok(quote(e,age(1),base,today).q.debug.savedResaleBound===true,'bound applied, age formula kept for display');
  const confirmed={...age(6),resalePrice:30000,resaleConfirmed:true,resaleConfirmedAt:today.toISOString()};
  const c=quote(e,confirmed,base,today);ok(c.q.debug.savedResaleBound===undefined&&c.q.a1===75000&&!c.economics.problem,'counter-confirmed resale keeps the exact formula');
  const capped=quote({...e,quote_safety:{max_raw_a1:20000}},age(6),base,today);ok(capped.q.a1===20000,'conservative cap applies at the model age');
  const bare={...e};delete bare.market_resale_estimate;ok(quote(bare,age(6),base,today).q.a1===75000,'no resale reference at all: age formula unchanged');
  const noLaunch={...e};delete noLaunch.launch_date;ok(quote(noLaunch,age(1),base,today).final===noAge,'no launch date: bound not scaled');
}
{ // Live catalogue: saved prices, every age band and condition.
  const today=new Date(Date.parse((db._meta.last_scoped_market_refresh?.checked_at)||Date.now())+3600e3);
  const ages=[0,1,3,6,12,18,24,36,48,60];
  for(const [key,e] of Object.entries(db)){
    if(key==='_meta'||!e.current_new_price)continue;
    const A=api.modelAgeMonths(e,today);
    for(const c of conds){
      const noAge=quote(e,{},c,today);if(!noAge.valid)continue;
      let prev=Infinity;
      for(const m of ages){
        const r=quote(e,age(m),c,today);if(!r.valid)continue;
        assert.ok(r.final<=prev+1e-9,`${key} ${m}mo: quote rose with age (${prev} -> ${r.final})`);prev=r.final;
        if(r.economics.problem){
          assert.ok(r.final<=Math.ceil(noAge.final*api.AGE_BOUND_MAX_UPLIFT/100)*100+100,`${key} ${m}mo: more than +25% over no-age`);
          if(A!=null&&m>=A)assert.ok(r.final<=noAge.final+100,`${key} ${m}mo: unit at/after model age above no-age (${r.final} > ${noAge.final})`);
        }
        comparisons++;
      }
    }
  }
  ok(comparisons>1000,'catalogue comparisons ran');
  const x=db.vivo_x300_fe_12_256,y=db.vivo_x300_fe_12_512;
  if(x?.current_new_price&&y?.current_new_price)for(const m of [0,1,3,6,12,24])ok(quote(x,age(m),base,today).final<=quote(y,age(m),base,today).final,`X300 FE 256 <= 512 at ${m} months`);
}
console.log(JSON.stringify({passed:true,checks,comparisons}));
