'use strict';
// Operational offer limits only. Never rewrite observed prices or historical anchors.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const work=path.resolve(process.argv[2]);
const read=n=>JSON.parse(fs.readFileSync(path.join(work,n),'utf8'));
const candidatePath=path.join(work,'candidate');
const originalDb=fs.readFileSync(path.join(candidatePath,'phone_db.json'),'utf8');
const originalHtml=fs.readFileSync(path.join(candidatePath,'index.html'),'utf8');
const db=JSON.parse(originalDb),baseline=read('baseline/phone_db.json');
const scope=read('scope.json').models;
const today=new Date(process.argv[3]||new Date().toISOString());
function engine(html){const context=vm.createContext({Date,URL,Intl});vm.runInContext(html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'))+'\n'+html.slice(html.indexOf('const FOLDABLE_OOW_RISK'),html.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={counterQuote,computeFinal};',context);return context.api;}
const api=engine(originalHtml),oldApi=engine(fs.readFileSync(path.join(work,'baseline/index.html'),'utf8'));
const condition={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
function quote(entry,valuationApi){if(!entry)return {valid:false,final:null};const q=valuationApi.counterQuote(entry,false,0,{},today);const r=valuationApi.computeFinal(entry,q,{modelKey:'review',condition,today});return {valid:r.valid,final:r.valid?r.final:null,raw:q.debug?.rawA1??q.a1};}
const current=e=>quote(e,api),before=e=>quote(e,oldApi);
const original=structuredClone(db),baselineQuotes={},beforeResolution={};
for(const [key,e]of Object.entries(db))if(key!=='_meta'){baselineQuotes[key]=before(baseline[key]);beforeResolution[key]=current(e);}
const pinned=[];
function limit(key,raw,reason,sibling){
 const e=db[key],old=e.quote_safety||{};
 e.quote_safety={...old,max_raw_a1:Math.min(old.max_raw_a1??Infinity,raw),reviewed_at:today.toISOString(),basis:'operational_offer_limit_not_market_price',reasons:[...new Set([...(old.reasons||[]),reason])],baseline_final_a1:baselineQuotes[key].final};
 if(sibling)e.quote_safety.ordering_siblings=[...new Set([...(old.ordering_siblings||[]),sibling])];
}
for(const [key,entry]of Object.entries(db))if(key!=='_meta'&&!entry.international){
 const b=baselineQuotes[key],a=current(entry);
 if(b.valid&&a.valid&&a.final>b.final*1.08+1e-8){limit(key,b.raw,'Uncorroborated increase withheld at previous raw offer');pinned.push(key);}
}
const groups=new Map();
for(const r of scope)if(r.storage!=null){const g=r.family.toLowerCase()+'|'+r.category;if(!groups.has(g))groups.set(g,[]);groups.get(g).push(r);}
const pairs=[];
for(const group of groups.values())for(const a of group)for(const b of group){
 if(a.key===b.key||a.storage>b.storage||(a.ram==null)!==(b.ram==null)||(a.ram!=null&&a.ram>b.ram)||(a.ram===b.ram&&a.storage===b.storage))continue;
 pairs.push([a.key,b.key]);
}
let changed=true,passes=0;
while(changed){changed=false;assert.ok(++passes<=scope.length,'Ordering failed to converge');
 for(const [small,big]of pairs){
  const a=current(db[small]),b=current(db[big]);if(!a.valid||!b.valid||a.final<=b.final)continue;
  let lo=0,hi=Math.ceil(a.raw);
  while(lo<hi){const mid=Math.ceil((lo+hi)/2),probe=structuredClone(db[small]);probe.quote_safety={...(probe.quote_safety||{}),max_raw_a1:mid};const r=current(probe);if(r.valid&&r.final<=b.final)lo=mid;else hi=mid-1;}
  if(lo<=0){db[small].quote_safety={...(db[small].quote_safety||{}),requires_counter_review:true,reviewed_at:today.toISOString()};}
  else limit(small,lo,'Conservative same-family RAM/storage offer ordering',big);
  const next=current(db[small]),base=baselineQuotes[small];
  if(!next.valid||base.valid&&next.final<base.final*.80-1e-8){
   db[small].quote_safety.requires_counter_review=true;
   db[small].quote_safety.reasons=[...new Set([...(db[small].quote_safety.reasons||[]),'Required correction exceeds weekly 20% drop limit'])];
   db[small].price_reference_pending='Price review required: confirm today’s exact new cash price, achievable A1 resale and the device’s actual age. Saved variant prices conflict; no automatic offer is available.';
  }
  changed=true;
 }
}
const rows=[],inversions=[],pendingPairs=[];
for(const [key,e]of Object.entries(db))if(key!=='_meta'){
 const b=baselineQuotes[key],a=current(e);
 if(a.valid&&b.valid){assert.ok(a.final<=b.final*1.08+1e-8,key+' rise');assert.ok(a.final>=b.final*.8-1e-8,key+' drop');}
 for(const field of Object.keys(original[key]))if(!['quote_safety','price_reference_pending'].includes(field))assert.deepEqual(e[field],original[key][field],key+' evidence/identity changed');
 if(e.international)assert.deepEqual(e,original[key]);
 rows.push({key,model:e.display_name,baseline_final:b.final,proposed_final:beforeResolution[key].final,final:a.final,valid:a.valid,safety:e.quote_safety||null});
}
for(const [small,big]of pairs){const a=current(db[small]),b=current(db[big]);if(!a.valid||!b.valid)pendingPairs.push({small,big,reason:'At least one variant requires verified inputs; no numeric ordering claim'});else if(a.final>b.final)inversions.push({small,big});}
assert.equal(inversions.length,0);
const summary={date:today.toISOString(),profile:condition,age:'unknown',pinned_increases:pinned,capped_models:rows.filter(r=>r.safety&&!r.safety.requires_counter_review).length,manual_review_models:rows.filter(r=>r.safety?.requires_counter_review).map(r=>r.key),numeric_inversions:inversions.length,pending_pairs:pendingPairs,passes,source_prices_unchanged:true,rows};
db._meta.quote_safety_review={reviewed_at:today.toISOString(),scope:'saved-reference quick estimates only; fully confirmed device-age quotes retain existing formula',capped_models:summary.capped_models,manual_review_models:summary.manual_review_models,source_prices_unchanged:true};
db._meta.version='6.29';db._meta.v6_29_changelog='30 October evidence refresh, released 31 October: retain original price observations; withhold uncorroborated rises, conservatively order saved offers, and require confirmed inputs where a safe correction exceeds the weekly drop limit. Four verified iPhone Duo variants remain price-pending. No model deleted.';
const compact=JSON.stringify(db),html=originalHtml.replace(/^const DB = (\{[^\r\n]*\});[ \t]*$/m,()=> 'const DB = '+compact+';');
assert.deepEqual(JSON.parse(html.match(/^const DB = (\{[^\n]+\});$/m)[1]),db);
assert.equal(fs.readFileSync(path.join(candidatePath,'phone_db.json'),'utf8'),originalDb,'Concurrent DB change');assert.equal(fs.readFileSync(path.join(candidatePath,'index.html'),'utf8'),originalHtml,'Concurrent HTML change');
fs.writeFileSync(path.join(candidatePath,'phone_db.json'),JSON.stringify(db,null,2)+'\n');fs.writeFileSync(path.join(candidatePath,'index.html'),html);fs.writeFileSync(path.join(work,'pricing-resolution.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({pinned:pinned.length,capped:summary.capped_models,manual_review:summary.manual_review_models,numeric_inversions:0,passes},null,2));
