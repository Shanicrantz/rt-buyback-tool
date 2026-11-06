'use strict';
// Regression: a correction bigger than the weekly 20% drop band must still leave a quote
// (Shane, 2026-11-06: Vivo X300 FE 12/256 showed no value because the resolver blocked it).
// Covers both causes: same-family RAM/storage ordering, and a large fall in fresh evidence.
// usage: node test_resolve_quote_safety.cjs [index.html]
const fs=require('fs'),os=require('os'),path=require('path'),assert=require('assert/strict'),{execFileSync}=require('child_process');
const html=fs.readFileSync(process.argv[2]||path.join(__dirname,'index.html'),'utf8');
const lineRe=/^const DB = (\{[^\r\n]*\});[ \t]*$/m;
const phone=(name,resale)=>({display_name:name,tier:'B',target_margin:.25,market_resale_estimate:resale,calibration_date:'2026-10-30'});
function resolve(baseline,candidate,scope){
  const work=fs.mkdtempSync(path.join(os.tmpdir(),'rt-resolver-'));
  try{
    for(const [side,db] of [['baseline',baseline],['candidate',candidate]]){
      fs.mkdirSync(path.join(work,side));
      fs.writeFileSync(path.join(work,side,'phone_db.json'),JSON.stringify(db));
      fs.writeFileSync(path.join(work,side,'index.html'),html.replace(lineRe,()=>'const DB = '+JSON.stringify(db)+';'));
    }
    fs.writeFileSync(path.join(work,'scope.json'),JSON.stringify({models:scope}));
    execFileSync('node',[path.join(__dirname,'_resolve_quote_safety.cjs'),work,'2026-10-31T06:00:00.000Z'],{stdio:'pipe'});
    return {r:JSON.parse(fs.readFileSync(path.join(work,'pricing-resolution.json'),'utf8')),db:JSON.parse(fs.readFileSync(path.join(work,'candidate','phone_db.json'),'utf8'))};
  }finally{fs.rmSync(work,{recursive:true,force:true});}
}
let checks=0;const ok=(v,msg)=>{assert.ok(v,msg);checks++;};
{ // 1. Ordering: the smaller variant must drop >20% to sit at or below its larger sibling.
  const db={_meta:{version:'test'},small:phone('Fixture 8/128GB',12500),large:phone('Fixture 8/256GB',9875)};
  const {r,db:out}=resolve(db,db,[{key:'small',family:'Fixture',category:'phone',storage:128,ram:8},{key:'large',family:'Fixture',category:'phone',storage:256,ram:8}]);
  const row=k=>r.rows.find(x=>x.key===k);
  ok(row('small').baseline_final>row('large').final/.8,'fixture must need a >20% correction');
  ok(row('small').valid,'ordering: small variant must still quote');
  ok(row('small').final<=row('large').final,'ordering: small variant must not out-quote the larger one');
  ok(r.manual_review_models.length===0,'ordering: nothing blocked');
  ok(r.drop_band_exceeded_models.includes('small'),'ordering: flagged for review');
  ok(out.small.quote_safety.requires_counter_review===undefined&&out.small.price_reference_pending===undefined,'ordering: no block fields');
  ok(out._meta.version==='test','resolver must not change the version unless asked');
}
{ // 2. Evidence: fresh resale falls 36%; the fall applies in full (no floor) and is not blocked.
  const before={_meta:{version:'test'},solo:phone('Solo 8/128GB',12500)},after={_meta:{version:'test'},solo:phone('Solo 8/128GB',8000)};
  const {r,db:out}=resolve(before,after,[{key:'solo',family:'Solo',category:'phone',storage:128,ram:8}]);
  const row=r.rows.find(x=>x.key==='solo');
  ok(row.valid,'evidence: still quotes');
  ok(row.final<row.baseline_final*.8,'evidence: fall applied in full, not floored at -20%');
  ok(r.manual_review_models.length===0&&r.drop_band_exceeded_models.includes('solo'),'evidence: flagged, not blocked');
  ok(out.solo.quote_safety.requires_counter_review===undefined&&out.solo.price_reference_pending===undefined,'evidence: no block fields');
}
console.log(JSON.stringify({passed:true,checks}));
