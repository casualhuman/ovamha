/* Ovamha service worker: caches the app's screens so it opens like an installed app even when the
   hub cannot be reached. API calls (speech, guidelines, records) always go to the local hub. */
const CACHE = "ovamha-shell-v1";
const SHELL = ["/", "/index.html", "/app.css", "/app.js", "/art.js", "/manifest.webmanifest", "/icon.svg", "/icon-192.png", "/icon-512.png"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.pathname.startsWith("/api/")) return;  // never cache clinical data
  // Network first (always the latest app from the hub); fall back to the cached screens.
  e.respondWith(fetch(e.request).then((r) => {
    const copy = r.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); return r;
  }).catch(() => caches.match(e.request).then((m) => m || caches.match("/"))));
});
