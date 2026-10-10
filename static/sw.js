/* CoffeeGuard AI service worker: lets the app open with no signal.
   Pages: network first, cached copy when offline. Static files: cache first
   (safe because every CSS/JS URL is versioned per deploy).
   API calls are never cached (photos taken offline are queued by predict.js). */
const VERSION = "cg-v2-2";  // bump to force every browser to drop old caches
// Pages only: CSS/JS URLs carry ?v=<deploy time> and are cached the first time they load
const PRECACHE = ["/predict", "/", "/static/icons/icon-192.png", "/manifest.webmanifest"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      const copy = res.clone(); caches.open(VERSION).then((c) => c.put(e.request, copy)); return res;
    })));
    return;
  }
  e.respondWith(fetch(e.request).then((res) => {
    const copy = res.clone(); caches.open(VERSION).then((c) => c.put(e.request, copy)); return res;
  }).catch(() => caches.match(e.request).then((hit) => hit || caches.match("/predict"))));
});
