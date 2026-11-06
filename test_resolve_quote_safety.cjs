'use strict';
// Regression: an ordering correction bigger than the weekly 20% drop band must still leave a quote
// (Shane, 2026-11-06: Vivo X300 FE 12/256 showed no value because the resolver blocked it).
// usage: node test_resolve_quote_safety.cjs [index.html]
const fs=require('fs'),os=require('os'),path=require('path'),assert=require('assert/strict'),{execFileSync}=require('child_process');
const html=fs.readFileSync(process.argv[2]||path.join(__dirname,'index.html'),'utf8');
const lineRe=/^const DB = (\{[^\r\n]*\});[ \t]*$/m;
const fixture={_meta:{version:'test'},
  small:{display_name:'Fixture 8/128GB',tier:'B',target_margin:.25,market_resale_estimate:12500,calibration_date:'2026-10-30'},
  large:{display_name:'Fixture 8/256GB',tier:'B',target_margin:.25,market_resale_estimate:9875,calibration_date:'2026-10-30'}};
const scope={models:[{key:'small',family:'Fixture',category:'phone',storage:128,ram:8},{key:'large',family:'Fixture',category:'phone',storage:256,ram:8}]};
const work=fs.mkdtempSync(path.join(os.tmpdir(),'rt-resolver-'));
try{
  for(const side of ['baseline','candidate']){
    fs.mkdirSync(path.join(work,side));
    fs.writeFileSync(path.join(work,side,'phone_db.json'),JSON.stringify(fixture));
    fs.writeFileSync(path.join(work,side,'index.html'),html.replace(lineRe,()=>'const DB = '+JSON.stringify(fixture)+';'));
  }
  fs.writeFileSync(path.join(work,'scope.json'),JSON.stringify(scope));
  execFileSync('node',[path.join(__dirname,'_resolve_quote_safety.cjs'),work,'2026-10-31T06:00:00.000Z'],{stdio:'pipe'});
  const r=JSON.parse(fs.readFileSync(path.join(work,'pricing-resolution.json'),'utf8'));
  const db=JSON.parse(fs.readFileSync(path.join(work,'candidate','phone_db.json'),'utf8'));
  const row=k=>r.rows.find(x=>x.key===k);
  assert.ok(row('small').baseline_final>row('large').final/.8,'fixture must need a >20% correction');
  assert.equal(row('small').valid,true,'small variant must still quote');
  assert.ok(row('small').final<=row('large').final,'small variant must not out-quote the larger one');
  assert.deepEqual(r.manual_review_models,[]);
  assert.deepEqual(r.drop_band_exceeded_models,['small']);
  assert.equal(db.small.quote_safety.requires_counter_review,undefined);
  assert.equal(db.small.price_reference_pending,undefined);
  assert.equal(db._meta.version,'test','resolver must not change the version unless asked');
  console.log(JSON.stringify({passed:true,checks:8,small:row('small').final,large:row('large').final}));
}finally{fs.rmSync(work,{recursive:true,force:true});}
