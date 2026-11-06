const C = "rt-buyback-cache-v6-33-agebound-20261107";
const PREFIX = "rt-buyback-cache-";
const NETWORK_WAIT_MS = 1000;
self.addEventListener("install", e => e.waitUntil(self.skipWaiting()));
// Keep the previous app available until a successful navigation seeds this cache.
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));

async function cachedPage(req) {
  const names = await caches.keys();
  for (const name of [C, ...names.filter(k => k !== C && k.startsWith(PREFIX)).reverse()]) {
    const cache = await caches.open(name);
    const hit = await cache.match(req) || (req.mode === "navigate" &&
      (await cache.match(new URL("./", self.location.href).href) ||
       await cache.match(new URL("index.html", self.location.href).href)));
    if (hit) return hit;
  }
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  const saved = cachedPage(req).catch(() => undefined);
  let servedSaved = false, timer;
  const fetched = fetch(req);
  const refreshed = fetched.then(async res => {
    if (res.ok) {
      const copy = res.clone();
      const cache = await caches.open(C);
      await cache.put(req, copy);
      if (req.mode === "navigate") {
        // Query-string entry points can also seed the normal offline entry point.
        if (new URL(req.url).pathname === "/" || new URL(req.url).pathname === "/index.html") {
          await cache.put(new URL("./", self.location.href).href, res.clone());
          const names = await caches.keys();
          await Promise.all(names.filter(k => k !== C && k.startsWith(PREFIX)).map(k => caches.delete(k)));
        }
        const old = await saved;
        if (servedSaved && old && old.headers.get("etag") !== res.headers.get("etag")) {
          const client = await self.clients.get(e.resultingClientId || e.clientId);
          if (client) client.postMessage({type:"RT_UPDATE_AVAILABLE"});
        }
      }
    }
  }).catch(() => {});
  // Return the network stream immediately; cache writes must not delay rendering.
  const network = fetched.then(async res => res.ok ? res : await saved || res)
    .catch(async () => await saved || new Response("Connection unavailable. Please reload when online.", {
    status:503, headers:{"Content-Type":"text/plain; charset=utf-8"}
  }));
  // A slow connection must not hold a previously loaded app indefinitely.
  const fallback = new Promise(resolve => {
    timer = setTimeout(async () => {
      const hit = await saved;
      if (hit) { servedSaved = true; resolve(hit); }
      // On first visit there is no saved app, so let the network finish.
    }, NETWORK_WAIT_MS);
  });
  e.respondWith(Promise.race([network, fallback]).finally(() => clearTimeout(timer)));
  // Finish refreshing the saved version even after a cached page was returned.
  e.waitUntil(refreshed);
});
