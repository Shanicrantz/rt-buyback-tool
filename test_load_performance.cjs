'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const code=fs.readFileSync(__dirname+'/sw.js','utf8');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
assert.doesNotMatch(html, /https:\/\/fonts\.(?:googleapis|gstatic)\.com/);
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject};}
function harness(cacheWriteWait){
  const handlers={},store=new Map(),timers=new Map(),messages=[];let timer=0;
  const url='https://rt.test/',pending=deferred();
  const cacheFor=name=>{if(!store.has(name))store.set(name,new Map());const data=store.get(name);return {
    match:async req=>data.get(typeof req==='string'?req:req.url)?.clone(),
    put:async(req,res)=>{if(cacheWriteWait)await cacheWriteWait;data.set(typeof req==='string'?req:req.url,res.clone())}
  }};
  const context={URL,Response,Promise,fetch:()=>pending.promise,
    setTimeout:(fn,ms)=>{assert.equal(ms,1000);timers.set(++timer,fn);return timer},clearTimeout:id=>timers.delete(id),
    caches:{keys:async()=>[...store.keys()],open:async name=>cacheFor(name),delete:async name=>store.delete(name)},
    self:{location:{origin:'https://rt.test',href:url+'sw.js'},skipWaiting:async()=>{},
      clients:{claim:async()=>{},get:async()=>({postMessage:m=>messages.push(m)})},addEventListener:(name,fn)=>handlers[name]=fn}
  };
  vm.runInNewContext(code,context);
  const seed=async(name='rt-buyback-cache-old',body='saved',etag='old')=>cacheFor(name).put(url,new Response(body,{headers:{etag}}));
  const request=(extra={})=>{let response;const work=[];handlers.fetch({request:{url,method:'GET',mode:'navigate',...extra},resultingClientId:'page',respondWith:p=>response=p,waitUntil:p=>work.push(p)});return {get response(){return response},done:()=>Promise.all(work)}};
  const tick=async()=>{for(const fn of [...timers.values()])await fn()};
  return {pending,store,messages,seed,request,tick,timers,handlers};
}
(async()=>{
  let checks=1;
  // Slow network serves saved HTML at the deadline, then replaces the cache and notifies.
  {
    const h=harness();await h.seed();await h.seed('other-application-cache','unrelated');
    const r=h.request();await h.tick();assert.equal(await (await r.response).text(),'saved');
    h.pending.resolve(new Response('fresh',{headers:{etag:'new'}}));await r.done();
    assert.ok(!h.store.has('rt-buyback-cache-old'));assert.ok(h.store.has('other-application-cache'));
    const cache=[...h.store.entries()].find(([name])=>name.startsWith('rt-buyback-cache-'))[1];
    assert.equal(await cache.get('https://rt.test/').clone().text(),'fresh');
    assert.equal(h.messages[0].type,'RT_UPDATE_AVAILABLE');checks++;
  }
  // Fast responses are streamed without waiting for cache.put to consume the body.
  {
    const write=deferred(),h=harness(write.promise),r=h.request();h.pending.resolve(new Response('fresh',{headers:{etag:'new'}}));
    let deadline;
    const response=await Promise.race([r.response,new Promise((_,reject)=>{deadline=setTimeout(()=>reject(new Error('Network response waited for cache write')),200)})]);
    clearTimeout(deadline);assert.equal(await response.text(),'fresh');
    write.resolve();await r.done();assert.equal(h.timers.size,0);checks++;
  }
  // A first visit cannot resolve to undefined just because the timeout elapsed.
  {
    const h=harness(),r=h.request();let settled=false;r.response.then(()=>settled=true);
    await h.tick();assert.equal(settled,false);h.pending.resolve(new Response('first'));
    assert.equal(await (await r.response).text(),'first');await r.done();checks++;
  }
  for(const failure of ['offline','server-error']){
    const h=harness();await h.seed();const r=h.request();
    failure==='offline'?h.pending.reject(new Error('offline')):h.pending.resolve(new Response('error',{status:503}));
    assert.equal(await (await r.response).text(),'saved');await r.done();assert.ok(h.store.has('rt-buyback-cache-old'));checks++;
  }
  {
    const h=harness(),r=h.request();h.pending.reject(new Error('offline'));
    assert.equal((await r.response).status,503);await r.done();checks++;
  }
  {
    const h=harness();await h.seed();const r=h.request();await h.tick();await r.response;
    h.pending.resolve(new Response('saved',{headers:{etag:'old'}}));await r.done();assert.equal(h.messages.length,0);checks++;
  }
  {
    const h=harness();await h.seed();let activation;h.handlers.activate({waitUntil:p=>activation=p});await activation;
    assert.ok(h.store.has('rt-buyback-cache-old'));
    assert.equal(h.request({method:'POST'}).response,undefined);
    assert.equal(h.request({url:'https://rt.test.other/'}).response,undefined);checks++;
  }
  console.log(JSON.stringify({passed:true,checks}));
})().catch(e=>{console.error(e);process.exitCode=1});
