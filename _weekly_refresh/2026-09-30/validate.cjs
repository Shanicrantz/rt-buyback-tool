const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('assert'), crypto = require('crypto');
const root = path.resolve(__dirname, '../..');
const base = JSON.parse(fs.readFileSync(path.join(root, 'phone_db.backup-2026-09-30.json')));
const oldHtml = fs.readFileSync(path.join(root, 'index.backup-2026-09-30.html'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, 'candidate/index.html'), 'utf8');
const db = JSON.parse(fs.readFileSync(path.join(__dirname, 'candidate/phone_db.json')));
const decisions = JSON.parse(fs.readFileSync(path.join(__dirname, 'decisions.json')));
const baseline = JSON.parse(fs.readFileSync(path.join(__dirname, 'baseline_quotes.json')));
const accepted = new Set(decisions.refreshed.map(x => x.key));
const added = new Set(decisions.added.map(x => x.key));
const removed = new Set(decisions.removed.map(x => x.key));
const dbRE = /^\s*const DB = (\{[^\r\n]*\});[ \t]*$/gm;
const matches = [...html.matchAll(dbRE)];
assert.equal(matches.length, 1);
assert.equal(matches[0][1], JSON.stringify(db), 'Inline DB bytes must equal the compact database bytes');
assert.equal(html.replace(dbRE, 'DB'), oldHtml.replace(dbRE, 'DB'), 'No UI/engine changes in a data refresh');
for (const s of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) new vm.Script(s[1]);
const engine = html.slice(html.indexOf('const TIER_FACTOR'), html.indexOf('// ============ UI STATE'));
const ctx = vm.createContext({});
vm.runInContext(engine + ';globalThis.quote=e=>computeA1(e,new Date(2026,8,30))[0];globalThis.grade=(a,g,o)=>gradeQuote(a,g,o);', ctx);
const finalEngine = html.slice(html.indexOf('const FOLDABLE_OOW_RISK'), html.indexOf('// ============ RENDER QUOTE'));
vm.runInContext('let _kit={box:true,bill:true,charger:true},_grade="A1",_battBand=0,_damages={};const BATT_DED=[0,.05,.10,.20];function warrantyFactor(){return 0;};'+finalEngine+';globalThis.finalFor=(e,a,g,b,k)=>{_grade=g;_battBand=b;_kit=k;return computeFinal(e,{a1:a}).final;};', ctx);
const issues = {quote:[],grade:[],finalOffer:[],newCeiling:[],resaleCeiling:[],weekly:[],manual:[],unrelated:[],storage:[],size:[],resaleIdentity:[],buyback:[]};
const families={}, prices={}, ceilings=[], offers=[];
const ranks={'32':0,'64':1,'128':2,'256':3,'512':4,'1024':5,'1tb':5,'2048':6,'2tb':6};
for(const [key,e] of Object.entries(db)) {
  if(key==='_meta')continue;
  const a1=ctx.quote(e); prices[key]=a1;
  if(!Number.isFinite(a1)||a1<=0||a1%100)issues.quote.push(key);
  let prev=Infinity;
  for(const grade of ['A1','A2','B','C','D']) {
    const q=ctx.grade(a1,grade,{});
    if(!Number.isFinite(q)||q<0||q>prev)issues.grade.push(key);
    prev=q;
    const full=ctx.finalFor(e,a1,grade,0,{box:true,bill:true,charger:true});
    const poor=ctx.finalFor(e,a1,grade,3,{box:false,bill:false,charger:false});
    if(!Number.isFinite(full)||!Number.isFinite(poor)||poor<0||poor>full)issues.finalOffer.push(key);
  }
  const changed=accepted.has(key)||added.has(key);
  const tolerance=changed?0:100; // Historical records retain their old rounding; new changes obey exact caps.
  if(e.net_new_inr>0&&a1>e.net_new_inr*.85+tolerance)issues.newCeiling.push(key);
  const resale=e.market_resale_estimate||e.market_resale_observed;
  if(resale>0&&a1>resale*.92+tolerance)issues.resaleCeiling.push(key);
  if(changed&&e.resale_target_a1!==e.market_resale_estimate)issues.resaleIdentity.push(key);
  if(accepted.has(key)&&(a1<baseline[key]*.8||a1>baseline[key]*1.2))issues.weekly.push(key);
  if(base[key]) {
    for(const field of ['rt_buyback_a1_override','rt_buyback_a1_warranty','warranty_premium','net_new_inr'])
      if(e[field]!==base[key][field])issues.manual.push([key,field]);
    if(!accepted.has(key)&&JSON.stringify(e)!==JSON.stringify(base[key]))issues.unrelated.push(key);
    if(!accepted.has(key)&&a1!==baseline[key])issues.unrelated.push(key+' quote');
  } else if(!added.has(key))issues.unrelated.push(key);
  if(e.buyback_market&&resale&&e.buyback_market>=resale)issues.buyback.push(key);
  if(changed&&e.buyback_market>a1)offers.push({key,name:e.display_name,rt_a1:a1,market:e.buyback_market});
  const m=key.match(/^(.*?)_(\d+|1tb|2tb)(_[a-z]+)?$/);
  if(m&&ranks[m[2]]!==undefined)(families[m[1]+(m[3]||'')]??=[]).push([ranks[m[2]],key,a1]);
}
for(const key of Object.keys(base))if(key!=='_meta'&&!db[key]&&!removed.has(key))issues.unrelated.push(key+' removed');
for(const rows of Object.values(families)) {
  rows.sort((a,b)=>a[0]-b[0]);
  for(let i=1;i<rows.length;i++)if(rows[i][2]<rows[i-1][2]-100)issues.storage.push([rows[i-1][1],rows[i][1]]);
}
for(const key of Object.keys(prices))if(key.startsWith('ipad_')&&key.includes('_11_')) {
  const big=key.replace('_11_','_13_');
  if(prices[big]&&prices[big]<prices[key]-100)issues.size.push([key,big]);
}
// Competitor reference evidence remains useful even when the proposed RT move
// was held; do not hide those likely lost-deal flags from the report.
for(const part of ['pricing_a','pricing_b']) {
  const review=JSON.parse(fs.readFileSync(path.join(__dirname,part+'.json')));
  for(const r of review.models) {
    const e=db[r.key]; if(!e)continue;
    const ceiling=r.buyback_ceiling||r.buyback_market;
    if(typeof ceiling==='number'&&ceiling>prices[r.key])ceilings.push({key:r.key,name:e.display_name,rt_a1:prices[r.key],ceiling,gap:ceiling-prices[r.key],price_held:!accepted.has(r.key)});
  }
}
const counts=Object.fromEntries(Object.entries(issues).map(([k,v])=>[k,v.length]));
const hashes=Object.fromEntries(['index.html','phone_db.json'].map(name=>[name,crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'candidate',name))).digest('hex')]));
const result={date:'2026-09-30',version:db._meta.version,entries:Object.keys(prices).length,paired_db_equal:true,non_db_html_unchanged:true,javascript_syntax:true,counts,issues,hashes,competitor_offers:offers,competitor_headline_alerts:ceilings.sort((a,b)=>b.gap-a.gap),passed:Object.values(counts).every(n=>n===0)};
fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({...result,issues:undefined,competitor_headline_alerts:undefined,hashes:undefined},null,2));
if(!result.passed)process.exit(1);
