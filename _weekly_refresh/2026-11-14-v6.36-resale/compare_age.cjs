'use strict';
// Actual-age quote (A1, full kit, out of warranty, saved new price, no entered price) before vs after.
const fs=require('fs'),vm=require('vm'),W=__dirname;
function engine(file){const h=fs.readFileSync(file,'utf8'),ctx=vm.createContext({Date,URL,Intl});vm.runInContext(h.slice(h.indexOf('const TIER_FACTOR'),h.indexOf('// ============ UI STATE'))+'\n'+h.slice(h.indexOf('const FOLDABLE_OOW_RISK'),h.indexOf('// ============ RENDER QUOTE'))+'\nglobalThis.api={counterQuote,computeFinal};',ctx);return ctx.api;}
const read=f=>JSON.parse(fs.readFileSync(W+'/'+f,'utf8'));
const old=read('baseline/phone_db.json'),db=read('candidate/phone_db.json'),moves=read('new-price-moves.json');
const A=engine(W+'/baseline/index.html'),B=engine(W+'/candidate/index.html'),today=new Date();
const c={grade:'A1',kit:{box:true,bill:true,charger:true},battery_band:0,under_warranty:false,warranty_band:null,damages:[]};
const mode=process.argv[2]||'launch';
function ageOf(e){if(mode!=='launch')return +mode;const [y,m]=(e.launch_date||'').split('-').map(Number);return Math.max(0,(today.getFullYear()-y)*12+today.getMonth()+1-m);}
function q(api,e){if(!e)return null;const r=api.computeFinal(e,api.counterQuote(e,false,0,{ageMode:'months',ageMonths:ageOf(e)},today),{modelKey:'cmp',condition:c,today});return r.valid?r.final:null;}
const rows=moves.map(x=>({...x,age:ageOf(db[x.key]),before_q:q(A,old[x.key]),after_q:q(B,db[x.key])})).filter(r=>r.before_q!==r.after_q);
rows.sort((a,b)=>Math.abs((b.after_q??0)-(b.before_q??0))-Math.abs((a.after_q??0)-(a.before_q??0)));
fs.writeFileSync(W+`/age-quote-changes-${mode}.json`,JSON.stringify(rows,null,1));
console.log(JSON.stringify({age:mode,changed:rows.length,up:rows.filter(r=>(r.after_q??0)>(r.before_q??0)).length,down:rows.filter(r=>(r.after_q??0)<(r.before_q??0)).length}));
for(const r of rows.slice(0,+(process.argv[3]||20)))console.log(`${r.model.slice(0,34).padEnd(34)} ${String(r.age).padStart(3)}mo new ${String(r.before??'-').padStart(7)} -> ${String(r.after??'-').padStart(7)} | quote ${String(r.before_q??'-').padStart(7)} -> ${String(r.after_q??'-').padStart(7)}`);
