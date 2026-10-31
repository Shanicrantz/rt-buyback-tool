const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(process.argv[2] || 'index.html','utf8');
const DB=JSON.parse(html.match(/^const DB = (\{[^\r\n]*\});$/m)[1]);
const ctx=vm.createContext({DB});
const start=html.indexOf('const STORAGE_TOKENS'),end=html.indexOf('function openModel',start);
vm.runInContext(html.slice(start,end)+'\nglobalThis.variants=variantsOf;globalThis.family=familyOf;',ctx);
assert.deepEqual(Array.from(ctx.variants('vivo_x200_fe_12_256')).sort(),['vivo_x200_fe_12_256','vivo_x200_fe_16_512']);
assert.equal(ctx.family('iphone_12_128'),'iphone_12');
assert.equal(ctx.family('iphone_13_128'),'iphone_13');
assert.notEqual(ctx.family('iphone_13_pro_128'),ctx.family('iphone_13_128'));
assert.notEqual(ctx.family('vivo_x200_fe_12_256'),ctx.family('vivo_x200_12_256'));
assert.deepEqual(Array.from(ctx.variants('vivo_t2_5g_6_128')).sort(),['vivo_t2_5g_6_128','vivo_t2_5g_8_128']);
assert.equal(DB.vivo_t2_5g_6_128.display_name,'Vivo T2 5G 6/128GB');
assert.equal(DB.vivo_t2_5g_8_256,undefined,'Official India T2 has no 256GB variant');
assert.notEqual(ctx.family('vivo_t2_5g_6_128'),ctx.family('vivo_t2x_5g_6_128'));
const searchContext=vm.createContext({DB,$search:{value:'vivo x200fe 512'},$results:{style:{},innerHTML:''},activeFilter:'all',_kbIndex:0,keyMatchesFilter:()=>true,quickA1:()=>35900,esc:s=>s,fmt:String});
const a=html.indexOf('function runSearch()'),b=html.indexOf('function showTopOfFilter()',a);
vm.runInContext(html.slice(a,b)+'\nrunSearch();',searchContext);
assert.match(searchContext.$results.innerHTML,/vivo_x200_fe_16_512/);
assert.doesNotMatch(searchContext.$results.innerHTML,/data-key="vivo_x200_fe_12_256"/);
assert.equal(DB.vivo_x60_pro_plus_12_256.display_name,'Vivo X60 Pro+ 12/256GB');
assert.notEqual(ctx.family('vivo_x60_pro_plus_12_256'),ctx.family('vivo_x60_pro_256'));
for(const query of ['vivo x60 pro plus','X60 Pro+','x60proplus','x60pro+ 256']) {
 searchContext.$search.value=query;
 vm.runInContext('runSearch();',searchContext);
 assert.match(searchContext.$results.innerHTML,/data-key="vivo_x60_pro_plus_12_256"/,query);
 assert.doesNotMatch(searchContext.$results.innerHTML,/data-key="vivo_x60_pro_256"/,query);
}
for(const query of ['vivo t2 5g 6/128','T2 6/128','vivot25g 6/128']) {
 searchContext.$search.value=query;
 vm.runInContext('runSearch();',searchContext);
 assert.match(searchContext.$results.innerHTML,/data-key="vivo_t2_5g_6_128"/,query);
 assert.doesNotMatch(searchContext.$results.innerHTML,/data-key="vivo_t2_5g_8_128"/,query);
 assert.doesNotMatch(searchContext.$results.innerHTML,/data-key="vivo_t2_5g_8_256"/,query);
}
console.log('PASS: T2 exact India RAM variants, X200 FE mixed-RAM variants, X60 Pro+ aliases, compact search, and model-family isolation.');
