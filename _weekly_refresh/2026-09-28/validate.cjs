const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const stage = __dirname;
const base = JSON.parse(fs.readFileSync(path.join(stage,'backup/phone_db.json'),'utf8'));
const html = fs.readFileSync(path.join(stage,'candidate/index.html'),'utf8');
const db = JSON.parse(fs.readFileSync(path.join(stage,'candidate/phone_db.json'),'utf8'));
const oldHtml = fs.readFileSync(path.join(stage,'backup/index.html'),'utf8');
const dbRE = /^const DB = (\{[^\r\n]*\});[ \t]*$/gm;
const matches = [...html.matchAll(dbRE)];
assert.equal(matches.length,1); assert.deepStrictEqual(JSON.parse(matches[0][1]),db);
assert.equal(html.replace(dbRE,'DB'),oldHtml.replace(dbRE,'DB'),'Only the DB line may change');
for (const s of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) new vm.Script(s[1]);
const engine = html.slice(html.indexOf('const TIER_FACTOR'),html.indexOf('// ============ UI STATE'));
const context = vm.createContext({});
vm.runInContext(engine + ';globalThis.quote=e=>computeA1(e,new Date(2026,8,28));globalThis.grade=(a,g,opts)=>gradeQuote(a,g,opts);',context);
// Exercise the original final-offer function with complete and missing kit, battery and fold risk.
const finalEngine = html.slice(html.indexOf('const FOLDABLE_OOW_RISK'),html.indexOf('// ============ RENDER QUOTE'));
vm.runInContext('let _kit={box:true,bill:true,charger:true},_grade="A1",_battBand=0,_damages={};const BATT_DED=[0,.05,.10,.20];function warrantyFactor(){return 0;};'+finalEngine+';globalThis.finalFor=(e,a,g,b,k)=>{_grade=g;_battBand=b;_kit=k;return computeFinal(e,{a1:a}).final;};',context);
const issues={quotes:[],grades:[],finalOffers:[],newCeiling:[],resaleCeiling:[],tierFloors:[],buybackCoherence:[],storage:[],size:[],manual:[],unexpectedChanges:[]};
const families={}, ranks={'32':0,'64':1,'128':2,'256':3,'512':4,'1024':5,'1tb':5,'2048':6,'2tb':6};
const allowed=new Set(['oppo_find_x8_pro_16_512']);let changed=[];
const prices={};
for (const [key,e] of Object.entries(db)) {
  if(key==='_meta')continue;
  const [a1]=context.quote(e); prices[key]=a1;
  if(!Number.isFinite(a1)||a1<=0)issues.quotes.push(key);
  let prev=Infinity;
  for(const grade of ['A1','A2','B','C','D']){
    const q=context.grade(a1,grade,{});if(!Number.isFinite(q)||q<0||q>prev)issues.grades.push(key);prev=q;
    const good=context.finalFor(e,a1,grade,0,{box:true,bill:true,charger:true});
    const degraded=context.finalFor(e,a1,grade,3,{box:false,bill:false,charger:false});
    if(!Number.isFinite(good)||!Number.isFinite(degraded)||degraded<0||degraded>good)issues.finalOffers.push(key);
  }
  // Rs100 tolerance matches the existing persisted-anchor rounding convention; accepted change is exact.
  if(e.net_new_inr>0&&a1>e.net_new_inr*.85+100)issues.newCeiling.push(key);
  if(e.market_resale_observed>0&&a1>e.market_resale_observed*.92+100)issues.resaleCeiling.push(key);
  const margin=e.target_margin??db._meta.default_margins_by_tier[e.tier];
  if(['C','D'].includes(e.tier)&&margin<db._meta.default_margins_by_tier[e.tier])issues.tierFloors.push(key);
  if(e.buyback_market&&e.market_resale_observed&&e.buyback_market>=e.market_resale_observed)issues.buybackCoherence.push(key);
  for(const field of ['rt_buyback_a1_override','rt_buyback_a1_warranty','warranty_premium','net_new_inr']) if(e[field]!==base[key]?.[field])issues.manual.push([key,field]);
  if(JSON.stringify(e)!==JSON.stringify(base[key])){changed.push(key);if(!allowed.has(key))issues.unexpectedChanges.push(key);}
  const m=key.match(/^(.*?)_(\d+|1tb|2tb)(_[a-z]+)?$/);
  if(m&&ranks[m[2]]!==undefined)(families[m[1]+(m[3]||'')]??=[]).push([ranks[m[2]],key,a1]);
}
assert.deepStrictEqual(Object.keys(db).sort(),Object.keys(base).sort(),'No models added or removed');
for(const rows of Object.values(families)){
  rows.sort((a,b)=>a[0]-b[0]);for(let i=1;i<rows.length;i++)if(rows[i][2]<rows[i-1][2]-100)issues.storage.push([rows[i-1][1],rows[i][1]]);
}
for(const key of Object.keys(prices)){
  if(key.startsWith('ipad_')&&key.includes('_11_')){const big=key.replace('_11_','_13_');if(prices[big]&&prices[big]<prices[key]-100)issues.size.push([key,big]);}
}
assert.deepStrictEqual(changed,[...allowed]);
const counts=Object.fromEntries(Object.entries(issues).map(([k,v])=>[k,v.length]));
const result={checked_at:'2026-09-28',entries:Object.keys(prices).length,changed,paired_db_equal:true,non_db_html_unchanged:true,javascript_syntax:true,rounding_tolerance_inr:100,counts,issues,passed:Object.values(counts).every(v=>v===0)};
fs.writeFileSync(path.join(stage,'validation.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({...result,issues:undefined},null,2));
if(!result.passed)process.exit(1);
