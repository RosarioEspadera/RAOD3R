const CACHE_NAME = "raod3r-cache-v1";
const urlsToCache = [
  "/",
  "/index.html",
  "/library.html",
  "/manifest.json",
  "/favicon.png",
];

// Install SW
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

// Serve from cache first
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
