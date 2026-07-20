const C = "rt-buyback-cache-v1";
self.addEventListener("install", e => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())
));
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || !req.url.startsWith(self.location.origin)) return;
  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) { const cp = res.clone(); caches.open(C).then(c => c.put(req, cp)); }
      return res;
    }).catch(() => caches.match(req).then(m => m || (req.mode === "navigate" ? caches.match("./") : undefined)))
  );
});
